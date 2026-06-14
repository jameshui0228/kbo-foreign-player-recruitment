#!/usr/bin/env python3
"""Collect 2026 NPB official first-team and farm player stats.

This expands the Asian market layer beyond rosters. It uses NPB official
English pages for team-level regular season and farm batting/pitching tables,
then joins those stats back to the official roster inventory and the existing
Asian quota market nationality seed.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from io import StringIO
from pathlib import Path
from zoneinfo import ZoneInfo

import certifi
import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"
RAW_DIR = ROOT / "data/raw/asian_market_rosters"

NPB_BASE = "https://npb.jp"
STAT_URL = "https://npb.jp/bis/eng/2026/stats/{stat_code}_{team_code}.html"

NPB_TEAMS = {
    "g": {"team_name": "Yomiuri Giants", "league": "CL"},
    "t": {"team_name": "Hanshin Tigers", "league": "CL"},
    "db": {"team_name": "Yokohama DeNA BayStars", "league": "CL"},
    "d": {"team_name": "Chunichi Dragons", "league": "CL"},
    "c": {"team_name": "Hiroshima Toyo Carp", "league": "CL"},
    "s": {"team_name": "Tokyo Yakult Swallows", "league": "CL"},
    "h": {"team_name": "Fukuoka SoftBank Hawks", "league": "PL"},
    "f": {"team_name": "Hokkaido Nippon-Ham Fighters", "league": "PL"},
    "b": {"team_name": "ORIX Buffaloes", "league": "PL"},
    "e": {"team_name": "Tohoku Rakuten Golden Eagles", "league": "PL"},
    "l": {"team_name": "Saitama Seibu Lions", "league": "PL"},
    "m": {"team_name": "Chiba Lotte Marines", "league": "PL"},
}

STAT_TABLES = {
    "idb1": {"level": "npb_first_team", "stat_type": "batting"},
    "idp1": {"level": "npb_first_team", "stat_type": "pitching"},
    "idb2": {"level": "npb_farm", "stat_type": "batting"},
    "idp2": {"level": "npb_farm", "stat_type": "pitching"},
}


def fetch(session: requests.Session, url: str) -> str:
    response = session.get(url, timeout=45, verify=certifi.where(), headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    if response.encoding is None or response.encoding.lower() in {"iso-8859-1", "ascii"}:
        response.encoding = response.apparent_encoding
    return response.text


def normalize_name(name: object) -> str:
    value = re.sub(r"\[[^\]]+\]", "", str(name or "")).strip()
    value = value.lstrip("*").strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    if "," in value:
        last, first = [part.strip() for part in value.split(",", 1)]
        value = f"{first} {last}"
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).strip().lower()
    return re.sub(r"\s+", " ", value)


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def ip_to_float(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    if "." not in text:
        return float(pd.to_numeric(text, errors="coerce"))
    whole, frac = text.split(".", 1)
    whole_num = float(pd.to_numeric(whole, errors="coerce"))
    if pd.isna(whole_num):
        return np.nan
    outs = int(frac[:1] or 0)
    return whole_num + outs / 3


def collect_stat_table(session: requests.Session, team_code: str, stat_code: str) -> tuple[pd.DataFrame, dict[str, object]]:
    url = STAT_URL.format(stat_code=stat_code, team_code=team_code)
    html = fetch(session, url)
    tables = pd.read_html(StringIO(html))
    meta = {
        "source_name": "NPB official English player stats",
        "league": "NPB",
        "team_code": team_code,
        "team_name": NPB_TEAMS[team_code]["team_name"],
        "npb_league": NPB_TEAMS[team_code]["league"],
        "stat_code": stat_code,
        "level": STAT_TABLES[stat_code]["level"],
        "stat_type": STAT_TABLES[stat_code]["stat_type"],
        "source_url": url,
        "rows": 0,
        "data_status": "no_table",
        "blocking_gap": "official NPB stats expose performance but not salary, contract, buyout, or nationality for all players",
    }
    if not tables:
        return pd.DataFrame(), meta
    df = tables[0].copy()
    df.columns = [str(col).strip() for col in df.columns]
    name_col = "Player" if "Player" in df.columns else "Pitcher"
    df = df[df[name_col].notna()].copy()
    df["raw_player_name"] = df[name_col].astype(str)
    df["player_name"] = df["raw_player_name"].str.lstrip("*").str.strip()
    df["npb_left_marker"] = df["raw_player_name"].str.startswith("*")
    df["normalized_player_name"] = df["player_name"].map(normalize_name)
    df["source_league"] = "NPB"
    df["npb_league"] = NPB_TEAMS[team_code]["league"]
    df["team_code"] = team_code
    df["team_name"] = NPB_TEAMS[team_code]["team_name"]
    df["level"] = STAT_TABLES[stat_code]["level"]
    df["stat_type"] = STAT_TABLES[stat_code]["stat_type"]
    df["source_url"] = url
    df["source_confidence"] = 4
    meta["rows"] = len(df)
    meta["data_status"] = "ok"
    return df, meta


def standardize_batting(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["G", "PA", "AB", "R", "H", "2B", "3B", "HR", "TB", "RBI", "SB", "CS", "BB", "SO", "GDP"]:
        if col in out.columns:
            out[col] = numeric(out[col])
    for col in ["AVG", "SLG", "OBP"]:
        if col in out.columns:
            out[col] = numeric(out[col])
    out["ops"] = out.get("OBP", np.nan) + out.get("SLG", np.nan)
    out["iso"] = out.get("SLG", np.nan) - out.get("AVG", np.nan)
    out["bb_pct"] = np.where(out.get("PA", 0).gt(0), out.get("BB", 0) / out.get("PA", 0), np.nan)
    out["so_pct"] = np.where(out.get("PA", 0).gt(0), out.get("SO", 0) / out.get("PA", 0), np.nan)
    out["hr_per_pa"] = np.where(out.get("PA", 0).gt(0), out.get("HR", 0) / out.get("PA", 0), np.nan)
    out["sb_attempts"] = out.get("SB", 0) + out.get("CS", 0)
    out["sb_success_pct"] = np.where(out["sb_attempts"].gt(0), out.get("SB", 0) / out["sb_attempts"], np.nan)
    out["run_kill_proxy"] = out.get("GDP", 0) + out.get("CS", 0)
    out["regular_playing_time_flag"] = out.get("PA", 0).ge(100)
    return out


def standardize_pitching(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["G", "W", "L", "SV", "HLD", "HP", "CG", "SHO", "NWG", "BF", "H", "HR", "BB", "IBB", "HB", "SO", "WP", "BK", "R", "ER"]:
        if col in out.columns:
            out[col] = numeric(out[col])
    out["ip_float"] = out["IP"].map(ip_to_float) if "IP" in out.columns else np.nan
    out["ERA"] = numeric(out["ERA"]) if "ERA" in out.columns else np.nan
    out["whip_calc"] = np.where(out["ip_float"].gt(0), (out.get("H", 0) + out.get("BB", 0)) / out["ip_float"], np.nan)
    out["k_pct"] = np.where(out.get("BF", 0).gt(0), out.get("SO", 0) / out.get("BF", 0), np.nan)
    out["bb_pct"] = np.where(out.get("BF", 0).gt(0), out.get("BB", 0) / out.get("BF", 0), np.nan)
    out["k_minus_bb_pct"] = out["k_pct"] - out["bb_pct"]
    out["k_per_9"] = np.where(out["ip_float"].gt(0), out.get("SO", 0) * 9 / out["ip_float"], np.nan)
    out["bb_per_9"] = np.where(out["ip_float"].gt(0), out.get("BB", 0) * 9 / out["ip_float"], np.nan)
    out["hr_per_9"] = np.where(out["ip_float"].gt(0), out.get("HR", 0) * 9 / out["ip_float"], np.nan)
    out["starter_workload_proxy"] = out.get("IP", "").astype(str).ne("") & out["ip_float"].ge(30)
    out["traffic_command_proxy"] = out["bb_pct"].le(0.08) & out["whip_calc"].le(1.25)
    return out


def collect_all_stats() -> tuple[pd.DataFrame, pd.DataFrame]:
    session = requests.Session()
    frames: list[pd.DataFrame] = []
    inventory: list[dict[str, object]] = []
    for team_code in NPB_TEAMS:
        for stat_code in STAT_TABLES:
            df, meta = collect_stat_table(session, team_code, stat_code)
            inventory.append(meta)
            if df.empty:
                continue
            if STAT_TABLES[stat_code]["stat_type"] == "batting":
                df = standardize_batting(df)
            else:
                df = standardize_pitching(df)
            frames.append(df)
    stats = pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()
    inv = pd.DataFrame(inventory)
    inv["collected_at"] = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    return stats, inv


def build_market_features(stats: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    roster = pd.read_csv(OUT_DIR / "npb_official_roster_2026_v1.csv")
    asian_status = pd.read_csv(OUT_DIR / "asian_quota_market_status_v1.csv")
    nat_cols = [
        "normalized_player_name",
        "team_code",
        "nationality",
        "nationality_source",
        "asian_quota_nationality_gate",
        "foreign_seed_position",
        "foreign_seed_notes",
        "candidate_release_policy",
    ]
    nat = asian_status[asian_status["source_league"].eq("NPB")][nat_cols].drop_duplicates(
        ["team_code", "normalized_player_name"]
    )
    roster_cols = [
        "team_code",
        "team_name",
        "normalized_player_name",
        "roster_no",
        "position_group",
        "position",
        "born",
        "height_cm",
        "weight_kg",
        "throws",
        "bats",
        "person_url",
    ]
    roster = roster[roster_cols].drop_duplicates(["team_code", "normalized_player_name"])
    out = stats.merge(roster, on=["team_code", "team_name", "normalized_player_name"], how="left", suffixes=("", "_roster"))
    out = out.merge(nat, on=["team_code", "normalized_player_name"], how="left")
    out["nationality"] = out["nationality"].fillna("")
    out["nationality_source"] = out["nationality_source"].fillna("not_available_on_npb_official")
    out["asian_quota_nationality_gate"] = out["asian_quota_nationality_gate"].fillna("unknown")
    out["npb_official_stats_attached"] = True

    # Role-level market buckets. These are inventory signals, not recommendations.
    out["npb_market_role_bucket"] = "inventory_only"
    batting = out["stat_type"].eq("batting")
    pitching = out["stat_type"].eq("pitching")
    out.loc[batting & out.get("PA", pd.Series(index=out.index, dtype=float)).fillna(0).ge(100), "npb_market_role_bucket"] = "npb_regular_batter"
    out.loc[batting & out.get("PA", pd.Series(index=out.index, dtype=float)).fillna(0).between(40, 99), "npb_market_role_bucket"] = "npb_part_time_batter"
    out.loc[pitching & out["ip_float"].fillna(0).ge(30), "npb_market_role_bucket"] = "npb_pitcher_30ip_plus"
    out.loc[pitching & out["ip_float"].fillna(0).between(10, 29.999), "npb_market_role_bucket"] = "npb_pitcher_10_30ip"
    out["market_access_bucket"] = "active_npb_under_club_control_low_access"
    out["contract_status_gate"] = "unknown_needs_salary_or_buyout_check"
    out["is_final_recommendation"] = False
    out["candidate_name_release_allowed"] = False

    summary = (
        out.groupby(["level", "stat_type", "npb_league", "npb_market_role_bucket"], dropna=False)
        .agg(
            rows=("normalized_player_name", "count"),
            unique_players=("normalized_player_name", "nunique"),
            known_foreign_seed=("nationality", lambda s: int(s.astype(str).str.len().gt(0).sum())),
            known_asian_quota_pass=("asian_quota_nationality_gate", lambda s: int(s.eq("pass").sum())),
        )
        .reset_index()
        .sort_values(["level", "stat_type", "rows"], ascending=[True, True, False])
    )
    return out, summary


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stats, inventory = collect_all_stats()
    market_features, summary = build_market_features(stats)

    stats_path = OUT_DIR / "npb_official_player_stats_2026_v1.csv"
    inventory_path = OUT_DIR / "npb_official_stats_source_inventory_2026_v1.csv"
    market_path = OUT_DIR / "npb_player_market_features_2026_v1.csv"
    summary_path = OUT_DIR / "npb_market_depth_summary_2026_v1.csv"
    stats.to_csv(stats_path, index=False)
    inventory.to_csv(inventory_path, index=False)
    market_features.to_csv(market_path, index=False)
    summary.to_csv(summary_path, index=False)

    manifest = {
        "collected_at": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "source": "NPB official English player stats",
        "url_template": STAT_URL,
        "rows": {
            "raw_stats": len(stats),
            "source_inventory": len(inventory),
            "market_features": len(market_features),
            "summary": len(summary),
        },
        "caveats": [
            "NPB official stats do not expose salary, buyout, contract length, or universal nationality fields.",
            "Candidate rows remain market inventory only and are not recommendations.",
        ],
    }
    (RAW_DIR / "npb_official_stats_2026_manifest_v1.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"wrote {stats_path} ({len(stats)} rows)")
    print(f"wrote {inventory_path} ({len(inventory)} rows)")
    print(f"wrote {market_path} ({len(market_features)} rows)")
    print(f"wrote {summary_path} ({len(summary)} rows)")


if __name__ == "__main__":
    main()
