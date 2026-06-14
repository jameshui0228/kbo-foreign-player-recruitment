#!/usr/bin/env python3
"""Run leakage-safe historical baselines for KBO foreign-player labels.

These are deliberately simple baselines. They are not meant to be the final
model; they set the minimum bar that later KBO translation and SSG-fit models
must beat.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, precision_score, roc_auc_score


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
LABEL_PATH = OUTPUT_DIR / "kbo_foreign_player_season_labels_v0_1.csv"
FOLDS = [
    ("fold_a_2022_holdout", list(range(2017, 2022)), 2022),
    ("fold_b_2023_holdout", list(range(2017, 2023)), 2023),
    ("fold_c_2024_holdout", list(range(2017, 2024)), 2024),
    ("fold_d_2025_holdout", list(range(2017, 2025)), 2025),
]


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def clip_prob(value: float) -> float:
    if pd.isna(value):
        return 0.5
    return float(np.clip(value, 0.02, 0.98))


def smooth_rate(successes: float, trials: float, prior: float, weight: float = 8.0) -> float:
    return clip_prob((successes + prior * weight) / (trials + weight))


def group_prior_predict(train: pd.DataFrame, valid: pd.DataFrame, target: str, group_cols: list[str]) -> pd.Series:
    global_rate = train[target].mean()
    grouped = train.groupby(group_cols, dropna=False)[target].agg(["sum", "count"]).reset_index()
    grouped["pred"] = grouped.apply(lambda row: smooth_rate(row["sum"], row["count"], global_rate), axis=1)
    merged = valid.merge(grouped[group_cols + ["pred"]], on=group_cols, how="left")
    return merged["pred"].fillna(global_rate).map(clip_prob)


def recent_role_prior_predict(train: pd.DataFrame, valid: pd.DataFrame, target: str) -> pd.Series:
    max_year = train["season"].max()
    work = train.copy()
    work["time_weight"] = 0.65 ** (max_year - work["season"])
    global_rate = np.average(work[target], weights=work["time_weight"])
    rows = []
    for role, group in work.groupby("role_group", dropna=False):
        successes = (group[target] * group["time_weight"]).sum()
        trials = group["time_weight"].sum()
        rows.append({"role_group": role, "pred": smooth_rate(successes, trials, global_rate, weight=3.0)})
    rates = pd.DataFrame(rows)
    merged = valid.merge(rates, on="role_group", how="left")
    return merged["pred"].fillna(global_rate).map(clip_prob)


def previous_season_team_role_predict(train: pd.DataFrame, valid: pd.DataFrame, target: str) -> pd.Series:
    valid_year = valid["season"].iloc[0]
    prev = train[train["season"].eq(valid_year - 1)].copy()
    if prev.empty:
        return group_prior_predict(train, valid, target, ["kbo_team", "role_group"])
    return group_prior_predict(prev, valid, target, ["kbo_team", "role_group"])


def evaluate(y_true: pd.Series, pred: pd.Series) -> dict[str, float]:
    y = pd.to_numeric(y_true, errors="coerce").fillna(0).astype(int).reset_index(drop=True)
    p = pd.to_numeric(pred, errors="coerce").fillna(0.5).clip(0.02, 0.98).reset_index(drop=True)
    hard = (p >= 0.5).astype(int)
    out = {
        "rows": len(y),
        "positive_rate": y.mean(),
        "pred_mean": p.mean(),
        "accuracy_at_0_5": accuracy_score(y, hard),
        "brier": brier_score_loss(y, p),
        "logloss": log_loss(y, p, labels=[0, 1]),
    }
    if y.nunique() > 1:
        out["auc"] = roc_auc_score(y, p)
        out["precision_at_0_5"] = precision_score(y, hard, zero_division=0)
    else:
        out["auc"] = np.nan
        out["precision_at_0_5"] = np.nan

    for share in [0.25, 0.33]:
        k = max(1, int(np.ceil(len(y) * share)))
        top_idx = p.sort_values(ascending=False).head(k).index
        out[f"precision_top_{int(share * 100)}pct"] = y.loc[top_idx].mean()
    return out


def build_predictions(labels: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    models = [
        ("global_prior", lambda train, valid, target: pd.Series(train[target].mean(), index=valid.index).map(clip_prob)),
        ("role_prior", lambda train, valid, target: group_prior_predict(train, valid, target, ["role_group"])),
        ("team_role_prior", lambda train, valid, target: group_prior_predict(train, valid, target, ["kbo_team", "role_group"])),
        ("recent_role_prior", recent_role_prior_predict),
        ("prev_season_team_role_prior", previous_season_team_role_predict),
    ]
    target_defs = [("success", "success_score"), ("failure", "failure_score")]

    pred_rows = []
    score_rows = []
    for fold_name, train_years, valid_year in FOLDS:
        train = labels[labels["season"].isin(train_years) & labels["label_available"]].copy()
        valid = labels[labels["season"].eq(valid_year) & labels["label_available"]].copy()
        if train.empty or valid.empty:
            continue
        for target, score_col in target_defs:
            for model_name, predictor in models:
                pred = predictor(train, valid, target)
                pred = pd.Series(pred.to_numpy(), index=valid.index)
                metrics = evaluate(valid[target], pred)
                score_rows.append(
                    {
                        "fold": fold_name,
                        "valid_year": valid_year,
                        "target": target,
                        "model": model_name,
                        **metrics,
                    }
                )
                for idx, row in valid.iterrows():
                    pred_rows.append(
                        {
                            "fold": fold_name,
                            "valid_year": valid_year,
                            "target": target,
                            "model": model_name,
                            "player_key": row["player_key"],
                            "player_name": row["player_name"],
                            "kbo_team": row["kbo_team"],
                            "role_group": row["role_group"],
                            "label": row[target],
                            score_col: pred.loc[idx],
                            "source_confidence_1_5": row["source_confidence_1_5"],
                            "outcome_available": row["outcome_available"],
                        }
                    )
    return pd.DataFrame(pred_rows), pd.DataFrame(score_rows)


def build_model_family_comparison(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return scores
    summary = (
        scores.groupby(["target", "model"], dropna=False)
        .agg(
            folds=("fold", "nunique"),
            mean_auc=("auc", "mean"),
            mean_brier=("brier", "mean"),
            mean_logloss=("logloss", "mean"),
            mean_accuracy_at_0_5=("accuracy_at_0_5", "mean"),
            mean_precision_top_25pct=("precision_top_25pct", "mean"),
            mean_precision_top_33pct=("precision_top_33pct", "mean"),
        )
        .reset_index()
    )
    baseline = summary[summary["model"].eq("global_prior")][["target", "mean_brier", "mean_precision_top_25pct"]]
    baseline = baseline.rename(
        columns={
            "mean_brier": "global_prior_mean_brier",
            "mean_precision_top_25pct": "global_prior_precision_top_25pct",
        }
    )
    out = summary.merge(baseline, on="target", how="left")
    out["brier_lift_vs_global"] = out["global_prior_mean_brier"] - out["mean_brier"]
    out["top25_precision_lift_vs_global"] = (
        out["mean_precision_top_25pct"] - out["global_prior_precision_top_25pct"]
    )
    out["promotion_status"] = np.select(
        [
            out["brier_lift_vs_global"].gt(0.005) & out["top25_precision_lift_vs_global"].ge(0),
            out["brier_lift_vs_global"].gt(0),
        ],
        ["promote_as_baseline_to_beat", "watch"],
        default="do_not_promote",
    )
    return out.sort_values(["target", "promotion_status", "mean_brier"], ascending=[True, True, True])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    labels = pd.read_csv(LABEL_PATH)
    for col in ["outcome_available", "label_available"]:
        labels[col] = to_bool(labels[col])
    for col in ["success", "failure", "strong_success"]:
        labels[col] = pd.to_numeric(labels[col], errors="coerce").fillna(0).astype(int)

    preds, scores = build_predictions(labels)
    comparison = build_model_family_comparison(scores)

    scores.to_csv(OUTPUT_DIR / "kbo_foreign_baseline_scores_v0_1.csv", index=False)
    preds.to_csv(OUTPUT_DIR / "kbo_foreign_oof_predictions_v0_1.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "kbo_foreign_model_family_comparison_v0_1.csv", index=False)

    print("wrote", OUTPUT_DIR / "kbo_foreign_baseline_scores_v0_1.csv", scores.shape)
    print("wrote", OUTPUT_DIR / "kbo_foreign_oof_predictions_v0_1.csv", preds.shape)
    print("wrote", OUTPUT_DIR / "kbo_foreign_model_family_comparison_v0_1.csv", comparison.shape)
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
