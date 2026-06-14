#!/usr/bin/env python3
"""Build tables for SSG-specific recruitment message development."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"


def build_runway_gap() -> pd.DataFrame:
    team = pd.read_csv(OUTPUT_DIR / "kbo_2026_team_situation_ranks.csv")
    metrics = ["OPS", "OBP", "SLG", "AVG", "HR", "RBI", "GDP", "PA", "bb_pct", "k_pct"]
    wide = team.pivot_table(
        index=["t_code", "t_code_name"],
        columns="context_label",
        values=metrics,
        aggfunc="first",
    )
    wide.columns = [f"{metric}_{context}" for metric, context in wide.columns]
    wide = wide.reset_index()
    wide["risp_minus_on_first_ops"] = wide["OPS_risp"] - wide["OPS_on_first"]
    wide["risp_minus_on_first_obp"] = wide["OBP_risp"] - wide["OBP_on_first"]
    wide["on_first_gdp_per_pa"] = wide["GDP_on_first"] / wide["PA_on_first"]
    wide["on_first_hr_per_pa"] = wide["HR_on_first"] / wide["PA_on_first"]
    wide["risp_ops_rank"] = wide["OPS_risp"].rank(method="min", ascending=False)
    wide["on_first_ops_rank"] = wide["OPS_on_first"].rank(method="min", ascending=False)
    wide["on_first_obp_rank"] = wide["OBP_on_first"].rank(method="min", ascending=False)
    wide["risp_to_on_first_gap_rank"] = wide["risp_minus_on_first_ops"].rank(method="min", ascending=False)
    wide["on_first_gdp_per_pa_rank_high"] = wide["on_first_gdp_per_pa"].rank(method="min", ascending=False)
    keep = [
        "t_code",
        "t_code_name",
        "OPS_risp",
        "risp_ops_rank",
        "OPS_on_first",
        "on_first_ops_rank",
        "OBP_on_first",
        "on_first_obp_rank",
        "risp_minus_on_first_ops",
        "risp_minus_on_first_obp",
        "risp_to_on_first_gap_rank",
        "GDP_on_first",
        "PA_on_first",
        "on_first_gdp_per_pa",
        "on_first_gdp_per_pa_rank_high",
        "HR_on_first",
        "on_first_hr_per_pa",
    ]
    return wide[keep].sort_values("risp_minus_on_first_ops", ascending=False)


def build_role_runway() -> pd.DataFrame:
    role = pd.read_csv(OUTPUT_DIR / "ssg_2026_situation_role_splits.csv")
    labels = ["on_first", "lt2_out_on_first", "runner_on_base", "risp"]
    segments = ["IF_C_core", "OF_high_leverage_usage", "OF_lower_or_mixed_usage", "DH_primary_or_bridge"]
    table = role[role["split_label"].isin(labels) & role["role_segment"].isin(segments)].copy()
    table["gdp_per_pa"] = table["gdp"] / table["pa"].replace(0, pd.NA)
    keep = [
        "role_segment",
        "split_label",
        "players",
        "pa",
        "h",
        "hr",
        "rbi",
        "gdp",
        "gdp_per_pa",
        "avg",
        "obp",
        "slg",
        "ops",
        "bb_pct",
        "k_pct",
        "rbi_per_pa",
    ]
    return table[keep].sort_values(["split_label", "role_segment"])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    runway_gap = build_runway_gap()
    role_runway = build_role_runway()
    runway_gap.to_csv(OUTPUT_DIR / "ssg_2026_runway_gap_by_team.csv", index=False)
    role_runway.to_csv(OUTPUT_DIR / "ssg_2026_role_runway_context.csv", index=False)
    print("wrote", OUTPUT_DIR / "ssg_2026_runway_gap_by_team.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_role_runway_context.csv")
    print(runway_gap.to_string(index=False))
    print()
    print(role_runway.to_string(index=False))


if __name__ == "__main__":
    main()
