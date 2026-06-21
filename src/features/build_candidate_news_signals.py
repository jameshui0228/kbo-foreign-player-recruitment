#!/usr/bin/env python3
"""Build candidate-level news signals from collected article metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKLIST = PROJECT_ROOT / "outputs/tables/ssg_market_realism_manual_worklist_v0_1.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

RELEASE_POLICY = "candidate_news_signals_research_only_no_recommendation"


TAG_RULES = {
    "injury_medical": [
        "injury",
        "injured",
        "il",
        "injured list",
        "rehab",
        "surgery",
        "strain",
        "sprain",
        "fracture",
        "shoulder",
        "elbow",
        "ucl",
        "tommy john",
        "hamstring",
        "oblique",
        "부상",
        "재활",
        "수술",
        "말소",
        "복귀",
    ],
    "contract_market": [
        "contract",
        "free agent",
        "dfa",
        "designated",
        "released",
        "waiver",
        "waivers",
        "outright",
        "outrighted",
        "optioned",
        "selected",
        "trade",
        "traded",
        "posting",
        "transfer",
        "buyout",
        "계약",
        "방출",
        "웨이버",
        "이적",
        "바이아웃",
    ],
    "korea_willingness": [
        "kbo",
        "korea",
        "korean baseball",
        "overseas",
        "asia",
        "npb",
        "cpbl",
        "foreign league",
        "한국",
        "해외",
        "아시아",
    ],
    "adaptation_context": [
        "adjustment",
        "adapt",
        "language",
        "culture",
        "visa",
        "travel",
        "role",
        "starter",
        "bullpen",
        "outfield",
        "적응",
        "비자",
        "역할",
        "선발",
        "불펜",
    ],
}


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def extract_tags(row: pd.Series) -> list[str]:
    text = f"{row.get('title', '')} {row.get('description', '')}"
    return [tag for tag, keywords in TAG_RULES.items() if contains_any(text, keywords)]


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["published_at"] = pd.to_datetime(out["pubDate"], errors="coerce", utc=True)
    max_date = out["published_at"].max()
    if pd.isna(max_date):
        out["days_since_article"] = pd.NA
        out["recent_180d_article"] = False
    else:
        out["days_since_article"] = (max_date - out["published_at"]).dt.days
        out["recent_180d_article"] = out["days_since_article"].between(0, 180, inclusive="both")
    return out


def build_article_relevance(news: pd.DataFrame) -> pd.DataFrame:
    out = parse_dates(news.copy())
    for col in ["title", "description", "query", "provider", "query_language", "originallink", "link", "source_name"]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].map(clean)
    out["news_tags_list"] = out.apply(extract_tags, axis=1)
    out["news_tags"] = out["news_tags_list"].map(lambda tags: ",".join(tags))
    out["candidate_name_match"] = out["candidate_name_match"].astype(str).str.lower().isin(["true", "1", "1.0"])
    out["article_relevance_score"] = 0
    out.loc[out["candidate_name_match"], "article_relevance_score"] += 4
    out.loc[out["news_tags"].str.contains("injury_medical", na=False), "article_relevance_score"] += 3
    out.loc[out["news_tags"].str.contains("contract_market", na=False), "article_relevance_score"] += 3
    out.loc[out["news_tags"].str.contains("korea_willingness", na=False), "article_relevance_score"] += 2
    out.loc[out["news_tags"].str.contains("adaptation_context", na=False), "article_relevance_score"] += 1
    out.loc[out["recent_180d_article"], "article_relevance_score"] += 1
    out["article_use_status"] = out["article_relevance_score"].ge(5).map({True: "usable_candidate_news_signal", False: "weak_or_background_news"})
    return out.sort_values(["candidate_key", "article_relevance_score", "published_at"], ascending=[True, False, False])


def summarize_candidate(group: pd.DataFrame) -> dict[str, object]:
    usable = group[group["article_use_status"].eq("usable_candidate_news_signal")]
    def count_tag(tag: str) -> int:
        return int(usable["news_tags"].str.contains(tag, na=False).sum())

    sample = usable.sort_values(["article_relevance_score", "published_at"], ascending=[False, False]).head(3)
    top_titles = " | ".join(sample["title"].drop_duplicates().astype(str).tolist())
    top_links = " | ".join(sample["link"].drop_duplicates().astype(str).tolist())
    latest = usable["published_at"].max()
    return {
        "candidate_key": group["candidate_key"].iloc[0],
        "fit_slot": group["fit_slot"].iloc[0],
        "player_id": group.get("player_id", pd.Series([pd.NA])).iloc[0],
        "player_name": group["player_name"].iloc[0],
        "team_or_org": group["team_or_org"].iloc[0],
        "article_rows": len(group),
        "usable_article_rows": len(usable),
        "english_article_rows": int(usable["query_language"].eq("en").sum()),
        "korean_article_rows": int(usable["query_language"].eq("ko").sum()),
        "injury_medical_article_rows": count_tag("injury_medical"),
        "contract_market_article_rows": count_tag("contract_market"),
        "korea_willingness_article_rows": count_tag("korea_willingness"),
        "adaptation_context_article_rows": count_tag("adaptation_context"),
        "latest_candidate_news_date": "" if pd.isna(latest) else str(latest),
        "top_candidate_news_titles": top_titles,
        "top_candidate_news_links": top_links,
    }


def build_summary(article_relevance: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    if article_relevance.empty:
        base = scope.copy()
        for col in [
            "article_rows",
            "usable_article_rows",
            "english_article_rows",
            "korean_article_rows",
            "injury_medical_article_rows",
            "contract_market_article_rows",
            "korea_willingness_article_rows",
            "adaptation_context_article_rows",
        ]:
            base[col] = 0
        base["latest_candidate_news_date"] = ""
        base["top_candidate_news_titles"] = ""
        base["top_candidate_news_links"] = ""
    else:
        summary = pd.DataFrame([summarize_candidate(group) for _, group in article_relevance.groupby("candidate_key")])
        base = scope.merge(summary, on=["candidate_key", "fit_slot", "player_id", "player_name", "team_or_org"], how="left")
        count_cols = [
            "article_rows",
            "usable_article_rows",
            "english_article_rows",
            "korean_article_rows",
            "injury_medical_article_rows",
            "contract_market_article_rows",
            "korea_willingness_article_rows",
            "adaptation_context_article_rows",
        ]
        for col in count_cols:
            base[col] = pd.to_numeric(base[col], errors="coerce").fillna(0).astype(int)
        for col in ["latest_candidate_news_date", "top_candidate_news_titles", "top_candidate_news_links"]:
            base[col] = base[col].fillna("")

    base["candidate_news_status"] = "no_candidate_specific_news_found"
    base.loc[base["usable_article_rows"].gt(0), "candidate_news_status"] = "candidate_news_review_available"
    base.loc[base["injury_medical_article_rows"].gt(0), "candidate_news_status"] = "medical_news_review_needed"
    base.loc[
        base["contract_market_article_rows"].gt(0) & base["injury_medical_article_rows"].eq(0),
        "candidate_news_status",
    ] = "market_contract_news_review_needed"
    base.loc[
        base["korea_willingness_article_rows"].gt(0)
        & base["injury_medical_article_rows"].eq(0)
        & base["contract_market_article_rows"].eq(0),
        "candidate_news_status",
    ] = "korea_or_overseas_context_found"
    base["candidate_news_release_policy"] = RELEASE_POLICY
    base["is_final_recommendation"] = False
    base["shortlist_label_allowed"] = False
    base["candidate_name_release_allowed"] = False
    base["candidate_news_score_release_allowed"] = False
    return base


def build_join(summary: pd.DataFrame, missing_status: str) -> pd.DataFrame:
    worklist = pd.read_csv(WORKLIST)
    joined = worklist.merge(
        summary[
            [
                "candidate_key",
                "fit_slot",
                "player_id",
                "player_name",
                "team_or_org",
                "position_or_role",
                "article_rows",
                "usable_article_rows",
                "english_article_rows",
                "korean_article_rows",
                "injury_medical_article_rows",
                "contract_market_article_rows",
                "korea_willingness_article_rows",
                "adaptation_context_article_rows",
                "candidate_news_status",
                "latest_candidate_news_date",
                "top_candidate_news_titles",
                "top_candidate_news_links",
                "candidate_news_release_policy",
                "candidate_news_score_release_allowed",
            ]
        ],
        on=["fit_slot", "player_id", "player_name", "team_or_org", "position_or_role"],
        how="left",
    )
    joined["candidate_news_status"] = joined["candidate_news_status"].fillna(missing_status)
    for col in [
        "usable_article_rows",
        "article_rows",
        "english_article_rows",
        "korean_article_rows",
        "injury_medical_article_rows",
        "contract_market_article_rows",
        "korea_willingness_article_rows",
        "adaptation_context_article_rows",
    ]:
        joined[col] = pd.to_numeric(joined[col], errors="coerce").fillna(0).astype(int)
    joined["candidate_news_release_policy"] = joined["candidate_news_release_policy"].fillna(RELEASE_POLICY)
    joined["candidate_news_score_release_allowed"] = False
    joined["is_final_recommendation"] = False
    joined["shortlist_label_allowed"] = False
    joined["candidate_name_release_allowed"] = False
    joined["score_release_allowed"] = False
    return joined


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default="data/raw/articles/candidate_news_pilot_v0_1")
    parser.add_argument("--raw-dirs", nargs="*", default=None)
    parser.add_argument("--scope-file", default="outputs/tables/candidate_news_pilot_scope_v0_1.csv")
    parser.add_argument("--output-suffix", default="v0_1")
    parser.add_argument("--missing-status", default="not_in_run025_pilot_scope")
    return parser.parse_args()


def read_news_metadata(raw_dirs: list[str]) -> pd.DataFrame:
    frames = []
    for raw_dir in raw_dirs:
        news_meta = PROJECT_ROOT / raw_dir / "candidate_news_metadata.csv"
        if news_meta.exists() and news_meta.stat().st_size > 0:
            try:
                frame = pd.read_csv(news_meta)
            except pd.errors.EmptyDataError:
                continue
            if frame.empty:
                continue
            frame["source_raw_dir"] = raw_dir
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    news = pd.concat(frames, ignore_index=True)
    dedupe_cols = [col for col in ["candidate_key", "originallink", "title", "pubDate"] if col in news.columns]
    if dedupe_cols:
        news = news.drop_duplicates(dedupe_cols)
    return news


def main() -> None:
    args = parse_args()
    raw_dirs = args.raw_dirs if args.raw_dirs else [args.raw_dir]
    scope_path = PROJECT_ROOT / args.scope_file

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scope = pd.read_csv(scope_path)
    news = read_news_metadata(raw_dirs)

    if news.empty:
        article_relevance = pd.DataFrame()
    else:
        article_relevance = build_article_relevance(news)

    summary = build_summary(article_relevance, scope)
    joined = build_join(summary, args.missing_status)

    article_relevance.to_csv(OUTPUT_DIR / f"candidate_news_article_relevance_{args.output_suffix}.csv", index=False)
    summary.to_csv(OUTPUT_DIR / f"candidate_news_signal_summary_{args.output_suffix}.csv", index=False)
    joined.to_csv(OUTPUT_DIR / f"ssg_market_realism_news_join_{args.output_suffix}.csv", index=False)

    slot_summary = (
        summary.groupby(["fit_slot", "candidate_news_status"], dropna=False)
        .agg(
            candidates=("candidate_key", "nunique"),
            usable_articles=("usable_article_rows", "sum"),
            injury_articles=("injury_medical_article_rows", "sum"),
            contract_articles=("contract_market_article_rows", "sum"),
            korea_context_articles=("korea_willingness_article_rows", "sum"),
        )
        .reset_index()
        .sort_values(["fit_slot", "candidates"], ascending=[True, False])
    )
    slot_summary.to_csv(OUTPUT_DIR / f"candidate_news_slot_summary_{args.output_suffix}.csv", index=False)

    print(f"article_rows={len(article_relevance)}")
    print(f"candidate_rows={len(summary)}")
    print(slot_summary.to_string(index=False))


if __name__ == "__main__":
    main()
