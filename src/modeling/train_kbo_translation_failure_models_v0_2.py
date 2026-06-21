#!/usr/bin/env python3
"""Train v0.2 KBO translation and failure-risk models.

v0.2 extends the v0.1 leakage-safe setup by allowing official pre-KBO MiLB
features, not only MLB/Savant features. The validation stays deliberately
conservative: role-specific targets, time-forward holdouts, repeated stratified
CV, and role-prior baselines are all retained.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, precision_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
MART_PATH = OUTPUT_DIR / "kbo_translation_feature_mart_v0_2.csv"
V0_1_REPEATED_COMPARISON_PATH = OUTPUT_DIR / "kbo_translation_failure_repeated_cv_comparison_v0_1.csv"

TARGETS = ["success", "failure"]
ROLE_FAMILIES = ["hitter", "pitcher"]
MIN_FEATURE_NON_NULL = 8
MODEL_READY_FLAG = "has_model_pre_kbo_features"


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def clip_prob(values: np.ndarray | pd.Series) -> np.ndarray:
    return np.clip(np.asarray(values, dtype=float), 0.02, 0.98)


def feature_columns(df: pd.DataFrame, role: str) -> list[str]:
    base = [col for col in df.columns if col.startswith("pre_")]
    if role == "hitter":
        blocked = {
            "pre_woba_allowed",
            "pre_starter_stabilizer_score",
            "pre_kbo_milb_ip",
            "pre_kbo_milb_games",
            "pre_kbo_milb_games_started",
            "pre_kbo_milb_k9",
            "pre_kbo_milb_bb9",
            "pre_kbo_milb_hr9",
            "pre_kbo_milb_era",
            "pre_kbo_milb_whip",
        }
    else:
        blocked = {
            "pre_woba",
            "pre_ssg_message_screen_score",
            "pre_kbo_milb_pa",
            "pre_kbo_milb_hr",
            "pre_kbo_milb_ops",
            "pre_kbo_milb_obp",
            "pre_kbo_milb_slg",
            "pre_kbo_milb_k_pct",
            "pre_kbo_milb_bb_pct",
        }
    candidates = [col for col in base if col not in blocked]
    usable = []
    for col in candidates:
        values = pd.to_numeric(df[col], errors="coerce")
        if values.notna().sum() >= MIN_FEATURE_NON_NULL and values.nunique(dropna=True) > 1:
            usable.append(col)
    return usable


def build_models(train_rows: int) -> dict[str, object]:
    models: dict[str, object] = {
        "ridge_logit": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(C=0.7, max_iter=2000, solver="lbfgs")),
            ]
        ),
        "balanced_ridge_logit": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(C=0.7, max_iter=2000, solver="lbfgs", class_weight="balanced")),
            ]
        ),
    }
    if train_rows >= 24:
        models["shallow_random_forest"] = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=300,
                        max_depth=3,
                        min_samples_leaf=4,
                        class_weight="balanced",
                        random_state=7,
                    ),
                ),
            ]
        )
    if train_rows >= 30:
        models["hist_gradient_boosting"] = Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_iter=60,
                        learning_rate=0.05,
                        max_leaf_nodes=6,
                        l2_regularization=0.5,
                        random_state=7,
                    ),
                ),
            ]
        )
    return models


def evaluate(y_true: pd.Series, pred: np.ndarray) -> dict[str, float]:
    y = pd.to_numeric(y_true, errors="coerce").fillna(0).astype(int).to_numpy()
    p = clip_prob(pred)
    hard = (p >= 0.5).astype(int)
    out = {
        "rows": len(y),
        "positive_rate": float(np.mean(y)) if len(y) else np.nan,
        "pred_mean": float(np.mean(p)) if len(p) else np.nan,
        "accuracy_at_0_5": accuracy_score(y, hard) if len(y) else np.nan,
        "brier": brier_score_loss(y, p) if len(y) else np.nan,
        "logloss": log_loss(y, p, labels=[0, 1]) if len(y) else np.nan,
        "precision_at_0_5": precision_score(y, hard, zero_division=0) if len(y) else np.nan,
    }
    out["auc"] = roc_auc_score(y, p) if len(np.unique(y)) > 1 else np.nan
    for share in [0.25, 0.33]:
        k = max(1, int(np.ceil(len(y) * share)))
        order = np.argsort(-p)[:k]
        out[f"precision_top_{int(share * 100)}pct"] = float(np.mean(y[order])) if len(order) else np.nan
    return out


def prior_prediction(train: pd.DataFrame, valid: pd.DataFrame, target: str) -> np.ndarray:
    rate = pd.to_numeric(train[target], errors="coerce").fillna(0).mean()
    return clip_prob(np.repeat(rate, len(valid)))


def trainable_rows(mart: pd.DataFrame) -> pd.DataFrame:
    return mart[mart[MODEL_READY_FLAG] & mart["label_available"]].copy()


def run_time_folds(mart: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred_rows = []
    score_rows = []
    trainable = trainable_rows(mart)
    for role in ROLE_FAMILIES:
        role_df = trainable[trainable["role_model_family"].eq(role)].copy()
        if role_df.empty:
            continue
        for target in TARGETS:
            for valid_year in sorted(role_df["season"].unique()):
                train = role_df[role_df["season"].lt(valid_year)].copy()
                valid = role_df[role_df["season"].eq(valid_year)].copy()
                if train.empty or valid.empty:
                    continue
                if train[target].nunique() < 2:
                    continue
                features = feature_columns(train, role)
                if not features:
                    continue
                models = {"role_prior": None}
                models.update(build_models(len(train)))
                for model_name, model in models.items():
                    if model_name == "role_prior":
                        pred = prior_prediction(train, valid, target)
                    else:
                        model.fit(train[features], train[target].astype(int))
                        pred = model.predict_proba(valid[features])[:, 1]
                    metrics = evaluate(valid[target], pred)
                    score_rows.append(
                        {
                            "validation_scheme": "time_forward_holdout",
                            "role_model_family": role,
                            "target": target,
                            "valid_year": int(valid_year),
                            "fold_id": f"time_{int(valid_year)}",
                            "model": model_name,
                            "train_rows": len(train),
                            "valid_rows": len(valid),
                            "feature_count": len(features),
                            **metrics,
                        }
                    )
                    for row, score in zip(valid.to_dict("records"), pred, strict=False):
                        pred_rows.append(
                            {
                                "validation_scheme": "time_forward_holdout",
                                "role_model_family": role,
                                "target": target,
                                "valid_year": int(valid_year),
                                "model": model_name,
                                "player_key": row["player_key"],
                                "player_name": row["player_name"],
                                "player_name_en": row["player_name_en"],
                                "kbo_team": row["kbo_team"],
                                "label": int(row[target]),
                                "prediction": float(clip_prob([score])[0]),
                                "success": int(row["success"]),
                                "failure": int(row["failure"]),
                                "model_feature_source": row.get("model_feature_source", ""),
                                "prior_savant_years": row.get("prior_savant_years", ""),
                                "pre_kbo_milb_latest_year": row.get("pre_kbo_milb_latest_year", ""),
                            }
                        )
    return pd.DataFrame(pred_rows), pd.DataFrame(score_rows)


def summarize_scores(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return scores
    group_cols = [col for col in ["validation_scheme", "role_model_family", "target", "model"] if col in scores.columns]
    fold_col = "fold_id" if "fold_id" in scores.columns else "valid_year"
    summary = (
        scores.groupby(group_cols, dropna=False)
        .agg(
            folds=(fold_col, "nunique"),
            total_valid_rows=("valid_rows", "sum"),
            mean_feature_count=("feature_count", "mean"),
            mean_auc=("auc", "mean"),
            mean_brier=("brier", "mean"),
            mean_logloss=("logloss", "mean"),
            mean_precision_top_25pct=("precision_top_25pct", "mean"),
            mean_precision_top_33pct=("precision_top_33pct", "mean"),
        )
        .reset_index()
    )
    prior_cols = [col for col in ["validation_scheme", "role_model_family", "target"] if col in summary.columns]
    prior = summary[summary["model"].eq("role_prior")][
        prior_cols + ["mean_brier", "mean_precision_top_25pct"]
    ].rename(
        columns={
            "mean_brier": "role_prior_mean_brier",
            "mean_precision_top_25pct": "role_prior_precision_top_25pct",
        }
    )
    out = summary.merge(prior, on=prior_cols, how="left")
    out["brier_lift_vs_role_prior"] = out["role_prior_mean_brier"] - out["mean_brier"]
    out["top25_precision_lift_vs_role_prior"] = (
        out["mean_precision_top_25pct"] - out["role_prior_precision_top_25pct"]
    )
    out["promotion_status"] = np.select(
        [
            out["model"].eq("role_prior"),
            out["brier_lift_vs_role_prior"].gt(0.01) & out["top25_precision_lift_vs_role_prior"].ge(0),
            out["brier_lift_vs_role_prior"].gt(0),
        ],
        ["baseline", "pilot_promote", "watch"],
        default="do_not_promote",
    )
    sort_cols = [col for col in ["validation_scheme", "role_model_family", "target", "mean_brier", "model"] if col in out.columns]
    return out.sort_values(sort_cols)


def run_repeated_stratified_cv(mart: pd.DataFrame) -> pd.DataFrame:
    score_rows = []
    trainable = trainable_rows(mart)
    splitter = RepeatedStratifiedKFold(n_splits=3, n_repeats=30, random_state=7)
    for role in ROLE_FAMILIES:
        role_df = trainable[trainable["role_model_family"].eq(role)].copy().reset_index(drop=True)
        if role_df.empty:
            continue
        for target in TARGETS:
            y = role_df[target].astype(int).to_numpy()
            if len(np.unique(y)) < 2 or pd.Series(y).value_counts().min() < 3:
                continue
            for fold_id, (train_idx, valid_idx) in enumerate(splitter.split(role_df, y), start=1):
                train = role_df.iloc[train_idx].copy()
                valid = role_df.iloc[valid_idx].copy()
                features = feature_columns(train, role)
                if not features:
                    continue
                models = {"role_prior": None}
                models.update(build_models(len(train)))
                for model_name, model in models.items():
                    if model_name == "role_prior":
                        pred = prior_prediction(train, valid, target)
                    else:
                        model.fit(train[features], train[target].astype(int))
                        pred = model.predict_proba(valid[features])[:, 1]
                    metrics = evaluate(valid[target], pred)
                    score_rows.append(
                        {
                            "validation_scheme": "repeated_stratified_cv",
                            "role_model_family": role,
                            "target": target,
                            "fold_id": fold_id,
                            "model": model_name,
                            "train_rows": len(train),
                            "valid_rows": len(valid),
                            "feature_count": len(features),
                            **metrics,
                        }
                    )
    return pd.DataFrame(score_rows)


def build_feature_signals(mart: pd.DataFrame) -> pd.DataFrame:
    trainable = trainable_rows(mart)
    rows = []
    for role in ROLE_FAMILIES:
        role_df = trainable[trainable["role_model_family"].eq(role)].copy()
        features = feature_columns(role_df, role)
        if not features:
            continue
        for target in TARGETS:
            if role_df[target].nunique() < 2:
                continue
            model = Pipeline(
                steps=[
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("model", LogisticRegression(C=0.7, max_iter=2000, solver="lbfgs", class_weight="balanced")),
                ]
            )
            model.fit(role_df[features], role_df[target].astype(int))
            coef = model.named_steps["model"].coef_[0]
            for feature, value in zip(features, coef, strict=False):
                rows.append(
                    {
                        "role_model_family": role,
                        "target": target,
                        "feature": feature,
                        "coefficient": float(value),
                        "abs_coefficient": float(abs(value)),
                        "direction": "raises_target_probability" if value > 0 else "lowers_target_probability",
                        "train_rows": len(role_df),
                        "positive_rows": int(role_df[target].sum()),
                    }
                )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["role_model_family", "target", "abs_coefficient"], ascending=[True, True, False])


def compare_to_v0_1(v0_2: pd.DataFrame) -> pd.DataFrame:
    if not V0_1_REPEATED_COMPARISON_PATH.exists() or v0_2.empty:
        return pd.DataFrame()
    v0_1 = pd.read_csv(V0_1_REPEATED_COMPARISON_PATH)
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
    keep_v0_1 = key_cols + [col for col in metric_cols if col in v0_1.columns]
    keep_v0_2 = key_cols + [col for col in metric_cols if col in v0_2.columns]
    comparison = v0_1[keep_v0_1].merge(
        v0_2[keep_v0_2],
        on=key_cols,
        how="outer",
        suffixes=("_v0_1", "_v0_2"),
    )
    for metric in ["mean_brier", "mean_auc", "mean_precision_top_25pct", "total_valid_rows", "mean_feature_count"]:
        left = f"{metric}_v0_1"
        right = f"{metric}_v0_2"
        if left in comparison.columns and right in comparison.columns:
            comparison[f"{metric}_delta_v0_2_minus_v0_1"] = comparison[right] - comparison[left]
    if "mean_brier_delta_v0_2_minus_v0_1" in comparison.columns:
        comparison["brier_direction"] = np.select(
            [
                comparison["mean_brier_delta_v0_2_minus_v0_1"].lt(-0.005),
                comparison["mean_brier_delta_v0_2_minus_v0_1"].gt(0.005),
            ],
            ["improved", "worse"],
            default="flat",
        )
    return comparison.sort_values(key_cols)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mart = pd.read_csv(MART_PATH)
    for col in ["has_pre_kbo_savant_features", "has_pre_kbo_milb", MODEL_READY_FLAG, "label_available"]:
        mart[col] = to_bool(mart[col])
    for col in TARGETS:
        mart[col] = pd.to_numeric(mart[col], errors="coerce").fillna(0).astype(int)

    preds, scores = run_time_folds(mart)
    repeated_scores = run_repeated_stratified_cv(mart)
    comparison = summarize_scores(scores)
    repeated_comparison = summarize_scores(repeated_scores)
    feature_signals = build_feature_signals(mart)
    v0_1_vs_v0_2 = compare_to_v0_1(repeated_comparison)

    preds.to_csv(OUTPUT_DIR / "kbo_translation_failure_oof_predictions_v0_2.csv", index=False)
    scores.to_csv(OUTPUT_DIR / "kbo_translation_failure_fold_scores_v0_2.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "kbo_translation_failure_model_comparison_v0_2.csv", index=False)
    repeated_scores.to_csv(OUTPUT_DIR / "kbo_translation_failure_repeated_cv_scores_v0_2.csv", index=False)
    repeated_comparison.to_csv(OUTPUT_DIR / "kbo_translation_failure_repeated_cv_comparison_v0_2.csv", index=False)
    feature_signals.to_csv(OUTPUT_DIR / "kbo_translation_failure_feature_signals_v0_2.csv", index=False)
    v0_1_vs_v0_2.to_csv(OUTPUT_DIR / "kbo_translation_failure_v0_1_vs_v0_2_comparison.csv", index=False)

    trainable = trainable_rows(mart)
    print("trainable rows", trainable.shape)
    print(trainable.groupby(["role_model_family", "model_feature_source"]).size().to_string())
    print()
    print("wrote", OUTPUT_DIR / "kbo_translation_failure_oof_predictions_v0_2.csv", preds.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_failure_fold_scores_v0_2.csv", scores.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_failure_model_comparison_v0_2.csv", comparison.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_failure_repeated_cv_scores_v0_2.csv", repeated_scores.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_failure_repeated_cv_comparison_v0_2.csv", repeated_comparison.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_failure_feature_signals_v0_2.csv", feature_signals.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_failure_v0_1_vs_v0_2_comparison.csv", v0_1_vs_v0_2.shape)
    print()
    print(comparison.to_string(index=False))
    print()
    print(repeated_comparison.to_string(index=False))
    print()
    print(v0_1_vs_v0_2.to_string(index=False))
    print()
    print(feature_signals.groupby(["role_model_family", "target"]).head(8).to_string(index=False))


if __name__ == "__main__":
    main()
