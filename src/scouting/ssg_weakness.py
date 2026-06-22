"""
SSG Landers 숨은 약점 마이닝 — 1단계
======================================
입력: data/raw/kbo/statiz/live_delta_20260611_from_api_v1/organized/
출력: outputs/tables/ssg_weakness_*.csv
       outputs/figures/ssg_weakness_*.png  (선택)

실행:
    python src/scouting/ssg_weakness.py
    python src/scouting/ssg_weakness.py --no-plot   # 그래프 없이

환경 변수 (프로젝트 루트 .env 참조):
    STATIZ_ORGANIZED_DIR   raw statiz organized 폴더 경로
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── 경로 설정 ────────────────────────────────────────────────────────────────

def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / ".env").exists() or (parent / "README.md").exists():
            return parent
    return Path.cwd()

PROJECT_ROOT = _find_project_root()

def _load_env() -> dict[str, str]:
    env_file = PROJECT_ROOT / ".env"
    env: dict[str, str] = {}
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    env.update(os.environ)
    return env

ENV = _load_env()

def _resolve_env_path(key: str, fallback: Path) -> Path:
    raw = ENV.get(key, "")
    if not raw:
        return fallback
    # 간단한 ${VAR} 치환
    for k, v in ENV.items():
        raw = raw.replace(f"${{{k}}}", v)
    return Path(raw)

ORGANIZED_DIR = _resolve_env_path(
    "STATIZ_ORGANIZED_DIR",
    PROJECT_ROOT / "data" / "raw" / "kbo" / "statiz" / "organized",
)

OUT_TABLES = PROJECT_ROOT / "outputs" / "tables"
OUT_FIGURES = PROJECT_ROOT / "outputs" / "figures"
OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGURES.mkdir(parents=True, exist_ok=True)

SSG_CODE = "SSG"
SSG_T_CODE = "9002"
ANALYSIS_SEASONS = [2023, 2024, 2025]   # 시즌 완료 연도 (다년도 트렌드용)
CURRENT_YEAR = 2026                       # 현재 진행 중인 시즌

# ── 데이터 로드 헬퍼 ─────────────────────────────────────────────────────────

def _read(rel: str) -> pd.DataFrame:
    path = ORGANIZED_DIR / rel
    if not path.exists():
        print(f"[WARN] 파일 없음: {path}", file=sys.stderr)
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)

def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")

# ── 1. 다년도 팀 타격 트렌드 ─────────────────────────────────────────────────

def build_season_trend(df_team: pd.DataFrame) -> pd.DataFrame:
    """SSG vs 리그 평균 OPS/ISO/BB%/K% 연도별 비교."""
    cols = ["year", "t_code_name", "G", "PA", "AVG", "OBP", "SLG", "OPS", "HR", "BB", "SO", "WAR"]
    avail = [c for c in cols if c in df_team.columns]
    df = df_team[avail].copy()
    for c in ["G", "PA", "HR", "BB", "SO"]:
        if c in df.columns:
            df[c] = _to_float(df[c])
    for c in ["AVG", "OBP", "SLG", "OPS", "WAR"]:
        if c in df.columns:
            df[c] = _to_float(df[c])

    df["year"] = _to_float(df["year"]).astype("Int64")
    df = df[df["year"].isin(ANALYSIS_SEASONS)]

    # ISO 계산
    if "SLG" in df.columns and "AVG" in df.columns:
        df["iso"] = df["SLG"] - df["AVG"]
    # BB%, K% 계산
    if "BB" in df.columns and "PA" in df.columns:
        df["bb_pct"] = df["BB"] / df["PA"]
    if "SO" in df.columns and "PA" in df.columns:
        df["k_pct"] = df["SO"] / df["PA"]

    league_avg = (
        df.groupby("year")[["OPS", "iso", "bb_pct", "k_pct", "WAR"]]
        .mean()
        .reset_index()
        .rename(columns=lambda c: f"lg_{c}" if c != "year" else c)
    )

    ssg = df[df["t_code_name"] == SSG_CODE].copy()
    ssg = ssg.merge(league_avg, on="year", how="left")
    for m in ["OPS", "iso", "bb_pct", "k_pct"]:
        if f"lg_{m}" in ssg.columns and m in ssg.columns:
            ssg[f"{m}_vs_lg"] = ssg[m] - ssg[f"lg_{m}"]

    return ssg.sort_values("year")


# ── 2. 상황별 OPS — 핵심 약점 탐지 ─────────────────────────────────────────

SITUATION_LABELS_KO = {
    "all":               "전체",
    "risp":              "득점권(RISP)",
    "runner_on_base":    "주자 있을 때",
    "no_runner":         "주자 없을 때",
    "on_first":          "1루 주자만",
    "on_second":         "2루 주자만",
    "bases_loaded":      "만루",
    "early_1_3":         "초반(1~3이닝)",
    "middle_4_6":        "중반(4~6이닝)",
    "late_7_9":          "후반(7~9이닝)",
    "0_out":             "무사",
    "1_out":             "1사",
    "2_out":             "2사",
    "vs_right":          "우투수 상대",
    "vs_left":           "좌투수 상대",
    "vs_right_under":    "우언더/사이드암 상대",
    "vs_left_orthodox":  "좌정통 상대",
    "home":              "홈",
    "away":              "원정",
}

def build_situation_profile(df_sit: pd.DataFrame) -> pd.DataFrame:
    """2026 상황별 OPS 순위와 리그 평균 대비 갭."""
    if df_sit.empty:
        return pd.DataFrame()

    for c in ["ops_calc", "OPS", "OPS_rank", "iso_calc", "bb_pct", "k_pct", "team_count"]:
        if c in df_sit.columns:
            df_sit[c] = _to_float(df_sit[c])

    # ops 컬럼 통일 (ops_calc 우선, 없으면 OPS)
    if "ops_calc" in df_sit.columns:
        df_sit["ops"] = df_sit["ops_calc"]
    elif "OPS" in df_sit.columns:
        df_sit["ops"] = _to_float(df_sit["OPS"])

    # 리그 평균 계산
    lg_avg = (
        df_sit.groupby("context_label")["ops"]
        .mean()
        .reset_index()
        .rename(columns={"ops": "lg_ops"})
    )

    ssg = df_sit[df_sit["t_code_name"] == SSG_CODE].copy()
    ssg = ssg.merge(lg_avg, on="context_label", how="left")
    ssg["ops_vs_lg"] = ssg["ops"] - ssg["lg_ops"]
    ssg["label_ko"] = ssg["context_label"].map(SITUATION_LABELS_KO).fillna(ssg["context_label"])

    keep_cols = [
        "context_family", "context_label", "label_ko",
        "ops", "lg_ops", "ops_vs_lg", "OPS_rank", "team_count",
        "iso_calc", "bb_pct", "k_pct",
    ]
    return (
        ssg[[c for c in keep_cols if c in ssg.columns]]
        .sort_values("ops_vs_lg")
        .reset_index(drop=True)
    )


# ── 3. 좌/우 투수 스플릿 약점 (팀 레벨) ─────────────────────────────────────

def build_handedness_split(df_sit: pd.DataFrame) -> pd.DataFrame:
    """좌/우 투수 OPS 격차와 리그 대비 취약도."""
    if df_sit.empty:
        return pd.DataFrame()

    hand = df_sit[df_sit["context_family"] == "pitcher_type"].copy()
    if "ops_calc" in hand.columns:
        hand["ops"] = _to_float(hand["ops_calc"])
    elif "OPS" in hand.columns:
        hand["ops"] = _to_float(hand["OPS"])

    lg_avg = (
        hand.groupby("context_label")["ops"]
        .mean()
        .reset_index()
        .rename(columns={"ops": "lg_ops"})
    )

    ssg = hand[hand["t_code_name"] == SSG_CODE].copy()
    ssg = ssg.merge(lg_avg, on="context_label", how="left")
    ssg["ops_vs_lg"] = ssg["ops"] - ssg["lg_ops"]
    ssg["label_ko"] = ssg["context_label"].map(SITUATION_LABELS_KO).fillna(ssg["context_label"])

    # vs_left - vs_right 갭 (SSG)
    ssg_pivot = ssg.set_index("context_label")["ops"]
    gap_lhp = ssg_pivot.get("vs_left", np.nan) - ssg_pivot.get("vs_right", np.nan)

    keep = ["context_label", "label_ko", "ops", "lg_ops", "ops_vs_lg", "OPS_rank"]
    result = ssg[[c for c in keep if c in ssg.columns]].copy()
    result.attrs["lhp_rhp_gap"] = gap_lhp
    return result.reset_index(drop=True)


# ── 4. 2아웃 / 클러치 격차 ──────────────────────────────────────────────────

def build_clutch_profile(df_sit: pd.DataFrame) -> pd.DataFrame:
    """RISP, 주자 없을 때, 2사 OPS 격차 — 클러치 생산성 진단."""
    if df_sit.empty:
        return pd.DataFrame()

    clutch_labels = {"risp", "no_runner", "runner_on_base", "0_out", "1_out", "2_out"}
    df = df_sit[df_sit["context_label"].isin(clutch_labels)].copy()

    if "ops_calc" in df.columns:
        df["ops"] = _to_float(df["ops_calc"])
    elif "OPS" in df.columns:
        df["ops"] = _to_float(df["OPS"])

    lg_avg = df.groupby("context_label")["ops"].mean().reset_index().rename(columns={"ops": "lg_ops"})
    ssg = df[df["t_code_name"] == SSG_CODE].copy()
    ssg = ssg.merge(lg_avg, on="context_label", how="left")
    ssg["ops_vs_lg"] = ssg["ops"] - ssg["lg_ops"]
    ssg["label_ko"] = ssg["context_label"].map(SITUATION_LABELS_KO).fillna(ssg["context_label"])

    # 득점권 vs 주자 없을 때 갭
    pivot = ssg.set_index("context_label")["ops"]
    risp_gap = pivot.get("risp", np.nan) - pivot.get("no_runner", np.nan)
    twoout_gap = pivot.get("2_out", np.nan) - pivot.get("0_out", np.nan)

    keep = ["context_label", "label_ko", "ops", "lg_ops", "ops_vs_lg", "OPS_rank"]
    result = ssg[[c for c in keep if c in ssg.columns]].sort_values("ops_vs_lg").reset_index(drop=True)
    result.attrs["risp_no_runner_gap"] = risp_gap
    result.attrs["twoout_0out_gap"] = twoout_gap
    return result


# ── 5. 이닝 분포 약점 ────────────────────────────────────────────────────────

def build_inning_profile(df_sit: pd.DataFrame) -> pd.DataFrame:
    """초반/중반/후반 이닝 OPS 분포 — 선발 지원 vs 불펜 의존도."""
    if df_sit.empty:
        return pd.DataFrame()

    inning_labels = {"early_1_3", "middle_4_6", "late_7_9"}
    df = df_sit[df_sit["context_label"].isin(inning_labels)].copy()

    if "ops_calc" in df.columns:
        df["ops"] = _to_float(df["ops_calc"])
    elif "OPS" in df.columns:
        df["ops"] = _to_float(df["OPS"])

    lg_avg = df.groupby("context_label")["ops"].mean().reset_index().rename(columns={"ops": "lg_ops"})
    ssg = df[df["t_code_name"] == SSG_CODE].copy()
    ssg = ssg.merge(lg_avg, on="context_label", how="left")
    ssg["ops_vs_lg"] = ssg["ops"] - ssg["lg_ops"]
    ssg["label_ko"] = ssg["context_label"].map(SITUATION_LABELS_KO).fillna(ssg["context_label"])

    keep = ["context_label", "label_ko", "ops", "lg_ops", "ops_vs_lg", "OPS_rank"]
    return ssg[[c for c in keep if c in ssg.columns]].reset_index(drop=True)


# ── 6. WAR 공백 진단 (다년도) ────────────────────────────────────────────────

def build_war_gap(df_team: pd.DataFrame) -> pd.DataFrame:
    """SSG WAR이 리그 평균보다 얼마나 낮은지 연도별."""
    for c in ["WAR", "year"]:
        if c in df_team.columns:
            df_team[c] = _to_float(df_team[c])

    df = df_team[df_team["year"].isin(ANALYSIS_SEASONS)].copy()
    df["year"] = df["year"].astype("Int64")

    lg_war = df.groupby("year")["WAR"].mean().reset_index().rename(columns={"WAR": "lg_war"})
    ssg = df[df["t_code_name"] == SSG_CODE][["year", "WAR"]].copy()
    ssg = ssg.merge(lg_war, on="year", how="left")
    ssg["war_vs_lg"] = ssg["WAR"] - ssg["lg_war"]
    ssg = ssg.rename(columns={"WAR": "ssg_war"})

    rank_df = (
        df.groupby("year")
        .apply(lambda g: g.sort_values("WAR", ascending=False).assign(rank=range(1, len(g) + 1)))
        .reset_index(drop=True)
    )
    ssg_ranks = rank_df[rank_df["t_code_name"] == SSG_CODE][["year", "rank"]].rename(columns={"rank": "war_rank"})
    ssg = ssg.merge(ssg_ranks, on="year", how="left")
    return ssg.sort_values("year")


# ── 7. 문학 구장 파크팩터 메모 ──────────────────────────────────────────────
#
# Proxy assumption (assumptions.md #9):
# 문학 구장 공식 파크팩터는 STATIZ API 스냅샷에 포함되어 있지 않다.
# 대신 홈/원정 OPS 격차(home_away 상황별 데이터)를 park effect proxy로 사용한다.
# 좌/우 펜스 95m, CF 120m, 담장 2.8m는 2차 출처(Wikipedia) 기준이며 공식 교차검증 필요.

MUNHAK_DIMS = {
    "LF_m": 95,
    "LCF_m": 115,
    "CF_m": 120,
    "RCF_m": 115,
    "RF_m": 95,
    "wall_height_m": 2.8,
    "source": "Wikipedia (needs official crosscheck)",
}

def build_park_proxy(df_sit: pd.DataFrame) -> pd.DataFrame:
    """홈/원정 OPS 격차를 파크팩터 프록시로 사용."""
    if df_sit.empty:
        return pd.DataFrame()

    ha = df_sit[df_sit["context_family"] == "home_away"].copy()
    if "ops_calc" in ha.columns:
        ha["ops"] = _to_float(ha["ops_calc"])
    elif "OPS" in ha.columns:
        ha["ops"] = _to_float(ha["OPS"])

    lg_avg = ha.groupby("context_label")["ops"].mean().reset_index().rename(columns={"ops": "lg_ops"})
    ssg = ha[ha["t_code_name"] == SSG_CODE].copy()
    ssg = ssg.merge(lg_avg, on="context_label", how="left")
    ssg["ops_vs_lg"] = ssg["ops"] - ssg["lg_ops"]
    ssg["label_ko"] = ssg["context_label"].map(SITUATION_LABELS_KO).fillna(ssg["context_label"])

    home_ops = ssg[ssg["context_label"] == "home"]["ops"].values
    away_ops = ssg[ssg["context_label"] == "away"]["ops"].values
    park_boost = (home_ops[0] - away_ops[0]) if len(home_ops) and len(away_ops) else np.nan

    keep = ["context_label", "label_ko", "ops", "lg_ops", "ops_vs_lg", "OPS_rank"]
    result = ssg[[c for c in keep if c in ssg.columns]].reset_index(drop=True)
    result.attrs["home_away_gap"] = park_boost
    result.attrs["munhak_dims"] = MUNHAK_DIMS
    return result


# ── 8. 종합 약점 스코어카드 ──────────────────────────────────────────────────

def build_weakness_scorecard(
    situation: pd.DataFrame,
) -> pd.DataFrame:
    """
    각 상황별 ops_vs_lg를 z-score로 표준화한 뒤
    음수(리그 평균 하회) 항목을 약점 스코어로 집계한다.

    외국인 영입 연결 변수(feature_contract):
      - 득점권 약점  → candidate_hitter_features.risp_ops 기대치
      - 1루 주자만  → SB 위협, 번트 상황 대응력 (runner_advancement_proxy)
      - 우언더 약점 → abs_zone_discipline_score (바깥 낮은 공 컨택)
      - 초반 이닝 약점 → kbo_translation_index 중 early_inning_support
    """
    if situation.empty:
        return pd.DataFrame()

    df = situation.copy()
    mu = df["ops_vs_lg"].mean()
    sigma = df["ops_vs_lg"].std()
    df["ops_vs_lg_z"] = (df["ops_vs_lg"] - mu) / (sigma + 1e-9)
    df["weakness_flag"] = df["ops_vs_lg"] < 0
    df["weakness_severity"] = df["ops_vs_lg_z"].clip(upper=0).abs()

    FEATURE_CONTRACT = {
        "risp":           "risp_ops (candidate_hitter_features)",
        "on_first":       "runner_advancement_proxy → SB threat, contact ability",
        "bases_loaded":   "risp_ops + clutch_pressure_proxy",
        "early_1_3":      "early_inning_support (kbo_translation_index)",
        "2_out":          "two_out_contact_proxy → chase_pct, zone_contact_pct",
        "vs_right_under": "abs_zone_discipline_score (low/outside zone)",
        "away":           "road_durability_proxy",
    }
    df["feature_contract"] = df["context_label"].map(FEATURE_CONTRACT).fillna("")

    return df.sort_values("weakness_severity", ascending=False).reset_index(drop=True)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main(plot: bool = True) -> None:
    print(f"[ssg_weakness] 데이터 경로: {ORGANIZED_DIR}")
    if not ORGANIZED_DIR.exists():
        sys.exit(f"[ERROR] STATIZ_ORGANIZED_DIR 경로를 찾을 수 없습니다: {ORGANIZED_DIR}\n"
                 ".env 파일의 STATIZ_ORGANIZED_DIR 값을 확인하세요.")

    # ── 데이터 로드 ──────────────────────────────────────────────────────────
    df_team_bat   = _read("teams/teams_season_batting.csv")
    df_sit_2026   = _read("team_records/team_record_batting_situations_2026_refetched.csv")

    # ── 분석 실행 ────────────────────────────────────────────────────────────
    print("\n[1/6] 다년도 시즌 트렌드 분석...")
    trend = build_season_trend(df_team_bat)
    trend.to_csv(OUT_TABLES / "ssg_season_trend.csv", index=False, encoding="utf-8-sig")
    print(trend[["year", "OPS", "iso", "bb_pct", "k_pct", "OPS_vs_lg", "WAR"]
               if "OPS_vs_lg" in trend.columns
               else ["year", "OPS", "iso", "bb_pct", "k_pct", "WAR"]].to_string(index=False))

    print("\n[2/6] 상황별 OPS 프로파일 (2026)...")
    situation = build_situation_profile(df_sit_2026)
    situation.to_csv(OUT_TABLES / "ssg_situation_profile_2026.csv", index=False, encoding="utf-8-sig")

    print("\n[3/6] 좌/우 투수 스플릿 약점...")
    hand_split = build_handedness_split(df_sit_2026)
    hand_split.to_csv(OUT_TABLES / "ssg_handedness_split_2026.csv", index=False, encoding="utf-8-sig")
    if hasattr(hand_split, "attrs") and "lhp_rhp_gap" in hand_split.attrs:
        print(f"  LHP vs RHP OPS 격차 (SSG): {hand_split.attrs['lhp_rhp_gap']:+.3f}")

    print("\n[4/6] 클러치/주자 상황 프로파일...")
    clutch = build_clutch_profile(df_sit_2026)
    clutch.to_csv(OUT_TABLES / "ssg_clutch_profile_2026.csv", index=False, encoding="utf-8-sig")
    if hasattr(clutch, "attrs"):
        print(f"  RISP vs 주자없음 OPS 격차: {clutch.attrs.get('risp_no_runner_gap', 'N/A'):+.3f}")
        print(f"  2사 vs 무사 OPS 격차:      {clutch.attrs.get('twoout_0out_gap', 'N/A'):+.3f}")

    print("\n[5/6] 이닝별 OPS 분포...")
    inning = build_inning_profile(df_sit_2026)
    inning.to_csv(OUT_TABLES / "ssg_inning_profile_2026.csv", index=False, encoding="utf-8-sig")

    print("\n[6/6] 파크팩터 프록시 (홈/원정 OPS 격차)...")
    park = build_park_proxy(df_sit_2026)
    park.to_csv(OUT_TABLES / "ssg_park_proxy_2026.csv", index=False, encoding="utf-8-sig")
    if hasattr(park, "attrs"):
        print(f"  홈 - 원정 OPS 격차 (SSG): {park.attrs.get('home_away_gap', 'N/A'):+.3f}")
        print(f"  문학 구장 치수 (2차 출처): {park.attrs.get('munhak_dims', {})}")

    print("\n[종합] 약점 스코어카드 생성...")
    scorecard = build_weakness_scorecard(situation)
    scorecard.to_csv(OUT_TABLES / "ssg_weakness_scorecard_2026.csv", index=False, encoding="utf-8-sig")

    # ── 출력 요약 ────────────────────────────────────────────────────────────
    _print_summary(trend, scorecard, hand_split)

    # ── 시각화 ──────────────────────────────────────────────────────────────
    if plot:
        _plot_weakness(situation, scorecard)

    print(f"\n[완료] 출력 파일:")
    for f in sorted(OUT_TABLES.glob("ssg_*.csv")):
        print(f"  {f.relative_to(PROJECT_ROOT)}")


def _print_summary(
    trend: pd.DataFrame,
    scorecard: pd.DataFrame,
    hand_split: pd.DataFrame,
) -> None:
    print("\n" + "=" * 60)
    print("SSG 랜더스 숨은 약점 요약 (2026 시즌 기준)")
    print("=" * 60)

    # 다년도 트렌드
    print("\n[다년도 OPS 트렌드]")
    ops_col = "OPS"
    if ops_col in trend.columns:
        for _, r in trend.iterrows():
            vs = r.get("OPS_vs_lg", r.get("ops_vs_lg", float("nan")))
            print(f"  {r['year']}: OPS {r[ops_col]:.3f}  vs 리그 {vs:+.3f}")

    # Top 5 약점
    if not scorecard.empty:
        weak = scorecard[scorecard["weakness_flag"]].head(5)
        print("\n[상위 5개 약점 상황 (OPS 리그 평균 하회)]")
        for _, r in weak.iterrows():
            label = r.get("label_ko", r.get("context_label", ""))
            ops = r.get("ops", float("nan"))
            vs = r.get("ops_vs_lg", float("nan"))
            rank = r.get("OPS_rank", "?")
            fc = r.get("feature_contract", "")
            print(f"  {label:<20} OPS {ops:.3f}  리그대비 {vs:+.3f}  순위 {rank}")
            if fc:
                print(f"    → 후보 평가 변수: {fc}")

    # 좌/우 스플릿
    if not hand_split.empty:
        print("\n[좌/우 투수 상대 스플릿]")
        for _, r in hand_split.iterrows():
            label = r.get("label_ko", r.get("context_label", ""))
            ops = r.get("ops", float("nan"))
            vs = r.get("ops_vs_lg", float("nan"))
            rank = r.get("OPS_rank", "?")
            print(f"  {label:<25} OPS {ops:.3f}  vs 리그 {vs:+.3f}  순위 {rank}")

    print("\n[외국인 영입 연결 - Feature Contract]")
    print("  득점권 약점    → candidate_hitter_features.risp_ops")
    print("  1루 주자 약점  → runner_advancement_proxy (컨택, SB 위협)")
    print("  우언더 약점    → abs_zone_discipline_score (낮고 바깥 공 존 컨택)")
    print("  초반이닝 약점  → early_inning_support (kbo_translation_index)")
    print("  2아웃 약점     → two_out_contact_proxy (chase_pct, zone_contact_pct)")
    print("=" * 60)


def _plot_weakness(situation: pd.DataFrame, scorecard: pd.DataFrame) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm

        # 한글 폰트 시도
        for font in ["Malgun Gothic", "AppleGothic", "NanumGothic", "DejaVu Sans"]:
            if any(font.lower() in f.name.lower() for f in fm.fontManager.ttflist):
                plt.rcParams["font.family"] = font
                break
        plt.rcParams["axes.unicode_minus"] = False

    except ImportError:
        print("[WARN] matplotlib 없음. 그래프 생략.")
        return

    if situation.empty or "ops_vs_lg" not in situation.columns:
        return

    df_plot = situation[situation["context_label"] != "all"].copy()
    df_plot = df_plot.sort_values("ops_vs_lg")
    labels = df_plot["label_ko"].fillna(df_plot["context_label"]).tolist()
    vals = df_plot["ops_vs_lg"].tolist()
    colors = ["#d94f3d" if v < 0 else "#4f8fd9" for v in vals]

    fig, ax = plt.subplots(figsize=(10, 8))
    bars = ax.barh(labels, vals, color=colors, edgecolor="white", linewidth=0.5)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("OPS vs 리그 평균")
    ax.set_title("SSG 랜더스 상황별 OPS 리그 대비 (2026)", fontsize=13, fontweight="bold")
    ax.grid(axis="x", alpha=0.3)

    for bar, val in zip(bars, vals):
        ax.text(
            val + (0.003 if val >= 0 else -0.003),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.3f}",
            va="center",
            ha="left" if val >= 0 else "right",
            fontsize=7.5,
        )

    plt.tight_layout()
    out_path = OUT_FIGURES / "ssg_weakness_situation_2026.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  그래프 저장: {out_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SSG 숨은 약점 마이닝")
    parser.add_argument("--no-plot", action="store_true", help="그래프 생성 생략")
    args = parser.parse_args()
    main(plot=not args.no_plot)
