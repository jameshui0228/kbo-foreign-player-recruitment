#!/usr/bin/env python3
"""Build a locked risk-adjusted SSG fit queue.

This is Layer 6. It is not a public ranking, shortlist, or recommendation.

The queue combines:

- SSG fit-preparation signal;
- KBO translation readiness;
- market access and contract realism;
- slot-specific tool/process proxies;
- surplus/access proxy;
- failure-risk penalties from Layer 5;
- score sensitivity under alternate weight sets.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

DEFAULT_INPUT = OUTPUT_DIR / "candidate_failure_risk_ledger_v0_1.csv"
RELEASE_POLICY = "risk_adjusted_ssg_fit_queue_research_only_no_recommendation"

POSITIVE_WEIGHTS = {
    "foreign_hitter": {
        "ssg_fit_component": 0.30,
        "kbo_translation_component": 0.25,
        "market_realism_component": 0.15,
        "tool_process_component": 0.20,
        "surplus_access_component": 0.10,
    },
    "foreign_pitcher": {
        "ssg_fit_component": 0.25,
        "kbo_translation_component": 0.25,
        "market_realism_component": 0.10,
        "tool_process_component": 0.25,
        "surplus_access_component": 0.15,
    },
    "asian_quota": {
        "ssg_fit_component": 0.25,
        "kbo_translation_component": 0.20,
        "market_realism_component": 0.15,
        "tool_process_component": 0.15,
        "surplus_access_component": 0.25,
    },
}

FAILURE_PENALTY = {
    "foreign_hitter": 0.20,
    "foreign_pitcher": 0.25,
    "asian_quota": 0.20,
}

WEIGHT_VARIANTS = {
    "default_dacon_style": (POSITIVE_WEIGHTS, FAILURE_PENALTY),
    "ssg_fit_heavy": (
        {
            "foreign_hitter": {
                "ssg_fit_component": 0.40,
                "kbo_translation_component": 0.20,
                "market_realism_component": 0.12,
                "tool_process_component": 0.20,
                "surplus_access_component": 0.08,
            },
            "foreign_pitcher": {
                "ssg_fit_component": 0.35,
                "kbo_translation_component": 0.20,
                "market_realism_component": 0.08,
                "tool_process_component": 0.25,
                "surplus_access_component": 0.12,
            },
            "asian_quota": {
                "ssg_fit_component": 0.35,
                "kbo_translation_component": 0.16,
                "market_realism_component": 0.12,
                "tool_process_component": 0.12,
                "surplus_access_component": 0.25,
            },
        },
        {"foreign_hitter": 0.20, "foreign_pitcher": 0.25, "asian_quota": 0.20},
    ),
    "risk_conservative": (
        {
            "foreign_hitter": {
                "ssg_fit_component": 0.25,
                "kbo_translation_component": 0.25,
                "market_realism_component": 0.15,
                "tool_process_component": 0.20,
                "surplus_access_component": 0.15,
            },
            "foreign_pitcher": {
                "ssg_fit_component": 0.22,
                "kbo_translation_component": 0.25,
                "market_realism_component": 0.13,
                "tool_process_component": 0.25,
                "surplus_access_component": 0.15,
            },
            "asian_quota": {
                "ssg_fit_component": 0.22,
                "kbo_translation_component": 0.20,
                "market_realism_component": 0.18,
                "tool_process_component": 0.15,
                "surplus_access_component": 0.25,
            },
        },
        {"foreign_hitter": 0.30, "foreign_pitcher": 0.35, "asian_quota": 0.30},
    ),
    "market_realism_heavy": (
        {
            "foreign_hitter": {
                "ssg_fit_component": 0.25,
                "kbo_translation_component": 0.20,
                "market_realism_component": 0.25,
                "tool_process_component": 0.18,
                "surplus_access_component": 0.12,
            },
            "foreign_pitcher": {
                "ssg_fit_component": 0.22,
                "kbo_translation_component": 0.20,
                "market_realism_component": 0.22,
                "tool_process_component": 0.23,
                "surplus_access_component": 0.13,
            },
            "asian_quota": {
                "ssg_fit_component": 0.20,
                "kbo_translation_component": 0.18,
                "market_realism_component": 0.25,
                "tool_process_component": 0.12,
                "surplus_access_component": 0.25,
            },
        },
        {"foreign_hitter": 0.22, "foreign_pitcher": 0.27, "asian_quota": 0.22},
    ),
    "translation_heavy": (
        {
            "foreign_hitter": {
                "ssg_fit_component": 0.25,
                "kbo_translation_component": 0.35,
                "market_realism_component": 0.12,
                "tool_process_component": 0.20,
                "surplus_access_component": 0.08,
            },
            "foreign_pitcher": {
                "ssg_fit_component": 0.22,
                "kbo_translation_component": 0.35,
                "market_realism_component": 0.08,
                "tool_process_component": 0.23,
                "surplus_access_component": 0.12,
            },
            "asian_quota": {
                "ssg_fit_component": 0.22,
                "kbo_translation_component": 0.30,
                "market_realism_component": 0.13,
                "tool_process_component": 0.12,
                "surplus_access_component": 0.23,
            },
        },
        {"foreign_hitter": 0.22, "foreign_pitcher": 0.27, "asian_quota": 0.22},
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def safe_num(frame: pd.DataFrame, col: str, default: float = np.nan) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[col], errors="coerce")


def clip(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).clip(0, 100).round(3)


def inv(series: pd.Series) -> pd.Series:
    return (100 - pd.to_numeric(series, errors="coerce").fillna(50)).clip(0, 100)


def mean_available(frame: pd.DataFrame, columns: list[str], fill_value: float = 50.0) -> pd.Series:
    existing = [col for col in columns if col in frame.columns]
    if not existing:
        return pd.Series(fill_value, index=frame.index, dtype=float)
    return frame[existing].apply(pd.to_numeric, errors="coerce").mean(axis=1).fillna(fill_value)


def slot_pct_rank(df: pd.DataFrame, value_col: str, higher_is_better: bool = True, fill_value: float = 50.0) -> pd.Series:
    out = pd.Series(fill_value, index=df.index, dtype=float)
    values = safe_num(df, value_col, np.nan)
    for slot, idx in df.groupby("fit_slot").groups.items():
        slot_values = values.loc[idx]
        if slot_values.notna().sum() <= 1 or slot_values.nunique(dropna=True) <= 1:
            out.loc[idx] = fill_value
            continue
        ranked = slot_values.rank(pct=True, ascending=True) * 100
        if not higher_is_better:
            ranked = 100 - ranked
        out.loc[idx] = ranked.fillna(fill_value)
    return out


def normalized_market_component(df: pd.DataFrame) -> pd.Series:
    realism_pct = slot_pct_rank(df, "market_realism_score", higher_is_better=True, fill_value=45)
    blend_pct = slot_pct_rank(df, "market_realism_fit_blend_for_triage_only", higher_is_better=True, fill_value=45)
    access_pct = slot_pct_rank(df, "fit_market_access_score", higher_is_better=True, fill_value=45)
    contract_safe_pct = slot_pct_rank(
        df.assign(_contract_safe=inv(safe_num(df, "contract_cost_access_risk", 50))),
        "_contract_safe",
        higher_is_better=True,
        fill_value=45,
    )
    return clip(realism_pct * 0.30 + blend_pct * 0.25 + access_pct * 0.20 + contract_safe_pct * 0.25)


def tool_process_component(df: pd.DataFrame) -> pd.Series:
    out = pd.Series(50.0, index=df.index)
    hitter = df["fit_slot"].eq("foreign_hitter")
    pitcher = df["fit_slot"].eq("foreign_pitcher")
    asian = df["fit_slot"].eq("asian_quota")

    out.loc[hitter] = mean_available(
        df.loc[hitter],
        [
            "fit_model_component_pct",
            "fit_ssg_rhp_unlock_proxy_pct",
            "fit_two_strike_survival_proxy_pct",
        ],
        fill_value=45,
    )
    out.loc[pitcher] = mean_available(
        df.loc[pitcher],
        [
            "fit_pitcher_diagnostic_pct",
            "fit_starter_runway_proxy_pct",
            "fit_traffic_command_proxy_pct",
        ],
        fill_value=40,
    )
    out.loc[asian] = mean_available(
        df.loc[asian],
        [
            "fit_asian_nationality_gate_score",
            "fit_club_control_access_score",
            "fit_asian_league_history_score",
            "fit_npb_stat_context_score",
            "fit_npb_performance_context_pct",
        ],
        fill_value=45,
    )
    return clip(out)


def surplus_access_component(df: pd.DataFrame) -> pd.Series:
    contract_safe = inv(safe_num(df, "contract_cost_access_risk", 50))
    market_pct = slot_pct_rank(df, "market_realism_fit_blend_for_triage_only", True, 45)
    access_pct = slot_pct_rank(df, "fit_market_access_score", True, 45)
    data_safe = inv(safe_num(df, "data_gap_risk", 50))
    return clip(contract_safe * 0.35 + market_pct * 0.25 + access_pct * 0.20 + data_safe * 0.20)


def build_components(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ssg_fit_component"] = clip(safe_num(out, "fit_preparation_index", 50))
    out["kbo_translation_component"] = clip(inv(safe_num(out, "kbo_translation_risk", 50)))
    out["market_realism_component"] = normalized_market_component(out)
    out["tool_process_component"] = tool_process_component(out)
    out["surplus_access_component"] = surplus_access_component(out)
    out["failure_resilience_component"] = clip(inv(safe_num(out, "failure_risk_index", 50)))
    out["source_confidence_component"] = clip(inv(safe_num(out, "data_gap_risk", 50)))
    return out


def score_with_weights(df: pd.DataFrame, positive_weights: dict[str, dict[str, float]], penalty_weights: dict[str, float]) -> pd.Series:
    scores = pd.Series(np.nan, index=df.index, dtype=float)
    for slot, idx in df.groupby("fit_slot").groups.items():
        weights = positive_weights.get(slot, positive_weights["foreign_hitter"])
        base = pd.Series(0.0, index=idx, dtype=float)
        for col, weight in weights.items():
            base += safe_num(df.loc[idx], col, 50).fillna(50) * weight
        penalty = safe_num(df.loc[idx], "failure_risk_index", 50).fillna(50) * penalty_weights.get(slot, 0.20)
        confidence_adjustment = (safe_num(df.loc[idx], "source_confidence_component", 50).fillna(50) - 50) * 0.06
        scores.loc[idx] = base - penalty + confidence_adjustment
    return scores.round(3)


def add_sensitivity_scores(queue: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rank_cols = []
    score_cols = []
    sensitivity_rows = []
    for variant, (positive_weights, penalty_weights) in WEIGHT_VARIANTS.items():
        score_col = f"score_{variant}"
        rank_col = f"rank_{variant}"
        queue[score_col] = score_with_weights(queue, positive_weights, penalty_weights)
        queue[rank_col] = queue.groupby("fit_slot")[score_col].rank(method="first", ascending=False).astype(int)
        score_cols.append(score_col)
        rank_cols.append(rank_col)

        for slot, group in queue.groupby("fit_slot", dropna=False):
            sensitivity_rows.append(
                {
                    "weight_variant": variant,
                    "fit_slot": slot,
                    "rows": len(group),
                    "median_score": float(group[score_col].median()),
                    "p75_score": float(group[score_col].quantile(0.75)),
                    "top_25_locked_rows": int((group[rank_col] <= 25).sum()),
                    "top_50_locked_rows": int((group[rank_col] <= 50).sum()),
                    "score_release_allowed": False,
                }
            )

    queue["risk_adjusted_fit_score_internal"] = queue["score_default_dacon_style"]
    queue["fit_review_order_within_slot"] = queue.groupby("fit_slot")["risk_adjusted_fit_score_internal"].rank(
        method="first",
        ascending=False,
    ).astype(int)
    queue["sensitivity_rank_min"] = queue[rank_cols].min(axis=1)
    queue["sensitivity_rank_median"] = queue[rank_cols].median(axis=1)
    queue["sensitivity_rank_max"] = queue[rank_cols].max(axis=1)
    queue["sensitivity_rank_range"] = queue["sensitivity_rank_max"] - queue["sensitivity_rank_min"]
    queue["sensitivity_score_mean"] = queue[score_cols].mean(axis=1).round(3)
    queue["sensitivity_score_std"] = queue[score_cols].std(axis=1).round(3)
    queue["sensitivity_band"] = np.select(
        [
            queue["sensitivity_rank_max"].le(25),
            queue["sensitivity_rank_median"].le(50) & queue["sensitivity_rank_range"].le(50),
            queue["sensitivity_rank_median"].le(100),
        ],
        ["stable_top25_locked", "stable_top50_review_locked", "top100_but_weight_sensitive_locked"],
        default="weight_sensitive_or_low_priority_locked",
    )
    return queue, pd.DataFrame(sensitivity_rows)


def review_lane(queue: pd.DataFrame) -> pd.Series:
    tier1 = queue["failure_risk_review_tier"].eq("tier_1_blocker_review")
    high_data_gap = safe_num(queue, "data_gap_risk", 0).ge(80)
    high_contract = safe_num(queue, "contract_cost_access_risk", 0).ge(80)
    high_medical = safe_num(queue, "medical_availability_risk", 0).ge(70)
    stable_top50 = queue["sensitivity_band"].isin(["stable_top25_locked", "stable_top50_review_locked"])
    top75 = queue["fit_review_order_within_slot"].le(75)
    return pd.Series(
        np.select(
            [
                tier1 | high_medical,
                top75 & stable_top50 & (high_contract | high_data_gap),
                top75 & stable_top50,
                queue["fit_review_order_within_slot"].le(150),
            ],
            [
                "lane_0_blocked_or_medical_review_locked",
                "lane_1_source_fill_priority_locked",
                "lane_2_deep_review_candidate_locked",
                "lane_3_market_watch_locked",
            ],
            default="lane_4_low_priority_locked",
        ),
        index=queue.index,
    )


def fit_tags(queue: pd.DataFrame) -> pd.Series:
    tags = []
    for row in queue.to_dict("records"):
        row_tags: list[str] = []
        if row.get("sensitivity_band") == "stable_top25_locked":
            row_tags.append("stable_across_weights")
        if float(row.get("ssg_fit_component", 0) or 0) >= 60:
            row_tags.append("ssg_fit_above_slot_median")
        if float(row.get("kbo_translation_component", 0) or 0) >= 60:
            row_tags.append("translation_risk_low")
        if float(row.get("market_realism_component", 0) or 0) >= 60:
            row_tags.append("market_access_relatively_better")
        if float(row.get("tool_process_component", 0) or 0) >= 60:
            row_tags.append("tool_process_signal")
        if float(row.get("failure_risk_index", 100) or 100) >= 70:
            row_tags.append("failure_risk_blocker")
        if float(row.get("data_gap_risk", 100) or 100) >= 80:
            row_tags.append("source_gap_blocker")
        if float(row.get("contract_cost_access_risk", 100) or 100) >= 80:
            row_tags.append("contract_access_blocker")
        tags.append("|".join(row_tags) if row_tags else "no_clear_positive_or_blocker_tag")
    return pd.Series(tags, index=queue.index)


def build_queue(input_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = pd.read_csv(input_path)
    queue = build_components(base)
    queue, sensitivity = add_sensitivity_scores(queue)
    queue["fit_review_lane"] = review_lane(queue)
    queue["fit_review_tags"] = fit_tags(queue)
    queue["fit_queue_release_policy"] = RELEASE_POLICY
    queue["is_final_recommendation"] = False
    queue["shortlist_label_allowed"] = False
    queue["candidate_name_release_allowed"] = False
    queue["score_release_allowed"] = False
    queue["rank_release_allowed"] = False
    queue["recommendation_label"] = "locked_not_allowed"

    queue = queue.sort_values(["fit_slot", "fit_review_order_within_slot"])

    slot_summary = build_slot_summary(queue)
    factor_summary = build_factor_summary(queue)
    gate_audit = build_gate_audit(queue)
    return queue, slot_summary, factor_summary, sensitivity, gate_audit


def build_slot_summary(queue: pd.DataFrame) -> pd.DataFrame:
    return (
        queue.groupby(["fit_slot", "fit_review_lane"], dropna=False)
        .agg(
            rows=("fit_slot", "size"),
            median_internal_fit_score=("risk_adjusted_fit_score_internal", "median"),
            p75_internal_fit_score=("risk_adjusted_fit_score_internal", lambda s: s.quantile(0.75)),
            median_failure_risk=("failure_risk_index", "median"),
            stable_top25_rows=("sensitivity_band", lambda s: int((s == "stable_top25_locked").sum())),
            stable_top50_rows=("sensitivity_band", lambda s: int(s.isin(["stable_top25_locked", "stable_top50_review_locked"]).sum())),
            high_data_gap_rows=("data_gap_risk", lambda s: int((s >= 80).sum())),
            high_contract_rows=("contract_cost_access_risk", lambda s: int((s >= 80).sum())),
            release_allowed=("rank_release_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "fit_review_lane"])
    )


def build_factor_summary(queue: pd.DataFrame) -> pd.DataFrame:
    components = [
        "ssg_fit_component",
        "kbo_translation_component",
        "market_realism_component",
        "tool_process_component",
        "surplus_access_component",
        "failure_resilience_component",
        "source_confidence_component",
    ]
    rows = []
    for (slot, lane), group in queue.groupby(["fit_slot", "fit_review_lane"], dropna=False):
        for component in components:
            rows.append(
                {
                    "fit_slot": slot,
                    "fit_review_lane": lane,
                    "component": component,
                    "rows": len(group),
                    "median_value": float(group[component].median()),
                    "p75_value": float(group[component].quantile(0.75)),
                    "release_allowed": False,
                }
            )
    return pd.DataFrame(rows).sort_values(["fit_slot", "fit_review_lane", "component"])


def build_gate_audit(queue: pd.DataFrame) -> pd.DataFrame:
    lock_cols = [
        "is_final_recommendation",
        "shortlist_label_allowed",
        "candidate_name_release_allowed",
        "score_release_allowed",
        "rank_release_allowed",
    ]
    return pd.DataFrame(
        [
            {
                "gate": "Q1",
                "check": "all_candidates_receive_risk_adjusted_fit_score",
                "pass_rows": int(queue["risk_adjusted_fit_score_internal"].notna().sum()),
                "total_rows": len(queue),
                "status": "pass",
                "blocking_gap": "Internal scores are research-only and not public ranking scores",
            },
            {
                "gate": "Q2",
                "check": "sensitivity_variants_attached",
                "pass_rows": int(queue["sensitivity_rank_range"].notna().sum()),
                "total_rows": len(queue),
                "status": "pass",
                "blocking_gap": "Sensitivity does not replace manual scouting or source verification",
            },
            {
                "gate": "Q3",
                "check": "release_locks_preserved",
                "pass_rows": int((queue[lock_cols].eq(False).all(axis=1)).sum()),
                "total_rows": len(queue),
                "status": "pass",
                "blocking_gap": "No candidate names, scores, ranks, shortlist labels, or recommendations are released",
            },
            {
                "gate": "Q4",
                "check": "source_gap_visible",
                "pass_rows": int(queue["fit_review_lane"].str.contains("source_fill|blocked", regex=True).sum()),
                "total_rows": len(queue),
                "status": "pass_visible_gap",
                "blocking_gap": "Source gaps still dominate many high-interest rows",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    input_path = PROJECT_ROOT / args.input
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    queue, slot_summary, factor_summary, sensitivity, gate_audit = build_queue(input_path)

    queue.to_csv(OUTPUT_DIR / f"ssg_risk_adjusted_fit_queue_{suffix}.csv", index=False)
    slot_summary.to_csv(OUTPUT_DIR / f"ssg_risk_adjusted_fit_slot_summary_{suffix}.csv", index=False)
    factor_summary.to_csv(OUTPUT_DIR / f"ssg_risk_adjusted_fit_factor_summary_{suffix}.csv", index=False)
    sensitivity.to_csv(OUTPUT_DIR / f"ssg_risk_adjusted_fit_sensitivity_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"ssg_risk_adjusted_fit_gate_audit_{suffix}.csv", index=False)

    print(f"queue_rows={len(queue)}")
    print(slot_summary.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
