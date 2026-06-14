#!/usr/bin/env python3
"""Build Savant pitcher features for replacement-starter profile learning.

This table is for feature learning and screening. It does not yet account for
contract status, 40-man roster constraints, KBO willingness, or medical risk.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAVANT_DIR = PROJECT_ROOT / "data/processed/mlb_milb/savant"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

YEARS = [2022, 2023, 2024, 2025, 2026]
READ_COLUMNS = [
    "game_date",
    "game_year",
    "player_name",
    "pitcher",
    "events",
    "description",
    "type",
    "pitch_type",
    "release_speed",
    "zone",
    "balls",
    "strikes",
    "pitch_number",
    "launch_speed",
    "launch_angle",
    "estimated_woba_using_speedangle",
    "estimated_slg_using_speedangle",
    "woba_value",
    "woba_denom",
    "launch_speed_angle",
    "bb_type",
    "game_pk",
    "inning",
    "outs_when_up",
    "on_1b",
    "on_2b",
    "on_3b",
    "n_thruorder_pitcher",
]

SWING_DESCRIPTIONS = {
    "swinging_strike",
    "swinging_strike_blocked",
    "foul",
    "foul_tip",
    "foul_bunt",
    "bunt_foul_tip",
    "missed_bunt",
    "hit_into_play",
}
WHIFF_DESCRIPTIONS = {"swinging_strike", "swinging_strike_blocked", "missed_bunt"}
HIT_EVENTS = {"single", "double", "triple", "home_run"}
WALK_EVENTS = {"walk", "intent_walk"}


def safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    return num / den.replace(0, np.nan)


def rank_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    if series.notna().sum() <= 1:
        return pd.Series(np.nan, index=series.index)
    pct = series.rank(pct=True, ascending=True)
    if not higher_is_better:
        pct = 1 - pct
    return pct * 100


def load_year(year: int) -> pd.DataFrame:
    path = SAVANT_DIR / f"savant_statcast_{year}.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_parquet(path, columns=READ_COLUMNS)


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in ["events", "description", "pitch_type", "type", "player_name"]:
        out[column] = out[column].fillna("")
    for column in [
        "pitcher",
        "zone",
        "balls",
        "strikes",
        "pitch_number",
        "launch_speed",
        "launch_angle",
        "estimated_woba_using_speedangle",
        "estimated_slg_using_speedangle",
        "woba_value",
        "woba_denom",
        "launch_speed_angle",
        "game_pk",
        "inning",
        "outs_when_up",
        "n_thruorder_pitcher",
    ]:
        out[column] = pd.to_numeric(out[column], errors="coerce")

    out["pitch"] = 1
    out["pa"] = ((out["events"] != "") & (out["events"] != "truncated_pa")).astype(int)
    out["hit"] = out["events"].isin(HIT_EVENTS).astype(int)
    out["walk"] = out["events"].isin(WALK_EVENTS).astype(int)
    out["hbp"] = out["events"].eq("hit_by_pitch").astype(int)
    out["strikeout"] = out["events"].str.contains("strikeout", na=False).astype(int)
    out["home_run"] = out["events"].eq("home_run").astype(int)
    out["swing"] = out["description"].isin(SWING_DESCRIPTIONS).astype(int)
    out["whiff"] = out["description"].isin(WHIFF_DESCRIPTIONS).astype(int)
    out["zone_pitch"] = out["zone"].between(1, 9, inclusive="both").astype(int)
    out["out_zone_pitch"] = ((out["zone"].notna()) & (~out["zone"].between(1, 9, inclusive="both"))).astype(int)
    out["chase_swing"] = ((out["swing"].eq(1)) & out["out_zone_pitch"].eq(1)).astype(int)
    out["first_pitch"] = out["pitch_number"].eq(1).astype(int)
    out["first_pitch_nonball"] = ((out["first_pitch"].eq(1)) & out["type"].isin(["S", "X"])).astype(int)
    out["three_ball_pitch"] = out["balls"].eq(3).astype(int)
    out["bbe"] = (
        out["launch_speed"].notna()
        & out["launch_angle"].notna()
        & out["description"].eq("hit_into_play")
    ).astype(int)
    out["hardhit"] = ((out["bbe"].eq(1)) & (out["launch_speed"] >= 95)).astype(int)
    out["barrel"] = ((out["bbe"].eq(1)) & (pd.to_numeric(out["launch_speed_angle"], errors="coerce") == 6)).astype(int)

    out["early_1_3"] = out["inning"].le(3).astype(int)
    out["runner_on_base"] = (out[["on_1b", "on_2b", "on_3b"]].notna().any(axis=1)).astype(int)
    out["risp"] = (out[["on_2b", "on_3b"]].notna().any(axis=1)).astype(int)
    out["third_time"] = out["n_thruorder_pitcher"].ge(3).astype(int)

    out["woba_num"] = out["woba_value"].where(out["pa"].eq(1), 0).fillna(0)
    out["woba_den"] = out["woba_denom"].where(out["pa"].eq(1), 0).fillna(0)
    out["xwoba_num"] = out["estimated_woba_using_speedangle"].where(out["bbe"].eq(1), 0).fillna(0)
    out["xslg_num"] = out["estimated_slg_using_speedangle"].where(out["bbe"].eq(1), 0).fillna(0)
    out["x_metric_den"] = ((out["bbe"].eq(1)) & out["estimated_woba_using_speedangle"].notna()).astype(int)

    for split in ["early_1_3", "runner_on_base", "risp", "third_time"]:
        mask = out[split].eq(1)
        out[f"{split}_pa"] = ((mask) & out["pa"].eq(1)).astype(int)
        out[f"{split}_woba_num"] = out["woba_value"].where(mask & out["pa"].eq(1), 0).fillna(0)
        out[f"{split}_woba_den"] = out["woba_denom"].where(mask & out["pa"].eq(1), 0).fillna(0)
        out[f"{split}_bbe"] = ((mask) & out["bbe"].eq(1)).astype(int)
        out[f"{split}_xwoba_num"] = out["estimated_woba_using_speedangle"].where(mask & out["bbe"].eq(1), 0).fillna(0)
        out[f"{split}_x_metric_den"] = ((mask) & out["bbe"].eq(1) & out["estimated_woba_using_speedangle"].notna()).astype(int)

    return out


def aggregate_year(df: pd.DataFrame) -> pd.DataFrame:
    flags = add_flags(df)
    group_cols = ["game_year", "pitcher", "player_name"]
    agg_cols = {
        "pa": "sum",
        "pitch": "sum",
        "hit": "sum",
        "walk": "sum",
        "hbp": "sum",
        "strikeout": "sum",
        "home_run": "sum",
        "swing": "sum",
        "whiff": "sum",
        "zone_pitch": "sum",
        "out_zone_pitch": "sum",
        "chase_swing": "sum",
        "first_pitch": "sum",
        "first_pitch_nonball": "sum",
        "three_ball_pitch": "sum",
        "bbe": "sum",
        "hardhit": "sum",
        "barrel": "sum",
        "woba_num": "sum",
        "woba_den": "sum",
        "xwoba_num": "sum",
        "xslg_num": "sum",
        "x_metric_den": "sum",
    }
    for split in ["early_1_3", "runner_on_base", "risp", "third_time"]:
        agg_cols[f"{split}_pa"] = "sum"
        agg_cols[f"{split}_woba_num"] = "sum"
        agg_cols[f"{split}_woba_den"] = "sum"
        agg_cols[f"{split}_bbe"] = "sum"
        agg_cols[f"{split}_xwoba_num"] = "sum"
        agg_cols[f"{split}_x_metric_den"] = "sum"

    pitcher = flags.groupby(group_cols, dropna=False).agg(agg_cols).reset_index()

    game = (
        flags.groupby([*group_cols, "game_pk"], dropna=False)
        .agg(
            game_pitches=("pitch", "sum"),
            game_pa=("pa", "sum"),
            min_inning=("inning", "min"),
            max_thru_order=("n_thruorder_pitcher", "max"),
        )
        .reset_index()
    )
    game["start_proxy"] = game["min_inning"].eq(1)
    game["game_80plus_pitches"] = game["game_pitches"].ge(80)
    game["game_90plus_pitches"] = game["game_pitches"].ge(90)
    game["game_100plus_pitches"] = game["game_pitches"].ge(100)
    game["game_20plus_pa"] = game["game_pa"].ge(20)
    game["reached_third_time"] = game["max_thru_order"].ge(3)

    game_summary = (
        game.groupby(group_cols, dropna=False)
        .agg(
            games=("game_pk", "nunique"),
            start_proxy_games=("start_proxy", "sum"),
            avg_game_pitches=("game_pitches", "mean"),
            avg_game_pa=("game_pa", "mean"),
            max_game_pitches=("game_pitches", "max"),
            games_80plus_pitches=("game_80plus_pitches", "sum"),
            games_90plus_pitches=("game_90plus_pitches", "sum"),
            games_100plus_pitches=("game_100plus_pitches", "sum"),
            games_20plus_pa=("game_20plus_pa", "sum"),
            games_reached_third_time=("reached_third_time", "sum"),
        )
        .reset_index()
    )
    out = pitcher.merge(game_summary, on=group_cols, how="left")
    return add_rates(out)


def add_rates(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    out["bb_pct"] = safe_div(out["walk"], out["pa"])
    out["bb_hbp_pct"] = safe_div(out["walk"] + out["hbp"], out["pa"])
    out["k_pct"] = safe_div(out["strikeout"], out["pa"])
    out["hr_pct"] = safe_div(out["home_run"], out["pa"])
    out["woba_allowed"] = safe_div(out["woba_num"], out["woba_den"])
    out["xwoba_allowed_bbe"] = safe_div(out["xwoba_num"], out["x_metric_den"])
    out["xslg_allowed_bbe"] = safe_div(out["xslg_num"], out["x_metric_den"])
    out["whiff_per_swing"] = safe_div(out["whiff"], out["swing"])
    out["chase_rate"] = safe_div(out["chase_swing"], out["out_zone_pitch"])
    out["zone_rate"] = safe_div(out["zone_pitch"], out["pitch"])
    out["first_pitch_nonball_rate"] = safe_div(out["first_pitch_nonball"], out["first_pitch"])
    out["three_ball_pitch_rate"] = safe_div(out["three_ball_pitch"], out["pitch"])
    out["hardhit_rate"] = safe_div(out["hardhit"], out["bbe"])
    out["barrel_rate"] = safe_div(out["barrel"], out["bbe"])
    out["start_proxy_rate"] = safe_div(out["start_proxy_games"], out["games"])
    out["games_80plus_rate"] = safe_div(out["games_80plus_pitches"], out["games"])
    out["games_20plus_pa_rate"] = safe_div(out["games_20plus_pa"], out["games"])
    out["third_time_game_rate"] = safe_div(out["games_reached_third_time"], out["games"])

    for split in ["early_1_3", "runner_on_base", "risp", "third_time"]:
        out[f"{split}_woba_allowed"] = safe_div(out[f"{split}_woba_num"], out[f"{split}_woba_den"])
        out[f"{split}_xwoba_allowed_bbe"] = safe_div(out[f"{split}_xwoba_num"], out[f"{split}_x_metric_den"])
        out[f"{split}_pa_rate"] = safe_div(out[f"{split}_pa"], out["pa"])
    return out


def add_stabilizer_score(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    eligible = (out["pa"] >= 150) & (out["start_proxy_games"] >= 3)
    parts = pd.DataFrame(index=out.index)
    parts["load_games"] = out.groupby("game_year")["start_proxy_games"].transform(rank_score)
    parts["load_pitches"] = out.groupby("game_year")["avg_game_pitches"].transform(rank_score)
    parts["load_80plus"] = out.groupby("game_year")["games_80plus_pitches"].transform(rank_score)
    parts["control_bb_hbp"] = out.groupby("game_year")["bb_hbp_pct"].transform(rank_score, higher_is_better=False)
    parts["control_three_ball"] = out.groupby("game_year")["three_ball_pitch_rate"].transform(rank_score, higher_is_better=False)
    parts["damage_hr"] = out.groupby("game_year")["hr_pct"].transform(rank_score, higher_is_better=False)
    parts["damage_woba"] = out.groupby("game_year")["woba_allowed"].transform(rank_score, higher_is_better=False)
    parts["damage_xwoba"] = out.groupby("game_year")["xwoba_allowed_bbe"].transform(rank_score, higher_is_better=False)
    parts["damage_hardhit"] = out.groupby("game_year")["hardhit_rate"].transform(rank_score, higher_is_better=False)
    parts["stress_risp"] = out.groupby("game_year")["risp_woba_allowed"].transform(rank_score, higher_is_better=False)
    parts["early_game"] = out.groupby("game_year")["early_1_3_woba_allowed"].transform(rank_score, higher_is_better=False)

    out["starter_stabilizer_score"] = parts.mean(axis=1)
    out["starter_stabilizer_eligible"] = eligible
    out.loc[~eligible, "starter_stabilizer_score"] = np.nan
    return out


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yearly = []
    for year in YEARS:
        df = load_year(year)
        yearly.append(aggregate_year(df))
        print("aggregated", year, len(df), "pitches")
    features = add_stabilizer_score(pd.concat(yearly, ignore_index=True, sort=False))
    screen = (
        features[features["starter_stabilizer_eligible"] & features["game_year"].ge(2025)]
        .sort_values(["starter_stabilizer_score", "game_year", "pa"], ascending=[False, False, False])
        .head(300)
    )

    detail_path = OUTPUT_DIR / "savant_pitcher_feature_summary_2022_2026.csv"
    legacy_detail_path = OUTPUT_DIR / "savant_pitcher_feature_summary_2023_2026.csv"
    features.to_csv(detail_path, index=False)
    features.to_csv(legacy_detail_path, index=False)
    screen.to_csv(OUTPUT_DIR / "savant_pitcher_stabilizer_screen_top.csv", index=False)

    show_cols = [
        "game_year",
        "player_name",
        "pitcher",
        "pa",
        "games",
        "start_proxy_games",
        "avg_game_pitches",
        "bb_hbp_pct",
        "hr_pct",
        "woba_allowed",
        "early_1_3_woba_allowed",
        "risp_woba_allowed",
        "hardhit_rate",
        "starter_stabilizer_score",
    ]
    print("wrote", detail_path)
    print("wrote", legacy_detail_path)
    print("wrote", OUTPUT_DIR / "savant_pitcher_stabilizer_screen_top.csv")
    print(screen[show_cols].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
