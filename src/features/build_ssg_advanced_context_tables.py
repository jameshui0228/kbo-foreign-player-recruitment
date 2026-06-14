#!/usr/bin/env python3
"""Build advanced 2026 SSG context tables.

Adds variables that are more roster- and game-context aware than broad
offense/defense totals: opponent starter handedness, hitter handedness,
humidity-month interaction, and game result by outfield run contribution.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
SSG_TEAM_NAME = "SSG"


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def aggregate_batting(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    num_cols = ["PA", "AB", "H", "2B", "3B", "HR", "BB", "HP", "SF", "SO", "TB", "R", "RBI", "SB"]
    df = to_numeric(df, num_cols)
    for column in num_cols:
        df[column] = df[column].fillna(0)
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


def add_ranks(df: pd.DataFrame, rank_group_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for metric in ["ops", "obp", "slg", "iso", "bb_pct"]:
        out[f"{metric}_rank"] = out.groupby(rank_group_cols)[metric].rank(method="min", ascending=False)
    out["k_pct_rank"] = out.groupby(rank_group_cols)["k_pct"].rank(method="min", ascending=True)
    out["team_count"] = out.groupby(rank_group_cols)["t_code"].transform("nunique")
    return out


def build_context_frame() -> pd.DataFrame:
    batting = pd.read_csv(OUTPUT_DIR / "kbo_2026_batting_with_context.csv", low_memory=False)
    schedule = pd.read_csv(STATIZ_ROOT / "organized/games/games_schedule.csv", low_memory=False)
    lineup = pd.read_csv(STATIZ_ROOT / "organized/games/games_lineup.csv", low_memory=False)

    starters = lineup[
        pd.to_numeric(lineup["s_no"], errors="coerce").between(20260000, 20269999)
        & lineup["position"].eq(1)
    ][["s_no", "t_code", "p_no", "p_name", "p_throw_name"]].drop_duplicates()

    team_games = []
    games = schedule[
        schedule["year"].eq(2026)
        & schedule["leagueType_name"].eq("정규시즌")
        & schedule["state_name"].eq("경기 종료")
    ].copy()
    for _, row in games.iterrows():
        s_no = int(row["s_no"])
        entries = [
            (int(row["awayTeam"]), int(row["homeTeam"]), row["homeTeam_name"]),
            (int(row["homeTeam"]), int(row["awayTeam"]), row["awayTeam_name"]),
        ]
        for team_code, opp_code, opp_name in entries:
            opp_starter = starters[starters["s_no"].eq(s_no) & starters["t_code"].eq(opp_code)]
            team_games.append(
                {
                    "s_no": s_no,
                    "t_code": team_code,
                    "opponent_name": opp_name,
                    "opp_sp_throw_name": None if opp_starter.empty else opp_starter["p_throw_name"].iloc[0],
                }
            )

    hitter_hands = lineup[
        pd.to_numeric(lineup["s_no"], errors="coerce").between(20260000, 20269999)
    ][["p_no", "p_bat_name"]].dropna().drop_duplicates("p_no")
    return batting.merge(pd.DataFrame(team_games), on=["s_no", "t_code", "opponent_name"], how="left").merge(
        hitter_hands,
        on="p_no",
        how="left",
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    batting = build_context_frame()

    role_hand = aggregate_batting(batting, ["opp_sp_throw_name", "role_group", "t_code", "t_code_name"])
    role_hand = add_ranks(role_hand, ["opp_sp_throw_name", "role_group"])
    ssg_role_hand = role_hand[
        role_hand["t_code_name"].eq(SSG_TEAM_NAME)
        & role_hand["role_group"].astype(str).str.startswith("OF")
        & role_hand["pa"].ge(30)
    ].sort_values(["role_group", "opp_sp_throw_name"])

    ssg_of = batting[batting["t_code_name"].eq(SSG_TEAM_NAME) & batting["position_group"].eq("OF")].copy()
    hitter_hand = aggregate_batting(ssg_of, ["p_bat_name", "role_group"]).sort_values(
        ["role_group", "pa"],
        ascending=[True, False],
    )
    humidity_month = aggregate_batting(ssg_of, ["month", "humidity_bucket"]).sort_values(["month", "humidity_bucket"])

    ssg = batting[batting["t_code_name"].eq(SSG_TEAM_NAME)].copy()
    team_game = ssg.drop_duplicates("s_no")[
        ["s_no", "game_dt", "home_away", "opponent_name", "team_score", "opp_score", "win", "month", "humidity_bucket"]
    ]
    of_game = aggregate_batting(ssg[ssg["position_group"].eq("OF")], ["s_no"])[
        ["s_no", "pa", "h", "tb", "hr", "bb", "so", "r", "rbi"]
    ]
    team_result = team_game.merge(of_game, on="s_no", how="left").fillna(
        {"pa": 0, "h": 0, "tb": 0, "hr": 0, "bb": 0, "so": 0, "r": 0, "rbi": 0}
    )
    team_result["of_rbi_bucket"] = pd.cut(
        team_result["rbi"],
        bins=[-1, 0, 2, 99],
        labels=["OF_RBI_0", "OF_RBI_1_2", "OF_RBI_3+"],
    )
    result_by_bucket = (
        team_result.groupby("of_rbi_bucket", dropna=False)
        .agg(
            games=("s_no", "nunique"),
            wins=("win", "sum"),
            team_runs=("team_score", "mean"),
            opp_runs=("opp_score", "mean"),
            of_pa=("pa", "mean"),
            of_hr=("hr", "sum"),
            of_rbi=("rbi", "sum"),
        )
        .reset_index()
    )
    result_by_bucket["win_pct"] = result_by_bucket["wins"] / result_by_bucket["games"]

    ssg_role_hand.to_csv(OUTPUT_DIR / "ssg_2026_of_role_by_opponent_starter_hand.csv", index=False)
    hitter_hand.to_csv(OUTPUT_DIR / "ssg_2026_of_hitter_hand_role_splits.csv", index=False)
    humidity_month.to_csv(OUTPUT_DIR / "ssg_2026_of_humidity_month_splits.csv", index=False)
    result_by_bucket.to_csv(OUTPUT_DIR / "ssg_2026_team_result_by_of_rbi_bucket.csv", index=False)

    print("wrote", OUTPUT_DIR / "ssg_2026_of_role_by_opponent_starter_hand.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_of_hitter_hand_role_splits.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_of_humidity_month_splits.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_team_result_by_of_rbi_bucket.csv")
    print(ssg_role_hand.to_string(index=False))
    print(result_by_bucket.to_string(index=False))


if __name__ == "__main__":
    main()
