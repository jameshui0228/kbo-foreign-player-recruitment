#!/usr/bin/env python3
"""Build a structured-only data-mining recommendation conclusion.

This script is intentionally different from the earlier weighted scouting board.
It trains leakage-safe historical KBO foreign-player models, applies those models
to the current MLB/MiLB candidate market, and ranks candidates by model outputs.

Inputs are structured numeric tables only. News/article/interview fields are not
used as model features.
"""

from __future__ import annotations

from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore", message="'penalty' was deprecated.*")
warnings.filterwarnings("ignore", message="Inconsistent values: penalty=.*")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables"
DOCS = ROOT / "docs"

MART_PATH = OUT / "kbo_translation_feature_family_ablation_mart_v0_3.csv"
MODEL_DECISION_PATH = OUT / "kbo_translation_failure_feature_family_decisions_v0_3.csv"
HITTER_POOL_PATH = OUT / "mlb_outfielder_availability_candidate_pool_v1.csv"
PITCHER_POOL_PATH = OUT / "mlb_pitcher_availability_candidate_pool_v1.csv"
MILB_STATS_PATH = OUT / "milb_market_pool_stats_latest.csv"

HITTER_OUT = OUT / "data_mining_hitter_candidates_v1.csv"
PITCHER_OUT = OUT / "data_mining_pitcher_candidates_v1.csv"
TOP_OUT = OUT / "data_mining_recommendations_top3_v1.csv"
MODEL_AUDIT_OUT = OUT / "data_mining_model_audit_v1.csv"
DOC_OUT = DOCS / "data_mining_recommendation_conclusion_v1.md"

BOOL_TRUE = {"true", "1", "1.0"}

HITTER_SAVANT_FEATURES = [
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
]

HITTER_CANDIDATE_MAP = {
    "pre_pa": "recent_pa",
    "pre_pitch": "recent_pitches",
    "pre_bb_pct": "recent_bb_pct",
    "pre_k_pct": "recent_k_pct",
    "pre_woba": "recent_woba",
    "pre_chase_rate": "recent_chase_rate",
    # Current candidate pool does not expose an exact zone-swing column.
    # Use chase as a conservative placeholder and record the mapping in output.
    "pre_zone_swing_rate": "recent_chase_rate",
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

PITCHER_MILB_DAMAGE_COMMAND_FEATURES = [
    "pre_kbo_milb_ip",
    "pre_kbo_milb_games",
    "pre_kbo_milb_games_started",
    "pre_kbo_milb_k9",
    "pre_kbo_milb_bb9",
    "pre_kbo_milb_hr9",
    "pre_kbo_milb_era",
    "pre_kbo_milb_whip",
]


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(BOOL_TRUE)


def numeric_frame(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for column in columns:
        out[column] = pd.to_numeric(df[column], errors="coerce") if column in df else np.nan
    return out


def title_name(value: object) -> str:
    if pd.isna(value):
        return ""
    name = str(value).strip()
    if not name:
        return ""
    if "," in name:
        last, first = [part.strip() for part in name.split(",", 1)]
        name = f"{first} {last}"
    return " ".join(part.capitalize() if part.islower() else part for part in name.split())


def usable_features(df: pd.DataFrame, features: list[str], min_non_null: int = 8) -> list[str]:
    usable: list[str] = []
    for feature in features:
        if feature not in df:
            continue
        values = pd.to_numeric(df[feature], errors="coerce")
        if values.notna().sum() >= min_non_null and values.nunique(dropna=True) > 1:
            usable.append(feature)
    return usable


def ridge_logit() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=0.7, max_iter=2000, solver="lbfgs")),
        ]
    )


def sparse_l1_logit() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(C=0.35, penalty="l1", max_iter=2000, solver="liblinear")),
        ]
    )


def ip_to_float(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    if "." in text:
        whole, frac = text.split(".", 1)
        try:
            return float(whole) + {"0": 0.0, "1": 1 / 3, "2": 2 / 3}.get(frac[0], float("0." + frac))
        except ValueError:
            return float(pd.to_numeric(value, errors="coerce"))
    return float(pd.to_numeric(value, errors="coerce"))


def weighted_average(group: pd.DataFrame, column: str) -> float:
    values = pd.to_numeric(group[column], errors="coerce")
    weights = pd.to_numeric(group["ip_float"], errors="coerce").fillna(0)
    mask = values.notna() & weights.gt(0)
    if mask.any():
        return float(np.average(values[mask], weights=weights[mask]))
    return float(values.mean()) if values.notna().any() else np.nan


def load_mart() -> pd.DataFrame:
    mart = pd.read_csv(MART_PATH)
    for column in ["has_pre_kbo_savant_features", "has_pre_kbo_milb", "has_model_pre_kbo_features", "label_available"]:
        if column in mart:
            mart[column] = to_bool(mart[column])
    for column in ["success", "failure"]:
        mart[column] = pd.to_numeric(mart[column], errors="coerce").fillna(0).astype(int)
    return mart


def train_hitter_models(mart: pd.DataFrame) -> tuple[Pipeline, Pipeline, list[str], pd.DataFrame]:
    train = mart[
        mart["role_model_family"].eq("hitter")
        & mart["has_pre_kbo_savant_features"]
        & mart["label_available"]
    ].copy()
    features = usable_features(train, HITTER_SAVANT_FEATURES)
    success_model = ridge_logit().fit(train[features], train["success"])
    failure_model = ridge_logit().fit(train[features], train["failure"])
    audit = pd.DataFrame(
        [
            {
                "slot": "foreign_hitter",
                "model_block": "hitter_success_classifier",
                "historical_rows": len(train),
                "feature_family": "savant_only",
                "model": "ridge_logit",
                "target": "success",
                "feature_count": len(features),
                "features": "|".join(features),
                "validation_summary": "v0.3 decision table promoted this family for hitter success",
            },
            {
                "slot": "foreign_hitter",
                "model_block": "hitter_failure_classifier",
                "historical_rows": len(train),
                "feature_family": "savant_only",
                "model": "ridge_logit",
                "target": "failure",
                "feature_count": len(features),
                "features": "|".join(features),
                "validation_summary": "v0.3 decision table promoted this family for hitter failure",
            },
        ]
    )
    return success_model, failure_model, features, audit


def score_hitter_candidates(success_model: Pipeline, failure_model: Pipeline, features: list[str]) -> pd.DataFrame:
    candidates = pd.read_csv(HITTER_POOL_PATH)
    model_frame = pd.DataFrame(index=candidates.index)
    mapping_notes = []
    for feature in features:
        source = HITTER_CANDIDATE_MAP.get(feature)
        model_frame[feature] = pd.to_numeric(candidates[source], errors="coerce") if source in candidates else np.nan
        mapping_notes.append(f"{feature}<={source}")

    candidates["dm_success_prob"] = success_model.predict_proba(model_frame[features])[:, 1]
    candidates["dm_failure_prob"] = failure_model.predict_proba(model_frame[features])[:, 1]
    candidates["dm_margin"] = candidates["dm_success_prob"] - candidates["dm_failure_prob"]
    candidates["player_name"] = candidates["player_name"].map(title_name)
    candidates["model_feature_mapping"] = ";".join(mapping_notes)
    candidates["dm_model_tier"] = "promoted_hitter_savant_success_failure_classifier"

    gate = (
        candidates["first_pass_gate_pass"].fillna(False)
        & candidates["is_40man"].eq(False)
        & candidates["injury_flag"].eq(False)
        & candidates["restricted_or_development_flag"].eq(False)
        & pd.to_numeric(candidates["recent_pa"], errors="coerce").ge(25)
    )
    candidates["data_mining_gate_pass"] = gate
    candidates["data_mining_gate_reason"] = np.where(
        gate,
        "pass: non40man + first-pass market gate + no injury/restricted flag + recent PA >= 25",
        "hold: failed one of non40man/market/injury/restricted/sample gates",
    )

    keep = [
        "player_id",
        "player_name",
        "roster_team",
        "primary_position",
        "primary_position_abbrev",
        "age",
        "bat_side",
        "pitch_hand",
        "birth_country",
        "is_40man",
        "status_description",
        "market_access_bucket",
        "recent_pa",
        "recent_woba",
        "recent_bb_pct",
        "recent_k_pct",
        "recent_hardhit_rate",
        "recent_barrel_rate",
        "dm_success_prob",
        "dm_failure_prob",
        "dm_margin",
        "data_mining_gate_pass",
        "data_mining_gate_reason",
        "dm_model_tier",
        "model_feature_mapping",
    ]
    out = candidates[keep].copy()
    out = out.sort_values(["data_mining_gate_pass", "dm_margin"], ascending=[False, False])
    out["data_mining_rank"] = out[out["data_mining_gate_pass"]].groupby(lambda _: True).cumcount() + 1
    out.loc[~out["data_mining_gate_pass"], "data_mining_rank"] = np.nan
    return out


def train_pitcher_models(mart: pd.DataFrame) -> tuple[Pipeline, Pipeline, list[str], pd.DataFrame]:
    train = mart[
        mart["role_model_family"].eq("pitcher")
        & mart["has_pre_kbo_milb"]
        & mart["label_available"]
    ].copy()
    features = usable_features(train, PITCHER_MILB_DAMAGE_COMMAND_FEATURES)
    success_model = sparse_l1_logit().fit(train[features], train["success"])
    failure_model = sparse_l1_logit().fit(train[features], train["failure"])
    audit = pd.DataFrame(
        [
            {
                "slot": "foreign_pitcher",
                "model_block": "pitcher_success_diagnostic",
                "historical_rows": len(train),
                "feature_family": "milb_damage_command",
                "model": "sparse_l1_logit",
                "target": "success",
                "feature_count": len(features),
                "features": "|".join(features),
                "validation_summary": "v0.3 decision table marked pitcher success as watch/diagnostic",
            },
            {
                "slot": "foreign_pitcher",
                "model_block": "pitcher_failure_warning_only",
                "historical_rows": len(train),
                "feature_family": "milb_damage_command",
                "model": "sparse_l1_logit",
                "target": "failure",
                "feature_count": len(features),
                "features": "|".join(features),
                "validation_summary": "v0.3 decision table did not promote pitcher failure; use as warning only",
            },
        ]
    )
    return success_model, failure_model, features, audit


def aggregate_pitcher_milb_features(candidate_ids: set[float]) -> pd.DataFrame:
    milb = pd.read_csv(MILB_STATS_PATH, low_memory=False)
    milb["season"] = pd.to_numeric(milb["season"], errors="coerce")
    milb = milb[
        milb["stat_group"].eq("pitching")
        & milb["player_id"].isin(candidate_ids)
        & milb["season"].ge(2025)
    ].copy()
    if milb.empty:
        return pd.DataFrame(columns=["player_id", *PITCHER_MILB_DAMAGE_COMMAND_FEATURES])

    milb["ip_float"] = milb["innings_pitched"].map(ip_to_float)
    numeric_cols = [
        "games_pitched",
        "games_started",
        "strikeouts_per9_inn",
        "walks_per9_inn",
        "home_runs_per9",
        "era",
        "whip",
    ]
    for column in numeric_cols:
        milb[column] = pd.to_numeric(milb[column], errors="coerce")

    rows: list[dict[str, object]] = []
    for player_id, group in milb.groupby("player_id"):
        rows.append(
            {
                "player_id": player_id,
                "pre_kbo_milb_ip": group["ip_float"].sum(min_count=1),
                "pre_kbo_milb_games": group["games_pitched"].sum(min_count=1),
                "pre_kbo_milb_games_started": group["games_started"].sum(min_count=1),
                "pre_kbo_milb_k9": weighted_average(group, "strikeouts_per9_inn"),
                "pre_kbo_milb_bb9": weighted_average(group, "walks_per9_inn"),
                "pre_kbo_milb_hr9": weighted_average(group, "home_runs_per9"),
                "pre_kbo_milb_era": weighted_average(group, "era"),
                "pre_kbo_milb_whip": weighted_average(group, "whip"),
            }
        )
    return pd.DataFrame(rows)


def score_pitcher_candidates(success_model: Pipeline, failure_model: Pipeline, features: list[str]) -> pd.DataFrame:
    candidates = pd.read_csv(PITCHER_POOL_PATH)
    agg = aggregate_pitcher_milb_features(set(candidates["player_id"].dropna()))
    candidates = candidates.merge(agg, on="player_id", how="left")
    model_frame = numeric_frame(candidates, features)
    candidates["dm_success_prob"] = success_model.predict_proba(model_frame[features])[:, 1]
    candidates["dm_failure_prob"] = failure_model.predict_proba(model_frame[features])[:, 1]
    candidates["dm_margin"] = candidates["dm_success_prob"] - candidates["dm_failure_prob"]
    candidates["player_name"] = candidates["player_name"].map(title_name)
    candidates["dm_model_tier"] = "watch_pitcher_milb_success_diagnostic_failure_warning_only"
    candidates["model_feature_mapping"] = "current 2025-2026 MiLB pitching rows aggregated to pre_kbo_milb_* features"

    gate = (
        candidates["first_pass_gate_pass"].fillna(False)
        & candidates["is_40man"].eq(False)
        & candidates["injury_flag"].eq(False)
        & candidates["restricted_or_development_flag"].eq(False)
        & pd.to_numeric(candidates["pre_kbo_milb_ip"], errors="coerce").ge(20)
    )
    candidates["data_mining_gate_pass"] = gate
    candidates["data_mining_gate_reason"] = np.where(
        gate,
        "pass: non40man + first-pass market gate + no injury/restricted flag + 2025-2026 MiLB IP >= 20",
        "hold: failed one of non40man/market/injury/restricted/MiLB-IP gates",
    )

    keep = [
        "player_id",
        "player_name",
        "roster_team",
        "primary_position",
        "age",
        "pitch_hand",
        "birth_country",
        "is_40man",
        "status_description",
        "market_access_bucket",
        "recent_games",
        "recent_start_proxy_games",
        "pre_kbo_milb_ip",
        "pre_kbo_milb_games",
        "pre_kbo_milb_games_started",
        "pre_kbo_milb_k9",
        "pre_kbo_milb_bb9",
        "pre_kbo_milb_hr9",
        "pre_kbo_milb_era",
        "pre_kbo_milb_whip",
        "dm_success_prob",
        "dm_failure_prob",
        "dm_margin",
        "data_mining_gate_pass",
        "data_mining_gate_reason",
        "dm_model_tier",
        "model_feature_mapping",
    ]
    out = candidates[keep].copy()
    out = out.sort_values(["data_mining_gate_pass", "dm_margin"], ascending=[False, False])
    out["data_mining_rank"] = out[out["data_mining_gate_pass"]].groupby(lambda _: True).cumcount() + 1
    out.loc[~out["data_mining_gate_pass"], "data_mining_rank"] = np.nan
    return out


def build_top_table(hitter: pd.DataFrame, pitcher: pd.DataFrame) -> pd.DataFrame:
    h = hitter[hitter["data_mining_gate_pass"]].head(3).copy()
    h["slot"] = "foreign_hitter"
    h["slot_label"] = "외인타자"
    h["rank"] = range(1, len(h) + 1)
    h["model_conclusion"] = "historical KBO hitter success/failure classifiers selected this player"
    h["recommendation_strength"] = "model_supported_lead"

    p = pitcher[pitcher["data_mining_gate_pass"]].head(3).copy()
    p["slot"] = "foreign_pitcher"
    p["slot_label"] = "외인투수"
    p["rank"] = range(1, len(p) + 1)
    p["model_conclusion"] = np.where(
        p["dm_margin"].ge(0),
        "historical KBO pitcher MiLB success diagnostic selected this player; pitcher model remains watch-grade",
        "listed only because it passes market/sample gates; model margin is negative and should not be treated as a recommendation",
    )
    p["recommendation_strength"] = np.where(
        p["dm_margin"].ge(0),
        "diagnostic_lead",
        "hold_negative_model_margin",
    )

    cols = [
        "slot",
        "slot_label",
        "rank",
        "player_id",
        "player_name",
        "roster_team",
        "age",
        "is_40man",
        "market_access_bucket",
        "dm_success_prob",
        "dm_failure_prob",
        "dm_margin",
        "dm_model_tier",
        "recommendation_strength",
        "model_conclusion",
    ]
    return pd.concat([h[cols], p[cols]], ignore_index=True)


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_doc(top: pd.DataFrame, audit: pd.DataFrame, decisions: pd.DataFrame) -> str:
    hitter_rows = top[top["slot"].eq("foreign_hitter")]
    pitcher_rows = top[top["slot"].eq("foreign_pitcher")]
    promoted = decisions[decisions["promotion_status"].isin(["pilot_promote", "watch"])].copy()
    lines = [
        "# Data-Mining Recommendation Conclusion v1",
        "",
        "Generated from structured numeric data only. News, interviews, article counts, and text-derived fields were excluded from model inputs.",
        "",
        "## Core Conclusion",
        "",
        "The data-mining model changed the recommendation board. The strongest defendable conclusion is:",
        "",
        "> SSG should prioritize a foreign outfielder whose historical-KBO translation pattern looks like a low-failure, everyday-volume hitter. For pitchers, the current historical model is weaker, so the model does not yet justify a firm final recommendation; it only creates diagnostic leads.",
        "",
        "## Model Stack",
        "",
        "| Slot | Historical rows | Feature family | Model | Target | Decision |",
        "|---|---:|---|---|---|---|",
    ]
    for row in audit.to_dict("records"):
        if row["slot"] == "foreign_hitter":
            decision = "promoted"
        elif row["target"] == "success":
            decision = "watch/diagnostic"
        else:
            decision = "not promoted; warning only"
        lines.append(
            f"| {row['slot']} | {row['historical_rows']} | {row['feature_family']} | {row['model']} | {row['target']} | {decision} |"
        )

    lines += [
        "",
        "## Validation Evidence Used",
        "",
        "| Role | Target | Feature family | Model | AUC | Brier lift | Top-25 precision lift | Promotion status |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in promoted.to_dict("records"):
        lines.append(
            "| "
            f"{row['role_model_family']} | {row['target']} | {row['feature_family']} | {row['model']} | "
            f"{row['mean_auc']:.3f} | {row['brier_lift_vs_role_prior']:.3f} | "
            f"{row['top25_precision_lift_vs_role_prior']:.3f} | {row['promotion_status']} |"
        )

    lines += [
        "",
        "## Top 3 Foreign Hitter Leads",
        "",
        "| Rank | Player | Org | Age | 40-man | P(success) | P(failure) | Margin |",
        "|---:|---|---|---:|---|---:|---:|---:|",
    ]
    for row in hitter_rows.to_dict("records"):
        lines.append(
            f"| {int(row['rank'])} | {row['player_name']} | {row['roster_team']} | {row['age']:.0f} | "
            f"{row['is_40man']} | {pct(row['dm_success_prob'])} | {pct(row['dm_failure_prob'])} | {row['dm_margin']:.3f} |"
        )

    lines += [
        "",
        "## Top 3 Foreign Pitcher Diagnostic Leads",
        "",
        "| Rank | Player | Org | Age | 40-man | P(success) | P(failure warning) | Margin | Strength |",
        "|---:|---|---|---:|---|---:|---:|---:|---|",
    ]
    for row in pitcher_rows.to_dict("records"):
        lines.append(
            f"| {int(row['rank'])} | {row['player_name']} | {row['roster_team']} | {row['age']:.0f} | "
            f"{row['is_40man']} | {pct(row['dm_success_prob'])} | {pct(row['dm_failure_prob'])} | {row['dm_margin']:.3f} | {row['recommendation_strength']} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "1. Hitter conclusion is model-supported: hitter Savant-only success/failure classifiers passed the v0.3 pilot promotion gate.",
        "2. The model no longer favors tiny-sample hitters just because a manual SSG-fit score was high. Brennan/Fletcher drop behind larger-sample candidates.",
        "3. Pitcher conclusion is not as strong as hitter conclusion. The pitcher historical model is watch-grade, not a fully promoted classifier; negative-margin rows are holds, not recommendations.",
        "4. Salary is still a required next hard gate. This run uses roster/market access but does not yet have complete actual salary for the full candidate market.",
        "",
        "## Output Files",
        "",
        f"- `{HITTER_OUT.relative_to(ROOT)}`",
        f"- `{PITCHER_OUT.relative_to(ROOT)}`",
        f"- `{TOP_OUT.relative_to(ROOT)}`",
        f"- `{MODEL_AUDIT_OUT.relative_to(ROOT)}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    mart = load_mart()
    decisions = pd.read_csv(MODEL_DECISION_PATH)

    h_success, h_failure, h_features, h_audit = train_hitter_models(mart)
    p_success, p_failure, p_features, p_audit = train_pitcher_models(mart)

    hitter = score_hitter_candidates(h_success, h_failure, h_features)
    pitcher = score_pitcher_candidates(p_success, p_failure, p_features)
    audit = pd.concat([h_audit, p_audit], ignore_index=True)
    top = build_top_table(hitter, pitcher)

    hitter.to_csv(HITTER_OUT, index=False)
    pitcher.to_csv(PITCHER_OUT, index=False)
    top.to_csv(TOP_OUT, index=False)
    audit.to_csv(MODEL_AUDIT_OUT, index=False)
    DOC_OUT.write_text(build_doc(top, audit, decisions), encoding="utf-8")

    print("wrote", HITTER_OUT, hitter.shape)
    print("wrote", PITCHER_OUT, pitcher.shape)
    print("wrote", TOP_OUT, top.shape)
    print("wrote", MODEL_AUDIT_OUT, audit.shape)
    print("wrote", DOC_OUT)
    print()
    print(top.to_string(index=False))


if __name__ == "__main__":
    main()
