#!/usr/bin/env python3
"""Summarize SSG need signals from Naver news metadata."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTICLE_CSV = PROJECT_ROOT / "data/raw/articles/naver_news/ssg_need_news_metadata.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

STOPWORDS = {
    "SSG",
    "랜더스",
    "프로야구",
    "야구",
    "시즌",
    "경기",
    "오늘",
    "내일",
    "기자",
    "단독",
    "인터뷰",
    "사진",
    "뉴스",
    "종합",
}


def tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", text)
    return [token for token in tokens if token not in STOPWORDS and len(token) >= 2]


def explode_tags(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        tags = [tag for tag in str(row.get("tags", "")).split(",") if tag]
        for tag in tags:
            rows.append(
                {
                    "tag": tag,
                    "article_id": row["article_id"],
                    "query": row["query"],
                    "title": row["title"],
                    "description": row["description"],
                    "pubDate": row["pubDate"],
                    "originallink": row["originallink"],
                }
            )
    return pd.DataFrame(rows)


def build_tag_summary(df: pd.DataFrame) -> pd.DataFrame:
    exploded = explode_tags(df)
    if exploded.empty:
        return pd.DataFrame(columns=["tag", "article_count", "query_count", "sample_titles"])
    summary = (
        exploded.groupby("tag")
        .agg(
            article_count=("article_id", "nunique"),
            query_count=("query", "nunique"),
            sample_titles=("title", lambda x: " || ".join(list(dict.fromkeys(x))[:3])),
        )
        .reset_index()
        .sort_values(["article_count", "query_count", "tag"], ascending=[False, False, True])
    )
    return summary


def build_keyword_summary(df: pd.DataFrame) -> pd.DataFrame:
    counter: Counter[str] = Counter()
    tag_counters: dict[str, Counter[str]] = {}
    for _, row in df.iterrows():
        text = f"{row.get('title', '')} {row.get('description', '')}"
        tokens = tokenize(text)
        counter.update(tokens)
        tags = [tag for tag in str(row.get("tags", "")).split(",") if tag]
        for tag in tags:
            tag_counters.setdefault(tag, Counter()).update(tokens)

    rows = []
    for keyword, count in counter.most_common(120):
        top_tags = []
        for tag, tag_counter in tag_counters.items():
            if keyword in tag_counter:
                top_tags.append((tag, tag_counter[keyword]))
        top_tags = sorted(top_tags, key=lambda x: (-x[1], x[0]))[:5]
        rows.append(
            {
                "keyword": keyword,
                "count": count,
                "top_tags": ",".join(f"{tag}:{tag_count}" for tag, tag_count in top_tags),
            }
        )
    return pd.DataFrame(rows)


def build_message_candidates(tag_summary: pd.DataFrame) -> pd.DataFrame:
    # Message candidates are intentionally weak labels. They are prompts for
    # cross-checking against STATIZ/Savant, not final conclusions.
    required = {
        "power": "장타/홈런 언급이 반복된다.",
        "run_creation": "타선/득점권/해결사 언급이 반복된다.",
        "outfield": "외야 포지션 언급이 반복된다.",
        "foreign_hitter": "외국인 타자/교체 맥락이 반복된다.",
        "injury_depth": "부상/공백/뎁스 맥락이 반복된다.",
        "onbase_discipline": "출루/선구안/존/삼진 맥락이 반복된다.",
    }
    tag_counts = dict(zip(tag_summary.get("tag", []), tag_summary.get("article_count", [])))
    rows = []
    for tag, interpretation in required.items():
        rows.append(
            {
                "candidate_signal": tag,
                "article_count": int(tag_counts.get(tag, 0)),
                "text_interpretation": interpretation,
                "data_crosscheck_needed": "STATIZ/Savant에서 같은 방향의 결핍 또는 후보 강점이 확인되어야 메시지로 승격",
            }
        )
    return pd.DataFrame(rows).sort_values(["article_count", "candidate_signal"], ascending=[False, True])


def add_relevance_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    text = (out["title"].astype(str) + " " + out["description"].astype(str)).str.lower()
    out["mentions_ssg_in_snippet"] = text.str.contains("ssg|랜더스", regex=True)
    out["mentions_foreign_context"] = text.str.contains("외국인|외인|대체|교체|영입", regex=True)
    out["mentions_hitter_context"] = text.str.contains("타자|타선|외야|홈런|장타|득점|출루", regex=True)
    out["strict_relevance"] = out["mentions_ssg_in_snippet"]
    out["high_value_relevance"] = (
        out["mentions_ssg_in_snippet"]
        & (out["mentions_foreign_context"] | out["mentions_hitter_context"])
    )
    return out


def main() -> None:
    if not ARTICLE_CSV.exists():
        raise SystemExit(f"Missing input: {ARTICLE_CSV}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = add_relevance_flags(pd.read_csv(ARTICLE_CSV).fillna(""))

    strict_df = df[df["strict_relevance"]].copy()
    high_value_df = df[df["high_value_relevance"]].copy()

    tag_summary = build_tag_summary(strict_df)
    keyword_summary = build_keyword_summary(strict_df)
    message_candidates = build_message_candidates(tag_summary)

    df.to_csv(OUTPUT_DIR / "ssg_news_need_relevance_labeled.csv", index=False)
    tag_summary.to_csv(OUTPUT_DIR / "ssg_news_need_tag_summary.csv", index=False)
    keyword_summary.to_csv(OUTPUT_DIR / "ssg_news_need_keyword_summary.csv", index=False)
    message_candidates.to_csv(OUTPUT_DIR / "ssg_message_candidates_from_text.csv", index=False)

    print("records_total", len(df))
    print("records_strict_ssg_snippet", len(strict_df))
    print("records_high_value", len(high_value_df))
    print("wrote", OUTPUT_DIR / "ssg_news_need_relevance_labeled.csv")
    print("wrote", OUTPUT_DIR / "ssg_news_need_tag_summary.csv")
    print("wrote", OUTPUT_DIR / "ssg_news_need_keyword_summary.csv")
    print("wrote", OUTPUT_DIR / "ssg_message_candidates_from_text.csv")
    print(message_candidates.to_string(index=False))


if __name__ == "__main__":
    main()
