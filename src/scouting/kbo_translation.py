"""
KBO 번역 모델 - 4단계
======================
입력:
  outputs/tables/candidate_hitter_pool.csv
  outputs/tables/candidate_starter_pool.csv

출력:
  outputs/tables/translated_hitter_pool.csv
  outputs/tables/translated_starter_pool.csv

번역 로직 (docs/assumptions.md #26-#33):
  ① PCL 파크팩터 보정: PCL 팀은 OPS/ERA에 PF 할인 적용
  ② AAA→KBO 리그팩터: 타자 +2%, 투수 ERA×0.90
  ③ KBO wRC+ 추정: 2025 KBO 리그평균 OPS 0.727 기준
  ④ ABS 존 보정: chase_pct 낮은 타자에게 미세 보너스
  ⑤ xwOBA park-neutral: Savant xwOBA는 파크팩터 무관, 직접 리그팩터만 적용
"""
from __future__ import annotations
import pathlib
import pandas as pd
import numpy as np

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "outputs" / "tables"

# ── 파크팩터 ────────────────────────────────────────────────────────────────
# PCL 팀별 추정 파크팩터 (타자 친화적 구장, assumption #20, #26)
# Albuquerque: 고도 1500m+ → Coors 효과, 가장 강함
# El Paso/Salt Lake/Reno/Sugar Land/Las Vegas/Round Rock: 중간 수준
PCL_PARK_FACTORS: dict[str, float] = {
    "Albuquerque Isotopes":        1.10,  # 해발 ~1524m, 가장 극단적
    "El Paso Chihuahuas":          1.07,
    "Salt Lake Bees":              1.07,
    "Reno Aces":                   1.06,
    "Sugar Land Space Cowboys":    1.05,
    "Las Vegas Aviators":          1.05,
    "Round Rock Express":          1.04,
}

# ── KBO 리그 기준값 (STATIZ 2023-2025 평균) ───────────────────────────────
# 2023: 0.712, 2024: 0.772, 2025: 0.727 → 3년 평균 0.737 (assumption #27)
KBO_LG_OPS    = 0.737
KBO_LG_ERA    = 4.25   # KBO 리그 선발 평균 ERA (2023-2025 추정)

# ── 리그팩터 ────────────────────────────────────────────────────────────────
# assumption #28: KBO 투수 수준 ≈ AA+ (AAA보다 약함)
# 타자: KBO에서 OPS 약 +2~3% 상향 (더 약한 투수 상대)
# 투수: KBO에서 ERA 약 -10% 개선 (더 약한 타자 상대, 단 작은 구장 상쇄)
HITTER_LEAGUE_FACTOR    = 1.02   # AAA OPS × 1.02 → 기대 KBO OPS
PITCHER_LEAGUE_FACTOR   = 0.90   # AAA ERA × 0.90 → 기대 KBO ERA
XWOBA_LEAGUE_FACTOR     = 0.98   # xwOBA는 park-neutral이지만 리그 품질 보정 필요

# ── ABS 보정 ────────────────────────────────────────────────────────────────
# assumption #29: KBO 2025 ABS 도입으로 스트라이크존 일관성 ↑
# 체이스율 낮은 타자(볼 판별력 좋음) → 볼 판정 일관성으로 미세 이득
# 체이스율 낮은 투수(zone command 좋음) → 일관적 스트라이크 → 약간 유리
ABS_HITTER_BONUS_MAX  = 0.015   # OPS 최대 +0.015 (체이스율 최하위 선수)
ABS_PITCHER_BONUS_MAX = 0.20    # ERA 최대 -0.20 (BB9 낮고 zone command 좋은 투수)


def _pcl_factor(row: pd.Series) -> float:
    """팀 기준 PCL 파크팩터. PCL 외 팀은 1.0."""
    return PCL_PARK_FACTORS.get(str(row.get("team_latest", "")), 1.0)


def translate_hitters(df: pd.DataFrame) -> pd.DataFrame:
    """
    타자 번역 모델:
      1. PCL 파크팩터 보정 → ops_park_adj
      2. xwOBA 리그팩터 보정 (park-neutral → KBO 리그)
      3. AAA→KBO 리그팩터 적용 → kbo_ops_est
      4. KBO wRC+ 추정
      5. ABS 보정
      6. 불확실성 플래그
    """
    df = df.copy()

    pf = df.apply(_pcl_factor, axis=1)

    # ① PCL 보정 OPS
    df["ops_park_adj"] = df["ops"].astype(float) / pf

    # ② xwOBA 리그팩터 (park-neutral → KBO 리그 품질 보정)
    df["xwoba_kbo"] = df["xwoba"].where(df["xwoba"].notna()) * XWOBA_LEAGUE_FACTOR

    # ③ KBO OPS 추정 (primary: xwOBA 기반 / fallback: park-adj OPS)
    def _kbo_ops(r: pd.Series) -> float:
        if pd.notna(r.get("xwoba")):
            # xwOBA → OPS 환산: OPS ≈ xwOBA × 2.05 (경험적 변환, assumption #30)
            return float(r["xwoba"]) * XWOBA_LEAGUE_FACTOR * 2.05
        return float(r["ops_park_adj"]) * HITTER_LEAGUE_FACTOR

    df["kbo_ops_est"] = df.apply(_kbo_ops, axis=1)

    # ④ KBO wRC+ 추정
    # wRC+ ≈ 100 + 280 × (player_ops - lg_ops): 리니어 근사 (assumption #31)
    # 기울기 280: OPS +0.100 당 wRC+ +28점 → 실제 KBO 데이터와 근사
    df["kbo_wrc_plus_est"] = 100 + 280 * (df["kbo_ops_est"] - KBO_LG_OPS)

    # ⑤ ABS 보정: chase_pct 낮을수록 볼 판정 일관성 이득
    def _abs_bonus(r: pd.Series) -> float:
        chase = r.get("chase_pct")
        if pd.isna(chase) or chase is None:
            return 0.0
        # 체이스율 0.18 이하 → 최대 보너스, 0.32 이상 → 0
        bonus = max(0.0, (0.32 - float(chase)) / (0.32 - 0.18)) * ABS_HITTER_BONUS_MAX
        return round(bonus, 4)

    df["abs_ops_bonus"] = df.apply(_abs_bonus, axis=1)
    df["kbo_ops_final"] = df["kbo_ops_est"] + df["abs_ops_bonus"]
    df["kbo_wrc_plus_final"] = 100 + 280 * (df["kbo_ops_final"] - KBO_LG_OPS)

    # ⑥ 불확실성 플래그
    # - PCL 출신 + Savant 없음: 가장 불확실
    # - Savant 있음: park-neutral xwOBA 사용 → 상대적 신뢰
    df["translation_confidence"] = df.apply(
        lambda r: "high"   if pd.notna(r.get("xwoba")) and not r.get("pcl_inflated")
             else "medium" if pd.notna(r.get("xwoba")) and r.get("pcl_inflated")
             else "low"    if r.get("pcl_inflated")
             else "medium",
        axis=1,
    )

    # PCL 할인 크기 플래그
    df["pcl_discount"] = (pf - 1.0).round(3)

    return df


def translate_starters(df: pd.DataFrame) -> pd.DataFrame:
    """
    선발 번역 모델:
      1. PCL 파크팩터 보정 → era_park_adj
      2. AAA→KBO 리그팩터 적용 → kbo_era_est
      3. ABS 보정 (BB9, command 기반)
      4. 불확실성 플래그
    """
    df = df.copy()

    pf = df.apply(_pcl_factor, axis=1)

    # ① PCL 보정 ERA (PCL 파크에서 투수는 ERA ↑ → 조정 후 낮아짐)
    # ERA는 PF와 반대 방향: PCL에서 ERA 높으면 실제 능력은 더 좋음
    df["era_park_adj"] = df["era"].astype(float) / (pf * 0.95)
    # ERA의 park factor는 OPS보다 작게 적용 (ERA에 미치는 파크 효과 ≈ OPS의 50%)

    # ② KBO ERA 추정
    df["kbo_era_est"] = df["era_park_adj"] * PITCHER_LEAGUE_FACTOR

    # ③ ABS 보정: BB9 낮고 zone command 좋은 투수 → ABS 일관성 이득
    def _abs_era_bonus(r: pd.Series) -> float:
        bb9 = r.get("bb9")
        if pd.isna(bb9) or bb9 is None:
            return 0.0
        # BB9 ≤ 2.5 → 최대 보너스 (ERA -0.20)
        bonus = max(0.0, (4.0 - float(bb9)) / (4.0 - 2.0)) * ABS_PITCHER_BONUS_MAX
        return round(min(bonus, ABS_PITCHER_BONUS_MAX), 3)

    df["abs_era_bonus"] = df.apply(_abs_era_bonus, axis=1)
    df["kbo_era_final"] = (df["kbo_era_est"] - df["abs_era_bonus"]).clip(lower=1.5)

    # ④ KBO ERA+ 추정 (100 = 리그 평균)
    df["kbo_era_plus_est"] = (KBO_LG_ERA / df["kbo_era_final"] * 100).round(1)

    # ⑤ 불확실성 플래그
    df["translation_confidence"] = df.apply(
        lambda r: "high"   if float(r.get("ip_total", 0)) >= 120 and not r.get("pcl_inflated")
             else "medium" if float(r.get("ip_total", 0)) >= 60
             else "low",
        axis=1,
    )
    df["pcl_discount"] = (pf - 1.0).round(3)

    return df


def _print_translation_summary(hitters: pd.DataFrame, starters: pd.DataFrame) -> None:
    print("=" * 80)
    print("4단계 KBO 번역 모델 결과 요약 (A/B/C 등급만)")
    print("=" * 80)

    def _abc(df: pd.DataFrame) -> pd.DataFrame:
        return df[df["acquisition_tier"].str.startswith(("A", "B", "C"))].copy()

    h = _abc(hitters).sort_values("kbo_wrc_plus_final", ascending=False)
    s = _abc(starters).sort_values("kbo_era_final", ascending=True)

    h_cols = [
        "full_name", "age", "position", "team_latest",
        "ops", "xwoba", "ops_park_adj", "kbo_ops_final",
        "kbo_wrc_plus_final", "abs_ops_bonus",
        "pcl_inflated", "pcl_discount", "translation_confidence",
        "acquisition_tier", "ssg_fit_score",
    ]
    s_cols = [
        "full_name", "age", "pitch_hand", "team_latest",
        "era", "bb9", "k9", "avg_velo",
        "era_park_adj", "kbo_era_final", "kbo_era_plus_est", "abs_era_bonus",
        "pcl_inflated", "pcl_discount", "translation_confidence",
        "acquisition_tier", "ssg_fit_score",
    ]

    h_disp = [c for c in h_cols if c in h.columns]
    s_disp = [c for c in s_cols if c in s.columns]

    print(f"\n[타자 KBO 예상 성적 (상위 20명, wRC+ 예상치 기준)] — {len(h)}명 중")
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", lambda x: f"{x:.3f}")
    print(h[h_disp].head(20).to_string(index=False))

    print(f"\n[선발 KBO 예상 ERA (상위 20명, ERA 낮은 순)] — {len(s)}명 중")
    print(s[s_disp].head(20).to_string(index=False))

    # 확신도별 분포
    print("\n[타자 번역 신뢰도 분포]")
    for conf, cnt in hitters["translation_confidence"].value_counts().items():
        print(f"  {conf}: {cnt}명")
    print("[선발 번역 신뢰도 분포]")
    for conf, cnt in starters["translation_confidence"].value_counts().items():
        print(f"  {conf}: {cnt}명")
    print("=" * 80)


def main() -> None:
    print("[kbo_translation] 4단계 시작\n")

    hitters  = pd.read_csv(OUT / "candidate_hitter_pool.csv")
    starters = pd.read_csv(OUT / "candidate_starter_pool.csv")

    print(f"  로드: 타자 {len(hitters)}명 / 선발 {len(starters)}명")

    # 타자 번역
    print("\n[1/2] 타자 번역 모델 적용...")
    hitters = translate_hitters(hitters)
    hitters.to_csv(OUT / "translated_hitter_pool.csv", index=False, encoding="utf-8-sig")
    print(f"  → kbo_ops_final 범위: {hitters['kbo_ops_final'].min():.3f} ~ {hitters['kbo_ops_final'].max():.3f}")
    print(f"  → kbo_wrc_plus_final 범위: {hitters['kbo_wrc_plus_final'].min():.0f} ~ {hitters['kbo_wrc_plus_final'].max():.0f}")

    # 선발 번역
    print("\n[2/2] 선발 번역 모델 적용...")
    starters = translate_starters(starters)
    starters.to_csv(OUT / "translated_starter_pool.csv", index=False, encoding="utf-8-sig")
    print(f"  → kbo_era_final 범위: {starters['kbo_era_final'].min():.3f} ~ {starters['kbo_era_final'].max():.3f}")
    print(f"  → kbo_era_plus_est 범위: {starters['kbo_era_plus_est'].min():.0f} ~ {starters['kbo_era_plus_est'].max():.0f}")

    _print_translation_summary(hitters, starters)

    print("\n[완료] 출력:")
    for f in ["translated_hitter_pool.csv", "translated_starter_pool.csv"]:
        print(f"  outputs/tables/{f}")


if __name__ == "__main__":
    main()
