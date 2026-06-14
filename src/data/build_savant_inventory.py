#!/usr/bin/env python3
"""Inventory downloaded Baseball Savant raw chunks and build yearly parquet files."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def infer_year(path: Path) -> int:
    # statcast_YYYYMMDD_YYYYMMDD.csv.gz
    return int(path.name.split("_")[1][:4])


def count_rows(path: Path) -> tuple[int, int]:
    columns = int(pd.read_csv(path, nrows=0).shape[1])
    rows = int(sum(len(chunk) for chunk in pd.read_csv(path, usecols=[0], chunksize=100_000)))
    return rows, columns


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build inventory and yearly parquet for Savant Statcast data.")
    parser.add_argument("--raw-dir", default="data/raw/mlb_milb/savant/statcast_mlb")
    parser.add_argument("--inventory-out", default="outputs/tables/savant_statcast_inventory.csv")
    parser.add_argument("--processed-dir", default="data/processed/mlb_milb/savant")
    parser.add_argument("--years", nargs="*", type=int, default=None)
    parser.add_argument("--skip-parquet", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raw_dir = Path(args.raw_dir)
    files = sorted(raw_dir.glob("statcast_*.csv.gz"))
    if not files:
        raise SystemExit(f"No raw files found under {raw_dir}")

    rows = []
    for file in files:
        row_count, column_count = count_rows(file)
        rows.append(
            {
                "year": infer_year(file),
                "file": str(file),
                "rows": row_count,
                "columns": column_count,
                "size_bytes": file.stat().st_size,
            }
        )

    inventory = pd.DataFrame(rows).sort_values(["year", "file"])
    inventory_path = Path(args.inventory_out)
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory.to_csv(inventory_path, index=False)
    print(inventory.groupby("year").agg(files=("file", "count"), rows=("rows", "sum"), size_bytes=("size_bytes", "sum")))

    if args.skip_parquet:
        return

    processed_dir = Path(args.processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)
    years = args.years or sorted(inventory["year"].unique())
    for year in years:
        year_files = inventory.loc[inventory["year"] == year, "file"].tolist()
        if not year_files:
            print(f"skip {year}: no files")
            continue
        frames = [pd.read_csv(file, low_memory=False) for file in year_files]
        combined = pd.concat(frames, ignore_index=True)
        out = processed_dir / f"savant_statcast_{year}.parquet"
        combined.to_parquet(out, index=False)
        print(f"wrote {out} rows={len(combined):,} cols={len(combined.columns)}")


if __name__ == "__main__":
    main()

