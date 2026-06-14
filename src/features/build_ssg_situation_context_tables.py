#!/usr/bin/env python3
"""Build SSG 2026 player-situation context tables.

STATIZ playerSituation is player-level, not position-at-PA-level. This script
therefore classifies each SSG batter by his actual 2026 daily PA usage first,
then attaches the player's cumulative situation splits.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
SITUATION_PATH = STATIZ_ROOT / "organized/player_situations/ssg_player_situation_batting_2026_refetched.csv"
BATTING_CONTEXT_PATH = OUTPUT_DIR / "kbo_2026_batting_with_context.csv"

OUTFIELD_ROLE_GROUPS = {"OF_1-2_table_setters", "OF_3-5_run_production", "OF_6-9_lower_lineup"}
FOCUS_SPLITS = {
    "Home",
    "Away",
    "risp",
    "2_out_risp",
    "runner_on_base",
    "no_runner",
    "tied_game",
    "within_one_run",
    "within_two_run",
    "late",
    "vs_right",
    "vs_left",
    "vs_right_orthdodx",
    "vs_right_under",
    "0B_2S",
    "1B_2S",
    "2B_2S",
    "3B_2S",
    "2B_0S",
    "3B_0S",
    "3B_1S",
}
NUMERIC_COLUMNS = [
    "PA",
    "AB",
    "R",
    "H",
    "1B",
    "2B",
    "3B",
    "HR",
    "TB",
    "RBI",
    "BB",
    "IB",
    "HP",
    "SO",
    "GDP",
    "SH",
    "SF",
    "SB",
    "CS",
]


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def aggregate_stats(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    work = to_numeric(df.copy(), NUMERIC_COLUMNS)
    for column in NUMERIC_COLUMNS:
        if column not in work.columns:
            work[column] = 0
        work[column] = work[column].fillna(0)
    agg = (
        work.groupby(group_cols, dropna=False)
        .agg(
            players=("query_p_no", "nunique"),
            pa=("PA", "sum"),
            ab=("AB", "sum"),
            r=("R", "sum"),
            h=("H", "sum"),
            doubles=("2B", "sum"),
            triples=("3B", "sum"),
            hr=("HR", "sum"),
            tb=("TB", "sum"),
            rbi=("RBI", "sum"),
            bb=("BB", "sum"),
            hbp=("HP", "sum"),
            so=("SO", "sum"),
            gdp=("GDP", "sum"),
            sf=("SF", "sum"),
            sb=("SB", "sum"),
        )
        .reset_index()
    )
    obp_den = agg["ab"] + agg["bb"] + agg["hbp"] + agg["sf"]
    agg["avg"] = agg["h"] / agg["ab"].replace(0, np.nan)
    agg["obp"] = (agg["h"] + agg["bb"] + agg["hbp"]) / obp_den.replace(0, np.nan)
    agg["slg"] = agg["tb"] / agg["ab"].replace(0, np.nan)
    agg["ops"] = agg["obp"] + agg["slg"]
    agg["iso"] = agg["slg"] - agg["avg"]
    agg["bb_pct"] = agg["bb"] / agg["pa"].replace(0, np.nan)
    agg["k_pct"] = agg["so"] / agg["pa"].replace(0, np.nan)
    agg["hr_per_pa"] = agg["hr"] / agg["pa"].replace(0, np.nan)
    agg["rbi_per_pa"] = agg["rbi"] / agg["pa"].replace(0, np.nan)
    return agg


def build_player_role_context() -> pd.DataFrame:
    batting = pd.read_csv(BATTING_CONTEXT_PATH, low_memory=False)
    batting = batting[batting["t_code_name"].eq("SSG")].copy()
    batting["PA"] = pd.to_numeric(batting["PA"], errors="coerce").fillna(0)
    grouped = (
        batting.groupby(["p_no", "p_name"], dropna=False)
        .agg(
            total_pa=("PA", "sum"),
            games=("s_no", "nunique"),
            of_pa=("PA", lambda values: values[batting.loc[values.index, "position_group"].eq("OF")].sum()),
            dh_pa=("PA", lambda values: values[batting.loc[values.index, "position_group"].eq("DH")].sum()),
            ifc_pa=("PA", lambda values: values[batting.loc[values.index, "position_group"].eq("IF_C")].sum()),
            of_12_pa=("PA", lambda values: values[batting.loc[values.index, "role_group"].eq("OF_1-2_table_setters")].sum()),
            of_35_pa=("PA", lambda values: values[batting.loc[values.index, "role_group"].eq("OF_3-5_run_production")].sum()),
            of_69_pa=("PA", lambda values: values[batting.loc[values.index, "role_group"].eq("OF_6-9_lower_lineup")].sum()),
        )
        .reset_index()
    )
    grouped["of_high_leverage_pa"] = grouped["of_12_pa"] + grouped["of_35_pa"]
    grouped["of_pa_share"] = grouped["of_pa"] / grouped["total_pa"].replace(0, np.nan)
    grouped["dh_pa_share"] = grouped["dh_pa"] / grouped["total_pa"].replace(0, np.nan)
    grouped["of_high_leverage_share_of_of"] = grouped["of_high_leverage_pa"] / grouped["of_pa"].replace(0, np.nan)

    conditions = [
        grouped["of_pa"].ge(25) & grouped["of_high_leverage_share_of_of"].ge(0.50),
        grouped["of_pa"].ge(25),
        grouped["dh_pa"].ge(25),
        grouped["ifc_pa"].ge(25),
    ]
    choices = [
        "OF_high_leverage_usage",
        "OF_lower_or_mixed_usage",
        "DH_primary_or_bridge",
        "IF_C_core",
    ]
    grouped["role_segment"] = np.select(conditions, choices, default="depth_other")
    grouped["replacement_relevant"] = grouped["role_segment"].isin(
        ["OF_high_leverage_usage", "OF_lower_or_mixed_usage", "DH_primary_or_bridge"]
    )
    return grouped.sort_values(["role_segment", "total_pa"], ascending=[True, False])


def classify_count(label: str) -> str:
    match = re.match(r"^([0-3])B_([0-2])S$", str(label))
    if not match:
        return "other_count"
    balls, strikes = int(match.group(1)), int(match.group(2))
    if strikes == 2:
        return "two_strikes"
    if balls == 3 or (balls >= 2 and strikes == 0):
        return "hitter_count"
    if strikes > balls:
        return "pitcher_count"
    return "neutral_count"


def add_split_family(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["split_family"] = out["bucket_group"]
    out.loc[out["query_si"].eq(3) & out["bucket_group"].eq("situation"), "split_family"] = "score_context"
    out.loc[out["query_si"].eq(3) & out["bucket_group"].eq("runner"), "split_family"] = "runner_context"
    out.loc[out["query_si"].eq(3) & out["bucket_group"].eq("inning"), "split_family"] = "inning_context"
    out.loc[out["query_si"].eq(4) & out["bucket_group"].eq("ballCount"), "split_family"] = "terminal_count"
    out.loc[out["query_si"].eq(4) & out["bucket_group"].eq("after_ballCount"), "split_family"] = "after_count"
    out.loc[out["query_si"].eq(5) & out["bucket_group"].eq("type"), "split_family"] = "pitcher_type"
    return out


def build_flags(summary: pd.DataFrame) -> pd.DataFrame:
    focus = summary[
        summary["split_label"].isin(FOCUS_SPLITS)
        & summary["role_segment"].isin(
            ["OF_high_leverage_usage", "OF_lower_or_mixed_usage", "DH_primary_or_bridge"]
        )
        & summary["pa"].ge(15)
    ].copy()
    focus["context_need_score"] = (
        (focus["pa"] / 50).clip(upper=3)
        + ((0.320 - focus["obp"]).clip(lower=0) * 5)
        + ((0.700 - focus["ops"]).clip(lower=0) * 2)
        + ((focus["k_pct"] - 0.230).clip(lower=0) * 3)
    )
    focus["candidate_screen_hint"] = np.select(
        [
            focus["split_label"].str.contains("vs_right", na=False),
            focus["split_label"].isin(["risp", "2_out_risp", "runner_on_base"]),
            focus["split_label"].isin(["tied_game", "within_one_run", "within_two_run"]),
            focus["split_label"].isin(["0B_2S", "1B_2S", "2B_2S", "3B_2S"]),
            focus["split_label"].eq("Away"),
        ],
        [
            "screen_for_RHP_damage_with_OBP",
            "screen_for_runner_context_run_conversion",
            "screen_for_close_game_plate_quality",
            "screen_for_two_strike_contact_survival",
            "screen_for_road_stability",
        ],
        default="screen_for_context_stability",
    )
    keep = [
        "role_segment",
        "split_family",
        "split_label",
        "bucket_path",
        "players",
        "pa",
        "hr",
        "bb",
        "so",
        "avg",
        "obp",
        "slg",
        "ops",
        "iso",
        "bb_pct",
        "k_pct",
        "hr_per_pa",
        "rbi_per_pa",
        "context_need_score",
        "candidate_screen_hint",
    ]
    return focus[keep].sort_values(["context_need_score", "pa"], ascending=[False, False])


def build_player_focus(merged: pd.DataFrame) -> pd.DataFrame:
    focus = merged[
        merged["split_label"].isin(FOCUS_SPLITS)
        & merged["role_segment"].isin(
            ["OF_high_leverage_usage", "OF_lower_or_mixed_usage", "DH_primary_or_bridge"]
        )
        & merged["PA"].ge(5)
    ].copy()
    player = aggregate_stats(
        focus,
        ["query_p_no", "p_name", "role_segment", "split_family", "split_label", "bucket_path"],
    )
    player["context_need_score"] = (
        (player["pa"] / 30).clip(upper=3)
        + ((0.320 - player["obp"]).clip(lower=0) * 5)
        + ((0.700 - player["ops"]).clip(lower=0) * 2)
        + ((player["k_pct"] - 0.230).clip(lower=0) * 3)
    )
    return player.sort_values(["context_need_score", "pa"], ascending=[False, False])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    situation = pd.read_csv(SITUATION_PATH, low_memory=False)
    situation = to_numeric(situation, ["query_p_no", "query_year", "query_si", *NUMERIC_COLUMNS])
    situation = situation[situation["query_year"].eq(2026) & situation["PA"].gt(0)].copy()
    situation = add_split_family(situation)
    roles = build_player_role_context()
    merged = situation.merge(
        roles,
        left_on="query_p_no",
        right_on="p_no",
        how="left",
        suffixes=("", "_role"),
    )

    role_summary = aggregate_stats(
        merged,
        ["role_segment", "replacement_relevant", "split_family", "query_si", "si_name", "bucket_group", "split_label", "bucket_path"],
    )
    count_rows = merged[
        merged["split_family"].eq("terminal_count")
        & merged["bucket_path"].astype(str).str.startswith("ballCount/0/")
    ].copy()
    count_rows["count_class"] = count_rows["split_label"].map(classify_count)
    count_class = aggregate_stats(count_rows, ["role_segment", "replacement_relevant", "count_class"])

    flags = build_flags(role_summary)
    player_focus = build_player_focus(merged)

    roles.to_csv(OUTPUT_DIR / "ssg_2026_player_role_context.csv", index=False)
    role_summary.to_csv(OUTPUT_DIR / "ssg_2026_situation_role_splits.csv", index=False)
    count_class.to_csv(OUTPUT_DIR / "ssg_2026_situation_count_class_splits.csv", index=False)
    flags.to_csv(OUTPUT_DIR / "ssg_2026_replacement_context_flags.csv", index=False)
    player_focus.to_csv(OUTPUT_DIR / "ssg_2026_player_situation_focus.csv", index=False)

    print("wrote", OUTPUT_DIR / "ssg_2026_player_role_context.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_situation_role_splits.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_situation_count_class_splits.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_replacement_context_flags.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_player_situation_focus.csv")
    print(flags.head(25).to_string(index=False))


if __name__ == "__main__":
    main()
