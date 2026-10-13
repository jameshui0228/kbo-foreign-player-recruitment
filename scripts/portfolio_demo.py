#!/usr/bin/env python3
"""Summarize tracked June 2026 result tables without raw data or API keys."""

import argparse
import csv
import math
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs/tables"
BOARD = "final_candidate_board_execution_v4.csv"
AUDIT = "model_probability_calibration_audit_v1.csv"


def read_rows(path, columns):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(columns) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
        rows = list(reader)
    if not rows:
        raise ValueError(f"{path.name}: no rows")
    return rows


def load_results(tables=TABLES):
    rows = read_rows(tables / BOARD, ["slot", "player", "decision_rank", "decision"])
    selected = []
    for slot in ("foreign_hitter", "foreign_pitcher"):
        candidates = [row for row in rows if row["slot"] == slot
                      and row["decision"].startswith("CONTACT_")]
        candidates.sort(key=lambda row: int(row["decision_rank"]))
        if [int(row["decision_rank"]) for row in candidates] != [1, 2, 3]:
            raise ValueError(f"{slot}: expected unique contact ranks 1, 2, 3")
        selected.extend(candidates)
    audit = read_rows(tables / AUDIT, ["target", "historical_rows", "unique_player_groups",
                                     "full_fit_auc", "leave_one_player_group_auc"])
    if sorted(row["target"] for row in audit) != ["failure", "success"]:
        raise ValueError("Audit must contain one success and one failure row")
    for row in audit:
        for field in ("full_fit_auc", "leave_one_player_group_auc"):
            value = float(row[field])
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"Invalid {field}: {row[field]}")
    return selected, audit


def markdown(selected, audit):
    lines = ["# Public Result Summary", "", "[Demo guide](README.md) | [한국어](results.ko.md)", "",
             "Snapshot: final June 2026 artifacts. This is not a current recommendation or a new model-training result.",
             "", "## Final Contact Priorities", "", "| Role | Rank | Candidate |", "|---|---:|---|"]
    for row in selected:
        slot = "Hitter" if row["slot"] == "foreign_hitter" else "Pitcher"
        player = row["player"].replace("|", "\\|")
        lines.append(f"| {slot} | {row['decision_rank']} | {player} |")
    lines += ["", "## Training Fit vs. Player-Held-Out Validation", "",
              "| Target | Training Rows | Unique Players | Training AUC | Player-Held-Out AUC |",
              "|---|---:|---:|---:|---:|"]
    for row in audit:
        lines.append(f"| {row['target']} | {row['historical_rows']} | {row['unique_player_groups']} | "
                     f"{float(row['full_fit_auc']):.3f} | {float(row['leave_one_player_group_auc']):.3f} |")
    lines += ["", "Training fit is not generalization. Model outputs support candidate comparison; they are not absolute success probabilities.",
              "", "![AUC by evaluation setting](validation.svg)", "", "## Source Tables & Methods", "",
              f"- [Final candidate table](../../outputs/tables/{BOARD})",
              f"- [Validation audit table](../../outputs/tables/{AUDIT})",
              "- [Final validation interpretation (Korean)](../final_report_last_validation_v1.md)",
              "- [Demo instructions](README.md)", "",
              "This document and chart are generated from public CSVs with `python3 scripts/portfolio_demo.py --write`."]
    return "\n".join(lines) + "\n"


def svg(audit):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="430" viewBox="0 0 1000 430" role="img" aria-labelledby="title desc">',
             '<title id="title">Training fit versus player-held-out validation</title>',
             '<desc id="desc">Stored June 2026 AUC results, not new model training. Exact values are labeled on each bar.</desc>',
             '<rect width="1000" height="430" fill="#faf9f6"/>',
             '<g font-family="Helvetica, sans-serif" fill="#192d36">',
             '<text x="40" y="46" font-size="25" font-weight="700">High training fit is not generalization.</text>',
             '<text x="40" y="78" font-size="16">Hitter models / 22 historical rows / 17 unique players / June 2026</text>',
             '<rect x="40" y="104" width="14" height="14" fill="#b4c3c9"/>',
             '<text x="64" y="117" font-size="15">Training fit</text>',
             '<rect x="220" y="104" width="14" height="14" fill="#126c69"/>',
             '<text x="244" y="117" font-size="15">Leave-one-player-group validation</text>']
    x0, width = 210, 680
    for tick in (0, 0.25, 0.5, 0.75, 1):
        x = x0 + tick * width
        parts += [f'<line x1="{x}" y1="142" x2="{x}" y2="345" stroke="#d9dfdf"/>',
                  f'<text x="{x}" y="368" text-anchor="middle" font-size="13">{tick:g}</text>']
    for i, row in enumerate(sorted(audit, key=lambda item: item["target"], reverse=True)):
        y = 156 + i * 100
        parts.append(f'<text x="40" y="{y+35}" font-size="19">{escape(row["target"].title())}</text>')
        for j, (field, color) in enumerate((("full_fit_auc", "#b4c3c9"), ("leave_one_player_group_auc", "#126c69"))):
            value = float(row[field])
            yy = y + j * 32
            parts += [f'<rect x="{x0}" y="{yy}" width="{value*width:.3f}" height="25" rx="3" fill="{color}"/>',
                      f'<text x="{x0+value*width+10:.3f}" y="{yy+18}" font-size="15">{value:.3f}</text>']
    parts += ['<text x="40" y="410" font-size="14">AUC scale: 0 to 1. Model signals support comparison; they are not absolute success probabilities.</text>', '</g></svg>']
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate result Markdown and SVG")
    mode.add_argument("--check", action="store_true", help="Compare tracked outputs with source CSVs")
    args = parser.parse_args()
    selected, audit = load_results()
    outputs = {"results.md": markdown(selected, audit), "validation.svg": svg(audit)}
    destination = ROOT / "docs/portfolio"
    if args.write:
        destination.mkdir(parents=True, exist_ok=True)
        for name, content in outputs.items():
            (destination / name).write_text(content, encoding="utf-8")
        print("Generated docs/portfolio/results.md and validation.svg from tracked CSVs.")
    elif args.check:
        for name, content in outputs.items():
            path = destination / name
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                raise ValueError(f"Stale portfolio output: {name}; run --write")
        print("PASS: 6 contact candidates, 2 audit rows, and generated outputs verified.")
    else:
        print(outputs["results.md"], end="")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as exc:
        print(f"Portfolio verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
