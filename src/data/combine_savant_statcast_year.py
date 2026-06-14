#!/usr/bin/env python3
"""Combine Baseball Savant raw chunks for exactly one season.

The generic downloader combines every `statcast_*.csv.gz` file in a directory.
This helper avoids cross-season contamination when multiple seasons share one
raw chunk directory.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Combine one Savant season from raw chunks.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--raw-dir", action="append", required=True, help="Raw chunk directory. Can be repeated.")
    parser.add_argument("--out", required=True, help="Parquet output path.")
    parser.add_argument("--manifest", required=True, help="JSON manifest output path.")
    return parser


def chunk_start_year(path: Path) -> int | None:
    match = re.search(r"statcast_(\d{8})_", path.name)
    if not match:
        return None
    return int(match.group(1)[:4])


def find_files(raw_dirs: list[str], year: int) -> list[Path]:
    files: list[Path] = []
    for raw_dir in raw_dirs:
        root = Path(raw_dir)
        if not root.exists():
            continue
        for file in sorted(root.glob("statcast_*.csv.gz")):
            if chunk_start_year(file) == year:
                files.append(file)
    return sorted(set(files))


def main() -> None:
    args = build_parser().parse_args()
    files = find_files(args.raw_dir, args.year)
    if not files:
        raise SystemExit(f"No raw files found for year {args.year}")

    frames = []
    file_rows = []
    for file in files:
        df = pd.read_csv(file, low_memory=False)
        before = len(df)
        if "game_year" in df.columns:
            df = df[pd.to_numeric(df["game_year"], errors="coerce").eq(args.year)].copy()
        frames.append(df)
        file_rows.append(
            {
                "file": str(file),
                "raw_rows": before,
                "kept_rows": len(df),
                "columns": len(df.columns),
            }
        )

    combined = pd.concat(frames, ignore_index=True, sort=False)
    if "game_pk" in combined.columns and "at_bat_number" in combined.columns and "pitch_number" in combined.columns:
        before_dedupe = len(combined)
        combined = combined.drop_duplicates(subset=["game_pk", "at_bat_number", "pitch_number"], keep="first")
    else:
        before_dedupe = len(combined)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(out_path, index=False)

    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "year": args.year,
        "source_files": file_rows,
        "rows_before_dedupe": before_dedupe,
        "rows_after_dedupe": len(combined),
        "columns": len(combined.columns),
        "output_file": str(out_path),
    }
    manifest_path = Path(args.manifest)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("combined", len(files), "files")
    print("rows_before_dedupe", before_dedupe)
    print("rows_after_dedupe", len(combined))
    print("wrote", out_path)
    print("wrote", manifest_path)


if __name__ == "__main__":
    main()
