#!/usr/bin/env python3
"""Refetch 2026 STATIZ playerDay pitching rows for SSG players."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from collect_statiz_2026_player_day import RateLimitError, StatizClient, load_name_maps  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
ORGANIZED_ROOT = STATIZ_ROOT / "organized"
DEFAULT_OUTPUT = ORGANIZED_ROOT / "players/players_day_pitching_2026_ssg_refetched.csv"

RESULT_KEYS = {"result_cd", "result_msg", "update_time"}
NUMERIC_COLUMNS = [
    "s_no",
    "request_year",
    "request_p_no",
    "p_no",
    "t_code",
    "vs_tCode",
    "awayTeam",
    "awayScore",
    "homeScore",
    "position",
    "AB",
    "AVG",
    "BB",
    "BH",
    "BS",
    "CG",
    "ER",
    "ERA",
    "G",
    "GDP",
    "GS",
    "H",
    "HD",
    "HP",
    "HR",
    "IB",
    "IP",
    "L",
    "NP",
    "OBP",
    "OPS",
    "R",
    "S",
    "SF",
    "SH",
    "SHO",
    "SLG",
    "SO",
    "TB",
    "TBF",
    "W",
    "WHIP",
    "rRA",
]


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def build_ssg_player_pool() -> pd.DataFrame:
    roster = pd.read_csv(ORGANIZED_ROOT / "players/players_roster_daily.csv", low_memory=False)
    lineup = pd.read_csv(ORGANIZED_ROOT / "games/games_lineup.csv", low_memory=False)
    existing = pd.read_csv(ORGANIZED_ROOT / "players/players_day_pitching.csv", low_memory=False)

    roster = roster[roster["request_date"].astype(str).between("2026-03-28", "2026-06-12")]
    roster = roster[roster["t_code_name"].eq("SSG")]
    lineup = lineup[
        pd.to_numeric(lineup["s_no"], errors="coerce").between(20260000, 20269999)
        & lineup["t_code_name"].eq("SSG")
        & lineup["position"].eq(1)
    ]
    existing = existing[existing["request_year"].eq(2026) & existing["t_code_name"].eq("SSG")]

    frames = [
        roster[["p_no"]].assign(source="roster"),
        lineup[["p_no"]].assign(source="lineup_starter"),
        existing[["p_no"]].assign(source="existing_pitching"),
    ]
    pool = pd.concat(frames, ignore_index=True)
    pool["p_no"] = pd.to_numeric(pool["p_no"], errors="coerce")
    pool = pool.dropna(subset=["p_no"]).copy()
    pool["p_no"] = pool["p_no"].astype(int)
    pool = pool[pool["p_no"].gt(0)]
    return pool.groupby("p_no", as_index=False)["source"].agg(lambda values: ",".join(sorted(set(values))))


def parse_player_day_pitching(payload: dict[str, Any], request_p_no: int, year: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if payload.get("result_cd") != 100:
        return rows
    for key, value in payload.items():
        if key in RESULT_KEYS or not isinstance(value, dict):
            continue
        row = dict(value)
        if "IP" not in row and "TBF" not in row and "GS" not in row:
            continue
        row["record_role"] = "pitcher"
        row["request_year"] = year
        row["request_p_no"] = request_p_no
        if "s_no" not in row and str(key).isdigit():
            row["s_no"] = int(key)
        rows.append(row)
    return rows


def fetch_with_retries(
    client: StatizClient,
    p_no: int,
    year: int,
    retries: int,
    sleep_sec: float,
) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            payload = client.player_day(p_no, year=year)
            return parse_player_day_pitching(payload, p_no, year)
        except RateLimitError as exc:
            last_error = exc
            wait = exc.cooldown_sec + 5
            print(f"[rate-limit] p_no={p_no} wait={wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = min(sleep_sec * (2**attempt), 20)
            print(f"[retry] p_no={p_no} attempt={attempt}/{retries} wait={wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"playerDay pitching failed for p_no={p_no}") from last_error


def normalize_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    team_map, position_map, player_map = load_name_maps()
    roster = pd.read_csv(ORGANIZED_ROOT / "players/players_roster_daily.csv", low_memory=False)
    for _, row in roster[["p_no", "name"]].dropna().drop_duplicates("p_no").iterrows():
        player_map.setdefault(int(row["p_no"]), str(row["name"]))

    df = pd.DataFrame(rows)
    df = to_numeric(df, NUMERIC_COLUMNS)
    df = df[df["s_no"].between(20260000, 20269999)].copy()
    df = df[df["IP"].notna() | df["TBF"].notna()].copy()
    df["t_code_name"] = df["t_code"].map(team_map)
    df["awayTeam_name"] = df["awayTeam"].map(team_map)
    df["position_name"] = df["position"].map(position_map)
    df["p_name"] = df["p_no"].map(player_map)
    ordered = [
        "record_role",
        "s_no",
        "gameDate",
        "request_year",
        "request_p_no",
        "p_no",
        "p_name",
        "t_code",
        "t_code_name",
        "awayTeam",
        "awayTeam_name",
        "position",
        "position_name",
        "record_key",
        "AB",
        "AVG",
        "BB",
        "BH",
        "BS",
        "CG",
        "ER",
        "ERA",
        "G",
        "GDP",
        "GS",
        "H",
        "HD",
        "HP",
        "HR",
        "IB",
        "IP",
        "L",
        "NP",
        "OBP",
        "OPS",
        "R",
        "S",
        "SF",
        "SH",
        "SHO",
        "SLG",
        "SO",
        "TB",
        "TBF",
        "W",
        "WHIP",
        "awayScore",
        "homeScore",
        "rRA",
        "situation",
        "vs_tCode",
    ]
    for column in ordered:
        if column not in df.columns:
            df[column] = pd.NA
    df["record_key"] = df["s_no"]
    return df[ordered].sort_values(["s_no", "t_code", "GS", "p_no"]).drop_duplicates(
        ["s_no", "p_no", "t_code"],
        keep="last",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sleep-sec", type=float, default=0.45)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    pool = build_ssg_player_pool()
    if args.limit:
        pool = pool.head(args.limit)
    client = StatizClient()
    all_rows: list[dict[str, Any]] = []
    print(f"fetching playerDay pitching candidates for {len(pool)} SSG players")
    for idx, row in pool.reset_index(drop=True).iterrows():
        p_no = int(row["p_no"])
        rows = fetch_with_retries(client, p_no, args.year, args.retries, args.sleep_sec)
        all_rows.extend(rows)
        if (idx + 1) % 10 == 0 or idx + 1 == len(pool):
            print(f"fetched {idx + 1}/{len(pool)} players; pitching_rows={len(all_rows)}")
        time.sleep(args.sleep_sec)

    output = normalize_rows(all_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    audit = {
        "players_requested": int(len(pool)),
        "rows_written": int(len(output)),
        "games_written": int(output["s_no"].nunique()) if len(output) else 0,
        "output": str(args.output),
    }
    args.output.with_suffix(".audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
