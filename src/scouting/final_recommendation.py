"""
최종 SSG Fit 랭킹 & 선수 추천 - 6단계
========================================
입력:
  outputs/tables/backtest_hitter_pool.csv
  outputs/tables/backtest_starter_pool.csv

종합 점수 계산:
  composite_score = 0.40 × ssg_fit_normalized
                  + 0.40 × kbo_perf_normalized
                  + 0.20 × tier_weight
  (A/B/C 등급만 대상)
"""
from __future__ import annotations
import pathlib
import pandas as pd
import numpy as np

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "outputs" / "tables"


# ── 등급별 tier weight ─────────────────────────────────────────────────────
TIER_WEIGHT = {
    "A_mlb_reject": 1.0,
    "A_dfa_milb":   0.85,
    "B_fa_veteran": 0.70,
    "B_fa_mid":     0.65,
    "B_fa_unknown": 0.60,
    "C_outrighted": 0.50,
}


def _normalize(series: pd.Series, ascending: bool = True) -> pd.Series:
    """min-max 정규화 → 0~1."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    norm = (series - mn) / (mx - mn)
    return norm if ascending else (1 - norm)


def score_hitters(df: pd.DataFrame) -> pd.DataFrame:
    """
    타자 종합 점수:
      ssg_fit_score (0-100): SSG 약점 대응 적합도
      kbo_wrc_plus_final: 4단계 KBO wRC+ 예상치
      tier_weight: 영입 현실성
    """
    df = df.copy()
    abc = df["acquisition_tier"].str.startswith(("A","B","C"))
    pool = df[abc].copy()

    pool["w_ssg_fit"]   = _normalize(pool["ssg_fit_score"], ascending=True)
    pool["w_kbo_wrc"]   = _normalize(pool["kbo_wrc_plus_final"], ascending=True)
    pool["w_tier"]      = pool["acquisition_tier"].map(TIER_WEIGHT).fillna(0.5)

    pool["composite_score"] = (
        0.40 * pool["w_ssg_fit"] +
        0.40 * pool["w_kbo_wrc"] +
        0.20 * pool["w_tier"]
    ).round(4)

    pool = pool.sort_values("composite_score", ascending=False).reset_index(drop=True)
    pool["final_rank"] = pool.index + 1
    return pool


def score_starters(df: pd.DataFrame) -> pd.DataFrame:
    """
    선발 종합 점수:
      ssg_fit_score (0-100): SSG 약점 대응 적합도
      kbo_era_final: 4단계 KBO ERA 예상치 (낮을수록 좋음)
      tier_weight: 영입 현실성
    """
    df = df.copy()
    abc = df["acquisition_tier"].str.startswith(("A","B","C"))
    pool = df[abc].copy()

    pool["w_ssg_fit"]   = _normalize(pool["ssg_fit_score"], ascending=True)
    pool["w_kbo_era"]   = _normalize(pool["kbo_era_final"], ascending=False)  # 낮을수록 좋음
    pool["w_tier"]      = pool["acquisition_tier"].map(TIER_WEIGHT).fillna(0.5)

    pool["composite_score"] = (
        0.40 * pool["w_ssg_fit"] +
        0.40 * pool["w_kbo_era"] +
        0.20 * pool["w_tier"]
    ).round(4)

    pool = pool.sort_values("composite_score", ascending=False).reset_index(drop=True)
    pool["final_rank"] = pool.index + 1
    return pool


def _print_final_report(hitters: pd.DataFrame, starters: pd.DataFrame) -> None:
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 240)
    pd.set_option("display.float_format", lambda x: f"{x:.3f}")

    print("=" * 90)
    print("6단계 SSG Landers 외국인 선수 최종 추천 보고서")
    print("=" * 90)

    # ── 타자 ──────────────────────────────────────────────────────────────
    h_cols = [
        "final_rank","full_name","age","position","bat_side",
        "ssg_fit_score","kbo_wrc_plus_final","kbo_ops_final",
        "bt_success_category","bt_warning_flags",
        "acquisition_tier","composite_score",
    ]
    h_disp = [c for c in h_cols if c in hitters.columns]
    print(f"\n▶ 타자 후보 최종 랭킹 (상위 10명)")
    print(hitters[h_disp].head(10).to_string(index=False))

    # ── 선발 ──────────────────────────────────────────────────────────────
    s_cols = [
        "final_rank","full_name","age","pitch_hand",
        "ssg_fit_score","kbo_era_final","kbo_era_plus_est","bb9","k9","avg_velo",
        "bt_success_category","bt_warning_flags",
        "acquisition_tier","composite_score",
    ]
    s_disp = [c for c in s_cols if c in starters.columns]
    print(f"\n▶ 선발 후보 최종 랭킹 (상위 10명)")
    print(starters[s_disp].head(10).to_string(index=False))

    # ── 최종 추천 ─────────────────────────────────────────────────────────
    rec_h = hitters.iloc[0]
    rec_s = starters.iloc[0]

    h2 = hitters.iloc[1] if len(hitters) > 1 else None
    s2 = starters.iloc[1] if len(starters) > 1 else None

    print("\n" + "=" * 90)
    print("★ SSG Landers 2026-27 외국인 선수 최종 추천")
    print("=" * 90)

    print(f"""
[외국인 타자 추천 #1]
  선수명: {rec_h.get('full_name')}
  나이·포지션·타격: {rec_h.get('age')}세 | {rec_h.get('position')} | {rec_h.get('bat_side', '?')}타
  영입 등급: {rec_h.get('acquisition_tier')} (MLB 처분/DFA 확인)
  AAA xwOBA: {rec_h.get('xwoba', 'N/A'):.3f}  |  PCL 보정 후 KBO OPS 예상: {rec_h.get('kbo_ops_final', 0):.3f}
  KBO wRC+ 예상: {rec_h.get('kbo_wrc_plus_final', 0):.1f} (역사적 성공군 평균 137.3 대비)
  SSG Fit: {rec_h.get('ssg_fit_score', 0):.0f}pt  |  종합 점수: {rec_h.get('composite_score', 0):.4f}
  성공 카테고리: {rec_h.get('bt_success_category')}
  경고 플래그: {rec_h.get('bt_warning_flags', '-')}
  추천 근거:
    · SSG 1루주자 OPS 10위 보완: chase율 낮음 → 볼넷 생산 + 주자 진루 압박
    · KBO 내성 결함: K%높음+xwOBA높음 → KBO 투수 수준에서 K%↓, 파워 유지
    · MLB에서 실패 확인 → KBO 시장 접근 현실적""")

    if h2 is not None:
        print(f"""
[외국인 타자 대안 #2]
  선수명: {h2.get('full_name')} | {h2.get('age')}세 | {h2.get('position')} | {h2.get('bat_side','?')}타
  영입 등급: {h2.get('acquisition_tier')}
  KBO wRC+ 예상: {h2.get('kbo_wrc_plus_final', 0):.1f}  |  SSG Fit: {h2.get('ssg_fit_score', 0):.0f}pt
  성공 카테고리: {h2.get('bt_success_category')}
  경고: {h2.get('bt_warning_flags', '-')}""")

    print(f"""
[외국인 선발 추천 #1]
  선수명: {rec_s.get('full_name')}
  나이·투구: {rec_s.get('age')}세 | {rec_s.get('pitch_hand', '?')}완
  영입 등급: {rec_s.get('acquisition_tier')}
  AAA ERA: {rec_s.get('era', 0):.3f}  BB9: {rec_s.get('bb9', 0):.2f}  K9: {rec_s.get('k9', 0):.2f}  구속: {rec_s.get('avg_velo', 0):.1f}mph
  KBO ERA 예상: {rec_s.get('kbo_era_final', 0):.3f}  (ERA+: {rec_s.get('kbo_era_plus_est', 0):.0f})
  SSG Fit: {rec_s.get('ssg_fit_score', 0):.0f}pt  |  종합 점수: {rec_s.get('composite_score', 0):.4f}
  성공 카테고리: {rec_s.get('bt_success_category')}
  경고 플래그: {rec_s.get('bt_warning_flags', '-')}
  추천 근거:
    · SSG 초반 이닝 약점 보완: 선발이 초반 장악 → 타선이 주도권 회복
    · BB9 매우 낮음(제구 탁월) → KBO ABS 일관성 이득 + 볼넷 실점 최소화
    · KBO 내성 결함: 저구속(89-92mph)+좋은 커맨드 → KBO 평균 구속↓ 환경에서 생존
    · MLB 이닝 소화 패턴 → KBO 6이닝↑ 기대 가능""")

    if s2 is not None:
        print(f"""
[외국인 선발 대안 #2]
  선수명: {s2.get('full_name')} | {s2.get('age')}세 | {s2.get('pitch_hand','?')}완
  영입 등급: {s2.get('acquisition_tier')}
  KBO ERA 예상: {s2.get('kbo_era_final', 0):.3f} (ERA+: {s2.get('kbo_era_plus_est', 0):.0f})  |  SSG Fit: {s2.get('ssg_fit_score', 0):.0f}pt
  성공 카테고리: {s2.get('bt_success_category')}
  경고: {s2.get('bt_warning_flags', '-')}""")

    print(f"""
[SSG 현황 맥락]
  2026 타자: 기예르모 에레디아 활동 중 (3년 연속 wRC+135-141, 최고 외국인 타자)
             → 에레디아 유지 시 이번 추천 타자는 2027 영입 또는 시즌 중 대체 후보
  2026 선발: 미치 화이트·히라모토 긴지로 시즌 중 교체 → 선발 보강 니즈 현재 존재
             앤서니 베니지아노·타케다 쇼타·토머스 해치 재계약/진행 중
             → 선발 추천은 즉시 영입 가능성 높음

[모델 한계 및 주의사항]
  1. 번역 모델 구간 신뢰도: PCL 인플레이션 선수는 xwOBA park-neutral 사용으로 보정,
     그러나 샘플 크기(2-3시즌 평균)로 인한 변동성 있음
  2. Savant 없는 선수(A_dfa_milb 일부): MiLB 전용 기록만 있어 번역 신뢰도 medium/low
  3. KBO 적응 변수(언어·문화·이동 피로 등) 정량화 불가
  4. 에이전트 협상/계약 의향은 실시간 확인 필요
  5. 부상 이력 스크리닝은 별도 필요 (본 모델 미반영)
""")
    print("=" * 90)


def main() -> None:
    print("[final_recommendation] 6단계 시작\n")

    hitters  = pd.read_csv(OUT / "backtest_hitter_pool.csv")
    starters = pd.read_csv(OUT / "backtest_starter_pool.csv")

    print(f"  로드: 타자 {len(hitters)}명 / 선발 {len(starters)}명")

    hitters_ranked  = score_hitters(hitters)
    starters_ranked = score_starters(starters)

    hitters_ranked.to_csv(OUT  / "final_hitter_ranking.csv",   index=False, encoding="utf-8-sig")
    starters_ranked.to_csv(OUT / "final_starter_ranking.csv",  index=False, encoding="utf-8-sig")

    _print_final_report(hitters_ranked, starters_ranked)

    print("\n[완료] 출력:")
    for f in ["final_hitter_ranking.csv", "final_starter_ranking.csv"]:
        print(f"  outputs/tables/{f}")


if __name__ == "__main__":
    main()
