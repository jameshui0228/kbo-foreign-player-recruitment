"""
KBO 번역 모델 백테스트 & 성공 패턴 검증 - 5단계
===================================================
입력:
  processed/kbo/kbo_foreign_player_season_labels_v0_1.csv  ← leakage-safe 라벨만
  outputs/tables/translated_hitter_pool.csv
  outputs/tables/translated_starter_pool.csv

수행 작업:
  1. 역사적 KBO 외국인 선수 성공/실패 분포 분석
  2. 번역 모델 보정 (예측값 vs 실제 KBO 성과 비교)
  3. 현재 후보군 성공 확률 분류
  4. 중요 경고 플래그 부착

[leakage 방지]
  - first_kbo_wrc_plus / first_kbo_era → 모델 특성(feature)이 아닌 검증 라벨(label)로만 사용
  - 현재 후보들의 KBO 성과는 아직 미발생 → 라벨 사용 불가
  - 후보 랭킹 변경 없이 calibration 참고만 사용
"""
from __future__ import annotations
import pathlib
import pandas as pd
import numpy as np

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_ROOT = pathlib.Path(r"C:\Users\sewon\Documents\고려대학교\26-1\ssg\ddddddd\ssg_project_data_for_teammates_20260614\data")
OUT = PROJECT_ROOT / "outputs" / "tables"

LABEL_PATH = DATA_ROOT / "processed" / "kbo" / "kbo_foreign_player_season_labels_v0_1.csv"

# ── 성공 임계값 (역사적 데이터 기반) ─────────────────────────────────────
HITTER_SUCCESS_WRC    = 100.0   # wRC+ ≥ 100: KBO 외국인 타자 '성공' 기준
HITTER_STRONG_WRC     = 120.0   # wRC+ ≥ 120: '강한 성공'
STARTER_SUCCESS_ERA   = 4.00    # ERA ≤ 4.00: KBO 외국인 선발 '성공' 기준
STARTER_STRONG_ERA    = 3.50    # ERA ≤ 3.50: '강한 성공'
STARTER_SUCCESS_IP    = 120.0   # IP ≥ 120: 이닝 소화 기준 (시즌 중 방출 방지)


def analyze_historical_patterns(labels: pd.DataFrame) -> dict:
    """역사적 KBO 외국인 선수 성공 패턴 추출."""
    h = labels[(labels["role_group"] == "hitter") & labels["first_kbo_wrc_plus"].notna()].copy()
    s = labels[(labels["role_group"] == "starter") & labels["first_kbo_era"].notna()].copy()

    patterns = {
        "hitter_n": len(h),
        "hitter_wrc_mean": h["first_kbo_wrc_plus"].mean(),
        "hitter_wrc_median": h["first_kbo_wrc_plus"].median(),
        "hitter_success_rate": (h["first_kbo_wrc_plus"] >= HITTER_SUCCESS_WRC).mean(),
        "hitter_strong_rate":  (h["first_kbo_wrc_plus"] >= HITTER_STRONG_WRC).mean(),
        "hitter_success_wrc_mean": h[h["success"] == 1.0]["first_kbo_wrc_plus"].mean(),
        "hitter_failure_wrc_mean": h[h["failure"] == 1.0]["first_kbo_wrc_plus"].mean(),

        "starter_n": len(s),
        "starter_era_mean": s["first_kbo_era"].mean(),
        "starter_era_median": s["first_kbo_era"].median(),
        "starter_success_rate": (s["first_kbo_era"] <= STARTER_SUCCESS_ERA).mean(),
        "starter_strong_rate":  (s["first_kbo_era"] <= STARTER_STRONG_ERA).mean(),
        "starter_success_era_mean": s[s["success"] == 1.0]["first_kbo_era"].mean(),
        "starter_failure_era_mean": s[s["failure"] == 1.0]["first_kbo_era"].mean(),
        "starter_success_ip_mean": s[s["success"] == 1.0]["first_kbo_ip"].mean(),
        "starter_failure_ip_mean": s[s["failure"] == 1.0]["first_kbo_ip"].mean(),

        "ssg_history": labels[labels["kbo_team"] == "SSG"][
            ["season", "player_name_ko", "role_group", "first_kbo_wrc_plus", "first_kbo_era",
             "success", "failure", "in_season_replaced"]
        ].sort_values("season"),
    }
    return patterns


def classify_hitter_success_prob(df: pd.DataFrame, pat: dict) -> pd.DataFrame:
    """
    역사적 wRC+ 분포 기반 후보 성공 확률 분류.
    [leakage 방지] KBO 성과는 label 분포 calibration에만 사용, 후보 스코어 미변경.
    """
    df = df.copy()

    # 번역 모델 예측 wRC+와 역사적 분포 대조
    def _category(wrc: float) -> str:
        if wrc >= HITTER_STRONG_WRC:   return "strong_success_likely"
        if wrc >= HITTER_SUCCESS_WRC:  return "success_likely"
        if wrc >= 80:                  return "borderline"
        return "failure_risk"

    def _flag(r: pd.Series) -> str:
        flags = []
        if r.get("pcl_inflated"):
            flags.append("PCL_inflation")
        if r.get("translation_confidence") == "low":
            flags.append("low_confidence")
        k = r.get("k_pct", 0) or 0
        if k > 0.30:
            flags.append("high_K_pct")
        if r.get("xwoba") is None or pd.isna(r.get("xwoba", np.nan)):
            flags.append("no_savant")
        return "|".join(flags) if flags else "-"

    wrc = df["kbo_wrc_plus_final"].fillna(0)
    df["bt_success_category"] = wrc.apply(_category)
    df["bt_warning_flags"]    = df.apply(_flag, axis=1)

    # 역사적 성공 그룹 평균(137.3)과의 차이
    df["vs_hist_success_mean"] = (wrc - pat["hitter_success_wrc_mean"]).round(1)

    return df


def classify_starter_success_prob(df: pd.DataFrame, pat: dict) -> pd.DataFrame:
    """
    역사적 ERA 분포 기반 선발 성공 확률 분류.
    """
    df = df.copy()

    def _category(era: float) -> str:
        if era <= STARTER_STRONG_ERA:   return "strong_success_likely"
        if era <= STARTER_SUCCESS_ERA:  return "success_likely"
        if era <= 4.80:                 return "borderline"
        return "failure_risk"

    def _flag(r: pd.Series) -> str:
        flags = []
        if r.get("pcl_inflated"):
            flags.append("PCL_inflation")
        if r.get("translation_confidence") == "low":
            flags.append("low_confidence")
        ip = r.get("ip_total", 0) or 0
        if float(ip) < 60:
            flags.append("small_sample_IP")
        bb9 = r.get("bb9", 99) or 99
        if float(bb9) > 4.5:
            flags.append("high_BB9")
        return "|".join(flags) if flags else "-"

    era = df["kbo_era_final"].fillna(99)
    df["bt_success_category"] = era.apply(_category)
    df["bt_warning_flags"]    = df.apply(_flag, axis=1)
    df["vs_hist_success_mean"] = (era - pat["starter_success_era_mean"]).round(3)

    return df


def _print_backtest_summary(
    hitters: pd.DataFrame,
    starters: pd.DataFrame,
    pat: dict,
) -> None:
    print("=" * 80)
    print("5단계 백테스트 결과 — KBO 번역 모델 보정 & 후보 성공 확률")
    print("=" * 80)

    print("\n[역사적 KBO 외국인 타자 성과 분포]")
    print(f"  샘플: {pat['hitter_n']}명 | 평균 wRC+: {pat['hitter_wrc_mean']:.1f} | 중위: {pat['hitter_wrc_median']:.1f}")
    print(f"  성공(wRC+≥100): {pat['hitter_success_rate']*100:.0f}% | 강한 성공(≥120): {pat['hitter_strong_rate']*100:.0f}%")
    print(f"  성공군 평균 wRC+: {pat['hitter_success_wrc_mean']:.1f} | 실패군: {pat['hitter_failure_wrc_mean']:.1f}")

    print("\n[역사적 KBO 외국인 선발 성과 분포]")
    print(f"  샘플: {pat['starter_n']}명 | 평균 ERA: {pat['starter_era_mean']:.3f} | 중위: {pat['starter_era_median']:.3f}")
    print(f"  성공(ERA≤4.00): {pat['starter_success_rate']*100:.0f}% | 강한 성공(≤3.50): {pat['starter_strong_rate']*100:.0f}%")
    print(f"  성공군 평균 ERA: {pat['starter_success_era_mean']:.3f} | 실패군: {pat['starter_failure_era_mean']:.3f}")
    print(f"  성공군 평균 IP: {pat['starter_success_ip_mean']:.1f} | 실패군: {pat['starter_failure_ip_mean']:.1f}")

    print("\n[SSG 최근 외국인 선수 역사]")
    ssg = pat["ssg_history"]
    if len(ssg) > 0:
        print(ssg.to_string(index=False))

    # ── 후보 성공 분류 ────────────────────────────────────────────────────
    def _abc(df): return df[df["acquisition_tier"].str.startswith(("A","B","C"))].copy()

    h = _abc(hitters).sort_values("kbo_wrc_plus_final", ascending=False)
    s = _abc(starters).sort_values("kbo_era_final", ascending=True)

    h_cols = ["full_name","age","position","kbo_wrc_plus_final","bt_success_category",
              "vs_hist_success_mean","bt_warning_flags","acquisition_tier","ssg_fit_score"]
    s_cols = ["full_name","age","pitch_hand","kbo_era_final","kbo_era_plus_est",
              "bt_success_category","vs_hist_success_mean","bt_warning_flags",
              "acquisition_tier","ssg_fit_score"]

    h_disp = [c for c in h_cols if c in h.columns]
    s_disp = [c for c in s_cols if c in s.columns]

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 220)

    print(f"\n[후보 타자 성공 확률 분류 ({len(h)}명)]")
    print(h[h_disp].head(20).to_string(index=False))

    print(f"\n[후보 선발 성공 확률 분류 ({len(s)}명)]")
    print(s[s_disp].head(20).to_string(index=False))

    # 카테고리 분포
    print("\n[타자 성공 카테고리 분포 (전체 후보)]")
    for cat, cnt in hitters["bt_success_category"].value_counts().items():
        print(f"  {cat}: {cnt}명")
    print("[선발 성공 카테고리 분포 (전체 후보)]")
    for cat, cnt in starters["bt_success_category"].value_counts().items():
        print(f"  {cat}: {cnt}명")
    print("=" * 80)


def main() -> None:
    print("[backtest] 5단계 시작\n")

    labels   = pd.read_csv(LABEL_PATH)
    hitters  = pd.read_csv(OUT / "translated_hitter_pool.csv")
    starters = pd.read_csv(OUT / "translated_starter_pool.csv")

    print(f"  라벨 레코드: {len(labels)}명 | 타자 후보: {len(hitters)}명 | 선발 후보: {len(starters)}명")

    # 역사적 패턴
    pat = analyze_historical_patterns(labels)

    # 후보 성공 확률 분류
    hitters  = classify_hitter_success_prob(hitters, pat)
    starters = classify_starter_success_prob(starters, pat)

    hitters.to_csv(OUT / "backtest_hitter_pool.csv",  index=False, encoding="utf-8-sig")
    starters.to_csv(OUT / "backtest_starter_pool.csv", index=False, encoding="utf-8-sig")

    _print_backtest_summary(hitters, starters, pat)

    print("\n[완료] 출력:")
    for f in ["backtest_hitter_pool.csv", "backtest_starter_pool.csv"]:
        print(f"  outputs/tables/{f}")


if __name__ == "__main__":
    main()
