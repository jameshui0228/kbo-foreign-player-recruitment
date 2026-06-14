#!/usr/bin/env python3
"""Download Baseball Savant Statcast data in resumable chunks.

The raw pitch/play-level files are intentionally stored before feature
engineering so candidate scoring can be rebuilt with different hypotheses.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from pybaseball import cache, statcast


SEED = 7
random.seed(SEED)


@dataclass
class ChunkResult:
    start_date: str
    end_date: str
    output_file: str
    rows: int
    columns: int
    status: str
    error: str | None = None


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def iter_chunks(start: date, end: date, chunk_days: int) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)
    return chunks


def chunk_filename(start: date, end: date, team: str | None) -> str:
    suffix = f"_{team}" if team else ""
    return f"statcast_{start:%Y%m%d}_{end:%Y%m%d}{suffix}.csv.gz"


def write_manifest(path: Path, results: list[ChunkResult], args: argparse.Namespace) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "Baseball Savant via pybaseball.statcast",
        "seed": SEED,
        "args": vars(args),
        "chunks": [asdict(item) for item in results],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def combine_chunks(raw_dir: Path, combined_path: Path, pattern: str) -> None:
    files = sorted(raw_dir.glob(pattern))
    if not files:
        raise SystemExit(f"No chunk files found for pattern: {raw_dir / pattern}")

    frames = []
    for file in files:
        frames.append(pd.read_csv(file, low_memory=False))
    combined = pd.concat(frames, ignore_index=True)

    combined_path.parent.mkdir(parents=True, exist_ok=True)
    if combined_path.suffix == ".parquet":
        combined.to_parquet(combined_path, index=False)
    elif combined_path.suffixes[-2:] == [".csv", ".gz"] or combined_path.suffix == ".csv":
        combined.to_csv(combined_path, index=False)
    else:
        raise SystemExit("Combined output must end with .parquet, .csv, or .csv.gz")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download Baseball Savant Statcast data.")
    parser.add_argument("--start", required=True, help="Start date, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date, YYYY-MM-DD")
    parser.add_argument("--team", default=None, help="Optional MLB team abbreviation")
    parser.add_argument("--chunk-days", type=int, default=7, help="Days per request chunk")
    parser.add_argument("--out-dir", default="data/raw/mlb_milb/savant/statcast", help="Raw chunk output directory")
    parser.add_argument("--manifest", default="outputs/tables/savant_statcast_download_manifest.json")
    parser.add_argument("--sleep-sec", type=float, default=1.0, help="Pause between chunks")
    parser.add_argument("--resume", action="store_true", help="Skip existing non-empty chunk files")
    parser.add_argument("--no-cache", action="store_true", help="Disable pybaseball local cache")
    parser.add_argument("--combine", action="store_true", help="Combine downloaded chunks after completion")
    parser.add_argument("--combined-out", default="data/processed/savant_statcast_combined.parquet")
    parser.add_argument("--parallel", action="store_true", help="Use pybaseball parallel mode inside each chunk")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    start = parse_date(args.start)
    end = parse_date(args.end)
    if end < start:
        raise SystemExit("--end must be on or after --start")
    if args.chunk_days < 1:
        raise SystemExit("--chunk-days must be positive")

    if not args.no_cache:
        cache.enable()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[ChunkResult] = []
    chunks = iter_chunks(start, end, args.chunk_days)
    for index, (chunk_start, chunk_end) in enumerate(chunks, start=1):
        out_file = out_dir / chunk_filename(chunk_start, chunk_end, args.team)
        if args.resume and out_file.exists() and out_file.stat().st_size > 0:
            try:
                row_count = int(sum(len(chunk) for chunk in pd.read_csv(out_file, usecols=[0], chunksize=100_000)))
                col_count = int(pd.read_csv(out_file, nrows=0).shape[1])
            except Exception:
                row_count = -1
                col_count = -1
            results.append(
                ChunkResult(
                    start_date=str(chunk_start),
                    end_date=str(chunk_end),
                    output_file=str(out_file),
                    rows=row_count,
                    columns=col_count,
                    status="skipped_existing",
                )
            )
            print(f"[{index}/{len(chunks)}] skip existing {out_file}")
            continue

        print(f"[{index}/{len(chunks)}] downloading {chunk_start} to {chunk_end}")
        try:
            df = statcast(
                start_dt=str(chunk_start),
                end_dt=str(chunk_end),
                team=args.team,
                verbose=False,
                parallel=args.parallel,
            )
            df.to_csv(out_file, index=False, compression="gzip")
            result = ChunkResult(
                start_date=str(chunk_start),
                end_date=str(chunk_end),
                output_file=str(out_file),
                rows=int(len(df)),
                columns=int(len(df.columns)),
                status="downloaded",
            )
            print(f"  wrote {len(df):,} rows x {len(df.columns)} cols -> {out_file}")
        except Exception as exc:  # noqa: BLE001
            result = ChunkResult(
                start_date=str(chunk_start),
                end_date=str(chunk_end),
                output_file=str(out_file),
                rows=0,
                columns=0,
                status="failed",
                error=str(exc),
            )
            print(f"  failed: {exc}")
        results.append(result)
        write_manifest(manifest_path, results, args)
        if args.sleep_sec > 0:
            time.sleep(args.sleep_sec)

    write_manifest(manifest_path, results, args)

    if args.combine:
        pattern = f"statcast_*_{args.team}.csv.gz" if args.team else "statcast_*.csv.gz"
        combine_chunks(out_dir, Path(args.combined_out), pattern)
        print(f"combined chunks -> {args.combined_out}")


if __name__ == "__main__":
    main()
