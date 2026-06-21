#!/usr/bin/env python3
"""Run compact feature-family ablations for KBO recruitment models.

Run 020 showed that the all-feature v0.2 model was too wide for the historical
sample. This script tests smaller, scout-readable feature families and keeps the
same conservative repeated-CV gate against role-prior baselines.

No current-player candidate scores or recommendation labels are produced here.
The output decides which model feature families are allowed to inform the later
SSG fit-ranking layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import warnings

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, precision_score, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
MART_V0_2_PATH = OUTPUT_DIR / "kbo_translation_feature_mart_v0_2.csv"
HISTORICAL_MILB_FEATURE_PATH = OUTPUT_DIR / "historical_kbo_prearrival_milb_features_v1.csv"

ABLATION_MART_PATH = OUTPUT_DIR / "kbo_translation_feature_family_ablation_mart_v0_3.csv"
FEATURE_SET_PATH = OUTPUT_DIR / "kbo_translation_failure_feature_family_sets_v0_3.csv"
CV_SCORE_PATH = OUTPUT_DIR / "kbo_translation_failure_feature_family_cv_scores_v0_3.csv"
CV_COMPARISON_PATH = OUTPUT_DIR / "kbo_translation_failure_feature_family_cv_comparison_v0_3.csv"
DECISION_PATH = OUTPUT_DIR / "kbo_translation_failure_feature_family_decisions_v0_3.csv"

TARGETS = ["success", "failure"]
ROLE_FAMILIES = ["hitter", "pitcher"]
MIN_FEATURE_NON_NULL = 8
MODEL_READY_FLAG = "has_model_pre_kbo_features"

warnings.filterwarnings("ignore", message="'penalty' was deprecated.*")
warnings.filterwarnings("ignore", message="Inconsistent values: penalty=.*")


@dataclass(frozen=True)
class FeatureFamily:
    name: str
    description: str
    role_features: dict[str, list[str]]
    source_filter: Callable[[pd.DataFrame], pd.Series]


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def clip_prob(values: np.ndarray | pd.Series) -> np.ndarray:
    return np.clip(np.asarray(values, dtype=float), 0.02, 0.98)


def add_missing_recent_level_feature(mart: pd.DataFrame) -> pd.DataFrame:
    """Add the historical recent-level feature that was not used in Run 020."""
    if "pre_kbo_recent_highest_level_score" in mart.columns:
        return mart
    historical = pd.read_csv(HISTORICAL_MILB_FEATURE_PATH)
    cols = ["season", "player_key", "role_model_family", "pre_kbo_recent_highest_level_score"]
    recent = historical[cols].drop_duplicates(subset=["season", "player_key", "role_model_family"])
    return mart.merge(recent, on=["season", "player_key", "role_model_family"], how="left", validate="many_to_one")


def build_feature_families() -> list[FeatureFamily]:
    savant_source = lambda df: df["has_pre_kbo_savant_features"]
    milb_source = lambda df: df["has_pre_kbo_milb"]
    mixed_source = lambda df: df[MODEL_READY_FLAG]
    return [
        FeatureFamily(
            name="savant_only",
            description="Pre-KBO MLB/Savant quality, approach, command, and contact-management variables only",
            source_filter=savant_source,
            role_features={
                "hitter": [
                    "pre_pa",
                    "pre_pitch",
                    "pre_bb_pct",
                    "pre_k_pct",
                    "pre_woba",
                    "pre_chase_rate",
                    "pre_zone_swing_rate",
                    "pre_nonfast_chase_rate",
                    "pre_nonfast_whiff_per_swing",
                    "pre_whiff_per_swing",
                    "pre_hardhit_rate",
                    "pre_barrel_rate",
                    "pre_sweet_spot_rate",
                    "pre_air_bbe_rate",
                    "pre_low_velo_xwoba",
                    "pre_high_velo_xwoba",
                    "pre_break_off_xwoba",
                    "pre_hitter_count_xwoba",
                ],
                "pitcher": [
                    "pre_pa",
                    "pre_pitch",
                    "pre_bb_hbp_pct",
                    "pre_k_pct",
                    "pre_hr_pct",
                    "pre_woba_allowed",
                    "pre_xwoba_allowed_bbe",
                    "pre_xslg_allowed_bbe",
                    "pre_whiff_per_swing",
                    "pre_chase_rate",
                    "pre_zone_rate",
                    "pre_first_pitch_nonball_rate",
                    "pre_three_ball_pitch_rate",
                    "pre_hardhit_rate",
                    "pre_barrel_rate",
                    "pre_early_1_3_woba_allowed",
                    "pre_runner_on_base_woba_allowed",
                    "pre_risp_woba_allowed",
                ],
            },
        ),
        FeatureFamily(
            name="milb_level_role",
            description="Pre-KBO MiLB level, recency, AAA/AA exposure, and role/load continuity only",
            source_filter=milb_source,
            role_features={
                "hitter": [
                    "pre_kbo_milb_rows",
                    "pre_kbo_milb_latest_year",
                    "pre_kbo_milb_recent_rows",
                    "pre_kbo_milb_highest_level_score",
                    "pre_kbo_recent_highest_level_score",
                    "pre_kbo_aaa_rows",
                    "pre_kbo_aa_rows",
                    "pre_kbo_milb_pa",
                ],
                "pitcher": [
                    "pre_kbo_milb_rows",
                    "pre_kbo_milb_latest_year",
                    "pre_kbo_milb_recent_rows",
                    "pre_kbo_milb_highest_level_score",
                    "pre_kbo_recent_highest_level_score",
                    "pre_kbo_aaa_rows",
                    "pre_kbo_aa_rows",
                    "pre_kbo_milb_ip",
                    "pre_kbo_milb_games",
                    "pre_kbo_milb_games_started",
                ],
            },
        ),
        FeatureFamily(
            name="milb_damage_command",
            description="Pre-KBO MiLB performance translation variables for damage, walks, strikeouts, and traffic",
            source_filter=milb_source,
            role_features={
                "hitter": [
                    "pre_kbo_milb_pa",
                    "pre_kbo_milb_hr",
                    "pre_kbo_milb_ops",
                    "pre_kbo_milb_obp",
                    "pre_kbo_milb_slg",
                    "pre_kbo_milb_k_pct",
                    "pre_kbo_milb_bb_pct",
                ],
                "pitcher": [
                    "pre_kbo_milb_ip",
                    "pre_kbo_milb_games",
                    "pre_kbo_milb_games_started",
                    "pre_kbo_milb_k9",
                    "pre_kbo_milb_bb9",
                    "pre_kbo_milb_hr9",
                    "pre_kbo_milb_era",
                    "pre_kbo_milb_whip",
                ],
            },
        ),
        FeatureFamily(
            name="recent_track_continuity",
            description="Recent usable track, highest-level proximity, and continuity without detailed skill rates",
            source_filter=milb_source,
            role_features={
                "hitter": [
                    "pre_kbo_milb_latest_year",
                    "pre_kbo_milb_recent_rows",
                    "pre_kbo_milb_rows",
                    "pre_kbo_milb_highest_level_score",
                    "pre_kbo_recent_highest_level_score",
                    "pre_kbo_aaa_rows",
                    "pre_kbo_milb_pa",
                ],
                "pitcher": [
                    "pre_kbo_milb_latest_year",
                    "pre_kbo_milb_recent_rows",
                    "pre_kbo_milb_rows",
                    "pre_kbo_milb_highest_level_score",
                    "pre_kbo_recent_highest_level_score",
                    "pre_kbo_aaa_rows",
                    "pre_kbo_milb_ip",
                    "pre_kbo_milb_games_started",
                ],
            },
        ),
        FeatureFamily(
            name="compact_mixed",
            description="At-most-ten scout-readable mixed variables combining Savant skill, MiLB rates, and continuity",
            source_filter=mixed_source,
            role_features={
                "hitter": [
                    "pre_pa",
                    "pre_woba",
                    "pre_whiff_per_swing",
                    "pre_nonfast_whiff_per_swing",
                    "pre_hitter_count_xwoba",
                    "pre_kbo_milb_pa",
                    "pre_kbo_milb_ops",
                    "pre_kbo_milb_k_pct",
                    "pre_kbo_milb_bb_pct",
                    "pre_kbo_milb_latest_year",
                ],
                "pitcher": [
                    "pre_woba_allowed",
                    "pre_three_ball_pitch_rate",
                    "pre_zone_rate",
                    "pre_whiff_per_swing",
                    "pre_kbo_milb_k9",
                    "pre_kbo_milb_bb9",
                    "pre_kbo_milb_hr9",
                    "pre_kbo_milb_latest_year",
                    "pre_kbo_milb_games_started",
                    "pre_kbo_recent_highest_level_score",
                ],
            },
        ),
    ]


def usable_features(df: pd.DataFrame, feature_candidates: list[str]) -> list[str]:
    usable = []
    for col in feature_candidates:
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        if values.notna().sum() >= MIN_FEATURE_NON_NULL and values.nunique(dropna=True) > 1:
            usable.append(col)
    return usable


def build_models() -> dict[str, object]:
    return {
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
        "sparse_l1_logit": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", LogisticRegression(C=0.35, penalty="l1", max_iter=2000, solver="liblinear")),
            ]
        ),
    }


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


def run_repeated_cv(mart: pd.DataFrame, families: list[FeatureFamily]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    splitter = RepeatedStratifiedKFold(n_splits=3, n_repeats=30, random_state=21)
    for family in families:
        family_ready = family.source_filter(mart) & mart["label_available"]
        family_df = mart[family_ready].copy()
        for role in ROLE_FAMILIES:
            role_df = family_df[family_df["role_model_family"].eq(role)].copy().reset_index(drop=True)
            if role_df.empty:
                continue
            candidate_features = family.role_features[role]
            for target in TARGETS:
                y = role_df[target].astype(int).to_numpy()
                if len(np.unique(y)) < 2 or pd.Series(y).value_counts().min() < 3:
                    continue
                for fold_id, (train_idx, valid_idx) in enumerate(splitter.split(role_df, y), start=1):
                    train = role_df.iloc[train_idx].copy()
                    valid = role_df.iloc[valid_idx].copy()
                    features = usable_features(train, candidate_features)
                    if not features:
                        continue

                    pred = prior_prediction(train, valid, target)
                    metrics = evaluate(valid[target], pred)
                    rows.append(
                        {
                            "validation_scheme": "repeated_stratified_cv",
                            "feature_family": family.name,
                            "role_model_family": role,
                            "target": target,
                            "fold_id": fold_id,
                            "model": "role_prior",
                            "source_rows": len(role_df),
                            "train_rows": len(train),
                            "valid_rows": len(valid),
                            "feature_count": len(features),
                            "features": "|".join(features),
                            **metrics,
                        }
                    )

                    for model_name, model in build_models().items():
                        model.fit(train[features], train[target].astype(int))
                        pred = model.predict_proba(valid[features])[:, 1]
                        metrics = evaluate(valid[target], pred)
                        rows.append(
                            {
                                "validation_scheme": "repeated_stratified_cv",
                                "feature_family": family.name,
                                "role_model_family": role,
                                "target": target,
                                "fold_id": fold_id,
                                "model": model_name,
                                "source_rows": len(role_df),
                                "train_rows": len(train),
                                "valid_rows": len(valid),
                                "feature_count": len(features),
                                "features": "|".join(features),
                                **metrics,
                            }
                        )
    return pd.DataFrame(rows)


def summarize_scores(scores: pd.DataFrame) -> pd.DataFrame:
    if scores.empty:
        return scores
    group_cols = ["validation_scheme", "feature_family", "role_model_family", "target", "model"]
    summary = (
        scores.groupby(group_cols, dropna=False)
        .agg(
            folds=("fold_id", "nunique"),
            source_rows=("source_rows", "max"),
            total_valid_rows=("valid_rows", "sum"),
            mean_feature_count=("feature_count", "mean"),
            median_feature_count=("feature_count", "median"),
            mean_auc=("auc", "mean"),
            mean_brier=("brier", "mean"),
            mean_logloss=("logloss", "mean"),
            mean_precision_top_25pct=("precision_top_25pct", "mean"),
            mean_precision_top_33pct=("precision_top_33pct", "mean"),
        )
        .reset_index()
    )
    prior_cols = ["validation_scheme", "feature_family", "role_model_family", "target"]
    prior = summary[summary["model"].eq("role_prior")][
        prior_cols + ["mean_brier", "mean_precision_top_25pct", "mean_precision_top_33pct"]
    ].rename(
        columns={
            "mean_brier": "role_prior_mean_brier",
            "mean_precision_top_25pct": "role_prior_precision_top_25pct",
            "mean_precision_top_33pct": "role_prior_precision_top_33pct",
        }
    )
    out = summary.merge(prior, on=prior_cols, how="left")
    out["brier_lift_vs_role_prior"] = out["role_prior_mean_brier"] - out["mean_brier"]
    out["top25_precision_lift_vs_role_prior"] = (
        out["mean_precision_top_25pct"] - out["role_prior_precision_top_25pct"]
    )
    out["top33_precision_lift_vs_role_prior"] = (
        out["mean_precision_top_33pct"] - out["role_prior_precision_top_33pct"]
    )
    out["promotion_status"] = np.select(
        [
            out["model"].eq("role_prior"),
            out["brier_lift_vs_role_prior"].gt(0.01)
            & out["top25_precision_lift_vs_role_prior"].ge(0)
            & out["mean_auc"].ge(0.55),
            out["brier_lift_vs_role_prior"].gt(0)
            & out["top25_precision_lift_vs_role_prior"].ge(0),
        ],
        ["baseline", "pilot_promote", "watch"],
        default="do_not_promote",
    )
    return out.sort_values(
        ["role_model_family", "target", "promotion_status", "mean_brier", "feature_family", "model"]
    )


def build_feature_set_registry(mart: pd.DataFrame, families: list[FeatureFamily]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for family in families:
        family_ready = family.source_filter(mart) & mart["label_available"]
        family_df = mart[family_ready].copy()
        for role in ROLE_FAMILIES:
            role_df = family_df[family_df["role_model_family"].eq(role)].copy()
            features = usable_features(role_df, family.role_features[role])
            rows.append(
                {
                    "feature_family": family.name,
                    "description": family.description,
                    "role_model_family": role,
                    "source_rows": len(role_df),
                    "usable_feature_count": len(features),
                    "usable_features": "|".join(features),
                    "candidate_feature_count": len(family.role_features[role]),
                    "candidate_features": "|".join(family.role_features[role]),
                }
            )
    return pd.DataFrame(rows)


def build_decision_table(comparison: pd.DataFrame) -> pd.DataFrame:
    non_prior = comparison[~comparison["model"].eq("role_prior")].copy()
    if non_prior.empty:
        return non_prior
    status_rank = {"pilot_promote": 0, "watch": 1, "do_not_promote": 2}
    non_prior["status_rank"] = non_prior["promotion_status"].map(status_rank).fillna(9)
    non_prior = non_prior.sort_values(
        [
            "role_model_family",
            "target",
            "status_rank",
            "mean_brier",
            "mean_auc",
            "mean_precision_top_25pct",
        ],
        ascending=[True, True, True, True, False, False],
    )
    best = non_prior.groupby(["role_model_family", "target"], dropna=False).head(1).copy()
    best["gate_decision"] = np.select(
        [
            best["promotion_status"].eq("pilot_promote"),
            best["promotion_status"].eq("watch"),
        ],
        ["allow_as_pilot_score_component", "allow_as_diagnostic_only"],
        default="do_not_use_for_ranking",
    )
    best["candidate_release_impact"] = "candidate_names_remain_locked"
    return best.drop(columns=["status_rank"])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    mart = pd.read_csv(MART_V0_2_PATH)
    mart = add_missing_recent_level_feature(mart)
    for col in ["has_pre_kbo_savant_features", "has_pre_kbo_milb", MODEL_READY_FLAG, "label_available"]:
        mart[col] = to_bool(mart[col])
    for col in TARGETS:
        mart[col] = pd.to_numeric(mart[col], errors="coerce").fillna(0).astype(int)

    families = build_feature_families()
    feature_sets = build_feature_set_registry(mart, families)
    scores = run_repeated_cv(mart, families)
    comparison = summarize_scores(scores)
    decisions = build_decision_table(comparison)

    mart.to_csv(ABLATION_MART_PATH, index=False)
    feature_sets.to_csv(FEATURE_SET_PATH, index=False)
    scores.to_csv(CV_SCORE_PATH, index=False)
    comparison.to_csv(CV_COMPARISON_PATH, index=False)
    decisions.to_csv(DECISION_PATH, index=False)

    print("wrote", ABLATION_MART_PATH, mart.shape)
    print("wrote", FEATURE_SET_PATH, feature_sets.shape)
    print("wrote", CV_SCORE_PATH, scores.shape)
    print("wrote", CV_COMPARISON_PATH, comparison.shape)
    print("wrote", DECISION_PATH, decisions.shape)
    print()
    print("feature families")
    print(feature_sets[["feature_family", "role_model_family", "source_rows", "usable_feature_count"]].to_string(index=False))
    print()
    print("promotion/watch rows")
    promoted = comparison[comparison["promotion_status"].isin(["pilot_promote", "watch"])]
    print(promoted.to_string(index=False))
    print()
    print("target-level decisions")
    print(decisions.to_string(index=False))


if __name__ == "__main__":
    main()
