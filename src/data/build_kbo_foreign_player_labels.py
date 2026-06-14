#!/usr/bin/env python3
"""Build a first historical KBO foreign-player season label table.

This is a validation target table, not a candidate feature table. KBO outcomes
such as WAR, wRC+, renewal, replacement, and failure labels must never be used
as pre-signing candidate features.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from urllib.parse import quote

import certifi
import numpy as np
import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data/external/kbo_foreign_players/wiki_templates"
PROCESSED_DIR = PROJECT_ROOT / "data/processed/kbo"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

STATIZ_DIR = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1/organized/players"
BATTING_PATH = STATIZ_DIR / "players_season_basic_batting.csv"
PITCHING_PATH = STATIZ_DIR / "players_season_basic_pitching.csv"

YEARS = list(range(2017, 2027))
OUTCOME_YEARS = set(range(2017, 2026))
STATIZ_OUTCOME_YEARS = set(range(2023, 2026))

TEAM_MAP = {
    "KIA 타이거즈": "KIA",
    "기아 타이거즈": "KIA",
    "삼성 라이온즈": "삼성",
    "LG 트윈스": "LG",
    "엘지 트윈스": "LG",
    "두산 베어스": "두산",
    "kt wiz": "KT",
    "KT 위즈": "KT",
    "SSG 랜더스": "SSG",
    "SK 와이번스": "SK",
    "롯데 자이언츠": "롯데",
    "한화 이글스": "한화",
    "NC 다이노스": "NC",
    "키움 히어로즈": "키움",
    "넥센 히어로즈": "넥센",
}

SHORT_TEAM_MAP = {
    "KIA": "KIA",
    "기아": "KIA",
    "삼성": "삼성",
    "LG": "LG",
    "엘지": "LG",
    "두산": "두산",
    "kt": "KT",
    "KT": "KT",
    "SSG": "SSG",
    "SK": "SK",
    "롯데": "롯데",
    "한화": "한화",
    "NC": "NC",
    "키움": "키움",
    "넥센": "넥센",
}

ROLE_KO_TO_GROUP = {
    "야수": "hitter",
    "투수": "starter",
}

STATIZ_NAME_ALIASES = {
    "브랜던워델": "브랜든",
    "이언매키니": "맥키니",
    "맷데이비드슨": "데이비슨",
    "터커데이비드슨": "데이비슨",
    "빅터레예스": "레이예스",
    "엔마누엘데헤수스": "헤이수스",
    "요나탄페를라사": "페라자",
    "에스테반플로리알": "플로리얼",
    "루벤카데나스": "카디네스",
}

TARGET_ONLY_COLUMNS = [
    "first_kbo_pa",
    "first_kbo_ip",
    "first_kbo_war",
    "first_kbo_wrc_plus",
    "first_kbo_era",
    "first_kbo_k_bb_pct",
    "renewed_next_year",
    "in_season_replaced",
    "injury_exit_flag",
    "performance_exit_flag",
    "temporary_foreign_flag",
    "success",
    "strong_success",
    "failure",
]


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_name(value: object) -> str:
    text = normalize_text(value)
    text = text.replace(".", "")
    text = re.sub(r"\s+", "", text)
    return text


def normalize_team(value: object) -> str:
    text = normalize_text(value)
    if text in TEAM_MAP:
        return TEAM_MAP[text]
    if text in SHORT_TEAM_MAP:
        return SHORT_TEAM_MAP[text]
    for key, mapped in TEAM_MAP.items():
        if key in text:
            return mapped
    for key, mapped in SHORT_TEAM_MAP.items():
        if key in text:
            return mapped
    return text


def fetch_template_html(year: int) -> str:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"ko_wiki_kbo_foreign_players_{year}.html"
    if path.exists() and path.stat().st_size > 1000:
        return path.read_text(encoding="utf-8")

    url = "https://ko.wikipedia.org/wiki/" + quote(f"틀:{year}년 KBO 리그 외국인 선수")
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (SDA KBO foreign player research)"},
        verify=certifi.where(),
        timeout=25,
    )
    response.raise_for_status()
    path.write_text(response.text, encoding="utf-8")
    return response.text


def parse_team_players(year: int, team: str, text: str) -> list[dict[str, object]]:
    rows = []
    for name, role in re.findall(r"([^()]+?)\s*\((투수|야수)\)", text):
        player_name_ko = normalize_text(name)
        if not player_name_ko:
            continue
        rows.append(
            {
                "season": year,
                "player_name_ko": player_name_ko,
                "kbo_team_raw": team,
                "kbo_team": normalize_team(team),
                "role_ko": role,
                "role_group": ROLE_KO_TO_GROUP.get(role, "unknown"),
                "template_status": "listed",
                "release_note": "",
                "source": "ko_wiki_foreign_player_template",
            }
        )
    return rows


def parse_release_players(year: int, text: str) -> list[dict[str, object]]:
    rows = []
    for name, note in re.findall(r"([^()]+?)\s*\(([^()]+)\)", text):
        player_name_ko = normalize_text(name)
        note = normalize_text(note)
        if not player_name_ko or player_name_ko in {"방출 외국인 선수"}:
            continue
        team_hint = ""
        if "," in note:
            team_hint = note.split(",")[-1].strip()
        else:
            pieces = note.split()
            if pieces:
                team_hint = pieces[-1].strip()
        rows.append(
            {
                "season": year,
                "player_name_ko": player_name_ko,
                "kbo_team_raw": team_hint,
                "kbo_team": normalize_team(team_hint),
                "role_ko": "",
                "role_group": "unknown",
                "template_status": "released",
                "release_note": note,
                "source": "ko_wiki_foreign_player_template_release_row",
            }
        )
    return rows


def parse_templates() -> pd.DataFrame:
    rows = []
    for year in YEARS:
        html = fetch_template_html(year)
        tables = pd.read_html(StringIO(html))
        if not tables:
            continue
        table = tables[0].copy()
        table.columns = ["team", "players"]
        for _, row in table.iterrows():
            team = normalize_text(row["team"])
            players_text = normalize_text(row["players"])
            if not team or not players_text:
                continue
            if "방출 외국인 선수" in team:
                rows.extend(parse_release_players(year, players_text))
            elif team.startswith("vte"):
                continue
            else:
                rows.extend(parse_team_players(year, team, players_text))

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    out["player_name_norm"] = out["player_name_ko"].map(normalize_name)
    out["team_norm"] = out["kbo_team"].map(normalize_team)
    out["player_season_team_key"] = (
        out["season"].astype(str) + "_" + out["team_norm"] + "_" + out["player_name_norm"]
    )
    return out.drop_duplicates(
        ["season", "team_norm", "player_name_norm", "template_status", "release_note"]
    ).reset_index(drop=True)


def baseball_ip_to_float(value: object) -> float:
    if pd.isna(value):
        return np.nan
    try:
        number = float(value)
    except (TypeError, ValueError):
        return np.nan
    whole = int(number)
    frac_digit = int(round((number - whole) * 10))
    if frac_digit in {1, 2}:
        return whole + frac_digit / 3
    return number


def load_statiz_profiles() -> tuple[pd.DataFrame, pd.DataFrame]:
    batting = pd.read_csv(BATTING_PATH)
    pitching = pd.read_csv(PITCHING_PATH)
    batting["team_norm"] = batting["t_code_name"].map(normalize_team)
    pitching["team_norm"] = pitching["t_code_name"].map(normalize_team)
    batting["p_name_norm"] = batting["p_name"].map(normalize_name)
    pitching["p_name_norm"] = pitching["p_name"].map(normalize_name)
    pitching["IP_float"] = pitching["IP"].map(baseball_ip_to_float)
    return batting, pitching


def name_match_score(template_name: str, statiz_name: str) -> int:
    template_norm = normalize_name(template_name)
    statiz_norm = normalize_name(statiz_name)
    if not template_norm or not statiz_norm:
        return 0
    alias = STATIZ_NAME_ALIASES.get(template_norm, "")
    if alias and alias == statiz_norm:
        return 95
    if template_norm == statiz_norm:
        return 100
    if statiz_norm in template_norm:
        return 80 + min(len(statiz_norm), 10)
    if template_norm in statiz_norm:
        return 70 + min(len(template_norm), 10)
    template_tokens = set(template_norm)
    statiz_tokens = set(statiz_norm)
    overlap = len(template_tokens & statiz_tokens)
    return overlap


def match_statiz_row(row: pd.Series, batting: pd.DataFrame, pitching: pd.DataFrame) -> dict[str, object]:
    season = row["season"]
    team = row["team_norm"]
    role_group = row["role_group"]
    if season not in STATIZ_OUTCOME_YEARS:
        return {}

    if role_group == "hitter":
        source = batting[(batting["year"].eq(season)) & (batting["team_norm"].eq(team))].copy()
    elif role_group in {"starter", "reliever"}:
        source = pitching[(pitching["year"].eq(season)) & (pitching["team_norm"].eq(team))].copy()
    else:
        source = pd.concat(
            [
                batting[(batting["year"].eq(season)) & (batting["team_norm"].eq(team))].assign(_role="hitter"),
                pitching[(pitching["year"].eq(season)) & (pitching["team_norm"].eq(team))].assign(_role="pitcher"),
            ],
            ignore_index=True,
            sort=False,
        )

    if source.empty:
        return {}
    source["_match_score"] = source["p_name"].map(lambda value: name_match_score(row["player_name_ko"], value))
    source = source[source["_match_score"].ge(70)].sort_values("_match_score", ascending=False)
    if source.empty:
        return {}

    matched = source.iloc[0].to_dict()
    return matched


def add_renewal_flags(parsed: pd.DataFrame) -> pd.DataFrame:
    out = parsed.copy()
    active = out[out["template_status"].eq("listed")].copy()
    active_pairs = set(zip(active["season"], active["player_name_norm"]))
    out["renewed_next_year"] = np.nan
    for idx, row in out.iterrows():
        season = int(row["season"])
        if season >= 2026:
            continue
        out.loc[idx, "renewed_next_year"] = int((season + 1, row["player_name_norm"]) in active_pairs)
    return out


def add_exit_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    release_note = out["release_note"].fillna("")
    out["in_season_replaced"] = out["template_status"].eq("released").astype(int)
    out["injury_exit_flag"] = release_note.str.contains(
        "부상|어깨|팔꿈치|허리|손가락|발목|발가락|무릎|햄스트링|근육|가슴|옆구리|종아리|발등|고관절",
        regex=True,
        na=False,
    ).astype(int)
    out["performance_exit_flag"] = release_note.str.contains(
        "성적 부진|기복|수비 실책|태업|부진",
        regex=True,
        na=False,
    ).astype(int)
    out["temporary_foreign_flag"] = release_note.str.contains("임시 외국인", regex=False, na=False).astype(int)
    return out


def make_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["outcome_available"] = out["season"].isin(STATIZ_OUTCOME_YEARS) & (
        out["first_kbo_pa"].notna() | out["first_kbo_ip"].notna()
    )
    out["label_available"] = out["season"].isin(OUTCOME_YEARS) & (
        out["outcome_available"] | out["template_status"].eq("released") | out["renewed_next_year"].notna()
    )

    out["success"] = np.nan
    out["strong_success"] = np.nan
    out["failure"] = np.nan

    hitter = out["role_group"].eq("hitter")
    pitcher = out["role_group"].isin(["starter", "reliever"])

    hitter_success = (
        hitter
        & (
            (out["first_kbo_pa"].ge(300) & (out["first_kbo_war"].ge(2.0) | out["first_kbo_wrc_plus"].ge(115)))
            | out["renewed_next_year"].eq(1)
        )
    )
    hitter_strong = hitter & (
        (out["first_kbo_pa"].ge(450) & (out["first_kbo_war"].ge(4.0) | out["first_kbo_wrc_plus"].ge(135)))
        | (out["renewed_next_year"].eq(1) & out["first_kbo_war"].ge(3.0))
    )
    hitter_failure = hitter & (
        out["in_season_replaced"].eq(1)
        | (
            out["renewed_next_year"].eq(0)
            & (
                out["first_kbo_pa"].lt(250)
                | out["first_kbo_war"].lt(0.5)
                | out["first_kbo_wrc_plus"].lt(80)
            )
        )
    )

    pitcher_success = pitcher & (
        (out["first_kbo_ip"].ge(100) & (out["first_kbo_war"].ge(2.5) | out["first_kbo_era"].le(4.0)))
        | out["renewed_next_year"].eq(1)
    )
    pitcher_strong = pitcher & (
        (out["first_kbo_ip"].ge(140) & (out["first_kbo_war"].ge(4.0) | out["first_kbo_era"].le(3.3)))
        | (out["renewed_next_year"].eq(1) & out["first_kbo_war"].ge(3.5))
    )
    pitcher_failure = pitcher & (
        out["in_season_replaced"].eq(1)
        | (
            out["renewed_next_year"].eq(0)
            & (
                out["first_kbo_ip"].lt(70)
                | out["first_kbo_war"].lt(0.5)
                | out["first_kbo_era"].ge(5.5)
            )
        )
    )

    label_mask = out["label_available"].eq(True)
    out.loc[label_mask, "success"] = (hitter_success | pitcher_success).astype(int)
    out.loc[label_mask, "strong_success"] = (hitter_strong | pitcher_strong).astype(int)
    out.loc[label_mask, "failure"] = (hitter_failure | pitcher_failure).astype(int)

    # If a player is explicitly released, failure is a safer label unless it is
    # a clearly marked temporary foreign-player exit.
    explicit_release = out["template_status"].eq("released") & out["temporary_foreign_flag"].eq(0)
    out.loc[explicit_release & label_mask, "failure"] = 1
    out.loc[explicit_release & label_mask, "success"] = 0
    out.loc[explicit_release & label_mask, "strong_success"] = 0
    return out


def build_label_table() -> pd.DataFrame:
    parsed = parse_templates()
    parsed = add_renewal_flags(parsed)
    parsed = add_exit_flags(parsed)
    batting, pitching = load_statiz_profiles()

    rows = []
    for _, row in parsed.iterrows():
        row_dict = row.to_dict()
        stat = match_statiz_row(row, batting, pitching)
        row_dict["statiz_matched"] = bool(stat)
        row_dict["source_player_id"] = stat.get("p_no", np.nan)
        row_dict["player_name_statiz"] = stat.get("p_name", "")
        row_dict["player_name_en"] = stat.get("p_nameEN", "")
        row_dict["position_or_role"] = stat.get("p_position", row.get("role_ko", ""))
        row_dict["first_kbo_pa"] = stat.get("PA", np.nan)
        row_dict["first_kbo_ip"] = baseball_ip_to_float(stat.get("IP", np.nan))
        row_dict["first_kbo_war"] = stat.get("WAR", np.nan)
        row_dict["first_kbo_wrc_plus"] = stat.get("wRCplus", np.nan)
        row_dict["first_kbo_era"] = stat.get("ERA", np.nan)
        row_dict["first_kbo_k_bb_pct"] = np.nan
        if row_dict["role_group"] in {"starter", "reliever"} and pd.notna(stat.get("KBB", np.nan)):
            row_dict["first_kbo_k_bb_pct"] = stat.get("KBB", np.nan)
        elif row_dict["role_group"] == "hitter" and pd.notna(stat.get("SO", np.nan)) and pd.notna(stat.get("BB", np.nan)):
            pa = stat.get("PA", np.nan)
            if pd.notna(pa) and pa:
                row_dict["first_kbo_k_bb_pct"] = (stat.get("SO", 0) - stat.get("BB", 0)) / pa

        if row_dict["role_group"] == "unknown":
            if pd.notna(row_dict["first_kbo_pa"]):
                row_dict["role_group"] = "hitter"
                row_dict["role_ko"] = "야수"
            elif pd.notna(row_dict["first_kbo_ip"]):
                row_dict["role_group"] = "starter"
                row_dict["role_ko"] = "투수"

        rows.append(row_dict)

    labels = pd.DataFrame(rows)
    labels = make_labels(labels)

    labels["player_key"] = labels["player_name_norm"]
    labels["player_name"] = labels["player_name_ko"]
    labels["arrival_season"] = labels["season"]
    labels["pre_arrival_primary_league"] = ""
    labels["pre_arrival_level"] = ""
    labels["age_at_arrival"] = np.nan
    labels["bats"] = ""
    labels["throws"] = ""
    labels["source_confidence_1_5"] = np.select(
        [
            labels["template_status"].eq("released"),
            labels["statiz_matched"].eq(True),
            labels["season"].le(2022),
        ],
        [4, 4, 2],
        default=3,
    )
    labels["coverage_gap"] = ""
    labels.loc[labels["season"].le(2022), "coverage_gap"] = "no local STATIZ season outcome attached yet"
    labels.loc[labels["season"].eq(2026), "coverage_gap"] = "current season; label intentionally unavailable"
    labels.loc[
        labels["season"].isin(STATIZ_OUTCOME_YEARS) & labels["statiz_matched"].eq(False),
        "coverage_gap",
    ] = "STATIZ Korean name/team match not found; manual alias review needed"
    labels["target_only_columns"] = ";".join(TARGET_ONLY_COLUMNS)
    labels["accessed_at"] = datetime.now(timezone.utc).isoformat()

    ordered = [
        "player_key",
        "season",
        "player_name",
        "player_name_ko",
        "player_name_statiz",
        "player_name_en",
        "arrival_season",
        "kbo_team",
        "kbo_team_raw",
        "role_group",
        "role_ko",
        "template_status",
        "release_note",
        "pre_arrival_primary_league",
        "pre_arrival_level",
        "age_at_arrival",
        "bats",
        "throws",
        "position_or_role",
        "source_player_id",
        "first_kbo_pa",
        "first_kbo_ip",
        "first_kbo_war",
        "first_kbo_wrc_plus",
        "first_kbo_era",
        "first_kbo_k_bb_pct",
        "renewed_next_year",
        "in_season_replaced",
        "injury_exit_flag",
        "performance_exit_flag",
        "temporary_foreign_flag",
        "outcome_available",
        "label_available",
        "success",
        "strong_success",
        "failure",
        "statiz_matched",
        "source_confidence_1_5",
        "coverage_gap",
        "source",
        "target_only_columns",
        "accessed_at",
    ]
    return labels[ordered].sort_values(["season", "kbo_team", "role_group", "player_name"]).reset_index(drop=True)


def build_coverage(labels: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, group in labels.groupby("season"):
        rows.append(
            {
                "season": season,
                "rows": len(group),
                "listed_rows": int(group["template_status"].eq("listed").sum()),
                "released_rows": int(group["template_status"].eq("released").sum()),
                "statiz_matched_rows": int(group["statiz_matched"].sum()),
                "outcome_available_rows": int(group["outcome_available"].sum()),
                "label_available_rows": int(group["label_available"].sum()),
                "success_rows": int(group["success"].fillna(0).sum()),
                "failure_rows": int(group["failure"].fillna(0).sum()),
                "coverage_note": (
                    "STATIZ outcome coverage"
                    if season in STATIZ_OUTCOME_YEARS
                    else "roster/renewal proxy only"
                    if season <= 2025
                    else "current season; labels withheld"
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    labels = build_label_table()
    coverage = build_coverage(labels)

    processed_path = PROCESSED_DIR / "kbo_foreign_player_season_labels_v0_1.csv"
    output_path = OUTPUT_DIR / "kbo_foreign_player_season_labels_v0_1.csv"
    coverage_path = OUTPUT_DIR / "kbo_foreign_label_coverage_v0_1.csv"

    labels.to_csv(processed_path, index=False)
    labels.to_csv(output_path, index=False)
    coverage.to_csv(coverage_path, index=False)

    print("wrote", processed_path)
    print("wrote", output_path)
    print("wrote", coverage_path)
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
