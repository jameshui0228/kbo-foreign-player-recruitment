#!/usr/bin/env python3
"""Attach market-realism gates to the locked SSG fit-preparation mart.

Run 024 is not a candidate-ranking run. It adds the practical checks that a
front office would need before believing any model output:

- current MLB roster control and transaction status;
- current or recent injury/rehab signals;
- Asian-quota nationality, club-control, salary/buyout gaps;
- explicit manual checks for contract, medical, agent/willingness, and news.

All row-level release locks stay false.
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

FIT_PREP = OUTPUT_DIR / "ssg_fit_preparation_mart_v0_1.csv"
MLB_TRANSACTIONS = OUTPUT_DIR / "mlb_transactions_latest.csv"
MLB_ROSTER = OUTPUT_DIR / "mlb_roster_status_latest.csv"
ASIAN_MARKET = OUTPUT_DIR / "asian_quota_market_status_v1.csv"

DEFAULT_OUTPUT_SUFFIX = "v0_1"


def output_path(stem: str, suffix: str) -> Path:
    return OUTPUT_DIR / f"{stem}_{suffix}.csv"


LAYER_OUT = output_path("ssg_market_realism_layer", DEFAULT_OUTPUT_SUFFIX)
SUMMARY_OUT = output_path("ssg_market_realism_slot_summary", DEFAULT_OUTPUT_SUFFIX)
WORKLIST_OUT = output_path("ssg_market_realism_manual_worklist", DEFAULT_OUTPUT_SUFFIX)
GATE_AUDIT_OUT = output_path("ssg_market_realism_gate_audit", DEFAULT_OUTPUT_SUFFIX)

RUN_DATE = date(2026, 6, 21)
RELEASE_POLICY = "market_realism_research_only_no_recommendation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-date",
        default=RUN_DATE.isoformat(),
        help="Evaluation date used for transaction recency, in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--output-suffix",
        default=DEFAULT_OUTPUT_SUFFIX,
        help="Suffix for output tables, for example v0_2.",
    )
    return parser.parse_args()


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def clip_score(values: pd.Series | np.ndarray) -> pd.Series:
    return pd.Series(values).astype(float).clip(0, 100).round(3)


def clean_player_id(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def make_flags(flags: list[str]) -> str:
    clean = [flag for flag in flags if flag]
    return "|".join(clean) if clean else "no_immediate_market_flag"


def transaction_summary() -> pd.DataFrame:
    tx = pd.read_csv(MLB_TRANSACTIONS)
    tx["player_id"] = clean_player_id(tx["player_id"])
    tx["date_dt"] = pd.to_datetime(tx["date"], errors="coerce")
    tx["days_since_transaction"] = (pd.Timestamp(RUN_DATE) - tx["date_dt"]).dt.days
    flag_cols = [
        "signed_free_agent_flag",
        "minor_league_contract_flag",
        "released_flag",
        "declared_free_agency_flag",
        "dfa_flag",
        "outrighted_flag",
        "optioned_flag",
        "assigned_flag",
        "selected_contract_flag",
        "injured_list_flag",
        "rehab_flag",
        "traded_flag",
        "roster_status_change_flag",
    ]
    for col in flag_cols:
        tx[col] = to_bool(tx[col])
        tx[f"recent_30d_{col}"] = tx[col] & tx["days_since_transaction"].between(0, 30, inclusive="both")

    latest = (
        tx.sort_values(["player_id", "date_dt", "transaction_id"], na_position="first")
        .groupby("player_id", as_index=False)
        .tail(1)
    )
    agg_spec = {
        "transaction_id": "count",
        "date_dt": "max",
        "days_since_transaction": "min",
    }
    for col in flag_cols:
        agg_spec[col] = "sum"
        agg_spec[f"recent_30d_{col}"] = "sum"
    summary = tx.groupby("player_id", dropna=False).agg(agg_spec).reset_index()
    summary = summary.rename(
        columns={
            "transaction_id": "mlb_transaction_count",
            "date_dt": "last_mlb_transaction_date",
            "days_since_transaction": "days_since_last_mlb_transaction",
        }
    )
    latest_cols = [
        "player_id",
        "type_code",
        "type_desc",
        "description",
        "from_team_name",
        "to_team_name",
        "source_url",
    ]
    latest = latest[latest_cols].rename(
        columns={
            "type_code": "latest_transaction_type_code",
            "type_desc": "latest_transaction_type_desc",
            "description": "latest_transaction_description",
            "from_team_name": "latest_transaction_from_team",
            "to_team_name": "latest_transaction_to_team",
            "source_url": "latest_transaction_source_url",
        }
    )
    out = summary.merge(latest, on="player_id", how="left", validate="one_to_one")
    out["last_mlb_transaction_date"] = out["last_mlb_transaction_date"].dt.date.astype(str)
    return out


def roster_summary() -> pd.DataFrame:
    roster = pd.read_csv(MLB_ROSTER)
    roster["player_id"] = clean_player_id(roster["player_id"])
    for col in ["is_40man", "is_active", "is_full_roster"]:
        roster[col] = to_bool(roster[col])
    roster["roster_medical_text_flag"] = (
        roster["status_description"].fillna("").str.contains("injur|60-day|10-day", case=False, regex=True)
        | roster["roster_note"].fillna("").str.contains("injur|surgery|rehab|strain|sprain|fracture|illness", case=False, regex=True)
    )

    def first_non_null(series: pd.Series) -> object:
        values = series.dropna()
        return values.iloc[0] if len(values) else np.nan

    out = (
        roster.sort_values(["player_id", "is_active", "is_40man"], ascending=[True, False, False])
        .groupby("player_id", dropna=False)
        .agg(
            roster_evaluation_date=("evaluation_date", first_non_null),
            roster_team_name=("team_name", first_non_null),
            roster_team_abbreviation=("team_abbreviation", first_non_null),
            current_status_code=("status_code", first_non_null),
            current_status_description=("status_description", first_non_null),
            current_roster_note=("roster_note", first_non_null),
            current_primary_position=("primary_position", first_non_null),
            current_is_40man=("is_40man", "max"),
            current_is_active=("is_active", "max"),
            current_is_full_roster=("is_full_roster", "max"),
            current_roster_medical_text_flag=("roster_medical_text_flag", "max"),
        )
        .reset_index()
    )
    return out


def asian_context() -> pd.DataFrame:
    asian = pd.read_csv(ASIAN_MARKET)
    keep = [
        "source_league",
        "team_name",
        "player_name",
        "normalized_player_name",
        "nationality",
        "nationality_source",
        "person_url",
        "source_url",
        "source_confidence",
        "asian_quota_nationality_gate",
        "contract_status_gate",
        "new_signing_cost_gate",
        "availability_bucket",
    ]
    out = asian[[col for col in keep if col in asian.columns]].copy()
    return out.drop_duplicates(["source_league", "team_name", "player_name"])


def attach_sources(mart: pd.DataFrame) -> pd.DataFrame:
    out = mart.copy()
    out["player_id_int"] = clean_player_id(out["player_id"])

    tx = transaction_summary()
    roster = roster_summary()
    out = out.merge(tx, left_on="player_id_int", right_on="player_id", how="left", suffixes=("", "_tx"))
    out = out.merge(roster, left_on="player_id_int", right_on="player_id", how="left", suffixes=("", "_roster"))

    asian = asian_context()
    out = out.merge(
        asian,
        left_on=["source_pool", "team_or_org", "player_name"],
        right_on=["source_league", "team_name", "player_name"],
        how="left",
        validate="many_to_one",
    )
    return out


def score_mlb(row: pd.Series) -> tuple[float, str, str, str]:
    if row["fit_slot"] not in {"foreign_hitter", "foreign_pitcher"}:
        return np.nan, "", "", ""

    flags: list[str] = []
    score = 45.0
    current_40 = bool(row.get("current_is_40man", False))
    current_active = bool(row.get("current_is_active", False))
    full_roster = bool(row.get("current_is_full_roster", False))
    recent_release = row.get("recent_30d_released_flag", 0) > 0 or row.get("recent_30d_declared_free_agency_flag", 0) > 0
    recent_dfa = row.get("recent_30d_dfa_flag", 0) > 0
    recent_outright = row.get("recent_30d_outrighted_flag", 0) > 0
    recent_option = row.get("recent_30d_optioned_flag", 0) > 0
    selected_contract = row.get("recent_30d_selected_contract_flag", 0) > 0
    recent_il = row.get("recent_30d_injured_list_flag", 0) > 0 or row.get("recent_30d_rehab_flag", 0) > 0
    roster_med = bool(row.get("current_roster_medical_text_flag", False))

    if recent_release:
        score += 35
        flags.append("recent_release_or_free_agency")
    if recent_dfa:
        score += 30
        flags.append("recent_designated_for_assignment")
    if recent_outright:
        score += 18
        flags.append("recent_outright_assignment")
    if recent_option:
        score += 8
        flags.append("recent_optioned_upper_minors")
    if full_roster and not current_40:
        score += 15
        flags.append("non40man_full_roster")
    if current_40:
        score -= 25
        flags.append("current_40man_contract_control")
    if current_active:
        score -= 25
        flags.append("current_active_mlb_blocker")
    if selected_contract:
        score -= 20
        flags.append("recent_selected_contract_blocker")
    if row.get("recent_30d_traded_flag", 0) > 0:
        score -= 10
        flags.append("recent_trade_context_change")
    if recent_il or roster_med:
        score -= 30
        flags.append("current_or_recent_medical_signal")

    if recent_il or roster_med:
        medical_bucket = "medical_hold_current_or_recent"
    elif row.get("injured_list_flag", 0) > 0 or row.get("rehab_flag", 0) > 0:
        medical_bucket = "medical_history_watch"
    else:
        medical_bucket = "no_public_medical_signal_from_roster_transactions"

    if medical_bucket == "medical_hold_current_or_recent":
        status = "medical_hold_before_scouting"
    elif score >= 75:
        status = "manual_contact_priority_locked"
    elif score >= 55:
        status = "contract_verification_needed"
    elif current_active or current_40 or selected_contract:
        status = "contract_blocker_watch"
    else:
        status = "low_access_or_unknown_market_status"

    if recent_release:
        contract_bucket = "recent_free_agent_or_released_high_access"
    elif recent_dfa:
        contract_bucket = "recent_dfa_high_access"
    elif recent_outright or (full_roster and not current_40):
        contract_bucket = "non40man_or_outrighted_medium_access"
    elif current_active:
        contract_bucket = "active_mlb_contract_blocker"
    elif current_40:
        contract_bucket = "40man_nonactive_contract_blocker"
    else:
        contract_bucket = "mlb_market_access_unknown_or_low"

    flags.append("needs_agent_contract_salary_korea_willingness_check")
    if row["fit_slot"] == "foreign_pitcher":
        flags.append("needs_pitcher_medical_file_review")
    else:
        flags.append("needs_hitter_defense_baserunning_role_review")
    return float(np.clip(score, 0, 100)), contract_bucket, medical_bucket, make_flags(flags)


def score_asian(row: pd.Series) -> tuple[float, str, str, str]:
    if row["fit_slot"] != "asian_quota":
        return np.nan, "", "", ""

    flags: list[str] = []
    nationality_gate = normalize_text(row.get("asian_quota_nationality_gate"))
    contract_gate = normalize_text(row.get("contract_status_gate"))
    access_bucket = normalize_text(row.get("availability_bucket"))
    source_league = normalize_text(row.get("source_pool"))
    score = 20.0

    if nationality_gate == "pass":
        score += 35
        flags.append("asian_quota_nationality_pass")
    elif nationality_gate == "unknown":
        score += 10
        flags.append("nationality_unknown_manual_verification")
    elif nationality_gate == "fail":
        score = 0.0
        flags.append("not_asian_quota_eligible")

    if "unknown" in contract_gate:
        score -= 10
        flags.append("contract_salary_buyout_unknown")
    if "low_access" in access_bucket or "club_control" in contract_gate:
        score -= 15
        flags.append("active_roster_club_control_or_buyout_risk")
    if source_league == "CPBL":
        flags.append("cpbl_salary_buyout_source_needed")
    elif source_league == "NPB":
        flags.append("npb_salary_buyout_source_needed")
    if row.get("source_confidence", np.nan) and pd.notna(row.get("source_confidence")):
        score += min(float(row.get("source_confidence")), 5.0)

    if nationality_gate == "fail":
        status = "not_asian_quota_eligible_regular_foreign_only"
        contract_bucket = "asian_quota_nationality_fail"
    elif nationality_gate == "unknown":
        status = "nationality_verification_needed"
        contract_bucket = "nationality_unknown_contract_unusable"
    else:
        status = "buyout_salary_agent_check_needed"
        contract_bucket = "eligible_but_contract_buyout_unknown"

    medical_bucket = "candidate_medical_news_not_collected"
    flags.append("needs_agent_willingness_and_role_acceptance_check")
    flags.append("needs_current_medical_news_search")
    return float(np.clip(score, 0, 100)), contract_bucket, medical_bucket, make_flags(flags)


def build_layer() -> pd.DataFrame:
    mart = pd.read_csv(FIT_PREP)
    out = attach_sources(mart)

    scores = []
    contract_buckets = []
    medical_buckets = []
    flags = []
    for row in out.to_dict("records"):
        row_series = pd.Series(row)
        if row["fit_slot"] in {"foreign_hitter", "foreign_pitcher"}:
            score, contract_bucket, medical_bucket, manual_flags = score_mlb(row_series)
        else:
            score, contract_bucket, medical_bucket, manual_flags = score_asian(row_series)
        scores.append(score)
        contract_buckets.append(contract_bucket)
        medical_buckets.append(medical_bucket)
        flags.append(manual_flags)

    out["market_realism_score"] = clip_score(scores)
    out["contract_control_bucket"] = contract_buckets
    out["medical_risk_bucket"] = medical_buckets
    out["run024_manual_check_flags"] = flags

    out["market_realism_status"] = np.select(
        [
            out["medical_risk_bucket"].eq("medical_hold_current_or_recent"),
            out["fit_slot"].eq("asian_quota") & out["contract_control_bucket"].eq("asian_quota_nationality_fail"),
            out["fit_slot"].eq("asian_quota") & out["contract_control_bucket"].eq("nationality_unknown_contract_unusable"),
            out["fit_slot"].eq("asian_quota"),
            out["market_realism_score"].ge(75),
            out["market_realism_score"].ge(55),
            out["contract_control_bucket"].str.contains("blocker", na=False),
        ],
        [
            "medical_hold_before_scouting",
            "not_asian_quota_eligible_regular_foreign_only",
            "nationality_verification_needed",
            "buyout_salary_agent_check_needed",
            "manual_contact_priority_locked",
            "contract_verification_needed",
            "contract_blocker_watch",
        ],
        default="low_access_or_unknown_market_status",
    )

    out["kbo_rule_cost_bucket"] = np.select(
        [
            out["fit_slot"].eq("asian_quota"),
            out["fit_slot"].isin(["foreign_hitter", "foreign_pitcher"]),
        ],
        [
            "asian_quota_200k_total_cost_cap_check_required",
            "regular_or_replacement_foreign_cost_check_required",
        ],
        default="cost_rule_check_required",
    )
    out["news_context_status"] = np.select(
        [
            out["fit_slot"].isin(["foreign_hitter", "foreign_pitcher"]),
            out["fit_slot"].eq("asian_quota"),
        ],
        [
            "candidate_specific_news_not_refreshed_naver_env_missing",
            "candidate_specific_asian_market_news_not_collected",
        ],
        default="news_context_not_collected",
    )
    out["market_realism_source_files"] = np.select(
        [
            out["fit_slot"].isin(["foreign_hitter", "foreign_pitcher"]),
            out["fit_slot"].eq("asian_quota"),
        ],
        [
            f"{MLB_TRANSACTIONS.name};{MLB_ROSTER.name};{FIT_PREP.name}",
            f"{ASIAN_MARKET.name};{FIT_PREP.name}",
        ],
        default=FIT_PREP.name,
    )
    out["market_realism_run_date"] = RUN_DATE.isoformat()
    out["candidate_release_policy"] = RELEASE_POLICY
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False
    out["score_release_allowed"] = False
    out["recommendation_label"] = "locked_not_allowed"
    out["market_realism_rank_within_slot"] = (
        out.groupby("fit_slot")["market_realism_score"].rank(method="first", ascending=False).astype(int)
    )
    out["market_realism_fit_blend_for_triage_only"] = (
        pd.to_numeric(out["market_realism_score"], errors="coerce") * 0.6
        + pd.to_numeric(out["fit_preparation_index"], errors="coerce") * 0.4
    ).round(3)
    out["blend_release_allowed"] = False
    return out.sort_values(["fit_slot", "market_realism_rank_within_slot"]).reset_index(drop=True)


def build_summary(layer: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for slot, group in layer.groupby("fit_slot", dropna=False):
        rows.append(
            {
                "fit_slot": slot,
                "rows": len(group),
                "median_market_realism_score": float(group["market_realism_score"].median()),
                "p75_market_realism_score": float(group["market_realism_score"].quantile(0.75)),
                "manual_contact_or_buyout_priority_rows": int(
                    group["market_realism_status"]
                    .isin(["manual_contact_priority_locked", "buyout_salary_agent_check_needed"])
                    .sum()
                ),
                "contract_blocker_or_low_access_rows": int(
                    group["market_realism_status"]
                    .isin(["contract_blocker_watch", "low_access_or_unknown_market_status"])
                    .sum()
                ),
                "medical_hold_rows": int(group["market_realism_status"].eq("medical_hold_before_scouting").sum()),
                "nationality_or_asian_eligibility_gap_rows": int(
                    group["market_realism_status"]
                    .isin(["nationality_verification_needed", "not_asian_quota_eligible_regular_foreign_only"])
                    .sum()
                ),
                "candidate_release_policy": RELEASE_POLICY,
            }
        )
    return pd.DataFrame(rows).sort_values("fit_slot")


def build_worklist(layer: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "fit_slot",
        "market_realism_rank_within_slot",
        "research_triage_order_within_slot",
        "player_id",
        "player_name",
        "team_or_org",
        "position_or_role",
        "fit_preparation_index",
        "market_realism_score",
        "market_realism_fit_blend_for_triage_only",
        "market_realism_status",
        "contract_control_bucket",
        "medical_risk_bucket",
        "kbo_rule_cost_bucket",
        "run024_manual_check_flags",
        "current_status_description",
        "current_roster_note",
        "last_mlb_transaction_date",
        "days_since_last_mlb_transaction",
        "latest_transaction_type_desc",
        "latest_transaction_description",
        "nationality",
        "nationality_source",
        "asian_quota_nationality_gate",
        "contract_status_gate",
        "new_signing_cost_gate",
        "person_url",
        "source_url",
        "news_context_status",
        "candidate_release_policy",
        "is_final_recommendation",
        "shortlist_label_allowed",
        "candidate_name_release_allowed",
        "score_release_allowed",
        "recommendation_label",
    ]
    existing = [col for col in keep if col in layer.columns]
    return layer[existing].sort_values(
        ["fit_slot", "market_realism_fit_blend_for_triage_only", "market_realism_score"],
        ascending=[True, False, False],
    )


def build_gate_audit(layer: pd.DataFrame) -> pd.DataFrame:
    mlb = layer[layer["fit_slot"].isin(["foreign_hitter", "foreign_pitcher"])]
    asian = layer[layer["fit_slot"].eq("asian_quota")]
    checks = [
        {
            "gate": "M1",
            "check": "updated_mlb_official_sources_joined",
            "pass_rows": int(mlb["roster_evaluation_date"].notna().sum()),
            "total_rows": len(mlb),
            "status": "partial_pass",
            "blocking_gap": "Official roster and transaction data are joined for MLB candidates, but salary and opt-out details are not available in this public layer",
        },
        {
            "gate": "M2",
            "check": "medical_signals_visible",
            "pass_rows": int(layer["medical_risk_bucket"].notna().sum()),
            "total_rows": len(layer),
            "status": "pass_visible_risk_layer",
            "blocking_gap": "Medical notes are roster/transaction proxies only and still require manual injury-history review",
        },
        {
            "gate": "M3",
            "check": "asian_contract_gap_visible",
            "pass_rows": int(asian["run024_manual_check_flags"].str.contains("contract_salary_buyout_unknown", na=False).sum()),
            "total_rows": len(asian),
            "status": "pass_visible_gap",
            "blocking_gap": "Asian-quota salary, transfer fee, buyout, and agent willingness remain manual checks",
        },
        {
            "gate": "M4",
            "check": "candidate_news_refresh_gap_visible",
            "pass_rows": int(layer["news_context_status"].notna().sum()),
            "total_rows": len(layer),
            "status": "pass_visible_gap",
            "blocking_gap": "Candidate-specific article/Naver signals are maintained in candidate_news_* outputs and are not attached inside this market-realism table",
        },
        {
            "gate": "M5",
            "check": "release_locks_preserved",
            "pass_rows": int(
                (
                    layer["is_final_recommendation"].eq(False)
                    & layer["shortlist_label_allowed"].eq(False)
                    & layer["candidate_name_release_allowed"].eq(False)
                    & layer["score_release_allowed"].eq(False)
                    & layer["blend_release_allowed"].eq(False)
                ).sum()
            ),
            "total_rows": len(layer),
            "status": "pass",
            "blocking_gap": "Market-realism layer is research-only; no recommendation labels allowed",
        },
    ]
    return pd.DataFrame(checks)


def main() -> None:
    args = parse_args()
    run_date = date.fromisoformat(args.run_date)
    suffix = args.output_suffix
    if not re.fullmatch(r"[A-Za-z0-9_]+", suffix):
        raise ValueError("--output-suffix must contain only letters, numbers, and underscores")

    global RUN_DATE, LAYER_OUT, SUMMARY_OUT, WORKLIST_OUT, GATE_AUDIT_OUT
    RUN_DATE = run_date
    LAYER_OUT = output_path("ssg_market_realism_layer", suffix)
    SUMMARY_OUT = output_path("ssg_market_realism_slot_summary", suffix)
    WORKLIST_OUT = output_path("ssg_market_realism_manual_worklist", suffix)
    GATE_AUDIT_OUT = output_path("ssg_market_realism_gate_audit", suffix)

    layer = build_layer()
    layer.to_csv(LAYER_OUT, index=False)
    build_summary(layer).to_csv(SUMMARY_OUT, index=False)
    build_worklist(layer).to_csv(WORKLIST_OUT, index=False)
    build_gate_audit(layer).to_csv(GATE_AUDIT_OUT, index=False)
    print(f"wrote {LAYER_OUT.relative_to(PROJECT_ROOT)} rows={len(layer)}")
    print(f"wrote {SUMMARY_OUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {WORKLIST_OUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {GATE_AUDIT_OUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
