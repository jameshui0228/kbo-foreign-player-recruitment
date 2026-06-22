#!/usr/bin/env python3
"""Build Layer 2 archetype validation and Layer 4 pitcher translation proxies.

This run strengthens the bridge between historical KBO foreign-player outcomes
and candidate-side translation signals. Candidate-side outputs stay locked:
names, teams, exact ranks, shortlist labels, and recommendations are excluded.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

BRIDGE = OUTPUT_DIR / "kbo_foreign_archetype_bridge_v0_2.csv"
RULES = OUTPUT_DIR / "kbo_foreign_archetype_rule_lifts_v0_2.csv"
PROFILE = OUTPUT_DIR / "kbo_foreign_archetype_prearrival_profile_v0_2.csv"
FIT_MART = OUTPUT_DIR / "ssg_fit_preparation_mart_v0_1.csv"

RELEASE_POLICY = "layer2_4_validation_sprint_research_only_no_candidate_release"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge", default=str(BRIDGE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--rules", default=str(RULES.relative_to(PROJECT_ROOT)))
    parser.add_argument("--profile", default=str(PROFILE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--fit-mart", default=str(FIT_MART.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def safe_num(frame: pd.DataFrame, col: str, default: float = np.nan) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[col], errors="coerce")


def safe_bool(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    return frame[col].astype(str).str.lower().isin(["true", "1", "1.0"])


def band_score(value: object) -> str:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if not np.isfinite(val):
        return "unknown"
    if val >= 70:
        return "strong"
    if val >= 55:
        return "above_average"
    if val >= 40:
        return "watch"
    return "weak_or_unknown"


def locked_id(row: pd.Series) -> str:
    seed = "|".join(str(row.get(col, "")) for col in ["fit_slot", "source_pool", "player_id", "position_or_role"])
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12].upper()
    return f"LOCKED-TRANS-{digest}"


def build_archetype_validation_matrix(bridge: pd.DataFrame, rules: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    df = bridge.copy()
    df["label_available_bool"] = safe_bool(df, "label_available")
    df["model_ready_bool"] = safe_bool(df, "has_model_pre_kbo_features")
    df["success_num"] = safe_num(df, "success", 0).fillna(0)
    df["failure_num"] = safe_num(df, "failure", 0).fillna(0)
    df["strong_success_num"] = safe_num(df, "strong_success", 0).fillna(0)
    df["in_season_replaced_num"] = safe_num(df, "in_season_replaced", 0).fillna(0)
    df["injury_exit_flag_num"] = safe_num(df, "injury_exit_flag", 0).fillna(0)
    df["performance_exit_flag_num"] = safe_num(df, "performance_exit_flag", 0).fillna(0)

    archetype_keys = ["role_model_family", "archetype_cluster_id", "archetype_name"]
    base = (
        df.groupby(archetype_keys, dropna=False)
        .agg(
            rows=("player_key", "nunique"),
            seasons=("season", "nunique"),
            label_rows=("label_available_bool", "sum"),
            model_ready_rows=("model_ready_bool", "sum"),
            success_rate=("success_num", "mean"),
            failure_rate=("failure_num", "mean"),
            strong_success_rate=("strong_success_num", "mean"),
            in_season_replaced_rate=("in_season_replaced_num", "mean"),
            injury_exit_rate=("injury_exit_flag_num", "mean"),
            performance_exit_rate=("performance_exit_flag_num", "mean"),
            median_first_kbo_war=("first_kbo_war", "median"),
            median_first_kbo_pa=("first_kbo_pa", "median"),
            median_first_kbo_ip=("first_kbo_ip", "median"),
        )
        .reset_index()
    )
    base["model_ready_rate"] = base["model_ready_rows"] / base["rows"].replace(0, np.nan)
    base["label_coverage_rate"] = base["label_rows"] / base["rows"].replace(0, np.nan)

    rule = rules.copy()
    rule["stable_rule"] = (
        safe_num(rule, "support_rows", 0).fillna(0).ge(5)
        & safe_num(rule, "abs_rate_delta", 0).fillna(0).ge(0.15)
        & safe_num(rule, "permutation_p_value", 1).fillna(1).le(0.35)
        & rule["semantic_alignment"].astype(str).isin(["aligned_positive", "aligned_risk"])
    )
    rule_summary = (
        rule.groupby("role_model_family", dropna=False)
        .agg(
            rule_rows=("rule", "size"),
            stable_rule_rows=("stable_rule", "sum"),
            median_support=("support_rows", "median"),
            best_abs_delta=("abs_rate_delta", "max"),
            best_lift=("lift_vs_role_base", "max"),
        )
        .reset_index()
    )
    base = base.merge(rule_summary, on="role_model_family", how="left")

    profile_keep = [
        "role_model_family",
        "archetype_cluster_id",
        "prearrival_strength_fingerprint",
        "prearrival_risk_fingerprint",
        "prearrival_profile_gate",
    ]
    base = base.merge(profile[[col for col in profile_keep if col in profile.columns]], on=["role_model_family", "archetype_cluster_id"], how="left")

    conditions = [
        base["rows"].ge(8) & base["model_ready_rate"].ge(0.6) & base["stable_rule_rows"].fillna(0).ge(10),
        base["rows"].ge(6) & base["model_ready_rate"].ge(0.45) & base["stable_rule_rows"].fillna(0).ge(5),
        base["rows"].ge(4) & base["model_ready_rate"].ge(0.3),
    ]
    choices = ["validated_core_archetype", "usable_research_archetype", "thin_but_trackable_archetype"]
    base["archetype_validation_tier"] = np.select(conditions, choices, default="backfill_required")
    base["candidate_release_allowed"] = False
    base["release_policy"] = RELEASE_POLICY
    return base.sort_values(["role_model_family", "archetype_validation_tier", "archetype_cluster_id"])


def build_rule_stability(rules: pd.DataFrame) -> pd.DataFrame:
    out = rules.copy()
    out["support_rows_num"] = safe_num(out, "support_rows", 0).fillna(0)
    out["abs_rate_delta_num"] = safe_num(out, "abs_rate_delta", 0).fillna(0)
    out["permutation_p_value_num"] = safe_num(out, "permutation_p_value", 1).fillna(1)
    out["rule_stability_score"] = (
        np.minimum(out["support_rows_num"], 20) * 2.0
        + out["abs_rate_delta_num"] * 100
        + (1 - out["permutation_p_value_num"].clip(0, 1)) * 25
    )
    out["rule_stability_tier"] = np.select(
        [
            out["support_rows_num"].ge(8) & out["abs_rate_delta_num"].ge(0.20) & out["permutation_p_value_num"].le(0.25),
            out["support_rows_num"].ge(5) & out["abs_rate_delta_num"].ge(0.15) & out["permutation_p_value_num"].le(0.35),
            out["support_rows_num"].ge(3) & out["abs_rate_delta_num"].ge(0.10),
        ],
        ["promote_to_candidate_proxy", "research_support_rule", "thin_watch_rule"],
        default="do_not_promote_rule",
    )
    out["candidate_release_allowed"] = False
    out["release_policy"] = RELEASE_POLICY
    keep = [
        "role_model_family",
        "signal_type",
        "rule",
        "target",
        "support_rows",
        "total_role_rows",
        "support_share",
        "target_rate_inside_rule",
        "role_base_target_rate",
        "rate_delta_vs_role_base",
        "lift_vs_role_base",
        "permutation_p_value",
        "semantic_alignment",
        "rule_gate",
        "rule_stability_score",
        "rule_stability_tier",
        "candidate_release_allowed",
        "release_policy",
    ]
    return out[[col for col in keep if col in out.columns]].sort_values(
        ["role_model_family", "rule_stability_tier", "rule_stability_score"], ascending=[True, True, False]
    )


def build_backfill_queue(bridge: pd.DataFrame) -> pd.DataFrame:
    df = bridge.copy()
    df["label_available_bool"] = safe_bool(df, "label_available")
    df["model_ready_bool"] = safe_bool(df, "has_model_pre_kbo_features")
    df["has_savant_bool"] = safe_bool(df, "has_pre_kbo_savant_features")
    df["has_milb_bool"] = safe_bool(df, "has_pre_kbo_milb")
    q = df[df["label_available_bool"] & ~df["model_ready_bool"]].copy()
    q["backfill_need"] = np.select(
        [
            ~q["has_savant_bool"] & ~q["has_milb_bool"],
            ~q["has_savant_bool"] & q["has_milb_bool"],
            q["has_savant_bool"] & ~q["has_milb_bool"],
        ],
        ["missing_savant_and_milb", "missing_savant_only", "missing_milb_only"],
        default="feature_mapping_gap",
    )
    q["backfill_priority"] = np.select(
        [
            q["season"].ge(2023),
            q["role_model_family"].eq("pitcher") & q["season"].ge(2020),
            q["role_model_family"].eq("hitter") & q["season"].ge(2020),
        ],
        ["P1_recent_outcome_backfill", "P2_pitcher_historical_backfill", "P3_hitter_historical_backfill"],
        default="P4_older_context_backfill",
    )
    q["candidate_release_allowed"] = False
    q["release_policy"] = RELEASE_POLICY
    keep = [
        "season",
        "player_key",
        "kbo_team",
        "role_model_family",
        "archetype_cluster_id",
        "archetype_name",
        "success",
        "failure",
        "in_season_replaced",
        "injury_exit_flag",
        "performance_exit_flag",
        "has_savant_bool",
        "has_milb_bool",
        "backfill_need",
        "backfill_priority",
        "candidate_release_allowed",
        "release_policy",
    ]
    return q[[col for col in keep if col in q.columns]].sort_values(["backfill_priority", "season", "player_key"])


def build_pitcher_translation_proxy(fit: pd.DataFrame) -> pd.DataFrame:
    pitchers = fit[fit["fit_slot"].eq("foreign_pitcher")].copy()
    coverage_inputs = [
        "pitcher_diagnostic_pct",
        "starter_runway_proxy_pct",
        "traffic_command_proxy_pct",
        "market_access_score",
        "availability_gate_score",
    ]
    pitchers["translation_proxy_component_coverage"] = (
        pitchers[[col for col in coverage_inputs if col in pitchers.columns]].apply(pd.to_numeric, errors="coerce").notna().sum(axis=1)
        / len(coverage_inputs)
        * 100
    )
    for col in [
        "pitcher_diagnostic_pct",
        "starter_runway_proxy_pct",
        "traffic_command_proxy_pct",
        "market_access_score",
        "availability_gate_score",
        "feature_coverage_score",
        "fit_preparation_index",
    ]:
        pitchers[col] = safe_num(pitchers, col, 0).fillna(0)
    pitchers["pitcher_translation_proxy_score"] = (
        pitchers["pitcher_diagnostic_pct"] * 0.30
        + pitchers["starter_runway_proxy_pct"] * 0.25
        + pitchers["traffic_command_proxy_pct"] * 0.25
        + pitchers["translation_proxy_component_coverage"] * 0.10
        + pitchers["availability_gate_score"] * 0.05
        + pitchers["market_access_score"] * 0.05
    )
    pitchers["pitcher_translation_proxy_band"] = pitchers["pitcher_translation_proxy_score"].map(band_score)
    pitchers["translation_proxy_locked_id"] = pitchers.apply(locked_id, axis=1)
    pitchers["translation_proxy_status"] = np.select(
        [
            pitchers["translation_proxy_component_coverage"].ge(80) & pitchers["pitcher_translation_proxy_score"].ge(60),
            pitchers["translation_proxy_component_coverage"].ge(80) & pitchers["pitcher_translation_proxy_score"].ge(45),
            pitchers["translation_proxy_component_coverage"].ge(60),
        ],
        ["usable_candidate_side_proxy", "research_proxy_needs_manual_review", "thin_proxy_needs_source_rebuild"],
        default="blocked_by_feature_gap",
    )
    pitchers["candidate_name_release_allowed"] = False
    pitchers["score_release_allowed"] = False
    pitchers["rank_release_allowed"] = False
    pitchers["shortlist_label_allowed"] = False
    pitchers["is_final_recommendation"] = False
    pitchers["recommendation_label"] = "locked_not_allowed"
    pitchers["release_policy"] = RELEASE_POLICY
    keep = [
        "translation_proxy_locked_id",
        "fit_slot",
        "source_pool",
        "age",
        "throws_or_bats",
        "position_or_role",
        "market_access_bucket",
        "availability_gate_pass",
        "pitcher_diagnostic_pct",
        "starter_runway_proxy_pct",
        "traffic_command_proxy_pct",
        "market_access_score",
        "availability_gate_score",
        "feature_coverage_score",
        "translation_proxy_component_coverage",
        "pitcher_translation_proxy_score",
        "pitcher_translation_proxy_band",
        "translation_proxy_status",
        "research_status",
        "manual_check_flags",
        "candidate_name_release_allowed",
        "score_release_allowed",
        "rank_release_allowed",
        "shortlist_label_allowed",
        "is_final_recommendation",
        "recommendation_label",
        "release_policy",
    ]
    return pitchers[[col for col in keep if col in pitchers.columns]].sort_values(
        ["translation_proxy_status", "pitcher_translation_proxy_band", "translation_proxy_locked_id"]
    )


def build_pitcher_proxy_summary(proxy: pd.DataFrame) -> pd.DataFrame:
    return (
        proxy.groupby(["source_pool", "translation_proxy_status", "pitcher_translation_proxy_band"], dropna=False)
        .agg(
            rows=("translation_proxy_locked_id", "nunique"),
            median_proxy_score=("pitcher_translation_proxy_score", "median"),
            median_component_coverage=("translation_proxy_component_coverage", "median"),
            release_allowed=("candidate_name_release_allowed", "any"),
        )
        .reset_index()
        .sort_values(["source_pool", "translation_proxy_status", "pitcher_translation_proxy_band"])
    )


def build_layer_gate_audit(matrix: pd.DataFrame, stability: pd.DataFrame, backfill: pd.DataFrame, proxy: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gate": "L2A",
                "layer": "KBO foreign-player success/failure archetype mining",
                "check": "archetype_validation_matrix_built",
                "pass_rows": int(matrix["archetype_validation_tier"].ne("backfill_required").sum()),
                "total_rows": len(matrix),
                "status": "pass_visible_gap",
                "blocking_gap": "Backfill-required archetypes still exist, but tiers are now explicit",
            },
            {
                "gate": "L2B",
                "layer": "KBO foreign-player success/failure archetype mining",
                "check": "rule_stability_tiers_built",
                "pass_rows": int(stability["rule_stability_tier"].isin(["promote_to_candidate_proxy", "research_support_rule"]).sum()),
                "total_rows": len(stability),
                "status": "pass_visible_gap",
                "blocking_gap": "Rules remain research-only and small-sample gates stay visible",
            },
            {
                "gate": "L2C",
                "layer": "KBO foreign-player success/failure archetype mining",
                "check": "historical_backfill_queue_built",
                "pass_rows": len(backfill),
                "total_rows": len(backfill),
                "status": "pass",
                "blocking_gap": "Backfill work is now measurable by row and priority",
            },
            {
                "gate": "L4A",
                "layer": "KBO translation model",
                "check": "pitcher_translation_proxy_component_built",
                "pass_rows": int(proxy["translation_proxy_status"].ne("blocked_by_feature_gap").sum()),
                "total_rows": len(proxy),
                "status": "pass_visible_gap",
                "blocking_gap": "Pitcher proxy is candidate-side and locked, not a final translation model",
            },
            {
                "gate": "LOCK",
                "layer": "Release policy",
                "check": "candidate_release_locks_preserved",
                "pass_rows": int(
                    (matrix["candidate_release_allowed"].eq(False).all())
                    and (stability["candidate_release_allowed"].eq(False).all())
                    and (backfill["candidate_release_allowed"].eq(False).all())
                    and (proxy["candidate_name_release_allowed"].eq(False).all())
                ),
                "total_rows": 1,
                "status": "pass",
                "blocking_gap": "No candidate names, ranks, scores, shortlist labels, or recommendations are released",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    bridge = pd.read_csv(PROJECT_ROOT / args.bridge)
    rules = pd.read_csv(PROJECT_ROOT / args.rules)
    profile = pd.read_csv(PROJECT_ROOT / args.profile)
    fit = pd.read_csv(PROJECT_ROOT / args.fit_mart)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    matrix = build_archetype_validation_matrix(bridge, rules, profile)
    stability = build_rule_stability(rules)
    backfill = build_backfill_queue(bridge)
    proxy = build_pitcher_translation_proxy(fit)
    proxy_summary = build_pitcher_proxy_summary(proxy)
    gate_audit = build_layer_gate_audit(matrix, stability, backfill, proxy)

    matrix.to_csv(OUTPUT_DIR / f"layer2_archetype_validation_matrix_{suffix}.csv", index=False)
    stability.to_csv(OUTPUT_DIR / f"layer2_rule_stability_tiers_{suffix}.csv", index=False)
    backfill.to_csv(OUTPUT_DIR / f"layer2_historical_backfill_queue_{suffix}.csv", index=False)
    proxy.to_csv(OUTPUT_DIR / f"layer4_pitcher_translation_proxy_component_{suffix}.csv", index=False)
    proxy_summary.to_csv(OUTPUT_DIR / f"layer4_pitcher_translation_proxy_summary_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"layer2_4_validation_sprint_gate_audit_{suffix}.csv", index=False)

    print(f"archetype_validation_rows={len(matrix)}")
    print(matrix["archetype_validation_tier"].value_counts(dropna=False).to_string())
    print(f"rule_stability_rows={len(stability)}")
    print(stability["rule_stability_tier"].value_counts(dropna=False).to_string())
    print(f"backfill_queue_rows={len(backfill)}")
    print(backfill["backfill_priority"].value_counts(dropna=False).to_string())
    print(f"pitcher_translation_proxy_rows={len(proxy)}")
    print(proxy["translation_proxy_status"].value_counts(dropna=False).to_string())
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
