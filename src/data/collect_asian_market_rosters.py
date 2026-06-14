#!/usr/bin/env python3
"""Collect NPB/CPBL roster inventory for Asian-quota market screening.

Official roster pages establish current Asian-league affiliation. Nationality is
handled conservatively: CPBL official player pages expose it, while NPB English
official pages do not, so NPB nationality is only seeded from a non-official
foreign-player list and must be manually verified before candidate release.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime
from io import StringIO
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import certifi
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"
RAW_DIR = ROOT / "data/raw/asian_market_rosters"

NPB_TEAMS = {
    "g": "Yomiuri Giants",
    "t": "Hanshin Tigers",
    "db": "Yokohama DeNA BayStars",
    "d": "Chunichi Dragons",
    "c": "Hiroshima Toyo Carp",
    "s": "Tokyo Yakult Swallows",
    "h": "Fukuoka SoftBank Hawks",
    "f": "Hokkaido Nippon-Ham Fighters",
    "b": "ORIX Buffaloes",
    "e": "Tohoku Rakuten Golden Eagles",
    "l": "Saitama Seibu Lions",
    "m": "Chiba Lotte Marines",
}

NPB_BASE = "https://npb.jp"
NPB_ROSTER_URL = "https://npb.jp/bis/eng/teams/rst_{team_code}.html"
CPBL_BASE = "https://en.cpbl.com.tw"
CPBL_TEAM_INDEX = "https://en.cpbl.com.tw/team?ClubNo=AKP"
NPB_FOREIGN_WIKI = "https://en.wikipedia.org/wiki/List_of_current_foreign_Nippon_Professional_Baseball_players"
CPBL_FOREIGN_WIKI = "https://en.wikipedia.org/wiki/List_of_current_foreign_CPBL_players"

PLAYER_SECTIONS = {"PITCHERS", "CATCHERS", "INFIELDERS", "OUTFIELDERS"}
ELIGIBLE_NATIONALITY_TOKENS = {
    "japan",
    "japanese",
    "taiwan",
    "taiwanese",
    "republic of china",
    "korea",
    "south korea",
    "korean",
    "china",
    "chinese",
    "australia",
    "australian",
    "philippines",
    "filipino",
    "hong kong",
    "thailand",
    "indonesia",
    "pakistan",
    "india",
    "mongolia",
}


def fetch(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=45, verify=certifi.where(), headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    if response.encoding is None or response.encoding.lower() in {"iso-8859-1", "ascii"}:
        response.encoding = response.apparent_encoding
    return response.text


def normalize_name(name: object) -> str:
    value = re.sub(r"\[[^\]]+\]", "", str(name or "")).strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    if "," in value:
        last, first = [part.strip() for part in value.split(",", 1)]
        value = f"{first} {last}"
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).strip().lower()
    return re.sub(r"\s+", " ", value)


def extract_team_name(soup: BeautifulSoup, fallback: str) -> str:
    team_name = soup.select_one(".team_name")
    if team_name:
        return team_name.get_text(" ", strip=True)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if ":" in title:
        return title.split(":", 1)[0].strip()
    return fallback


def parse_npb_team(session: requests.Session, team_code: str, fallback_team_name: str) -> tuple[list[dict], dict]:
    url = NPB_ROSTER_URL.format(team_code=team_code)
    html = fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    team_name = extract_team_name(soup, fallback_team_name)
    table = soup.select_one("table.rosterlisttbl")
    records: list[dict] = []
    current_section = ""
    if table is None:
        return records, {"url": url, "team_code": team_code, "team_name": team_name, "rows": 0, "status": "no_table"}

    for row in table.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
        if not cells:
            continue
        if cells[0] == "No." and len(cells) >= 2:
            current_section = cells[1].upper()
            continue
        if current_section not in PLAYER_SECTIONS or len(cells) < 5:
            continue
        link = row.find("a", href=True)
        player_url = urljoin(NPB_BASE, link["href"]) if link else ""
        position_group = current_section.title()
        record = {
            "source_league": "NPB",
            "team_code": team_code,
            "team_name": team_name,
            "roster_no": cells[0],
            "player_name": cells[1],
            "normalized_player_name": normalize_name(cells[1]),
            "position_group": position_group,
            "position": position_group[:-1] if position_group.endswith("s") else position_group,
            "born": cells[2] if len(cells) > 2 else "",
            "height_cm": cells[3] if len(cells) > 3 else "",
            "weight_kg": cells[4] if len(cells) > 4 else "",
            "throws": cells[5] if len(cells) > 5 else "",
            "bats": cells[6] if len(cells) > 6 else "",
            "note": cells[7] if len(cells) > 7 else "",
            "person_url": player_url,
            "source_url": url,
            "source_confidence": 4,
        }
        records.append(record)
    return records, {"url": url, "team_code": team_code, "team_name": team_name, "rows": len(records), "status": "ok"}


def collect_npb_rosters(session: requests.Session) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict] = []
    inventory: list[dict] = []
    for code, name in NPB_TEAMS.items():
        team_records, meta = parse_npb_team(session, code, name)
        records.extend(team_records)
        inventory.append(
            {
                "source_name": "NPB official English roster",
                "league": "NPB",
                "source_url": meta["url"],
                "team_code": code,
                "team_name": meta["team_name"],
                "rows": meta["rows"],
                "data_status": meta["status"],
                "blocking_gap": "official roster has no nationality field; salary/contract status not exposed",
            }
        )
    return pd.DataFrame(records), pd.DataFrame(inventory)


def parse_cpbl_player_detail(session: requests.Session, url: str) -> dict:
    html = fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")
    brief = soup.select_one(".PlayerBrief")
    text = brief.get_text(" ", strip=True) if brief else ""
    out = {
        "detail_position": "",
        "tb": "",
        "detail_height_cm": "",
        "detail_weight_kg": "",
        "born": "",
        "debut": "",
        "nationality": "",
    }
    patterns = {
        "detail_position": r"Position\s+(.+?)\s+T/B",
        "tb": r"T/B\s+(.+?)\s+HT/WT",
        "born": r"Born\s+([0-9/]+)",
        "debut": r"Debut\s+([0-9/]+)",
        "nationality": r"Nationality\s+(.+)$",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            out[key] = match.group(1).strip()
    hw = re.search(r"HT/WT\s+([0-9]+)\s+\(CM\)\s*/\s*([0-9]+)\s+\(KG\)", text)
    if hw:
        out["detail_height_cm"] = hw.group(1)
        out["detail_weight_kg"] = hw.group(2)
    return out


def discover_cpbl_teams(session: requests.Session) -> list[tuple[str, str, str]]:
    html = fetch(session, CPBL_TEAM_INDEX)
    soup = BeautifulSoup(html, "html.parser")
    teams: dict[str, tuple[str, str, str]] = {}
    for link in soup.find_all("a", href=True):
        href = link["href"]
        match = re.search(r"ClubNo=([A-Z0-9]+)", href)
        if not match:
            continue
        code = match.group(1)
        name = link.get_text(" ", strip=True)
        if name and name.upper() not in {"PLAYERS", "HOME"}:
            teams[code] = (code, name, urljoin(CPBL_BASE, href))
    return sorted(teams.values(), key=lambda item: item[0])


def parse_cpbl_team(session: requests.Session, team_code: str, fallback_team_name: str, team_url: str) -> tuple[list[dict], dict]:
    html = fetch(session, team_url)
    soup = BeautifulSoup(html, "html.parser")
    team_name = extract_team_name(soup, fallback_team_name)
    records: list[dict] = []
    for item in soup.select(".TeamPlayersList .item"):
        name_link = item.select_one(".cont .name a[href]")
        if name_link is None:
            continue
        position = item.select_one(".cont .pos")
        number = item.select_one(".cont .number")
        player_url = urljoin(CPBL_BASE, name_link["href"])
        detail = parse_cpbl_player_detail(session, player_url)
        tb = detail.get("tb", "")
        throws, bats = ("", "")
        if "/" in tb:
            throws, bats = [part.strip() for part in tb.split("/", 1)]
        records.append(
            {
                "source_league": "CPBL",
                "team_code": team_code,
                "team_name": team_name,
                "roster_no": number.get_text(" ", strip=True) if number else "",
                "player_name": name_link.get_text(" ", strip=True),
                "normalized_player_name": normalize_name(name_link.get_text(" ", strip=True)),
                "position_group": "",
                "position": position.get_text(" ", strip=True) if position else detail.get("detail_position", ""),
                "born": detail.get("born", ""),
                "height_cm": detail.get("detail_height_cm", ""),
                "weight_kg": detail.get("detail_weight_kg", ""),
                "throws": throws,
                "bats": bats,
                "note": "",
                "nationality": detail.get("nationality", ""),
                "debut": detail.get("debut", ""),
                "person_url": player_url,
                "source_url": team_url,
                "source_confidence": 4,
            }
        )
    return records, {
        "source_name": "CPBL official English roster and player pages",
        "league": "CPBL",
        "source_url": team_url,
        "team_code": team_code,
        "team_name": team_name,
        "rows": len(records),
        "data_status": "ok" if records else "no_players_parsed",
        "blocking_gap": "salary/contract status not exposed; active roster means release/buyout feasibility unknown",
    }


def collect_cpbl_rosters(session: requests.Session) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict] = []
    inventory: list[dict] = []
    for code, name, url in discover_cpbl_teams(session):
        team_records, meta = parse_cpbl_team(session, code, name, url)
        records.extend(team_records)
        inventory.append(meta)
    return pd.DataFrame(records), pd.DataFrame(inventory)


def read_wiki_table(session: requests.Session, url: str, table_index: int = 0) -> pd.DataFrame:
    html = fetch(session, url)
    tables = pd.read_html(StringIO(html))
    if not tables:
        return pd.DataFrame()
    df = tables[table_index].copy()
    df["source_url"] = url
    return df


def collect_foreign_seeds(session: requests.Session) -> tuple[pd.DataFrame, pd.DataFrame]:
    npb = read_wiki_table(session, NPB_FOREIGN_WIKI, table_index=0)
    if not npb.empty:
        npb["source_league"] = "NPB"
        npb["normalized_player_name"] = npb["Player"].map(normalize_name)
    cpbl = read_wiki_table(session, CPBL_FOREIGN_WIKI, table_index=1)
    if not cpbl.empty:
        cpbl["source_league"] = "CPBL"
        cpbl["normalized_player_name"] = cpbl["Player"].map(normalize_name)
    return npb, cpbl


def nationality_gate(nationality: object) -> str:
    value = str(nationality or "").strip().lower()
    if not value:
        return "unknown"
    if any(token in value for token in ELIGIBLE_NATIONALITY_TOKENS):
        return "pass"
    return "fail"


def build_asian_quota_status(npb: pd.DataFrame, cpbl: pd.DataFrame, npb_seed: pd.DataFrame) -> pd.DataFrame:
    npb_out = npb.copy()
    if not npb_seed.empty:
        seed_cols = ["normalized_player_name", "Nationality", "Position", "Debut season", "Notes", "source_url"]
        npb_out = npb_out.merge(npb_seed[seed_cols], on="normalized_player_name", how="left", suffixes=("", "_seed"))
        npb_out["nationality"] = npb_out["Nationality"].fillna("")
        npb_out["nationality_source"] = np.where(npb_out["Nationality"].notna(), "wikipedia_foreign_seed", "not_available_on_npb_official")
        npb_out["foreign_seed_position"] = npb_out["Position"]
        npb_out["foreign_seed_notes"] = npb_out["Notes"]
    else:
        npb_out["nationality"] = ""
        npb_out["nationality_source"] = "not_available_on_npb_official"
        npb_out["foreign_seed_position"] = ""
        npb_out["foreign_seed_notes"] = ""

    cpbl_out = cpbl.copy()
    cpbl_out["nationality_source"] = "cpbl_official_player_page"
    cpbl_out["foreign_seed_position"] = ""
    cpbl_out["foreign_seed_notes"] = ""

    common_cols = [
        "source_league",
        "team_code",
        "team_name",
        "roster_no",
        "player_name",
        "normalized_player_name",
        "position_group",
        "position",
        "born",
        "height_cm",
        "weight_kg",
        "throws",
        "bats",
        "note",
        "nationality",
        "nationality_source",
        "foreign_seed_position",
        "foreign_seed_notes",
        "person_url",
        "source_url",
        "source_confidence",
    ]
    for df in [npb_out, cpbl_out]:
        for column in common_cols:
            if column not in df.columns:
                df[column] = ""
    out = pd.concat([npb_out[common_cols], cpbl_out[common_cols]], ignore_index=True)
    out["asian_league_history_gate"] = "pass_current_roster"
    out["asian_quota_nationality_gate"] = out["nationality"].map(nationality_gate)
    out.loc[out["source_league"].eq("NPB") & out["nationality"].eq(""), "asian_quota_nationality_gate"] = "unknown"
    out["contract_status_gate"] = "unknown_current_roster_under_club_control"
    out["new_signing_cost_gate"] = "unknown_needs_salary_or_buyout_check"
    out["availability_bucket"] = "active_asian_league_roster_low_access"
    out["candidate_release_policy"] = "market_inventory_only_no_recommendation"
    out["is_final_recommendation"] = False
    out["candidate_name_release_allowed"] = False
    return out.sort_values(["source_league", "team_name", "position", "player_name"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-cpbl-details",
        action="store_true",
        help="Keep CPBL team-page rows only. Default fetches official player detail pages.",
    )
    args = parser.parse_args()
    if args.skip_cpbl_details:
        raise SystemExit("CPBL detail pages are required for nationality gates in this collector.")

    session = requests.Session()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")

    npb, npb_inventory = collect_npb_rosters(session)
    cpbl, cpbl_inventory = collect_cpbl_rosters(session)
    npb_seed, cpbl_seed = collect_foreign_seeds(session)
    asian_quota = build_asian_quota_status(npb, cpbl, npb_seed)
    inventory = pd.concat([npb_inventory, cpbl_inventory], ignore_index=True)
    inventory["collected_at"] = collected_at

    npb_path = OUT_DIR / "npb_official_roster_2026_v1.csv"
    cpbl_path = OUT_DIR / "cpbl_official_roster_2026_v1.csv"
    npb_seed_path = OUT_DIR / "npb_foreign_player_seed_wikipedia_v1.csv"
    cpbl_seed_path = OUT_DIR / "cpbl_foreign_player_seed_wikipedia_v1.csv"
    asian_path = OUT_DIR / "asian_quota_market_status_v1.csv"
    inventory_path = OUT_DIR / "asian_market_source_inventory_v1.csv"

    npb.to_csv(npb_path, index=False)
    cpbl.to_csv(cpbl_path, index=False)
    npb_seed.to_csv(npb_seed_path, index=False)
    cpbl_seed.to_csv(cpbl_seed_path, index=False)
    asian_quota.to_csv(asian_path, index=False)
    inventory.to_csv(inventory_path, index=False)

    raw_manifest = {
        "collected_at": collected_at,
        "sources": {
            "npb_roster_url_template": NPB_ROSTER_URL,
            "cpbl_team_index": CPBL_TEAM_INDEX,
            "npb_foreign_seed": NPB_FOREIGN_WIKI,
            "cpbl_foreign_seed": CPBL_FOREIGN_WIKI,
        },
        "rows": {
            "npb": len(npb),
            "cpbl": len(cpbl),
            "npb_foreign_seed": len(npb_seed),
            "cpbl_foreign_seed": len(cpbl_seed),
            "asian_quota_market_status": len(asian_quota),
        },
    }
    (RAW_DIR / "asian_market_roster_manifest_v1.json").write_text(
        json.dumps(raw_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"wrote {npb_path} ({len(npb)} rows)")
    print(f"wrote {cpbl_path} ({len(cpbl)} rows)")
    print(f"wrote {asian_path} ({len(asian_quota)} rows)")
    print(f"wrote {inventory_path} ({len(inventory)} rows)")


if __name__ == "__main__":
    main()
