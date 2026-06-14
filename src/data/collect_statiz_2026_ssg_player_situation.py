#!/usr/bin/env python3
"""Fetch current 2026 STATIZ playerSituation rows for SSG batters.

The endpoint returns player-level cumulative splits by time, location,
situation, count, and pitcher type. Credentials are read from environment
variables and are never written to the repository.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from collect_statiz_2026_player_day import (  # noqa: E402
    RateLimitError,
    StatizClient,
    load_name_maps,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
ORGANIZED_ROOT = STATIZ_ROOT / "organized"
DEFAULT_OUTPUT = ORGANIZED_ROOT / "player_situations/ssg_player_situation_batting_2026_refetched.csv"
REFETCHED_BATTING = ORGANIZED_ROOT / "players/players_day_batting_2026_refetched.csv"

META_KEYS = {"result_cd", "result_msg", "update_time"}
STAT_ITEM_KEYS = {
    "p_no",
    "t_code",
    "year",
    "G",
    "GS",
    "PA",
    "AB",
    "H",
    "HR",
    "RBI",
    "BB",
    "SO",
    "OPS",
    "IP",
    "ERA",
    "WHIP",
}
NUMERIC_COLUMNS = [
    "query_p_no",
    "query_year",
    "query_si",
    "p_no",
    "t_code",
    "year",
    "G",
    "GS",
    "PA",
    "ePA",
    "AB",
    "R",
    "H",
    "1B",
    "2B",
    "3B",
    "HR",
    "TB",
    "RBI",
    "BB",
    "IB",
    "HP",
    "SO",
    "GDP",
    "SH",
    "SF",
    "SB",
    "CS",
    "NP",
    "AVG",
    "OBP",
    "SLG",
    "OPS",
]
SI_NAMES = {
    1: "time",
    2: "location_team_stadium",
    3: "game_situation",
    4: "ball_count",
    5: "pitcher_type",
}


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def flatten_situation_value(
    query_p_no: int,
    query_year: int,
    query_si: int,
    path: list[str],
    value: Any,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if STAT_ITEM_KEYS.intersection(value.keys()):
            row = dict(value)
            row["query_p_no"] = query_p_no
            row["query_year"] = query_year
            row["query_si"] = query_si
            row["si_name"] = SI_NAMES.get(query_si, str(query_si))
            row["bucket_path"] = "/".join(path)
            row["bucket_group"] = path[0] if path else ""
            row["bucket_key"] = path[1] if len(path) > 1 else ""
            row["bucket_subkey"] = path[2] if len(path) > 2 else ""
            rows.append(row)
        else:
            for child_key, child_value in value.items():
                rows.extend(
                    flatten_situation_value(
                        query_p_no=query_p_no,
                        query_year=query_year,
                        query_si=query_si,
                        path=path + [str(child_key)],
                        value=child_value,
                    )
                )
    elif isinstance(value, list):
        for idx, child_value in enumerate(value):
            rows.extend(
                flatten_situation_value(
                    query_p_no=query_p_no,
                    query_year=query_year,
                    query_si=query_si,
                    path=path + [str(idx)],
                    value=child_value,
                )
            )
    return rows


def parse_player_situation(payload: dict[str, Any], p_no: int, year: int, si: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if payload.get("result_cd") != 100:
        return rows
    for key, value in payload.items():
        if key in META_KEYS:
            continue
        rows.extend(
            flatten_situation_value(
                query_p_no=p_no,
                query_year=year,
                query_si=si,
                path=[str(key)],
                value=value,
            )
        )
    for row in rows:
        row["api_update_time"] = payload.get("update_time")
        row["record_role"] = "batter"
    return rows


def build_ssg_batter_pool(min_pa: int) -> pd.DataFrame:
    if not REFETCHED_BATTING.exists():
        raise FileNotFoundError(f"Missing refetched batting file: {REFETCHED_BATTING}")
    batting = pd.read_csv(REFETCHED_BATTING, low_memory=False)
    batting["PA"] = pd.to_numeric(batting["PA"], errors="coerce").fillna(0)
    batting = batting[batting["t_code_name"].eq("SSG") & batting["PA"].gt(0)].copy()
    pool = (
        batting.groupby(["p_no", "p_name"], dropna=False)
        .agg(pa=("PA", "sum"), games=("s_no", "nunique"))
        .reset_index()
    )
    pool["p_no"] = pd.to_numeric(pool["p_no"], errors="coerce")
    pool = pool.dropna(subset=["p_no"]).copy()
    pool["p_no"] = pool["p_no"].astype(int)
    pool = pool[pool["pa"].ge(min_pa)].sort_values(["pa", "p_name"], ascending=[False, True])
    return pool.reset_index(drop=True)


def fetch_with_retries(
    client: StatizClient,
    p_no: int,
    year: int,
    si: int,
    retries: int,
    sleep_sec: float,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            payload = client.get("/prediction/playerSituation", {"p_no": p_no, "si": si, "year": year})
            return parse_player_situation(payload, p_no, year, si), payload
        except RateLimitError as exc:
            last_error = exc
            wait = exc.cooldown_sec + 5
            print(f"[rate-limit] p_no={p_no} si={si} wait={wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = min(sleep_sec * (2**attempt), 20)
            print(f"[retry] p_no={p_no} si={si} attempt={attempt}/{retries} wait={wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"playerSituation failed for p_no={p_no} si={si}") from last_error


def normalize_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    team_map, _position_map, player_map = load_name_maps()
    df = pd.DataFrame(rows)
    df = to_numeric(df, NUMERIC_COLUMNS)
    df["p_no"] = df["p_no"].fillna(df["query_p_no"])
    df["p_name"] = df["query_p_no"].map(player_map)
    df["t_code_name"] = df["t_code"].map(team_map)
    df["split_label"] = df["situation"].fillna(df["bucket_subkey"])
    df.loc[df["split_label"].astype(str).eq(""), "split_label"] = df["bucket_key"]
    ordered = [
        "record_role",
        "query_year",
        "query_p_no",
        "p_name",
        "query_si",
        "si_name",
        "bucket_group",
        "bucket_key",
        "bucket_subkey",
        "bucket_path",
        "split_label",
        "api_update_time",
        "p_no",
        "t_code",
        "t_code_name",
        "year",
        "G",
        "GS",
        "PA",
        "ePA",
        "AB",
        "R",
        "H",
        "1B",
        "2B",
        "3B",
        "HR",
        "TB",
        "RBI",
        "BB",
        "IB",
        "HP",
        "SO",
        "GDP",
        "SH",
        "SF",
        "SB",
        "CS",
        "NP",
        "AVG",
        "OBP",
        "SLG",
        "OPS",
        "situation",
    ]
    for column in ordered:
        if column not in df.columns:
            df[column] = pd.NA
    return df[ordered].sort_values(["query_p_no", "query_si", "bucket_path"]).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--min-pa", type=int, default=10)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sleep-sec", type=float, default=0.45)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0, help="Debug limit for number of players")
    args = parser.parse_args()

    pool = build_ssg_batter_pool(args.min_pa)
    if args.limit:
        pool = pool.head(args.limit)

    client = StatizClient()
    all_rows: list[dict[str, Any]] = []
    raw_payloads: list[dict[str, Any]] = []
    total_calls = len(pool) * 5
    print(f"fetching playerSituation for {len(pool)} SSG batters; calls={total_calls}")
    call_idx = 0
    for _, player in pool.iterrows():
        p_no = int(player["p_no"])
        for si in range(1, 6):
            call_idx += 1
            rows, payload = fetch_with_retries(client, p_no, args.year, si, args.retries, args.sleep_sec)
            all_rows.extend(rows)
            raw_payloads.append(
                {
                    "request": {"p_no": p_no, "year": args.year, "si": si},
                    "response": payload,
                }
            )
            if call_idx % 10 == 0 or call_idx == total_calls:
                print(f"fetched {call_idx}/{total_calls}; rows={len(all_rows)}")
            time.sleep(args.sleep_sec)

    output = normalize_rows(all_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    raw_path = args.output.with_suffix(".raw.jsonl")
    with raw_path.open("w", encoding="utf-8") as fp:
        for payload in raw_payloads:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    audit = {
        "players_requested": int(len(pool)),
        "min_pa": int(args.min_pa),
        "calls_requested": int(total_calls),
        "rows_written": int(len(output)),
        "output": str(args.output),
        "raw_output": str(raw_path),
        "api_update_time_min": None if output.empty else str(output["api_update_time"].min()),
        "api_update_time_max": None if output.empty else str(output["api_update_time"].max()),
    }
    args.output.with_suffix(".audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
