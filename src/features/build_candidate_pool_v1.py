#!/usr/bin/env python3
"""Build first-pass availability-aware MLB candidate pools.

The output is not a final recommendation list. It joins Savant-derived recent
performance profiles with MLB organization roster status so the project can
prioritize who is worth deeper contract, medical, and scouting research.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

PITCHER_FEATURES = OUTPUT_DIR / "savant_pitcher_feature_summary_2023_2026.csv"
HITTER_FEATURES = OUTPUT_DIR / "savant_hitter_feature_summary_2023_2026.csv"
ROSTER_STATUS = OUTPUT_DIR / "mlb_roster_status_latest.csv"


def safe_rank(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() <= 1:
        return pd.Series(np.nan, index=series.index)
    ranked = numeric.rank(pct=True, ascending=True) * 100
    if not higher_is_better:
        ranked = 100 - ranked
    return ranked


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    values = pd.to_numeric(values, errors="coerce")
    weights = pd.to_numeric(weights, errors="coerce").fillna(0)
    mask = values.notna() & weights.gt(0)
    if not mask.any():
        return float("nan")
    return float(np.average(values[mask], weights=weights[mask]))


def join_unique(values: pd.Series, max_items: int = 4) -> str:
    cleaned = [str(value).strip() for value in values.dropna().unique() if str(value).strip()]
    if not cleaned:
        return ""
    if len(cleaned) > max_items:
        return " | ".join(cleaned[:max_items]) + f" | +{len(cleaned) - max_items}"
    return " | ".join(cleaned)


def first_non_null(values: pd.Series) -> object:
    non_null = values.dropna()
    if non_null.empty:
        return np.nan
    return non_null.iloc[0]


def collapse_roster(roster: pd.DataFrame) -> pd.DataFrame:
    out = roster.copy()
    out["player_id"] = pd.to_numeric(out["player_id"], errors="coerce").astype("Int64")
    out["is_40man"] = out["is_40man"].astype(bool)
    out["is_active"] = out["is_active"].astype(bool)
    out["is_full_roster"] = out["is_full_roster"].astype(bool)

    collapsed = (
        out.groupby("player_id", dropna=False)
        .agg(
            roster_evaluation_date=("evaluation_date", "max"),
            roster_team=("team_abbreviation", join_unique),
            roster_team_name=("team_name", join_unique),
            roster_player_name=("player_name", first_non_null),
            primary_position=("primary_position", first_non_null),
            primary_position_type=("primary_position_type", first_non_null),
            primary_position_abbrev=("primary_position_abbrev", first_non_null),
            status_code=("status_code", join_unique),
            status_description=("status_description", join_unique),
            roster_note=("roster_note", join_unique),
            is_40man=("is_40man", "max"),
            is_active=("is_active", "max"),
            is_full_roster=("is_full_roster", "max"),
            age=("age", "max"),
            bat_side=("bat_side", first_non_null),
            pitch_hand=("pitch_hand", first_non_null),
            mlb_debut_date=("mlb_debut_date", first_non_null),
            birth_country=("birth_country", first_non_null),
            height=("height", first_non_null),
            weight=("weight", "max"),
        )
        .reset_index()
    )
    collapsed["in_current_mlb_org"] = True
    return collapsed


def add_market_status(df: pd.DataFrame, slot: str) -> pd.DataFrame:
    out = df.copy()
    out["in_current_mlb_org"] = out["in_current_mlb_org"].astype("boolean").fillna(False).astype(bool)
    for column in ["status_code", "status_description", "roster_note", "primary_position_type", "primary_position_abbrev"]:
        if column not in out.columns:
            out[column] = ""
        out[column] = out[column].fillna("").astype(str)
    out["is_40man"] = out["is_40man"].astype("boolean").fillna(False).astype(bool)
    out["is_active"] = out["is_active"].astype("boolean").fillna(False).astype(bool)

    status_blob = (
        out["status_code"].str.lower()
        + " "
        + out["status_description"].str.lower()
        + " "
        + out["roster_note"].str.lower()
    )
    out["dfa_or_designated_flag"] = status_blob.str.contains("des|designated|dfa", regex=True, na=False)
    out["injury_flag"] = status_blob.str.contains(
        "injured|surgery|strain|sprain|recovery|reconstruction|ucl|shoulder|elbow|hamstring|oblique",
        regex=True,
        na=False,
    )
    out["restricted_or_development_flag"] = status_blob.str.contains(
        "restricted|development|not yet reported", regex=True, na=False
    )

    out["market_access_bucket"] = "unknown_not_in_current_mlb_org"
    out.loc[out["in_current_mlb_org"] & out["is_active"], "market_access_bucket"] = "mlb_active_low_access"
    out.loc[
        out["in_current_mlb_org"] & out["is_40man"] & ~out["is_active"],
        "market_access_bucket",
    ] = "40man_not_active_medium_low_access"
    out.loc[
        out["in_current_mlb_org"] & ~out["is_40man"] & ~out["is_active"],
        "market_access_bucket",
    ] = "non40man_org_candidate"
    out.loc[out["dfa_or_designated_flag"], "market_access_bucket"] = "dfa_designated_high_signal"
    out.loc[out["injury_flag"], "market_access_bucket"] = "medical_red_flag"

    out["market_access_score"] = 45.0
    out.loc[out["market_access_bucket"].eq("non40man_org_candidate"), "market_access_score"] = 75
    out.loc[out["market_access_bucket"].eq("dfa_designated_high_signal"), "market_access_score"] = 95
    out.loc[out["market_access_bucket"].eq("40man_not_active_medium_low_access"), "market_access_score"] = 35
    out.loc[out["market_access_bucket"].eq("mlb_active_low_access"), "market_access_score"] = 10
    out.loc[out["market_access_bucket"].eq("medical_red_flag"), "market_access_score"] = 15
    out.loc[out["restricted_or_development_flag"], "market_access_score"] = np.minimum(out["market_access_score"], 30)

    out["age"] = pd.to_numeric(out["age"], errors="coerce")
    if slot == "pitcher":
        age_target = out["age"].between(24, 33, inclusive="both")
        age_near = out["age"].between(24, 35, inclusive="both")
    else:
        age_target = out["age"].between(23, 32, inclusive="both")
        age_near = out["age"].between(23, 34, inclusive="both")
    out["age_fit_score"] = np.select([age_target, age_near, out["age"].isna()], [100, 70, 55], default=35)

    return out


def summarize_pitchers(features: pd.DataFrame) -> pd.DataFrame:
    recent = features[features["game_year"].ge(2025)].copy()
    recent["pitcher"] = pd.to_numeric(recent["pitcher"], errors="coerce").astype("Int64")
    rate_cols = [
        "starter_stabilizer_score",
        "bb_hbp_pct",
        "k_pct",
        "hr_pct",
        "woba_allowed",
        "xwoba_allowed_bbe",
        "whiff_per_swing",
        "chase_rate",
        "zone_rate",
        "first_pitch_nonball_rate",
        "three_ball_pitch_rate",
        "hardhit_rate",
        "barrel_rate",
        "early_1_3_woba_allowed",
        "risp_woba_allowed",
        "third_time_woba_allowed",
    ]

    rows = []
    for player_id, group in recent.groupby("pitcher", dropna=False):
        latest_year = int(group["game_year"].max())
        latest = group.sort_values("game_year").iloc[-1]
        row = {
            "slot": "regular_foreign_pitcher",
            "player_id": player_id,
            "player_name": latest["player_name"],
            "recent_years": join_unique(group["game_year"].astype(str), max_items=4),
            "latest_game_year": latest_year,
            "recent_pa": group["pa"].sum(),
            "recent_pitches": group["pitch"].sum(),
            "recent_games": group["games"].sum(),
            "recent_start_proxy_games": group["start_proxy_games"].sum(),
            "recent_games_80plus_pitches": group["games_80plus_pitches"].sum(),
            "latest_pa": latest["pa"],
            "latest_pitches": latest["pitch"],
            "latest_start_proxy_games": latest["start_proxy_games"],
            "current_2026_pa": group.loc[group["game_year"].eq(2026), "pa"].sum(),
            "current_2026_pitches": group.loc[group["game_year"].eq(2026), "pitch"].sum(),
        }
        for column in rate_cols:
            row[f"recent_{column}"] = weighted_mean(group[column], group["pa"])
            row[f"latest_{column}"] = latest[column]
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    out["workload_process_score"] = pd.concat(
        [
            safe_rank(out["recent_start_proxy_games"]),
            safe_rank(out["recent_games_80plus_pitches"]),
            safe_rank(out["recent_pitches"]),
        ],
        axis=1,
    ).mean(axis=1, skipna=True)
    out["damage_control_score"] = pd.concat(
        [
            safe_rank(out["recent_bb_hbp_pct"], higher_is_better=False),
            safe_rank(out["recent_hr_pct"], higher_is_better=False),
            safe_rank(out["recent_woba_allowed"], higher_is_better=False),
            safe_rank(out["recent_hardhit_rate"], higher_is_better=False),
            safe_rank(out["recent_risp_woba_allowed"], higher_is_better=False),
        ],
        axis=1,
    ).mean(axis=1, skipna=True)
    out["recency_sample_score"] = safe_rank(out["current_2026_pitches"].fillna(0))
    out["performance_fit_score"] = pd.concat(
        [
            out["recent_starter_stabilizer_score"],
            out["workload_process_score"],
            out["damage_control_score"],
            out["recency_sample_score"] * 0.5,
        ],
        axis=1,
    ).mean(axis=1, skipna=True)
    return out


def summarize_hitters(features: pd.DataFrame) -> pd.DataFrame:
    recent = features[features["game_year"].ge(2025)].copy()
    recent["batter"] = pd.to_numeric(recent["batter"], errors="coerce").astype("Int64")
    rate_cols = [
        "ssg_message_screen_score",
        "woba",
        "bb_pct",
        "k_pct",
        "hr_pct",
        "chase_rate",
        "nonfast_chase_rate",
        "whiff_per_swing",
        "nonfast_whiff_per_swing",
        "barrel_rate",
        "hardhit_rate",
        "sweet_spot_rate",
        "air_bbe_rate",
        "same_field_air_rate_proxy",
        "low_velo_xwoba",
        "high_velo_xwoba",
        "break_off_xwoba",
        "hitter_count_xwoba",
    ]

    rows = []
    for player_id, group in recent.groupby("batter", dropna=False):
        latest_year = int(group["game_year"].max())
        latest = group.sort_values("game_year").iloc[-1]
        row = {
            "slot": "regular_foreign_hitter_outfield_priority",
            "player_id": player_id,
            "player_name": latest.get("batter_name", ""),
            "recent_years": join_unique(group["game_year"].astype(str), max_items=4),
            "latest_game_year": latest_year,
            "recent_pa": group["pa"].sum(),
            "recent_pitches": group["pitch"].sum(),
            "latest_pa": latest["pa"],
            "current_2026_pa": group.loc[group["game_year"].eq(2026), "pa"].sum(),
        }
        for column in rate_cols:
            row[f"recent_{column}"] = weighted_mean(group[column], group["pa"])
            row[f"latest_{column}"] = latest[column]
        rows.append(row)

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    out["process_damage_score"] = pd.concat(
        [
            out["recent_ssg_message_screen_score"],
            safe_rank(out["recent_bb_pct"]),
            safe_rank(out["recent_chase_rate"], higher_is_better=False),
            safe_rank(out["recent_barrel_rate"]),
            safe_rank(out["recent_hardhit_rate"]),
            safe_rank(out["recent_break_off_xwoba"]),
            safe_rank(out["recent_low_velo_xwoba"]),
        ],
        axis=1,
    ).mean(axis=1, skipna=True)
    out["flawed_market_signal"] = (
        (out["recent_ssg_message_screen_score"].ge(65))
        & (
            out["recent_k_pct"].ge(0.25)
            | out["recent_woba"].le(0.335)
            | out["recent_chase_rate"].ge(0.30)
        )
        & out["recent_bb_pct"].ge(0.075)
        & out["recent_barrel_rate"].ge(0.075)
    )
    out["recency_sample_score"] = safe_rank(out["current_2026_pa"].fillna(0))
    out["performance_fit_score"] = pd.concat(
        [
            out["process_damage_score"],
            out["recent_ssg_message_screen_score"],
            out["recency_sample_score"] * 0.5,
        ],
        axis=1,
    ).mean(axis=1, skipna=True)
    return out


def add_role_and_final_scores(candidates: pd.DataFrame, slot: str) -> pd.DataFrame:
    out = add_market_status(candidates, slot=slot)
    if slot == "hitter":
        pos_blob = (out["primary_position_type"] + " " + out["primary_position_abbrev"]).str.lower()
        out["role_gate_pass"] = pos_blob.str.contains("outfield|lf|cf|rf|of", regex=True, na=False)
        out["role_fit_score"] = np.where(out["role_gate_pass"], 100, 25)
        min_recent_pa = 150
        min_current_sample = 20
        out["age_gate_pass"] = out["age"].between(23, 34, inclusive="both")
    else:
        out["role_gate_pass"] = out["recent_start_proxy_games"].ge(3)
        out["role_fit_score"] = np.where(out["role_gate_pass"], 100, 35)
        min_recent_pa = 150
        min_current_sample = 50
        out["age_gate_pass"] = out["age"].between(24, 36, inclusive="both")

    out["sample_gate_pass"] = out["recent_pa"].ge(min_recent_pa) & (
        out["current_2026_pa"].fillna(0).ge(min_current_sample) | out["latest_game_year"].ge(2025)
    )
    out["availability_gate_pass"] = (
        out["in_current_mlb_org"]
        & ~out["is_active"]
        & out["market_access_score"].ge(55)
        & ~out["injury_flag"]
        & ~out["restricted_or_development_flag"]
    )
    out["economic_proxy_gate_pass"] = ~out["is_active"] & ~(
        out["is_40man"] & out["market_access_score"].lt(50)
    )
    out["first_pass_gate_pass"] = (
        out["sample_gate_pass"]
        & out["role_gate_pass"]
        & out["availability_gate_pass"]
        & out["economic_proxy_gate_pass"]
        & out["age_gate_pass"].fillna(False)
    )

    out["final_priority_score"] = (
        out["performance_fit_score"].fillna(50) * 0.55
        + out["market_access_score"].fillna(50) * 0.25
        + out["age_fit_score"].fillna(55) * 0.10
        + out["role_fit_score"].fillna(50) * 0.10
    )
    out.loc[out["injury_flag"], "final_priority_score"] -= 20
    out.loc[out["is_active"], "final_priority_score"] -= 15
    out["final_priority_score"] = out["final_priority_score"].clip(lower=0, upper=100)

    reasons = []
    for _, row in out.iterrows():
        fail = []
        if not row["sample_gate_pass"]:
            fail.append("sample")
        if not row["role_gate_pass"]:
            fail.append("role")
        if not row["availability_gate_pass"]:
            fail.append("availability")
        if not row["economic_proxy_gate_pass"]:
            fail.append("economic_proxy")
        if not row["age_gate_pass"]:
            fail.append("age")
        reasons.append(",".join(fail))
    out["gate_fail_reason"] = reasons
    return out.sort_values(["first_pass_gate_pass", "final_priority_score"], ascending=[False, False])


def build_summary(pitchers: pd.DataFrame, hitters: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for name, df in [
        ("regular_foreign_pitcher", pitchers),
        ("regular_foreign_hitter_outfield_priority", hitters),
    ]:
        if df.empty:
            frames.append(
                {
                    "slot": name,
                    "rows": 0,
                    "first_pass_gate_pass": 0,
                    "non40man_org_candidate": 0,
                    "dfa_designated_high_signal": 0,
                    "medical_red_flag": 0,
                    "mlb_active_low_access": 0,
                    "top_score": np.nan,
                }
            )
            continue
        bucket_counts = df["market_access_bucket"].value_counts()
        frames.append(
            {
                "slot": name,
                "rows": len(df),
                "first_pass_gate_pass": int(df["first_pass_gate_pass"].sum()),
                "non40man_org_candidate": int(bucket_counts.get("non40man_org_candidate", 0)),
                "dfa_designated_high_signal": int(bucket_counts.get("dfa_designated_high_signal", 0)),
                "medical_red_flag": int(bucket_counts.get("medical_red_flag", 0)),
                "mlb_active_low_access": int(bucket_counts.get("mlb_active_low_access", 0)),
                "top_score": round(float(df["final_priority_score"].max()), 2),
            }
        )
    return pd.DataFrame(frames)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    roster = collapse_roster(pd.read_csv(ROSTER_STATUS))
    pitcher_features = pd.read_csv(PITCHER_FEATURES)
    hitter_features = pd.read_csv(HITTER_FEATURES)

    pitchers = summarize_pitchers(pitcher_features).merge(
        roster, on="player_id", how="left", validate="many_to_one"
    )
    hitters = summarize_hitters(hitter_features).merge(
        roster, on="player_id", how="left", validate="many_to_one"
    )

    pitchers = add_role_and_final_scores(pitchers, slot="pitcher")
    hitters = add_role_and_final_scores(hitters, slot="hitter")

    pitcher_path = OUTPUT_DIR / "mlb_pitcher_availability_candidate_pool_v1.csv"
    hitter_path = OUTPUT_DIR / "mlb_outfielder_availability_candidate_pool_v1.csv"
    summary_path = OUTPUT_DIR / "candidate_pool_summary_v1.csv"

    pitchers.to_csv(pitcher_path, index=False)
    hitters.to_csv(hitter_path, index=False)
    build_summary(pitchers, hitters).to_csv(summary_path, index=False)

    print("wrote", pitcher_path)
    print("wrote", hitter_path)
    print("wrote", summary_path)
    print(build_summary(pitchers, hitters).to_string(index=False))

    show_cols = [
        "player_name",
        "player_id",
        "latest_game_year",
        "recent_pa",
        "market_access_bucket",
        "primary_position_abbrev",
        "age",
        "performance_fit_score",
        "market_access_score",
        "final_priority_score",
        "gate_fail_reason",
    ]
    print("\nPitcher first-pass gate leaders")
    print(pitchers[pitchers["first_pass_gate_pass"]][show_cols].head(12).to_string(index=False))
    print("\nOutfield hitter first-pass gate leaders")
    print(hitters[hitters["first_pass_gate_pass"]][show_cols].head(12).to_string(index=False))


if __name__ == "__main__":
    main()
