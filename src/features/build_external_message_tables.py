#!/usr/bin/env python3
"""Build non-STATIZ evidence tables for SSG message discovery."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
ABS_RESULT_DIR = PROJECT_ROOT / "data/external/kbo_abs_paper/result"


def read_csv_any_encoding(path: Path) -> pd.DataFrame:
    for encoding in ["utf-8-sig", "cp949", "euc-kr", "latin1"]:
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def build_abs_summary() -> pd.DataFrame:
    source = read_csv_any_encoding(ABS_RESULT_DIR / "mlb_kbo.csv").rename(columns={"Unnamed: 0": "parameter"})
    source["kbo_2024_minus_2023"] = source["kbo_2024"] - source["kbo_2023"]
    source["kbo_2024_vs_2023_pct"] = source["kbo_2024_minus_2023"] / source["kbo_2023"].replace(0, np.nan)
    source["interpretation"] = source["parameter"].map(
        {
            "alpha": "Estimated half-width/size proxy: lower values imply a narrower called zone.",
            "beta": "Boundary strictness/consistency: higher values imply sharper ball-strike separation.",
            "lambda": "Width-height ratio of the modeled zone.",
            "r": "Rectilinearity: higher values imply a more rule-book rectangular zone.",
            "x0": "Horizontal center calibration.",
            "y0": "Vertical center calibration.",
        }
    )
    return source


def build_hatch_context() -> pd.DataFrame:
    features = pd.read_csv(OUTPUT_DIR / "savant_pitcher_feature_summary_2023_2026.csv")
    screen = pd.read_csv(OUTPUT_DIR / "savant_pitcher_stabilizer_screen_top.csv")

    metrics = [
        "pa",
        "games",
        "start_proxy_games",
        "avg_game_pitches",
        "bb_hbp_pct",
        "hr_pct",
        "woba_allowed",
        "early_1_3_woba_allowed",
        "risp_woba_allowed",
        "hardhit_rate",
        "barrel_rate",
        "three_ball_pitch_rate",
        "zone_rate",
        "first_pitch_nonball_rate",
        "starter_stabilizer_score",
    ]
    eligible = features[(features["starter_stabilizer_eligible"] == True) & (features["game_year"] >= 2025)].copy()  # noqa: E712
    top100 = screen.head(100).copy()

    baselines = []
    for label, frame in [("eligible_2025_2026_median", eligible), ("top100_stabilizer_median", top100)]:
        row = {"group": label, "player_name": "", "game_year": ""}
        for metric in metrics:
            row[metric] = frame[metric].median()
        baselines.append(row)

    hatch = features[features["player_name"].str.contains("Hatch, Thomas", na=False)].copy()
    hatch["group"] = "thomas_hatch_mlb"
    out = pd.concat([hatch[["group", "player_name", "game_year", *metrics]], pd.DataFrame(baselines)], ignore_index=True, sort=False)
    return out


def build_message_candidates() -> pd.DataFrame:
    rows = [
        {
            "priority_rank": 1,
            "message_id": "abs_native_command",
            "message_title": "ABS-native command is the next hidden scouting edge.",
            "korean_message": "KBO의 완전 ABS 환경에서는 '제구가 좋다'는 평판보다, 실제로 룰북 존 안에서 스트라이크를 만들고 3-ball 카운트를 피하는 능력이 더 중요하다. SSG는 대체 외인투수를 ABS-native 커맨드형으로 정의해야 한다.",
            "external_evidence": "Scientific Reports KBO ABS paper; public ABS result CSV; MLB Savant pitcher plate-discipline features.",
            "why_ssg": "SSG가 영입한 해치의 자기소개는 효율/스트라이크지만, MLB Savant 표본에서는 2025 zone_rate and BB/HBP profile이 top stabilizer baseline과 거리가 있다. 즉 메시지는 '해치가 답'이 아니라 '해치형 주장도 검증하는 ABS-native 필터가 필요하다'다.",
            "candidate_filter_translation": "zone_rate, first_pitch_nonball_rate, three_ball_pitch_rate, BB+HBP%, HR%, early-inning wOBA, RISP wOBA.",
            "distinctiveness_1_5": 5,
            "actionability_1_5": 5,
            "evidence_1_5": 4,
            "risk": "KBO pitch-location raw feed를 팀별로 직접 확보하지 못하면 MLB-to-KBO translation으로 남는다.",
            "main_sources": "https://www.nature.com/articles/s41598-025-28142-y | https://github.com/eis-lab/where-do-the-robot-umpires-see | https://baseballsavant.mlb.com/savant-player/thomas-hatch-641672",
        },
        {
            "priority_rank": 2,
            "message_id": "asian_quota_optionality_trap",
            "message_title": "Asian quota should be treated as option value, not as a rotation pillar.",
            "korean_message": "2026 아시아쿼터는 20만 달러 상한의 4번째 외국인 슬롯이다. SSG의 숨은 실수는 이 슬롯을 저비용 depth/option이 아니라 선발 로테이션 기둥처럼 사용한 데 있다.",
            "external_evidence": "KBO 2026 Asia quota rule articles; SSG Takeda-related news; Naver pitching corpus.",
            "why_ssg": "SSG는 김광현 부상과 외인 선발 공백 속에서 아시아쿼터/단기 대체 자원을 선발 안정화 책임으로 끌어올렸다. 룰의 취지는 depth expansion인데, 팀의 사용법은 scarcity solution에 가까웠다.",
            "candidate_filter_translation": "Asian quota = low-cost option: prior-year Asia/Australia playing requirement, $200k cap, replacement availability, role ceiling as swingman/spot starter unless command/workload proof exists.",
            "distinctiveness_1_5": 5,
            "actionability_1_5": 4,
            "evidence_1_5": 4,
            "risk": "아시아쿼터 전체 성패는 표본이 2026 첫해라 아직 불안정하다.",
            "main_sources": "https://www.koreatimes.co.kr/sports/20250123/kbo-to-introduce-asia-quota-system-in-2026 | https://koreajoongangdaily.joins.com/news/2026-04-22/sports/Baseball/Australian-Taiwanese-imports-shine-Japanese-ones-disappoint-under-KBOs-new-Asian-player-quota-/2573432",
        },
        {
            "priority_rank": 3,
            "message_id": "replacement_audition_pipeline",
            "message_title": "The temporary replacement rule is an audition market, not only an emergency patch.",
            "korean_message": "단기 대체 외국인 제도는 부상 대응용이지만, 실제로는 다음 시즌/정식 계약 후보를 미리 테스트하는 시장이 될 수 있다. SSG는 긴급 영입이 아니라 상시 후보군을 보유해야 한다.",
            "external_evidence": "Korea JoongAng Daily article on six-week replacement rule and Ryan Weiss precedent; SSG Hatch/White/Ginjiro articles.",
            "why_ssg": "화이트 장기 이탈 이후 긴지로-해치 흐름은 사후 대응에 가까웠다. 프로젝트 메시지는 '좋은 선수 추천'보다 '상시 대체외인 파이프라인 구축'으로 더 획기적으로 갈 수 있다.",
            "candidate_filter_translation": "Maintain pre-cleared pool: visa feasibility, recent starter workload, health, contract escape route, pitch-shape/ABS command, KBO adaptation interview signals.",
            "distinctiveness_1_5": 4,
            "actionability_1_5": 5,
            "evidence_1_5": 4,
            "risk": "실제 계약 가능성/비자/소속팀 buyout 데이터가 추가로 필요하다.",
            "main_sources": "https://www.koreajoongangdaily.com/sports/kbo-clubs-hold-steady-on-foreign-players-for-now/12000017 | https://www.yna.co.kr/view/AKR20260606021300007",
        },
        {
            "priority_rank": 4,
            "message_id": "bullpen_fatigue_non_linear",
            "message_title": "One starter inning is worth more than one inning because bullpen fatigue is nonlinear.",
            "korean_message": "SSG의 외인 선발 보강 효과는 단순히 ERA 개선이 아니라, 불펜의 숨은 피로 누적을 줄이는 데 있다. 그래서 5.0이닝 평균 투수보다 6.0이닝 반복 가능성이 있는 투수가 더 큰 레버리지다.",
            "external_evidence": "Pitcher fatigue/workload literature; Naver pitching news signals on bullpen load; MLB workload concepts.",
            "why_ssg": "외부 기사에서도 SSG의 연패/반등 논의는 외인 선발 부진과 불펜 부담을 같이 언급한다. 기존 정량 결과와 결합하면 선발 1이닝의 가치가 과소평가되고 있다.",
            "candidate_filter_translation": "80-90 pitch history, starts reaching third time through order, low three-ball rate, recovery/rest history, no sudden workload spikes.",
            "distinctiveness_1_5": 4,
            "actionability_1_5": 4,
            "evidence_1_5": 3,
            "risk": "팀 내부 불펜 가용성, 트레이닝, warm-up pitch 데이터가 없으면 피로 크기는 추정에 그친다.",
            "main_sources": "https://pmc.ncbi.nlm.nih.gov/articles/PMC6673423/ | https://www.drivelinebaseball.com/2020/05/starting-pitching-workloads-part-1/",
        },
        {
            "priority_rank": 5,
            "message_id": "munhak_summer_damage_control",
            "message_title": "In summer air, HR suppression may be more valuable than raw strikeout ceiling.",
            "korean_message": "문학/인천 여름 환경까지 고려하면 SSG 투수 영입은 탈삼진보다 피홈런과 barrel 억제가 먼저일 수 있다. 날씨가 타구 비거리를 돕는 환경에서는 실투 한 번의 비용이 커진다.",
            "external_evidence": "Weather and park-factor research on temperature/air density and home run carry; MLB park factor methodology.",
            "why_ssg": "SSG는 이미 초반 실점과 피홈런/볼넷이 문제인 팀이다. 여름 홈경기 환경이 장타 리스크를 키우면 '볼넷 줄이고 HR 억제'형 선발 메시지가 더 강해진다.",
            "candidate_filter_translation": "HR%, barrel%, hard-hit%, fly-ball damage, sinker/cutter ground-ball shape, no-doubter/xHR gap, warm-weather splits.",
            "distinctiveness_1_5": 3,
            "actionability_1_5": 3,
            "evidence_1_5": 3,
            "risk": "인천 구장별 실측 기상/바람/타구 데이터 결합이 아직 부족하다.",
            "main_sources": "https://journals.ametsoc.org/view/journals/wcas/5/4/wcas-d-13-00002_1.pdf | https://blogs.fangraphs.com/the-park-factors-are-in-the-pudding/",
        },
    ]
    out = pd.DataFrame(rows)
    out["total_score"] = out[["distinctiveness_1_5", "actionability_1_5", "evidence_1_5"]].sum(axis=1)
    return out.sort_values(["total_score", "priority_rank"], ascending=[False, True])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    abs_summary = build_abs_summary()
    hatch_context = build_hatch_context()
    message_candidates = build_message_candidates()

    abs_summary.to_csv(OUTPUT_DIR / "external_abs_zone_shift_summary.csv", index=False)
    hatch_context.to_csv(OUTPUT_DIR / "external_hatch_savant_context.csv", index=False)
    message_candidates.to_csv(OUTPUT_DIR / "external_message_candidates_v1.csv", index=False)

    print("wrote", OUTPUT_DIR / "external_abs_zone_shift_summary.csv")
    print("wrote", OUTPUT_DIR / "external_hatch_savant_context.csv")
    print("wrote", OUTPUT_DIR / "external_message_candidates_v1.csv")
    print(message_candidates[["priority_rank", "message_id", "total_score", "message_title"]].to_string(index=False))


if __name__ == "__main__":
    main()
