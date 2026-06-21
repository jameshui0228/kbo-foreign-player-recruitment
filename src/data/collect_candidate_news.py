#!/usr/bin/env python3
"""Collect candidate-specific news metadata for market-realism review.

The first pass intentionally uses a small priority scope from Run 024:

- MLB hitter/pitcher rows with `manual_contact_priority_locked`;
- a limited number of Asian-quota rows that pass nationality but still need
  buyout/salary/agent checks.

Google News RSS is used for English-language metadata without a Google API key.
Naver Search News is supported only when NAVER_CLIENT_ID and
NAVER_CLIENT_SECRET are loaded in the shell environment. Credentials are never
written to disk.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import ssl
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd
import certifi


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKLIST = PROJECT_ROOT / "outputs/tables/ssg_market_realism_manual_worklist_v0_1.csv"
OUTPUT_DIR = PROJECT_ROOT / "data/raw/articles/candidate_news_pilot_v0_1"
TABLE_DIR = PROJECT_ROOT / "outputs/tables"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def clean_text(value: object) -> str:
    if value is None:
        return ""
    value = re.sub(r"<[^>]+>", " ", str(value))
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def stable_id(*parts: object) -> str:
    text = "||".join(clean_text(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def player_search_name(name: object) -> str:
    text = clean_text(name)
    if "," in text:
        pieces = [piece.strip() for piece in text.split(",", 1)]
        if len(pieces) == 2 and all(pieces):
            return f"{pieces[1]} {pieces[0]}"
    return text


def candidate_scope(worklist: pd.DataFrame, asian_limit: int, mlb_limit_per_slot: int) -> pd.DataFrame:
    priority = worklist[
        (
            worklist["fit_slot"].isin(["foreign_hitter", "foreign_pitcher"])
            & worklist["market_realism_status"].eq("manual_contact_priority_locked")
        )
        | (
            worklist["fit_slot"].eq("asian_quota")
            & worklist["market_realism_status"].eq("buyout_salary_agent_check_needed")
        )
    ].copy()
    priority = priority.sort_values(
        ["fit_slot", "market_realism_fit_blend_for_triage_only", "market_realism_score"],
        ascending=[True, False, False],
    )
    parts = []
    for slot, group in priority.groupby("fit_slot", sort=False):
        if slot == "asian_quota" and asian_limit >= 0:
            parts.append(group.head(asian_limit))
        elif slot in {"foreign_hitter", "foreign_pitcher"} and mlb_limit_per_slot >= 0:
            parts.append(group.head(mlb_limit_per_slot))
        else:
            parts.append(group)
    priority = pd.concat(parts, ignore_index=True) if parts else priority
    priority["candidate_news_scope"] = "run024_market_realism_priority_pilot"
    priority["search_name"] = priority["player_name"].map(player_search_name)
    priority["candidate_key"] = priority.apply(
        lambda row: stable_id(row.get("fit_slot"), row.get("player_id"), row.get("player_name"), row.get("team_or_org")),
        axis=1,
    )
    keep = [
        "candidate_key",
        "candidate_news_scope",
        "fit_slot",
        "player_id",
        "player_name",
        "search_name",
        "team_or_org",
        "position_or_role",
        "market_realism_status",
        "contract_control_bucket",
        "medical_risk_bucket",
        "market_realism_fit_blend_for_triage_only",
        "person_url",
        "source_url",
    ]
    return priority[[col for col in keep if col in priority.columns]]


def build_google_queries(row: pd.Series, query_mode: str) -> list[str]:
    name = row["search_name"]
    quoted = f'"{name}"'
    if row["fit_slot"] in {"foreign_hitter", "foreign_pitcher"}:
        if query_mode == "compact":
            return [
                f'{quoted} baseball',
                f'{quoted} injury OR contract OR DFA OR released OR KBO',
            ]
        return [
            f'{quoted} baseball',
            f'{quoted} injury OR injured OR rehab',
            f'{quoted} DFA OR designated OR released OR waivers OR outrighted',
            f'{quoted} contract OR free agent OR optioned',
            f'{quoted} KBO OR Korea baseball OR overseas baseball',
        ]
    team = clean_text(row.get("team_or_org"))
    team_piece = f' "{team}"' if team else ""
    if query_mode == "compact":
        return [
            f'{quoted}{team_piece} baseball',
            f'{quoted} NPB OR CPBL OR injury OR contract OR KBO',
        ]
    return [
        f'{quoted}{team_piece} baseball',
        f'{quoted} NPB OR CPBL',
        f'{quoted} injury OR injured OR rehab',
        f'{quoted} contract OR posting OR transfer OR buyout',
        f'{quoted} KBO OR Korea baseball OR overseas baseball',
    ]


def build_naver_queries(row: pd.Series) -> list[str]:
    name = row["search_name"]
    if row["fit_slot"] in {"foreign_hitter", "foreign_pitcher"}:
        return [
            f"{name} 야구",
            f"{name} 부상 재활",
            f"{name} DFA 방출 웨이버",
            f"{name} 계약 자유계약",
            f"{name} KBO 한국",
        ]
    return [
        f"{name} 야구",
        f"{name} 부상 재활",
        f"{name} 계약 이적료 바이아웃",
        f"{name} NPB CPBL",
        f"{name} KBO 한국",
    ]


def fetch_google_news(query: str, max_items: int, timeout_sec: float) -> list[dict[str, object]]:
    params = urllib.parse.urlencode({"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    url = f"https://news.google.com/rss/search?{params}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=timeout_sec, context=SSL_CONTEXT) as response:
            payload = response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        return [{"provider_error": clean_text(exc), "query": query, "provider_url": url}]

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return [{"provider_error": f"xml_parse_error: {clean_text(exc)}", "query": query, "provider_url": url}]

    rows = []
    channel = root.find("channel")
    if channel is None:
        return rows
    for item in channel.findall("item")[:max_items]:
        source = item.find("source")
        rows.append(
            {
                "provider": "google_news_rss",
                "query": query,
                "query_language": "en",
                "title": clean_text(item.findtext("title")),
                "description": clean_text(item.findtext("description")),
                "pubDate": clean_text(item.findtext("pubDate")),
                "originallink": clean_text(item.findtext("link")),
                "link": clean_text(item.findtext("link")),
                "source_name": clean_text(source.text if source is not None else ""),
                "provider_url": url,
            }
        )
    return rows


def fetch_naver_news(query: str, max_items: int, client_id: str, client_secret: str, timeout_sec: float) -> list[dict[str, object]]:
    params = urllib.parse.urlencode({"query": query, "display": min(max_items, 100), "start": 1, "sort": "date"})
    url = f"https://openapi.naver.com/v1/search/news.json?{params}"
    request = Request(
        url,
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        },
    )
    try:
        with urlopen(request, timeout=timeout_sec, context=SSL_CONTEXT) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return [{"provider_error": clean_text(exc), "query": query, "provider_url": url}]

    rows = []
    for item in payload.get("items", [])[:max_items]:
        rows.append(
            {
                "provider": "naver_news",
                "query": query,
                "query_language": "ko",
                "title": clean_text(item.get("title")),
                "description": clean_text(item.get("description")),
                "pubDate": clean_text(item.get("pubDate")),
                "originallink": clean_text(item.get("originallink")),
                "link": clean_text(item.get("link")),
                "source_name": "",
                "provider_url": "https://openapi.naver.com/v1/search/news.json",
            }
        )
    return rows


def record_matches_candidate(record: dict[str, object], search_name: str) -> bool:
    text = f"{record.get('title', '')} {record.get('description', '')}".lower()
    tokens = [token.lower() for token in re.findall(r"[A-Za-z가-힣]+", search_name) if len(token) >= 2]
    if not tokens:
        return False
    if len(tokens) == 1:
        return tokens[0] in text
    return all(token in text for token in tokens[:2])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asian-limit", type=int, default=30)
    parser.add_argument("--mlb-limit-per-slot", type=int, default=-1)
    parser.add_argument("--max-items-per-query", type=int, default=10)
    parser.add_argument("--sleep-sec", type=float, default=0.2)
    parser.add_argument("--timeout-sec", type=float, default=8.0)
    parser.add_argument("--query-mode", choices=["compact", "full"], default="compact")
    parser.add_argument("--providers", nargs="+", default=["google_news_rss", "naver_news"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    worklist = pd.read_csv(WORKLIST)
    scope = candidate_scope(worklist, args.asian_limit, args.mlb_limit_per_slot)
    scope.to_csv(TABLE_DIR / "candidate_news_pilot_scope_v0_1.csv", index=False)

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
                        "message": "NAVER_CLIENT_ID and NAVER_CLIENT_SECRET are not loaded in the shell environment",
                    }
                )

        for provider in providers:
            queries = build_google_queries(candidate, args.query_mode) if provider == "google_news_rss" else build_naver_queries(candidate)
            for query in queries:
                if provider == "google_news_rss":
                    fetched = fetch_google_news(query, args.max_items_per_query, args.timeout_sec)
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
                    is_candidate_match = record_matches_candidate(item, candidate["search_name"])
                    records.append(
                        {
                            **candidate_dict,
                            **item,
                            "article_id": item_id,
                            "collected_at": collected_at,
                            "candidate_name_match": is_candidate_match,
                        }
                    )
                time.sleep(args.sleep_sec)

    metadata_path = OUTPUT_DIR / "candidate_news_metadata.csv"
    raw_path = OUTPUT_DIR / "candidate_news_raw.jsonl"
    audit_path = TABLE_DIR / "candidate_news_collection_audit_v0_1.csv"
    with raw_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    if records:
        pd.DataFrame(records).to_csv(metadata_path, index=False)
    else:
        pd.DataFrame().to_csv(metadata_path, index=False)
    pd.DataFrame(provider_audit).to_csv(audit_path, index=False)

    manifest = {
        "collected_at": collected_at,
        "scope_rows": len(scope),
        "article_rows": len(records),
        "candidate_name_match_rows": int(sum(bool(record.get("candidate_name_match")) for record in records)),
        "providers_requested": args.providers,
        "query_mode": args.query_mode,
        "mlb_limit_per_slot": args.mlb_limit_per_slot,
        "asian_limit": args.asian_limit,
        "naver_status": "attempted" if naver_client_id and naver_client_secret else "skipped_missing_env",
        "google_api_needed": False,
        "metadata_path": str(metadata_path.relative_to(PROJECT_ROOT)),
        "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
        "scope_path": "outputs/tables/candidate_news_pilot_scope_v0_1.csv",
        "audit_path": "outputs/tables/candidate_news_collection_audit_v0_1.csv",
    }
    manifest_path = OUTPUT_DIR / "candidate_news_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
