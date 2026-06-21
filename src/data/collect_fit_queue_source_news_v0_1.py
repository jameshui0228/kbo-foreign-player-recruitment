#!/usr/bin/env python3
"""Collect news metadata for the locked risk-adjusted SSG fit queue.

Run 034 targets the candidates that can actually move the final SSG fit queue:

- lane 1 source-fill priority rows;
- lane 2 deep-review rows;
- a small top-scored lane 0 medical/blocker sample for verification.

The script writes raw metadata under data/raw/articles, which is gitignored.
Only scope and provider-audit tables are tracked.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "src/data"
if str(DATA_DIR) not in sys.path:
    sys.path.insert(0, str(DATA_DIR))

from collect_candidate_news import (  # noqa: E402
    build_google_queries,
    build_google_ko_queries,
    build_naver_queries,
    clean_text,
    fetch_google_news,
    fetch_naver_news,
    load_env_file,
    player_search_name,
    record_matches_candidate,
    stable_id,
)


QUEUE = PROJECT_ROOT / "outputs/tables/ssg_risk_adjusted_fit_queue_v0_1.csv"
RAW_ARTICLE_DIR = PROJECT_ROOT / "data/raw/articles"
TABLE_DIR = PROJECT_ROOT / "outputs/tables"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue-file", default=str(QUEUE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-name", default="fit_queue_source_news_v0_1")
    parser.add_argument("--table-suffix", default="v0_1")
    parser.add_argument("--scope-label", default="run034_risk_adjusted_fit_source_fill")
    parser.add_argument("--include-lane0-per-foreign-slot", type=int, default=10)
    parser.add_argument("--max-items-per-query", type=int, default=5)
    parser.add_argument("--sleep-sec", type=float, default=0.05)
    parser.add_argument("--timeout-sec", type=float, default=8.0)
    parser.add_argument("--query-mode", choices=["compact", "full"], default="compact")
    parser.add_argument("--providers", nargs="+", default=["google_news_rss", "naver_news"])
    parser.add_argument("--env-file", default=".env.naver")
    return parser.parse_args()


def build_scope(queue: pd.DataFrame, include_lane0_per_foreign_slot: int, scope_label: str) -> pd.DataFrame:
    main = queue[
        queue["fit_review_lane"].isin(
            [
                "lane_1_source_fill_priority_locked",
                "lane_2_deep_review_candidate_locked",
            ]
        )
    ].copy()

    lane0_parts = []
    if include_lane0_per_foreign_slot > 0:
        lane0 = queue[
            queue["fit_review_lane"].eq("lane_0_blocked_or_medical_review_locked")
            & queue["fit_slot"].isin(["foreign_hitter", "foreign_pitcher"])
        ].copy()
        for _, group in lane0.groupby("fit_slot", sort=False):
            lane0_parts.append(group.sort_values("risk_adjusted_fit_score_internal", ascending=False).head(include_lane0_per_foreign_slot))
    if lane0_parts:
        scope = pd.concat([main, *lane0_parts], ignore_index=True)
    else:
        scope = main

    scope = scope.drop_duplicates(["fit_slot", "player_id", "player_name", "team_or_org", "position_or_role"]).copy()
    scope["source_fill_scope_label"] = scope_label
    scope["search_name"] = scope["player_name"].map(player_search_name)
    scope["source_fill_candidate_key"] = scope.apply(
        lambda row: stable_id(row.get("fit_slot"), row.get("player_id"), row.get("player_name"), row.get("team_or_org")),
        axis=1,
    )
    if "candidate_key" not in scope.columns:
        scope["candidate_key"] = scope["source_fill_candidate_key"]
    scope["candidate_key"] = scope["candidate_key"].fillna(scope["source_fill_candidate_key"])

    keep = [
        "candidate_key",
        "source_fill_candidate_key",
        "source_fill_scope_label",
        "fit_slot",
        "fit_review_lane",
        "fit_review_order_within_slot",
        "sensitivity_band",
        "player_id",
        "player_name",
        "search_name",
        "team_or_org",
        "position_or_role",
        "risk_adjusted_fit_score_internal",
        "failure_risk_index",
        "failure_risk_review_tier",
        "manual_source_lanes",
        "fit_review_tags",
        "contract_control_bucket",
        "medical_risk_bucket",
        "current_status_description",
        "nationality",
        "nationality_source",
        "person_url",
        "source_url",
    ]
    return scope[[col for col in keep if col in scope.columns]].sort_values(
        ["fit_slot", "fit_review_lane", "fit_review_order_within_slot"],
        na_position="last",
    )


def compact_naver_queries(candidate: pd.Series, query_mode: str) -> list[str]:
    queries = build_naver_queries(candidate)
    if query_mode != "compact":
        return queries
    name = candidate["search_name"]
    if candidate["fit_slot"] in {"foreign_hitter", "foreign_pitcher"}:
        return [
            f"{name} 부상 계약 방출",
            f"{name} KBO 한국 해외",
        ]
    return [
        f"{name} 계약 이적료 바이아웃",
        f"{name} 부상 KBO 한국",
    ]


def fetch_for_scope(scope: pd.DataFrame, args: argparse.Namespace) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    naver_client_id = os.getenv("NAVER_CLIENT_ID")
    naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")
    provider_audit: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    collected_at = datetime.now().isoformat(timespec="seconds")

    for _, candidate in scope.iterrows():
        candidate_dict = candidate.to_dict()
        providers = []
        if "google_news_rss" in args.providers:
            providers.append("google_news_rss")
        if "google_news_rss_ko" in args.providers:
            providers.append("google_news_rss_ko")
        if "naver_news" in args.providers:
            if naver_client_id and naver_client_secret:
                providers.append("naver_news")
            else:
                provider_audit.append(
                    {
                        "provider": "naver_news",
                        "status": "skipped_missing_env",
                        "candidate_key": candidate["candidate_key"],
                        "candidate_name": candidate["player_name"],
                        "message": "NAVER_CLIENT_ID and NAVER_CLIENT_SECRET are not loaded",
                    }
                )

        for provider in providers:
            if provider == "google_news_rss":
                queries = build_google_queries(candidate, args.query_mode)
            elif provider == "google_news_rss_ko":
                queries = build_google_ko_queries(candidate, args.query_mode)
            else:
                queries = compact_naver_queries(candidate, args.query_mode)
            for query in queries:
                if provider == "google_news_rss":
                    fetched = fetch_google_news(query, args.max_items_per_query, args.timeout_sec)
                elif provider == "google_news_rss_ko":
                    fetched = fetch_google_news(
                        query,
                        args.max_items_per_query,
                        args.timeout_sec,
                        provider="google_news_rss_ko",
                        query_language="ko",
                        hl="ko",
                        gl="KR",
                        ceid="KR:ko",
                    )
                else:
                    fetched = fetch_naver_news(
                        query,
                        args.max_items_per_query,
                        naver_client_id or "",
                        naver_client_secret or "",
                        args.timeout_sec,
                    )
                provider_audit.append(
                    {
                        "provider": provider,
                        "status": "attempted",
                        "candidate_key": candidate["candidate_key"],
                        "candidate_name": candidate["player_name"],
                        "fit_slot": candidate["fit_slot"],
                        "fit_review_lane": candidate["fit_review_lane"],
                        "query": query,
                        "returned_rows": len([item for item in fetched if "provider_error" not in item]),
                        "error_rows": len([item for item in fetched if "provider_error" in item]),
                    }
                )
                for item in fetched:
                    if "provider_error" in item:
                        continue
                    item_id = stable_id(item.get("provider"), item.get("originallink"), item.get("title"), item.get("pubDate"))
                    if item_id in seen:
                        continue
                    seen.add(item_id)
                    records.append(
                        {
                            **candidate_dict,
                            **item,
                            "article_id": item_id,
                            "collected_at": collected_at,
                            "candidate_name_match": record_matches_candidate(item, clean_text(candidate["search_name"])),
                        }
                    )
                time.sleep(args.sleep_sec)
    return records, provider_audit


def main() -> None:
    args = parse_args()
    if args.env_file:
        load_env_file(PROJECT_ROOT / args.env_file)

    queue = pd.read_csv(PROJECT_ROOT / args.queue_file)
    scope = build_scope(queue, args.include_lane0_per_foreign_slot, args.scope_label)

    output_dir = RAW_ARTICLE_DIR / args.output_name
    output_dir.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    scope_path = TABLE_DIR / f"ssg_fit_source_news_scope_{args.table_suffix}.csv"
    audit_path = TABLE_DIR / f"ssg_fit_source_news_collection_audit_{args.table_suffix}.csv"
    scope.to_csv(scope_path, index=False)

    records, provider_audit = fetch_for_scope(scope, args)

    metadata_path = output_dir / "candidate_news_metadata.csv"
    raw_path = output_dir / "candidate_news_raw.jsonl"
    with raw_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    if records:
        pd.DataFrame(records).to_csv(metadata_path, index=False)
    else:
        pd.DataFrame().to_csv(metadata_path, index=False)
    pd.DataFrame(provider_audit).to_csv(audit_path, index=False)

    manifest = {
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "scope_rows": len(scope),
        "article_rows": len(records),
        "candidate_name_match_rows": int(sum(bool(record.get("candidate_name_match")) for record in records)),
        "providers_requested": args.providers,
        "query_mode": args.query_mode,
        "include_lane0_per_foreign_slot": args.include_lane0_per_foreign_slot,
        "naver_status": "attempted" if os.getenv("NAVER_CLIENT_ID") and os.getenv("NAVER_CLIENT_SECRET") else "skipped_missing_env",
        "metadata_path": str(metadata_path.relative_to(PROJECT_ROOT)),
        "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
        "scope_path": str(scope_path.relative_to(PROJECT_ROOT)),
        "audit_path": str(audit_path.relative_to(PROJECT_ROOT)),
    }
    manifest_path = output_dir / "candidate_news_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
