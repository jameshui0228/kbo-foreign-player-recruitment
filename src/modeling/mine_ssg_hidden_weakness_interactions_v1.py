#!/usr/bin/env python3
"""Develop SSG hidden-weakness mining with game and role interactions.

This run is for Layer 1 only. It does not score player candidates. It mines
where SSG's 2026 roster context creates non-obvious recruitment needs.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def aggregate_batting(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    work = df.copy()
    stat_cols = ["PA", "AB", "H", "2B", "3B", "HR", "BB", "HP", "SF", "SO", "GDP", "TB", "R", "RBI", "SB"]
    for col in stat_cols:
        if col not in work.columns:
            work[col] = 0
        work[col] = to_num(work[col]).fillna(0)
    agg = (
        work.groupby(group_cols, dropna=False)
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
            gdp=("GDP", "sum"),
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
    agg["rbi_per_pa"] = agg["rbi"] / agg["pa"].replace(0, np.nan)
    agg["hr_per_pa"] = agg["hr"] / agg["pa"].replace(0, np.nan)
    return agg


def build_game_frame() -> pd.DataFrame:
    batting = pd.read_csv(OUT_DIR / "kbo_2026_batting_with_context.csv", low_memory=False)
    ssg = batting[batting["t_code_name"].eq("SSG")].copy()
    base_cols = [
        "s_no",
        "game_dt",
        "opponent_name",
        "home_away",
        "team_score",
        "opp_score",
        "win",
        "run_diff",
        "month",
        "humidity_bucket",
        "temp_bucket",
        "weather_name",
    ]
    game = ssg.drop_duplicates("s_no")[base_cols].copy()

    role_groups = {
        "of_all": ssg["position_group"].eq("OF"),
        "of_high": ssg["role_group"].isin(["OF_1-2_table_setters", "OF_3-5_run_production"]),
        "of_top": ssg["role_group"].eq("OF_1-2_table_setters"),
        "of_middle": ssg["role_group"].eq("OF_3-5_run_production"),
        "of_lower": ssg["role_group"].eq("OF_6-9_lower_lineup"),
        "dh": ssg["position_group"].eq("DH"),
        "ifc": ssg["position_group"].eq("IF_C"),
        "replacement_slot": ssg["position_group"].isin(["OF", "DH"]),
    }
    for name, mask in role_groups.items():
        role = aggregate_batting(ssg[mask], ["s_no"])
        rename = {col: f"{name}_{col}" for col in role.columns if col != "s_no"}
        game = game.merge(role.rename(columns=rename), on="s_no", how="left")

    workload = pd.read_csv(OUT_DIR / "ssg_2026_game_pitching_workload.csv", low_memory=False)
    workload_cols = [
        "s_no_filled",
        "starter_outs",
        "starter_er",
        "starter_r",
        "starter_h",
        "starter_hr",
        "starter_bb",
        "starter_tbf",
        "starter_np",
        "starter_ip",
        "starter_short_lt5",
        "starter_quality_6ip_3er",
        "starter_disaster",
        "bullpen_outs",
        "bullpen_er",
        "bullpen_r",
        "bullpen_h",
        "bullpen_hr",
        "bullpen_bb",
        "bullpen_tbf",
        "bullpen_ip",
        "bullpen_ip_after_start",
        "team_margin",
    ]
    game = game.merge(
        workload[workload_cols],
        left_on="s_no",
        right_on="s_no_filled",
        how="left",
    )
    numeric_cols = [col for col in game.columns if col not in ["game_dt", "opponent_name", "home_away", "humidity_bucket", "temp_bucket", "weather_name"]]
    for col in numeric_cols:
        game[col] = to_num(game[col])
    return game


def add_flags(game: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    out = game.copy()
    flag_desc: dict[str, str] = {}

    def add(name: str, mask: pd.Series, desc: str) -> None:
        out[name] = mask.fillna(False).astype(bool)
        flag_desc[name] = desc

    add("starter_short_lt5", out["starter_short_lt5"].eq(True), "starter failed to complete 5 innings")
    add("starter_er4plus", out["starter_er"].ge(4), "starter allowed 4+ ER")
    add("starter_disaster", out["starter_disaster"].eq(True), "starter disaster: 5+ ER or fewer than 4 innings")
    add("bullpen_ip_ge5", out["bullpen_ip_after_start"].ge(5), "bullpen had to cover 5+ innings")
    add("bullpen_er3plus", out["bullpen_er"].ge(3), "bullpen allowed 3+ ER")
    add("bullpen_bb4plus", out["bullpen_bb"].ge(4), "bullpen issued 4+ walks")
    add("of_rbi_zero", out["of_all_rbi"].fillna(0).eq(0), "all outfielders combined for 0 RBI")
    add("of_rbi_lt3", out["of_all_rbi"].fillna(0).lt(3), "outfielders combined for fewer than 3 RBI")
    add("of_hr_zero", out["of_all_hr"].fillna(0).eq(0), "outfielders hit no HR")
    add("of_high_rbi_zero", out["of_high_rbi"].fillna(0).eq(0), "high-leverage OF lineup slots had 0 RBI")
    add("of_high_obp_le_250", out["of_high_obp"].fillna(0).le(0.250), "high-leverage OF OBP was .250 or lower")
    add("of_top_obp_le_250", out["of_top_obp"].fillna(0).le(0.250), "OF table-setter OBP was .250 or lower")
    add("replacement_slot_rbi_lt3", out["replacement_slot_rbi"].fillna(0).lt(3), "OF/DH replacement-relevant slots had fewer than 3 RBI")
    add("replacement_slot_k_ge5", out["replacement_slot_so"].fillna(0).ge(5), "OF/DH replacement-relevant slots struck out 5+ times")
    add("team_runs_le3", out["team_score"].le(3), "SSG scored 3 or fewer runs")
    add("opp_runs_ge6", out["opp_score"].ge(6), "opponent scored 6+ runs")
    add("away_game", out["home_away"].eq("away"), "away game")
    add("humid_60plus", out["humidity_bucket"].eq("humid_60+"), "humid game, 60%+")
    return out, flag_desc


def describe_subset(game: pd.DataFrame, mask: pd.Series) -> dict[str, float]:
    subset = game[mask]
    comp = game[~mask]
    if subset.empty:
        return {}
    win_pct = subset["win"].mean()
    comp_win_pct = comp["win"].mean() if not comp.empty else np.nan
    return {
        "games": int(len(subset)),
        "win_pct": win_pct,
        "complement_win_pct": comp_win_pct,
        "win_pct_delta": win_pct - comp_win_pct if pd.notna(comp_win_pct) else np.nan,
        "loss_rate": 1 - win_pct,
        "avg_run_diff": subset["run_diff"].mean(),
        "avg_team_runs": subset["team_score"].mean(),
        "avg_opp_runs": subset["opp_score"].mean(),
        "avg_starter_outs": subset["starter_outs"].mean(),
        "avg_bullpen_ip": subset["bullpen_ip_after_start"].mean(),
        "avg_of_rbi": subset["of_all_rbi"].mean(),
        "avg_of_high_obp": subset["of_high_obp"].mean(),
        "avg_replacement_slot_k": subset["replacement_slot_so"].mean(),
    }


def mine_game_interactions(game: pd.DataFrame, flag_desc: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    flags = list(flag_desc)
    base_loss = 1 - game["win"].mean()
    single_loss_lift: dict[str, float] = {}
    for flag in flags:
        mask = game[flag]
        stats = describe_subset(game, mask)
        if not stats or stats["games"] < 5:
            continue
        loss_lift = stats["loss_rate"] - base_loss
        single_loss_lift[flag] = loss_lift
        rows.append(
            {
                "rule_type": "single",
                "rule": flag,
                "rule_description": flag_desc[flag],
                "component_a": flag,
                "component_b": "",
                "hidden_interaction_lift": np.nan,
                "loss_rate_lift_vs_baseline": loss_lift,
                "hidden_need_score": stats["games"] / len(game) * 2 + max(0, loss_lift) * 4,
                **stats,
            }
        )

    for a, b in combinations(flags, 2):
        mask = game[a] & game[b]
        stats = describe_subset(game, mask)
        if not stats or stats["games"] < 7:
            continue
        loss_lift = stats["loss_rate"] - base_loss
        component_lift = max(single_loss_lift.get(a, 0), single_loss_lift.get(b, 0))
        hidden_interaction_lift = loss_lift - component_lift
        rows.append(
            {
                "rule_type": "pair",
                "rule": f"{a} AND {b}",
                "rule_description": f"{flag_desc[a]} + {flag_desc[b]}",
                "component_a": a,
                "component_b": b,
                "hidden_interaction_lift": hidden_interaction_lift,
                "loss_rate_lift_vs_baseline": loss_lift,
                "hidden_need_score": stats["games"] / len(game) * 2 + max(0, loss_lift) * 4 + max(0, hidden_interaction_lift) * 3,
                **stats,
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values(["hidden_need_score", "games"], ascending=[False, False])


def build_role_context_summary() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    hand = pd.read_csv(OUT_DIR / "ssg_2026_of_role_by_opponent_starter_hand.csv")
    for _, row in hand.iterrows():
        if row["pa"] < 50:
            continue
        bad_rank_mean = np.nanmean([row.get("ops_rank"), row.get("obp_rank"), row.get("slg_rank"), row.get("iso_rank")])
        rows.append(
            {
                "signal_id": "of_role_vs_starter_hand",
                "slot_implication": "foreign_hitter",
                "context": f"{row['role_group']} vs {row['opp_sp_throw_name']} starter",
                "sample": row["pa"],
                "observed": f"OPS {row['ops']:.3f}, OBP {row['obp']:.3f}, SLG {row['slg']:.3f}, ISO {row['iso']:.3f}",
                "rank_context": f"OPS rank {row['ops_rank']:.0f}/{row['team_count']:.0f}; OBP rank {row['obp_rank']:.0f}/{row['team_count']:.0f}; SLG rank {row['slg_rank']:.0f}/{row['team_count']:.0f}",
                "hidden_need_score": row["pa"] / 80 + max(0, bad_rank_mean - 6) / 4,
                "candidate_screen_translation": "RHP-resistant OF/DH bat with OBP plus damage; do not screen only for raw HR",
                "source_table": "outputs/tables/ssg_2026_of_role_by_opponent_starter_hand.csv",
            }
        )

    count = pd.read_csv(OUT_DIR / "ssg_2026_situation_count_class_splits.csv")
    focus = count[count["replacement_relevant"].eq(True) & count["count_class"].isin(["two_strikes", "pitcher_count"])].copy()
    for _, row in focus.iterrows():
        if row["pa"] < 15:
            continue
        rows.append(
            {
                "signal_id": "replacement_count_survival",
                "slot_implication": "foreign_hitter",
                "context": f"{row['role_segment']} in {row['count_class']}",
                "sample": row["pa"],
                "observed": f"OPS {row['ops']:.3f}, OBP {row['obp']:.3f}, K% {row['k_pct']:.3f}, RBI/PA {row['rbi_per_pa']:.3f}",
                "rank_context": "SSG role segment only; candidate screen should validate with candidate-level contact data",
                "hidden_need_score": row["pa"] / 60 + max(0, 0.700 - row["ops"]) * 2 + max(0, row["k_pct"] - 0.25) * 3,
                "candidate_screen_translation": "two-strike survival and chase/contact stability, especially for OF/DH bridge roles",
                "source_table": "outputs/tables/ssg_2026_situation_count_class_splits.csv",
            }
        )

    result = pd.read_csv(OUT_DIR / "ssg_2026_team_result_by_of_rbi_bucket.csv")
    zero = result[result["of_rbi_bucket"].eq("OF_RBI_0")]
    high = result[result["of_rbi_bucket"].eq("OF_RBI_3+")]
    if not zero.empty and not high.empty:
        z = zero.iloc[0]
        h = high.iloc[0]
        rows.append(
            {
                "signal_id": "of_rbi_game_result_cliff",
                "slot_implication": "foreign_hitter",
                "context": "game result by total OF RBI bucket",
                "sample": z["games"],
                "observed": f"OF RBI 0 games: win% {z['win_pct']:.3f}, team runs {z['team_runs']:.2f}; OF RBI 3+ games: win% {h['win_pct']:.3f}, team runs {h['team_runs']:.2f}",
                "rank_context": "within-SSG game-result contrast",
                "hidden_need_score": (h["win_pct"] - z["win_pct"]) * 4 + z["games"] / 20,
                "candidate_screen_translation": "OF bat should be evaluated by run-conversion frequency, not only season HR/SLG",
                "source_table": "outputs/tables/ssg_2026_team_result_by_of_rbi_bucket.csv",
            }
        )

    pitching = pd.read_csv(OUT_DIR / "ssg_pitching_message_v0_2_context_validation.csv")
    top_pitch = pitching.sort_values("bad_context_score", ascending=False).head(5)
    for _, row in top_pitch.iterrows():
        rows.append(
            {
                "signal_id": "starter_context_damage",
                "slot_implication": "foreign_pitcher",
                "context": row["context_unit"],
                "sample": row["TBF"],
                "observed": f"ERA {row['ERA']:.2f}, WHIP {row['WHIP']:.2f}, OPSA {row['OPS']:.3f}",
                "rank_context": f"ERA rank {row['ERA_rank']:.0f}/10; WHIP rank {row['WHIP_rank']:.0f}/10; OPSA rank {row['OPS_rank']:.0f}/10",
                "hidden_need_score": row["bad_context_score"],
                "candidate_screen_translation": "traffic command plus early-count strike/zone stability, not pure strikeout-first profile",
                "source_table": "outputs/tables/ssg_pitching_message_v0_2_context_validation.csv",
            }
        )

    out = pd.DataFrame(rows)
    return out.sort_values(["hidden_need_score", "sample"], ascending=[False, False])


def build_message_candidates(game_rules: pd.DataFrame, role_context: pd.DataFrame) -> pd.DataFrame:
    def top_obs(signal_id: str, n: int = 2) -> str:
        subset = role_context[role_context["signal_id"].eq(signal_id)].head(n)
        return " | ".join(subset["observed"].astype(str).tolist())

    pair = game_rules[game_rules["rule_type"].eq("pair")].head(10)
    best_system_rule = pair.iloc[0] if not pair.empty else pd.Series(dtype=object)

    messages = [
        {
            "message_id": "L1_M01_rhp_high_leverage_of_void",
            "slot_priority": "foreign_hitter",
            "message": "SSG's outfield problem is not generic power; it is high-leverage OF/DH run conversion against right-handed starters.",
            "why_hidden": "Overall OF power can look acceptable, but role x opponent-starter-hand splits expose a top-lineup OF collapse vs RHP.",
            "key_evidence": top_obs("of_role_vs_starter_hand", 3),
            "candidate_translation": "Prioritize a RHP-resistant OF/DH bat with OBP plus damage and low empty-power risk.",
            "novelty_1_5": 5,
            "ssg_specificity_1_5": 5,
            "actionability_1_5": 5,
            "data_strength_1_5": 4,
        },
        {
            "message_id": "L1_M02_two_strike_replacement_slot_survival",
            "slot_priority": "foreign_hitter",
            "message": "The replacement-relevant OF/DH slots leak value after count pressure; SSG needs two-strike survival, not only first-pitch damage.",
            "why_hidden": "This does not show in season OPS alone; it appears after splitting replacement-relevant roles by count class.",
            "key_evidence": top_obs("replacement_count_survival", 3),
            "candidate_translation": "Screen candidates for two-strike contact, chase restraint, and damage retention after pitcher counts.",
            "novelty_1_5": 4,
            "ssg_specificity_1_5": 5,
            "actionability_1_5": 4,
            "data_strength_1_5": 3,
        },
        {
            "message_id": "L1_M03_starter_of_double_bind",
            "slot_priority": "foreign_pitcher_then_hitter",
            "message": "SSG's game script breaks when starter length and outfield run conversion fail together.",
            "why_hidden": "The signal is an interaction, not a single leaderboard rank: short starts are damaging, but the game becomes much harder to save when OF run conversion is also absent.",
            "key_evidence": "" if best_system_rule.empty else f"{best_system_rule['rule_description']}: {best_system_rule['games']} games, win% {best_system_rule['win_pct']:.3f}, run diff {best_system_rule['avg_run_diff']:.2f}",
            "candidate_translation": "Foreign pitcher remains first priority; hitter profile should specifically reduce OF_RBI_0/low-conversion games.",
            "novelty_1_5": 5,
            "ssg_specificity_1_5": 5,
            "actionability_1_5": 5,
            "data_strength_1_5": 4,
        },
        {
            "message_id": "L1_M04_abs_traffic_command_starter",
            "slot_priority": "foreign_pitcher",
            "message": "SSG needs a starter who prevents traffic from becoming crooked innings in the ABS-era strike-zone environment.",
            "why_hidden": "Starter ERA is obvious; the hidden layer is context concentration in early innings, RISP/runner states, and right-handed pitcher contexts.",
            "key_evidence": top_obs("starter_context_damage", 4),
            "candidate_translation": "Screen for first-pitch non-ball rate, zone command, walk suppression, and damage control with runners on.",
            "novelty_1_5": 4,
            "ssg_specificity_1_5": 5,
            "actionability_1_5": 5,
            "data_strength_1_5": 5,
        },
    ]
    out = pd.DataFrame(messages)
    out["message_score"] = out[["novelty_1_5", "ssg_specificity_1_5", "actionability_1_5", "data_strength_1_5"]].sum(axis=1)
    return out.sort_values(["message_score", "message_id"], ascending=[False, True])


def build_need_contract(messages: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, msg in messages.iterrows():
        if msg["slot_priority"] == "foreign_hitter":
            rows.append(
                {
                    "message_id": msg["message_id"],
                    "slot": "foreign_hitter",
                    "must_have": "RHP-resistant OF/DH bat; OBP plus damage; two-strike survival; run-conversion consistency",
                    "avoid": "empty pull power, high chase/high whiff in two-strike counts, platoon-only lefty masher without RHP stability",
                    "candidate_features_to_join": "vs_RHP_xwOBA/OPS; chase_rate; whiff_per_swing; two_strike_wOBA_proxy; BB%; K%; OF/DH role fit",
                    "why_this_is_ssg_specific": msg["why_hidden"],
                }
            )
        elif msg["slot_priority"] == "foreign_pitcher":
            rows.append(
                {
                    "message_id": msg["message_id"],
                    "slot": "foreign_pitcher",
                    "must_have": "load-bearing starter; traffic command; early-inning stability; walk suppression; ABS-friendly zone/first-pitch profile",
                    "avoid": "short-start volatility, high BB/HBP traffic, third-time collapse without 5-inning floor",
                    "candidate_features_to_join": "starter_stabilizer_score; BB/HBP%; first_pitch_nonball_rate; zone_rate; RISP wOBA allowed; workload continuity",
                    "why_this_is_ssg_specific": msg["why_hidden"],
                }
            )
        else:
            rows.append(
                {
                    "message_id": msg["message_id"],
                    "slot": "foreign_pitcher_then_hitter",
                    "must_have": "pitcher first for game-script floor; hitter secondary for OF run-conversion cliff",
                    "avoid": "solving only one side of the interaction with a generic OPS/ERA target",
                    "candidate_features_to_join": "starter length + OF/DH RHP conversion + low-stale-track market feasibility",
                    "why_this_is_ssg_specific": msg["why_hidden"],
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    game = build_game_frame()
    game_flags, flag_desc = add_flags(game)
    game_rules = mine_game_interactions(game_flags, flag_desc)
    role_context = build_role_context_summary()
    messages = build_message_candidates(game_rules, role_context)
    need_contract = build_need_contract(messages)

    game_flags.to_csv(OUT_DIR / "ssg_hidden_weakness_game_frame_v1.csv", index=False)
    game_rules.to_csv(OUT_DIR / "ssg_hidden_weakness_game_interactions_v1.csv", index=False)
    role_context.to_csv(OUT_DIR / "ssg_hidden_weakness_role_context_v1.csv", index=False)
    messages.to_csv(OUT_DIR / "ssg_hidden_weakness_message_candidates_v1.csv", index=False)
    need_contract.to_csv(OUT_DIR / "ssg_hidden_weakness_need_contract_v1.csv", index=False)

    print(f"wrote {OUT_DIR / 'ssg_hidden_weakness_game_frame_v1.csv'} ({len(game_flags)} rows)")
    print(f"wrote {OUT_DIR / 'ssg_hidden_weakness_game_interactions_v1.csv'} ({len(game_rules)} rows)")
    print(f"wrote {OUT_DIR / 'ssg_hidden_weakness_role_context_v1.csv'} ({len(role_context)} rows)")
    print(f"wrote {OUT_DIR / 'ssg_hidden_weakness_message_candidates_v1.csv'} ({len(messages)} rows)")
    print(f"wrote {OUT_DIR / 'ssg_hidden_weakness_need_contract_v1.csv'} ({len(need_contract)} rows)")
    print(messages[["message_id", "slot_priority", "message_score", "message"]].to_string(index=False))


if __name__ == "__main__":
    main()
