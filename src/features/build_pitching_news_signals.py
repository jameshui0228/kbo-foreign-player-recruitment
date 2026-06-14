#!/usr/bin/env python3
"""Build pitcher-side news signals for SSG need discovery."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data/raw/articles/naver_news_pitching/ssg_need_news_metadata.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

TAG_RULES = {
    "foreign_pitcher": ["외국인 투수", "외인 투수", "외국인 선발", "대체 외국인 투수", "외인 선발"],
    "replacement_decision": ["교체", "퇴출", "방출", "웨이버", "영입", "대체", "계약", "새 외국인"],
    "starter_rotation": ["선발", "선발진", "로테이션", "퀄리티스타트", "QS", "이닝", "조기 강판", "강판"],
    "bullpen_load": ["불펜", "필승조", "과부하", "연투", "마무리", "셋업", "중간계투", "구원"],
    "injury_depth": ["부상", "이탈", "공백", "복귀", "재활", "엔트리", "말소"],
    "run_prevention": ["실점", "평균자책", "ERA", "피안타", "볼넷", "피홈런", "제구", "무실점", "위기"],
    "defense_support": ["수비", "실책", "포수", "도루", "주루", "프레이밍"],
    "front_office": ["감독", "단장", "스카우트", "프런트", "결단", "고민"],
}

NAME_RULES = {
    "타케다": ["타케다", "케이쇼"],
    "베니지아노": ["베니지아노"],
    "화이트": ["화이트", "미치 화이트"],
    "긴지로": ["긴지로"],
    "김광현": ["김광현"],
    "김건우": ["김건우"],
    "최민준": ["최민준"],
    "문승원": ["문승원"],
    "노경은": ["노경은"],
    "조병현": ["조병현"],
    "김민": ["김민"],
    "이로운": ["이로운"],
}


def clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def extract_tags(text: str) -> list[str]:
    return [tag for tag, keywords in TAG_RULES.items() if contains_any(text, keywords)]


def extract_names(text: str) -> list[str]:
    return [name for name, keywords in NAME_RULES.items() if contains_any(text, keywords)]


def build_labeled(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for column in ["query", "title", "description", "pubDate", "originallink", "link", "tags"]:
        if column not in out.columns:
            out[column] = ""
        out[column] = out[column].map(clean)
    out["text"] = out["query"] + " " + out["title"] + " " + out["description"]
    out["pitching_tags_list"] = out["text"].map(extract_tags)
    out["ssg_pitcher_names_list"] = out["text"].map(extract_names)
    out["pitching_tags"] = out["pitching_tags_list"].map(lambda values: ",".join(values))
    out["ssg_pitcher_names"] = out["ssg_pitcher_names_list"].map(lambda values: ",".join(values))
    out["mentions_ssg"] = out["text"].str.contains("SSG|랜더스|쓱", regex=True, na=False)
    out["pitching_intent"] = out["pitching_tags_list"].map(bool) | out["ssg_pitcher_names_list"].map(bool)
    out["strategy_signal"] = (
        out["mentions_ssg"]
        & (
            out["pitching_tags"].str.contains(
                "foreign_pitcher|replacement_decision|starter_rotation|bullpen_load|injury_depth",
                regex=True,
                na=False,
            )
            | out["ssg_pitcher_names_list"].map(bool)
        )
    )
    out["published_at"] = pd.to_datetime(out["pubDate"], errors="coerce", utc=True)
    out["published_year"] = out["published_at"].dt.year
    out["recency_2026"] = out["published_year"].eq(2026)

    out["signal_score"] = 0
    out.loc[out["mentions_ssg"], "signal_score"] += 3
    out.loc[out["pitching_tags"].str.contains("foreign_pitcher|replacement_decision", regex=True, na=False), "signal_score"] += 3
    out.loc[out["pitching_tags"].str.contains("starter_rotation|bullpen_load|injury_depth", regex=True, na=False), "signal_score"] += 2
    out.loc[out["pitching_tags"].str.contains("run_prevention|front_office", regex=True, na=False), "signal_score"] += 1
    out.loc[out["ssg_pitcher_names_list"].map(bool), "signal_score"] += 1
    out.loc[out["recency_2026"], "signal_score"] += 1
    return out.sort_values(["signal_score", "published_at"], ascending=[False, False])


def summarize_tags(labeled: pd.DataFrame) -> pd.DataFrame:
    signals = labeled[labeled["strategy_signal"]].copy()
    exploded = signals.explode("pitching_tags_list")
    exploded = exploded[exploded["pitching_tags_list"].notna() & exploded["pitching_tags_list"].ne("")]
    if exploded.empty:
        return pd.DataFrame(columns=["tag", "articles", "latest_pub_date", "sample_titles"])
    summary = (
        exploded.groupby("pitching_tags_list")
        .agg(
            articles=("article_id", "nunique"),
            latest_pub_date=("published_at", "max"),
            sample_titles=("title", lambda values: " | ".join(pd.Series(values).drop_duplicates().head(5))),
        )
        .reset_index()
        .rename(columns={"pitching_tags_list": "tag"})
        .sort_values(["articles", "tag"], ascending=[False, True])
    )
    summary["latest_pub_date"] = summary["latest_pub_date"].astype(str)
    return summary


def summarize_names(labeled: pd.DataFrame) -> pd.DataFrame:
    signals = labeled[labeled["strategy_signal"]].copy()
    exploded = signals.explode("ssg_pitcher_names_list")
    exploded = exploded[exploded["ssg_pitcher_names_list"].notna() & exploded["ssg_pitcher_names_list"].ne("")]
    if exploded.empty:
        return pd.DataFrame(columns=["name", "articles", "latest_pub_date", "sample_titles"])
    summary = (
        exploded.groupby("ssg_pitcher_names_list")
        .agg(
            articles=("article_id", "nunique"),
            latest_pub_date=("published_at", "max"),
            sample_titles=("title", lambda values: " | ".join(pd.Series(values).drop_duplicates().head(5))),
        )
        .reset_index()
        .rename(columns={"ssg_pitcher_names_list": "name"})
        .sort_values(["articles", "name"], ascending=[False, True])
    )
    summary["latest_pub_date"] = summary["latest_pub_date"].astype(str)
    return summary


def summarize_queries(labeled: pd.DataFrame) -> pd.DataFrame:
    return (
        labeled.groupby("query")
        .agg(
            articles=("article_id", "nunique"),
            strategy_signals=("strategy_signal", "sum"),
            avg_signal_score=("signal_score", "mean"),
            latest_pub_date=("published_at", "max"),
        )
        .reset_index()
        .sort_values(["strategy_signals", "articles"], ascending=[False, False])
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not INPUT_PATH.exists():
        raise SystemExit(f"missing Naver pitching metadata: {INPUT_PATH}")

    source = pd.read_csv(INPUT_PATH)
    labeled = build_labeled(source)
    tag_summary = summarize_tags(labeled)
    name_summary = summarize_names(labeled)
    query_summary = summarize_queries(labeled)

    labeled.to_csv(OUTPUT_DIR / "ssg_pitching_news_relevance_labeled.csv", index=False)
    tag_summary.to_csv(OUTPUT_DIR / "ssg_pitching_news_tag_summary.csv", index=False)
    name_summary.to_csv(OUTPUT_DIR / "ssg_pitching_news_name_summary.csv", index=False)
    query_summary.to_csv(OUTPUT_DIR / "ssg_pitching_news_query_summary.csv", index=False)

    print("wrote", OUTPUT_DIR / "ssg_pitching_news_relevance_labeled.csv")
    print("strategy_signals", int(labeled["strategy_signal"].sum()), "of", len(labeled))
    print(tag_summary.head(12).to_string(index=False))
    print()
    print(name_summary.head(12).to_string(index=False))


if __name__ == "__main__":
    main()
