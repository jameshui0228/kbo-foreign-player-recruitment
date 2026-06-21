#!/usr/bin/env python3
"""Bridge KBO foreign-player outcome archetypes to pre-arrival fingerprints.

Layer 2 should not be only a success/failure classifier. This script keeps the
historical KBO outcome archetypes from v0.1, then attaches pre-arrival Savant
and MiLB feature-family scores so the project can ask a sharper question:

Which pre-arrival fingerprints tended to land in each KBO success/failure
archetype?

All outputs remain research-only. Candidate release locks stay closed.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

MART_PATH = OUTPUT_DIR / "kbo_translation_feature_mart_v0_2.csv"
ASSIGNMENT_PATH = OUTPUT_DIR / "kbo_foreign_archetype_assignments_v0_1.csv"
SUMMARY_PATH = OUTPUT_DIR / "kbo_foreign_archetype_summary_v0_1.csv"

BRIDGE_OUT = OUTPUT_DIR / "kbo_foreign_archetype_bridge_v0_2.csv"
PROFILE_OUT = OUTPUT_DIR / "kbo_foreign_archetype_prearrival_profile_v0_2.csv"
RULE_OUT = OUTPUT_DIR / "kbo_foreign_archetype_rule_lifts_v0_2.csv"
CONTRACT_OUT = OUTPUT_DIR / "kbo_foreign_archetype_feature_contract_v0_2.csv"
GATE_OUT = OUTPUT_DIR / "kbo_foreign_archetype_gate_audit_v0_2.csv"

RELEASE_POLICY = "layer2_archetype_research_only_no_candidate_release"
RANDOM_SEED = 31

warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)


@dataclass(frozen=True)
class FeatureSpec:
    feature: str
    direction: int


FEATURE_FAMILIES: dict[str, dict[str, list[FeatureSpec]]] = {
    "hitter": {
        "hitter_quality_of_contact": [
            FeatureSpec("pre_woba", 1),
            FeatureSpec("pre_hardhit_rate", 1),
            FeatureSpec("pre_barrel_rate", 1),
            FeatureSpec("pre_sweet_spot_rate", 1),
            FeatureSpec("pre_air_bbe_rate", 1),
            FeatureSpec("pre_low_velo_xwoba", 1),
            FeatureSpec("pre_high_velo_xwoba", 1),
            FeatureSpec("pre_break_off_xwoba", 1),
            FeatureSpec("pre_hitter_count_xwoba", 1),
        ],
        "hitter_contact_discipline_floor": [
            FeatureSpec("pre_bb_pct", 1),
            FeatureSpec("pre_k_pct", -1),
            FeatureSpec("pre_whiff_per_swing", -1),
            FeatureSpec("pre_chase_rate", -1),
            FeatureSpec("pre_nonfast_chase_rate", -1),
            FeatureSpec("pre_nonfast_whiff_per_swing", -1),
            FeatureSpec("pre_zone_swing_rate", 1),
        ],
        "hitter_milb_surface_power": [
            FeatureSpec("pre_kbo_milb_ops", 1),
            FeatureSpec("pre_kbo_milb_obp", 1),
            FeatureSpec("pre_kbo_milb_slg", 1),
            FeatureSpec("pre_kbo_milb_hr", 1),
            FeatureSpec("pre_kbo_milb_bb_pct", 1),
            FeatureSpec("pre_kbo_milb_k_pct", -1),
        ],
        "hitter_track_continuity": [
            FeatureSpec("pre_kbo_milb_latest_year", 1),
            FeatureSpec("pre_kbo_milb_recent_rows", 1),
            FeatureSpec("pre_kbo_milb_highest_level_score", 1),
            FeatureSpec("pre_kbo_aaa_rows", 1),
            FeatureSpec("pre_kbo_milb_pa", 1),
        ],
        "hitter_ssg_pilot_screen": [
            FeatureSpec("pre_ssg_message_screen_score", 1),
        ],
    },
    "pitcher": {
        "pitcher_damage_suppression": [
            FeatureSpec("pre_woba_allowed", -1),
            FeatureSpec("pre_xwoba_allowed_bbe", -1),
            FeatureSpec("pre_xslg_allowed_bbe", -1),
            FeatureSpec("pre_hardhit_rate", -1),
            FeatureSpec("pre_barrel_rate", -1),
            FeatureSpec("pre_kbo_milb_hr9", -1),
            FeatureSpec("pre_kbo_milb_era", -1),
            FeatureSpec("pre_kbo_milb_whip", -1),
        ],
        "pitcher_command_floor": [
            FeatureSpec("pre_bb_hbp_pct", -1),
            FeatureSpec("pre_three_ball_pitch_rate", -1),
            FeatureSpec("pre_first_pitch_nonball_rate", -1),
            FeatureSpec("pre_zone_rate", 1),
            FeatureSpec("pre_kbo_milb_bb9", -1),
            FeatureSpec("pre_kbo_milb_bb_pct", -1),
        ],
        "pitcher_raw_miss_upside": [
            FeatureSpec("pre_k_pct", 1),
            FeatureSpec("pre_whiff_per_swing", 1),
            FeatureSpec("pre_chase_rate", 1),
            FeatureSpec("pre_kbo_milb_k9", 1),
            FeatureSpec("pre_kbo_milb_k_pct", 1),
        ],
        "pitcher_role_continuity_workload": [
            FeatureSpec("pre_start_proxy_rate", 1),
            FeatureSpec("pre_start_proxy_games", 1),
            FeatureSpec("pre_games_80plus_pitches", 1),
            FeatureSpec("pre_games_90plus_pitches", 1),
            FeatureSpec("pre_games_100plus_pitches", 1),
            FeatureSpec("pre_kbo_milb_ip", 1),
            FeatureSpec("pre_kbo_milb_games_started", 1),
            FeatureSpec("pre_kbo_milb_recent_rows", 1),
            FeatureSpec("pre_kbo_milb_latest_year", 1),
            FeatureSpec("pre_kbo_aaa_rows", 1),
        ],
        "pitcher_traffic_stress_control": [
            FeatureSpec("pre_runner_on_base_woba_allowed", -1),
            FeatureSpec("pre_risp_woba_allowed", -1),
            FeatureSpec("pre_third_time_woba_allowed", -1),
            FeatureSpec("pre_early_1_3_woba_allowed", -1),
            FeatureSpec("pre_starter_stabilizer_score", 1),
        ],
    },
}

TARGETS = ["success", "failure", "strong_success", "in_season_replaced", "injury_exit_flag", "performance_exit_flag"]
POSITIVE_TARGETS = {"success", "strong_success"}
RISK_TARGETS = {"failure", "in_season_replaced", "injury_exit_flag", "performance_exit_flag"}


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def safe_numeric(frame: pd.DataFrame, col: str) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(np.nan, index=frame.index)
    return pd.to_numeric(frame[col], errors="coerce")


def safe_median(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.median()) if len(values) else np.nan


def safe_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return float(values.mean()) if len(values) else np.nan


def z_score_by_role(frame: pd.DataFrame, role: str, feature: str) -> pd.Series:
    values = safe_numeric(frame, feature)
    role_mask = frame["role_model_family"].eq(role) & frame["has_model_pre_kbo_features"]
    basis = values[role_mask].dropna()
    out = pd.Series(np.nan, index=frame.index, dtype=float)
    if len(basis) < 5 or basis.nunique() <= 1:
        return out
    center = float(basis.median())
    scale = float(basis.std(ddof=0))
    if not np.isfinite(scale) or scale == 0:
        scale = float((basis.quantile(0.75) - basis.quantile(0.25)) / 1.349)
    if not np.isfinite(scale) or scale == 0:
        return out
    out.loc[role_mask] = (values.loc[role_mask] - center) / scale
    return out.clip(-3, 3)


def attach_family_scores(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for role, families in FEATURE_FAMILIES.items():
        role_mask = out["role_model_family"].eq(role)
        for family, specs in families.items():
            family_cols = []
            for spec in specs:
                z_col = f"z__{family}__{spec.feature}"
                out[z_col] = z_score_by_role(out, role, spec.feature) * spec.direction
                family_cols.append(z_col)
            score_col = f"{family}_score"
            count_col = f"{family}_nonnull_features"
            out[score_col] = np.nan
            out[count_col] = 0
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=RuntimeWarning)
                out.loc[role_mask, score_col] = out.loc[role_mask, family_cols].mean(axis=1, skipna=True)
            out.loc[role_mask, count_col] = out.loc[role_mask, family_cols].notna().sum(axis=1)
    return out


def load_bridge() -> pd.DataFrame:
    mart = pd.read_csv(MART_PATH)
    assignments = pd.read_csv(ASSIGNMENT_PATH)
    summary = pd.read_csv(SUMMARY_PATH)

    for col in ["has_pre_kbo_savant_features", "has_pre_kbo_milb", "has_model_pre_kbo_features", "label_available"]:
        if col in mart.columns:
            mart[col] = to_bool(mart[col])
    for col in TARGETS + ["success", "failure", "strong_success"]:
        if col in mart.columns:
            mart[col] = pd.to_numeric(mart[col], errors="coerce").fillna(0).astype(int)

    assignments = assignments.merge(
        summary[
            [
                "archetype_model_role",
                "archetype_cluster_id",
                "archetype_name",
                "success_rate",
                "failure_rate",
                "strong_success_rate",
            ]
        ],
        on=["archetype_model_role", "archetype_cluster_id"],
        how="left",
        validate="many_to_one",
    )
    assignments["role_model_family"] = assignments["archetype_model_role"].map({"starter": "pitcher"}).fillna(
        assignments["archetype_model_role"]
    )
    assignment_key = ["player_key", "season", "role_model_family"]
    assignments["cluster_label_alignment_score"] = np.where(
        pd.to_numeric(assignments["failure"], errors="coerce").fillna(0).eq(1),
        pd.to_numeric(assignments["failure_rate"], errors="coerce").fillna(0),
        pd.to_numeric(assignments["success_rate"], errors="coerce").fillna(0),
    )
    assignments = (
        assignments.sort_values(assignment_key + ["cluster_label_alignment_score"], ascending=[True, True, True, False])
        .drop_duplicates(assignment_key, keep="first")
        .reset_index(drop=True)
    )
    mart = mart.drop_duplicates(["player_key", "season", "role_model_family"]).reset_index(drop=True)
    archetype_cols = [
        "player_key",
        "season",
        "role_model_family",
        "archetype_cluster_id",
        "archetype_name",
        "archetype_input_features",
    ]
    out = mart.merge(
        assignments[archetype_cols],
        on=["player_key", "season", "role_model_family"],
        how="left",
        validate="one_to_one",
    )
    out = attach_family_scores(out)

    out["layer2_bridge_status"] = np.select(
        [
            out["archetype_name"].isna(),
            out["has_model_pre_kbo_features"].eq(True),
            out["label_available"].eq(True),
        ],
        [
            "missing_outcome_archetype",
            "outcome_archetype_with_prearrival_fingerprint",
            "outcome_archetype_label_only_no_prearrival_features",
        ],
        default="insufficient_label_or_feature_context",
    )
    out["layer2_release_policy"] = RELEASE_POLICY
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False
    out["score_release_allowed"] = False
    return out


def family_score_cols(role: str) -> list[str]:
    return [f"{family}_score" for family in FEATURE_FAMILIES[role]]


def nonnull_cols(role: str) -> list[str]:
    return [f"{family}_nonnull_features" for family in FEATURE_FAMILIES[role]]


def describe_fingerprint(row: pd.Series, role: str) -> tuple[str, str]:
    scores = []
    for family in FEATURE_FAMILIES[role]:
        col = f"median_{family}_score"
        value = row.get(col, np.nan)
        if pd.notna(value):
            scores.append((family, float(value)))
    if not scores:
        return "", ""
    strengths = [f"{family}:{value:+.2f}" for family, value in sorted(scores, key=lambda x: x[1], reverse=True)[:3]]
    risks = [f"{family}:{value:+.2f}" for family, value in sorted(scores, key=lambda x: x[1])[:3]]
    return " | ".join(strengths), " | ".join(risks)


def build_profiles(bridge: pd.DataFrame) -> pd.DataFrame:
    rows = []
    grouped = bridge[bridge["archetype_name"].notna()].groupby(
        ["role_model_family", "archetype_cluster_id", "archetype_name"],
        dropna=False,
    )
    for (role, cluster_id, archetype), group in grouped:
        role = str(role)
        if group["injury_exit_flag"].mean() >= 0.65:
            subtype = "injury_exit_cluster"
        elif group["performance_exit_flag"].mean() >= 0.65:
            subtype = "performance_exit_cluster"
        elif group["failure"].mean() >= 0.70:
            subtype = "low_impact_or_replacement_cluster"
        elif group["strong_success"].mean() >= 0.45:
            subtype = "strong_success_cluster"
        else:
            subtype = "survivor_cluster"
        ready = group[group["has_model_pre_kbo_features"]].copy()
        row = {
            "role_model_family": role,
            "archetype_cluster_id": cluster_id,
            "archetype_name": archetype,
            "archetype_signature": f"{archetype}__c{int(cluster_id)}__{subtype}",
            "archetype_subtype": subtype,
            "rows": len(group),
            "model_ready_rows": int(group["has_model_pre_kbo_features"].sum()),
            "success_rate": group["success"].mean(),
            "strong_success_rate": group["strong_success"].mean(),
            "failure_rate": group["failure"].mean(),
            "in_season_replaced_rate": group["in_season_replaced"].mean(),
            "injury_exit_rate": group["injury_exit_flag"].mean(),
            "performance_exit_rate": group["performance_exit_flag"].mean(),
            "median_first_kbo_pa": group["first_kbo_pa"].median(),
            "median_first_kbo_ip": group["first_kbo_ip"].median(),
            "median_first_kbo_war": group["first_kbo_war"].median(),
        }
        if role in FEATURE_FAMILIES:
            for score_col in family_score_cols(role):
                row[f"median_{score_col}"] = safe_median(ready[score_col])
                row[f"mean_{score_col}"] = safe_mean(ready[score_col])
            for count_col in nonnull_cols(role):
                row[f"median_{count_col}"] = safe_median(ready[count_col])
            strengths, risks = describe_fingerprint(pd.Series(row), role)
            row["prearrival_strength_fingerprint"] = strengths
            row["prearrival_risk_fingerprint"] = risks
        row["prearrival_profile_gate"] = np.select(
            [row["model_ready_rows"] >= 12, row["model_ready_rows"] >= 6, row["model_ready_rows"] > 0],
            ["usable_descriptive_profile", "thin_profile_use_with_caution", "very_thin_profile_watch_only"],
            default="no_prearrival_profile",
        )
        row["release_policy"] = RELEASE_POLICY
        row["candidate_release_allowed"] = False
        rows.append(row)
    return pd.DataFrame(rows).sort_values(
        ["role_model_family", "failure_rate", "success_rate", "archetype_cluster_id"],
        ascending=[True, False, False, True],
    )


def target_rate_delta(frame: pd.DataFrame, condition: pd.Series, target: str) -> tuple[float, float, float]:
    target_values = pd.to_numeric(frame[target], errors="coerce").fillna(0).astype(float)
    if condition.sum() == 0:
        return np.nan, float(target_values.mean()), np.nan
    rule_rate = float(target_values[condition].mean())
    base_rate = float(target_values.mean())
    return rule_rate, base_rate, rule_rate - base_rate


def permutation_p_value(frame: pd.DataFrame, condition: pd.Series, target: str, observed_delta: float) -> float:
    if pd.isna(observed_delta) or condition.sum() < 3:
        return np.nan
    rng = np.random.default_rng(RANDOM_SEED + len(frame) + int(condition.sum()))
    y = pd.to_numeric(frame[target], errors="coerce").fillna(0).astype(float).to_numpy()
    mask = condition.to_numpy(dtype=bool)
    more_extreme = 0
    reps = 500
    for _ in range(reps):
        shuffled = rng.permutation(y)
        perm_delta = float(shuffled[mask].mean() - shuffled.mean())
        if abs(perm_delta) >= abs(observed_delta):
            more_extreme += 1
    return (more_extreme + 1) / (reps + 1)


def interpret_rule(rule_name: str, target: str, delta: float) -> tuple[str, str]:
    has_low = "low_bottom_tercile" in rule_name
    has_high = "high_top_tercile" in rule_name
    high_only = has_high and not has_low
    mixed_or_low = has_low

    if target in POSITIVE_TARGETS and delta > 0:
        direction = "success_enrichment"
        semantically_aligned = high_only
    elif target in POSITIVE_TARGETS and delta < 0:
        direction = "success_suppression"
        semantically_aligned = mixed_or_low
    elif target in RISK_TARGETS and delta > 0:
        direction = "risk_enrichment"
        semantically_aligned = mixed_or_low
    elif target in RISK_TARGETS and delta < 0:
        direction = "risk_suppression"
        semantically_aligned = high_only
    else:
        direction = "flat_or_unknown"
        semantically_aligned = False

    if semantically_aligned:
        return direction, "semantically_aligned"
    return direction, "counterintuitive_or_negative_control"


def classify_rule_gate(rule_name: str, target: str, delta: float, support: int, p_value: float) -> tuple[str, str, str]:
    direction, alignment = interpret_rule(rule_name, target, delta)
    enough_signal = support >= 5 and abs(delta) >= 0.18 and (pd.isna(p_value) or p_value <= 0.20)
    if enough_signal and alignment == "semantically_aligned":
        return "promote_as_research_archetype_signal", direction, alignment
    if enough_signal:
        return "counterintuitive_watch_do_not_score", direction, alignment
    return "watch_small_sample_signal", direction, alignment


def rule_rows_for_condition(
    role_df: pd.DataFrame,
    role: str,
    rule_name: str,
    condition: pd.Series,
    signal_type: str,
) -> list[dict[str, object]]:
    rows = []
    support = int(condition.sum())
    if support < 4:
        return rows
    for target in TARGETS:
        if target not in role_df.columns or role_df[target].nunique() < 2:
            continue
        rule_rate, base_rate, delta = target_rate_delta(role_df, condition, target)
        p_value = permutation_p_value(role_df, condition, target, delta)
        rule_gate, direction, alignment = classify_rule_gate(rule_name, target, delta, support, p_value)
        rows.append(
            {
                "role_model_family": role,
                "signal_type": signal_type,
                "rule": rule_name,
                "target": target,
                "support_rows": support,
                "total_role_rows": len(role_df),
                "support_share": support / len(role_df) if len(role_df) else np.nan,
                "target_rate_inside_rule": rule_rate,
                "role_base_target_rate": base_rate,
                "rate_delta_vs_role_base": delta,
                "lift_vs_role_base": (rule_rate / base_rate) if base_rate else np.nan,
                "permutation_p_value": p_value,
                "signal_direction": direction,
                "semantic_alignment": alignment,
                "rule_gate": rule_gate,
                "release_policy": RELEASE_POLICY,
                "candidate_release_allowed": False,
            }
        )
    return rows


def build_rule_lifts(bridge: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    model_ready = bridge[bridge["has_model_pre_kbo_features"]].copy()
    for role, role_df in model_ready.groupby("role_model_family", dropna=False):
        role = str(role)
        if role not in FEATURE_FAMILIES or len(role_df) < 10:
            continue
        family_cols = family_score_cols(role)
        thresholds: dict[str, tuple[float, float]] = {}
        for col in family_cols:
            values = role_df[col].dropna()
            if len(values) < 8 or values.nunique() <= 1:
                continue
            thresholds[col] = (float(values.quantile(0.67)), float(values.quantile(0.33)))

        single_conditions: list[tuple[str, pd.Series]] = []
        for col, (high_cut, low_cut) in thresholds.items():
            family = col.replace("_score", "")
            high = role_df[col].ge(high_cut)
            low = role_df[col].le(low_cut)
            single_conditions.append((f"{family}=high_top_tercile", high))
            single_conditions.append((f"{family}=low_bottom_tercile", low))
            rows.extend(rule_rows_for_condition(role_df, role, f"{family}=high_top_tercile", high, "single_family"))
            rows.extend(rule_rows_for_condition(role_df, role, f"{family}=low_bottom_tercile", low, "single_family"))

        for i, (left_name, left_mask) in enumerate(single_conditions):
            for right_name, right_mask in single_conditions[i + 1 :]:
                left_family = left_name.split("=")[0]
                right_family = right_name.split("=")[0]
                if left_family == right_family:
                    continue
                combined = left_mask & right_mask
                rows.extend(
                    rule_rows_for_condition(
                        role_df,
                        role,
                        f"{left_name} AND {right_name}",
                        combined,
                        "two_family_interaction",
                    )
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["abs_rate_delta"] = out["rate_delta_vs_role_base"].abs()
    return out.sort_values(
        ["role_model_family", "target", "rule_gate", "abs_rate_delta", "support_rows"],
        ascending=[True, True, True, False, False],
    )


def build_feature_contract(profiles: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    promoted = rules[rules["rule_gate"].eq("promote_as_research_archetype_signal")].copy()
    rows = [
        {
            "slot": "foreign_hitter",
            "archetype_contract": "hitter_success_is_not_surface_power_only",
            "scouting_question": "Does the bat pair impact with contact/discipline floor and recent track continuity?",
            "candidate_side_proxy": "Savant pilot success component plus MiLB OPS/OBP/SLG, K%, BB%, and recent AAA/AA continuity",
            "evidence_output": str(PROFILE_OUT.relative_to(PROJECT_ROOT)),
            "model_gate": "hitter_savant_only_pilot_can_feed_L6_as_component",
            "release_policy": RELEASE_POLICY,
            "candidate_release_allowed": False,
        },
        {
            "slot": "foreign_pitcher",
            "archetype_contract": "raw_miss_needs_damage_and_command_separation",
            "scouting_question": "Is bat-missing supported by damage suppression, walk control, and starter workload continuity?",
            "candidate_side_proxy": "MiLB HR9/BB9/WHIP/ERA, Savant wOBA allowed, three-ball rate, and recent starter workload context",
            "evidence_output": str(RULE_OUT.relative_to(PROJECT_ROOT)),
            "model_gate": "pitcher_rules_are_research_signals_not_ranking_scores",
            "release_policy": RELEASE_POLICY,
            "candidate_release_allowed": False,
        },
        {
            "slot": "asian_quota",
            "archetype_contract": "asian_quota_needs_prearrival_context_before_translation",
            "scouting_question": "Can NPB/CPBL pre-arrival context be mapped to the same damage, command, contact, and continuity families?",
            "candidate_side_proxy": "NPB/CPBL official stats plus contract/buyout/nationality gates; no direct KBO archetype promotion yet",
            "evidence_output": str(PROFILE_OUT.relative_to(PROJECT_ROOT)),
            "model_gate": "needs_NPB_CPBL_historical_prearrival_backfill",
            "release_policy": RELEASE_POLICY,
            "candidate_release_allowed": False,
        },
    ]
    if not promoted.empty:
        top = (
            promoted.sort_values(["abs_rate_delta", "support_rows"], ascending=[False, False])
            .groupby(["role_model_family", "target"], as_index=False)
            .head(2)
        )
        for _, row in top.iterrows():
            rows.append(
                {
                    "slot": f"{row['role_model_family']}_archetype_rule",
            "archetype_contract": row["rule"],
            "scouting_question": (
                f"{row['signal_direction']} for {row['target']} with delta "
                f"{row['rate_delta_vs_role_base']:+.3f}"
            ),
                    "candidate_side_proxy": "Apply only as source-backed feature-family review, not as a final ranking score",
                    "evidence_output": str(RULE_OUT.relative_to(PROJECT_ROOT)),
                    "model_gate": row["rule_gate"],
                    "release_policy": RELEASE_POLICY,
                    "candidate_release_allowed": False,
                }
            )
    return pd.DataFrame(rows)


def build_gate_audit(bridge: pd.DataFrame, profiles: pd.DataFrame, rules: pd.DataFrame) -> pd.DataFrame:
    locks = ["is_final_recommendation", "shortlist_label_allowed", "candidate_name_release_allowed", "score_release_allowed"]
    return pd.DataFrame(
        [
            {
                "gate": "L2A",
                "check": "outcome_archetypes_joined_to_translation_mart",
                "pass_rows": int(bridge["archetype_name"].notna().sum()),
                "total_rows": len(bridge),
                "status": "pass" if bridge["archetype_name"].notna().all() else "partial",
                "blocking_gap": "Historical labels still cover only the current outcome-attached sample",
            },
            {
                "gate": "L2B",
                "check": "prearrival_fingerprint_rows_available",
                "pass_rows": int(bridge["has_model_pre_kbo_features"].sum()),
                "total_rows": len(bridge),
                "status": "partial_pass",
                "blocking_gap": "Only model-ready rows can support pre-arrival archetype mining",
            },
            {
                "gate": "L2C",
                "check": "archetype_profiles_created",
                "pass_rows": len(profiles),
                "total_rows": int(bridge[["role_model_family", "archetype_cluster_id"]].drop_duplicates().shape[0]),
                "status": "pass",
                "blocking_gap": "Profiles remain descriptive and should be used as feature contracts, not final decisions",
            },
            {
                "gate": "L2D",
                "check": "rule_lifts_mined_with_small_sample_gate",
                "pass_rows": int(rules["rule_gate"].eq("promote_as_research_archetype_signal").sum()) if not rules.empty else 0,
                "total_rows": len(rules),
                "status": "pass_research_only",
                "blocking_gap": "Rules are small-sample research signals and need candidate-side source validation",
            },
            {
                "gate": "L2E",
                "check": "release_locks_preserved",
                "pass_rows": int((bridge[locks].eq(False).all(axis=1)).sum()),
                "total_rows": len(bridge),
                "status": "pass",
                "blocking_gap": "No candidate recommendations or shortlist labels are released",
            },
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    bridge = load_bridge()
    profiles = build_profiles(bridge)
    rules = build_rule_lifts(bridge)
    contract = build_feature_contract(profiles, rules)
    audit = build_gate_audit(bridge, profiles, rules)

    bridge.to_csv(BRIDGE_OUT, index=False)
    profiles.to_csv(PROFILE_OUT, index=False)
    rules.to_csv(RULE_OUT, index=False)
    contract.to_csv(CONTRACT_OUT, index=False)
    audit.to_csv(GATE_OUT, index=False)

    print(f"wrote {BRIDGE_OUT.relative_to(PROJECT_ROOT)} rows={len(bridge)}")
    print(f"wrote {PROFILE_OUT.relative_to(PROJECT_ROOT)} rows={len(profiles)}")
    print(f"wrote {RULE_OUT.relative_to(PROJECT_ROOT)} rows={len(rules)}")
    print(f"wrote {CONTRACT_OUT.relative_to(PROJECT_ROOT)} rows={len(contract)}")
    print(f"wrote {GATE_OUT.relative_to(PROJECT_ROOT)} rows={len(audit)}")
    print()
    print(profiles[["role_model_family", "archetype_name", "rows", "model_ready_rows", "prearrival_strength_fingerprint", "prearrival_risk_fingerprint"]].to_string(index=False))
    print()
    if not rules.empty:
        print(rules.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
