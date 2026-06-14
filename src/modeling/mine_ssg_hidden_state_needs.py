#!/usr/bin/env python3
"""Mine SSG-specific hidden needs from already-built context tables.

This is an unsupervised/anomaly-style pass. It does not pick candidates. It
scores where SSG is unusually weak relative to league rank, role thresholds, or
workload stress, then aggregates those rows into slot-specific message themes.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"


def read_csv(path: str) -> pd.DataFrame:
    file_path = OUTPUT_DIR / path
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def minmax(series: pd.Series) -> pd.Series:
    values = numeric(series)
    if values.notna().sum() == 0:
        return pd.Series(0.0, index=series.index)
    lo = values.min()
    hi = values.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.0, index=series.index)
    return (values - lo) / (hi - lo)


def bad_rank_score(df: pd.DataFrame, rank_cols: list[str]) -> pd.Series:
    score = pd.Series(0.0, index=df.index)
    for col in rank_cols:
        if col in df.columns:
            team_count = numeric(df.get("team_count", pd.Series(10, index=df.index))).replace(0, np.nan)
            score += ((numeric(df[col]) - 1) / (team_count - 1)).clip(lower=0, upper=1).fillna(0)
    return score


def sample_score(df: pd.DataFrame, sample_col: str, scale: float) -> pd.Series:
    if sample_col not in df.columns:
        return pd.Series(0.0, index=df.index)
    return (numeric(df[sample_col]) / scale).clip(lower=0, upper=1.5).fillna(0)


def infer_theme(source_layer: str, row: pd.Series) -> tuple[str, str, str]:
    text = " ".join(
        str(row.get(col, ""))
        for col in ["context_family", "context_label", "split_family", "split_label", "role_segment", "pitch_role"]
    ).lower()
    if source_layer.startswith("batting") or source_layer.startswith("role"):
        if "on_first" in text or "runner_on_first" in text or "runner_on_base" in text or "lt2_out_on_first" in text:
            return "foreign_hitter", "first_base_traffic_converter", "turn runner-on-first states into scoring-position pressure"
        if "vs_right" in text or "right" in text:
            return "foreign_hitter", "rhp_role_stabilizer", "stabilize OF/DH production against right-handed pitching"
        if "two" in text or "2s" in text:
            return "foreign_hitter", "two_strike_survival_bat", "reduce replacement-slot collapse after two strikes"
        if "dh" in text:
            return "foreign_hitter", "of_dh_bridge_bat", "repair the replacement-relevant OF/DH bridge"
        return "foreign_hitter", "context_runway_bat", "add offense in SSG-specific weak game states"

    if source_layer.startswith("pitching") or source_layer.startswith("workload"):
        if "early" in text or "starter" in text:
            return "foreign_pitcher", "abs_native_load_bearing_starter", "turn short starts into repeatable 5-6 inning starts"
        if "risp" in text or "runner" in text:
            return "foreign_pitcher", "traffic_command_starter", "prevent innings from exploding after traffic appears"
        if "bullpen" in text or source_layer == "workload_stress":
            return "asian_quota", "option_layer_shock_absorber", "protect the roster when starters compress bullpen workload"
        return "foreign_pitcher", "run_prevention_stabilizer", "raise the floor of run prevention across contexts"

    return "unknown", "unassigned", "unassigned"


def build_batting_team_cards() -> pd.DataFrame:
    df = read_csv("kbo_2026_team_situation_ranks.csv")
    if df.empty:
        return df
    ssg = df[df["t_code_name"].eq("SSG")].copy()
    rank_cols = [
        "OPS_rank",
        "OBP_rank",
        "SLG_rank",
        "bb_pct_rank",
        "ops_calc_rank",
        "obp_calc_rank",
        "slg_calc_rank",
        "rbi_per_pa_rank",
    ]
    ssg["anomaly_score"] = bad_rank_score(ssg, rank_cols) + sample_score(ssg, "PA", 250)
    ssg["source_layer"] = "batting_team_context_rank"
    ssg["unit"] = ssg["context_family"].astype(str) + ":" + ssg["context_label"].astype(str)
    ssg["metric_snapshot"] = (
        "OPS_rank="
        + ssg.get("OPS_rank", pd.Series(np.nan, index=ssg.index)).astype(str)
        + ";OBP_rank="
        + ssg.get("OBP_rank", pd.Series(np.nan, index=ssg.index)).astype(str)
        + ";OPS="
        + ssg.get("OPS", pd.Series(np.nan, index=ssg.index)).astype(str)
        + ";PA="
        + ssg.get("PA", pd.Series(np.nan, index=ssg.index)).astype(str)
    )
    return ssg


def build_runway_cards() -> pd.DataFrame:
    cards = []
    team = read_csv("ssg_2026_runway_gap_by_team.csv")
    if not team.empty:
        ssg = team[team["t_code_name"].eq("SSG")].copy()
        if not ssg.empty:
            ssg["anomaly_score"] = (
                (11 - numeric(ssg["risp_to_on_first_gap_rank"])) / 10
                + (11 - numeric(ssg["on_first_ops_rank"])) / 10
                + (11 - numeric(ssg["on_first_obp_rank"])) / 10
                + sample_score(ssg, "PA_on_first", 450)
            )
            ssg["source_layer"] = "batting_team_runway_gap"
            ssg["unit"] = "runner_on_first_vs_risp_gap"
            ssg["metric_snapshot"] = (
                "RISP_OPS="
                + ssg["OPS_risp"].astype(str)
                + ";on_first_OPS="
                + ssg["OPS_on_first"].astype(str)
                + ";on_first_OBP_rank="
                + ssg["on_first_obp_rank"].astype(str)
                + ";gap_rank="
                + ssg["risp_to_on_first_gap_rank"].astype(str)
            )
            cards.append(ssg)

    role = read_csv("ssg_2026_role_runway_context.csv")
    if not role.empty:
        focus = role[role["role_segment"].astype(str).str.contains("OF|DH", regex=True, na=False)].copy()
        focus["anomaly_score"] = (
            sample_score(focus, "pa", 70)
            + ((0.700 - numeric(focus["ops"])).clip(lower=0) * 3).fillna(0)
            + ((0.320 - numeric(focus["obp"])).clip(lower=0) * 4).fillna(0)
            + (numeric(focus["gdp_per_pa"]).fillna(0) * 8)
        )
        focus["source_layer"] = "role_runway_context"
        focus["unit"] = focus["role_segment"].astype(str) + ":" + focus["split_label"].astype(str)
        focus["metric_snapshot"] = (
            "OPS="
            + focus["ops"].round(3).astype(str)
            + ";OBP="
            + focus["obp"].round(3).astype(str)
            + ";GDP/PA="
            + focus["gdp_per_pa"].round(3).astype(str)
            + ";PA="
            + focus["pa"].astype(str)
        )
        cards.append(focus)

    return pd.concat(cards, ignore_index=True, sort=False) if cards else pd.DataFrame()


def build_role_context_cards() -> pd.DataFrame:
    df = read_csv("ssg_2026_situation_role_splits.csv")
    if df.empty:
        return df
    focus = df[df["replacement_relevant"].eq(True) & numeric(df["pa"]).ge(20)].copy()
    focus["anomaly_score"] = (
        sample_score(focus, "pa", 80)
        + ((0.700 - numeric(focus["ops"])).clip(lower=0) * 2.5).fillna(0)
        + ((0.320 - numeric(focus["obp"])).clip(lower=0) * 4).fillna(0)
        + ((numeric(focus["k_pct"]) - 0.230).clip(lower=0) * 2).fillna(0)
    )
    focus["source_layer"] = "role_split_context"
    focus["unit"] = (
        focus["role_segment"].astype(str)
        + ":"
        + focus["split_family"].astype(str)
        + ":"
        + focus["split_label"].astype(str)
    )
    focus["metric_snapshot"] = (
        "OPS="
        + focus["ops"].round(3).astype(str)
        + ";OBP="
        + focus["obp"].round(3).astype(str)
        + ";K%="
        + focus["k_pct"].round(3).astype(str)
        + ";PA="
        + focus["pa"].astype(str)
    )
    return focus


def build_pitching_cards() -> pd.DataFrame:
    cards = []
    team = read_csv("kbo_2026_team_pitching_situation_ranks.csv")
    if not team.empty:
        ssg = team[df_filter(team, "t_code_name", "SSG")].copy()
        rank_cols = [
            "ERA_rank",
            "WHIP_rank",
            "OPS_rank",
            "OBP_rank",
            "era_calc_rank",
            "whip_calc_rank",
            "ops_allowed_calc_rank",
            "obp_allowed_calc_rank",
            "bb9_rank",
            "hr9_rank",
        ]
        ssg["anomaly_score"] = bad_rank_score(ssg, rank_cols) + sample_score(ssg, "TBF", 400)
        ssg["source_layer"] = "pitching_team_context_rank"
        ssg["unit"] = ssg["context_family"].astype(str) + ":" + ssg["context_label"].astype(str)
        ssg["metric_snapshot"] = (
            "ERA_rank="
            + ssg.get("ERA_rank", pd.Series(np.nan, index=ssg.index)).astype(str)
            + ";WHIP_rank="
            + ssg.get("WHIP_rank", pd.Series(np.nan, index=ssg.index)).astype(str)
            + ";OPS_allowed_rank="
            + ssg.get("OPS_rank", pd.Series(np.nan, index=ssg.index)).astype(str)
            + ";TBF="
            + ssg.get("TBF", pd.Series(np.nan, index=ssg.index)).astype(str)
        )
        cards.append(ssg)

    role = read_csv("ssg_2026_team_pitching_role_ranks.csv")
    if not role.empty:
        focus = role.copy()
        rank_cols = ["era_rank", "whip_rank", "ops_allowed_rank", "bb9_rank", "hr9_rank"]
        focus["anomaly_score"] = bad_rank_score(focus, rank_cols) + (
            (10 - numeric(focus.get("outs_per_start_rank", pd.Series(10, index=focus.index)))) / 9
        ).clip(lower=0).fillna(0)
        focus["source_layer"] = "pitching_role_rank"
        focus["unit"] = focus["pitch_role"].astype(str)
        focus["metric_snapshot"] = (
            "ERA="
            + focus["era"].round(2).astype(str)
            + ";WHIP="
            + focus["whip"].round(2).astype(str)
            + ";OPS_allowed="
            + focus["ops_allowed"].round(3).astype(str)
            + ";outs/start="
            + focus["outs_per_start"].round(1).astype(str)
        )
        cards.append(focus)

    workload = read_csv("ssg_2026_game_pitching_workload.csv")
    if not workload.empty:
        row = {
            "source_layer": "workload_stress",
            "unit": "short_start_bullpen_compression",
            "anomaly_score": (
                workload["starter_short_lt5"].mean() * 4
                + workload["starter_disaster"].mean() * 3
                + numeric(workload["bullpen_ip_after_start"]).mean() / 3
            ),
            "metric_snapshot": (
                f"short_start_rate={workload['starter_short_lt5'].mean():.3f};"
                f"disaster_start_rate={workload['starter_disaster'].mean():.3f};"
                f"avg_bullpen_ip={numeric(workload['bullpen_ip_after_start']).mean():.2f};"
                f"games={len(workload)}"
            ),
            "pitch_role": "starter_to_bullpen_system",
        }
        cards.append(pd.DataFrame([row]))

    return pd.concat(cards, ignore_index=True, sort=False) if cards else pd.DataFrame()


def df_filter(df: pd.DataFrame, column: str, value: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(False, index=df.index)
    return df[column].eq(value)


def add_theme_columns(cards: pd.DataFrame) -> pd.DataFrame:
    out = cards.copy()
    themes = out.apply(lambda row: infer_theme(str(row.get("source_layer", "")), row), axis=1)
    out["slot"] = [item[0] for item in themes]
    out["message_theme"] = [item[1] for item in themes]
    out["theme_plain_english"] = [item[2] for item in themes]
    keep = [
        "slot",
        "message_theme",
        "theme_plain_english",
        "source_layer",
        "unit",
        "anomaly_score",
        "metric_snapshot",
        "context_family",
        "context_label",
        "split_family",
        "split_label",
        "role_segment",
        "pitch_role",
    ]
    for col in keep:
        if col not in out.columns:
            out[col] = np.nan
    return out[keep].sort_values(["anomaly_score"], ascending=False)


def build_message_candidates(cards: pd.DataFrame) -> pd.DataFrame:
    if cards.empty:
        return cards
    ranked = cards.copy()
    ranked["evidence_rank_within_theme"] = ranked.groupby("message_theme")["anomaly_score"].rank(
        method="first", ascending=False
    )
    top_evidence = (
        ranked[ranked["evidence_rank_within_theme"].le(5)]
        .groupby(["slot", "message_theme", "theme_plain_english"], dropna=False)
        .agg(
            evidence_rows=("unit", "count"),
            total_anomaly_score=("anomaly_score", "sum"),
            max_anomaly_score=("anomaly_score", "max"),
            top_units=("unit", lambda s: " | ".join(s.astype(str).head(5))),
            top_metric_snapshots=("metric_snapshot", lambda s: " | ".join(s.astype(str).head(3))),
        )
        .reset_index()
    )
    top_evidence["message_priority_score"] = (
        top_evidence["total_anomaly_score"] + top_evidence["max_anomaly_score"] * 0.5
    )
    return top_evidence.sort_values("message_priority_score", ascending=False)


def build_feature_contract(messages: pd.DataFrame) -> pd.DataFrame:
    contracts = {
        "first_base_traffic_converter": {
            "candidate_slot": "foreign_hitter",
            "must_have_features": "RHP damage;OBP floor;low GDP batted-ball shape;two-strike contact;line-drive/sweet-spot quality",
            "available_candidate_columns": "latest_woba;latest_bb_pct;latest_k_pct;latest_chase_rate;latest_sweet_spot_rate;latest_air_bbe_rate;latest_low_velo_xwoba",
        },
        "rhp_role_stabilizer": {
            "candidate_slot": "foreign_hitter",
            "must_have_features": "right-handed-pitcher stability;non-fastball contact;zone discipline",
            "available_candidate_columns": "latest_nonfast_chase_rate;latest_nonfast_whiff_per_swing;latest_bb_pct;latest_woba",
        },
        "two_strike_survival_bat": {
            "candidate_slot": "foreign_hitter",
            "must_have_features": "two-strike contact;chase suppression;usable opposite/line-drive contact",
            "available_candidate_columns": "latest_k_pct;latest_whiff_per_swing;latest_chase_rate;latest_sweet_spot_rate",
        },
        "of_dh_bridge_bat": {
            "candidate_slot": "foreign_hitter",
            "must_have_features": "OF/DH role fit;OBP and damage floor;not only max power",
            "available_candidate_columns": "eligible_of_priority;latest_woba;latest_bb_pct;latest_barrel_rate;latest_hardhit_rate",
        },
        "abs_native_load_bearing_starter": {
            "candidate_slot": "foreign_pitcher",
            "must_have_features": "zone creation;low BB+HBP;HR suppression;80+ pitch games;starter workload",
            "available_candidate_columns": "latest_zone_rate;latest_bb_hbp_pct;latest_hr_pct;latest_games_80plus_pitches;latest_starter_stabilizer_score",
        },
        "traffic_command_starter": {
            "candidate_slot": "foreign_pitcher",
            "must_have_features": "run prevention after traffic;walk suppression;barrel suppression;first-pitch strike proxy",
            "available_candidate_columns": "latest_bb_hbp_pct;latest_barrel_rate;latest_woba_allowed;latest_first_pitch_nonball_rate",
        },
        "run_prevention_stabilizer": {
            "candidate_slot": "foreign_pitcher",
            "must_have_features": "floor not ceiling;wOBA allowed;hard-hit suppression;starter workload",
            "available_candidate_columns": "latest_woba_allowed;latest_hardhit_rate;latest_starter_stabilizer_score;latest_pitches",
        },
        "option_layer_shock_absorber": {
            "candidate_slot": "asian_quota",
            "must_have_features": "availability;multi-inning depth;low cost;optionability;fast replacement readiness",
            "available_candidate_columns": "pending_NPB_CPBL_ABL_collection;contract_gate;role_flexibility;recent_workload",
        },
    }
    rows = []
    for _, msg in messages.iterrows():
        theme = msg["message_theme"]
        base = contracts.get(
            theme,
            {
                "candidate_slot": msg["slot"],
                "must_have_features": "context-specific stability",
                "available_candidate_columns": "to_be_defined",
            },
        )
        rows.append(
            {
                "message_theme": theme,
                "slot": msg["slot"],
                "candidate_slot": base["candidate_slot"],
                "must_have_features": base["must_have_features"],
                "available_candidate_columns": base["available_candidate_columns"],
                "evidence_rows": msg["evidence_rows"],
                "message_priority_score": msg["message_priority_score"],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_cards = pd.concat(
        [
            build_batting_team_cards(),
            build_runway_cards(),
            build_role_context_cards(),
            build_pitching_cards(),
        ],
        ignore_index=True,
        sort=False,
    )
    cards = add_theme_columns(raw_cards)
    messages = build_message_candidates(cards)
    contract = build_feature_contract(messages)

    cards.to_csv(OUTPUT_DIR / "ssg_hidden_state_mining_v0_1.csv", index=False)
    messages.to_csv(OUTPUT_DIR / "ssg_hidden_state_message_candidates_v0_1.csv", index=False)
    contract.to_csv(OUTPUT_DIR / "ssg_hidden_state_feature_contract_v0_1.csv", index=False)

    print("wrote", OUTPUT_DIR / "ssg_hidden_state_mining_v0_1.csv", cards.shape)
    print("wrote", OUTPUT_DIR / "ssg_hidden_state_message_candidates_v0_1.csv", messages.shape)
    print("wrote", OUTPUT_DIR / "ssg_hidden_state_feature_contract_v0_1.csv", contract.shape)
    if not messages.empty:
        print(messages.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
