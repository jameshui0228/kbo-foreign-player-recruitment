# Message Discovery Findings

업데이트: 2026-06-11 KST

## Current Leading Message Candidate

아직 최종 메시지는 아니다. 또한 이 문서는 2023-2025 중심의 첫 pass 결과였으므로, 2026 현재 시즌 분석은 `docs/ssg_2026_current_findings.md`를 우선한다.

첫 pass에서는 다음 방향이 강해 보였다.

> SSG 외야의 문제는 단순한 장타 부족이 아니라, 장타 신호가 출루와 안정적 득점 생산성으로 충분히 번역되지 않는 구조일 수 있다.

2026 현재 데이터까지 반영하면 이 메시지는 더 구체화되어야 한다.

> SSG는 외야 장타가 없는 팀이 아니다. 2026 현재 더 구체적인 구멍은 DH와 외야 중심타선의 기능이다. 따라서 대체 외국인 외야수는 단순 거포가 아니라, 코너 외야/DH를 오가며 3-5번에서 볼넷과 장타를 동시에 유지할 수 있는 타자여야 한다.

## Evidence Layer 1: News/Text

Naver Search News metadata를 넓게 수집한 결과, strict SSG/랜더스 snippet set에서 반복 신호는 다음과 같다.

| signal | records |
|---|---:|
| power | 2,358 |
| injury_depth | 1,692 |
| run_creation | 1,611 |
| onbase_discipline | 1,192 |
| foreign_hitter | 1,155 |
| outfield | 988 |

텍스트는 `장타/홈런`, `부상/뎁스`, `타선/득점권`, `외국인 타자`, `출루/존/삼진`, `외야`를 반복적으로 건드린다.

## Evidence Layer 2: STATIZ SSG Splits

2023-2025 SSG 외야의 핵심 rank는 다음과 같다.

| metric | 2023 | 2024 | 2025 | read |
|---|---:|---:|---:|---|
| HR rank | 3 | 1 | 1 | 장타 생산량은 강하다. |
| ISO rank | 3 | 3 | 5 | 순장타도 상위권 또는 중상위권이다. |
| OPS rank | 4 | 5 | 5 | 전체 생산성은 장타 순위만큼 높지 않다. |
| OBP rank | 4 | 9 | 7 | 출루 쪽에서 하락 신호가 있다. |
| BB% rank | 9 | 10 | 9 | 볼넷/존 판단 쪽 병목이 강하다. |
| K% rank | 4 | 7 | 8 | 삼진 억제도 최근 약해졌다. |

이 조합은 "거포가 필요하다"보다 "장타는 있는데 출루/존 판단/컨택 리스크 때문에 득점 생산성이 제한된다"는 메시지를 더 강하게 지지한다.

## Evidence Layer 3: Lineup/OF Subsplits

SSG 전체 3-5번 타순은 2023년에는 OPS 2위였지만 2024년 6위, 2025년 8위로 떨어졌다. 같은 기간 3-5번 타순 BB% rank는 10위, 10위, 8위였다.

SSG 외야 3-5번 타순도 BB% rank가 2023년 9위, 2024년 9위, 2025년 7위로 낮다.

따라서 대체 외국인 외야수는 단순 HR 추가보다 `중심타선에서 볼넷과 장타를 동시에 유지하는 선수`가 더 좋은 문제 정의일 수 있다.

## Evidence Layer 4: Savant Feature Screen

Savant 2023-2026 pitch/play-level data로 다음 feature를 만들었다.

- `bb_pct`
- `k_pct`
- `barrel_rate`
- `hardhit_rate`
- `low_velo_xwoba`
- `break_off_xwoba`
- `chase_rate`
- `nonfast_chase_rate`
- `hitter_count_swing_rate`
- `hitter_count_xwoba`
- `same_field_air_rate_proxy`

산출물:

- `outputs/tables/savant_hitter_feature_summary_2023_2026.csv`
- `outputs/tables/savant_hitter_message_screen_top.csv`
- `outputs/tables/savant_hitter_flawed_profile_screen.csv`

첫 screen은 슈퍼스타를 먼저 올리므로 영입 후보 추천에 직접 쓰면 안 된다. 두 번째 flawed profile screen은 `장타질/존 판단/변화구 대응은 보이지만 삼진, wOBA, chase 등 결함이 있는 선수`를 따로 남긴다. 이 screen은 다음 단계에서 외야수 여부, 40-man status, 계약/부상/최근 DFA 여부로 강하게 걸러야 한다.

## Current Project Message Status

| candidate message | status | reason |
|---|---|---|
| SSG needs more raw power | weakened | 텍스트에는 많지만 STATIZ HR/ISO가 반박한다. |
| SSG needs OF run creation, not just HR | strong candidate | 텍스트 run_creation + STATIZ OPS/OBP/BB% 병목이 맞물린다. |
| SSG should target a flawed but disciplined power OF | strong candidate | Savant에서 power + BB/low chase + flaw profile이 실제로 존재한다. |
| SSG injury/depth is the main message | pending | 텍스트는 강하지만 injury-days/roster absence table이 아직 없다. |

## Next Validation

1. 외야수 여부와 40-man/계약 상태를 붙여 Savant flawed screen을 실제 후보군으로 줄인다.
2. SSG 현재 외국인 타자/외야수별 PA 공백과 부상 뉴스 태그를 연결한다.
3. KBO 외국인 타자 성공 사례와 비교해 `disciplined power flaw` 유형이 KBO에서 살아남았는지 backtest한다.
