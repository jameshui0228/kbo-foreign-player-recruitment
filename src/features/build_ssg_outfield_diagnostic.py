#!/usr/bin/env python3
"""Build the first SSG outfield/power-gap diagnostic from STATIZ snapshot."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

SSG_TEAM_CODE = 9002
OUTFIELD_POSITIONS = {7, 8, 9}


def _to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def _rank_within_year(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        out[f"{column}_rank"] = out.groupby("year")[column].rank(
            method="min",
            ascending=False,
        )
    return out


def build_team_batting_rank() -> pd.DataFrame:
    teams = pd.read_csv(STATIZ_ROOT / "feature/core/teams_season_strength.csv")
    teams = _to_numeric(
        teams,
        [
            "year",
            "t_code",
            "team_bat_avg",
            "team_bat_obp",
            "team_bat_slg",
            "team_bat_ops",
            "team_bat_pa",
            "team_bat_r",
            "team_bat_hr",
            "team_bat_war",
            "team_bat_bb",
            "team_bat_so",
        ],
    )
    teams["team_bat_iso"] = teams["team_bat_slg"] - teams["team_bat_avg"]
    teams["team_bat_k_pct"] = teams["team_bat_so"] / teams["team_bat_pa"]
    teams["team_bat_bb_pct"] = teams["team_bat_bb"] / teams["team_bat_pa"]
    rank_cols = [
        "team_bat_ops",
        "team_bat_slg",
        "team_bat_iso",
        "team_bat_hr",
        "team_bat_war",
        "team_bat_r",
        "team_bat_bb_pct",
    ]
    ranked = _rank_within_year(teams, rank_cols)
    return ranked.sort_values(["year", "team_bat_ops_rank", "t_code_name"])


def build_outfield_batting() -> pd.DataFrame:
    batting = pd.read_csv(STATIZ_ROOT / "organized/players/players_season_basic_batting.csv")
    batting = _to_numeric(
        batting,
        [
            "year",
            "t_code",
            "p_position",
            "G",
            "PA",
            "AB",
            "H",
            "2B",
            "3B",
            "HR",
            "BB",
            "HP",
            "SF",
            "SO",
            "TB",
            "R",
            "RBI",
            "SB",
            "WAR",
            "WAROff",
            "WARDef",
            "wRCplus",
        ],
    )
    of = batting[batting["p_position"].isin(OUTFIELD_POSITIONS)].copy()
    group_cols = ["year", "t_code", "t_code_name"]
    agg = (
        of.groupby(group_cols, dropna=False)
        .agg(
            players=("p_no", "nunique"),
            pa=("PA", "sum"),
            ab=("AB", "sum"),
            h=("H", "sum"),
            doubles=("2B", "sum"),
            triples=("3B", "sum"),
            hr=("HR", "sum"),
            bb=("BB", "sum"),
            hbp=("HP", "sum"),
            sf=("SF", "sum"),
            so=("SO", "sum"),
            tb=("TB", "sum"),
            r=("R", "sum"),
            rbi=("RBI", "sum"),
            sb=("SB", "sum"),
            war=("WAR", "sum"),
            war_off=("WAROff", "sum"),
            war_def=("WARDef", "sum"),
        )
        .reset_index()
    )
    agg["avg"] = agg["h"] / agg["ab"]
    agg["obp"] = (agg["h"] + agg["bb"] + agg["hbp"]) / (
        agg["ab"] + agg["bb"] + agg["hbp"] + agg["sf"]
    )
    agg["slg"] = agg["tb"] / agg["ab"]
    agg["ops"] = agg["obp"] + agg["slg"]
    agg["iso"] = agg["slg"] - agg["avg"]
    agg["k_pct"] = agg["so"] / agg["pa"]
    agg["bb_pct"] = agg["bb"] / agg["pa"]

    # PA-weighted wRC+ by team outfield group.
    weighted = of.assign(wrc_weight=of["wRCplus"] * of["PA"]).groupby(group_cols, dropna=False)
    weighted_wrc = (weighted["wrc_weight"].sum() / weighted["PA"].sum()).rename("wrc_plus_pa_weighted")
    agg = agg.merge(weighted_wrc.reset_index(), on=group_cols, how="left")

    rank_cols = ["ops", "slg", "iso", "hr", "war", "war_off", "wrc_plus_pa_weighted", "bb_pct"]
    source_team_count = agg.groupby("year")["t_code"].nunique().rename("source_team_count")
    agg = agg.merge(source_team_count.reset_index(), on="year", how="left")
    agg["coverage_status"] = agg["source_team_count"].where(
        agg["source_team_count"] >= 8,
        "incomplete_year_excluded_from_rank",
    )
    agg.loc[agg["source_team_count"] >= 8, "coverage_status"] = "rankable"

    rankable = agg[agg["source_team_count"] >= 8].copy()
    incomplete = agg[agg["source_team_count"] < 8].copy()
    rankable = _rank_within_year(rankable, rank_cols)
    for column in rank_cols:
        incomplete[f"{column}_rank"] = np.nan
    agg = pd.concat([rankable, incomplete], ignore_index=True)
    return agg.sort_values(["year", "ops_rank", "t_code_name"])


def build_ssg_gap_summary(team_rank: pd.DataFrame, of_rank: pd.DataFrame) -> pd.DataFrame:
    team_ssg = team_rank[team_rank["t_code"] == SSG_TEAM_CODE].copy()
    of_ssg = of_rank[of_rank["t_code"] == SSG_TEAM_CODE].copy()
    rows = []
    for year in sorted(set(team_ssg["year"]).intersection(of_ssg["year"])):
        team_row = team_ssg[team_ssg["year"] == year].iloc[0]
        of_row = of_ssg[of_ssg["year"] == year].iloc[0]
        league_of = of_rank[of_rank["year"] == year]
        rows.append(
            {
                "year": int(year),
                "team_ops": team_row["team_bat_ops"],
                "team_ops_rank": int(team_row["team_bat_ops_rank"]),
                "team_slg": team_row["team_bat_slg"],
                "team_slg_rank": int(team_row["team_bat_slg_rank"]),
                "team_iso": team_row["team_bat_iso"],
                "team_iso_rank": int(team_row["team_bat_iso_rank"]),
                "team_hr": int(team_row["team_bat_hr"]),
                "team_hr_rank": int(team_row["team_bat_hr_rank"]),
                "of_pa": int(of_row["pa"]),
                "of_ops": of_row["ops"],
                "of_ops_rank": int(of_row["ops_rank"]),
                "of_slg": of_row["slg"],
                "of_slg_rank": int(of_row["slg_rank"]),
                "of_iso": of_row["iso"],
                "of_iso_rank": int(of_row["iso_rank"]),
                "of_hr": int(of_row["hr"]),
                "of_hr_rank": int(of_row["hr_rank"]),
                "of_wrc_plus_pa_weighted": of_row["wrc_plus_pa_weighted"],
                "of_wrc_plus_rank": int(of_row["wrc_plus_pa_weighted_rank"]),
                "of_ops_vs_lg_avg": of_row["ops"] - league_of["ops"].mean(),
                "of_iso_vs_lg_avg": of_row["iso"] - league_of["iso"].mean(),
                "of_hr_vs_lg_avg": of_row["hr"] - league_of["hr"].mean(),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    team_rank = build_team_batting_rank()
    of_rank = build_outfield_batting()
    gap = build_ssg_gap_summary(team_rank, of_rank)

    team_rank.to_csv(OUTPUT_DIR / "kbo_team_batting_rank_2023_2026.csv", index=False)
    of_rank.to_csv(OUTPUT_DIR / "kbo_team_outfield_batting_2023_2026.csv", index=False)
    gap.to_csv(OUTPUT_DIR / "ssg_outfield_gap_summary.csv", index=False)

    print("wrote", OUTPUT_DIR / "kbo_team_batting_rank_2023_2026.csv")
    print("wrote", OUTPUT_DIR / "kbo_team_outfield_batting_2023_2026.csv")
    print("wrote", OUTPUT_DIR / "ssg_outfield_gap_summary.csv")
    print(gap.to_string(index=False))


if __name__ == "__main__":
    main()
