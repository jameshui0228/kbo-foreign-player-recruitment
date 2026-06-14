#!/usr/bin/env python3
"""Build 2026 SSG context signals beyond offense/defense totals.

This script joins STATIZ daily batting rows with game context from the schedule
table, then searches for hidden splits by home/away, month, weather, rest,
opponent, lineup role, and positional role.
"""

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
SSG_TEAM_NAME = "SSG"
OUTFIELD_POSITIONS = {7, 8, 9}


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    return num / den.replace(0, np.nan)


def metric_aggregate(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
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
    agg["avg"] = safe_div(agg["h"], agg["ab"])
    agg["obp"] = safe_div(agg["h"] + agg["bb"] + agg["hbp"], obp_den)
    agg["slg"] = safe_div(agg["tb"], agg["ab"])
    agg["ops"] = agg["obp"] + agg["slg"]
    agg["iso"] = agg["slg"] - agg["avg"]
    agg["bb_pct"] = safe_div(agg["bb"], agg["pa"])
    agg["k_pct"] = safe_div(agg["so"], agg["pa"])
    agg["hr_pa"] = safe_div(agg["hr"], agg["pa"])
    agg["r_pa"] = safe_div(agg["r"], agg["pa"])
    agg["rbi_pa"] = safe_div(agg["rbi"], agg["pa"])
    return agg


def load_team_game_context() -> pd.DataFrame:
    schedule = pd.read_csv(STATIZ_ROOT / "organized/games/games_schedule.csv")
    schedule = schedule[
        schedule["leagueType_name"].eq("정규시즌")
        & schedule["state_name"].eq("경기 종료")
        & schedule["year"].eq(2026)
    ].copy()
    schedule["game_dt"] = pd.to_datetime(schedule["gameDate_kst"], errors="coerce")
    schedule = to_numeric(
        schedule,
        [
            "s_no",
            "awayTeam",
            "homeTeam",
            "awayScore",
            "homeScore",
            "temperature",
            "humidity",
            "windSpeed",
        ],
    )

    away = schedule.assign(
        t_code=schedule["awayTeam"],
        t_code_name=schedule["awayTeam_name"],
        opponent_code=schedule["homeTeam"],
        opponent_name=schedule["homeTeam_name"],
        home_away="away",
        team_score=schedule["awayScore"],
        opp_score=schedule["homeScore"],
    )
    home = schedule.assign(
        t_code=schedule["homeTeam"],
        t_code_name=schedule["homeTeam_name"],
        opponent_code=schedule["awayTeam"],
        opponent_name=schedule["awayTeam_name"],
        home_away="home",
        team_score=schedule["homeScore"],
        opp_score=schedule["awayScore"],
    )
    games = pd.concat([away, home], ignore_index=True)
    games["win"] = (games["team_score"] > games["opp_score"]).astype(int)
    games["run_diff"] = games["team_score"] - games["opp_score"]
    games["month"] = games["game_dt"].dt.month.astype("Int64").astype(str).str.zfill(2)
    games["weekday"] = games["game_dt"].dt.day_name()
    games["is_weekend"] = games["weekday"].isin(["Saturday", "Sunday"]).astype(int)
    games["temp_bucket"] = pd.cut(
        games["temperature"],
        bins=[-np.inf, 15, 20, 25, np.inf],
        labels=["cold_<=15", "cool_15_20", "mild_20_25", "warm_25+"],
    ).astype(str)
    games["humidity_bucket"] = pd.cut(
        games["humidity"],
        bins=[-np.inf, 40, 60, np.inf],
        labels=["dry_<=40", "normal_40_60", "humid_60+"],
    ).astype(str)
    games["wind_bucket"] = pd.cut(
        games["windSpeed"],
        bins=[-np.inf, 1, 3, np.inf],
        labels=["calm_<=1", "wind_1_3", "wind_3+"],
    ).astype(str)

    games = games.sort_values(["t_code", "game_dt", "s_no"])
    games["prev_game_dt"] = games.groupby("t_code")["game_dt"].shift(1)
    games["days_since_prev"] = (games["game_dt"] - games["prev_game_dt"]).dt.days
    games["rest_bucket"] = np.select(
        [
            games["days_since_prev"].isna(),
            games["days_since_prev"] <= 1,
            games["days_since_prev"] == 2,
            games["days_since_prev"] >= 3,
        ],
        ["first_game", "back_to_back", "one_day_rest", "two_plus_days_rest"],
        default="unknown",
    )
    games["prev_home_away"] = games.groupby("t_code")["home_away"].shift(1)
    games["home_away_switch"] = (
        games["prev_home_away"].notna() & games["prev_home_away"].ne(games["home_away"])
    ).astype(int)

    return games[
        [
            "s_no",
            "year",
            "game_dt",
            "t_code",
            "t_code_name",
            "opponent_name",
            "home_away",
            "team_score",
            "opp_score",
            "win",
            "run_diff",
            "month",
            "weekday",
            "is_weekend",
            "weather_name",
            "temperature",
            "humidity",
            "windSpeed",
            "temp_bucket",
            "humidity_bucket",
            "wind_bucket",
            "days_since_prev",
            "rest_bucket",
            "home_away_switch",
        ]
    ]


def add_role_labels(df: pd.DataFrame) -> pd.DataFrame:
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
    out["role_group"] = np.where(
        out["position_group"].eq("OF"),
        "OF_" + out["lineup_group"],
        out["position_group"],
    )
    return out


def load_batting_with_context() -> pd.DataFrame:
    if REFETCHED_2026_BATTING_PATH.exists():
        batting = pd.read_csv(REFETCHED_2026_BATTING_PATH, low_memory=False)
    else:
        batting = pd.read_csv(BASE_BATTING_PATH, low_memory=False)
    context = load_team_game_context()
    batting = batting.merge(context, on=["s_no", "t_code", "t_code_name"], how="inner")
    batting = to_numeric(
        batting,
        [
            "p_no",
            "t_code",
            "battingOrder",
            "position",
            "PA",
            "AB",
            "H",
            "1B",
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
    for column in ["PA", "AB", "H", "1B", "2B", "3B", "HR", "BB", "HP", "SF", "SO", "TB", "R", "RBI", "SB"]:
        batting[column] = batting[column].fillna(0)
    return add_role_labels(batting)


def add_context_ranks(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for metric in ["ops", "obp", "slg", "iso", "bb_pct", "hr_pa", "r_pa", "rbi_pa"]:
        out[f"{metric}_rank"] = out.groupby(group_cols)[metric].rank(method="min", ascending=False)
    out["k_pct_rank"] = out.groupby(group_cols)["k_pct"].rank(method="min", ascending=True)
    out["team_count"] = out.groupby(group_cols)["t_code"].transform("nunique")
    return out


def build_league_context_ranks(batting: pd.DataFrame) -> pd.DataFrame:
    frames = []
    context_cols = [
        "home_away",
        "month",
        "temp_bucket",
        "humidity_bucket",
        "wind_bucket",
        "rest_bucket",
        "opponent_name",
        "is_weekend",
    ]
    role_cols = ["position_group", "role_group", "lineup_group"]
    for context_col in context_cols:
        for role_col in role_cols:
            agg = metric_aggregate(batting, [context_col, role_col, "t_code", "t_code_name"])
            agg = agg.rename(columns={context_col: "context_value", role_col: "role_value"})
            agg["context_type"] = context_col
            agg["role_type"] = role_col
            agg = add_context_ranks(agg, ["context_type", "context_value", "role_type", "role_value"])
            frames.append(agg)
    return pd.concat(frames, ignore_index=True)


def build_ssg_context_summary(batting: pd.DataFrame, league_ranks: pd.DataFrame) -> pd.DataFrame:
    ssg = league_ranks[league_ranks["t_code"].eq(SSG_TEAM_CODE)].copy()
    ssg = ssg[(ssg["pa"] >= 15) & (ssg["team_count"] >= 6)].copy()
    ssg["hidden_signal"] = ""
    ssg.loc[
        (ssg["iso_rank"] <= 3) & (ssg["ops_rank"] >= 5),
        "hidden_signal",
    ] = "power_without_full_run_value"
    ssg.loc[
        (ssg["ops_rank"] >= 8) | (ssg["obp_rank"] >= 8) | (ssg["slg_rank"] >= 8) | (ssg["k_pct_rank"] >= 8),
        "hidden_signal",
    ] = np.where(
        ssg.loc[
            (ssg["ops_rank"] >= 8) | (ssg["obp_rank"] >= 8) | (ssg["slg_rank"] >= 8) | (ssg["k_pct_rank"] >= 8),
            "hidden_signal",
        ].eq(""),
        "contextual_weakness",
        ssg.loc[
            (ssg["ops_rank"] >= 8) | (ssg["obp_rank"] >= 8) | (ssg["slg_rank"] >= 8) | (ssg["k_pct_rank"] >= 8),
            "hidden_signal",
        ] + "+contextual_weakness",
    )
    ssg.loc[
        (ssg["bb_pct_rank"] <= 3) & (ssg["ops_rank"] >= 7),
        "hidden_signal",
    ] = np.where(
        ssg.loc[(ssg["bb_pct_rank"] <= 3) & (ssg["ops_rank"] >= 7), "hidden_signal"].eq(""),
        "walks_not_converting_to_damage",
        ssg.loc[(ssg["bb_pct_rank"] <= 3) & (ssg["ops_rank"] >= 7), "hidden_signal"]
        + "+walks_not_converting_to_damage",
    )
    return ssg[ssg["hidden_signal"].ne("")].sort_values(
        ["role_type", "role_value", "context_type", "context_value"]
    )


def build_ssg_player_context(batting: pd.DataFrame) -> pd.DataFrame:
    lineup_names = pd.read_csv(
        STATIZ_ROOT / "organized/games/games_lineup.csv",
        usecols=["s_no", "p_no", "p_name"],
    ).drop_duplicates()
    ssg = batting[batting["t_code"].eq(SSG_TEAM_CODE)].copy()
    if "p_name" not in ssg.columns:
        ssg = ssg.merge(lineup_names, on=["s_no", "p_no"], how="left")
    else:
        ssg = ssg.merge(lineup_names, on=["s_no", "p_no"], how="left", suffixes=("", "_lineup"))
        ssg["p_name"] = ssg["p_name"].fillna(ssg["p_name_lineup"])
        ssg = ssg.drop(columns=["p_name_lineup"])
    frames = []
    for context_col in ["month", "home_away", "role_group"]:
        agg = metric_aggregate(ssg, [context_col, "p_no", "p_name"])
        agg = agg.rename(columns={context_col: "context_value"})
        agg["context_type"] = context_col
        frames.append(agg)
    return pd.concat(frames, ignore_index=True).sort_values(["context_type", "context_value", "pa"], ascending=[True, True, False])


def build_narrative_candidates(league_ranks: pd.DataFrame) -> pd.DataFrame:
    rows = []
    ssg = league_ranks[league_ranks["t_code"].eq(SSG_TEAM_CODE)].copy()

    def pick(context_type: str, context_value: str, role_type: str, role_value: str) -> pd.Series | None:
        sub = ssg[
            ssg["context_type"].eq(context_type)
            & ssg["context_value"].astype(str).eq(str(context_value))
            & ssg["role_type"].eq(role_type)
            & ssg["role_value"].eq(role_value)
        ]
        return None if sub.empty else sub.iloc[0]

    candidates = [
        ("DH_slot_collapse", "home_away", "home", "position_group", "DH"),
        ("DH_slot_collapse", "home_away", "away", "position_group", "DH"),
        ("OF_table_setter_mismatch", "home_away", "home", "role_group", "OF_1-2_table_setters"),
        ("OF_table_setter_mismatch", "home_away", "away", "role_group", "OF_1-2_table_setters"),
        ("OF_middle_order_mismatch", "home_away", "home", "role_group", "OF_3-5_run_production"),
        ("OF_middle_order_mismatch", "home_away", "away", "role_group", "OF_3-5_run_production"),
        ("May_OF_slump", "month", "05", "position_group", "OF"),
        ("June_OF_rebound", "month", "06", "position_group", "OF"),
        ("back_to_back_role_stress", "rest_bucket", "back_to_back", "role_group", "OF_3-5_run_production"),
        ("humid_game_signal", "humidity_bucket", "humid_60+", "position_group", "OF"),
    ]
    for label, context_type, context_value, role_type, role_value in candidates:
        row = pick(context_type, context_value, role_type, role_value)
        if row is None:
            continue
        rows.append(
            {
                "candidate": label,
                "context_type": context_type,
                "context_value": context_value,
                "role_type": role_type,
                "role_value": role_value,
                "pa": row["pa"],
                "ops": row["ops"],
                "ops_rank": row["ops_rank"],
                "obp": row["obp"],
                "obp_rank": row["obp_rank"],
                "slg": row["slg"],
                "slg_rank": row["slg_rank"],
                "iso": row["iso"],
                "iso_rank": row["iso_rank"],
                "bb_pct": row["bb_pct"],
                "bb_pct_rank": row["bb_pct_rank"],
                "k_pct": row["k_pct"],
                "k_pct_rank": row["k_pct_rank"],
                "team_count": row["team_count"],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    batting = load_batting_with_context()
    league_ranks = build_league_context_ranks(batting)
    hidden = build_ssg_context_summary(batting, league_ranks)
    player_context = build_ssg_player_context(batting)
    narrative = build_narrative_candidates(league_ranks)

    batting.to_csv(OUTPUT_DIR / "kbo_2026_batting_with_context.csv", index=False)
    league_ranks.to_csv(OUTPUT_DIR / "kbo_2026_context_role_ranks.csv", index=False)
    hidden.to_csv(OUTPUT_DIR / "ssg_2026_hidden_context_signals.csv", index=False)
    player_context.to_csv(OUTPUT_DIR / "ssg_2026_player_context_splits.csv", index=False)
    narrative.to_csv(OUTPUT_DIR / "ssg_2026_narrative_context_candidates.csv", index=False)

    print("wrote", OUTPUT_DIR / "kbo_2026_batting_with_context.csv")
    print("wrote", OUTPUT_DIR / "kbo_2026_context_role_ranks.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_hidden_context_signals.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_player_context_splits.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_narrative_context_candidates.csv")
    print(narrative.to_string(index=False))


if __name__ == "__main__":
    main()
