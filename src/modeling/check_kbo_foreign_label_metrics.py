#!/usr/bin/env python3
"""Validate the KBO foreign-player label table before model training."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LABEL_PATH = PROJECT_ROOT / "outputs/tables/kbo_foreign_player_season_labels_v0_1.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

TARGET_ONLY_COLUMNS = [
    "first_kbo_pa",
    "first_kbo_ip",
    "first_kbo_war",
    "first_kbo_wrc_plus",
    "first_kbo_era",
    "first_kbo_k_bb_pct",
    "renewed_next_year",
    "in_season_replaced",
    "injury_exit_flag",
    "performance_exit_flag",
    "temporary_foreign_flag",
    "success",
    "strong_success",
    "failure",
]

BACKTEST_FOLDS = [
    ("fold_a_2022_holdout", 2017, 2021, 2022),
    ("fold_b_2023_holdout", 2017, 2022, 2023),
    ("fold_c_2024_holdout", 2017, 2023, 2024),
    ("fold_d_2025_holdout", 2017, 2024, 2025),
]


def safe_rate(series: pd.Series) -> float:
    valid = pd.to_numeric(series, errors="coerce").dropna()
    if valid.empty:
        return np.nan
    return float(valid.mean())


def majority_baseline_accuracy(train: pd.DataFrame, valid: pd.DataFrame, target: str) -> float:
    train_target = pd.to_numeric(train[target], errors="coerce").dropna()
    valid_target = pd.to_numeric(valid[target], errors="coerce").dropna()
    if train_target.empty or valid_target.empty:
        return np.nan
    majority = int(train_target.mean() >= 0.5)
    return float((valid_target.astype(int).eq(majority)).mean())


def build_overview(labels: pd.DataFrame) -> pd.DataFrame:
    current = labels[labels["season"].eq(2026)]
    checks = [
        {
            "check": "rows_total",
            "value": len(labels),
            "status": "pass" if len(labels) > 0 else "fail",
            "note": "foreign-player season rows",
        },
        {
            "check": "label_available_rows",
            "value": int(labels["label_available"].fillna(False).sum()),
            "status": "pass" if labels["label_available"].fillna(False).sum() > 100 else "warn",
            "note": "rows usable as historical supervised labels",
        },
        {
            "check": "statiz_outcome_rows",
            "value": int(labels["outcome_available"].fillna(False).sum()),
            "status": "pass" if labels["outcome_available"].fillna(False).sum() >= 100 else "warn",
            "note": "rows with local STATIZ performance outcomes attached",
        },
        {
            "check": "current_2026_labels_withheld",
            "value": int(current["label_available"].fillna(False).sum()) if not current.empty else 0,
            "status": "pass" if current.empty or current["label_available"].fillna(False).sum() == 0 else "fail",
            "note": "2026 should be current context, not completed-season label",
        },
        {
            "check": "target_only_column_count",
            "value": len(TARGET_ONLY_COLUMNS),
            "status": "pass",
            "note": "these columns are forbidden as candidate ranking features",
        },
        {
            "check": "required_identity_non_null",
            "value": int(labels[["player_key", "season", "player_name", "kbo_team"]].isna().sum().sum()),
            "status": "pass"
            if int(labels[["player_key", "season", "player_name", "kbo_team"]].isna().sum().sum()) == 0
            else "fail",
            "note": "identity grain should be complete",
        },
    ]
    return pd.DataFrame(checks)


def build_fold_report(labels: pd.DataFrame) -> pd.DataFrame:
    usable = labels[labels["label_available"].fillna(False)].copy()
    rows = []
    for fold_name, train_start, train_end, valid_year in BACKTEST_FOLDS:
        train = usable[usable["season"].between(train_start, train_end)]
        valid = usable[usable["season"].eq(valid_year)]
        rows.append(
            {
                "fold": fold_name,
                "train_years": f"{train_start}-{train_end}",
                "valid_year": valid_year,
                "train_rows": len(train),
                "valid_rows": len(valid),
                "train_success_rate": safe_rate(train["success"]),
                "valid_success_rate": safe_rate(valid["success"]),
                "train_failure_rate": safe_rate(train["failure"]),
                "valid_failure_rate": safe_rate(valid["failure"]),
                "success_majority_baseline_acc": majority_baseline_accuracy(train, valid, "success"),
                "failure_majority_baseline_acc": majority_baseline_accuracy(train, valid, "failure"),
                "high_confidence_valid_rows": int(valid["source_confidence_1_5"].ge(4).sum()),
                "outcome_valid_rows": int(valid["outcome_available"].fillna(False).sum()),
                "fold_status": "usable" if len(train) >= 100 and len(valid) >= 30 else "thin",
            }
        )
    return pd.DataFrame(rows)


def build_segment_report(labels: pd.DataFrame) -> pd.DataFrame:
    usable = labels[labels["label_available"].fillna(False)].copy()
    group_cols = ["season", "role_group"]
    return (
        usable.groupby(group_cols, dropna=False)
        .agg(
            rows=("player_key", "count"),
            outcome_rows=("outcome_available", "sum"),
            released_rows=("in_season_replaced", "sum"),
            success_rate=("success", "mean"),
            strong_success_rate=("strong_success", "mean"),
            failure_rate=("failure", "mean"),
            avg_source_confidence=("source_confidence_1_5", "mean"),
        )
        .reset_index()
        .sort_values(group_cols)
    )


def build_forbidden_columns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "column": TARGET_ONLY_COLUMNS,
            "allowed_as_candidate_feature": False,
            "allowed_as_label_or_validation_outcome": True,
            "reason": "post-KBO outcome; using it for candidate ranking would be target leakage",
        }
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    labels = pd.read_csv(LABEL_PATH)

    overview = build_overview(labels)
    folds = build_fold_report(labels)
    segments = build_segment_report(labels)
    forbidden = build_forbidden_columns()

    overview_path = OUTPUT_DIR / "kbo_foreign_label_metric_overview_v0_1.csv"
    fold_path = OUTPUT_DIR / "kbo_foreign_label_backtest_folds_v0_1.csv"
    segment_path = OUTPUT_DIR / "kbo_foreign_label_segment_balance_v0_1.csv"
    forbidden_path = OUTPUT_DIR / "kbo_foreign_label_forbidden_feature_columns_v0_1.csv"

    overview.to_csv(overview_path, index=False)
    folds.to_csv(fold_path, index=False)
    segments.to_csv(segment_path, index=False)
    forbidden.to_csv(forbidden_path, index=False)

    print("wrote", overview_path)
    print("wrote", fold_path)
    print("wrote", segment_path)
    print("wrote", forbidden_path)
    print(overview.to_string(index=False))
    print()
    print(folds.to_string(index=False))


if __name__ == "__main__":
    main()
