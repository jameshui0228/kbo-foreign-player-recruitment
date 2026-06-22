#!/usr/bin/env python3
"""Filter final SSG foreign player candidates with extended criteria.

기존 모델(ssg_risk_adjusted_fit_queue)의 lane_2 + stable_top25 후보에서
다음 두 가지 추가 기준을 적용해 최종 후보를 압축한다.

[타자 추가 기준]
  1. 좌타/스위치 우선 (SSG 선발진 우투 비율 고려)
  2. break_off_xwoba + low_velo_xwoba >= 0.20 (KBO 변화구·저속 대응 능력)
  3. K% 단순 패널티 대신 구종별 xwOBA로 약점 유형 구분

[투수 추가 기준]
  1. BB9 <= 3.5 (KBO ABS 도입 이후 존 판정 엄격, MLB보다 불리하게 번역)
  2. third_time_woba_allowed 낮은 선수 우선 (KBO 선발 5~6이닝 책임)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

QUEUE_PATH = OUTPUT_DIR / "ssg_risk_adjusted_fit_queue_v0_1.csv"
HITTER_FEAT_PATH = OUTPUT_DIR / "savant_hitter_feature_summary_2023_2026.csv"
PITCHER_FEAT_PATH = OUTPUT_DIR / "savant_pitcher_feature_summary_2023_2026.csv"
ROSTER_PATH = OUTPUT_DIR / "mlb_roster_status_latest.csv"

# 타자: 변화구·저속 대응 최소 기준
MIN_BREAK_OFF_XWOBA = 0.20
MIN_LOW_VELO_XWOBA = 0.20

# 투수: 커맨드 기준
MAX_BB9 = 3.5

# 출력할 타자 컬럼
HITTER_DISPLAY_COLS = [
    "rank",
    "player_name",
    "team_or_org",
    "bat_side",
    "hitter_recent_woba",
    "break_off_xwoba",
    "low_velo_xwoba",
    "hitter_recent_k_pct",
    "hitter_recent_bb_pct",
    "hitter_recent_barrel_rate",
    "hitter_recent_hardhit_rate",
    "failure_risk_index",
    "contract_control_bucket",
    "medical_risk_bucket",
    "filter_note",
]

# 출력할 투수 컬럼
PITCHER_DISPLAY_COLS = [
    "rank",
    "player_name",
    "team_or_org",
    "pitcher_milb_2026_ip",
    "pitcher_milb_2026_k9",
    "pitcher_milb_2026_bb9",
    "pitcher_milb_2026_hr9",
    "third_time_woba",
    "risp_woba",
    "pitcher_milb_role_continuity_bucket",
    "failure_risk_index",
    "contract_control_bucket",
    "medical_risk_bucket",
    "filter_note",
]


def load_base_candidates(slot: str) -> pd.DataFrame:
    """lane_2 + stable_top25 후보를 큐에서 가져온다."""
    queue = pd.read_csv(QUEUE_PATH)
    return queue[
        queue["fit_slot"].eq(slot)
        & queue["fit_review_lane"].eq("lane_2_deep_review_candidate_locked")
        & queue["sensitivity_band"].eq("stable_top25_locked")
    ].copy()


def attach_bat_side(df: pd.DataFrame) -> pd.DataFrame:
    roster = pd.read_csv(ROSTER_PATH)[["player_id", "bat_side"]].drop_duplicates("player_id")
    roster["player_id"] = pd.to_numeric(roster["player_id"], errors="coerce")
    df["player_id"] = pd.to_numeric(df["player_id"], errors="coerce")
    return df.merge(roster, on="player_id", how="left")


def attach_hitter_xwoba(df: pd.DataFrame) -> pd.DataFrame:
    """2024년 이후 Savant 피처에서 구종별 xwOBA를 가중평균으로 조인한다."""
    feat = pd.read_csv(HITTER_FEAT_PATH)
    agg = (
        feat[feat["game_year"].ge(2024)]
        .groupby("batter")
        .agg(
            break_off_xwoba=("break_off_xwoba", "mean"),
            low_velo_xwoba=("low_velo_xwoba", "mean"),
            high_velo_xwoba=("high_velo_xwoba", "mean"),
        )
        .reset_index()
        .rename(columns={"batter": "player_id"})
    )
    agg["player_id"] = pd.to_numeric(agg["player_id"], errors="coerce")
    return df.merge(agg, on="player_id", how="left")


def attach_pitcher_third_time(df: pd.DataFrame) -> pd.DataFrame:
    """2024년 이후 Savant 피처에서 3차전 wOBA·RISP wOBA를 조인한다."""
    feat = pd.read_csv(PITCHER_FEAT_PATH)
    agg = (
        feat[feat["game_year"].ge(2024)]
        .groupby("pitcher")
        .agg(
            third_time_woba=("third_time_woba_allowed", "mean"),
            risp_woba=("risp_woba_allowed", "mean"),
        )
        .reset_index()
        .rename(columns={"pitcher": "player_id"})
    )
    agg["player_id"] = pd.to_numeric(agg["player_id"], errors="coerce")
    return df.merge(agg, on="player_id", how="left")


def bat_side_score(side: str) -> int:
    """좌타=2, 스위치=1, 우타=0."""
    if str(side).lower() in ("left", "l"):
        return 2
    if str(side).lower() in ("switch", "s", "b"):
        return 1
    return 0


def filter_hitters(df: pd.DataFrame) -> pd.DataFrame:
    """타자 추가 필터링 + 점수 재산출."""
    df = attach_bat_side(df)
    df = attach_hitter_xwoba(df)

    # 부상 이력 제외
    df = df[~df["medical_risk_bucket"].str.contains("medical_hold", case=False, na=False)].copy()

    # 구종 대응 기준 미달 제외 (둘 다 데이터 있을 때만 적용)
    has_data = df["break_off_xwoba"].notna() & df["low_velo_xwoba"].notna()
    fails_xwoba = (
        df["break_off_xwoba"].lt(MIN_BREAK_OFF_XWOBA)
        | df["low_velo_xwoba"].lt(MIN_LOW_VELO_XWOBA)
    )
    df = df[~(has_data & fails_xwoba)].copy()

    # 재순위 점수: 기존 모델 점수 + 타석 방향 보정 + 구종 xwOBA 보정
    df["bat_side_score"] = df["bat_side"].apply(bat_side_score)
    df["xwoba_pitch_bonus"] = (
        df["break_off_xwoba"].fillna(0) + df["low_velo_xwoba"].fillna(0)
    ) * 5  # 스케일 조정
    df["adjusted_score"] = (
        df["risk_adjusted_fit_score_internal"].fillna(50)
        + df["bat_side_score"] * 2
        + df["xwoba_pitch_bonus"]
    )

    df = df.sort_values("adjusted_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    # 필터 노트
    notes = []
    for _, row in df.iterrows():
        parts = []
        if str(row.get("bat_side", "")).lower() in ("left", "l"):
            parts.append("좌타")
        elif str(row.get("bat_side", "")).lower() in ("switch", "s", "b"):
            parts.append("스위치")
        if pd.notna(row.get("break_off_xwoba")) and row["break_off_xwoba"] >= 0.30:
            parts.append("변화구대응우수")
        if "dfa" in str(row.get("contract_control_bucket", "")).lower() or \
           "released" in str(row.get("contract_control_bucket", "")).lower():
            parts.append("즉시접촉가능")
        notes.append(" | ".join(parts) if parts else "-")
    df["filter_note"] = notes

    return df


def filter_pitchers(df: pd.DataFrame) -> pd.DataFrame:
    """투수 추가 필터링 + 점수 재산출."""
    df = attach_pitcher_third_time(df)

    # 부상 이력 제외
    df = df[~df["medical_risk_bucket"].str.contains("medical_hold", case=False, na=False)].copy()

    # BB9 기준 미달 제외
    bb9 = pd.to_numeric(df["pitcher_milb_2026_bb9"], errors="coerce")
    df = df[bb9.isna() | bb9.le(MAX_BB9)].copy()

    # 재순위 점수: 기존 점수 + third_time 보정 + BB9 보정
    bb9_score = (MAX_BB9 - pd.to_numeric(df["pitcher_milb_2026_bb9"], errors="coerce").fillna(MAX_BB9)).clip(0) * 3
    third_time_score = (0.5 - df["third_time_woba"].fillna(0.4)).clip(0) * 20
    df["adjusted_score"] = (
        df["risk_adjusted_fit_score_internal"].fillna(50)
        + bb9_score
        + third_time_score
    )

    df = df.sort_values("adjusted_score", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    # 필터 노트
    notes = []
    for _, row in df.iterrows():
        parts = []
        bb9_val = pd.to_numeric(row.get("pitcher_milb_2026_bb9"), errors="coerce")
        if pd.notna(bb9_val) and bb9_val <= 2.0:
            parts.append("커맨드탁월")
        if pd.notna(row.get("third_time_woba")) and row["third_time_woba"] <= 0.30:
            parts.append("3차전강함")
        if "starter" in str(row.get("pitcher_milb_role_continuity_bucket", "")).lower():
            parts.append("선발이닝유지")
        if "dfa" in str(row.get("contract_control_bucket", "")).lower() or \
           "released" in str(row.get("contract_control_bucket", "")).lower():
            parts.append("즉시접촉가능")
        notes.append(" | ".join(parts) if parts else "-")
    df["filter_note"] = notes

    return df


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    hitters = filter_hitters(load_base_candidates("foreign_hitter"))
    pitchers = filter_pitchers(load_base_candidates("foreign_pitcher"))

    hitter_out = OUTPUT_DIR / "final_candidate_hitters_v1.csv"
    pitcher_out = OUTPUT_DIR / "final_candidate_pitchers_v1.csv"

    hitters.to_csv(hitter_out, index=False)
    pitchers.to_csv(pitcher_out, index=False)

    display_h = [c for c in HITTER_DISPLAY_COLS if c in hitters.columns]
    display_p = [c for c in PITCHER_DISPLAY_COLS if c in pitchers.columns]

    print("=" * 70)
    print(f"외국인 타자 최종 후보 ({len(hitters)}명)")
    print("=" * 70)
    print(hitters[display_h].head(10).to_string(index=False))

    print()
    print("=" * 70)
    print(f"외국인 투수 최종 후보 ({len(pitchers)}명)")
    print("=" * 70)
    print(pitchers[display_p].head(10).to_string(index=False))

    print()
    print(f"wrote {hitter_out.relative_to(PROJECT_ROOT)}")
    print(f"wrote {pitcher_out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
