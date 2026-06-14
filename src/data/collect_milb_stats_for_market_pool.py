#!/usr/bin/env python3
"""Collect MiLB year-by-year stats for transaction-screened market candidates.

This adds a role/level continuity layer. It is not a final ranking source by
itself; it tells us whether a player is currently working at AAA/AA, whether a
pitcher is stretched out, and whether a hitter is getting enough recent PA.
"""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import certifi
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"
RAW_DIR = ROOT / "data/raw/mlb/milb_stats"
MARKET_STATUS = OUT_DIR / "mlb_replacement_market_status_v1.csv"
BASE_URL = "https://statsapi.mlb.com/api/v1"

DEFAULT_SPORTS = {
    11: "AAA",
    12: "AA",
    13: "High-A",
    14: "Single-A",
    16: "Rookie",
}


def snake_case(value: str) -> str:
    out = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", str(value))
    out = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", out)
    out = re.sub(r"[^A-Za-z0-9]+", "_", out)
    return out.strip("_").lower()


def selected_candidates(market: pd.DataFrame, scope: str) -> pd.DataFrame:
    out = market.copy()
    out["player_id"] = pd.to_numeric(out["player_id"], errors="coerce").astype("Int64")
    out["stat_group"] = "hitting"
    out.loc[out["slot"].eq("regular_foreign_pitcher"), "stat_group"] = "pitching"

    if scope == "all":
        mask = out["player_id"].notna()
    elif scope == "research_only":
        mask = out["candidate_release_policy_v2"].eq("research_lead_only_manual_check_required")
    elif scope == "research_plus_medical":
        mask = out["candidate_release_policy_v2"].isin(
            ["research_lead_only_manual_check_required", "hold_medical_context_required"]
        )
    else:
        raise ValueError(f"unknown scope: {scope}")

    cols = [
        "player_id",
        "player_name",
        "slot",
        "stat_group",
        "candidate_release_policy_v2",
        "market_availability_bucket",
        "market_access_score_v2",
        "final_priority_score",
    ]
    return (
        out.loc[mask, cols]
        .dropna(subset=["player_id"])
        .drop_duplicates(["player_id", "stat_group"])
        .sort_values(["slot", "player_name"])
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


def flatten_payload(result: dict, player_lookup: dict[tuple[int, str], dict], collected_at: str) -> tuple[list[dict], dict]:
    key = (int(result["player_id"]), result["stat_group"])
    player = player_lookup.get(key, {})
    rows: list[dict] = []
    stats = result.get("payload", {}).get("stats") or []
    split_count = 0
    for stat_block in stats:
        for split in stat_block.get("splits", []) or []:
            split_count += 1
            stat = split.get("stat") or {}
            team = split.get("team") or {}
            league = split.get("league") or {}
            sport = split.get("sport") or {}
            row = {
                "player_id": result["player_id"],
                "player_name": player.get("player_name"),
                "slot": player.get("slot"),
                "stat_group": result["stat_group"],
                "market_availability_bucket": player.get("market_availability_bucket"),
                "candidate_release_policy_v2": player.get("candidate_release_policy_v2"),
                "market_access_score_v2": player.get("market_access_score_v2"),
                "final_priority_score": player.get("final_priority_score"),
                "season": split.get("season"),
                "game_type": split.get("gameType"),
                "sport_id": sport.get("id") or result["sport_id"],
                "sport_name": sport.get("name"),
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
        "player_name": player.get("player_name"),
        "stat_group": result["stat_group"],
        "sport_id": result["sport_id"],
        "sport_level": DEFAULT_SPORTS.get(result["sport_id"], str(result["sport_id"])),
        "status_code": result.get("status_code"),
        "split_count": split_count,
        "error": result.get("error", ""),
        "source_url": result.get("url"),
        "collected_at": collected_at,
    }
    return rows, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["all", "research_only", "research_plus_medical"], default="research_plus_medical")
    parser.add_argument("--sport-ids", default="11,12,13,14,16")
    parser.add_argument("--max-workers", type=int, default=12)
    parser.add_argument("--limit", type=int, default=0, help="Optional player limit for debugging.")
    args = parser.parse_args()

    market = pd.read_csv(MARKET_STATUS)
    candidates = selected_candidates(market, args.scope)
    if args.limit > 0:
        candidates = candidates.head(args.limit).copy()
    sport_ids = [int(value.strip()) for value in args.sport_ids.split(",") if value.strip()]
    tasks = [
        (int(row.player_id), row.stat_group, sport_id)
        for row in candidates.itertuples(index=False)
        for sport_id in sport_ids
    ]
    player_lookup = {
        (int(row.player_id), row.stat_group): row._asdict()
        for row in candidates.itertuples(index=False)
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    compact_ts = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d_%H%M%S")
    raw_jsonl_path = RAW_DIR / f"milb_stats_{args.scope}_{compact_ts}.jsonl"

    all_rows: list[dict] = []
    audits: list[dict] = []
    with raw_jsonl_path.open("w", encoding="utf-8") as handle:
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = {
                executor.submit(fetch_stats, player_id, stat_group, sport_id): (player_id, stat_group, sport_id)
                for player_id, stat_group, sport_id in tasks
            }
            for index, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                rows, audit = flatten_payload(result, player_lookup, collected_at)
                all_rows.extend(rows)
                audits.append(audit)
                if index % 250 == 0 or index == len(futures):
                    print(f"completed {index}/{len(futures)} requests; rows={len(all_rows)}")

    suffix = f"{args.scope}_v1"
    stats_path = OUT_DIR / f"milb_market_pool_stats_{suffix}.csv"
    audit_path = OUT_DIR / f"milb_market_pool_stats_request_audit_{suffix}.csv"
    latest_stats_path = OUT_DIR / "milb_market_pool_stats_latest.csv"
    latest_audit_path = OUT_DIR / "milb_market_pool_stats_request_audit_latest.csv"

    stats_df = pd.DataFrame(all_rows)
    audit_df = pd.DataFrame(audits)
    stats_df.to_csv(stats_path, index=False)
    audit_df.to_csv(audit_path, index=False)
    stats_df.to_csv(latest_stats_path, index=False)
    audit_df.to_csv(latest_audit_path, index=False)

    manifest = {
        "scope": args.scope,
        "candidate_rows": len(candidates),
        "request_count": len(tasks),
        "stat_rows": len(stats_df),
        "audit_rows": len(audit_df),
        "sport_ids": sport_ids,
        "raw_jsonl_path": str(raw_jsonl_path),
        "collected_at": collected_at,
    }
    manifest_path = OUT_DIR / "milb_market_pool_stats_manifest_v1.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"wrote {stats_path} ({len(stats_df)} rows)")
    print(f"wrote {audit_path} ({len(audit_df)} rows)")
    print(f"wrote {manifest_path}")
    print(f"raw jsonl: {raw_jsonl_path}")


if __name__ == "__main__":
    main()
