#!/usr/bin/env python3
"""Build MiLB role/level continuity features for market-screened candidates."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"
STATS = OUT_DIR / "milb_market_pool_stats_latest.csv"
AUDIT = OUT_DIR / "milb_market_pool_stats_request_audit_latest.csv"
MARKET = OUT_DIR / "mlb_replacement_market_status_v1.csv"

LEVEL_SCORE = {11: 100, 12: 80, 13: 60, 14: 45, 16: 25}
LEVEL_NAME = {11: "AAA", 12: "AA", 13: "High-A", 14: "Single-A", 16: "Rookie"}


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def ip_to_outs(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    if "." not in text:
        return float(text) * 3
    whole, frac = text.split(".", 1)
    whole_outs = int(float(whole)) * 3 if whole else 0
    frac = frac[:1]
    extra_outs = int(frac) if frac in {"0", "1", "2"} else 0
    return float(whole_outs + extra_outs)


def outs_to_ip(outs: object) -> float:
    if pd.isna(outs):
        return np.nan
    return float(outs) / 3.0


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    numeric = to_num(values)
    weights = to_num(weights).fillna(0)
    mask = numeric.notna() & weights.gt(0)
    if not mask.any():
        return float(numeric.mean()) if numeric.notna().any() else np.nan
    return float(np.average(numeric[mask], weights=weights[mask]))


def prepare_rows(stats: pd.DataFrame) -> pd.DataFrame:
    out = stats.copy()
    out["player_id"] = to_num(out["player_id"]).astype("Int64")
    out["season"] = to_num(out["season"]).astype("Int64")
    out["sport_id"] = to_num(out["sport_id"]).astype("Int64")
    out["level_score"] = out["sport_id"].map(LEVEL_SCORE).fillna(0)
    out["level_name"] = out["sport_id"].map(LEVEL_NAME).fillna(out["sport_abbreviation"].fillna(""))
    out["team_id_missing"] = out["team_id"].isna()
    if "innings_pitched" in out.columns:
        out["innings_outs"] = out["innings_pitched"].map(ip_to_outs)
    else:
        out["innings_outs"] = np.nan
    for column in [
        "games_played",
        "games_started",
        "strike_outs",
        "base_on_balls",
        "home_runs",
        "hits",
        "earned_runs",
        "batters_faced",
        "plate_appearances",
        "at_bats",
        "total_bases",
        "doubles",
        "triples",
        "rbi",
    ]:
        if column not in out.columns:
            out[column] = np.nan
        out[column] = to_num(out[column])
    for column in ["ops", "obp", "slg", "avg", "era", "whip"]:
        if column not in out.columns:
            out[column] = np.nan
        out[column] = to_num(out[column])
    return out


def collapse_multi_team(rows: pd.DataFrame) -> pd.DataFrame:
    """Use official total rows when present; otherwise aggregate team rows."""
    collapsed: list[dict] = []
    group_cols = ["player_id", "stat_group", "season", "sport_id"]
    count_cols = [
        "games_played",
        "games_started",
        "strike_outs",
        "base_on_balls",
        "home_runs",
        "hits",
        "earned_runs",
        "batters_faced",
        "plate_appearances",
        "at_bats",
        "total_bases",
        "doubles",
        "triples",
        "rbi",
        "innings_outs",
    ]
    for keys, group in rows.groupby(group_cols, dropna=False):
        total_rows = group[group["team_id_missing"]]
        if not total_rows.empty:
            row = total_rows.sort_values(["level_score"], ascending=False).iloc[-1].to_dict()
            row["used_official_total_row"] = True
            collapsed.append(row)
            continue

        first = group.iloc[0].to_dict()
        row = {key: value for key, value in first.items() if key not in count_cols}
        for column in count_cols:
            row[column] = group[column].sum(min_count=1)
        weight = group["plate_appearances"].fillna(group["batters_faced"]).fillna(group["games_played"])
        for column in ["ops", "obp", "slg", "avg", "era", "whip"]:
            row[column] = weighted_mean(group[column], weight)
        row["team_name"] = " | ".join([str(x) for x in group["team_name"].dropna().unique()[:4]])
        row["used_official_total_row"] = False
        collapsed.append(row)
    return pd.DataFrame(collapsed)


def pitcher_features(player: pd.DataFrame) -> dict:
    recent = player[player["season"].between(2025, 2026, inclusive="both")].copy()
    current = player[player["season"].eq(2026)].copy()
    aaa_current = current[current["sport_id"].eq(11)]
    highest_2026 = current["level_score"].max() if not current.empty else np.nan
    highest_recent = recent["level_score"].max() if not recent.empty else np.nan
    current_ip = outs_to_ip(current["innings_outs"].sum(min_count=1))
    current_games = current["games_played"].sum(min_count=1)
    current_starts = current["games_started"].sum(min_count=1)
    current_bf = current["batters_faced"].sum(min_count=1)
    current_k = current["strike_outs"].sum(min_count=1)
    current_bb = current["base_on_balls"].sum(min_count=1)
    current_hr = current["home_runs"].sum(min_count=1)
    aaa_ip = outs_to_ip(aaa_current["innings_outs"].sum(min_count=1))
    aaa_games = aaa_current["games_played"].sum(min_count=1)
    aaa_starts = aaa_current["games_started"].sum(min_count=1)
    starter_share = current_starts / current_games if pd.notna(current_games) and current_games > 0 else np.nan
    ip_per_game = current_ip / current_games if pd.notna(current_games) and current_games > 0 else np.nan
    k9 = current_k / current_ip * 9 if pd.notna(current_ip) and current_ip > 0 else np.nan
    bb9 = current_bb / current_ip * 9 if pd.notna(current_ip) and current_ip > 0 else np.nan
    hr9 = current_hr / current_ip * 9 if pd.notna(current_ip) and current_ip > 0 else np.nan

    if current.empty:
        bucket = "no_2026_milb_track"
    elif highest_2026 < 80:
        bucket = "current_lower_level_risk"
    elif not aaa_current.empty and pd.notna(aaa_starts) and aaa_starts >= 4 and pd.notna(aaa_ip) and aaa_ip >= 20:
        bucket = "current_aaa_starter_load"
    elif not aaa_current.empty and pd.notna(aaa_ip) and aaa_ip >= 10 and (aaa_starts >= 1 or ip_per_game >= 1.5):
        bucket = "current_aaa_swing_or_multi_inning"
    elif not aaa_current.empty and pd.notna(aaa_games) and aaa_games >= 8:
        bucket = "current_aaa_bullpen_track"
    elif not recent.empty:
        bucket = "recent_2025_2026_track_noncurrent"
    else:
        bucket = "unknown_milb_track"

    level_component = highest_2026 if pd.notna(highest_2026) else (highest_recent * 0.7 if pd.notna(highest_recent) else 20)
    load_component = min((current_ip or 0) / 45 * 100, 100) if pd.notna(current_ip) else 15
    starter_component = 100 if bucket == "current_aaa_starter_load" else 75 if bucket == "current_aaa_swing_or_multi_inning" else 45 if "bullpen" in bucket else 25
    command_component = 60
    if pd.notna(k9) and pd.notna(bb9):
        command_component = max(0, min(100, 50 + (k9 - 8) * 7 - (bb9 - 3.5) * 8))
    score = 0.30 * level_component + 0.25 * load_component + 0.25 * starter_component + 0.20 * command_component

    return {
        "milb_2026_highest_level_score": highest_2026,
        "milb_2025_2026_highest_level_score": highest_recent,
        "milb_2026_ip": current_ip,
        "milb_2026_games": current_games,
        "milb_2026_games_started": current_starts,
        "milb_2026_starter_share": starter_share,
        "milb_2026_ip_per_game": ip_per_game,
        "milb_2026_k9": k9,
        "milb_2026_bb9": bb9,
        "milb_2026_hr9": hr9,
        "milb_2026_batters_faced": current_bf,
        "milb_2026_aaa_ip": aaa_ip,
        "milb_2026_aaa_games": aaa_games,
        "milb_2026_aaa_games_started": aaa_starts,
        "milb_role_continuity_bucket": bucket,
        "milb_role_context_score": round(float(score), 3),
    }


def hitter_features(player: pd.DataFrame) -> dict:
    recent = player[player["season"].between(2025, 2026, inclusive="both")].copy()
    current = player[player["season"].eq(2026)].copy()
    aaa_current = current[current["sport_id"].eq(11)]
    highest_2026 = current["level_score"].max() if not current.empty else np.nan
    highest_recent = recent["level_score"].max() if not recent.empty else np.nan
    current_pa = current["plate_appearances"].sum(min_count=1)
    current_hr = current["home_runs"].sum(min_count=1)
    current_ops = weighted_mean(current["ops"], current["plate_appearances"]) if not current.empty else np.nan
    current_k = current["strike_outs"].sum(min_count=1)
    current_bb = current["base_on_balls"].sum(min_count=1)
    aaa_pa = aaa_current["plate_appearances"].sum(min_count=1)
    aaa_ops = weighted_mean(aaa_current["ops"], aaa_current["plate_appearances"]) if not aaa_current.empty else np.nan
    k_pct = current_k / current_pa if pd.notna(current_pa) and current_pa > 0 else np.nan
    bb_pct = current_bb / current_pa if pd.notna(current_pa) and current_pa > 0 else np.nan

    if current.empty:
        bucket = "no_2026_milb_track"
    elif highest_2026 < 80:
        bucket = "current_lower_level_risk"
    elif pd.notna(aaa_pa) and aaa_pa >= 150:
        bucket = "current_aaa_regular"
    elif pd.notna(aaa_pa) and aaa_pa >= 50:
        bucket = "current_aaa_part_time"
    elif not aaa_current.empty:
        bucket = "current_aaa_tiny_sample"
    elif not recent.empty:
        bucket = "recent_2025_2026_track_noncurrent"
    else:
        bucket = "unknown_milb_track"

    level_component = highest_2026 if pd.notna(highest_2026) else (highest_recent * 0.7 if pd.notna(highest_recent) else 20)
    sample_component = min((current_pa or 0) / 250 * 100, 100) if pd.notna(current_pa) else 15
    performance_component = 50
    if pd.notna(current_ops):
        performance_component = max(0, min(100, 50 + (current_ops - 0.75) * 140))
    contact_component = 50
    if pd.notna(k_pct) and pd.notna(bb_pct):
        contact_component = max(0, min(100, 55 + (bb_pct - 0.08) * 180 - (k_pct - 0.24) * 120))
    score = 0.25 * level_component + 0.25 * sample_component + 0.30 * performance_component + 0.20 * contact_component

    return {
        "milb_2026_highest_level_score": highest_2026,
        "milb_2025_2026_highest_level_score": highest_recent,
        "milb_2026_pa": current_pa,
        "milb_2026_hr": current_hr,
        "milb_2026_ops": current_ops,
        "milb_2026_k_pct": k_pct,
        "milb_2026_bb_pct": bb_pct,
        "milb_2026_aaa_pa": aaa_pa,
        "milb_2026_aaa_ops": aaa_ops,
        "milb_role_continuity_bucket": bucket,
        "milb_role_context_score": round(float(score), 3),
    }


def build_features() -> tuple[pd.DataFrame, pd.DataFrame]:
    stats = prepare_rows(pd.read_csv(STATS))
    audit = pd.read_csv(AUDIT)
    audit["player_id"] = to_num(audit["player_id"]).astype("Int64")
    requested = (
        audit.groupby(["player_id", "stat_group"], dropna=False)
        .agg(
            milb_request_count=("sport_id", "count"),
            milb_request_success_count=("status_code", lambda x: int((to_num(x) == 200).sum())),
            milb_request_split_count=("split_count", "sum"),
        )
        .reset_index()
    )
    collapsed = collapse_multi_team(stats)
    market = pd.read_csv(MARKET)
    market["player_id"] = to_num(market["player_id"]).astype("Int64")
    market["stat_group"] = "hitting"
    market.loc[market["slot"].eq("regular_foreign_pitcher"), "stat_group"] = "pitching"

    feature_rows: list[dict] = []
    for (player_id, stat_group), player in collapsed.groupby(["player_id", "stat_group"], dropna=False):
        first = player.iloc[0]
        row = {
            "player_id": player_id,
            "player_name": first.get("player_name"),
            "slot": first.get("slot"),
            "stat_group": stat_group,
            "milb_stat_rows": len(player),
            "milb_seasons": " | ".join(map(str, sorted(player["season"].dropna().astype(int).unique()))),
            "milb_levels_seen": " | ".join(
                [LEVEL_NAME.get(int(x), str(x)) for x in sorted(player["sport_id"].dropna().astype(int).unique())]
            ),
        }
        row.update(pitcher_features(player) if stat_group == "pitching" else hitter_features(player))
        feature_rows.append(row)

    features = pd.DataFrame(feature_rows)
    out = market.merge(features, on=["player_id", "stat_group"], how="left", suffixes=("", "_milb"))
    out = out.merge(requested, on=["player_id", "stat_group"], how="left")
    out["milb_requested_in_run"] = out["milb_request_count"].notna()
    out["has_milb_stat_track"] = out["milb_stat_rows"].notna()
    out["milb_role_continuity_bucket"] = out["milb_role_continuity_bucket"].fillna("no_milb_stats_found")
    out.loc[~out["milb_requested_in_run"], "milb_role_continuity_bucket"] = "not_collected_in_run_013_scope"
    out["milb_role_context_score"] = out["milb_role_context_score"].fillna(20)
    out["candidate_release_allowed_after_milb"] = False

    summary = (
        out.groupby(["slot", "candidate_release_policy_v2", "milb_role_continuity_bucket"], dropna=False)
        .agg(
            rows=("player_id", "count"),
            has_milb_track=("has_milb_stat_track", "sum"),
            median_milb_role_context_score=("milb_role_context_score", "median"),
            median_market_access_score_v2=("market_access_score_v2", "median"),
            median_final_priority_score=("final_priority_score", "median"),
        )
        .reset_index()
        .sort_values(["slot", "rows"], ascending=[True, False])
    )
    return out, summary


def main() -> None:
    features, summary = build_features()
    features_path = OUT_DIR / "mlb_market_pool_milb_role_context_v1.csv"
    summary_path = OUT_DIR / "mlb_market_pool_milb_role_context_summary_v1.csv"
    features.to_csv(features_path, index=False)
    summary.to_csv(summary_path, index=False)
    print(f"wrote {features_path} ({len(features)} rows)")
    print(f"wrote {summary_path} ({len(summary)} rows)")


if __name__ == "__main__":
    main()
