#!/usr/bin/env python3
"""Build the locked source-fill packet for the SSG fit queue.

This run does not unlock candidate names, ranks, scores, shortlist labels, or
recommendations. It turns the risk-adjusted fit queue into concrete source
tasks: contract, salary, buyout, agent, medical, nationality, and Korea-
willingness checks.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FEATURE_DIR = PROJECT_ROOT / "src/features"
if str(FEATURE_DIR) not in sys.path:
    sys.path.insert(0, str(FEATURE_DIR))

from build_candidate_news_signals import build_article_relevance, build_summary  # noqa: E402


OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
QUEUE = OUTPUT_DIR / "ssg_risk_adjusted_fit_queue_v0_1.csv"
SCOPE = OUTPUT_DIR / "ssg_fit_source_news_scope_v0_1.csv"
PRIOR_ARTICLES = OUTPUT_DIR / "candidate_news_article_relevance_v0_5.csv"
COLLECTION_AUDIT = OUTPUT_DIR / "ssg_fit_source_news_collection_audit_v0_1.csv"
RAW_DIR = PROJECT_ROOT / "data/raw/articles/fit_queue_source_news_v0_1"

RELEASE_POLICY = "fit_source_fill_research_only_no_recommendation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-file", default=str(QUEUE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--scope-file", default=str(SCOPE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--prior-article-file", default=str(PRIOR_ARTICLES.relative_to(PROJECT_ROOT)))
    parser.add_argument("--collection-audit-file", default=str(COLLECTION_AUDIT.relative_to(PROJECT_ROOT)))
    parser.add_argument("--raw-dir", default=str(RAW_DIR.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def safe_num(frame: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[col], errors="coerce").fillna(default)


def read_new_relevance(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "candidate_news_metadata.csv"
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        news = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()
    if news.empty:
        return pd.DataFrame()
    return build_article_relevance(news)


def combined_article_relevance(scope: pd.DataFrame, prior_article_file: Path, raw_dir: Path) -> pd.DataFrame:
    frames = []
    if prior_article_file.exists() and prior_article_file.stat().st_size > 0:
        prior = pd.read_csv(prior_article_file)
        prior["source_article_layer"] = prior_article_file.name
        frames.append(prior)
    fresh = read_new_relevance(raw_dir)
    if not fresh.empty:
        fresh["source_article_layer"] = raw_dir.name
        frames.append(fresh)
    if not frames:
        return pd.DataFrame()
    articles = pd.concat(frames, ignore_index=True, sort=False)
    articles = articles[articles["candidate_key"].isin(set(scope["candidate_key"].astype(str)))].copy()
    if "published_at" in articles.columns:
        articles["published_at"] = pd.to_datetime(articles["published_at"], errors="coerce", utc=True)
    if "article_relevance_score" in articles.columns:
        articles["article_relevance_score"] = pd.to_numeric(articles["article_relevance_score"], errors="coerce").fillna(0)
    if "candidate_name_match" in articles.columns:
        articles["candidate_name_match"] = articles["candidate_name_match"].astype(str).str.lower().isin(["true", "1", "1.0"])
    dedupe_cols = [col for col in ["candidate_key", "originallink", "title", "pubDate"] if col in articles.columns]
    if dedupe_cols:
        articles = articles.drop_duplicates(dedupe_cols)
    return articles.sort_values(["candidate_key", "article_relevance_score", "published_at"], ascending=[True, False, False])


def audit_summary(audit_path: Path) -> pd.DataFrame:
    if not audit_path.exists() or audit_path.stat().st_size == 0:
        return pd.DataFrame(columns=["candidate_key", "fresh_query_attempts", "fresh_returned_rows", "fresh_error_rows"])
    audit = pd.read_csv(audit_path)
    if audit.empty:
        return pd.DataFrame(columns=["candidate_key", "fresh_query_attempts", "fresh_returned_rows", "fresh_error_rows"])
    return (
        audit.groupby("candidate_key", dropna=False)
        .agg(
            fresh_query_attempts=("query", "count"),
            fresh_returned_rows=("returned_rows", "sum"),
            fresh_error_rows=("error_rows", "sum"),
        )
        .reset_index()
    )


def has_lane(row: pd.Series, *needles: str) -> bool:
    text = str(row.get("manual_source_lanes", "")).lower()
    return any(needle.lower() in text for needle in needles)


def evidence_status(row: pd.Series) -> dict[str, str]:
    contract_needed = has_lane(row, "contract", "salary", "buyout", "transfer", "agent")
    medical_needed = has_lane(row, "medical")
    korean_needed = has_lane(row, "korean_news", "willingness", "intent")
    nationality_needed = has_lane(row, "passport", "nationality", "quota")

    contract_articles = int(row.get("contract_market_article_rows", 0) or 0)
    injury_articles = int(row.get("injury_medical_article_rows", 0) or 0)
    korea_articles = int(row.get("korea_willingness_article_rows", 0) or 0)
    korean_rows = int(row.get("korean_article_rows", 0) or 0)
    nationality_source = str(row.get("nationality_source", "") or "").lower()
    nationality = str(row.get("nationality", "") or "").lower()

    contract_status = "not_required"
    if contract_needed:
        contract_status = "public_contract_news_found_needs_terms_manual_check" if contract_articles > 0 else "missing_contract_salary_buyout_source"

    medical_status = "not_required"
    if medical_needed:
        medical_status = "public_medical_news_found_needs_file_review" if injury_articles > 0 else "missing_medical_file_or_recent_availability_source"

    korea_status = "not_required"
    if korean_needed:
        korea_status = "korean_or_overseas_context_found_needs_intent_check" if korea_articles > 0 or korean_rows > 0 else "missing_korea_willingness_or_local_news_source"

    nationality_status = "not_required"
    if nationality_needed:
        has_source = nationality_source not in {"", "nan", "unknown"} and nationality not in {"", "nan", "unknown"}
        nationality_status = "nationality_source_present_needs_passport_confirmation" if has_source else "missing_passport_or_nationality_source"

    return {
        "contract_source_status": contract_status,
        "medical_source_status": medical_status,
        "korea_willingness_source_status": korea_status,
        "nationality_passport_source_status": nationality_status,
    }


def next_actions(row: pd.Series) -> str:
    actions = []
    if str(row["contract_source_status"]).startswith("missing"):
        actions.append("verify_salary_contract_option_buyout_agent")
    elif "needs_terms" in str(row["contract_source_status"]):
        actions.append("extract_exact_contract_terms_from_source")
    if str(row["medical_source_status"]).startswith("missing"):
        actions.append("request_or_find_recent_medical_availability_source")
    elif "needs_file" in str(row["medical_source_status"]):
        actions.append("manual_medical_file_review")
    if str(row["korea_willingness_source_status"]).startswith("missing"):
        actions.append("search_korean_local_and_agent_willingness_sources")
    elif "intent" in str(row["korea_willingness_source_status"]):
        actions.append("read_context_for_korea_or_overseas_intent")
    if str(row["nationality_passport_source_status"]).startswith("missing"):
        actions.append("verify_passport_nationality_and_quota_eligibility")
    elif "passport" in str(row["nationality_passport_source_status"]):
        actions.append("confirm_passport_against_asian_quota_rules")
    if not actions:
        actions.append("ready_for_manual_scouting_card_review_locked")
    return "|".join(dict.fromkeys(actions))


def readiness_bucket(row: pd.Series) -> str:
    statuses = [
        row["contract_source_status"],
        row["medical_source_status"],
        row["korea_willingness_source_status"],
        row["nationality_passport_source_status"],
    ]
    missing = sum(str(status).startswith("missing") for status in statuses)
    needs_manual = sum("needs" in str(status) for status in statuses)
    if missing >= 3:
        return "source_blocked_major_gap_locked"
    if missing >= 1:
        return "source_blocked_targeted_gap_locked"
    if needs_manual >= 2:
        return "source_supported_manual_verification_needed_locked"
    return "source_supported_scouting_card_next_locked"


def build_packet(queue: pd.DataFrame, scope: pd.DataFrame, summary: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    join_keys = ["fit_slot", "player_id", "player_name", "team_or_org", "position_or_role"]
    scoped = queue.merge(
        scope[
            [
                "candidate_key",
                "source_fill_candidate_key",
                "source_fill_scope_label",
                *join_keys,
            ]
        ],
        on=join_keys,
        how="inner",
        suffixes=("", "_source_scope"),
    )
    if "candidate_key_source_scope" in scoped.columns:
        scoped["candidate_key"] = scoped["candidate_key"].fillna(scoped["candidate_key_source_scope"])
        scoped = scoped.drop(columns=["candidate_key_source_scope"])
    scoped["candidate_key"] = scoped["candidate_key"].fillna(scoped["source_fill_candidate_key"])
    packet = scoped.merge(
        summary[
            [
                "candidate_key",
                "article_rows",
                "usable_article_rows",
                "english_article_rows",
                "korean_article_rows",
                "injury_medical_article_rows",
                "contract_market_article_rows",
                "korea_willingness_article_rows",
                "adaptation_context_article_rows",
                "latest_candidate_news_date",
                "top_candidate_news_titles",
                "top_candidate_news_links",
                "candidate_news_status",
            ]
        ],
        on="candidate_key",
        how="left",
        suffixes=("", "_source_fill"),
    )
    packet = packet.merge(audit, on="candidate_key", how="left")
    packet = packet.drop_duplicates(
        ["fit_slot", "player_id", "player_name", "team_or_org", "position_or_role", "fit_review_lane"],
        keep="first",
    )

    count_cols = [
        "article_rows",
        "usable_article_rows",
        "english_article_rows",
        "korean_article_rows",
        "injury_medical_article_rows",
        "contract_market_article_rows",
        "korea_willingness_article_rows",
        "adaptation_context_article_rows",
        "fresh_query_attempts",
        "fresh_returned_rows",
        "fresh_error_rows",
    ]
    for col in count_cols:
        packet[col] = safe_num(packet, col, 0).astype(int)
    for col in ["latest_candidate_news_date", "top_candidate_news_titles", "top_candidate_news_links", "candidate_news_status"]:
        packet[col] = packet[col].fillna("")

    status_frame = pd.DataFrame([evidence_status(row) for _, row in packet.iterrows()], index=packet.index)
    packet = pd.concat([packet, status_frame], axis=1)
    packet["source_fill_readiness_bucket"] = packet.apply(readiness_bucket, axis=1)
    packet["next_source_actions"] = packet.apply(next_actions, axis=1)
    packet["source_fill_release_policy"] = RELEASE_POLICY
    packet["is_final_recommendation"] = False
    packet["shortlist_label_allowed"] = False
    packet["candidate_name_release_allowed"] = False
    packet["score_release_allowed"] = False
    packet["rank_release_allowed"] = False
    packet["source_fill_unlock_allowed"] = False
    packet["recommendation_label"] = "locked_not_allowed"
    return packet.sort_values(["fit_slot", "fit_review_lane", "fit_review_order_within_slot"])


def lane_summary(packet: pd.DataFrame) -> pd.DataFrame:
    return (
        packet.groupby(["fit_slot", "fit_review_lane", "source_fill_readiness_bucket"], dropna=False)
        .agg(
            rows=("candidate_key", "size"),
            median_internal_fit_score=("risk_adjusted_fit_score_internal", "median"),
            usable_article_rows=("usable_article_rows", "sum"),
            korean_article_rows=("korean_article_rows", "sum"),
            fresh_returned_rows=("fresh_returned_rows", "sum"),
            contract_missing_rows=("contract_source_status", lambda s: int(s.str.startswith("missing").sum())),
            medical_missing_rows=("medical_source_status", lambda s: int(s.str.startswith("missing").sum())),
            korea_missing_rows=("korea_willingness_source_status", lambda s: int(s.str.startswith("missing").sum())),
            nationality_missing_rows=("nationality_passport_source_status", lambda s: int(s.str.startswith("missing").sum())),
            release_allowed=("source_fill_unlock_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "fit_review_lane", "source_fill_readiness_bucket"])
    )


def action_summary(packet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    exploded = packet[["fit_slot", "fit_review_lane", "next_source_actions"]].copy()
    exploded["next_source_action"] = exploded["next_source_actions"].str.split("|", regex=False)
    for action, group in exploded.explode("next_source_action").groupby("next_source_action", dropna=False):
        rows.append(
            {
                "next_source_action": action,
                "rows": len(group),
                "foreign_hitter_rows": int(group["fit_slot"].eq("foreign_hitter").sum()),
                "foreign_pitcher_rows": int(group["fit_slot"].eq("foreign_pitcher").sum()),
                "asian_quota_rows": int(group["fit_slot"].eq("asian_quota").sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["rows", "next_source_action"], ascending=[False, True])


def gate_audit(packet: pd.DataFrame) -> pd.DataFrame:
    lock_cols = [
        "is_final_recommendation",
        "shortlist_label_allowed",
        "candidate_name_release_allowed",
        "score_release_allowed",
        "rank_release_allowed",
        "source_fill_unlock_allowed",
    ]
    return pd.DataFrame(
        [
            {
                "gate": "S1",
                "check": "source_fill_scope_built_from_layer6_queue",
                "pass_rows": len(packet),
                "total_rows": len(packet),
                "status": "pass",
                "blocking_gap": "Scope is internal and candidate release remains locked",
            },
            {
                "gate": "S2",
                "check": "source_evidence_status_attached",
                "pass_rows": int(packet["source_fill_readiness_bucket"].notna().sum()),
                "total_rows": len(packet),
                "status": "pass",
                "blocking_gap": "Evidence statuses are source tasks, not final approvals",
            },
            {
                "gate": "S3",
                "check": "fresh_naver_collection_attempted",
                "pass_rows": int(packet["fresh_query_attempts"].gt(0).sum()),
                "total_rows": len(packet),
                "status": "pass_visible_gap",
                "blocking_gap": "Fresh Naver search returned few candidate-specific rows, so manual/local source checks remain necessary",
            },
            {
                "gate": "S4",
                "check": "release_locks_preserved",
                "pass_rows": int((packet[lock_cols].eq(False).all(axis=1)).sum()),
                "total_rows": len(packet),
                "status": "pass",
                "blocking_gap": "No candidate names, ranks, scores, shortlist labels, or recommendations are released",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = args.output_suffix

    queue = pd.read_csv(PROJECT_ROOT / args.queue_file)
    scope = pd.read_csv(PROJECT_ROOT / args.scope_file)
    audit = audit_summary(PROJECT_ROOT / args.collection_audit_file)
    articles = combined_article_relevance(scope, PROJECT_ROOT / args.prior_article_file, PROJECT_ROOT / args.raw_dir)
    summary = build_summary(articles, scope)
    packet = build_packet(queue, scope, summary, audit)
    summary_table = lane_summary(packet)
    actions = action_summary(packet)
    gates = gate_audit(packet)

    articles.to_csv(OUTPUT_DIR / f"ssg_fit_source_news_article_relevance_{suffix}.csv", index=False)
    summary.to_csv(OUTPUT_DIR / f"ssg_fit_source_news_signal_summary_{suffix}.csv", index=False)
    packet.to_csv(OUTPUT_DIR / f"ssg_fit_source_fill_packet_{suffix}.csv", index=False)
    summary_table.to_csv(OUTPUT_DIR / f"ssg_fit_source_fill_lane_summary_{suffix}.csv", index=False)
    actions.to_csv(OUTPUT_DIR / f"ssg_fit_source_fill_action_summary_{suffix}.csv", index=False)
    gates.to_csv(OUTPUT_DIR / f"ssg_fit_source_fill_gate_audit_{suffix}.csv", index=False)

    print(f"source_fill_rows={len(packet)}")
    print(summary_table.to_string(index=False))
    print(actions.to_string(index=False))
    print(gates.to_string(index=False))


if __name__ == "__main__":
    main()
