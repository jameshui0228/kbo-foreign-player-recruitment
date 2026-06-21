#!/usr/bin/env python3
"""Attach validated model signals and feasibility tags to candidate markets.

Run 021 promoted only one true pilot scoring component: the hitter Savant-only
translation family. Pitcher MiLB damage/command remained diagnostic only.

This script applies that policy to the current candidate pools:

1. score MLB outfielder candidates with a candidate-compatible hitter Savant
   pilot component;
2. attach non-ranking MiLB damage/command diagnostic tags to MLB pitcher
   candidates;
3. attach current Asian-quota feasibility tags from the existing NPB/CPBL
   roster and nationality gates.

The outputs are explicitly not shortlist or recommendation files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

HISTORICAL_MART = OUTPUT_DIR / "kbo_translation_feature_family_ablation_mart_v0_3.csv"
HITTER_POOL = OUTPUT_DIR / "mlb_outfielder_availability_candidate_pool_v1.csv"
PITCHER_POOL = OUTPUT_DIR / "mlb_pitcher_availability_candidate_pool_v1.csv"
MILB_ROLE_CONTEXT = OUTPUT_DIR / "mlb_market_pool_milb_role_context_v1.csv"
ASIAN_MARKET = OUTPUT_DIR / "asian_quota_market_status_v1.csv"

HITTER_COMPONENT_OUT = OUTPUT_DIR / "candidate_side_hitter_savant_pilot_component_v0_1.csv"
HITTER_AUDIT_OUT = OUTPUT_DIR / "candidate_side_hitter_savant_pilot_model_audit_v0_1.csv"
HITTER_FEATURE_MAP_OUT = OUTPUT_DIR / "candidate_side_hitter_savant_feature_map_v0_1.csv"
PITCHER_DIAGNOSTIC_OUT = OUTPUT_DIR / "candidate_side_pitcher_milb_diagnostic_tags_v0_1.csv"
ASIAN_FEASIBILITY_OUT = OUTPUT_DIR / "candidate_side_asian_quota_feasibility_tags_v0_1.csv"
SUMMARY_OUT = OUTPUT_DIR / "candidate_side_signal_join_summary_v0_1.csv"

TARGETS = ["success", "failure"]

HITTER_FEATURE_MAP = {
    "pre_pa": "recent_pa",
    "pre_pitch": "recent_pitches",
    "pre_bb_pct": "recent_bb_pct",
    "pre_k_pct": "recent_k_pct",
    "pre_woba": "recent_woba",
    "pre_chase_rate": "recent_chase_rate",
    "pre_nonfast_chase_rate": "recent_nonfast_chase_rate",
    "pre_nonfast_whiff_per_swing": "recent_nonfast_whiff_per_swing",
    "pre_whiff_per_swing": "recent_whiff_per_swing",
    "pre_hardhit_rate": "recent_hardhit_rate",
    "pre_barrel_rate": "recent_barrel_rate",
    "pre_sweet_spot_rate": "recent_sweet_spot_rate",
    "pre_air_bbe_rate": "recent_air_bbe_rate",
    "pre_low_velo_xwoba": "recent_low_velo_xwoba",
    "pre_high_velo_xwoba": "recent_high_velo_xwoba",
    "pre_break_off_xwoba": "recent_break_off_xwoba",
    "pre_hitter_count_xwoba": "recent_hitter_count_xwoba",
}


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def clip_prob(values: np.ndarray | pd.Series) -> np.ndarray:
    return np.clip(np.asarray(values, dtype=float), 0.02, 0.98)


def safe_rank(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() <= 1:
        return pd.Series(np.nan, index=series.index)
    ranked = numeric.rank(pct=True, ascending=True) * 100
    if not higher_is_better:
        ranked = 100 - ranked
    return ranked


def build_logit() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=0.7, max_iter=2000, solver="lbfgs")),
        ]
    )


def evaluate_predictions(y_true: pd.Series, pred: np.ndarray) -> dict[str, float]:
    y = pd.to_numeric(y_true, errors="coerce").fillna(0).astype(int).to_numpy()
    p = clip_prob(pred)
    out = {
        "rows": len(y),
        "positive_rate": float(np.mean(y)) if len(y) else np.nan,
        "pred_mean": float(np.mean(p)) if len(p) else np.nan,
        "brier": brier_score_loss(y, p) if len(y) else np.nan,
        "logloss": log_loss(y, p, labels=[0, 1]) if len(y) else np.nan,
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


def load_hitter_training() -> tuple[pd.DataFrame, list[str]]:
    mart = pd.read_csv(HISTORICAL_MART)
    mart["has_pre_kbo_savant_features"] = to_bool(mart["has_pre_kbo_savant_features"])
    mart["label_available"] = to_bool(mart["label_available"])
    for target in TARGETS:
        mart[target] = pd.to_numeric(mart[target], errors="coerce").fillna(0).astype(int)
    train = mart[
        mart["role_model_family"].eq("hitter")
        & mart["has_pre_kbo_savant_features"]
        & mart["label_available"]
    ].copy()
    usable = []
    for feature, candidate_col in HITTER_FEATURE_MAP.items():
        values = pd.to_numeric(train[feature], errors="coerce")
        if values.notna().sum() >= 8 and values.nunique(dropna=True) > 1:
            usable.append(feature)
    return train, usable


def build_hitter_feature_map(features: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "historical_feature": feature,
                "candidate_feature": HITTER_FEATURE_MAP[feature],
                "feature_family": "savant_only_candidate_compatible",
                "use_status": "used",
            }
            for feature in features
        ]
    )


def audit_hitter_model(train: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    splitter = RepeatedStratifiedKFold(n_splits=3, n_repeats=30, random_state=22)
    for target in TARGETS:
        y = train[target].astype(int).to_numpy()
        if len(np.unique(y)) < 2 or pd.Series(y).value_counts().min() < 3:
            continue
        for fold_id, (train_idx, valid_idx) in enumerate(splitter.split(train, y), start=1):
            fold_train = train.iloc[train_idx].copy()
            fold_valid = train.iloc[valid_idx].copy()

            pred = prior_prediction(fold_train, fold_valid, target)
            metrics = evaluate_predictions(fold_valid[target], pred)
            rows.append(
                {
                    "validation_scheme": "repeated_stratified_cv",
                    "candidate_component": "hitter_savant_pilot_candidate_compatible",
                    "target": target,
                    "model": "role_prior",
                    "fold_id": fold_id,
                    "train_rows": len(fold_train),
                    "valid_rows": len(fold_valid),
                    "feature_count": len(features),
                    **metrics,
                }
            )

            model = build_logit()
            model.fit(fold_train[features], fold_train[target])
            pred = model.predict_proba(fold_valid[features])[:, 1]
            metrics = evaluate_predictions(fold_valid[target], pred)
            rows.append(
                {
                    "validation_scheme": "repeated_stratified_cv",
                    "candidate_component": "hitter_savant_pilot_candidate_compatible",
                    "target": target,
                    "model": "ridge_logit",
                    "fold_id": fold_id,
                    "train_rows": len(fold_train),
                    "valid_rows": len(fold_valid),
                    "feature_count": len(features),
                    **metrics,
                }
            )

    scores = pd.DataFrame(rows)
    if scores.empty:
        return scores
    summary = (
        scores.groupby(["validation_scheme", "candidate_component", "target", "model"], dropna=False)
        .agg(
            folds=("fold_id", "nunique"),
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
    prior = summary[summary["model"].eq("role_prior")][
        ["validation_scheme", "candidate_component", "target", "mean_brier", "mean_precision_top_25pct"]
    ].rename(
        columns={
            "mean_brier": "role_prior_mean_brier",
            "mean_precision_top_25pct": "role_prior_precision_top_25pct",
        }
    )
    out = summary.merge(prior, on=["validation_scheme", "candidate_component", "target"], how="left")
    out["brier_lift_vs_role_prior"] = out["role_prior_mean_brier"] - out["mean_brier"]
    out["top25_precision_lift_vs_role_prior"] = (
        out["mean_precision_top_25pct"] - out["role_prior_precision_top_25pct"]
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
    return out.sort_values(["target", "mean_brier", "model"])


def score_hitter_candidates(train: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    candidates = pd.read_csv(HITTER_POOL)
    feature_map = {candidate_col: feature for feature, candidate_col in HITTER_FEATURE_MAP.items() if feature in features}
    candidate_features = pd.DataFrame(index=candidates.index)
    for candidate_col, feature in feature_map.items():
        candidate_features[feature] = pd.to_numeric(candidates[candidate_col], errors="coerce")
    out = candidates.copy()
    out["hitter_model_feature_count"] = len(features)
    out["hitter_model_feature_non_null_count"] = candidate_features.notna().sum(axis=1)
    for target in TARGETS:
        model = build_logit()
        model.fit(train[features], train[target])
        out[f"hitter_savant_pilot_{target}_prob"] = clip_prob(model.predict_proba(candidate_features[features])[:, 1])
    out["hitter_savant_pilot_net_signal"] = (
        out["hitter_savant_pilot_success_prob"] - out["hitter_savant_pilot_failure_prob"]
    )
    out["hitter_savant_pilot_component_status"] = np.select(
        [
            out["hitter_model_feature_non_null_count"].lt(max(6, int(len(features) * 0.5))),
            out["hitter_savant_pilot_net_signal"].ge(0.25),
            out["hitter_savant_pilot_net_signal"].le(-0.10),
        ],
        ["insufficient_savant_feature_coverage", "positive_pilot_signal_unranked", "negative_pilot_signal_risk"],
        default="neutral_pilot_signal_unranked",
    )
    out["candidate_release_policy"] = "signal_component_only_no_recommendation"
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False

    keep = [
        "slot",
        "player_id",
        "player_name",
        "roster_team",
        "age",
        "bat_side",
        "birth_country",
        "market_access_bucket",
        "market_access_score",
        "availability_gate_pass",
        "first_pass_gate_pass",
        "final_priority_score",
        "recent_pa",
        "recent_woba",
        "recent_bb_pct",
        "recent_k_pct",
        "recent_whiff_per_swing",
        "recent_nonfast_whiff_per_swing",
        "recent_hardhit_rate",
        "recent_barrel_rate",
        "recent_hitter_count_xwoba",
        "hitter_model_feature_count",
        "hitter_model_feature_non_null_count",
        "hitter_savant_pilot_success_prob",
        "hitter_savant_pilot_failure_prob",
        "hitter_savant_pilot_net_signal",
        "hitter_savant_pilot_component_status",
        "candidate_release_policy",
        "is_final_recommendation",
        "shortlist_label_allowed",
        "candidate_name_release_allowed",
    ]
    return out[[col for col in keep if col in out.columns]]


def attach_pitcher_diagnostics() -> pd.DataFrame:
    pitchers = pd.read_csv(PITCHER_POOL)
    context = pd.read_csv(MILB_ROLE_CONTEXT)
    milb_cols = [
        "player_id",
        "milb_2026_highest_level_score",
        "milb_2025_2026_highest_level_score",
        "milb_2026_ip",
        "milb_2026_games",
        "milb_2026_games_started",
        "milb_2026_starter_share",
        "milb_2026_ip_per_game",
        "milb_2026_k9",
        "milb_2026_bb9",
        "milb_2026_hr9",
        "milb_2026_batters_faced",
        "milb_2026_aaa_ip",
        "milb_2026_aaa_games",
        "milb_2026_aaa_games_started",
        "milb_role_continuity_bucket",
        "milb_role_context_score",
    ]
    context = context[[col for col in milb_cols if col in context.columns]].drop_duplicates("player_id")
    out = pitchers.merge(context, on="player_id", how="left", validate="one_to_one")

    out["milb_damage_suppression_pct"] = safe_rank(out["milb_2026_hr9"], higher_is_better=False)
    out["milb_command_pct"] = safe_rank(out["milb_2026_bb9"], higher_is_better=False)
    out["milb_bat_missing_pct"] = safe_rank(out["milb_2026_k9"], higher_is_better=True)
    out["milb_current_track_pct"] = safe_rank(out["milb_2026_ip"].fillna(0), higher_is_better=True)
    out["pitcher_milb_damage_command_diagnostic_score"] = (
        out[["milb_damage_suppression_pct", "milb_command_pct", "milb_bat_missing_pct", "milb_current_track_pct"]]
        .mean(axis=1, skipna=True)
        .round(3)
    )
    no_track = out["milb_2026_ip"].isna() | out["milb_2026_ip"].fillna(0).le(0)
    out.loc[no_track, "pitcher_milb_damage_command_diagnostic_score"] = np.nan

    tags: list[list[str]] = []
    for row in out.to_dict("records"):
        row_tags: list[str] = []
        bucket = str(row.get("milb_role_continuity_bucket", ""))
        if not bucket or bucket == "nan":
            row_tags.append("no_milb_context_join")
        elif "no_2026" in bucket:
            row_tags.append("no_current_milb_track")
        elif "lower_level" in bucket:
            row_tags.append("current_lower_level_risk")
        elif "starter_load" in bucket:
            row_tags.append("current_aaa_starter_track")
        elif "swing" in bucket or "multi" in bucket:
            row_tags.append("current_aaa_multi_inning_track")
        elif "bullpen" in bucket:
            row_tags.append("current_aaa_bullpen_track")

        k9 = row.get("milb_2026_k9")
        bb9 = row.get("milb_2026_bb9")
        hr9 = row.get("milb_2026_hr9")
        ip = row.get("milb_2026_ip")
        if pd.notna(hr9) and hr9 >= 1.5:
            row_tags.append("home_run_damage_risk")
        if pd.notna(bb9) and bb9 >= 4.5:
            row_tags.append("walk_command_risk")
        if pd.notna(k9) and k9 >= 9.0:
            row_tags.append("bat_missing_upside")
        if pd.notna(hr9) and pd.notna(bb9) and pd.notna(ip) and hr9 <= 1.0 and bb9 <= 3.5 and ip >= 10:
            row_tags.append("damage_command_watch")
        if pd.notna(k9) and pd.notna(bb9) and k9 >= 9.0 and bb9 >= 4.5:
            row_tags.append("volatile_stuff_profile")
        if bool(row.get("injury_flag", False)):
            row_tags.append("medical_status_flag")
        if not row_tags:
            row_tags.append("neutral_milb_diagnostic")
        tags.append(row_tags)

    out["pitcher_milb_diagnostic_tags"] = ["|".join(items) for items in tags]
    out["pitcher_milb_diagnostic_status"] = np.select(
        [
            out["pitcher_milb_diagnostic_tags"].str.contains("damage_command_watch", na=False),
            out["pitcher_milb_diagnostic_tags"].str.contains("home_run_damage_risk|walk_command_risk", regex=True, na=False),
            out["pitcher_milb_diagnostic_tags"].str.contains("no_current_milb_track|no_milb_context_join", regex=True, na=False),
        ],
        ["positive_diagnostic_watch_not_score", "risk_diagnostic_review_needed", "missing_or_stale_milb_context"],
        default="neutral_diagnostic_review",
    )
    out["pitcher_score_use_allowed"] = False
    out["pitcher_diagnostic_use_allowed"] = True
    out["candidate_release_policy"] = "diagnostic_tags_only_no_recommendation"
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False

    keep = [
        "slot",
        "player_id",
        "player_name",
        "roster_team",
        "age",
        "pitch_hand",
        "birth_country",
        "market_access_bucket",
        "market_access_score",
        "availability_gate_pass",
        "first_pass_gate_pass",
        "final_priority_score",
        "recent_starter_stabilizer_score",
        "recent_woba_allowed",
        "recent_three_ball_pitch_rate",
        "milb_role_continuity_bucket",
        "milb_role_context_score",
        "milb_2026_ip",
        "milb_2026_games_started",
        "milb_2026_k9",
        "milb_2026_bb9",
        "milb_2026_hr9",
        "pitcher_milb_damage_command_diagnostic_score",
        "pitcher_milb_diagnostic_tags",
        "pitcher_milb_diagnostic_status",
        "pitcher_score_use_allowed",
        "pitcher_diagnostic_use_allowed",
        "candidate_release_policy",
        "is_final_recommendation",
        "shortlist_label_allowed",
        "candidate_name_release_allowed",
    ]
    return out[[col for col in keep if col in out.columns]]


def attach_asian_feasibility() -> pd.DataFrame:
    market = pd.read_csv(ASIAN_MARKET)
    out = market.copy()
    nationality = out["asian_quota_nationality_gate"].fillna("unknown").astype(str)
    contract = out["contract_status_gate"].fillna("unknown").astype(str)
    access = out["availability_bucket"].fillna("").astype(str)
    out["asian_quota_feasibility_bucket"] = "needs_manual_feasibility_review"
    out.loc[nationality.eq("pass") & contract.str.contains("unknown", na=False), "asian_quota_feasibility_bucket"] = (
        "nationality_pass_contract_unknown"
    )
    out.loc[nationality.eq("unknown"), "asian_quota_feasibility_bucket"] = "nationality_unknown"
    out.loc[nationality.eq("fail"), "asian_quota_feasibility_bucket"] = "nationality_fail_regular_foreign_only"
    out["club_control_risk_flag"] = access.str.contains("low_access|under_club_control", regex=True, na=False)
    out["candidate_release_policy"] = "feasibility_inventory_only_no_recommendation"
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False

    keep = [
        "source_league",
        "team_code",
        "team_name",
        "roster_no",
        "player_name",
        "normalized_player_name",
        "position_group",
        "position",
        "born",
        "throws",
        "bats",
        "nationality",
        "nationality_source",
        "asian_league_history_gate",
        "asian_quota_nationality_gate",
        "contract_status_gate",
        "new_signing_cost_gate",
        "availability_bucket",
        "asian_quota_feasibility_bucket",
        "club_control_risk_flag",
        "candidate_release_policy",
        "is_final_recommendation",
        "shortlist_label_allowed",
        "candidate_name_release_allowed",
    ]
    return out[[col for col in keep if col in out.columns]]


def build_summary(hitters: pd.DataFrame, hitter_audit: pd.DataFrame, pitchers: pd.DataFrame, asian: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    rows.append(
        {
            "scope": "mlb_outfielder_hitter_pool",
            "rows": len(hitters),
            "primary_signal": "hitter_savant_pilot_component",
            "positive_or_watch_rows": int(hitters["hitter_savant_pilot_component_status"].eq("positive_pilot_signal_unranked").sum()),
            "risk_or_gap_rows": int(
                hitters["hitter_savant_pilot_component_status"]
                .isin(["negative_pilot_signal_risk", "insufficient_savant_feature_coverage"])
                .sum()
            ),
            "candidate_release_policy": "signal_component_only_no_recommendation",
        }
    )
    rows.append(
        {
            "scope": "mlb_pitcher_pool",
            "rows": len(pitchers),
            "primary_signal": "pitcher_milb_damage_command_diagnostic",
            "positive_or_watch_rows": int(
                pitchers["pitcher_milb_diagnostic_status"].eq("positive_diagnostic_watch_not_score").sum()
            ),
            "risk_or_gap_rows": int(
                pitchers["pitcher_milb_diagnostic_status"]
                .isin(["risk_diagnostic_review_needed", "missing_or_stale_milb_context"])
                .sum()
            ),
            "candidate_release_policy": "diagnostic_tags_only_no_recommendation",
        }
    )
    rows.append(
        {
            "scope": "asian_quota_market",
            "rows": len(asian),
            "primary_signal": "current_feasibility_tags",
            "positive_or_watch_rows": int(asian["asian_quota_feasibility_bucket"].eq("nationality_pass_contract_unknown").sum()),
            "risk_or_gap_rows": int(
                asian["asian_quota_feasibility_bucket"]
                .isin(["nationality_unknown", "nationality_fail_regular_foreign_only"])
                .sum()
            ),
            "candidate_release_policy": "feasibility_inventory_only_no_recommendation",
        }
    )
    audit_promoted = hitter_audit[
        hitter_audit["model"].eq("ridge_logit") & hitter_audit["promotion_status"].eq("pilot_promote")
    ]
    rows.append(
        {
            "scope": "hitter_model_audit",
            "rows": len(hitter_audit),
            "primary_signal": "candidate_compatible_repeated_cv",
            "positive_or_watch_rows": len(audit_promoted),
            "risk_or_gap_rows": int(len(hitter_audit) - len(audit_promoted)),
            "candidate_release_policy": "model_component_audit_only",
        }
    )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    hitter_train, hitter_features = load_hitter_training()
    hitter_audit = audit_hitter_model(hitter_train, hitter_features)
    hitter_feature_map = build_hitter_feature_map(hitter_features)
    hitters = score_hitter_candidates(hitter_train, hitter_features)
    pitchers = attach_pitcher_diagnostics()
    asian = attach_asian_feasibility()
    summary = build_summary(hitters, hitter_audit, pitchers, asian)

    hitters.to_csv(HITTER_COMPONENT_OUT, index=False)
    hitter_audit.to_csv(HITTER_AUDIT_OUT, index=False)
    hitter_feature_map.to_csv(HITTER_FEATURE_MAP_OUT, index=False)
    pitchers.to_csv(PITCHER_DIAGNOSTIC_OUT, index=False)
    asian.to_csv(ASIAN_FEASIBILITY_OUT, index=False)
    summary.to_csv(SUMMARY_OUT, index=False)

    print("wrote", HITTER_COMPONENT_OUT, hitters.shape)
    print("wrote", HITTER_AUDIT_OUT, hitter_audit.shape)
    print("wrote", HITTER_FEATURE_MAP_OUT, hitter_feature_map.shape)
    print("wrote", PITCHER_DIAGNOSTIC_OUT, pitchers.shape)
    print("wrote", ASIAN_FEASIBILITY_OUT, asian.shape)
    print("wrote", SUMMARY_OUT, summary.shape)
    print()
    print(hitter_audit.to_string(index=False))
    print()
    print(summary.to_string(index=False))
    print()
    print(pitchers["pitcher_milb_diagnostic_status"].value_counts(dropna=False).to_string())
    print()
    print(asian["asian_quota_feasibility_bucket"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
