#!/usr/bin/env python3
"""Backfill recent KBO foreign-player MiLB features from MLB StatsAPI.

This is historical training-data work for Layer 2/4. It does not touch the
current candidate market and does not release candidate recommendations.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from zoneinfo import ZoneInfo

import certifi
import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.collect_historical_kbo_milb_stats import (  # noqa: E402
    SPORTS,
    build_prearrival_features,
    fetch_stats,
    flatten_payload,
)


OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
RAW_DIR = PROJECT_ROOT / "data/raw/mlb/layer2_backfill_milb"
BACKFILL_QUEUE = OUTPUT_DIR / "layer2_historical_backfill_queue_v0_1.csv"
LABELS = PROJECT_ROOT / "data/processed/kbo/kbo_foreign_player_season_labels_v0_1.csv"

BASE_URL = "https://statsapi.mlb.com/api/v1"
RELEASE_POLICY = "layer2_backfill_historical_training_only_no_current_candidate_release"
SUFFIX_WORDS = {"jr", "junior", "sr", "senior", "ii", "iii", "iv"}

QUERY_ALIASES = {
    "andrew james anderson": ["Drew Anderson"],
    "ariel bolivar jurado agrazal": ["Ariel Jurado"],
    "brian o grady": ["Brian O'Grady"],
    "cristopher crisostomo mercedes": ["C.C. Mercedes", "Cristopher Mercedes"],
    "dylan michael file": ["Dylan File"],
    "guillermo heredia molina": ["Guillermo Heredia"],
    "jose manuel pirela": ["Jose Pirela"],
    "kirkland kirk mccarty": ["Kirk McCarty"],
    "matthew glen davidson": ["Matt Davidson"],
    "raul alcantara": ["Raul Alcantara"],
    "socrates orel brito": ["Socrates Brito"],
    "thomas edward pannone jr": ["Thomas Pannone"],
    "vincent john velasquez": ["Vince Velasquez"],
    "william chandler crowe": ["Wil Crowe"],
    "william enrique cuevas osorio": ["William Cuevas"],
    "yasiel puig valdes": ["Yasiel Puig"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backfill-queue", default=str(BACKFILL_QUEUE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--labels", default=str(LABELS.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    parser.add_argument("--max-workers", type=int, default=12)
    return parser.parse_args()


def normalize_name(value: object) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z ]+", " ", text).lower()
    tokens = [token for token in text.split() if token not in SUFFIX_WORDS]
    return " ".join(tokens)


def query_variants(value: object) -> list[str]:
    base = normalize_name(value)
    if not base:
        return []
    tokens = base.split()
    variants: list[str] = []
    variants.extend(QUERY_ALIASES.get(base, []))
    variants.append(base)
    if len(tokens) >= 2:
        variants.append(f"{tokens[0]} {tokens[1]}")
        variants.append(f"{tokens[0]} {tokens[-1]}")
    if len(tokens) >= 3:
        variants.append(f"{tokens[0]} {tokens[1]} {tokens[-1]}")

    seen: list[str] = []
    for variant in variants:
        cleaned = " ".join(str(variant).strip().split())
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


def role_matches(role: str, person: dict) -> bool:
    abbreviation = (person.get("primaryPosition") or {}).get("abbreviation", "")
    if role == "pitcher":
        return abbreviation == "P"
    return abbreviation != "P"


def birth_year(person: dict) -> int:
    date = str(person.get("birthDate") or "")
    match = re.match(r"(\d{4})", date)
    return int(match.group(1)) if match else 9999


def candidate_score(source_name: object, query: str, role: str, person: dict) -> tuple[float, float, bool]:
    full_name = normalize_name(person.get("fullName"))
    query_norm = normalize_name(query)
    source_norm = normalize_name(source_name)
    string_score = max(
        SequenceMatcher(None, query_norm, full_name).ratio(),
        SequenceMatcher(None, source_norm, full_name).ratio(),
    )
    query_tokens = query_norm.split()
    full_tokens = full_name.split()
    if len(query_tokens) >= 2 and len(full_tokens) >= 2 and query_tokens[0] == full_tokens[0] and query_tokens[-1] == full_tokens[-1]:
        string_score = max(string_score, 0.99)
    role_ok = role_matches(role, person)
    year = birth_year(person)
    adjusted_score = string_score
    adjusted_score += 0.08 if role_ok else -0.20
    adjusted_score += 0.04 if person.get("mlbDebutDate") else 0.0
    if year < 1975:
        adjusted_score -= 0.50
    elif 1975 <= year <= 2005:
        adjusted_score += 0.02
    elif year > 2005:
        adjusted_score -= 0.08
    return adjusted_score, string_score, role_ok


def search_people(query: str) -> list[dict]:
    url = f"{BASE_URL}/people/search?names={urllib.parse.quote(query)}"
    try:
        response = requests.get(url, timeout=20, verify=certifi.where())
        payload = response.json() if response.content else {}
        return payload.get("people", []) if isinstance(payload, dict) else []
    except Exception:
        return []
    finally:
        time.sleep(0.03)


def best_match(row: pd.Series, cache: dict[str, list[dict]]) -> dict[str, object]:
    source_name = row.get("player_name_en", "")
    role = str(row.get("role_model_family", ""))
    variants = query_variants(source_name)
    searched: list[str] = []
    best_key: tuple[float, float, int] | None = None
    best: tuple[float, bool, str, dict] | None = None
    for variant in variants:
        searched.append(variant)
        if variant not in cache:
            cache[variant] = search_people(variant)
        for person in cache[variant]:
            adjusted, string_score, role_ok = candidate_score(source_name, variant, role, person)
            candidate_key = (adjusted, string_score, int(role_ok))
            if best_key is None or candidate_key > best_key:
                best_key = candidate_key
                best = (string_score, role_ok, variant, person)

    if best is None:
        return {
            "searched_variants": "|".join(searched),
            "matched_player_id": pd.NA,
            "matched_full_name": "",
            "matched_position": "",
            "matched_birth_date": "",
            "matched_mlb_debut_date": "",
            "match_variant": "",
            "match_string_score": pd.NA,
            "role_match": False,
            "match_status": "unmatched_manual_lookup_required",
        }

    string_score, role_ok, variant, person = best
    high_confidence = string_score >= 0.97 and role_ok
    needs_review = string_score >= 0.90 and role_ok
    status = "matched_high_confidence" if high_confidence else "matched_needs_manual_review" if needs_review else "unmatched_manual_lookup_required"
    return {
        "searched_variants": "|".join(searched),
        "matched_player_id": person.get("id", pd.NA),
        "matched_full_name": person.get("fullName", ""),
        "matched_position": (person.get("primaryPosition") or {}).get("abbreviation", ""),
        "matched_birth_date": person.get("birthDate", ""),
        "matched_mlb_debut_date": person.get("mlbDebutDate", ""),
        "match_variant": variant,
        "match_string_score": round(float(string_score), 4),
        "role_match": bool(role_ok),
        "match_status": status,
    }


def load_backfill_pool(queue_path: Path, labels_path: Path) -> pd.DataFrame:
    queue = pd.read_csv(queue_path)
    labels = pd.read_csv(labels_path)
    label_cols = [
        "season",
        "player_key",
        "player_name",
        "player_name_en",
        "kbo_team",
        "role_group",
        "source_confidence_1_5",
    ]
    labels = labels[[col for col in label_cols if col in labels.columns]].drop_duplicates(["season", "player_key"])
    base = queue.drop_duplicates(["season", "player_key"]).merge(labels, on=["season", "player_key"], how="left", suffixes=("", "_label"))
    if "player_name_label" in base.columns:
        base["player_name"] = base["player_name"].fillna(base["player_name_label"])
    if "kbo_team_label" in base.columns:
        base["kbo_team"] = base["kbo_team"].fillna(base["kbo_team_label"])
    return base


def build_name_match_audit(pool: pd.DataFrame) -> pd.DataFrame:
    cache: dict[str, list[dict]] = {}
    rows: list[dict[str, object]] = []
    for _, row in pool.iterrows():
        match = best_match(row, cache)
        rows.append({**row.to_dict(), **match})
    out = pd.DataFrame(rows)
    out["candidate_release_allowed"] = False
    out["release_policy"] = RELEASE_POLICY
    return out


def build_fetch_pool(matches: pd.DataFrame) -> pd.DataFrame:
    matched = matches[matches["match_status"].eq("matched_high_confidence")].copy()
    matched["player_id"] = pd.to_numeric(matched["matched_player_id"], errors="coerce").astype("Int64")
    matched = matched.dropna(subset=["player_id"])
    matched["stat_group"] = matched["role_model_family"].map({"pitcher": "pitching", "hitter": "hitting"})
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
    return matched[cols].drop_duplicates(["season", "player_key", "player_id", "stat_group"]).reset_index(drop=True)


def collect_stats(pool: pd.DataFrame, max_workers: int, collected_at: str, raw_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    tasks = [
        (int(row.player_id), row.stat_group, sport_id)
        for row in pool.drop_duplicates(["player_id", "stat_group"]).itertuples(index=False)
        for sport_id in SPORTS
    ]
    lookup: dict[tuple[int, str], list[dict]] = {}
    for row in pool.itertuples(index=False):
        lookup.setdefault((int(row.player_id), row.stat_group), []).append(row._asdict())

    rows: list[dict] = []
    audits: list[dict] = []
    with raw_path.open("w", encoding="utf-8") as handle:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
                if index % 50 == 0 or index == len(futures):
                    print(f"completed {index}/{len(futures)} backfill requests; rows={len(rows)}")
    return pd.DataFrame(rows), pd.DataFrame(audits)


def build_resolution_matrix(queue: pd.DataFrame, matches: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    feature_cols = [
        "season",
        "player_key",
        "has_pre_kbo_milb",
        "pre_kbo_milb_rows",
        "pre_kbo_milb_latest_year",
        "pre_kbo_milb_recent_rows",
        "pre_kbo_milb_highest_level_score",
        "pre_kbo_aaa_rows",
        "pre_kbo_aa_rows",
        "pre_kbo_milb_pa",
        "pre_kbo_milb_ops",
        "pre_kbo_milb_obp",
        "pre_kbo_milb_slg",
        "pre_kbo_milb_k_pct",
        "pre_kbo_milb_bb_pct",
        "pre_kbo_milb_ip",
        "pre_kbo_milb_games_started",
        "pre_kbo_milb_k9",
        "pre_kbo_milb_bb9",
        "pre_kbo_milb_hr9",
        "pre_kbo_milb_era",
        "pre_kbo_milb_whip",
    ]
    match_cols = [
        "season",
        "player_key",
        "player_name_en",
        "matched_player_id",
        "matched_full_name",
        "matched_position",
        "matched_birth_date",
        "matched_mlb_debut_date",
        "match_variant",
        "match_string_score",
        "match_status",
    ]
    out = queue.drop_duplicates(["season", "player_key"]).merge(matches[match_cols], on=["season", "player_key"], how="left")
    if not features.empty:
        out = out.merge(features[[col for col in feature_cols if col in features.columns]], on=["season", "player_key"], how="left")
    else:
        out["has_pre_kbo_milb"] = False
    out["has_pre_kbo_milb"] = out["has_pre_kbo_milb"].fillna(False)
    out["backfill_resolution_status"] = "unresolved"
    out.loc[out["match_status"].eq("unmatched_manual_lookup_required"), "backfill_resolution_status"] = "manual_player_id_lookup_required"
    out.loc[out["match_status"].eq("matched_needs_manual_review"), "backfill_resolution_status"] = "matched_needs_manual_review"
    out.loc[out["match_status"].eq("matched_high_confidence") & ~out["has_pre_kbo_milb"], "backfill_resolution_status"] = "matched_no_pre_kbo_milb_rows"
    out.loc[out["match_status"].eq("matched_high_confidence") & out["has_pre_kbo_milb"], "backfill_resolution_status"] = "statsapi_backfilled_model_ready"
    out["candidate_release_allowed"] = False
    out["release_policy"] = RELEASE_POLICY
    return out.sort_values(["backfill_resolution_status", "season", "player_key"])


def build_gate_audit(queue: pd.DataFrame, matches: pd.DataFrame, resolution: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "gate": "L2B1",
                "layer": "KBO foreign-player success/failure archetype mining",
                "check": "recent_backfill_queue_preserved",
                "pass_rows": len(resolution),
                "total_rows": len(queue.drop_duplicates(["season", "player_key"])),
                "status": "pass",
                "blocking_gap": "Recent 2023-2025 backfill queue is now row-addressable.",
            },
            {
                "gate": "L2B2",
                "layer": "KBO foreign-player success/failure archetype mining",
                "check": "statsapi_name_matching",
                "pass_rows": int(matches["match_status"].eq("matched_high_confidence").sum()),
                "total_rows": len(matches),
                "status": "pass_visible_gap",
                "blocking_gap": "Unmatched or ambiguous historical names still need manual player-id lookup.",
            },
            {
                "gate": "L2B3",
                "layer": "KBO foreign-player success/failure archetype mining",
                "check": "pre_kbo_milb_features_backfilled",
                "pass_rows": int(resolution["backfill_resolution_status"].eq("statsapi_backfilled_model_ready").sum()),
                "total_rows": len(resolution),
                "status": "pass_visible_gap",
                "blocking_gap": "Some matched historical players have no StatsAPI MiLB rows before KBO arrival.",
            },
            {
                "gate": "LOCK",
                "layer": "Release policy",
                "check": "no_current_candidate_release",
                "pass_rows": int(
                    matches["candidate_release_allowed"].eq(False).all()
                    and resolution["candidate_release_allowed"].eq(False).all()
                ),
                "total_rows": 1,
                "status": "pass",
                "blocking_gap": "Only historical KBO training rows are exposed; current candidate names/ranks/scores remain locked.",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    collected_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    raw_path = RAW_DIR / f"layer2_backfill_milb_statsapi_{datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d_%H%M%S')}.jsonl"

    queue_path = PROJECT_ROOT / args.backfill_queue
    labels_path = PROJECT_ROOT / args.labels
    queue = pd.read_csv(queue_path)
    pool = load_backfill_pool(queue_path, labels_path)
    matches = build_name_match_audit(pool)
    fetch_pool = build_fetch_pool(matches)
    stats, request_audit = collect_stats(fetch_pool, args.max_workers, collected_at, raw_path) if not fetch_pool.empty else (pd.DataFrame(), pd.DataFrame())
    features = build_prearrival_features(stats, fetch_pool) if not fetch_pool.empty else fetch_pool.assign(has_pre_kbo_milb=False)
    resolution = build_resolution_matrix(queue, matches, features)
    gate_audit = build_gate_audit(queue, matches, resolution)

    matches.to_csv(OUTPUT_DIR / f"layer2_backfill_statsapi_name_match_audit_{suffix}.csv", index=False)
    stats.to_csv(OUTPUT_DIR / f"layer2_backfill_statsapi_milb_stats_{suffix}.csv", index=False)
    request_audit.to_csv(OUTPUT_DIR / f"layer2_backfill_statsapi_request_audit_{suffix}.csv", index=False)
    features.to_csv(OUTPUT_DIR / f"layer2_backfill_statsapi_milb_features_{suffix}.csv", index=False)
    resolution.to_csv(OUTPUT_DIR / f"layer2_backfill_resolution_matrix_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"layer2_backfill_statsapi_gate_audit_{suffix}.csv", index=False)

    manifest = {
        "queue_rows": int(len(queue.drop_duplicates(["season", "player_key"]))),
        "match_rows": int(len(matches)),
        "high_confidence_match_rows": int(matches["match_status"].eq("matched_high_confidence").sum()),
        "fetch_pool_rows": int(len(fetch_pool)),
        "request_rows": int(len(request_audit)),
        "stats_rows": int(len(stats)),
        "feature_rows": int(len(features)),
        "model_ready_backfill_rows": int(resolution["backfill_resolution_status"].eq("statsapi_backfilled_model_ready").sum()),
        "raw_jsonl_path": str(raw_path),
        "collected_at": collected_at,
        "release_policy": RELEASE_POLICY,
    }
    (OUTPUT_DIR / f"layer2_backfill_statsapi_manifest_{suffix}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(matches["match_status"].value_counts(dropna=False).to_string())
    print(resolution["backfill_resolution_status"].value_counts(dropna=False).to_string())
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
