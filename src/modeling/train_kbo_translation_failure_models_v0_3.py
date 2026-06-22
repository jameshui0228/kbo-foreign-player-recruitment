#!/usr/bin/env python3
"""Train augmented KBO translation/failure models after Layer 2 backfill."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from train_kbo_translation_failure_models_v0_2 import (
    MODEL_READY_FLAG,
    TARGETS,
    build_feature_signals,
    run_repeated_stratified_cv,
    run_time_folds,
    summarize_scores,
    to_bool,
    trainable_rows,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
DEFAULT_MART = OUTPUT_DIR / "kbo_translation_feature_mart_backfill_augmented_v0_1.csv"
PREVIOUS_REPEATED = OUTPUT_DIR / "kbo_translation_failure_repeated_cv_comparison_v0_2.csv"
RELEASE_POLICY = "kbo_translation_v0_3_augmented_training_no_current_candidate_release"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mart", default=str(DEFAULT_MART.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_3")
    return parser.parse_args()


def compare_to_previous(current: pd.DataFrame, previous_path: Path) -> pd.DataFrame:
    if not previous_path.exists() or current.empty:
        return pd.DataFrame()
    previous = pd.read_csv(previous_path)
    key_cols = ["validation_scheme", "role_model_family", "target", "model"]
    metric_cols = [
        "folds",
        "total_valid_rows",
        "mean_feature_count",
        "mean_auc",
        "mean_brier",
        "mean_logloss",
        "mean_precision_top_25pct",
        "mean_precision_top_33pct",
        "brier_lift_vs_role_prior",
        "top25_precision_lift_vs_role_prior",
        "promotion_status",
    ]
    left = previous[key_cols + [col for col in metric_cols if col in previous.columns]]
    right = current[key_cols + [col for col in metric_cols if col in current.columns]]
    out = left.merge(right, on=key_cols, how="outer", suffixes=("_v0_2", "_v0_3"))
    for metric in ["mean_brier", "mean_auc", "mean_precision_top_25pct", "total_valid_rows", "mean_feature_count"]:
        a = f"{metric}_v0_2"
        b = f"{metric}_v0_3"
        if a in out.columns and b in out.columns:
            out[f"{metric}_delta_v0_3_minus_v0_2"] = out[b] - out[a]
    if "mean_brier_delta_v0_3_minus_v0_2" in out.columns:
        out["brier_direction"] = np.select(
            [
                out["mean_brier_delta_v0_3_minus_v0_2"].lt(-0.005),
                out["mean_brier_delta_v0_3_minus_v0_2"].gt(0.005),
            ],
            ["improved", "worse"],
            default="flat",
        )
    return out.sort_values(key_cols)


def build_readiness(mart: pd.DataFrame, repeated: pd.DataFrame, comparison: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    trainable = trainable_rows(mart)
    rows = []
    for scope, frame in [("all", mart)] + [
        (role, mart[mart["role_model_family"].eq(role)]) for role in sorted(mart["role_model_family"].dropna().unique())
    ]:
        train = trainable if scope == "all" else trainable[trainable["role_model_family"].eq(scope)]
        repeated_scope = repeated if scope == "all" else repeated[repeated["role_model_family"].eq(scope)]
        signal_scope = signals if scope == "all" else signals[signals["role_model_family"].eq(scope)]
        rows.append(
            {
                "scope": scope,
                "rows": len(frame),
                "trainable_rows": len(train),
                "model_ready_rate": round(len(train) / len(frame), 4) if len(frame) else np.nan,
                "repeated_cv_rows": len(repeated_scope),
                "feature_signal_rows": len(signal_scope),
                "pilot_promote_rows": int(repeated_scope.get("promotion_status", pd.Series(dtype=str)).eq("pilot_promote").sum()),
                "watch_rows": int(repeated_scope.get("promotion_status", pd.Series(dtype=str)).eq("watch").sum()),
                "release_policy": RELEASE_POLICY,
                "candidate_release_allowed": False,
            }
        )
    if not comparison.empty:
        improved = comparison.get("brier_direction", pd.Series(dtype=str)).eq("improved").sum()
        flat = comparison.get("brier_direction", pd.Series(dtype=str)).eq("flat").sum()
        rows.append(
            {
                "scope": "v0_2_vs_v0_3",
                "rows": len(comparison),
                "trainable_rows": int(trainable.shape[0]),
                "model_ready_rate": round(trainable.shape[0] / mart.shape[0], 4),
                "repeated_cv_rows": len(comparison),
                "feature_signal_rows": int(signals.shape[0]),
                "pilot_promote_rows": int(improved),
                "watch_rows": int(flat),
                "release_policy": RELEASE_POLICY,
                "candidate_release_allowed": False,
            }
        )
    return pd.DataFrame(rows)


def build_gate_audit(mart: pd.DataFrame, repeated: pd.DataFrame, comparison: pd.DataFrame, signals: pd.DataFrame) -> pd.DataFrame:
    trainable = trainable_rows(mart)
    model_ready_rate = trainable.shape[0] / mart.shape[0] if len(mart) else 0
    return pd.DataFrame(
        [
            {
                "gate": "G4A",
                "layer": "KBO translation model",
                "check": "augmented_mart_trainable_coverage",
                "pass_rows": int(trainable.shape[0]),
                "total_rows": int(mart.shape[0]),
                "status": "pass" if model_ready_rate >= 0.95 else "pass_visible_gap",
                "blocking_gap": f"Model-ready rate is {model_ready_rate:.1%}; remaining rows need manual lookup or non-MLB sources.",
            },
            {
                "gate": "G4B",
                "layer": "KBO translation model",
                "check": "repeated_leakage_safe_cv_rerun",
                "pass_rows": int(len(repeated)),
                "total_rows": 1,
                "status": "pass" if len(repeated) > 0 else "fail",
                "blocking_gap": "Repeated stratified CV is research-only and small-sample guarded.",
            },
            {
                "gate": "G4C",
                "layer": "KBO translation model",
                "check": "v0_2_vs_v0_3_comparison_built",
                "pass_rows": int(len(comparison)),
                "total_rows": 1,
                "status": "pass" if len(comparison) > 0 else "fail",
                "blocking_gap": "Comparison is diagnostic; promotion still depends on model family stability.",
            },
            {
                "gate": "G4D",
                "layer": "KBO translation model",
                "check": "feature_signals_built",
                "pass_rows": int(len(signals)),
                "total_rows": 1,
                "status": "pass" if len(signals) > 0 else "fail",
                "blocking_gap": "Feature signals are explanatory model diagnostics, not causal claims.",
            },
            {
                "gate": "LOCK",
                "layer": "Release policy",
                "check": "historical_only_no_current_candidate_release",
                "pass_rows": 1,
                "total_rows": 1,
                "status": "pass",
                "blocking_gap": "Outputs are historical KBO rows and aggregate metrics; current candidate release remains locked.",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mart = pd.read_csv(PROJECT_ROOT / args.mart)
    for col in ["has_pre_kbo_savant_features", "has_pre_kbo_milb", MODEL_READY_FLAG, "label_available"]:
        if col in mart.columns:
            mart[col] = to_bool(mart[col])
    for col in TARGETS:
        mart[col] = pd.to_numeric(mart[col], errors="coerce").fillna(0).astype(int)

    preds, scores = run_time_folds(mart)
    repeated_scores = run_repeated_stratified_cv(mart)
    comparison = summarize_scores(scores)
    repeated_comparison = summarize_scores(repeated_scores)
    feature_signals = build_feature_signals(mart)
    v0_2_vs_v0_3 = compare_to_previous(repeated_comparison, PREVIOUS_REPEATED)
    readiness = build_readiness(mart, repeated_comparison, v0_2_vs_v0_3, feature_signals)
    gate_audit = build_gate_audit(mart, repeated_comparison, v0_2_vs_v0_3, feature_signals)

    preds.to_csv(OUTPUT_DIR / f"kbo_translation_failure_oof_predictions_{suffix}.csv", index=False)
    scores.to_csv(OUTPUT_DIR / f"kbo_translation_failure_fold_scores_{suffix}.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / f"kbo_translation_failure_model_comparison_{suffix}.csv", index=False)
    repeated_scores.to_csv(OUTPUT_DIR / f"kbo_translation_failure_repeated_cv_scores_{suffix}.csv", index=False)
    repeated_comparison.to_csv(OUTPUT_DIR / f"kbo_translation_failure_repeated_cv_comparison_{suffix}.csv", index=False)
    feature_signals.to_csv(OUTPUT_DIR / f"kbo_translation_failure_feature_signals_{suffix}.csv", index=False)
    v0_2_vs_v0_3.to_csv(OUTPUT_DIR / "kbo_translation_failure_v0_2_vs_v0_3_comparison.csv", index=False)
    readiness.to_csv(OUTPUT_DIR / f"kbo_translation_model_readiness_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"kbo_translation_retrain_gate_audit_{suffix}.csv", index=False)

    trainable = trainable_rows(mart)
    print("trainable rows", trainable.shape)
    print(trainable.groupby(["role_model_family", "model_feature_source"]).size().to_string())
    print("repeated_comparison")
    print(repeated_comparison.to_string(index=False))
    print("v0_2_vs_v0_3")
    print(v0_2_vs_v0_3.to_string(index=False))
    print("readiness")
    print(readiness.to_string(index=False))
    print("gate_audit")
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
