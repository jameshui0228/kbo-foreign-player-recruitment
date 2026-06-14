#!/usr/bin/env python3
"""Score MLB pitcher candidates against the SSG v0.2 pitcher message.

The output is a research-lead board, not a final recommendation. Roster and
contract statuses can change quickly and must be manually verified before any
presentation-grade shortlist.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
POOL_PATH = OUTPUT_DIR / "mlb_pitcher_availability_candidate_pool_v1.csv"
MESSAGE_DECISION_PATH = OUTPUT_DIR / "ssg_pitching_message_v0_2_decision_table.csv"


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def num(df: pd.DataFrame, col: str, default: float = np.nan) -> pd.Series:
    if col not in df.columns:
        return pd.Series(default, index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def coalesce(df: pd.DataFrame, *cols: str, default: float = np.nan) -> pd.Series:
    out = pd.Series(default, index=df.index, dtype="float64")
    for col in cols:
        vals = num(df, col)
        out = out.where(out.notna(), vals)
    return out


def pct_high(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    if vals.notna().sum() <= 1:
        return pd.Series(50.0, index=series.index)
    return vals.rank(pct=True, ascending=True).mul(100).fillna(50)


def pct_low(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    if vals.notna().sum() <= 1:
        return pd.Series(50.0, index=series.index)
    return (1 - vals.rank(pct=True, ascending=True)).mul(100).fillna(50)


def scaled_existing(series: pd.Series) -> pd.Series:
    vals = pd.to_numeric(series, errors="coerce")
    return vals.clip(0, 100).fillna(50)


def weighted_sum(parts: list[tuple[pd.Series, float]]) -> pd.Series:
    total = pd.Series(0.0, index=parts[0][0].index)
    weight_sum = 0.0
    for series, weight in parts:
        total += pd.to_numeric(series, errors="coerce").fillna(50) * weight
        weight_sum += weight
    return total / weight_sum if weight_sum else total


def verification_need(row: pd.Series) -> str:
    reasons = []
    if not bool(row.get("first_pass_gate_pass", False)):
        fail = str(row.get("gate_fail_reason", ""))
        if fail and fail != "nan":
            reasons.append(f"resolve gate fail: {fail}")
    bucket = str(row.get("market_access_bucket", ""))
    if "40man" in bucket:
        reasons.append("verify 40-man option/access cost")
    if "dfa" in bucket:
        reasons.append("verify DFA/release timing")
    if "unknown" in bucket:
        reasons.append("verify current organization or free-agent status")
    if bool(row.get("injury_flag", False)):
        reasons.append("medical review required")
    if not reasons:
        reasons.append("verify contract, salary, role willingness, Korea interest")
    return "; ".join(reasons)


def assign_tier(row: pd.Series) -> str:
    score = row["ssg_pitcher_fit_score"]
    first_pass = bool(row["first_pass_gate_pass"])
    availability = bool(row["availability_gate_pass"])
    economic = bool(row["economic_proxy_gate_pass"])
    injury = bool(row["injury_flag"])
    active = bool(row["is_active"])
    if first_pass and score >= 62:
        return "A_research_lead"
    if first_pass:
        return "B_research_lead"
    if score >= 66 and availability and economic and not injury and not active:
        return "B_plus_gate_review"
    if score >= 60 and not injury:
        return "C_watchlist"
    return "D_hold"


def build_scores() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pool = pd.read_csv(POOL_PATH)
    decision = pd.read_csv(MESSAGE_DECISION_PATH)
    message_promoted = decision["overall_decision"].astype(str).str.contains("promote", na=False).any()

    out = pool.copy()
    for col in [
        "is_40man",
        "is_active",
        "in_current_mlb_org",
        "injury_flag",
        "role_gate_pass",
        "age_gate_pass",
        "sample_gate_pass",
        "availability_gate_pass",
        "economic_proxy_gate_pass",
        "first_pass_gate_pass",
    ]:
        if col in out.columns:
            out[col] = to_bool(out[col])
        else:
            out[col] = False

    out["starter_stabilizer_input"] = coalesce(
        out,
        "latest_starter_stabilizer_score",
        "recent_starter_stabilizer_score",
        "performance_fit_score",
    )
    out["zone_rate_input"] = coalesce(out, "latest_zone_rate", "recent_zone_rate")
    out["bb_hbp_input"] = coalesce(out, "latest_bb_hbp_pct", "recent_bb_hbp_pct")
    out["hr_input"] = coalesce(out, "latest_hr_pct", "recent_hr_pct")
    out["woba_allowed_input"] = coalesce(out, "latest_woba_allowed", "recent_woba_allowed")
    out["xwoba_allowed_input"] = coalesce(out, "latest_xwoba_allowed_bbe", "recent_xwoba_allowed_bbe")
    out["first_pitch_nonball_input"] = coalesce(
        out, "latest_first_pitch_nonball_rate", "recent_first_pitch_nonball_rate"
    )
    out["three_ball_pitch_input"] = coalesce(out, "latest_three_ball_pitch_rate", "recent_three_ball_pitch_rate")
    out["hardhit_input"] = coalesce(out, "latest_hardhit_rate", "recent_hardhit_rate")
    out["barrel_input"] = coalesce(out, "latest_barrel_rate", "recent_barrel_rate")
    out["early_woba_input"] = coalesce(out, "latest_early_1_3_woba_allowed", "recent_early_1_3_woba_allowed")
    out["risp_woba_input"] = coalesce(out, "latest_risp_woba_allowed", "recent_risp_woba_allowed")
    out["third_time_woba_input"] = coalesce(out, "latest_third_time_woba_allowed", "recent_third_time_woba_allowed")
    out["recent_80_pitch_games_input"] = num(out, "recent_games_80plus_pitches", 0).fillna(0)
    out["recent_start_games_input"] = num(out, "recent_start_proxy_games", 0).fillna(0)

    out["traffic_command_score"] = weighted_sum(
        [
            (pct_low(out["bb_hbp_input"]), 0.24),
            (pct_high(out["zone_rate_input"]), 0.20),
            (pct_low(out["risp_woba_input"]), 0.20),
            (pct_low(out["first_pitch_nonball_input"]), 0.14),
            (pct_low(out["three_ball_pitch_input"]), 0.12),
            (pct_low(out["woba_allowed_input"]), 0.10),
        ]
    )
    out["load_bearing_score"] = weighted_sum(
        [
            (scaled_existing(num(out, "workload_process_score", 50)), 0.30),
            (pct_high(out["starter_stabilizer_input"]), 0.25),
            (pct_high(out["recent_80_pitch_games_input"]), 0.20),
            (pct_high(out["recent_start_games_input"]), 0.15),
            (scaled_existing(num(out, "recency_sample_score", 50)), 0.10),
        ]
    )
    out["damage_control_score_v2"] = weighted_sum(
        [
            (scaled_existing(num(out, "damage_control_score", 50)), 0.25),
            (pct_low(out["hr_input"]), 0.16),
            (pct_low(out["barrel_input"]), 0.16),
            (pct_low(out["hardhit_input"]), 0.14),
            (pct_low(out["woba_allowed_input"]), 0.14),
            (pct_low(out["early_woba_input"]), 0.10),
            (pct_low(out["xwoba_allowed_input"]), 0.05),
        ]
    )
    gate_bonus = (
        out["availability_gate_pass"].astype(int) * 18
        + out["economic_proxy_gate_pass"].astype(int) * 14
        + out["first_pass_gate_pass"].astype(int) * 12
        + (~out["injury_flag"]).astype(int) * 8
        + (~out["is_active"]).astype(int) * 8
    )
    out["availability_realism_score"] = weighted_sum(
        [
            (scaled_existing(num(out, "market_access_score", 30)), 0.45),
            (scaled_existing(num(out, "age_fit_score", 55)), 0.20),
            (gate_bonus.clip(0, 60) * (100 / 60), 0.35),
        ]
    )
    out["sample_confidence_score"] = weighted_sum(
        [
            (scaled_existing(num(out, "recency_sample_score", 50)), 0.45),
            (pct_high(num(out, "recent_pitches", 0)), 0.30),
            (pct_high(num(out, "current_2026_pitches", 0)), 0.25),
        ]
    )

    out["ssg_pitcher_fit_score"] = weighted_sum(
        [
            (out["traffic_command_score"], 0.30),
            (out["load_bearing_score"], 0.25),
            (out["damage_control_score_v2"], 0.20),
            (out["availability_realism_score"], 0.15),
            (out["sample_confidence_score"], 0.10),
        ]
    )
    out["message_promoted_v0_2"] = message_promoted
    out["research_tier"] = out.apply(assign_tier, axis=1)
    out["verification_need"] = out.apply(verification_need, axis=1)

    sort_cols = ["research_tier", "ssg_pitcher_fit_score"]
    out = out.sort_values(sort_cols, ascending=[True, False])

    top_cols = [
        "player_id",
        "player_name",
        "research_tier",
        "ssg_pitcher_fit_score",
        "traffic_command_score",
        "load_bearing_score",
        "damage_control_score_v2",
        "availability_realism_score",
        "sample_confidence_score",
        "market_access_bucket",
        "roster_team",
        "roster_team_name",
        "status_code",
        "status_description",
        "is_40man",
        "is_active",
        "injury_flag",
        "age",
        "pitch_hand",
        "recent_start_games_input",
        "recent_80_pitch_games_input",
        "zone_rate_input",
        "bb_hbp_input",
        "hr_input",
        "woba_allowed_input",
        "early_woba_input",
        "risp_woba_input",
        "first_pass_gate_pass",
        "gate_fail_reason",
        "verification_need",
    ]
    for col in top_cols:
        if col not in out.columns:
            out[col] = np.nan

    realistic_mask = (
        out["research_tier"].isin(["A_research_lead", "B_research_lead", "B_plus_gate_review", "C_watchlist"])
        & out["role_gate_pass"]
        & out["sample_gate_pass"]
        & ~out["market_access_bucket"].eq("mlb_active_low_access")
        & ~out["injury_flag"]
    )
    top = out[realistic_mask][top_cols].head(60)
    benchmark = out[out["market_access_bucket"].eq("mlb_active_low_access")][top_cols].head(30)
    summary = (
        out.groupby(["research_tier", "market_access_bucket"], dropna=False)
        .agg(
            rows=("player_id", "count"),
            mean_fit_score=("ssg_pitcher_fit_score", "mean"),
            max_fit_score=("ssg_pitcher_fit_score", "max"),
            first_pass_rows=("first_pass_gate_pass", "sum"),
        )
        .reset_index()
        .sort_values(["research_tier", "max_fit_score"], ascending=[True, False])
    )
    return out, top, benchmark, summary


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scored, top, benchmark, summary = build_scores()
    scored.to_csv(OUTPUT_DIR / "mlb_pitcher_ssg_fit_scores_v0_1.csv", index=False)
    top.to_csv(OUTPUT_DIR / "mlb_pitcher_ssg_fit_top_research_leads_v0_1.csv", index=False)
    benchmark.to_csv(OUTPUT_DIR / "mlb_pitcher_ssg_fit_unavailable_benchmark_v0_1.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "mlb_pitcher_ssg_fit_summary_v0_1.csv", index=False)

    print("wrote", OUTPUT_DIR / "mlb_pitcher_ssg_fit_scores_v0_1.csv", scored.shape)
    print("wrote", OUTPUT_DIR / "mlb_pitcher_ssg_fit_top_research_leads_v0_1.csv", top.shape)
    print("wrote", OUTPUT_DIR / "mlb_pitcher_ssg_fit_unavailable_benchmark_v0_1.csv", benchmark.shape)
    print("wrote", OUTPUT_DIR / "mlb_pitcher_ssg_fit_summary_v0_1.csv", summary.shape)
    print(top.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
