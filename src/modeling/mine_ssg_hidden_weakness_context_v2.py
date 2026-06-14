#!/usr/bin/env python3
"""Extend Layer 1 SSG hidden-weakness mining with context frictions.

Run 014 found a game-script double bind: starter/bullpen stress plus OF/DH
run-conversion failure. This Run 015 extension checks whether that message
survives when fielding errors, unearned runs, baserunning outs, park run
environment, opponent quality, and opponent starter handedness are attached.

This script is Layer 1 only. It does not score or rank player candidates.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
OUT_DIR = ROOT / "outputs/tables"
SSG_CODE = 9002
SSG_NAME = "SSG"


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    return num / den.replace(0, np.nan)


def load_schedule() -> pd.DataFrame:
    schedule = pd.read_csv(STATIZ_ROOT / "organized/games/games_schedule.csv", low_memory=False)
    schedule = schedule[
        schedule["year"].eq(2026)
        & schedule["leagueType_name"].eq("정규시즌")
        & schedule["state_name"].eq("경기 종료")
    ].copy()
    for col in ["s_no", "awayTeam", "homeTeam", "awayScore", "homeScore", "s_code", "temperature", "humidity", "windSpeed"]:
        schedule[col] = to_num(schedule[col])
    schedule["total_runs"] = schedule["awayScore"] + schedule["homeScore"]
    return schedule


def team_records(schedule: pd.DataFrame) -> pd.DataFrame:
    away = schedule.assign(
        t_code=schedule["awayTeam"],
        t_code_name=schedule["awayTeam_name"],
        runs_for=schedule["awayScore"],
        runs_against=schedule["homeScore"],
    )
    home = schedule.assign(
        t_code=schedule["homeTeam"],
        t_code_name=schedule["homeTeam_name"],
        runs_for=schedule["homeScore"],
        runs_against=schedule["awayScore"],
    )
    games = pd.concat([away, home], ignore_index=True)
    games["win"] = games["runs_for"].gt(games["runs_against"]).astype(int)
    records = (
        games.groupby(["t_code", "t_code_name"], dropna=False)
        .agg(
            games=("s_no", "nunique"),
            wins=("win", "sum"),
            runs_for=("runs_for", "sum"),
            runs_against=("runs_against", "sum"),
            avg_runs_for=("runs_for", "mean"),
            avg_runs_against=("runs_against", "mean"),
        )
        .reset_index()
    )
    records["win_pct"] = records["wins"] / records["games"].replace(0, np.nan)
    records["win_pct_rank"] = records["win_pct"].rank(method="min", ascending=False)
    records["run_diff_per_game"] = (records["runs_for"] - records["runs_against"]) / records["games"].replace(0, np.nan)
    records["run_diff_rank"] = records["run_diff_per_game"].rank(method="min", ascending=False)
    return records


def park_summary(schedule: pd.DataFrame) -> pd.DataFrame:
    summary = (
        schedule.groupby("s_code", dropna=False)
        .agg(
            park_games=("s_no", "nunique"),
            park_total_runs=("total_runs", "mean"),
            park_temperature=("temperature", "mean"),
            park_humidity=("humidity", "mean"),
            park_wind=("windSpeed", "mean"),
        )
        .reset_index()
    )
    summary["park_run_rank"] = summary["park_total_runs"].rank(method="min", ascending=False)
    if len(summary) > 1:
        summary["park_run_z"] = (summary["park_total_runs"] - summary["park_total_runs"].mean()) / summary[
            "park_total_runs"
        ].std(ddof=0)
    else:
        summary["park_run_z"] = 0
    q_low = summary["park_total_runs"].quantile(0.33)
    q_high = summary["park_total_runs"].quantile(0.67)
    summary["park_run_bucket"] = np.select(
        [
            summary["park_total_runs"].le(q_low),
            summary["park_total_runs"].ge(q_high),
        ],
        ["low_run_park", "high_run_park"],
        default="mid_run_park",
    )
    return summary


def opponent_starter_hand(schedule: pd.DataFrame) -> pd.DataFrame:
    lineup = pd.read_csv(STATIZ_ROOT / "organized/games/games_lineup.csv", low_memory=False)
    starters = lineup[
        to_num(lineup["s_no"]).between(20260000, 20269999) & to_num(lineup["position"]).eq(1)
    ][["s_no", "t_code", "p_no", "p_name", "p_throw_name"]].drop_duplicates()

    rows: list[dict[str, Any]] = []
    for _, row in schedule.iterrows():
        if int(row["awayTeam"]) == SSG_CODE:
            opponent_code = int(row["homeTeam"])
        elif int(row["homeTeam"]) == SSG_CODE:
            opponent_code = int(row["awayTeam"])
        else:
            continue
        opp_sp = starters[starters["s_no"].eq(row["s_no"]) & starters["t_code"].eq(opponent_code)]
        rows.append(
            {
                "s_no": int(row["s_no"]),
                "opp_sp_throw_name": "" if opp_sp.empty else str(opp_sp["p_throw_name"].iloc[0]),
                "opp_sp_name": "" if opp_sp.empty else str(opp_sp["p_name"].iloc[0]),
            }
        )
    return pd.DataFrame(rows)


def ssg_game_context(schedule: pd.DataFrame) -> pd.DataFrame:
    records = team_records(schedule)
    parks = park_summary(schedule)
    starters = opponent_starter_hand(schedule)
    pitching_ranks = pd.read_csv(OUT_DIR / "kbo_2026_team_pitching_situation_ranks.csv", low_memory=False)
    batting_ranks = pd.read_csv(OUT_DIR / "kbo_2026_team_situation_ranks.csv", low_memory=False)
    overall_pitch = pitching_ranks[
        pitching_ranks["context_family"].eq("overall") & pitching_ranks["context_label"].eq("all")
    ][["t_code", "ERA_rank", "WHIP_rank", "bb9_rank", "kbb_rank"]].rename(
        columns={
            "t_code": "opponent_code",
            "ERA_rank": "opp_pitch_era_rank",
            "WHIP_rank": "opp_pitch_whip_rank",
            "bb9_rank": "opp_pitch_bb9_rank",
            "kbb_rank": "opp_pitch_kbb_rank",
        }
    )
    overall_bat = batting_ranks[
        batting_ranks["context_family"].eq("overall") & batting_ranks["context_label"].eq("all")
    ][["t_code", "OPS_rank", "OBP_rank", "SLG_rank", "rbi_per_pa_rank"]].rename(
        columns={
            "t_code": "opponent_code",
            "OPS_rank": "opp_bat_ops_rank",
            "OBP_rank": "opp_bat_obp_rank",
            "SLG_rank": "opp_bat_slg_rank",
            "rbi_per_pa_rank": "opp_bat_rbi_per_pa_rank",
        }
    )
    opponent_records = records.rename(
        columns={
            "t_code": "opponent_code",
            "t_code_name": "opponent_record_name",
            "games": "opp_record_games",
            "wins": "opp_record_wins",
            "win_pct": "opp_win_pct",
            "win_pct_rank": "opp_win_pct_rank",
            "run_diff_per_game": "opp_run_diff_per_game",
            "run_diff_rank": "opp_run_diff_rank",
        }
    )

    rows: list[dict[str, Any]] = []
    for _, row in schedule.iterrows():
        away = int(row["awayTeam"])
        home = int(row["homeTeam"])
        if away == SSG_CODE:
            rows.append(
                {
                    "s_no": int(row["s_no"]),
                    "opponent_code": home,
                    "venue_half_offense": "top",
                    "venue_half_defense": "bottom",
                    "ssg_is_home": False,
                    "s_code": row["s_code"],
                    "ssg_team_score_check": row["awayScore"],
                    "ssg_opp_score_check": row["homeScore"],
                }
            )
        elif home == SSG_CODE:
            rows.append(
                {
                    "s_no": int(row["s_no"]),
                    "opponent_code": away,
                    "venue_half_offense": "bottom",
                    "venue_half_defense": "top",
                    "ssg_is_home": True,
                    "s_code": row["s_code"],
                    "ssg_team_score_check": row["homeScore"],
                    "ssg_opp_score_check": row["awayScore"],
                }
            )
    out = pd.DataFrame(rows)
    out = out.merge(opponent_records, on="opponent_code", how="left")
    out = out.merge(overall_pitch, on="opponent_code", how="left")
    out = out.merge(overall_bat, on="opponent_code", how="left")
    out = out.merge(parks, on="s_code", how="left")
    out = out.merge(starters, on="s_no", how="left")
    return out


def fielding_from_innings(context: pd.DataFrame) -> pd.DataFrame:
    lines = pd.read_csv(STATIZ_ROOT / "organized/games/games_boxscore_inning_lines.csv", low_memory=False)
    lines["request_s_no"] = to_num(lines["request_s_no"])
    lines["E"] = to_num(lines["E"]).fillna(0)
    lines["R"] = to_num(lines["R"]).fillna(0)
    ctx = context[["s_no", "venue_half_offense", "venue_half_defense"]].copy()
    merged = lines.merge(ctx, left_on="request_s_no", right_on="s_no", how="inner")
    merged["half"] = np.where(merged["inningMode"].eq("T"), "top", "bottom")
    offense = (
        merged[merged["half"].eq(merged["venue_half_offense"])]
        .groupby("s_no")
        .agg(opp_fielding_errors=("E", "sum"), ssg_offense_inning_runs=("R", "sum"))
        .reset_index()
    )
    defense = (
        merged[merged["half"].eq(merged["venue_half_defense"])]
        .groupby("s_no")
        .agg(ssg_fielding_errors=("E", "sum"), ssg_defense_inning_runs_allowed=("R", "sum"))
        .reset_index()
    )
    return offense.merge(defense, on="s_no", how="outer")


def pitching_unearned_runs() -> pd.DataFrame:
    pitching = pd.read_csv(OUT_DIR / "kbo_2026_pitching_with_context.csv", low_memory=False)
    ssg = pitching[pitching["t_code_name"].eq(SSG_NAME)].copy()
    for col in ["R", "ER", "BB", "HP", "HR", "TBF", "NP"]:
        if col not in ssg.columns:
            ssg[col] = 0
        ssg[col] = to_num(ssg[col]).fillna(0)
    agg = (
        ssg.groupby("s_no_filled", dropna=False)
        .agg(
            pitcher_runs=("R", "sum"),
            pitcher_er=("ER", "sum"),
            pitcher_bb=("BB", "sum"),
            pitcher_hbp=("HP", "sum"),
            pitcher_hr=("HR", "sum"),
            pitcher_tbf=("TBF", "sum"),
            pitcher_np=("NP", "sum"),
        )
        .reset_index()
        .rename(columns={"s_no_filled": "s_no"})
    )
    agg["s_no"] = to_num(agg["s_no"]).astype("Int64")
    agg["unearned_runs_allowed"] = (agg["pitcher_runs"] - agg["pitcher_er"]).clip(lower=0)
    return agg


def batting_friction() -> pd.DataFrame:
    batting = pd.read_csv(OUT_DIR / "kbo_2026_batting_with_context.csv", low_memory=False)
    ssg = batting[batting["t_code_name"].eq(SSG_NAME)].copy()
    for col in ["PA", "GDP", "CS", "SB", "SH", "SF", "SO", "RBI", "R", "BB", "HP"]:
        if col not in ssg.columns:
            ssg[col] = 0
        ssg[col] = to_num(ssg[col]).fillna(0)

    def agg(mask: pd.Series, prefix: str) -> pd.DataFrame:
        sub = ssg[mask].copy()
        out = (
            sub.groupby("s_no", dropna=False)
            .agg(
                pa=("PA", "sum"),
                gdp=("GDP", "sum"),
                cs=("CS", "sum"),
                sb=("SB", "sum"),
                sh=("SH", "sum"),
                sf=("SF", "sum"),
                so=("SO", "sum"),
                rbi=("RBI", "sum"),
                runs=("R", "sum"),
                bb=("BB", "sum"),
                hbp=("HP", "sum"),
            )
            .reset_index()
        )
        return out.rename(columns={c: f"{prefix}_{c}" for c in out.columns if c != "s_no"})

    team = agg(pd.Series(True, index=ssg.index), "team_bat")
    ofdh = agg(ssg["position_group"].isin(["OF", "DH"]), "ofdh")
    high_of = agg(ssg["role_group"].isin(["OF_1-2_table_setters", "OF_3-5_run_production"]), "high_of")
    out = team.merge(ofdh, on="s_no", how="left").merge(high_of, on="s_no", how="left")
    for prefix in ["team_bat", "ofdh", "high_of"]:
        out[f"{prefix}_run_kill_events"] = out[f"{prefix}_gdp"].fillna(0) + out[f"{prefix}_cs"].fillna(0)
        out[f"{prefix}_sb_efficiency"] = safe_div(out[f"{prefix}_sb"], out[f"{prefix}_sb"] + out[f"{prefix}_cs"])
        out[f"{prefix}_rbi_per_pa"] = safe_div(out[f"{prefix}_rbi"], out[f"{prefix}_pa"])
    return out


def build_context_frame() -> pd.DataFrame:
    base = pd.read_csv(OUT_DIR / "ssg_hidden_weakness_game_frame_v1.csv", low_memory=False)
    schedule = load_schedule()
    context = ssg_game_context(schedule)
    fielding = fielding_from_innings(context)
    unearned = pitching_unearned_runs()
    friction = batting_friction()
    out = (
        base.merge(context, on="s_no", how="left")
        .merge(fielding, on="s_no", how="left")
        .merge(unearned, on="s_no", how="left")
        .merge(friction, on="s_no", how="left")
    )
    fill_zero = [
        "opp_fielding_errors",
        "ssg_fielding_errors",
        "unearned_runs_allowed",
        "team_bat_gdp",
        "team_bat_cs",
        "team_bat_sb",
        "team_bat_run_kill_events",
        "ofdh_gdp",
        "ofdh_cs",
        "ofdh_run_kill_events",
        "high_of_gdp",
        "high_of_cs",
        "high_of_run_kill_events",
    ]
    for col in fill_zero:
        if col in out.columns:
            out[col] = to_num(out[col]).fillna(0)
    return out


def add_flags(game: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    out = game.copy()
    flag_desc: dict[str, str] = {}

    def add(name: str, mask: pd.Series, desc: str) -> None:
        out[name] = mask.fillna(False).astype(bool)
        flag_desc[name] = desc

    add("starter_short_lt5", out["starter_short_lt5"].eq(True), "starter failed to complete 5 innings")
    add("starter_disaster", out["starter_disaster"].eq(True), "starter disaster: 5+ ER or fewer than 4 innings")
    add("bullpen_er3plus", out["bullpen_er"].ge(3), "bullpen allowed 3+ ER")
    add("bullpen_bb4plus", out["bullpen_bb"].ge(4), "bullpen issued 4+ walks")
    add("of_rbi_lt3", out["of_all_rbi"].fillna(0).lt(3), "outfielders combined for fewer than 3 RBI")
    add("of_high_rbi_zero", out["of_high_rbi"].fillna(0).eq(0), "high-leverage OF lineup slots had 0 RBI")
    add("of_top_obp_le_250", out["of_top_obp"].fillna(0).le(0.250), "OF table-setter OBP was .250 or lower")
    add("replacement_slot_rbi_lt3", out["replacement_slot_rbi"].fillna(0).lt(3), "OF/DH slots had fewer than 3 RBI")
    add("team_runs_le3", out["team_score"].le(3), "SSG scored 3 or fewer runs")
    add("opp_runs_ge6", out["opp_score"].ge(6), "opponent scored 6+ runs")
    add("opp_sp_right", out["opp_sp_throw_name"].astype(str).str.contains("우", na=False), "opponent starter was right-handed")
    add("opp_top3_win_pct", out["opp_win_pct_rank"].le(3), "opponent ranked top 3 by current 2026 win percentage")
    add("opp_pitching_top3", out["opp_pitch_era_rank"].le(3), "opponent ranked top 3 by current team ERA")
    add("opp_offense_top3", out["opp_bat_ops_rank"].le(3), "opponent ranked top 3 by current team OPS")
    add("low_run_park", out["park_run_bucket"].eq("low_run_park"), "game was in a lower-run venue bucket")
    add("high_run_park", out["park_run_bucket"].eq("high_run_park"), "game was in a higher-run venue bucket")
    add("ssg_errors_ge1", out["ssg_fielding_errors"].ge(1), "SSG committed at least 1 fielding error")
    add("ssg_errors_ge2", out["ssg_fielding_errors"].ge(2), "SSG committed 2+ fielding errors")
    add("unearned_runs_ge1", out["unearned_runs_allowed"].ge(1), "SSG allowed at least 1 unearned run")
    add("team_run_kill_ge2", out["team_bat_run_kill_events"].ge(2), "SSG had 2+ GDP/CS run-kill events")
    add("ofdh_run_kill_ge1", out["ofdh_run_kill_events"].ge(1), "OF/DH slots had at least 1 GDP/CS run-kill event")
    add(
        "opp_error_no_cash",
        out["opp_fielding_errors"].ge(1) & out["team_score"].le(3),
        "opponent made an error but SSG still scored 3 or fewer runs",
    )
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
        "avg_ssg_errors": subset["ssg_fielding_errors"].mean(),
        "avg_unearned_runs": subset["unearned_runs_allowed"].mean(),
        "avg_team_run_kill": subset["team_bat_run_kill_events"].mean(),
        "avg_ofdh_run_kill": subset["ofdh_run_kill_events"].mean(),
        "avg_opp_win_pct": subset["opp_win_pct"].mean(),
        "avg_park_total_runs": subset["park_total_runs"].mean(),
    }


def mine_interactions(game: pd.DataFrame, flag_desc: dict[str, str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    flags = list(flag_desc)
    base_loss = 1 - game["win"].mean()
    single_loss_lift: dict[str, float] = {}

    def append_row(rule_type: str, components: tuple[str, ...], stats: dict[str, float]) -> None:
        loss_lift = stats["loss_rate"] - base_loss
        component_lift = max([single_loss_lift.get(c, 0) for c in components] or [0])
        hidden_interaction_lift = np.nan if rule_type == "single" else loss_lift - component_lift
        rows.append(
            {
                "rule_type": rule_type,
                "rule": " AND ".join(components),
                "rule_description": " + ".join(flag_desc[c] for c in components),
                "components": ";".join(components),
                "hidden_interaction_lift": hidden_interaction_lift,
                "loss_rate_lift_vs_baseline": loss_lift,
                "hidden_need_score": stats["games"] / len(game) * 2
                + max(0, loss_lift) * 4
                + (0 if pd.isna(hidden_interaction_lift) else max(0, hidden_interaction_lift) * 3),
                **stats,
            }
        )

    for flag in flags:
        stats = describe_subset(game, game[flag])
        if not stats or stats["games"] < 5:
            continue
        single_loss_lift[flag] = stats["loss_rate"] - base_loss
        append_row("single", (flag,), stats)

    for size, min_games in [(2, 7), (3, 5)]:
        for combo in combinations(flags, size):
            stats = describe_subset(game, game[list(combo)].all(axis=1))
            if not stats or stats["games"] < min_games:
                continue
            append_row("pair" if size == 2 else "triple", combo, stats)

    out = pd.DataFrame(rows)
    return out.sort_values(["hidden_need_score", "games"], ascending=[False, False])


def summarize_message_upgrade(interactions: pd.DataFrame, game: pd.DataFrame) -> pd.DataFrame:
    def top_rule_contains(*parts: str) -> pd.Series:
        mask = pd.Series(True, index=interactions.index)
        for part in parts:
            mask &= interactions["components"].str.contains(part, regex=False, na=False)
        sub = interactions[mask]
        return sub.iloc[0] if not sub.empty else pd.Series(dtype=object)

    rows: list[dict[str, Any]] = []
    rules = [
        (
            "L1_V2_context_double_bind",
            "foreign_pitcher_then_hitter",
            "SSG's hidden weakness is a context-amplified game-script lock, not a one-stat gap.",
            top_rule_contains("of_rbi_lt3", "opp_runs_ge6", "opp_sp_right"),
            "The original run-conversion problem remains when opponent starter handedness is attached.",
            "Pitcher first for game-script floor; hitter screen must be RHP-resistant and run-conversion stable.",
        ),
        (
            "L1_V2_unearned_extra_out_lock",
            "foreign_pitcher_then_hitter",
            "SSG's no-recovery games are amplified when extra-out damage meets a high-leverage OF run-conversion void.",
            top_rule_contains("unearned_runs_ge1", "of_high_rbi_zero"),
            "The defensive/pitching leak is hidden because it is clearer through unearned-run states than raw error count.",
            "Pitcher screen should value traffic command and extra-out resilience; hitter screen should preserve rescue value.",
        ),
        (
            "L1_V2_rhp_run_kill_hitter_filter",
            "foreign_hitter",
            "The hitter filter should punish RHP-side run-killing outs, not only low OPS.",
            top_rule_contains("opp_sp_right", "ofdh_run_kill_ge1", "of_top_obp_le_250"),
            "GDP/CS friction in OF/DH slots worsens the RHP-side low-conversion tail.",
            "Add GDP avoidance, baserunning decision quality, and contact shape to the OF/DH screen.",
        ),
        (
            "L1_V2_top_opponent_margin_of_error",
            "foreign_pitcher_then_hitter",
            "Against top opponents, SSG has almost no margin for short starts plus high-leverage OF silence.",
            top_rule_contains("starter_short_lt5", "of_high_rbi_zero", "opp_top3_win_pct"),
            "The issue is not just losing to good teams; it is the specific pathway where starter length and OF conversion vanish together.",
            "Stress-test candidates for performance retention against playoff-level opponents and right-handed starter scripts.",
        ),
    ]
    for message_id, slot, message, rule, why_hidden, translation in rules:
        if rule.empty:
            evidence = "No qualifying rule at the selected support threshold."
            data_strength = 2
            games = 0
            win_pct = np.nan
            run_diff = np.nan
        else:
            evidence = (
                f"{rule['rule_description']}: {int(rule['games'])} games, "
                f"win% {rule['win_pct']:.3f}, run diff {rule['avg_run_diff']:.2f}, "
                f"hidden lift {rule['hidden_interaction_lift']:.3f}"
            )
            data_strength = 4 if int(rule["games"]) >= 7 else 3
            games = int(rule["games"])
            win_pct = rule["win_pct"]
            run_diff = rule["avg_run_diff"]
        rows.append(
            {
                "message_id": message_id,
                "slot_priority": slot,
                "message": message,
                "supporting_rule": "" if rule.empty else rule["rule"],
                "supporting_games": games,
                "supporting_win_pct": win_pct,
                "supporting_avg_run_diff": run_diff,
                "why_hidden": why_hidden,
                "key_evidence": evidence,
                "candidate_translation": translation,
                "novelty_1_5": 5,
                "ssg_specificity_1_5": 5,
                "actionability_1_5": 5,
                "data_strength_1_5": data_strength,
                "message_score": 15 + data_strength,
            }
        )
    return pd.DataFrame(rows).sort_values(["message_score", "supporting_games"], ascending=[False, False])


def build_feature_contract(messages: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "foreign_pitcher": {
            "must_have": "traffic command; low BB/HBP; extra-out resilience; starter length; stable first-pitch/zone profile",
            "avoid": "short-start volatility, high free-pass traffic, fielding-dependent contact profile without command floor",
            "candidate_features_to_join": "BB%; HBP%; first-pitch non-ball; zone%; GB%; hard-hit allowed; RISP wOBA; workload continuity",
        },
        "foreign_hitter": {
            "must_have": "RHP-resistant OF/DH bat; OBP plus damage; two-strike survival; run-kill avoidance",
            "avoid": "empty pull power, high chase/whiff, high GDP risk, weak baserunning decisions, platoon-only value",
            "candidate_features_to_join": "vs_RHP OPS/xwOBA; chase%; whiff%; two-strike wOBA; GDP rate; sprint/baserunning proxies; BB/K",
        },
        "foreign_pitcher_then_hitter": {
            "must_have": "pitcher first for game-script floor; hitter as low-conversion tail reducer",
            "avoid": "solving only one side with generic ERA or OPS",
            "candidate_features_to_join": "starter stabilizer score; OF/DH RHP conversion score; market feasibility; failure-risk score",
        },
    }
    rows = []
    for _, row in messages.iterrows():
        slot = row["slot_priority"]
        values = mapping.get(slot, mapping["foreign_hitter"])
        rows.append(
            {
                "message_id": row["message_id"],
                "slot": slot,
                **values,
                "supporting_rule": row["supporting_rule"],
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    game = build_context_frame()
    game, flag_desc = add_flags(game)
    interactions = mine_interactions(game, flag_desc)
    messages = summarize_message_upgrade(interactions, game)
    feature_contract = build_feature_contract(messages)

    outputs = [
        ("ssg_hidden_weakness_context_frame_v2.csv", game),
        ("ssg_hidden_weakness_context_interactions_v2.csv", interactions),
        ("ssg_hidden_weakness_context_message_upgrade_v2.csv", messages),
        ("ssg_hidden_weakness_context_feature_contract_v2.csv", feature_contract),
    ]
    for name, df in outputs:
        path = OUT_DIR / name
        df.to_csv(path, index=False)
        print(f"wrote {path} ({len(df)} rows)")

    print(messages[["message_id", "slot_priority", "message_score", "supporting_games", "message"]].to_string(index=False))
    print(interactions.head(12)[["rule_type", "rule", "games", "win_pct", "avg_run_diff", "hidden_need_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
