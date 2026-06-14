#!/usr/bin/env python3
"""Collect official MLB transaction feed for replacement-market screening.

This table is a market-access layer, not a recommendation engine. It tells us
which current MLB/MiLB players have recent signals such as release, DFA,
outright assignment, minor-league signing, injured list, or rehab assignment.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import certifi
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://statsapi.mlb.com/api/v1/transactions"


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def nested_name(payload: dict, key: str) -> tuple[object, object]:
    value = payload.get(key) or {}
    return value.get("id"), value.get("name")


def bool_flag(blob: str, *patterns: str) -> bool:
    return any(re.search(pattern, blob, flags=re.IGNORECASE) for pattern in patterns)


def flatten_transaction(transaction: dict, source_url: str, collected_at: str) -> dict:
    person = transaction.get("person") or {}
    from_team_id, from_team_name = nested_name(transaction, "fromTeam")
    to_team_id, to_team_name = nested_name(transaction, "toTeam")
    type_code = normalize_text(transaction.get("typeCode"))
    type_desc = normalize_text(transaction.get("typeDesc"))
    description = normalize_text(transaction.get("description"))
    blob = f"{type_code} {type_desc} {description}".lower()

    return {
        "transaction_id": transaction.get("id"),
        "player_id": person.get("id"),
        "player_name": person.get("fullName"),
        "from_team_id": from_team_id,
        "from_team_name": from_team_name,
        "to_team_id": to_team_id,
        "to_team_name": to_team_name,
        "date": transaction.get("date"),
        "effective_date": transaction.get("effectiveDate"),
        "resolution_date": transaction.get("resolutionDate"),
        "type_code": type_code,
        "type_desc": type_desc,
        "description": description,
        "signed_free_agent_flag": bool_flag(blob, r"\bsfa\b", r"signed .*free agent", r"signed as free agent"),
        "minor_league_contract_flag": bool_flag(blob, r"minor league contract", r"milb contract"),
        "released_flag": bool_flag(blob, r"\brel\b", r"released"),
        "declared_free_agency_flag": bool_flag(blob, r"\bdfa\b", r"declared free agency"),
        "dfa_flag": bool_flag(blob, r"\bdes\b", r"designated .*assignment"),
        "outrighted_flag": bool_flag(blob, r"\bout\b", r"outright"),
        "optioned_flag": bool_flag(blob, r"\bopt\b", r"optioned"),
        "assigned_flag": bool_flag(blob, r"assigned", r"assignment"),
        "selected_contract_flag": bool_flag(blob, r"selected .*contract", r"contract selected"),
        "injured_list_flag": bool_flag(blob, r"injured list", r"\bil\b", r"placed .*injured"),
        "rehab_flag": bool_flag(blob, r"rehab"),
        "traded_flag": bool_flag(blob, r"\btraded\b", r"\btrade\b"),
        "roster_status_change_flag": bool_flag(blob, r"status change", r"activated", r"recalled", r"transferred"),
        "source_url": source_url,
        "collected_at": collected_at,
    }


def collect_transactions(start_date: str, end_date: str) -> tuple[pd.DataFrame, dict, str]:
    params = {"sportId": 1, "startDate": start_date, "endDate": end_date}
    response = requests.get(BASE_URL, params=params, timeout=60, verify=certifi.where())
    response.raise_for_status()
    payload = response.json()
    collected_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds")
    records = [
        flatten_transaction(transaction, response.url, collected_at)
        for transaction in payload.get("transactions", [])
    ]
    df = pd.DataFrame(records)
    if not df.empty:
        df["transaction_id"] = pd.to_numeric(df["transaction_id"], errors="coerce").astype("Int64")
        df["player_id"] = pd.to_numeric(df["player_id"], errors="coerce").astype("Int64")
        df = df.sort_values(["date", "transaction_id", "player_name"], na_position="last")
    return df, payload, response.url


def main() -> None:
    today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="2025-10-01", help="YYYY-MM-DD")
    parser.add_argument("--end-date", default=today, help="YYYY-MM-DD")
    args = parser.parse_args()

    df, raw, source_url = collect_transactions(args.start_date, args.end_date)
    raw_dir = ROOT / "data/raw/mlb/transactions"
    out_dir = ROOT / "outputs/tables"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = f"{args.start_date.replace('-', '')}_{args.end_date.replace('-', '')}"
    raw_path = raw_dir / f"mlb_transactions_raw_{suffix}.json"
    table_path = out_dir / f"mlb_transactions_{suffix}.csv"
    latest_path = out_dir / "mlb_transactions_latest.csv"

    raw_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    df.to_csv(table_path, index=False)
    df.to_csv(latest_path, index=False)

    print(f"source: {source_url}")
    print(f"wrote {table_path} ({len(df)} rows)")
    print(f"wrote {raw_path}")


if __name__ == "__main__":
    main()
