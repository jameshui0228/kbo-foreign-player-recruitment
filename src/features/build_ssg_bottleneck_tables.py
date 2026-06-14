#!/usr/bin/env python3
"""Build SSG batting bottleneck tables from STATIZ daily batting rows."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
BASE_BATTING_PATH = STATIZ_ROOT / "organized/players/players_day_batting.csv"
REFETCHED_2026_BATTING_PATH = STATIZ_ROOT / "organized/players/players_day_batting_2026_refetched.csv"

SSG_TEAM_CODE = 9002
OUTFIELD_POSITIONS = {7, 8, 9}

POSITIVE_METRICS = ["pa", "r", "rbi", "hr", "avg", "obp", "slg", "ops", "iso", "bb_pct"]
LOW_IS_BETTER_METRICS = ["k_pct"]


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def load_daily_batting() -> pd.DataFrame:
    batting = pd.read_csv(BASE_BATTING_PATH, low_memory=False)
    if REFETCHED_2026_BATTING_PATH.exists():
        refetched_2026 = pd.read_csv(REFETCHED_2026_BATTING_PATH, low_memory=False)
        batting = pd.concat(
            [
                batting[~batting["request_year"].eq(2026)],
                refetched_2026,
            ],
            ignore_index=True,
            sort=False,
        )
    games = pd.read_csv(
        STATIZ_ROOT / "organized/games/games_schedule.csv",
        usecols=["s_no", "year", "leagueType_name", "state_name"],
    )
    batting = batting.merge(games, on="s_no", how="left", suffixes=("", "_game"))
    batting = batting[batting["leagueType_name"].eq("정규시즌")].copy()
    batting["year"] = batting["year"].fillna(batting["request_year"])
    batting = to_numeric(
        batting,
        [
            "year",
            "p_no",
            "t_code",
            "battingOrder",
            "position",
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
        ],
    )
    for column in ["PA", "AB", "H", "2B", "3B", "HR", "BB", "HP", "SF", "SO", "TB", "R", "RBI", "SB"]:
        batting[column] = batting[column].fillna(0)
    return batting


def add_split_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["position_group"] = np.select(
        [
            out["position"].isin(OUTFIELD_POSITIONS),
            out["position"].eq(10),
            out["position"].eq(11),
            out["position"].between(2, 6, inclusive="both"),
        ],
        ["OF", "DH", "PH", "IF_C"],
        default="other",
    )
    out["lineup_group"] = np.select(
        [
            out["battingOrder"].between(1, 2, inclusive="both"),
            out["battingOrder"].between(3, 5, inclusive="both"),
            out["battingOrder"].between(6, 9, inclusive="both"),
        ],
        ["1-2_table_setters", "3-5_run_production", "6-9_lower_lineup"],
        default="bench_or_pinch",
    )
    out["of_lineup_group"] = np.where(
        out["position"].isin(OUTFIELD_POSITIONS),
        "OF_" + out["lineup_group"],
        "non_OF",
    )
    return out


def aggregate_batting(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    agg = (
        df.groupby(group_cols, dropna=False)
        .agg(
            games=("s_no", "nunique"),
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
    return agg


def add_ranks(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    rank_group = ["year", "split_type", "split_value"]
    for metric in POSITIVE_METRICS:
        out[f"{metric}_rank"] = out.groupby(rank_group)[metric].rank(method="min", ascending=False)
    for metric in LOW_IS_BETTER_METRICS:
        out[f"{metric}_rank"] = out.groupby(rank_group)[metric].rank(method="min", ascending=True)
    out["team_count_in_split"] = out.groupby(rank_group)["t_code"].transform("nunique")
    return out


def build_team_splits(batting: pd.DataFrame) -> pd.DataFrame:
    split_frames = []
    for split_type, split_col in [
        ("position_group", "position_group"),
        ("lineup_group", "lineup_group"),
        ("of_lineup_group", "of_lineup_group"),
    ]:
        agg = aggregate_batting(batting, ["year", "t_code", "t_code_name", split_col])
        agg = agg.rename(columns={split_col: "split_value"})
        agg["split_type"] = split_type
        split_frames.append(agg)
    all_team = aggregate_batting(batting, ["year", "t_code", "t_code_name"])
    all_team["split_type"] = "team_total"
    all_team["split_value"] = "all"
    split_frames.append(all_team)
    splits = pd.concat(split_frames, ignore_index=True)
    splits = add_ranks(splits)
    return splits.sort_values(["year", "split_type", "split_value", "ops_rank", "t_code_name"])


def build_ssg_of_players(batting: pd.DataFrame) -> pd.DataFrame:
    of = batting[(batting["t_code"].eq(SSG_TEAM_CODE)) & (batting["position"].isin(OUTFIELD_POSITIONS))].copy()
    lineup_names = pd.read_csv(
        STATIZ_ROOT / "organized/games/games_lineup.csv",
        usecols=["s_no", "p_no", "p_name"],
    )
    lineup_names["year"] = (pd.to_numeric(lineup_names["s_no"], errors="coerce") // 10000).astype("Int64")
    name_map = (
        lineup_names.dropna(subset=["year", "p_no", "p_name"])
        .groupby(["year", "p_no"])["p_name"]
        .agg(lambda values: values.mode().iloc[0] if not values.mode().empty else values.iloc[0])
        .reset_index()
    )
    name_map["year"] = pd.to_numeric(name_map["year"], errors="coerce")
    name_map["p_no"] = pd.to_numeric(name_map["p_no"], errors="coerce")
    player = aggregate_batting(of, ["year", "p_no"])
    player = player.merge(name_map, on=["year", "p_no"], how="left")
    player["team_of_pa_share"] = player["pa"] / player.groupby("year")["pa"].transform("sum")
    player = player.sort_values(["year", "pa"], ascending=[True, False])
    return player[
        [
            "year",
            "p_no",
            "p_name",
            "games",
            "pa",
            "team_of_pa_share",
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
            "r",
            "rbi",
            "sb",
        ]
    ]


def build_signal_crosswalk(splits: pd.DataFrame, message_candidates: pd.DataFrame) -> pd.DataFrame:
    ssg = splits[
        (splits["t_code"].eq(SSG_TEAM_CODE))
        & (splits["year"].between(2023, 2025))
        & (splits["split_type"].eq("position_group"))
        & (splits["split_value"].eq("OF"))
    ].copy()
    means = ssg[
        [
            "hr_rank",
            "iso_rank",
            "ops_rank",
            "obp_rank",
            "bb_pct_rank",
            "k_pct_rank",
            "r_rank",
            "rbi_rank",
        ]
    ].mean(numeric_only=True)

    candidate_counts = dict(
        zip(message_candidates["candidate_signal"], message_candidates["article_count"])
    )
    rows = [
        {
            "signal": "power",
            "text_article_count": int(candidate_counts.get("power", 0)),
            "statiz_evidence": (
                f"SSG OF HR rank avg {means['hr_rank']:.1f}, ISO rank avg {means['iso_rank']:.1f}; "
                f"this does not support a simple power-shortage message."
            ),
            "status": "mixed_or_reframed",
            "next_question": "Is power failing to convert into OBP/run creation rather than being absent?",
        },
        {
            "signal": "run_creation",
            "text_article_count": int(candidate_counts.get("run_creation", 0)),
            "statiz_evidence": (
                f"SSG OF OPS rank avg {means['ops_rank']:.1f}, R rank avg {means['r_rank']:.1f}, "
                f"RBI rank avg {means['rbi_rank']:.1f}."
            ),
            "status": "supported_for_deeper_split",
            "next_question": "Which lineup slots or player types create the conversion bottleneck?",
        },
        {
            "signal": "onbase_discipline",
            "text_article_count": int(candidate_counts.get("onbase_discipline", 0)),
            "statiz_evidence": (
                f"SSG OF OBP rank avg {means['obp_rank']:.1f}, BB% rank avg {means['bb_pct_rank']:.1f}, "
                f"K% rank avg {means['k_pct_rank']:.1f}."
            ),
            "status": "strong_candidate",
            "next_question": "Should the replacement OF prioritize zone discipline/BB retention over raw HR only?",
        },
        {
            "signal": "foreign_hitter",
            "text_article_count": int(candidate_counts.get("foreign_hitter", 0)),
            "statiz_evidence": "Text strongly links the issue to foreign-player context; quantitative check requires current roster/foreign-player PA split.",
            "status": "needs_roster_context",
            "next_question": "How much of SSG OF production depends on current foreign hitter availability?",
        },
        {
            "signal": "outfield",
            "text_article_count": int(candidate_counts.get("outfield", 0)),
            "statiz_evidence": "SSG OF is a valid split with full 2023-2025 rank coverage; current first-priority role is measurable.",
            "status": "supported_as_role_scope",
            "next_question": "Should candidate pool be strict OF only or OF/DH with flaw maskability?",
        },
        {
            "signal": "injury_depth",
            "text_article_count": int(candidate_counts.get("injury_depth", 0)),
            "statiz_evidence": "Daily batting can measure PA concentration, but injury-days data is not yet attached.",
            "status": "pending_external_injury_context",
            "next_question": "Use news tags plus PA concentration to identify depth/absence risk.",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    batting = add_split_labels(load_daily_batting())
    splits = build_team_splits(batting)
    ssg_splits = splits[splits["t_code"].eq(SSG_TEAM_CODE)].copy()
    ssg_players = build_ssg_of_players(batting)

    message_path = OUTPUT_DIR / "ssg_message_candidates_from_text.csv"
    if message_path.exists():
        message_candidates = pd.read_csv(message_path)
        crosswalk = build_signal_crosswalk(splits, message_candidates)
    else:
        crosswalk = pd.DataFrame()

    splits.to_csv(OUTPUT_DIR / "kbo_team_batting_splits_from_day.csv", index=False)
    ssg_splits.to_csv(OUTPUT_DIR / "ssg_batting_bottleneck_by_split.csv", index=False)
    ssg_players.to_csv(OUTPUT_DIR / "ssg_of_player_contributions.csv", index=False)
    crosswalk.to_csv(OUTPUT_DIR / "ssg_text_quant_signal_crosswalk.csv", index=False)

    print("wrote", OUTPUT_DIR / "kbo_team_batting_splits_from_day.csv")
    print("wrote", OUTPUT_DIR / "ssg_batting_bottleneck_by_split.csv")
    print("wrote", OUTPUT_DIR / "ssg_of_player_contributions.csv")
    print("wrote", OUTPUT_DIR / "ssg_text_quant_signal_crosswalk.csv")
    print(crosswalk.to_string(index=False))


if __name__ == "__main__":
    main()
