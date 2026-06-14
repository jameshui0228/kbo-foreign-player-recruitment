#!/usr/bin/env python3
"""Validate the pitcher-first SSG hidden-need message.

This script checks whether the run_008 pitcher message is stable enough to
drive candidate scoring:

1. time stability across 2026 months;
2. game-result impact of short/disaster starts;
3. contextual concentration of bad pitching ranks.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
PITCHING_PATH = OUTPUT_DIR / "kbo_2026_pitching_with_context.csv"
WORKLOAD_PATH = OUTPUT_DIR / "ssg_2026_game_pitching_workload.csv"
SITUATION_RANK_PATH = OUTPUT_DIR / "kbo_2026_team_pitching_situation_ranks.csv"
RUN008_MESSAGE_PATH = OUTPUT_DIR / "ssg_hidden_state_message_candidates_v0_1.csv"


def numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = 0
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def aggregate_pitching(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    work = numeric(
        df,
        ["outs", "ER", "R", "H", "HR", "BB", "HP", "SO", "TB", "AB", "SF", "TBF", "NP", "GS"],
    )
    for col in ["outs", "ER", "R", "H", "HR", "BB", "HP", "SO", "TB", "AB", "SF", "TBF", "NP", "GS"]:
        work[col] = work[col].fillna(0)
    agg = (
        work.groupby(group_cols, dropna=False)
        .agg(
            games=("s_no_filled", "nunique"),
            appearances=("p_no", "count"),
            pitchers=("p_no", "nunique"),
            starts=("GS", "sum"),
            outs=("outs", "sum"),
            er=("ER", "sum"),
            r=("R", "sum"),
            h=("H", "sum"),
            hr=("HR", "sum"),
            bb=("BB", "sum"),
            hbp=("HP", "sum"),
            so=("SO", "sum"),
            tb=("TB", "sum"),
            ab=("AB", "sum"),
            sf=("SF", "sum"),
            tbf=("TBF", "sum"),
            np=("NP", "sum"),
        )
        .reset_index()
    )
    agg["ip"] = agg["outs"] / 3
    agg["era"] = agg["er"] * 27 / agg["outs"].replace(0, np.nan)
    agg["ra9"] = agg["r"] * 27 / agg["outs"].replace(0, np.nan)
    agg["whip"] = (agg["h"] + agg["bb"]) * 3 / agg["outs"].replace(0, np.nan)
    agg["bb9"] = agg["bb"] * 27 / agg["outs"].replace(0, np.nan)
    agg["hr9"] = agg["hr"] * 27 / agg["outs"].replace(0, np.nan)
    agg["k9"] = agg["so"] * 27 / agg["outs"].replace(0, np.nan)
    agg["kbb"] = agg["so"] / agg["bb"].replace(0, np.nan)
    obp_den = agg["ab"] + agg["bb"] + agg["hbp"] + agg["sf"]
    agg["obp_allowed"] = (agg["h"] + agg["bb"] + agg["hbp"]) / obp_den.replace(0, np.nan)
    agg["slg_allowed"] = agg["tb"] / agg["ab"].replace(0, np.nan)
    agg["ops_allowed"] = agg["obp_allowed"] + agg["slg_allowed"]
    agg["outs_per_start"] = agg["outs"] / agg["starts"].replace(0, np.nan)
    agg["ip_per_game"] = agg["ip"] / agg["games"].replace(0, np.nan)
    return agg


def add_monthly_ranks(monthly: pd.DataFrame) -> pd.DataFrame:
    out = monthly.copy()
    rank_group = ["month", "pitch_role"]
    for metric in ["era", "ra9", "whip", "bb9", "hr9", "obp_allowed", "slg_allowed", "ops_allowed"]:
        out[f"{metric}_rank"] = out.groupby(rank_group)[metric].rank(method="min", ascending=True)
    for metric in ["outs_per_start", "ip_per_game", "k9", "kbb"]:
        out[f"{metric}_rank"] = out.groupby(rank_group)[metric].rank(method="min", ascending=False)
    out["team_count"] = out.groupby(rank_group)["t_code_name"].transform("nunique")
    bad_rank_cols = [
        "era_rank",
        "whip_rank",
        "bb9_rank",
        "hr9_rank",
        "ops_allowed_rank",
        "outs_per_start_rank",
    ]
    out["bad_rank_points"] = 0.0
    for col in bad_rank_cols:
        out["bad_rank_points"] += ((out[col] - 1) / (out["team_count"] - 1)).clip(lower=0, upper=1).fillna(0)
    out["bottom_three_core_flag"] = (
        out[["era_rank", "whip_rank", "ops_allowed_rank", "outs_per_start_rank"]].ge(out["team_count"] - 2, axis=0).sum(axis=1)
        >= 2
    )
    return out


def build_monthly_validation() -> tuple[pd.DataFrame, pd.DataFrame]:
    pitching = pd.read_csv(PITCHING_PATH, low_memory=False)
    monthly = aggregate_pitching(pitching, ["month", "pitch_role", "t_code", "t_code_name"])
    ranked = add_monthly_ranks(monthly)
    ssg = ranked[ranked["t_code_name"].eq("SSG")].copy()
    summary = (
        ssg.groupby("pitch_role")
        .agg(
            months=("month", "nunique"),
            bottom_three_months=("bottom_three_core_flag", "sum"),
            mean_bad_rank_points=("bad_rank_points", "mean"),
            mean_era_rank=("era_rank", "mean"),
            mean_whip_rank=("whip_rank", "mean"),
            mean_ops_allowed_rank=("ops_allowed_rank", "mean"),
            mean_outs_per_start_rank=("outs_per_start_rank", "mean"),
            median_outs_per_start=("outs_per_start", "median"),
            total_ip=("ip", "sum"),
        )
        .reset_index()
    )
    summary["temporal_stability_flag"] = summary["bottom_three_months"].ge(2) | summary["mean_bad_rank_points"].ge(3.0)
    return ranked, summary


def summarize_flag(workload: pd.DataFrame, flag_col: str) -> dict[str, object]:
    work = workload.copy()
    work[flag_col] = work[flag_col].astype(bool)
    yes = work[work[flag_col]]
    no = work[~work[flag_col]]
    return {
        "signal": flag_col,
        "signal_games": len(yes),
        "non_signal_games": len(no),
        "signal_game_share": len(yes) / len(work) if len(work) else np.nan,
        "signal_win_rate": yes["win"].mean() if len(yes) else np.nan,
        "non_signal_win_rate": no["win"].mean() if len(no) else np.nan,
        "win_rate_delta_signal_minus_non": (yes["win"].mean() - no["win"].mean()) if len(yes) and len(no) else np.nan,
        "signal_avg_margin": yes["team_margin"].mean() if len(yes) else np.nan,
        "non_signal_avg_margin": no["team_margin"].mean() if len(no) else np.nan,
        "signal_avg_bullpen_ip": yes["bullpen_ip_after_start"].mean() if len(yes) else np.nan,
        "non_signal_avg_bullpen_ip": no["bullpen_ip_after_start"].mean() if len(no) else np.nan,
        "signal_avg_starter_outs": yes["starter_outs"].mean() if len(yes) else np.nan,
        "non_signal_avg_starter_outs": no["starter_outs"].mean() if len(no) else np.nan,
    }


def build_game_impact() -> pd.DataFrame:
    workload = pd.read_csv(WORKLOAD_PATH)
    workload["starter_5ip_plus"] = pd.to_numeric(workload["starter_outs"], errors="coerce").ge(15)
    workload["starter_6ip_plus"] = pd.to_numeric(workload["starter_outs"], errors="coerce").ge(18)
    workload["starter_er_4plus"] = pd.to_numeric(workload["starter_er"], errors="coerce").ge(4)
    workload["bullpen_5ip_plus"] = pd.to_numeric(workload["bullpen_ip_after_start"], errors="coerce").ge(5)
    rows = [
        summarize_flag(workload, flag)
        for flag in [
            "starter_short_lt5",
            "starter_disaster",
            "starter_quality_6ip_3er",
            "starter_5ip_plus",
            "starter_6ip_plus",
            "starter_er_4plus",
            "bullpen_5ip_plus",
        ]
    ]
    out = pd.DataFrame(rows)
    out["absolute_win_delta"] = out["win_rate_delta_signal_minus_non"].abs()
    out["game_impact_score"] = out["absolute_win_delta"].fillna(0) * out["signal_game_share"].fillna(0)
    out["direction"] = np.where(out["win_rate_delta_signal_minus_non"].lt(0), "hurts_win_rate", "helps_win_rate")
    return out.sort_values("game_impact_score", ascending=False)


def build_context_validation() -> pd.DataFrame:
    ranks = pd.read_csv(SITUATION_RANK_PATH)
    ssg = ranks[ranks["t_code_name"].eq("SSG")].copy()
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
    ssg["bad_context_score"] = 0.0
    for col in rank_cols:
        if col in ssg.columns:
            ssg["bad_context_score"] += ((ssg[col] - 1) / (ssg["team_count"] - 1)).clip(lower=0, upper=1).fillna(0)
    ssg["context_unit"] = ssg["context_family"].astype(str) + ":" + ssg["context_label"].astype(str)
    keep = [
        "context_unit",
        "context_family",
        "context_label",
        "G",
        "TBF",
        "IP",
        "ERA",
        "WHIP",
        "OPS",
        "era_calc",
        "whip_calc",
        "bb9",
        "hr9",
        "ERA_rank",
        "WHIP_rank",
        "OPS_rank",
        "OBP_rank",
        "bb9_rank",
        "hr9_rank",
        "bad_context_score",
    ]
    for col in keep:
        if col not in ssg.columns:
            ssg[col] = np.nan
    return ssg[keep].sort_values("bad_context_score", ascending=False)


def build_decision_table(monthly_summary: pd.DataFrame, game_impact: pd.DataFrame, context_validation: pd.DataFrame) -> pd.DataFrame:
    messages = pd.read_csv(RUN008_MESSAGE_PATH)
    pitcher_priority = messages[messages["slot"].eq("foreign_pitcher")]["message_priority_score"].max()
    starter_month = monthly_summary[monthly_summary["pitch_role"].eq("starter")]
    short = game_impact[game_impact["signal"].eq("starter_short_lt5")]
    disaster = game_impact[game_impact["signal"].eq("starter_disaster")]
    top_contexts = context_validation.head(8)

    rows = [
        {
            "criterion": "run008_signal_strength",
            "value": pitcher_priority,
            "threshold": ">= 50",
            "status": "pass" if pitcher_priority >= 50 else "watch",
            "note": "pitcher message should clearly outrank hitter message",
        },
        {
            "criterion": "starter_monthly_stability",
            "value": float(starter_month["bottom_three_months"].iloc[0]) if not starter_month.empty else np.nan,
            "threshold": ">= 2 bottom-three months",
            "status": "pass" if (not starter_month.empty and starter_month["temporal_stability_flag"].iloc[0]) else "watch",
            "note": "controls for one-month noise",
        },
        {
            "criterion": "short_start_win_rate_penalty",
            "value": float(short["win_rate_delta_signal_minus_non"].iloc[0]) if not short.empty else np.nan,
            "threshold": "<= -0.12",
            "status": "pass" if (not short.empty and short["win_rate_delta_signal_minus_non"].iloc[0] <= -0.12) else "watch",
            "note": "short starts should materially hurt game outcome",
        },
        {
            "criterion": "disaster_start_win_rate_penalty",
            "value": float(disaster["win_rate_delta_signal_minus_non"].iloc[0]) if not disaster.empty else np.nan,
            "threshold": "<= -0.20",
            "status": "pass" if (not disaster.empty and disaster["win_rate_delta_signal_minus_non"].iloc[0] <= -0.20) else "watch",
            "note": "disaster starts should separate wins from losses",
        },
        {
            "criterion": "context_concentration",
            "value": int((top_contexts["bad_context_score"] >= 7).sum()),
            "threshold": ">= 3 severe contexts",
            "status": "pass" if (top_contexts["bad_context_score"] >= 7).sum() >= 3 else "watch",
            "note": "bad ranks should concentrate in interpretable contexts",
        },
    ]
    out = pd.DataFrame(rows)
    out["overall_decision"] = "promote_pitcher_message_v0_2" if out["status"].eq("pass").sum() >= 4 else "keep_testing"
    return out


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    monthly, monthly_summary = build_monthly_validation()
    game_impact = build_game_impact()
    context_validation = build_context_validation()
    decision = build_decision_table(monthly_summary, game_impact, context_validation)

    monthly.to_csv(OUTPUT_DIR / "ssg_pitching_message_v0_2_monthly_role_ranks.csv", index=False)
    monthly_summary.to_csv(OUTPUT_DIR / "ssg_pitching_message_v0_2_monthly_summary.csv", index=False)
    game_impact.to_csv(OUTPUT_DIR / "ssg_pitching_message_v0_2_game_impact.csv", index=False)
    context_validation.to_csv(OUTPUT_DIR / "ssg_pitching_message_v0_2_context_validation.csv", index=False)
    decision.to_csv(OUTPUT_DIR / "ssg_pitching_message_v0_2_decision_table.csv", index=False)

    print("wrote", OUTPUT_DIR / "ssg_pitching_message_v0_2_monthly_role_ranks.csv", monthly.shape)
    print("wrote", OUTPUT_DIR / "ssg_pitching_message_v0_2_monthly_summary.csv", monthly_summary.shape)
    print("wrote", OUTPUT_DIR / "ssg_pitching_message_v0_2_game_impact.csv", game_impact.shape)
    print("wrote", OUTPUT_DIR / "ssg_pitching_message_v0_2_context_validation.csv", context_validation.shape)
    print("wrote", OUTPUT_DIR / "ssg_pitching_message_v0_2_decision_table.csv", decision.shape)
    print(decision.to_string(index=False))


if __name__ == "__main__":
    main()
