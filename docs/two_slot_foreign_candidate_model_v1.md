# Two-Slot Foreign Candidate Model v1

Updated: 2026-06-22 KST

## Scope

이 모델은 SSG 랜더스의 외국인 영입 후보를 두 슬롯으로만 평가한다.

- `foreign_hitter`: 외국인 타자 1명
- `foreign_starter`: 외국인 선발투수 1명

아시아쿼터와 불펜투수는 제외한다. 친구 모델에서 나온 후보명은 seed 또는 정답으로 사용하지 않는다. 다음 후보는 전체 후보 풀에서 이 모델 기준으로 독립 산출한다.

## Data Policy

사용한다:

- KBO/STATIZ 팀 및 선수 기록
- MLB/MiLB official stats
- MLB Statcast/Savant pitch and batted-ball data
- MLB roster status and transactions

사용하지 않는다:

- 현재 두 슬롯 범위를 벗어나는 후보군
- 사용자 요청으로 제외한 외부 메타데이터, 문헌, source log 계열 문서

## Hitter Model

목표는 단순 OPS 상위 선수가 아니라, MLB에서는 결함이 보였지만 KBO/SSG 환경에서 장점이 살아날 수 있는 타자를 찾는 것이다.

Core filters:

- 2026 AAA 또는 MLB 타석 표본 보유
- OF 또는 1B/DH 현실성
- 나이, 로스터 상태, 최근 출전 흐름이 지나치게 막혀 있지 않을 것

Core features:

- `aaa_ops_2026`
- `mlb_ops_recent`
- `mlb_ops_career`
- `ops_translation_gap_recent = aaa_ops_2026 - mlb_ops_recent`
- `ops_translation_gap_career = aaa_ops_2026 - mlb_ops_career`
- `max_ev`
- `ev90`
- `hard_hit_pct`
- `barrel_pct`
- `sweet_spot_pct`
- `iso_aaa_2026`
- `k_pct_aaa_2026`
- `bb_pct_aaa_2026`

Interpretation:

- OPS gap이 너무 크면 AAA 성적의 MLB 번역 실패 리스크가 있다.
- OPS gap이 0에 가까우면 floor는 안정적일 수 있지만, KBO에 올 현실성은 낮을 수 있다.
- SSG 외국인 타자 후보는 "MLB에서는 부족하지만 AAA 장점이 선명하고, quality-of-contact가 받쳐주는 선수"를 우선 검토한다.

Score sketch:

```text
hitter_score =
  power_quality_score
+ contact_stability_score
+ kbo_translation_score
+ ssg_fit_score
- swing_miss_risk
- mlb_too_good_risk
```

## Starter Model

목표는 구속 상위 선수가 아니라, 문학 구장과 KBO 환경에서 선발로 버틸 수 있는 외국인 투수를 찾는 것이다.

Core filters:

- 2026 AAA 또는 MLB 선발/스윙맨 이닝 보유
- 최근 IP/GS가 선발 전환 가능성을 보여줄 것
- BB9, HR9가 과도하게 높지 않을 것

Core features:

- `aaa_ip_2026`
- `aaa_gs_2026`
- `aaa_ip_per_gs_2026`
- `aaa_k9_2026`
- `aaa_bb9_2026`
- `aaa_hr9_2026`
- `aaa_k_bb_ratio_2026`
- `gb_pct_statcast`
- `mlb_career_bb9`
- `mlb_career_hr9`
- `starter_continuity`

Interpretation:

- 높은 GB%와 낮은 BB9/HR9는 문학 적합성의 핵심 가산점이다.
- 탈삼진은 장점이지만, BB9가 높으면 선발 안정성에서 크게 감점한다.
- MLB 커리어 HR9가 높으면 KBO/문학 홈런 리스크를 별도 경고로 둔다.

Score sketch:

```text
starter_score =
  command_score
+ hr_suppression_score
+ groundball_fit_score
+ starter_durability_score
- walk_risk
- homer_risk
- role_uncertainty
```

## Output Labels

- `target`: 다음 수동 검토에 올릴 후보
- `watch`: 장점은 있지만 결함 또는 표본 문제가 큰 후보
- `reject`: SSG 환경에서 결함을 가리기 어렵거나 시장 현실성이 낮은 후보

## Required Output Columns

각 슬롯 산출물은 최소한 아래 컬럼을 가진다.

- `player_name`
- `slot`
- `current_org`
- `current_team`
- `level`
- `league`
- `age`
- `bats_or_throws`
- `position_or_role`
- `aaa_2026_line`
- `mlb_recent_line`
- `mlb_career_line`
- `ops_translation_gap_recent` for hitters
- `ops_translation_gap_career` for hitters
- `gb_pct_statcast` for starters
- `key_strength`
- `main_defect`
- `ssg_fit_reason`
- `risk_reason`
- `model_score`
- `review_label`

## Next Step

다음 작업은 전체 후보 풀에서 위 feature schema를 채운 뒤, `foreign_hitter_candidates.csv`와 `foreign_starter_candidates.csv`를 생성하는 것이다.
