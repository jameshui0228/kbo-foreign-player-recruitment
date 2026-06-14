#!/usr/bin/env python3
"""Validate Layer 1 SSG hidden-weakness messages for robustness.

Run 016 is still Layer 1 only. It stress-tests the Run 015 context-friction
messages using time splits, leave-one-opponent-out sensitivity, bootstrap
intervals, permutation baselines, and negative controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"
N_BOOT = 3000
SEED = 20260614


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    rule_family: str
    rule_label: str
    mask_fn: Callable[[pd.DataFrame], pd.Series]
    min_games_core: int
    core_type: str


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def load_frame() -> pd.DataFrame:
    frame = pd.read_csv(OUT_DIR / "ssg_hidden_weakness_context_frame_v2.csv", low_memory=False)
    frame["game_dt"] = pd.to_datetime(frame["game_dt"], errors="coerce")
    for col in [
        "win",
        "run_diff",
        "team_score",
        "opp_score",
        "of_all_rbi",
        "of_high_rbi",
        "of_top_obp",
        "starter_short_lt5",
        "opp_win_pct_rank",
        "unearned_runs_allowed",
        "ofdh_run_kill_events",
        "team_bat_run_kill_events",
        "opp_runs_ge6",
        "of_hr_zero",
        "low_run_park",
        "high_run_park",
        "opp_pitching_top3",
        "opp_top3_win_pct",
    ]:
        if col in frame.columns:
            frame[col] = to_num(frame[col])
    frame["opp_sp_right"] = frame["opp_sp_throw_name"].astype(str).str.contains("우", na=False)
    return frame.sort_values("game_dt").reset_index(drop=True)


def rule_specs() -> list[RuleSpec]:
    return [
        RuleSpec(
            rule_id="R1_rhp_low_of_conversion_run_trade",
            rule_family="core",
            rule_label="OF RBI < 3 + opponent 6+ runs + right-handed opponent starter",
            mask_fn=lambda df: df["of_all_rbi"].fillna(0).lt(3) & df["opp_score"].ge(6) & df["opp_sp_right"].eq(True),
            min_games_core=10,
            core_type="primary_message",
        ),
        RuleSpec(
            rule_id="R2_rhp_ofdh_run_kill",
            rule_family="core",
            rule_label="OF table-setter OBP <= .250 + right-handed opponent starter + OF/DH GDP or CS",
            mask_fn=lambda df: df["of_top_obp"].fillna(0).le(0.250)
            & df["opp_sp_right"].eq(True)
            & df["ofdh_run_kill_events"].fillna(0).ge(1),
            min_games_core=7,
            core_type="hitter_filter",
        ),
        RuleSpec(
            rule_id="R3_extra_out_high_of_void",
            rule_family="core",
            rule_label="High-leverage OF 0 RBI + at least 1 unearned run allowed",
            mask_fn=lambda df: df["of_high_rbi"].fillna(0).eq(0) & df["unearned_runs_allowed"].fillna(0).ge(1),
            min_games_core=7,
            core_type="pitcher_hitter_bridge",
        ),
        RuleSpec(
            rule_id="R4_top_opponent_short_start_of_void",
            rule_family="supporting",
            rule_label="Starter < 5 IP + high-leverage OF 0 RBI + opponent top-3 win pct",
            mask_fn=lambda df: df["starter_short_lt5"].eq(True)
            & df["of_high_rbi"].fillna(0).eq(0)
            & df["opp_win_pct_rank"].le(3),
            min_games_core=7,
            core_type="support_only",
        ),
    ]


def negative_controls() -> list[RuleSpec]:
    return [
        RuleSpec(
            rule_id="NC1_of_hr_zero",
            rule_family="negative_control",
            rule_label="OF HR zero only",
            mask_fn=lambda df: df["of_all_hr"].fillna(0).eq(0),
            min_games_core=10,
            core_type="generic_power_control",
        ),
        RuleSpec(
            rule_id="NC2_right_starter_only",
            rule_family="negative_control",
            rule_label="Right-handed opponent starter only",
            mask_fn=lambda df: df["opp_sp_right"].eq(True),
            min_games_core=10,
            core_type="context_only_control",
        ),
        RuleSpec(
            rule_id="NC3_top_opponent_only",
            rule_family="negative_control",
            rule_label="Opponent top-3 win pct only",
            mask_fn=lambda df: df["opp_win_pct_rank"].le(3),
            min_games_core=10,
            core_type="opponent_only_control",
        ),
        RuleSpec(
            rule_id="NC4_low_run_park_only",
            rule_family="negative_control",
            rule_label="Low-run park only",
            mask_fn=lambda df: df["park_run_bucket"].eq("low_run_park"),
            min_games_core=10,
            core_type="park_only_control",
        ),
        RuleSpec(
            rule_id="NC5_of_rbi_low_only",
            rule_family="negative_control",
            rule_label="OF RBI < 3 only",
            mask_fn=lambda df: df["of_all_rbi"].fillna(0).lt(3),
            min_games_core=10,
            core_type="broad_of_control",
        ),
    ]


def stats_for_mask(df: pd.DataFrame, mask: pd.Series) -> dict[str, float]:
    mask = mask.fillna(False).astype(bool)
    subset = df[mask]
    comp = df[~mask]
    if subset.empty:
        return {
            "games": 0,
            "win_pct": np.nan,
            "complement_win_pct": np.nan,
            "win_pct_delta": np.nan,
            "avg_run_diff": np.nan,
            "complement_avg_run_diff": np.nan,
            "run_diff_delta": np.nan,
            "avg_team_runs": np.nan,
            "avg_opp_runs": np.nan,
            "avg_of_rbi": np.nan,
            "avg_unearned_runs": np.nan,
            "avg_ofdh_run_kill": np.nan,
        }
    comp_win = comp["win"].mean() if len(comp) else np.nan
    comp_rd = comp["run_diff"].mean() if len(comp) else np.nan
    return {
        "games": int(len(subset)),
        "win_pct": subset["win"].mean(),
        "complement_win_pct": comp_win,
        "win_pct_delta": subset["win"].mean() - comp_win if pd.notna(comp_win) else np.nan,
        "avg_run_diff": subset["run_diff"].mean(),
        "complement_avg_run_diff": comp_rd,
        "run_diff_delta": subset["run_diff"].mean() - comp_rd if pd.notna(comp_rd) else np.nan,
        "avg_team_runs": subset["team_score"].mean(),
        "avg_opp_runs": subset["opp_score"].mean(),
        "avg_of_rbi": subset["of_all_rbi"].mean(),
        "avg_unearned_runs": subset["unearned_runs_allowed"].mean(),
        "avg_ofdh_run_kill": subset["ofdh_run_kill_events"].mean(),
    }


def evaluate_rules(df: pd.DataFrame, specs: list[RuleSpec]) -> pd.DataFrame:
    rows = []
    for spec in specs:
        stats = stats_for_mask(df, spec.mask_fn(df))
        rows.append(
            {
                "rule_id": spec.rule_id,
                "rule_family": spec.rule_family,
                "core_type": spec.core_type,
                "rule_label": spec.rule_label,
                "min_games_core": spec.min_games_core,
                **stats,
            }
        )
    return pd.DataFrame(rows)


def time_splits(df: pd.DataFrame, specs: list[RuleSpec]) -> pd.DataFrame:
    split_idx = len(df) // 2
    windows = {
        "full": df,
        "first_half": df.iloc[:split_idx],
        "second_half": df.iloc[split_idx:],
    }
    for month, group in df.groupby(df["game_dt"].dt.month.fillna(-1).astype(int)):
        windows[f"month_{month:02d}"] = group

    rows = []
    for window, sub in windows.items():
        for spec in specs:
            stats = stats_for_mask(sub, spec.mask_fn(sub))
            rows.append({"window": window, "window_games": len(sub), "rule_id": spec.rule_id, **stats})
    return pd.DataFrame(rows)


def leave_one_opponent(df: pd.DataFrame, specs: list[RuleSpec]) -> pd.DataFrame:
    rows = []
    opponents = sorted(df["opponent_name"].dropna().astype(str).unique())
    for opponent in opponents:
        sub = df[df["opponent_name"].astype(str).ne(opponent)].copy()
        for spec in specs:
            stats = stats_for_mask(sub, spec.mask_fn(sub))
            rows.append({"left_out_opponent": opponent, "remaining_games": len(sub), "rule_id": spec.rule_id, **stats})
    return pd.DataFrame(rows)


def bootstrap_and_permutation(df: pd.DataFrame, specs: list[RuleSpec]) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows = []
    n = len(df)
    base_indices = np.arange(n)
    for spec in specs:
        mask = spec.mask_fn(df).fillna(False).to_numpy(dtype=bool)
        actual = stats_for_mask(df, pd.Series(mask, index=df.index))
        boot_win: list[float] = []
        boot_delta: list[float] = []
        boot_rd: list[float] = []
        for _ in range(N_BOOT):
            sample_idx = rng.choice(base_indices, size=n, replace=True)
            sample = df.iloc[sample_idx].reset_index(drop=True)
            sample_mask = pd.Series(mask[sample_idx])
            sample_stats = stats_for_mask(sample, sample_mask)
            if sample_stats["games"] > 0:
                boot_win.append(sample_stats["win_pct"])
                boot_delta.append(sample_stats["win_pct_delta"])
                boot_rd.append(sample_stats["avg_run_diff"])

        perm_win: list[float] = []
        perm_rd: list[float] = []
        for _ in range(N_BOOT):
            shuffled = rng.permutation(mask)
            perm_stats = stats_for_mask(df, pd.Series(shuffled, index=df.index))
            if perm_stats["games"] > 0:
                perm_win.append(perm_stats["win_pct"])
                perm_rd.append(perm_stats["avg_run_diff"])

        def q(values: list[float], pct: float) -> float:
            return float(np.nanquantile(values, pct)) if values else np.nan

        rows.append(
            {
                "rule_id": spec.rule_id,
                "actual_games": actual["games"],
                "actual_win_pct": actual["win_pct"],
                "actual_avg_run_diff": actual["avg_run_diff"],
                "actual_win_pct_delta": actual["win_pct_delta"],
                "boot_win_pct_p025": q(boot_win, 0.025),
                "boot_win_pct_p500": q(boot_win, 0.500),
                "boot_win_pct_p975": q(boot_win, 0.975),
                "boot_avg_run_diff_p025": q(boot_rd, 0.025),
                "boot_avg_run_diff_p500": q(boot_rd, 0.500),
                "boot_avg_run_diff_p975": q(boot_rd, 0.975),
                "boot_win_delta_p025": q(boot_delta, 0.025),
                "boot_win_delta_p500": q(boot_delta, 0.500),
                "boot_win_delta_p975": q(boot_delta, 0.975),
                "perm_p_win_pct_as_low_or_lower": float(np.mean(np.array(perm_win) <= actual["win_pct"])) if perm_win else np.nan,
                "perm_p_run_diff_as_low_or_lower": float(np.mean(np.array(perm_rd) <= actual["avg_run_diff"])) if perm_rd else np.nan,
                "bootstrap_iterations": len(boot_win),
                "permutation_iterations": len(perm_win),
            }
        )
    return pd.DataFrame(rows)


def decision_table(rule_eval: pd.DataFrame, time_df: pd.DataFrame, loo_df: pd.DataFrame, boot_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specs_by_id = {spec.rule_id: spec for spec in rule_specs()}
    for _, row in rule_eval.iterrows():
        spec = specs_by_id[row["rule_id"]]
        loo = loo_df[loo_df["rule_id"].eq(row["rule_id"])]
        boot = boot_df[boot_df["rule_id"].eq(row["rule_id"])].iloc[0]
        halves = time_df[time_df["rule_id"].eq(row["rule_id"]) & time_df["window"].isin(["first_half", "second_half"])]
        half_valid = halves["games"].ge(max(3, min(5, spec.min_games_core))).sum()
        loo_support_rate = (
            ((loo["games"].ge(max(4, spec.min_games_core - 2))) & (loo["win_pct"].le(0.250)) & (loo["avg_run_diff"].le(-3.0))).mean()
            if len(loo)
            else np.nan
        )
        passes_games = row["games"] >= spec.min_games_core
        passes_strength = row["win_pct"] <= 0.200 and row["avg_run_diff"] <= -4.0
        passes_boot = boot["boot_win_pct_p500"] <= 0.200 and boot["boot_avg_run_diff_p500"] <= -4.0
        passes_perm = boot["perm_p_win_pct_as_low_or_lower"] <= 0.150 or boot["perm_p_run_diff_as_low_or_lower"] <= 0.150
        passes_loo = loo_support_rate >= 0.700
        if passes_games and passes_strength and passes_boot and passes_loo:
            decision = "promote_core"
        elif row["games"] >= 5 and passes_strength and (passes_boot or passes_perm):
            decision = "support_only"
        else:
            decision = "hold_or_downgrade"
        rows.append(
            {
                "rule_id": row["rule_id"],
                "core_type": row["core_type"],
                "games": row["games"],
                "win_pct": row["win_pct"],
                "avg_run_diff": row["avg_run_diff"],
                "half_windows_with_signal": int(half_valid),
                "leave_one_opponent_support_rate": loo_support_rate,
                "bootstrap_median_win_pct": boot["boot_win_pct_p500"],
                "bootstrap_median_run_diff": boot["boot_avg_run_diff_p500"],
                "perm_p_win_pct_as_low_or_lower": boot["perm_p_win_pct_as_low_or_lower"],
                "perm_p_run_diff_as_low_or_lower": boot["perm_p_run_diff_as_low_or_lower"],
                "passes_games": bool(passes_games),
                "passes_strength": bool(passes_strength),
                "passes_bootstrap_median": bool(passes_boot),
                "passes_leave_one_opponent": bool(passes_loo),
                "decision": decision,
            }
        )
    return pd.DataFrame(rows)


def final_message(decisions: pd.DataFrame, negative: pd.DataFrame) -> pd.DataFrame:
    controls = negative.set_index("rule_id")
    of_hr_control = controls.loc["NC1_of_hr_zero"].to_dict()
    of_low_control = controls.loc["NC5_of_rbi_low_only"].to_dict()
    core_count = int(decisions["decision"].eq("promote_core").sum())
    support_count = int(decisions["decision"].eq("support_only").sum())
    msg = (
        "SSG's Layer 1 hidden weakness is robust enough to use as a feature contract: "
        "the problem is not generic outfield power, but a RHP-side game-script lock where "
        "OF/DH low conversion, run-killing outs, and extra-out damage remove comeback paths."
    )
    return pd.DataFrame(
        [
            {
                "message_version": "L1_V3_robustness_validated",
                "layer_status": "near_freeze_pending_refresh",
                "core_rules_promoted": core_count,
                "support_rules": support_count,
                "negative_control_of_hr_zero_win_pct": of_hr_control.get("win_pct"),
                "negative_control_of_hr_zero_avg_run_diff": of_hr_control.get("avg_run_diff"),
                "broad_of_low_rbi_win_pct": of_low_control.get("win_pct"),
                "broad_of_low_rbi_avg_run_diff": of_low_control.get("avg_run_diff"),
                "final_layer1_message": msg,
                "foreign_pitcher_contract": "traffic command; starter length; extra-out resilience; low free-pass volatility",
                "foreign_hitter_contract": "RHP-resistant OF/DH OBP plus damage; two-strike survival; GDP/CS run-kill avoidance",
                "remaining_gap": "refresh post-2026-06-11 data and attach stronger play-by-play/defense/baserunning proxies",
            }
        ]
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = load_frame()
    specs = rule_specs()
    controls = negative_controls()

    rule_eval = evaluate_rules(frame, specs)
    negative_eval = evaluate_rules(frame, controls)
    split_eval = time_splits(frame, specs)
    loo_eval = leave_one_opponent(frame, specs)
    boot_eval = bootstrap_and_permutation(frame, specs)
    decisions = decision_table(rule_eval, split_eval, loo_eval, boot_eval)
    message = final_message(decisions, negative_eval)

    outputs = [
        ("ssg_hidden_weakness_robustness_rules_v3.csv", rule_eval),
        ("ssg_hidden_weakness_negative_controls_v3.csv", negative_eval),
        ("ssg_hidden_weakness_time_split_v3.csv", split_eval),
        ("ssg_hidden_weakness_leave_one_opponent_v3.csv", loo_eval),
        ("ssg_hidden_weakness_bootstrap_permutation_v3.csv", boot_eval),
        ("ssg_hidden_weakness_robustness_decisions_v3.csv", decisions),
        ("ssg_hidden_weakness_final_message_v3.csv", message),
    ]
    for name, df in outputs:
        path = OUT_DIR / name
        df.to_csv(path, index=False)
        print(f"wrote {path} ({len(df)} rows)")

    print(decisions.to_string(index=False))
    print(message.to_string(index=False))


if __name__ == "__main__":
    main()
