#!/usr/bin/env python3
"""Build Savant hitter features for SSG message discovery.

This is a first-pass feature table, not an acquisition recommendation. It
does not yet filter by outfield eligibility, 40-man status, contract status,
or willingness/availability to sign in KBO.
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
    "batter",
    "events",
    "description",
    "type",
    "pitch_type",
    "release_speed",
    "zone",
    "stand",
    "p_throws",
    "balls",
    "strikes",
    "launch_speed",
    "launch_angle",
    "estimated_woba_using_speedangle",
    "estimated_slg_using_speedangle",
    "woba_value",
    "woba_denom",
    "babip_value",
    "iso_value",
    "launch_speed_angle",
    "bb_type",
    "hc_x",
    "hc_y",
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
FASTBALLS = {"FF", "SI", "FC", "FA"}
BREAKING = {"SL", "ST", "CU", "KC", "SV"}
OFFSPEED = {"CH", "FS", "FO", "SC", "KN", "EP"}
WALK_EVENTS = {"walk", "intent_walk"}
HIT_EVENTS = {"single", "double", "triple", "home_run"}


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
    return pd.read_parquet(path, columns=READ_COLUMNS)


def add_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["events"] = out["events"].fillna("")
    out["description"] = out["description"].fillna("")
    out["pitch_type"] = out["pitch_type"].fillna("")
    out["zone"] = pd.to_numeric(out["zone"], errors="coerce")
    out["release_speed"] = pd.to_numeric(out["release_speed"], errors="coerce")
    out["balls"] = pd.to_numeric(out["balls"], errors="coerce")
    out["strikes"] = pd.to_numeric(out["strikes"], errors="coerce")

    out["pitch"] = 1
    out["pa"] = ((out["events"] != "") & (out["events"] != "truncated_pa")).astype(int)
    out["hit"] = out["events"].isin(HIT_EVENTS).astype(int)
    out["walk"] = out["events"].isin(WALK_EVENTS).astype(int)
    out["strikeout"] = out["events"].eq("strikeout").astype(int)
    out["home_run"] = out["events"].eq("home_run").astype(int)
    out["hbp"] = out["events"].eq("hit_by_pitch").astype(int)

    out["swing"] = out["description"].isin(SWING_DESCRIPTIONS).astype(int)
    out["whiff"] = out["description"].isin(WHIFF_DESCRIPTIONS).astype(int)
    out["zone_pitch"] = out["zone"].between(1, 9, inclusive="both").astype(int)
    out["out_zone_pitch"] = ((out["zone"].notna()) & (~out["zone"].between(1, 9, inclusive="both"))).astype(int)
    out["chase_swing"] = ((out["swing"].eq(1)) & (out["out_zone_pitch"].eq(1))).astype(int)
    out["zone_swing"] = ((out["swing"].eq(1)) & (out["zone_pitch"].eq(1))).astype(int)

    out["non_fastball"] = (~out["pitch_type"].isin(FASTBALLS) & out["pitch_type"].ne("")).astype(int)
    out["breaking_or_offspeed"] = out["pitch_type"].isin(BREAKING | OFFSPEED).astype(int)
    out["nonfast_swing"] = ((out["non_fastball"].eq(1)) & out["swing"].eq(1)).astype(int)
    out["nonfast_whiff"] = ((out["non_fastball"].eq(1)) & out["whiff"].eq(1)).astype(int)
    out["nonfast_out_zone"] = ((out["non_fastball"].eq(1)) & out["out_zone_pitch"].eq(1)).astype(int)
    out["nonfast_chase"] = ((out["non_fastball"].eq(1)) & out["chase_swing"].eq(1)).astype(int)

    out["bbe"] = (
        out["launch_speed"].notna()
        & out["launch_angle"].notna()
        & out["description"].eq("hit_into_play")
    ).astype(int)
    out["hardhit"] = ((out["bbe"].eq(1)) & (out["launch_speed"] >= 95)).astype(int)
    out["barrel"] = ((out["bbe"].eq(1)) & (pd.to_numeric(out["launch_speed_angle"], errors="coerce") == 6)).astype(int)
    out["sweet_spot"] = ((out["bbe"].eq(1)) & out["launch_angle"].between(8, 32, inclusive="both")).astype(int)
    out["air_bbe"] = ((out["bbe"].eq(1)) & out["bb_type"].isin(["fly_ball", "line_drive"])).astype(int)
    out["low_velo_bbe"] = ((out["bbe"].eq(1)) & (out["release_speed"] <= 92)).astype(int)
    out["high_velo_bbe"] = ((out["bbe"].eq(1)) & (out["release_speed"] >= 95)).astype(int)
    out["nonfast_bbe"] = ((out["bbe"].eq(1)) & out["non_fastball"].eq(1)).astype(int)
    out["breaking_offspeed_bbe"] = ((out["bbe"].eq(1)) & out["breaking_or_offspeed"].eq(1)).astype(int)
    out["hitter_count"] = (
        ((out["balls"].eq(2)) & out["strikes"].eq(0))
        | ((out["balls"].eq(3)) & out["strikes"].isin([0, 1]))
    ).astype(int)
    out["hitter_count_swing"] = ((out["hitter_count"].eq(1)) & out["swing"].eq(1)).astype(int)
    out["hitter_count_bbe"] = ((out["hitter_count"].eq(1)) & out["bbe"].eq(1)).astype(int)

    # Spray direction proxy: MLBAM hit coordinates are approximate and should
    # be treated as an exploratory feature until validated visually.
    out["left_field_air_proxy"] = ((out["air_bbe"].eq(1)) & (out["hc_x"] < 125.42)).astype(int)
    out["right_field_air_proxy"] = ((out["air_bbe"].eq(1)) & (out["hc_x"] > 125.42)).astype(int)
    out["same_field_air_proxy"] = (
        ((out["stand"].eq("R")) & out["left_field_air_proxy"].eq(1))
        | ((out["stand"].eq("L")) & out["right_field_air_proxy"].eq(1))
    ).astype(int)

    for prefix, mask_col in [
        ("bbe", "bbe"),
        ("low_velo", "low_velo_bbe"),
        ("high_velo", "high_velo_bbe"),
        ("nonfast", "nonfast_bbe"),
        ("break_off", "breaking_offspeed_bbe"),
        ("hitter_count", "hitter_count_bbe"),
    ]:
        mask = out[mask_col].eq(1)
        out[f"{prefix}_xwoba_sum"] = out["estimated_woba_using_speedangle"].where(mask, 0).fillna(0)
        out[f"{prefix}_xslg_sum"] = out["estimated_slg_using_speedangle"].where(mask, 0).fillna(0)
        out[f"{prefix}_x_metric_denom"] = (
            mask & out["estimated_woba_using_speedangle"].notna()
        ).astype(int)

    out["woba_num"] = out["woba_value"].where(out["pa"].eq(1), 0).fillna(0)
    out["woba_den"] = out["woba_denom"].where(out["pa"].eq(1), 0).fillna(0)
    return out


def aggregate_year(df: pd.DataFrame) -> pd.DataFrame:
    flags = add_flags(df)
    agg_cols = {
        "pa": "sum",
        "pitch": "sum",
        "hit": "sum",
        "walk": "sum",
        "strikeout": "sum",
        "home_run": "sum",
        "hbp": "sum",
        "swing": "sum",
        "whiff": "sum",
        "zone_pitch": "sum",
        "out_zone_pitch": "sum",
        "chase_swing": "sum",
        "zone_swing": "sum",
        "non_fastball": "sum",
        "nonfast_swing": "sum",
        "nonfast_whiff": "sum",
        "nonfast_out_zone": "sum",
        "nonfast_chase": "sum",
        "bbe": "sum",
        "hardhit": "sum",
        "barrel": "sum",
        "sweet_spot": "sum",
        "air_bbe": "sum",
        "low_velo_bbe": "sum",
        "high_velo_bbe": "sum",
        "nonfast_bbe": "sum",
        "breaking_offspeed_bbe": "sum",
        "hitter_count": "sum",
        "hitter_count_swing": "sum",
        "hitter_count_bbe": "sum",
        "left_field_air_proxy": "sum",
        "right_field_air_proxy": "sum",
        "same_field_air_proxy": "sum",
        "woba_num": "sum",
        "woba_den": "sum",
    }
    for prefix in ["bbe", "low_velo", "high_velo", "nonfast", "break_off", "hitter_count"]:
        agg_cols[f"{prefix}_xwoba_sum"] = "sum"
        agg_cols[f"{prefix}_xslg_sum"] = "sum"
        agg_cols[f"{prefix}_x_metric_denom"] = "sum"

    out = flags.groupby(["game_year", "batter"], dropna=False).agg(agg_cols).reset_index()
    out["bb_pct"] = safe_div(out["walk"], out["pa"])
    out["k_pct"] = safe_div(out["strikeout"], out["pa"])
    out["hr_pct"] = safe_div(out["home_run"], out["pa"])
    out["woba"] = safe_div(out["woba_num"], out["woba_den"])
    out["swing_rate"] = safe_div(out["swing"], out["pitch"])
    out["whiff_per_swing"] = safe_div(out["whiff"], out["swing"])
    out["chase_rate"] = safe_div(out["chase_swing"], out["out_zone_pitch"])
    out["zone_swing_rate"] = safe_div(out["zone_swing"], out["zone_pitch"])
    out["nonfast_whiff_per_swing"] = safe_div(out["nonfast_whiff"], out["nonfast_swing"])
    out["nonfast_chase_rate"] = safe_div(out["nonfast_chase"], out["nonfast_out_zone"])
    out["hardhit_rate"] = safe_div(out["hardhit"], out["bbe"])
    out["barrel_rate"] = safe_div(out["barrel"], out["bbe"])
    out["sweet_spot_rate"] = safe_div(out["sweet_spot"], out["bbe"])
    out["air_bbe_rate"] = safe_div(out["air_bbe"], out["bbe"])
    out["same_field_air_rate_proxy"] = safe_div(out["same_field_air_proxy"], out["air_bbe"])
    out["hitter_count_swing_rate"] = safe_div(out["hitter_count_swing"], out["hitter_count"])

    for prefix in ["bbe", "low_velo", "high_velo", "nonfast", "break_off", "hitter_count"]:
        out[f"{prefix}_xwoba"] = safe_div(out[f"{prefix}_xwoba_sum"], out[f"{prefix}_x_metric_denom"])
        out[f"{prefix}_xslg"] = safe_div(out[f"{prefix}_xslg_sum"], out[f"{prefix}_x_metric_denom"])

    return out


def add_player_names(features: pd.DataFrame) -> pd.DataFrame:
    try:
        from pybaseball import playerid_reverse_lookup

        ids = sorted(features["batter"].dropna().astype(int).unique().tolist())
        lookup = playerid_reverse_lookup(ids, key_type="mlbam")
        lookup["batter_name"] = lookup["name_first"].fillna("") + " " + lookup["name_last"].fillna("")
        lookup = lookup[["key_mlbam", "batter_name", "key_fangraphs", "key_bbref"]].rename(
            columns={"key_mlbam": "batter"}
        )
        features = features.merge(lookup, on="batter", how="left")
    except Exception as exc:  # noqa: BLE001
        print(f"name lookup failed: {exc}")
        features["batter_name"] = ""
        features["key_fangraphs"] = np.nan
        features["key_bbref"] = ""
    return features


def add_screen_score(features: pd.DataFrame) -> pd.DataFrame:
    out = features.copy()
    eligible = out["pa"] >= 100
    score_parts = pd.DataFrame(index=out.index)
    score_parts["barrel"] = out.groupby("game_year")["barrel_rate"].transform(rank_score)
    score_parts["hardhit"] = out.groupby("game_year")["hardhit_rate"].transform(rank_score)
    score_parts["low_velo_damage"] = out.groupby("game_year")["low_velo_xwoba"].transform(rank_score)
    score_parts["nonfast_damage"] = out.groupby("game_year")["break_off_xwoba"].transform(rank_score)
    score_parts["bb"] = out.groupby("game_year")["bb_pct"].transform(rank_score)
    score_parts["chase"] = out.groupby("game_year")["chase_rate"].transform(lambda s: rank_score(s, higher_is_better=False))
    score_parts["hitter_count_damage"] = out.groupby("game_year")["hitter_count_xwoba"].transform(rank_score)
    out["ssg_message_screen_score"] = score_parts.mean(axis=1, skipna=True)
    out.loc[~eligible, "ssg_message_screen_score"] = np.nan
    return out


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frames = []
    for year in YEARS:
        df = load_year(year)
        frames.append(aggregate_year(df))
        print("aggregated", year)
    features = pd.concat(frames, ignore_index=True)
    features = add_player_names(features)
    features = add_screen_score(features)

    detail_path = OUTPUT_DIR / "savant_hitter_feature_summary_2022_2026.csv"
    legacy_detail_path = OUTPUT_DIR / "savant_hitter_feature_summary_2023_2026.csv"
    screen_path = OUTPUT_DIR / "savant_hitter_message_screen_top.csv"
    flawed_path = OUTPUT_DIR / "savant_hitter_flawed_profile_screen.csv"
    features.to_csv(detail_path, index=False)
    features.to_csv(legacy_detail_path, index=False)

    screen_cols = [
        "game_year",
        "batter",
        "batter_name",
        "pa",
        "ssg_message_screen_score",
        "woba",
        "bb_pct",
        "k_pct",
        "barrel_rate",
        "hardhit_rate",
        "low_velo_xwoba",
        "break_off_xwoba",
        "chase_rate",
        "nonfast_chase_rate",
        "hitter_count_swing_rate",
        "hitter_count_xwoba",
        "same_field_air_rate_proxy",
    ]
    screen = (
        features[features["pa"] >= 100]
        .sort_values(["game_year", "ssg_message_screen_score"], ascending=[False, False])
        .groupby("game_year")
        .head(50)[screen_cols]
    )
    screen.to_csv(screen_path, index=False)

    flawed_mask = (
        (features["pa"] >= 120)
        & (features["ssg_message_screen_score"] >= 70)
        & (features["woba"] <= 0.365)
        & (
            (features["k_pct"] >= 0.26)
            | (features["woba"] <= 0.330)
            | (features["chase_rate"] >= 0.30)
        )
        & (features["barrel_rate"] >= 0.08)
        & (features["bb_pct"] >= 0.08)
        & (features["break_off_xwoba"] >= 0.320)
        & (features["low_velo_xwoba"] >= 0.340)
    )
    flawed = (
        features[flawed_mask]
        .sort_values(["game_year", "ssg_message_screen_score"], ascending=[False, False])
        .groupby("game_year")
        .head(25)[screen_cols]
    )
    flawed.to_csv(flawed_path, index=False)

    print("wrote", detail_path)
    print("wrote", legacy_detail_path)
    print("wrote", screen_path)
    print("wrote", flawed_path)
    print(screen[screen["game_year"].isin([2025, 2026])].groupby("game_year").head(10).to_string(index=False))


if __name__ == "__main__":
    main()
