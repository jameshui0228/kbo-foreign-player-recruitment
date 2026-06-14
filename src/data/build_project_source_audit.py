from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    import pyarrow.parquet as pq
except Exception:  # pragma: no cover - optional local dependency
    pq = None


ROOT = Path(__file__).resolve().parents[2]


def csv_shape(path: Path, encoding: str | None = None) -> tuple[int | None, int | None]:
    try:
        head = pd.read_csv(path, nrows=5, encoding=encoding)
    except UnicodeDecodeError:
        head = pd.read_csv(path, nrows=5, encoding="cp949")
    rows = sum(1 for _ in path.open("rb")) - 1
    return rows, len(head.columns)


def parquet_shape(path: Path) -> tuple[int | None, int | None]:
    if pq is None:
        return None, None
    meta = pq.ParquetFile(path).metadata
    return meta.num_rows, meta.num_columns


def size_mb(paths: list[Path]) -> float:
    return round(sum(path.stat().st_size for path in paths if path.exists()) / 1024 / 1024, 2)


def dir_size_mb(path: Path) -> float | None:
    if not path.exists():
        return None
    return round(sum(child.stat().st_size for child in path.rglob("*") if child.is_file()) / 1024 / 1024, 2)


def build_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    statiz_inventory = ROOT / "outputs/tables/statiz_20260611_snapshot_inventory.csv"
    statiz_total_rows = None
    statiz_max_cols = None
    if statiz_inventory.exists():
        statiz_df = pd.read_csv(statiz_inventory)
        statiz_total_rows = int(statiz_df["rows"].sum())
        statiz_max_cols = int(statiz_df["columns"].max())
    statiz_dir = ROOT / "data/raw/kbo/statiz/live_delta_20260611_from_api_v1"
    rows.append(
        {
            "source_group": "KBO/STATIZ API snapshot",
            "local_path": "data/raw/kbo/statiz/live_delta_20260611_from_api_v1",
            "files": "multi-file snapshot",
            "rows": statiz_total_rows,
            "columns": statiz_max_cols,
            "size_mb": dir_size_mb(statiz_dir),
            "coverage": "2023-2026; latest refreshed through 2026-06-11 where API returned data",
            "candidate_use": "SSG need mining, KBO context, role/situation splits, historical transfer labels",
            "status": "secured",
            "gap": "need exact 2026 rulebook/cap treatment and KBO pitch-location raw if available",
        }
    )

    savant_paths = sorted((ROOT / "data/processed/mlb_milb/savant").glob("savant_statcast_*.parquet"))
    savant_total_rows = 0
    savant_cols = None
    for path in savant_paths:
        r, c = parquet_shape(path)
        if r is not None:
            savant_total_rows += r
        savant_cols = c or savant_cols
    rows.append(
        {
            "source_group": "MLB Baseball Savant Statcast",
            "local_path": "data/processed/mlb_milb/savant",
            "files": len(savant_paths),
            "rows": savant_total_rows if savant_total_rows else None,
            "columns": savant_cols,
            "size_mb": size_mb(savant_paths),
            "coverage": "MLB pitch/play level, 2023-2026; 2026 populated through 2026-06-09",
            "candidate_use": "pitcher stuff/location/workload proxies, hitter batted-ball/swing process features",
            "status": "secured",
            "gap": "does not include complete MiLB Statcast; needs roster/40-man/AAA availability data",
        }
    )

    roster_path = ROOT / "outputs/tables/mlb_roster_status_latest.csv"
    roster_rows, roster_cols = csv_shape(roster_path) if roster_path.exists() else (None, None)
    rows.append(
        {
            "source_group": "MLB roster status",
            "local_path": "outputs/tables/mlb_roster_status_latest.csv",
            "files": 1 if roster_path.exists() else 0,
            "rows": roster_rows,
            "columns": roster_cols,
            "size_mb": size_mb([roster_path]) if roster_path.exists() else None,
            "coverage": "MLB official 40-man, active, and full organization roster status collected 2026-06-12",
            "candidate_use": "availability gate, too-good-to-acquire screen, age/handedness/team context",
            "status": "secured_initial",
            "gap": "needs transaction/DFA/release/free-agent feed and salary/option data",
        }
    )

    article_paths = [
        ROOT / "data/raw/articles/naver_news/ssg_need_news_metadata.csv",
        ROOT / "data/raw/articles/naver_news_pitching/ssg_need_news_metadata.csv",
    ]
    article_rows = 0
    article_cols = None
    for path in article_paths:
        if path.exists():
            r, c = csv_shape(path)
            article_rows += r or 0
            article_cols = c or article_cols
    rows.append(
        {
            "source_group": "Naver news metadata corpus",
            "local_path": "data/raw/articles/naver_news*",
            "files": len([p for p in article_paths if p.exists()]),
            "rows": article_rows,
            "columns": article_cols,
            "size_mb": size_mb(article_paths),
            "coverage": "SSG offense/foreign-player/pitching/depth articles collected 2026-06-11 to 2026-06-12",
            "candidate_use": "public narrative corroboration, injury/depth/adaptation signals, name/entity mining",
            "status": "partial",
            "gap": "metadata secured; full-text corpus and quote-level citation extraction still needed",
        }
    )

    abs_paths = sorted((ROOT / "data/external/kbo_abs_paper/result").glob("*.csv"))
    abs_rows = 0
    abs_cols = None
    for path in abs_paths:
        r, c = csv_shape(path)
        abs_rows += r or 0
        abs_cols = c or abs_cols
    rows.append(
        {
            "source_group": "KBO ABS research result data",
            "local_path": "data/external/kbo_abs_paper/result",
            "files": len(abs_paths),
            "rows": abs_rows,
            "columns": abs_cols,
            "size_mb": size_mb(abs_paths),
            "coverage": "public result CSVs for 2021-2024 KBO umpire/ABS zone model summaries",
            "candidate_use": "ABS-native command thesis and zone-shift evidence",
            "status": "secured",
            "gap": "raw KBO pitch-location data by player/team not secured",
        }
    )

    literature_paths = sorted((ROOT / "data/external/literature").glob("*.pdf"))
    rows.append(
        {
            "source_group": "Literature PDFs",
            "local_path": "data/external/literature",
            "files": len(literature_paths),
            "rows": None,
            "columns": None,
            "size_mb": size_mb(literature_paths),
            "coverage": "KBO labor market, foreign-pitcher renewal ML, KBO adaptation, KBO ABS impact",
            "candidate_use": "feature justification, label design, risk/adaptation framework, rule-market framing",
            "status": "secured_core_partial_broader_literature",
            "gap": "broader paid/full-text literature still needs library access if used for final claims",
        }
    )

    rule_path = ROOT / "outputs/tables/kbo_contract_constraints_v1.csv"
    rule_rows, rule_cols = csv_shape(rule_path) if rule_path.exists() else (None, None)
    rows.append(
        {
            "source_group": "KBO/SSG contract and rule constraints",
            "local_path": "outputs/tables/kbo_contract_constraints_v1.csv",
            "files": 1 if rule_path.exists() else 0,
            "rows": rule_rows,
            "columns": rule_cols,
            "size_mb": size_mb([rule_path]) if rule_path.exists() else None,
            "coverage": "2026 Asian quota, replacement foreign player, current SSG foreign-player cost baseline",
            "candidate_use": "hard gates before candidate scoring",
            "status": "secured_with_open_checks",
            "gap": "latest downloadable KBO regulation text and official SSG Asian quota release still need confirmation",
        }
    )

    return rows


def main() -> None:
    out_path = ROOT / "outputs/tables/project_data_coverage_audit_v1.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(build_rows())
    df.to_csv(out_path, index=False)
    print(f"wrote {out_path} ({len(df)} rows)")


if __name__ == "__main__":
    main()
