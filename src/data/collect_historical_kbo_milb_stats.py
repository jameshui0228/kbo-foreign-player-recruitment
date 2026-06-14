#!/usr/bin/env python3
"""Collect pre-KBO MiLB history for historical foreign-player labels.

This backfills the model side, not the current candidate side. The goal is to
make KBO translation/failure-risk training less dependent on MLB Statcast-only
pre-arrival features.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import certifi
import numpy as np
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"
RAW_DIR = ROOT / "data/raw/mlb/milb_stats"
TRANSLATION_MART = OUT_DIR / "kbo_translation_feature_mart_v0_1.csv"
BASE_URL = "https://statsapi.mlb.com/api/v1"
SPORTS = {11: "AAA", 12: "AA", 13: "High-A", 14: "Single-A", 16: "Rookie"}


def snake_case(value: str) -> str:
    out = []
    previous_lower = False
    for char in str(value):
        if char.isupper() and previous_lower:
            out.append("_")
        if char.isalnum():
            out.append(char.lower())
            previous_lower = char.islower() or char.isdigit()
        else:
            if out and out[-1] != "_":
                out.append("_")
            previous_lower = False
    return "".join(out).strip("_")


def to_num(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def ip_to_outs(value: object) -> float:
    if pd.isna(value):
        return np.nan
    text = str(value).strip()
    if not text:
        return np.nan
    if "." not in text:
        return float(pd.to_numeric(text, errors="coerce")) * 3
    whole, frac = text.split(".", 1)
    whole_outs = int(float(whole)) * 3 if whole else 0
    extra_outs = int(frac[:1]) if frac[:1] in {"0", "1", "2"} else 0
    return float(whole_outs + extra_outs)


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    numeric = to_num(values)
    weights = to_num(weights).fillna(0)
    mask = numeric.notna() & weights.gt(0)
    if not mask.any():
        return float(numeric.mean()) if numeric.notna().any() else np.nan
    return float(np.average(numeric[mask], weights=weights[mask]))


def historical_pool() -> pd.DataFrame:
    mart = pd.read_csv(TRANSLATION_MART)
    out = mart[mart["matched_to_savant"].fillna(False)].copy()
    out["player_id"] = pd.to_numeric(out["matched_savant_player_id"], errors="coerce").astype("Int64")
    out["stat_group"] = np.where(out["role_model_family"].eq("pitcher"), "pitching", "hitting")
    cols = [
        "season",
        "player_key",
        "player_name",
        "player_name_en",
        "kbo_team",
        "role_model_family",
        "stat_group",
        "player_id",
        "success",
        "failure",
    ]
    return (
        out[cols]
        .dropna(subset=["player_id"])
        .drop_duplicates(["season", "player_key", "player_id", "stat_group"])
        .sort_values(["season", "role_model_family", "player_name"])
        .reset_index(drop=True)
    )


def fetch_stats(player_id: int, stat_group: str, sport_id: int) -> dict:
    params = {"stats": "yearByYear", "group": stat_group, "sportId": sport_id}
    url = f"{BASE_URL}/people/{player_id}/stats"
    try:
        response = requests.get(url, params=params, timeout=30, verify=certifi.where())
        payload = response.json() if response.content else {}
        return {
            "player_id": player_id,
            "stat_group": stat_group,
            "sport_id": sport_id,
            "status_code": response.status_code,
            "url": response.url,
            "payload": payload,
            "error": "",
        }
    except Exception as exc:  # pragma: no cover - network defensive path
        return {
            "player_id": player_id,
            "stat_group": stat_group,
            "sport_id": sport_id,
            "status_code": None,
            "url": url,
            "payload": {},
            "error": f"{type(exc).__name__}: {exc}",
        }


def flatten_payload(result: dict, player_lookup: dict[tuple[int, str], list[dict]], collected_at: str) -> tuple[list[dict], dict]:
    player_rows = player_lookup.get((int(result["player_id"]), result["stat_group"]), [])
    rows: list[dict] = []
    split_count = 0
    for stat_block in result.get("payload", {}).get("stats") or []:
        for split in stat_block.get("splits", []) or []:
            split_count += 1
            stat = split.get("stat") or {}
            team = split.get("team") or {}
            league = split.get("league") or {}
            sport = split.get("sport") or {}
            for player in player_rows:
                row = {
                    **player,
                    "source_player_id": result["player_id"],
                    "milb_stat_group": result["stat_group"],
                    "milb_season": split.get("season"),
                    "game_type": split.get("gameType"),
                    "sport_id": sport.get("id") or result["sport_id"],
                    "sport_level": SPORTS.get(result["sport_id"], str(result["sport_id"])),
                    "sport_abbreviation": sport.get("abbreviation"),
                    "team_id": team.get("id"),
                    "team_name": team.get("name"),
                    "league_id": league.get("id"),
                    "league_name": league.get("name"),
                    "source_url": result.get("url"),
                    "collected_at": collected_at,
                }
                for name, value in stat.items():
                    row[snake_case(name)] = value
                rows.append(row)

    audit = {
        "player_id": result["player_id"],
        "stat_group": result["stat_group"],
        "sport_id": result["sport_id"],
        "sport_level": SPORTS.get(result["sport_id"], str(result["sport_id"])),
        "status_code": result.get("status_code"),
        "split_count": split_count,
        "error": result.get("error", ""),
        "source_url": result.get("url"),
        "collected_at": collected_at,
    }
    return rows, audit


def prepare_stats(stats: pd.DataFrame) -> pd.DataFrame:
    out = stats.copy()
    out["season"] = to_num(out["season"]).astype("Int64")
    out["milb_season"] = np.floor(to_num(out["milb_season"])).astype("Int64")
    out["sport_id"] = to_num(out["sport_id"]).astype("Int64")
    out["level_score"] = out["sport_id"].map({11: 100, 12: 80, 13: 60, 14: 45, 16: 25}).fillna(0)
    out["pre_kbo_milb"] = out["milb_season"].lt(out["season"])
    out["pre_kbo_recent_2yr"] = out["milb_season"].between(out["season"] - 2, out["season"] - 1, inclusive="both")
    for col in [
        "plate_appearances",
        "home_runs",
        "strike_outs",
        "base_on_balls",
        "ops",
        "obp",
        "slg",
        "avg",
        "games_played",
        "games_started",
        "innings_pitched",
        "strikeouts_per9_inn",
        "walks_per9_inn",
        "home_runs_per9",
        "strikeout_walk_ratio",
        "era",
        "whip",
        "batters_faced",
    ]:
        if col not in out.columns:
            out[col] = np.nan
        if col != "innings_pitched":
            out[col] = to_num(out[col])
    out["innings_outs"] = out["innings_pitched"].map(ip_to_outs)
    return out


def build_prearrival_features(stats: pd.DataFrame, pool: pd.DataFrame) -> pd.DataFrame:
    if stats.empty:
        return pool.assign(has_pre_kbo_milb=False)
    rows = prepare_stats(stats)
    rows = rows[rows["pre_kbo_milb"]].copy()
    feature_rows: list[dict] = []
    keys = ["season", "player_key", "source_player_id", "milb_stat_group"]
    for key, group in rows.groupby(keys, dropna=False):
        season, player_key, player_id, stat_group = key
        recent = group[group["pre_kbo_recent_2yr"]].copy()
        basis = recent if not recent.empty else group
        latest_year = group["milb_season"].max()
        aaa = basis[basis["sport_id"].eq(11)]
        aa = basis[basis["sport_id"].eq(12)]
        row = {
            "season": int(season),
            "player_key": player_key,
            "source_player_id": int(player_id),
            "milb_stat_group": stat_group,
            "has_pre_kbo_milb": True,
            "pre_kbo_milb_rows": int(len(group)),
            "pre_kbo_milb_latest_year": int(latest_year) if pd.notna(latest_year) else np.nan,
            "pre_kbo_milb_recent_rows": int(len(recent)),
            "pre_kbo_milb_highest_level_score": float(group["level_score"].max()),
            "pre_kbo_recent_highest_level_score": float(basis["level_score"].max()),
            "pre_kbo_aaa_rows": int(len(aaa)),
            "pre_kbo_aa_rows": int(len(aa)),
        }
        if stat_group == "hitting":
            pa = basis["plate_appearances"].sum(min_count=1)
            row.update(
                {
                    "pre_kbo_milb_pa": pa,
                    "pre_kbo_milb_hr": basis["home_runs"].sum(min_count=1),
                    "pre_kbo_milb_ops": weighted_mean(basis["ops"], basis["plate_appearances"]),
                    "pre_kbo_milb_obp": weighted_mean(basis["obp"], basis["plate_appearances"]),
                    "pre_kbo_milb_slg": weighted_mean(basis["slg"], basis["plate_appearances"]),
                    "pre_kbo_milb_k_pct": basis["strike_outs"].sum(min_count=1) / pa if pd.notna(pa) and pa > 0 else np.nan,
                    "pre_kbo_milb_bb_pct": basis["base_on_balls"].sum(min_count=1) / pa if pd.notna(pa) and pa > 0 else np.nan,
                }
            )
        else:
            ip = basis["innings_outs"].sum(min_count=1) / 3
            bf = basis["batters_faced"].sum(min_count=1)
            row.update(
                {
                    "pre_kbo_milb_ip": ip,
                    "pre_kbo_milb_games": basis["games_played"].sum(min_count=1),
                    "pre_kbo_milb_games_started": basis["games_started"].sum(min_count=1),
                    "pre_kbo_milb_k9": basis["strike_outs"].sum(min_count=1) * 9 / ip if pd.notna(ip) and ip > 0 else np.nan,
                    "pre_kbo_milb_bb9": basis["base_on_balls"].sum(min_count=1) * 9 / ip if pd.notna(ip) and ip > 0 else np.nan,
                    "pre_kbo_milb_hr9": basis["home_runs"].sum(min_count=1) * 9 / ip if pd.notna(ip) and ip > 0 else np.nan,
                    "pre_kbo_milb_k_pct": basis["strike_outs"].sum(min_count=1) / bf if pd.notna(bf) and bf > 0 else np.nan,
                    "pre_kbo_milb_bb_pct": basis["base_on_balls"].sum(min_count=1) / bf if pd.notna(bf) and bf > 0 else np.nan,
                    "pre_kbo_milb_era": weighted_mean(basis["era"], basis["innings_outs"]),
                    "pre_kbo_milb_whip": weighted_mean(basis["whip"], basis["innings_outs"]),
                }
            )
        feature_rows.append(row)
    features = pd.DataFrame(feature_rows)
    merged = pool.merge(
        features,
        left_on=["season", "player_key", "player_id", "stat_group"],
        right_on=["season", "player_key", "source_player_id", "milb_stat_group"],
        how="left",
    )
    merged["has_pre_kbo_milb"] = merged["has_pre_kbo_milb"].fillna(False)
    return merged


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pool = historical_pool()
    tasks = [
        (int(row.player_id), row.stat_group, sport_id)
        for row in pool.drop_duplicates(["player_id", "stat_group"]).itertuples(index=False)
        for sport_id in SPORTS
    ]
    lookup: dict[tuple[int, str], list[dict]] = {}
    for row in pool.itertuples(index=False):
        lookup.setdefault((int(row.player_id), row.stat_group), []).append(row._asdict())

    collected_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    compact_ts = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S")
    raw_path = RAW_DIR / f"historical_kbo_milb_stats_{compact_ts}.jsonl"
    rows: list[dict] = []
    audits: list[dict] = []
    with raw_path.open("w", encoding="utf-8") as handle:
        with ThreadPoolExecutor(max_workers=12) as executor:
            futures = {
                executor.submit(fetch_stats, player_id, stat_group, sport_id): (player_id, stat_group, sport_id)
                for player_id, stat_group, sport_id in tasks
            }
            for index, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                flat_rows, audit = flatten_payload(result, lookup, collected_at)
                rows.extend(flat_rows)
                audits.append(audit)
                if index % 100 == 0 or index == len(futures):
                    print(f"completed {index}/{len(futures)} requests; rows={len(rows)}")

    stats = pd.DataFrame(rows)
    audit = pd.DataFrame(audits)
    features = build_prearrival_features(stats, pool)

    stats_path = OUT_DIR / "historical_kbo_prearrival_milb_stats_v1.csv"
    audit_path = OUT_DIR / "historical_kbo_prearrival_milb_request_audit_v1.csv"
    feature_path = OUT_DIR / "historical_kbo_prearrival_milb_features_v1.csv"
    stats.to_csv(stats_path, index=False)
    audit.to_csv(audit_path, index=False)
    features.to_csv(feature_path, index=False)
    manifest = {
        "historical_pool_rows": len(pool),
        "unique_player_stat_groups": int(pool.drop_duplicates(["player_id", "stat_group"]).shape[0]),
        "request_count": len(tasks),
        "stat_rows": len(stats),
        "audit_rows": len(audit),
        "feature_rows": len(features),
        "pre_kbo_milb_feature_rows": int(features["has_pre_kbo_milb"].sum()),
        "raw_jsonl_path": str(raw_path),
        "collected_at": collected_at,
    }
    manifest_path = OUT_DIR / "historical_kbo_prearrival_milb_manifest_v1.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"wrote {stats_path}")
    print(f"wrote {audit_path}")
    print(f"wrote {feature_path}")


if __name__ == "__main__":
    main()
