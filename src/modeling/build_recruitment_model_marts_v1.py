#!/usr/bin/env python3
"""Build gate-level marts for the foreign-player recruitment pipeline.

This run intentionally avoids final player recommendations. It checks whether
the current data can support the next modeling layers:

1. historical KBO outcome labels joined to pre-KBO Savant features;
2. KBO translation modeling readiness;
3. failure-risk modeling readiness;
4. candidate-market coverage readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from difflib import SequenceMatcher
import re
import unicodedata

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

LABEL_PATH = OUTPUT_DIR / "kbo_foreign_player_season_labels_v0_1.csv"
PITCHER_FEATURE_PATH = OUTPUT_DIR / "savant_pitcher_feature_summary_2022_2026.csv"
HITTER_FEATURE_PATH = OUTPUT_DIR / "savant_hitter_feature_summary_2022_2026.csv"
PITCHER_FEATURE_FALLBACK_PATH = OUTPUT_DIR / "savant_pitcher_feature_summary_2023_2026.csv"
HITTER_FEATURE_FALLBACK_PATH = OUTPUT_DIR / "savant_hitter_feature_summary_2023_2026.csv"
PITCHER_POOL_PATH = OUTPUT_DIR / "mlb_pitcher_availability_candidate_pool_v1.csv"
HITTER_POOL_PATH = OUTPUT_DIR / "mlb_outfielder_availability_candidate_pool_v1.csv"
MARKET_PLAN_PATH = OUTPUT_DIR / "candidate_market_collection_plan_v1.csv"
SSG_PITCHER_DECISION_PATH = OUTPUT_DIR / "ssg_pitching_message_v0_2_decision_table.csv"
ARCHETYPE_SUMMARY_PATH = OUTPUT_DIR / "kbo_foreign_archetype_summary_v0_1.csv"


TRAINING_READY_MIN_ROWS = 60
TRAINING_READY_MIN_ROLE_ROWS = 20
TRAINING_READY_MIN_CLASS_ROWS = 8


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def normalize_name(value: object) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    if "," in text:
        parts = [part.strip() for part in text.split(",", 1)]
        text = f"{parts[1]} {parts[0]}"
    text = re.sub(r"\\b(jr|sr|ii|iii|iv|v)\\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\\s+", " ", text).strip()


def name_variants(value: object) -> set[str]:
    base = normalize_name(value)
    if not base:
        return set()
    tokens = base.split()
    variants = {base}
    if len(tokens) >= 2:
        variants.add(f"{tokens[0]} {tokens[-1]}")
        variants.add(f"{tokens[-1]} {tokens[0]}")
    if len(tokens) >= 3:
        variants.add(" ".join([tokens[0], tokens[1], tokens[-1]]))
    return {variant for variant in variants if variant}


@dataclass
class NameMatch:
    source_name: str
    matched_name: str
    match_key: str
    match_method: str
    match_score: float
    matched_player_id: object


def build_name_index(features: pd.DataFrame, name_col: str, id_col: str) -> dict[str, list[dict[str, object]]]:
    index: dict[str, list[dict[str, object]]] = {}
    unique_players = features[[id_col, name_col]].dropna().drop_duplicates()
    for _, row in unique_players.iterrows():
        raw_name = str(row[name_col])
        for variant in name_variants(raw_name):
            index.setdefault(variant, []).append(
                {
                    "raw_name": raw_name,
                    "player_id": row[id_col],
                    "match_key": variant,
                }
            )
    return index


def find_name_match(source_name: object, index: dict[str, list[dict[str, object]]]) -> NameMatch | None:
    variants = name_variants(source_name)
    if not variants:
        return None

    for variant in sorted(variants, key=lambda item: (-len(item), item)):
        candidates = index.get(variant, [])
        if len(candidates) == 1:
            candidate = candidates[0]
            return NameMatch(
                source_name=str(source_name),
                matched_name=str(candidate["raw_name"]),
                match_key=variant,
                match_method="exact_variant",
                match_score=1.0,
                matched_player_id=candidate["player_id"],
            )

    best: tuple[float, str, dict[str, object]] | None = None
    for variant in variants:
        for key, candidates in index.items():
            score = SequenceMatcher(None, variant, key).ratio()
            if score < 0.94:
                continue
            if len(candidates) != 1:
                continue
            candidate = candidates[0]
            if best is None or score > best[0]:
                best = (score, key, candidate)

    if best is None:
        return None

    score, key, candidate = best
    return NameMatch(
        source_name=str(source_name),
        matched_name=str(candidate["raw_name"]),
        match_key=key,
        match_method="fuzzy_high_confidence",
        match_score=score,
        matched_player_id=candidate["player_id"],
    )


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    numeric = pd.to_numeric(values, errors="coerce")
    weight = pd.to_numeric(weights, errors="coerce").fillna(0)
    mask = numeric.notna() & weight.gt(0)
    if not mask.any():
        return float("nan")
    return float(np.average(numeric[mask], weights=weight[mask]))


def join_unique(values: pd.Series) -> str:
    cleaned = [str(value).strip() for value in values.dropna().unique() if str(value).strip()]
    return " | ".join(cleaned)


def aggregate_prior_features(prior: pd.DataFrame, role: str) -> dict[str, object]:
    if prior.empty:
        return {}
    years = sorted(int(year) for year in prior["game_year"].dropna().unique())
    row: dict[str, object] = {
        "prior_savant_years": "|".join(map(str, years)),
        "prior_savant_rows": len(prior),
        "prior_savant_latest_year": max(years) if years else np.nan,
    }
    if role == "hitter":
        weight_col = "pa"
        numeric_cols = [
            "pa",
            "pitch",
            "bb_pct",
            "k_pct",
            "hr_pct",
            "woba",
            "chase_rate",
            "zone_swing_rate",
            "nonfast_chase_rate",
            "nonfast_whiff_per_swing",
            "whiff_per_swing",
            "hardhit_rate",
            "barrel_rate",
            "sweet_spot_rate",
            "air_bbe_rate",
            "same_field_air_rate_proxy",
            "low_velo_xwoba",
            "high_velo_xwoba",
            "break_off_xwoba",
            "hitter_count_xwoba",
            "ssg_message_screen_score",
        ]
    else:
        weight_col = "pa"
        numeric_cols = [
            "pa",
            "pitch",
            "games",
            "start_proxy_games",
            "games_80plus_pitches",
            "games_90plus_pitches",
            "games_100plus_pitches",
            "bb_hbp_pct",
            "k_pct",
            "hr_pct",
            "woba_allowed",
            "xwoba_allowed_bbe",
            "xslg_allowed_bbe",
            "whiff_per_swing",
            "chase_rate",
            "zone_rate",
            "first_pitch_nonball_rate",
            "three_ball_pitch_rate",
            "hardhit_rate",
            "barrel_rate",
            "start_proxy_rate",
            "third_time_game_rate",
            "early_1_3_woba_allowed",
            "runner_on_base_woba_allowed",
            "risp_woba_allowed",
            "third_time_woba_allowed",
            "starter_stabilizer_score",
        ]
    for column in numeric_cols:
        if column not in prior.columns:
            continue
        if column in {"pa", "pitch", "games", "start_proxy_games", "games_80plus_pitches", "games_90plus_pitches", "games_100plus_pitches"}:
            row[f"pre_{column}"] = pd.to_numeric(prior[column], errors="coerce").sum()
        else:
            row[f"pre_{column}"] = weighted_mean(prior[column], prior[weight_col])
    return row


def build_historical_savant_marts(
    labels: pd.DataFrame, pitcher_features: pd.DataFrame, hitter_features: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pitcher_index = build_name_index(pitcher_features, "player_name", "pitcher")
    hitter_index = build_name_index(hitter_features, "batter_name", "batter")
    rows: list[dict[str, object]] = []
    audit_rows: list[dict[str, object]] = []

    eligible = labels[
        labels["season"].between(2023, 2025)
        & labels["outcome_available"]
        & labels["role_group"].isin(["hitter", "starter"])
        & labels["player_name_en"].notna()
    ].copy()

    for _, label in eligible.iterrows():
        role = "hitter" if label["role_group"] == "hitter" else "pitcher"
        features = hitter_features if role == "hitter" else pitcher_features
        id_col = "batter" if role == "hitter" else "pitcher"
        index = hitter_index if role == "hitter" else pitcher_index
        match = find_name_match(label["player_name_en"], index)
        prior = pd.DataFrame()
        if match is not None:
            prior = features[
                (pd.to_numeric(features[id_col], errors="coerce") == pd.to_numeric(pd.Series([match.matched_player_id]), errors="coerce").iloc[0])
                & (features["game_year"] < int(label["season"]))
            ].copy()

        has_prior = not prior.empty
        audit_rows.append(
            {
                "season": int(label["season"]),
                "player_key": label["player_key"],
                "player_name": label["player_name"],
                "player_name_en": label["player_name_en"],
                "kbo_team": label["kbo_team"],
                "role_group": label["role_group"],
                "role_model_family": role,
                "matched_to_savant": bool(match is not None),
                "has_pre_kbo_savant_features": has_prior,
                "match_method": match.match_method if match else "",
                "match_score": match.match_score if match else np.nan,
                "match_key": match.match_key if match else "",
                "matched_savant_name": match.matched_name if match else "",
                "matched_savant_player_id": match.matched_player_id if match else np.nan,
                "prior_savant_years": join_unique(prior["game_year"].astype(str)) if has_prior else "",
                "prior_savant_rows": len(prior),
                "success": int(label["success"]),
                "failure": int(label["failure"]),
            }
        )

        base = {
            "season": int(label["season"]),
            "player_key": label["player_key"],
            "player_name": label["player_name"],
            "player_name_en": label["player_name_en"],
            "kbo_team": label["kbo_team"],
            "role_group": label["role_group"],
            "role_model_family": role,
            "source_confidence_1_5": label["source_confidence_1_5"],
            "outcome_available": bool(label["outcome_available"]),
            "label_available": bool(label["label_available"]),
            "success": int(label["success"]),
            "strong_success": int(label["strong_success"]),
            "failure": int(label["failure"]),
            "first_kbo_pa": label["first_kbo_pa"],
            "first_kbo_ip": label["first_kbo_ip"],
            "first_kbo_war": label["first_kbo_war"],
            "first_kbo_wrc_plus": label["first_kbo_wrc_plus"],
            "first_kbo_era": label["first_kbo_era"],
            "renewed_next_year": label["renewed_next_year"],
            "in_season_replaced": label["in_season_replaced"],
            "injury_exit_flag": label["injury_exit_flag"],
            "performance_exit_flag": label["performance_exit_flag"],
            "matched_to_savant": bool(match is not None),
            "has_pre_kbo_savant_features": has_prior,
            "match_method": match.match_method if match else "",
            "match_score": match.match_score if match else np.nan,
            "matched_savant_name": match.matched_name if match else "",
            "matched_savant_player_id": match.matched_player_id if match else np.nan,
        }
        base.update(aggregate_prior_features(prior, role) if has_prior else {})
        rows.append(base)

    translation_mart = pd.DataFrame(rows)
    audit = pd.DataFrame(audit_rows)
    failure_mart = translation_mart.copy()
    if not failure_mart.empty:
        failure_mart["risk_target"] = failure_mart["failure"]
        failure_mart["risk_target_definition"] = "KBO first-season failure proxy from renewal/replacement/performance-exit labels"
        failure_mart["trainable_row"] = failure_mart["has_pre_kbo_savant_features"] & failure_mart["label_available"]
        failure_mart["current_limitations"] = np.where(
            failure_mart["trainable_row"],
            "pre_kbo_savant_features_available",
            "missing_pre_kbo_savant_features_or_label",
        )

    return translation_mart, failure_mart, audit


def build_translation_readiness(translation_mart: pd.DataFrame) -> pd.DataFrame:
    if translation_mart.empty:
        return pd.DataFrame()
    rows = []
    for role, group in translation_mart.groupby("role_model_family", dropna=False):
        trainable = group[group["has_pre_kbo_savant_features"] & group["label_available"]]
        success_count = int(trainable["success"].sum()) if not trainable.empty else 0
        failure_count = int(trainable["failure"].sum()) if not trainable.empty else 0
        rows.append(
            {
                "model_layer": "kbo_translation_and_failure_risk",
                "role_model_family": role,
                "eligible_labeled_rows": len(group),
                "pre_kbo_savant_matched_rows": len(trainable),
                "coverage_rate": len(trainable) / len(group) if len(group) else np.nan,
                "success_rows": success_count,
                "failure_rows": failure_count,
                "training_ready": bool(
                    len(trainable) >= TRAINING_READY_MIN_ROLE_ROWS
                    and success_count >= TRAINING_READY_MIN_CLASS_ROWS
                    and failure_count >= TRAINING_READY_MIN_CLASS_ROWS
                ),
                "minimum_role_rows_required": TRAINING_READY_MIN_ROLE_ROWS,
                "minimum_class_rows_required": TRAINING_READY_MIN_CLASS_ROWS,
            }
        )
    trainable_all = translation_mart[translation_mart["has_pre_kbo_savant_features"] & translation_mart["label_available"]]
    rows.append(
        {
            "model_layer": "kbo_translation_and_failure_risk",
            "role_model_family": "all_roles",
            "eligible_labeled_rows": len(translation_mart),
            "pre_kbo_savant_matched_rows": len(trainable_all),
            "coverage_rate": len(trainable_all) / len(translation_mart) if len(translation_mart) else np.nan,
            "success_rows": int(trainable_all["success"].sum()) if not trainable_all.empty else 0,
            "failure_rows": int(trainable_all["failure"].sum()) if not trainable_all.empty else 0,
            "training_ready": bool(
                len(trainable_all) >= TRAINING_READY_MIN_ROWS
                and trainable_all["success"].sum() >= TRAINING_READY_MIN_CLASS_ROWS
                and trainable_all["failure"].sum() >= TRAINING_READY_MIN_CLASS_ROWS
            ),
            "minimum_role_rows_required": TRAINING_READY_MIN_ROWS,
            "minimum_class_rows_required": TRAINING_READY_MIN_CLASS_ROWS,
        }
    )
    return pd.DataFrame(rows)


def build_candidate_market_coverage() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    plan = pd.read_csv(MARKET_PLAN_PATH) if MARKET_PLAN_PATH.exists() else pd.DataFrame()

    def add_current_pool(slot: str, path: Path, source_scope: str) -> None:
        if path.exists():
            pool = pd.read_csv(path)
            rows.append(
                {
                    "slot": slot,
                    "market_scope": source_scope,
                    "rows": len(pool),
                    "first_pass_gate_pass": int(pool.get("first_pass_gate_pass", pd.Series(dtype=bool)).astype(bool).sum()),
                    "non40man_org_candidate": int(pool["market_access_bucket"].eq("non40man_org_candidate").sum())
                    if "market_access_bucket" in pool.columns
                    else 0,
                    "dfa_designated_high_signal": int(pool["market_access_bucket"].eq("dfa_designated_high_signal").sum())
                    if "market_access_bucket" in pool.columns
                    else 0,
                    "medical_red_flag": int(pool["market_access_bucket"].eq("medical_red_flag").sum())
                    if "market_access_bucket" in pool.columns
                    else 0,
                    "mlb_active_low_access": int(pool["market_access_bucket"].eq("mlb_active_low_access").sum())
                    if "market_access_bucket" in pool.columns
                    else 0,
                    "data_status": "partial_current_mlb_org_only",
                    "blocking_gap": "needs transaction/free-agent feed, option/salary proxy, medical review, Korea-willingness, and manual contract feasibility",
                }
            )
        else:
            rows.append(
                {
                    "slot": slot,
                    "market_scope": source_scope,
                    "rows": 0,
                    "first_pass_gate_pass": 0,
                    "non40man_org_candidate": 0,
                    "dfa_designated_high_signal": 0,
                    "medical_red_flag": 0,
                    "mlb_active_low_access": 0,
                    "data_status": "missing",
                    "blocking_gap": "pool file not built",
                }
            )

    add_current_pool("regular_foreign_pitcher", PITCHER_POOL_PATH, "MLB Savant 2025-2026 plus MLB official roster status")
    add_current_pool("regular_foreign_hitter_outfield_priority", HITTER_POOL_PATH, "MLB Savant 2025-2026 plus MLB official roster status")

    for bucket in ["injury_replacement", "asian_quota", "article_full_text", "weather_park_context"]:
        plan_row = plan[plan["market_bucket"].eq(bucket)].head(1) if not plan.empty else pd.DataFrame()
        rows.append(
            {
                "slot": bucket,
                "market_scope": plan_row["primary_source"].iloc[0] if not plan_row.empty else "",
                "rows": 0,
                "first_pass_gate_pass": 0,
                "non40man_org_candidate": 0,
                "dfa_designated_high_signal": 0,
                "medical_red_flag": 0,
                "mlb_active_low_access": 0,
                "data_status": plan_row["status"].iloc[0] if not plan_row.empty else "not_started",
                "blocking_gap": plan_row["data_needed"].iloc[0] if not plan_row.empty else "not_started",
            }
        )

    return pd.DataFrame(rows)


def build_gate_status(translation_readiness: pd.DataFrame, market_coverage: pd.DataFrame) -> pd.DataFrame:
    ssg_need_pass = False
    if SSG_PITCHER_DECISION_PATH.exists():
        decision = pd.read_csv(SSG_PITCHER_DECISION_PATH)
        pass_col = "pass"
        if pass_col in decision.columns:
            ssg_need_pass = bool(to_bool(decision[pass_col]).all())
        elif "criteria_pass" in decision.columns:
            ssg_need_pass = bool(to_bool(decision["criteria_pass"]).all())
        else:
            ssg_need_pass = len(decision) > 0

    archetype_ready = ARCHETYPE_SUMMARY_PATH.exists() and len(pd.read_csv(ARCHETYPE_SUMMARY_PATH)) > 0
    mlb_market_partial = bool(
        market_coverage["slot"].isin(["regular_foreign_pitcher", "regular_foreign_hitter_outfield_priority"]).any()
    )
    market_complete = bool((market_coverage["data_status"] == "secured_or_ready").all())
    role_ready = translation_readiness[translation_readiness["role_model_family"].isin(["hitter", "pitcher"])]
    translation_ready = bool(not role_ready.empty and role_ready["training_ready"].all())
    failure_ready = translation_ready

    return pd.DataFrame(
        [
            {
                "gate": "G1",
                "layer": "SSG hidden-need mining",
                "status": "pass" if ssg_need_pass else "not_passed",
                "evidence_output": "outputs/tables/ssg_pitching_message_v0_2_decision_table.csv",
                "decision": "pitcher-first message can define target features",
                "blocking_gap": "" if ssg_need_pass else "message criteria did not all pass",
            },
            {
                "gate": "G2",
                "layer": "KBO success/failure archetype mining",
                "status": "partial_pass" if archetype_ready else "not_passed",
                "evidence_output": "outputs/tables/kbo_foreign_archetype_summary_v0_1.csv",
                "decision": "target archetypes exist, but are target/outcome-side rather than pre-arrival explanatory features",
                "blocking_gap": "needs pre-arrival MLB/MiLB/NPB/CPBL features to explain why archetypes occur",
            },
            {
                "gate": "G3",
                "layer": "Candidate market construction",
                "status": "partial" if mlb_market_partial and not market_complete else ("pass" if market_complete else "not_started"),
                "evidence_output": "outputs/tables/candidate_market_coverage_v0_2.csv",
                "decision": "MLB current-org market exists; Asian quota and free-agent/transaction layers are not complete",
                "blocking_gap": "NPB/CPBL/ABL, MiLB free agents, transactions, salary/options, medical and Korea-willingness checks",
            },
            {
                "gate": "G4",
                "layer": "KBO translation model",
                "status": "blocked_by_sample" if not translation_ready else "pass",
                "evidence_output": "outputs/tables/kbo_translation_readiness_v0_1.csv",
                "decision": "do not train final translation model yet" if not translation_ready else "translation model can be trained",
                "blocking_gap": "current pre-KBO Savant matched sample is below role/class thresholds" if not translation_ready else "",
            },
            {
                "gate": "G5",
                "layer": "Failure-risk model",
                "status": "blocked_by_sample_and_context" if not failure_ready else "pass",
                "evidence_output": "outputs/tables/failure_risk_feature_mart_v0_1.csv",
                "decision": "do not train final failure-risk model yet" if not failure_ready else "failure-risk model can be trained",
                "blocking_gap": "needs broader historical pre-arrival data plus medical/adaptation/full-text article signals"
                if not failure_ready
                else "",
            },
            {
                "gate": "G6",
                "layer": "Final SSG fit and shortlist",
                "status": "locked",
                "evidence_output": "docs/candidate_release_gates_v1.md",
                "decision": "candidate names remain research leads only",
                "blocking_gap": "unlock only after G3-G5 pass",
            },
        ]
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    labels = pd.read_csv(LABEL_PATH)
    pitcher_feature_path = PITCHER_FEATURE_PATH if PITCHER_FEATURE_PATH.exists() else PITCHER_FEATURE_FALLBACK_PATH
    hitter_feature_path = HITTER_FEATURE_PATH if HITTER_FEATURE_PATH.exists() else HITTER_FEATURE_FALLBACK_PATH
    pitcher_features = pd.read_csv(pitcher_feature_path)
    hitter_features = pd.read_csv(hitter_feature_path)

    for column in ["outcome_available", "label_available"]:
        labels[column] = to_bool(labels[column])
    for column in ["success", "strong_success", "failure"]:
        labels[column] = pd.to_numeric(labels[column], errors="coerce").fillna(0).astype(int)

    translation_mart, failure_mart, audit = build_historical_savant_marts(labels, pitcher_features, hitter_features)
    readiness = build_translation_readiness(translation_mart)
    market_coverage = build_candidate_market_coverage()
    gate_status = build_gate_status(readiness, market_coverage)

    audit.to_csv(OUTPUT_DIR / "historical_kbo_savant_name_match_audit_v0_1.csv", index=False)
    translation_mart.to_csv(OUTPUT_DIR / "kbo_translation_feature_mart_v0_1.csv", index=False)
    failure_mart.to_csv(OUTPUT_DIR / "failure_risk_feature_mart_v0_1.csv", index=False)
    readiness.to_csv(OUTPUT_DIR / "kbo_translation_readiness_v0_1.csv", index=False)
    market_coverage.to_csv(OUTPUT_DIR / "candidate_market_coverage_v0_2.csv", index=False)
    gate_status.to_csv(OUTPUT_DIR / "recruitment_gate_status_v1.csv", index=False)

    print("wrote", OUTPUT_DIR / "historical_kbo_savant_name_match_audit_v0_1.csv", audit.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_feature_mart_v0_1.csv", translation_mart.shape)
    print("wrote", OUTPUT_DIR / "failure_risk_feature_mart_v0_1.csv", failure_mart.shape)
    print("wrote", OUTPUT_DIR / "kbo_translation_readiness_v0_1.csv", readiness.shape)
    print("wrote", OUTPUT_DIR / "candidate_market_coverage_v0_2.csv", market_coverage.shape)
    print("wrote", OUTPUT_DIR / "recruitment_gate_status_v1.csv", gate_status.shape)
    print()
    print(readiness.to_string(index=False))
    print()
    print(gate_status.to_string(index=False))


if __name__ == "__main__":
    main()
