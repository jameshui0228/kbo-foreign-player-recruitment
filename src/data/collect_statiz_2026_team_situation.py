#!/usr/bin/env python3
"""Fetch current 2026 STATIZ teamRecord situational batting ranks."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent))
from collect_statiz_2026_player_day import RateLimitError, StatizClient, load_name_maps  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATIZ_ROOT = PROJECT_ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
ORGANIZED_ROOT = STATIZ_ROOT / "organized"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
DEFAULT_OUTPUT = ORGANIZED_ROOT / "team_records/team_record_batting_situations_2026_refetched.csv"

CONTEXTS: list[dict[str, Any]] = [
    {"context_family": "overall", "context_label": "all", "params": {}},
    {"context_family": "home_away", "context_label": "home", "params": {"ha": "H"}},
    {"context_family": "home_away", "context_label": "away", "params": {"ha": "N"}},
    {"context_family": "runner", "context_label": "risp", "params": {"rr": "R"}},
    {"context_family": "runner", "context_label": "runner_on_base", "params": {"rr": "1"}},
    {"context_family": "runner", "context_label": "no_runner", "params": {"rr": "20000"}},
    {"context_family": "runner", "context_label": "on_first", "params": {"rr": "20001"}},
    {"context_family": "runner", "context_label": "on_second", "params": {"rr": "20010"}},
    {"context_family": "runner", "context_label": "bases_loaded", "params": {"rr": "20111"}},
    {"context_family": "inning", "context_label": "early_1_3", "params": {"ii": "F"}},
    {"context_family": "inning", "context_label": "middle_4_6", "params": {"ii": "M"}},
    {"context_family": "inning", "context_label": "late_7_9", "params": {"ii": "L"}},
    {"context_family": "outs", "context_label": "0_out", "params": {"oo": "N"}},
    {"context_family": "outs", "context_label": "1_out", "params": {"oo": "1"}},
    {"context_family": "outs", "context_label": "2_out", "params": {"oo": "2"}},
    {"context_family": "count", "context_label": "0B_2S", "params": {"bc": "1002"}},
    {"context_family": "count", "context_label": "1B_2S", "params": {"bc": "1012"}},
    {"context_family": "count", "context_label": "2B_2S", "params": {"bc": "1022"}},
    {"context_family": "count", "context_label": "3B_2S", "params": {"bc": "1032"}},
    {"context_family": "count", "context_label": "2B_0S", "params": {"bc": "1020"}},
    {"context_family": "count", "context_label": "3B_0S", "params": {"bc": "1030"}},
    {"context_family": "count", "context_label": "3B_1S", "params": {"bc": "1031"}},
    {"context_family": "pitcher_type", "context_label": "vs_right", "params": {"pt": "R"}},
    {"context_family": "pitcher_type", "context_label": "vs_left", "params": {"pt": "L"}},
    {"context_family": "pitcher_type", "context_label": "vs_right_orthodox", "params": {"pt": "1"}},
    {"context_family": "pitcher_type", "context_label": "vs_right_under", "params": {"pt": "2"}},
    {"context_family": "pitcher_type", "context_label": "vs_left_orthodox", "params": {"pt": "3"}},
]

NUMERIC_COLUMNS = [
    "year",
    "t_code",
    "G",
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
    "AVG",
    "OBP",
    "SLG",
    "OPS",
]


def to_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def fetch_with_retries(
    client: StatizClient,
    params: dict[str, Any],
    retries: int,
    sleep_sec: float,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return client.get("/prediction/teamRecord", params)
        except RateLimitError as exc:
            last_error = exc
            wait = exc.cooldown_sec + 5
            print(f"[rate-limit] params={params} wait={wait}s", file=sys.stderr)
            time.sleep(wait)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            wait = min(sleep_sec * (2**attempt), 20)
            print(f"[retry] params={params} attempt={attempt}/{retries} wait={wait:.1f}s", file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(f"teamRecord failed for params={params}") from last_error


def add_metrics_and_ranks(df: pd.DataFrame) -> pd.DataFrame:
    out = to_numeric(df.copy(), NUMERIC_COLUMNS)
    for column in ["PA", "AB", "H", "BB", "HP", "SF", "SO", "TB", "HR", "RBI"]:
        if column not in out.columns:
            out[column] = 0
        out[column] = out[column].fillna(0)
    obp_den = out["AB"] + out["BB"] + out["HP"] + out["SF"]
    out["avg_calc"] = out["H"] / out["AB"].replace(0, np.nan)
    out["obp_calc"] = (out["H"] + out["BB"] + out["HP"]) / obp_den.replace(0, np.nan)
    out["slg_calc"] = out["TB"] / out["AB"].replace(0, np.nan)
    out["ops_calc"] = out["obp_calc"] + out["slg_calc"]
    out["iso_calc"] = out["slg_calc"] - out["avg_calc"]
    out["bb_pct"] = out["BB"] / out["PA"].replace(0, np.nan)
    out["k_pct"] = out["SO"] / out["PA"].replace(0, np.nan)
    out["hr_per_pa"] = out["HR"] / out["PA"].replace(0, np.nan)
    out["rbi_per_pa"] = out["RBI"] / out["PA"].replace(0, np.nan)
    rank_group = ["context_family", "context_label"]
    for metric in ["OPS", "OBP", "SLG", "AVG", "HR", "RBI", "bb_pct", "hr_per_pa", "rbi_per_pa", "ops_calc", "obp_calc", "slg_calc", "iso_calc"]:
        if metric in out.columns:
            out[f"{metric}_rank"] = out.groupby(rank_group)[metric].rank(method="min", ascending=False)
    out["k_pct_rank"] = out.groupby(rank_group)["k_pct"].rank(method="min", ascending=True)
    out["team_count"] = out.groupby(rank_group)["t_code"].transform("nunique")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sleep-sec", type=float, default=0.45)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()

    client = StatizClient()
    team_map, _position_map, _player_map = load_name_maps()
    rows: list[dict[str, Any]] = []
    raw_payloads: list[dict[str, Any]] = []
    for idx, context in enumerate(CONTEXTS, start=1):
        params = {"m2": "batting", "year": args.year}
        params.update(context["params"])
        payload = fetch_with_retries(client, params, args.retries, args.sleep_sec)
        raw_payloads.append({"context": context, "request": params, "response": payload})
        for item in payload.get("list", []):
            row = dict(item)
            row["context_family"] = context["context_family"]
            row["context_label"] = context["context_label"]
            row["context_params"] = json.dumps(context["params"], ensure_ascii=False, sort_keys=True)
            row["api_update_time"] = payload.get("update_time")
            rows.append(row)
        print(f"fetched {idx}/{len(CONTEXTS)} {context['context_family']}:{context['context_label']} rows={len(rows)}")
        time.sleep(args.sleep_sec)

    output = pd.DataFrame(rows)
    if not output.empty:
        output = to_numeric(output, NUMERIC_COLUMNS)
        output["t_code_name"] = output["t_code"].map(team_map)
        output = add_metrics_and_ranks(output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(args.output, index=False)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_DIR / "kbo_2026_team_situation_ranks.csv", index=False)
    raw_path = args.output.with_suffix(".raw.jsonl")
    with raw_path.open("w", encoding="utf-8") as fp:
        for payload in raw_payloads:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    audit = {
        "contexts_requested": len(CONTEXTS),
        "rows_written": int(len(output)),
        "output": str(args.output),
        "rank_output": str(OUTPUT_DIR / "kbo_2026_team_situation_ranks.csv"),
        "raw_output": str(raw_path),
    }
    args.output.with_suffix(".audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
