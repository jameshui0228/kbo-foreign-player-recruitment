#!/usr/bin/env python3
"""Collect Naver Search News metadata for SSG need discovery.

The Naver API returns titles, snippets, links, and dates rather than full
article bodies. This script stores those fields as a reproducible article
metadata corpus for keyword/BM25-style need discovery.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "data/raw/articles/naver_news"

DEFAULT_QUERIES = [
    "SSG 외국인 타자",
    "SSG 외국인 선수 교체",
    "SSG 대체 외국인",
    "SSG 외야수",
    "SSG 타선 문제",
    "SSG 장타",
    "SSG 득점권",
    "SSG 중심타선",
    "SSG 감독 타선",
    "SSG 단장 외국인",
    "SSG 랜더스 외국인 타자",
    "SSG 랜더스 외야",
    "SSG 에레디아",
    "SSG 오태곤 하재훈 최지훈",
    "SSG 문학 홈런 타선",
]


TAG_RULES = {
    "foreign_hitter": ["외국인 타자", "외인 타자", "외국인 선수", "대체 외국인", "교체"],
    "outfield": ["외야", "외야수", "중견수", "좌익수", "우익수"],
    "power": ["장타", "홈런", "거포", "slug", "타구", "파워"],
    "run_creation": ["득점", "타선", "중심타선", "클러치", "득점권", "찬스", "해결사"],
    "onbase_discipline": ["출루", "볼넷", "선구안", "삼진", "존", "ABS"],
    "injury_depth": ["부상", "이탈", "공백", "복귀", "엔트리", "뎁스"],
    "defense_speed": ["수비", "주루", "도루", "범위"],
    "front_office": ["단장", "감독", "프런트", "스카우트", "영입"],
    "park_context": ["문학", "인천", "랜더스필드", "홈구장"],
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def stable_id(*parts: str) -> str:
    joined = "||".join(parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:16]


def fetch_page(
    client_id: str,
    client_secret: str,
    query: str,
    start: int,
    display: int,
    transport: str,
) -> dict:
    url = "https://openapi.naver.com/v1/search/news.json?" + urlencode(
        {"query": query, "display": display, "start": start, "sort": "date"}
    )
    if transport == "curl":
        cmd = [
            "curl",
            "-sS",
            "--max-time",
            "20",
            url,
            "-H",
            f"X-Naver-Client-Id: {client_id}",
            "-H",
            f"X-Naver-Client-Secret: {client_secret}",
            "-w",
            "\n__STATUS__:%{http_code}",
        ]
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=25)
        if proc.returncode != 0:
            detail = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"Naver curl transport error: {detail[:500]}")
        if "\n__STATUS__:" not in proc.stdout:
            raise RuntimeError("Naver curl response missing status marker")
        body, status_text = proc.stdout.rsplit("\n__STATUS__:", 1)
        status_code = int(status_text.strip())
        if status_code >= 400:
            raise RuntimeError(f"Naver API HTTP {status_code}: {body[:500]}")
        return json.loads(body)

    req = Request(
        url,
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Naver API HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Naver API transport error: {exc}") from exc


def tag_record(title: str, description: str) -> str:
    text = f"{title} {description}".lower()
    tags = []
    for tag, keywords in TAG_RULES.items():
        if any(keyword.lower() in text for keyword in keywords):
            tags.append(tag)
    return ",".join(tags)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--queries", nargs="*", default=DEFAULT_QUERIES)
    parser.add_argument("--display", type=int, default=100)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--sleep-sec", type=float, default=0.15)
    parser.add_argument("--transport", choices=["curl", "urllib"], default="curl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_dir = args.output_dir.resolve()
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("NAVER_CLIENT_ID and NAVER_CLIENT_SECRET must be set in the environment")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now().isoformat(timespec="seconds")

    records = []
    seen = set()
    for query in args.queries:
        for page_idx in range(args.pages):
            start = page_idx * args.display + 1
            if start > 1000:
                break
            payload = fetch_page(client_id, client_secret, query, start, args.display, args.transport)
            for item in payload.get("items", []):
                title = clean_text(item.get("title"))
                description = clean_text(item.get("description"))
                link = item.get("originallink") or item.get("link") or ""
                article_id = stable_id(link, title, item.get("pubDate", ""))
                if article_id in seen:
                    continue
                seen.add(article_id)
                records.append(
                    {
                        "article_id": article_id,
                        "collected_at": collected_at,
                        "query": query,
                        "title": title,
                        "description": description,
                        "pubDate": item.get("pubDate", ""),
                        "originallink": item.get("originallink", ""),
                        "link": item.get("link", ""),
                        "tags": tag_record(title, description),
                    }
                )
            time.sleep(args.sleep_sec)

    raw_path = args.output_dir / "ssg_need_news_raw.jsonl"
    csv_path = args.output_dir / "ssg_need_news_metadata.csv"
    with raw_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()) if records else [])
        if records:
            writer.writeheader()
            writer.writerows(records)

    manifest = {
        "collected_at": collected_at,
        "queries": args.queries,
        "display": args.display,
        "pages": args.pages,
        "transport": args.transport,
        "records": len(records),
        "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
        "csv_path": str(csv_path.relative_to(PROJECT_ROOT)),
    }
    manifest_path = args.output_dir / "ssg_need_news_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
