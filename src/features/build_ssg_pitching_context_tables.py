#!/usr/bin/env python3
"""Build SSG 2026 pitching context tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
BASE_PITCHING = STATIZ_ROOT / "organized/players/players_day_pitching.csv"
REFETCHED_SSG_PITCHING = STATIZ_ROOT / "organized/players/players_day_pitching_2026_ssg_refetched.csv"
SCHEDULE = STATIZ_ROOT / "organized/games/games_schedule.csv"
ROSTER = STATIZ_ROOT / "organized/players/players_roster_daily.csv"

IMPORT_SLOT_NAMES = {"베니지아노", "타케다", "긴지로", "화이트"}
NUMERIC_COLUMNS = ["AB", "BB", "ER", "G", "GDP", "GS", "H", "HD", "HP", "HR", "IP", "NP", "OBP", "OPS", "R", "SF", "SLG", "SO", "TB", "TBF", "W", "WHIP"]


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def ip_to_outs(value: Any) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value)
    if "." not in text:
        return float(int(float(text)) * 3)
    whole, frac = text.split(".", 1)
    frac = frac[:1]
    return float(int(whole) * 3 + int(frac or 0))


def outs_to_ip(outs: pd.Series) -> pd.Series:
    whole = (outs // 3).astype("Int64")
    rem = (outs % 3).astype("Int64")
    return whole.astype(str) + "." + rem.astype(str)


def load_pitching() -> pd.DataFrame:
    base = pd.read_csv(BASE_PITCHING, low_memory=False)
    base["s_no_filled"] = pd.to_numeric(base["s_no"].fillna(base["record_key"]), errors="coerce")
    if REFETCHED_SSG_PITCHING.exists():
        refetched = pd.read_csv(REFETCHED_SSG_PITCHING, low_memory=False)
        refetched["s_no_filled"] = pd.to_numeric(refetched["s_no"].fillna(refetched["record_key"]), errors="coerce")
        base = pd.concat(
            [
                base[~(base["request_year"].eq(2026) & base["t_code_name"].eq("SSG"))],
                refetched,
            ],
            ignore_index=True,
            sort=False,
        )
    roster = pd.read_csv(ROSTER, low_memory=False)
    name_map = roster[["p_no", "name"]].dropna().drop_duplicates("p_no")
    base = base.merge(name_map, on="p_no", how="left")
    base["p_name"] = base["p_name"].fillna(base["name"])
    base = to_numeric(base, ["s_no_filled", "request_year", "p_no", "t_code", *NUMERIC_COLUMNS])
    base["outs"] = base["IP"].map(ip_to_outs)
    base["pitch_role"] = np.where(base["GS"].fillna(0).gt(0), "starter", "bullpen")
    base["import_slot_group"] = np.where(base["p_name"].isin(IMPORT_SLOT_NAMES), "import_slot_pitcher", "domestic_pitcher")
    return base


def add_game_context(pitching: pd.DataFrame) -> pd.DataFrame:
    games = pd.read_csv(SCHEDULE, low_memory=False)
    games = games[
        games["year"].eq(2026)
        & games["leagueType_name"].eq("정규시즌")
        & games["state_name"].eq("경기 종료")
    ].copy()
    rows = []
    for _, game in games.iterrows():
        s_no = int(game["s_no"])
        for side in ["away", "home"]:
            if side == "away":
                team_code, team_name = int(game["awayTeam"]), game["awayTeam_name"]
                opp_code, opp_name = int(game["homeTeam"]), game["homeTeam_name"]
                team_score, opp_score = game["awayScore"], game["homeScore"]
                home_away = "away"
            else:
                team_code, team_name = int(game["homeTeam"]), game["homeTeam_name"]
                opp_code, opp_name = int(game["awayTeam"]), game["awayTeam_name"]
                team_score, opp_score = game["homeScore"], game["awayScore"]
                home_away = "home"
            rows.append(
                {
                    "s_no_filled": s_no,
                    "game_dt": str(game["gameDate_kst"])[:10],
                    "t_code": team_code,
                    "t_code_name": team_name,
                    "opponent_code": opp_code,
                    "opponent_name": opp_name,
                    "home_away": home_away,
                    "team_score": team_score,
                    "opp_score": opp_score,
                    "win": int(float(team_score) > float(opp_score)),
                    "temperature": game.get("temperature"),
                    "humidity": game.get("humidity"),
                    "weather_name": game.get("weather_name"),
                    "month": game.get("month"),
                }
            )
    context = pd.DataFrame(rows)
    out = pitching.merge(context, on=["s_no_filled", "t_code", "t_code_name"], how="inner")
    return out[out["request_year"].eq(2026)].copy()


def aggregate_pitching(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    work = df.copy()
    work = to_numeric(work, NUMERIC_COLUMNS + ["outs"])
    for column in ["AB", "BB", "ER", "GDP", "H", "HP", "HR", "R", "SF", "SO", "TB", "TBF", "NP", "outs"]:
        work[column] = work[column].fillna(0)
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
            gdp=("GDP", "sum"),
        )
        .reset_index()
    )
    agg["ip"] = agg["outs"] / 3
    agg["era"] = agg["er"] * 27 / agg["outs"].replace(0, np.nan)
    agg["ra9"] = agg["r"] * 27 / agg["outs"].replace(0, np.nan)
    agg["whip"] = (agg["h"] + agg["bb"]) * 3 / agg["outs"].replace(0, np.nan)
    agg["k9"] = agg["so"] * 27 / agg["outs"].replace(0, np.nan)
    agg["bb9"] = agg["bb"] * 27 / agg["outs"].replace(0, np.nan)
    agg["hr9"] = agg["hr"] * 27 / agg["outs"].replace(0, np.nan)
    agg["kbb"] = agg["so"] / agg["bb"].replace(0, np.nan)
    obp_den = agg["ab"] + agg["bb"] + agg["hbp"] + agg["sf"]
    agg["avg_allowed"] = agg["h"] / agg["ab"].replace(0, np.nan)
    agg["obp_allowed"] = (agg["h"] + agg["bb"] + agg["hbp"]) / obp_den.replace(0, np.nan)
    agg["slg_allowed"] = agg["tb"] / agg["ab"].replace(0, np.nan)
    agg["ops_allowed"] = agg["obp_allowed"] + agg["slg_allowed"]
    agg["ip_per_game"] = agg["ip"] / agg["games"].replace(0, np.nan)
    agg["outs_per_start"] = agg["outs"] / agg["starts"].replace(0, np.nan)
    agg["pitches_per_ip"] = agg["np"] / agg["ip"].replace(0, np.nan)
    return agg


def add_team_role_ranks(role: pd.DataFrame) -> pd.DataFrame:
    out = role.copy()
    rank_group = ["pitch_role"]
    for metric in ["era", "ra9", "whip", "bb9", "hr9", "avg_allowed", "obp_allowed", "slg_allowed", "ops_allowed"]:
        out[f"{metric}_rank"] = out.groupby(rank_group)[metric].rank(method="min", ascending=True)
    for metric in ["ip_per_game", "outs_per_start", "k9", "kbb"]:
        out[f"{metric}_rank"] = out.groupby(rank_group)[metric].rank(method="min", ascending=False)
    out["team_count"] = out.groupby(rank_group)["t_code_name"].transform("nunique")
    return out


def build_team_role_table(pitching: pd.DataFrame) -> pd.DataFrame:
    role = aggregate_pitching(pitching, ["pitch_role", "t_code", "t_code_name"])
    total = aggregate_pitching(pitching, ["t_code", "t_code_name"])
    total["pitch_role"] = "total"
    combined = pd.concat([role, total], ignore_index=True, sort=False)
    return add_team_role_ranks(combined)


def build_ssg_game_workload(pitching: pd.DataFrame) -> pd.DataFrame:
    ssg = pitching[pitching["t_code_name"].eq("SSG")].copy()
    starter = aggregate_pitching(ssg[ssg["pitch_role"].eq("starter")], ["s_no_filled", "game_dt", "opponent_name", "home_away", "team_score", "opp_score", "win"])
    starter = starter.rename(columns={column: f"starter_{column}" for column in starter.columns if column not in ["s_no_filled", "game_dt", "opponent_name", "home_away", "team_score", "opp_score", "win"]})
    bullpen = aggregate_pitching(ssg[ssg["pitch_role"].eq("bullpen")], ["s_no_filled"])
    bullpen = bullpen.rename(columns={column: f"bullpen_{column}" for column in bullpen.columns if column != "s_no_filled"})
    out = starter.merge(bullpen, on="s_no_filled", how="left")
    out["starter_short_lt5"] = out["starter_outs"].lt(15)
    out["starter_quality_6ip_3er"] = out["starter_outs"].ge(18) & out["starter_er"].le(3)
    out["starter_disaster"] = out["starter_er"].ge(5) | out["starter_outs"].lt(12)
    out["bullpen_ip_after_start"] = out["bullpen_outs"] / 3
    out["team_margin"] = pd.to_numeric(out["team_score"], errors="coerce") - pd.to_numeric(out["opp_score"], errors="coerce")
    return out.sort_values("s_no_filled")


def build_ssg_pitcher_summary(pitching: pd.DataFrame) -> pd.DataFrame:
    ssg = pitching[pitching["t_code_name"].eq("SSG")].copy()
    summary = aggregate_pitching(ssg, ["p_no", "p_name", "pitch_role", "import_slot_group"])
    starts = ssg[ssg["pitch_role"].eq("starter")].copy()
    start_flags = starts.assign(
        short_lt5=starts["outs"].lt(15),
        quality_6ip_3er=starts["outs"].ge(18) & starts["ER"].le(3),
        disaster=starts["ER"].ge(5) | starts["outs"].lt(12),
    )
    flags = (
        start_flags.groupby(["p_no", "pitch_role"], dropna=False)
        .agg(
            short_starts=("short_lt5", "sum"),
            quality_starts=("quality_6ip_3er", "sum"),
            disaster_starts=("disaster", "sum"),
        )
        .reset_index()
    )
    summary = summary.merge(flags, on=["p_no", "pitch_role"], how="left")
    for column in ["short_starts", "quality_starts", "disaster_starts"]:
        summary[column] = summary[column].fillna(0).astype(int)
    summary["short_start_rate"] = summary["short_starts"] / summary["starts"].replace(0, np.nan)
    summary["quality_start_rate"] = summary["quality_starts"] / summary["starts"].replace(0, np.nan)
    summary["disaster_start_rate"] = summary["disaster_starts"] / summary["starts"].replace(0, np.nan)
    return summary.sort_values(["pitch_role", "ip"], ascending=[False, False])


def build_import_slot_impact(pitching: pd.DataFrame) -> pd.DataFrame:
    ssg = pitching[pitching["t_code_name"].eq("SSG")].copy()
    return aggregate_pitching(ssg, ["import_slot_group", "pitch_role"]).sort_values(["pitch_role", "import_slot_group"])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pitching = add_game_context(load_pitching())
    team_role = build_team_role_table(pitching)
    ssg_team_role = team_role[team_role["t_code_name"].eq("SSG")].sort_values("pitch_role")
    game_workload = build_ssg_game_workload(pitching)
    pitcher_summary = build_ssg_pitcher_summary(pitching)
    import_impact = build_import_slot_impact(pitching)

    pitching.to_csv(OUTPUT_DIR / "kbo_2026_pitching_with_context.csv", index=False)
    team_role.to_csv(OUTPUT_DIR / "kbo_2026_team_pitching_role_ranks.csv", index=False)
    ssg_team_role.to_csv(OUTPUT_DIR / "ssg_2026_team_pitching_role_ranks.csv", index=False)
    game_workload.to_csv(OUTPUT_DIR / "ssg_2026_game_pitching_workload.csv", index=False)
    pitcher_summary.to_csv(OUTPUT_DIR / "ssg_2026_pitcher_summary.csv", index=False)
    import_impact.to_csv(OUTPUT_DIR / "ssg_2026_import_slot_pitching_impact.csv", index=False)

    print("wrote", OUTPUT_DIR / "ssg_2026_team_pitching_role_ranks.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_game_pitching_workload.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_pitcher_summary.csv")
    print("wrote", OUTPUT_DIR / "ssg_2026_import_slot_pitching_impact.csv")
    print(ssg_team_role[["pitch_role", "games", "starts", "ip", "era", "whip", "ops_allowed", "ip_per_game", "outs_per_start", "era_rank", "whip_rank", "ops_allowed_rank", "ip_per_game_rank", "outs_per_start_rank"]].to_string(index=False))
    print()
    print(import_impact[["import_slot_group", "pitch_role", "games", "starts", "ip", "era", "whip", "ops_allowed", "short_starts" if "short_starts" in import_impact.columns else "games"]].to_string(index=False))


if __name__ == "__main__":
    main()
