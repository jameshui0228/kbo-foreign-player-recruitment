#!/usr/bin/env python3
"""Build a teammate-facing data manifest.

The manifest lists local data files, sizes, rough row counts, git tracking
status, and whether the file is safe to publish directly in a public GitHub
repository. It intentionally records source visibility without exposing API
keys or duplicating raw data.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "outputs/tables/project_data_file_manifest_v1.csv"
DOC_PATH = ROOT / "docs/data_manifest_for_teammates.md"


def git_ls_files(args: list[str]) -> set[str]:
    try:
        out = subprocess.check_output(["git", *args], cwd=ROOT, text=True)
    except subprocess.CalledProcessError:
        return set()
    return {line.strip() for line in out.splitlines() if line.strip()}


def sha256_prefix(path: Path, n_bytes: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read(n_bytes))
    return h.hexdigest()[:16]


def line_count(path: Path) -> int | None:
    try:
        with path.open("rb") as f:
            return sum(1 for _ in f)
    except OSError:
        return None


def row_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        count = line_count(path)
        return max(count - 1, 0) if count is not None else None
    if suffix == ".jsonl":
        return line_count(path)
    if suffix == ".json":
        try:
            obj = json.loads(path.read_text(errors="ignore"))
        except Exception:
            return None
        if isinstance(obj, list):
            return len(obj)
        if isinstance(obj, dict):
            for key in ("data", "rows", "items", "records"):
                value = obj.get(key)
                if isinstance(value, list):
                    return len(value)
        return None
    if suffix == ".parquet":
        try:
            return len(pd.read_parquet(path, columns=[]))
        except Exception:
            return None
    return None


def source_group(path: str) -> str:
    if path.startswith("data/raw/kbo/statiz/"):
        return "STATIZ API/local KBO snapshot"
    if path.startswith("data/raw/mlb_milb/savant/") or path.startswith("data/processed/mlb_milb/savant/"):
        return "Baseball Savant/Statcast"
    if path.startswith("data/raw/mlb/"):
        return "MLB official/stats API"
    if path.startswith("data/raw/articles/naver_news"):
        return "Naver News Search API"
    if path.startswith("data/raw/articles/naver_news_pitching"):
        return "Naver News Search API"
    if path.startswith("data/raw/asian_market_rosters/"):
        return "NPB/CPBL official roster collection"
    if path.startswith("data/external/literature/"):
        return "Literature PDFs"
    if path.startswith("data/external/kbo_foreign_players/"):
        return "Wikipedia templates"
    if path.startswith("data/external/kbo_abs_paper/"):
        return "External ABS paper replication data"
    if path.startswith("data/processed/kbo/"):
        return "Processed KBO labels"
    if path.startswith("data/schemas/"):
        return "Project schema"
    if path.startswith("outputs/tables/"):
        return "Tracked analysis output"
    return "Other"


def publish_policy(path: str, tracked: bool) -> tuple[str, str]:
    if path.startswith("data/schemas/") or path.startswith("outputs/tables/"):
        return "tracked_in_github", "Small derived/schema file already committed for collaboration."
    if path.startswith("data/raw/kbo/statiz/"):
        return "do_not_public_git", "Contest/API-derived STATIZ data; share privately or regenerate with authorized key."
    if path.startswith("data/raw/articles/"):
        return "do_not_public_git", "API-derived news metadata/raw snippets; share privately or regenerate with authorized key."
    if path.startswith("data/external/literature/") or path.endswith(".pdf"):
        return "do_not_public_git", "PDF redistribution may be copyright-sensitive; cite source and share links."
    if path.endswith((".parquet", ".gz")):
        return "large_or_regenerable", "Large generated/downloaded file; use Git LFS, Release, or shared drive if raw access is required."
    if path.startswith("data/raw/") or path.startswith("data/processed/") or path.startswith("data/external/"):
        return "private_or_regenerate", "Not tracked in public repo; use source log, scripts, or shared drive."
    if tracked:
        return "tracked_in_github", "Committed."
    return "review_before_publish", "Review size, source terms, and sensitivity before publishing."


def main() -> None:
    tracked_files = git_ls_files(["ls-files"])
    ignored_files = git_ls_files(["ls-files", "--others", "--ignored", "--exclude-standard"])

    scan_roots = [ROOT / "data", ROOT / "outputs/tables"]
    rows: list[dict[str, object]] = []
    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(ROOT).as_posix()
            tracked = rel in tracked_files
            ignored = rel in ignored_files
            policy, note = publish_policy(rel, tracked)
            size = path.stat().st_size
            rows.append(
                {
                    "path": rel,
                    "source_group": source_group(rel),
                    "extension": path.suffix.lower().lstrip(".") or "none",
                    "size_bytes": size,
                    "size_mb": round(size / 1024 / 1024, 3),
                    "row_count_estimate": row_count(path),
                    "sha256_1mb_prefix": sha256_prefix(path),
                    "git_tracked": tracked,
                    "git_ignored_or_untracked": ignored,
                    "publish_policy": policy,
                    "note": note,
                }
            )

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    df = pd.DataFrame(rows)
    by_group = (
        df.groupby(["source_group", "publish_policy"], dropna=False)
        .agg(files=("path", "count"), size_mb=("size_mb", "sum"))
        .reset_index()
        .sort_values(["source_group", "publish_policy"])
    )

    total_size = df["size_mb"].sum()
    raw_size = df[df["path"].str.startswith("data/raw/")]["size_mb"].sum()
    processed_size = df[df["path"].str.startswith("data/processed/")]["size_mb"].sum()
    tracked_size = df[df["git_tracked"]]["size_mb"].sum()

    md_lines = [
        "# Data Manifest For Teammates",
        "",
        "이 문서는 팀원들이 프로젝트에서 어떤 데이터를 썼는지 확인하기 위한 manifest입니다.",
        "원천 데이터 전체를 public GitHub에 그대로 올리는 대신, 파일 목록, 출처 그룹, 용량, 행 수 추정치, 공개 정책을 기록합니다.",
        "",
        "## Summary",
        "",
        f"- Total local data/output files scanned: {len(df):,}",
        f"- Total scanned size: {total_size:,.1f} MB",
        f"- Raw data size: {raw_size:,.1f} MB",
        f"- Processed data size: {processed_size:,.1f} MB",
        f"- Git-tracked data/output size: {tracked_size:,.1f} MB",
        "",
        "## Policy",
        "",
        "- `tracked_in_github`: GitHub에 올라간 schema/derived output입니다.",
        "- `do_not_public_git`: API/대회/뉴스/PDF 등 public repo 재배포가 조심스러운 원천입니다.",
        "- `large_or_regenerable`: 대용량 파일입니다. 필요하면 Git LFS, Release, Google Drive, 또는 재수집 스크립트를 씁니다.",
        "- `private_or_regenerate`: public GitHub에는 올리지 않고, source log와 script로 재현하거나 private 공유합니다.",
        "",
        "## Source Group Summary",
        "",
        "| source group | publish policy | files | size MB |",
        "|---|---|---:|---:|",
    ]
    for row in by_group.itertuples(index=False):
        md_lines.append(
            f"| {row.source_group} | {row.publish_policy} | {int(row.files)} | {float(row.size_mb):,.1f} |"
        )
    md_lines.extend(
        [
            "",
            "## Full Manifest",
            "",
            f"Full CSV: `outputs/tables/{MANIFEST_PATH.name}`",
            "",
            "## Practical Sharing Recommendation",
            "",
            "팀원이 분석 흐름과 사용 데이터 종류를 확인하는 데는 이 manifest와 `docs/source_log.md`면 충분합니다.",
            "실제 원천 파일까지 실행해야 하는 팀원에게는 `data/raw/`, `data/processed/`, `data/external/`을 Google Drive 또는 별도 private 저장소로 공유하는 편이 안전합니다.",
            "특히 STATIZ API/공모전 데이터와 Naver API raw data는 public GitHub에 직접 올리지 않는 것을 권장합니다.",
            "",
        ]
    )
    DOC_PATH.write_text("\n".join(md_lines))
    print(f"wrote {MANIFEST_PATH} rows={len(df)}")
    print(f"wrote {DOC_PATH}")


if __name__ == "__main__":
    main()
