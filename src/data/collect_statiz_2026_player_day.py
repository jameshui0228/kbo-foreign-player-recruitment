#!/usr/bin/env python3
"""Refetch 2026 STATIZ player-day batting rows.

The copied live-delta snapshot contains complete 2026 schedules/lineups, but
the player-day batting table can miss games when a player was not included in
the original daily fetch pool. This script rebuilds 2026 batting rows by
requesting playerDay for every 2026 roster/lineup player and writes a separate
enriched CSV. It never stores API credentials; provide them through
STATIZ_API_KEY and STATIZ_API_SECRET.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
ORGANIZED_ROOT = STATIZ_ROOT / "organized"
DEFAULT_OUTPUT = ORGANIZED_ROOT / "players/players_day_batting_2026_refetched.csv"

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
    "battingOrder",
    "position",
    "1B",
    "2B",
    "3B",
    "AB",
    "AVG",
    "BB",
    "BH",
    "BS",
    "CG",
    "CS",
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
    "PA",
    "R",
    "RBI",
    "S",
    "SB",
    "SF",
    "SH",
    "SHO",
    "SLG",
    "SO",
    "TB",
    "TBF",
    "W",
    "WHIP",
    "ePA",
    "rRA",
    "situation",
]


class RateLimitError(RuntimeError):
    def __init__(self, message: str, cooldown_sec: int = 60):
        super().__init__(message)
        self.cooldown_sec = cooldown_sec


def normalize_query(params: dict[str, Any]) -> str:
    safe = "-_.!~*'()"
    return "&".join(
        f"{quote(str(key), safe=safe)}={quote(str(params[key]), safe=safe)}"
        for key in sorted(params)
    )


class StatizClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("STATIZ_API_BASE_URL", "https://api.statiz.co.kr/baseballApi").rstrip("/")
        self.api_key = os.getenv("STATIZ_API_KEY", "")
        self.api_secret = os.getenv("STATIZ_API_SECRET", "")
        self.timeout_sec = int(os.getenv("STATIZ_TIMEOUT_SEC", "20"))
        if not self.api_key or not self.api_secret:
            raise RuntimeError("STATIZ_API_KEY and STATIZ_API_SECRET must be set in the environment")

    def hmac_headers(self, method: str, path: str, params: dict[str, Any]) -> dict[str, str]:
        timestamp = str(int(time.time()))
        payload = f"{method.upper()}|{path.lstrip('/')}|{normalize_query(params)}|{timestamp}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "X-API-KEY": self.api_key,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
        }

    def get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        query = normalize_query(params)
        url_with_query = url if not query else f"{url}?{query}"
        cmd = [
            "curl",
            "-sS",
            "--max-time",
            str(self.timeout_sec),
            "-X",
            "GET",
            url_with_query,
            "-H",
            "Accept: application/json",
            "-H",
            "Content-Type: application/json",
            "-H",
            "User-Agent: sda-kbo-recruitment/1.0",
            "-w",
            "\n__CURL_STATUS__:%{http_code}",
        ]
        for key, value in self.hmac_headers("GET", path, params).items():
            cmd.extend(["-H", f"{key}: {value}"])
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout_sec + 5,
        )
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
        marker = "\n__CURL_STATUS__:"
        if marker not in proc.stdout:
            raise RuntimeError("curl response missing HTTP status marker")
        body, status = proc.stdout.rsplit(marker, 1)
        status_code = int(status.strip())
        if status_code >= 400:
            if status_code == 429:
                try:
                    payload = json.loads(body)
                    cooldown = int(payload.get("rate_limit", {}).get("cooldown_sec", 60))
                except Exception:  # noqa: BLE001
                    cooldown = 60
                raise RateLimitError(f"HTTP 429 rate limit: cooldown={cooldown}s", cooldown)
            raise RuntimeError(f"HTTP {status_code}: {body[:500]}")
        return json.loads(body)

    def player_day(self, p_no: int, year: int = 2026) -> dict[str, Any]:
        return self.get("/prediction/playerDay", {"p_no": p_no, "year": year})


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def load_name_maps() -> tuple[dict[int, str], dict[int, str], dict[int, str]]:
    schedule = pd.read_csv(ORGANIZED_ROOT / "games/games_schedule.csv", low_memory=False)
    lineups = pd.read_csv(ORGANIZED_ROOT / "games/games_lineup.csv", low_memory=False)
    team_pairs = pd.concat(
        [
            schedule[["awayTeam", "awayTeam_name"]].rename(columns={"awayTeam": "code", "awayTeam_name": "name"}),
            schedule[["homeTeam", "homeTeam_name"]].rename(columns={"homeTeam": "code", "homeTeam_name": "name"}),
        ],
        ignore_index=True,
    ).dropna()
    team_map = {
        int(row["code"]): str(row["name"])
        for _, row in team_pairs.drop_duplicates("code").iterrows()
    }
    position_map = {
        int(row["position"]): str(row["position_name"])
        for _, row in lineups[["position", "position_name"]].dropna().drop_duplicates("position").iterrows()
    }
    player_map = {
        int(row["p_no"]): str(row["p_name"])
        for _, row in lineups[["p_no", "p_name"]].dropna().drop_duplicates("p_no").iterrows()
    }
    roster = pd.read_csv(ORGANIZED_ROOT / "players/players_roster_daily.csv", low_memory=False)
    for _, row in roster[["p_no", "name"]].dropna().drop_duplicates("p_no").iterrows():
        player_map.setdefault(int(row["p_no"]), str(row["name"]))
    return team_map, position_map, player_map


def build_player_pool(team: str | None = None) -> pd.DataFrame:
    lineups = pd.read_csv(ORGANIZED_ROOT / "games/games_lineup.csv", low_memory=False)
    roster = pd.read_csv(ORGANIZED_ROOT / "players/players_roster_daily.csv", low_memory=False)
    existing = pd.read_csv(ORGANIZED_ROOT / "players/players_day_batting.csv", low_memory=False)

    lineups = lineups[pd.to_numeric(lineups["s_no"], errors="coerce").between(20260000, 20269999)].copy()
    roster = roster[roster["request_date"].astype(str).between("2026-03-28", "2026-06-11")].copy()
    existing = existing[existing["request_year"].eq(2026)].copy()
    if team:
        lineups = lineups[lineups["t_code_name"].eq(team)]
        roster = roster[roster["t_code_name"].eq(team)]
        existing = existing[existing["t_code_name"].eq(team)]

    frames = [
        lineups[["p_no"]].assign(source="lineup"),
        roster[["p_no"]].assign(source="roster"),
        existing[["p_no"]].assign(source="existing_batting"),
    ]
    pool = pd.concat(frames, ignore_index=True)
    pool["p_no"] = pd.to_numeric(pool["p_no"], errors="coerce")
    pool = pool.dropna(subset=["p_no"]).copy()
    pool["p_no"] = pool["p_no"].astype(int)
    pool = pool[pool["p_no"] > 0].copy()
    return pool.groupby("p_no", as_index=False)["source"].agg(lambda values: ",".join(sorted(set(values))))


def parse_player_day(payload: dict[str, Any], request_p_no: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in payload.items():
        if key in RESULT_KEYS or not isinstance(value, dict):
            continue
        row = dict(value)
        row["record_role"] = "batter"
        row["request_year"] = 2026
        row["request_p_no"] = request_p_no
        if "s_no" not in row and str(key).isdigit():
            row["s_no"] = int(key)
        rows.append(row)
    return rows


def fetch_with_retries(client: StatizClient, p_no: int, year: int, retries: int, sleep_sec: float) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            payload = client.player_day(p_no, year=year)
            return parse_player_day(payload, p_no)
        except RateLimitError as exc:
            last_error = exc
            wait = exc.cooldown_sec + 5
            print(f"[rate-limit] p_no={p_no} wait={wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = min(sleep_sec * (2 ** attempt), 20)
            print(f"[retry] p_no={p_no} attempt={attempt}/{retries} wait={wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"playerDay failed for p_no={p_no}") from last_error


def normalize_rows(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    team_map, position_map, player_map = load_name_maps()
    df = pd.DataFrame(rows)
    df = to_numeric(df, NUMERIC_COLUMNS)
    df = df[df["s_no"].between(20260000, 20269999)].copy()
    df = df[df["PA"].notna()].copy()
    df["gameDate_kst"] = pd.NA
    df["t_code_name"] = df["t_code"].map(team_map)
    df["awayTeam_name"] = df["awayTeam"].map(team_map)
    df["position_name"] = df["position"].map(position_map)
    df["p_name"] = df["p_no"].map(player_map)
    for column in [
        "BH",
        "BS",
        "CG",
        "ER",
        "ERA",
        "HD",
        "IP",
        "L",
        "SHO",
        "TBF",
        "W",
        "WHIP",
        "rRA",
    ]:
        if column not in df.columns:
            df[column] = pd.NA
    ordered = [
        "record_role",
        "s_no",
        "gameDate_kst",
        "gameDate",
        "request_year",
        "request_p_no",
        "p_no",
        "p_name",
        "t_code",
        "t_code_name",
        "awayTeam",
        "awayTeam_name",
        "battingOrder",
        "position",
        "position_name",
        "record_key",
        "1B",
        "2B",
        "3B",
        "AB",
        "AVG",
        "BB",
        "BH",
        "BS",
        "CG",
        "CS",
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
        "PA",
        "R",
        "RBI",
        "S",
        "SB",
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
        "ePA",
        "homeScore",
        "rRA",
        "situation",
        "vs_tCode",
    ]
    for column in ordered:
        if column not in df.columns:
            df[column] = pd.NA
    df["record_key"] = df["s_no"]
    return df[ordered].sort_values(["s_no", "t_code", "battingOrder", "p_no"]).drop_duplicates(
        ["s_no", "p_no", "t_code", "battingOrder", "position"],
        keep="last",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team", default=None, help="Optional t_code_name filter, e.g. SSG")
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sleep-sec", type=float, default=0.05)
    parser.add_argument("--retries", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0, help="Debug limit for number of players")
    parser.add_argument("--checkpoint-every", type=int, default=25)
    args = parser.parse_args()

    pool = build_player_pool(args.team)
    if args.limit:
        pool = pool.head(args.limit)
    client = StatizClient()
    all_rows: list[dict[str, Any]] = []
    checkpoint_path = args.output.with_suffix(".partial.csv")
    print(f"fetching playerDay for {len(pool)} players")
    for idx, row in pool.reset_index(drop=True).iterrows():
        p_no = int(row["p_no"])
        rows = fetch_with_retries(client, p_no, args.year, args.retries, args.sleep_sec)
        all_rows.extend(rows)
        if (idx + 1) % 25 == 0 or idx + 1 == len(pool):
            print(f"fetched {idx + 1}/{len(pool)} players; rows={len(all_rows)}")
        if args.checkpoint_every and (idx + 1) % args.checkpoint_every == 0:
            normalize_rows(all_rows).to_csv(checkpoint_path, index=False)
        time.sleep(args.sleep_sec)

    output = normalize_rows(all_rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    audit = {
        "players_requested": int(len(pool)),
        "rows_written": int(len(output)),
        "games_written": int(output["s_no"].nunique()) if len(output) else 0,
        "teams_written": int(output["t_code"].nunique()) if len(output) else 0,
        "output": str(args.output),
    }
    audit_path = args.output.with_suffix(".audit.json")
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
