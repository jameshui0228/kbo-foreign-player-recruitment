# Methodology

접근일: 2026-06-11 KST

## 1. Ranking Philosophy

이 프로젝트의 랭킹은 단일 예측 모델이 아니라 다음 요소의 결합이다.

```text
Final Acquisition Score
  = weighted(
      Raw Skill Score,
      SSG Need Fit Score,
      KBO Translation Score,
      Availability Score,
      Risk Score
    )

Risk Score = 100 - Risk Penalty
```

모든 score는 0-100 scale로 정규화한다. `Risk Penalty`는 높을수록 위험하고, 최종 표에는 해석 편의를 위해 `risk_score`를 100점 만점의 안정성 점수로 함께 제공한다.

현재 1차 우선순위는 `대체 외국인 외야수`다. 이 역할에서는 "가장 좋은 선수"보다 "SSG가 다른 팀보다 더 잘 활용할 수 있는 특색 있는 선수"를 우선한다. 따라서 타자 랭킹에서는 일반 raw skill보다 다음 두 가지를 특별히 크게 본다.

- `Hidden SSG Edge`: SSG의 외야/중심타선/장타 결핍, 문학 구장, ABS, KBO 투구 생태계에서 후보 장점이 증폭되는가.
- `Acquirable Flaw`: MLB/MiLB에서는 약점으로 가격이 낮아졌지만 KBO/SSG에서는 감당 가능한 결함인가.

## 2. Draft Role Weights

EDA 전 초안이며, SSG 전력 진단과 historical backtest 이후 조정한다.

### Foreign hitter/outfielder

| component | weight | reason |
|---|---:|---|
| Hidden SSG Edge Score | 0.25 | SSG 외야/장타/라인업 결핍과 후보의 특수 강점이 맞아야 한다. |
| KBO Translation Score | 0.20 | 타구 질만 좋아도 변화구/ABS/컨택 전환이 안 되면 실패한다. |
| Acquirable Flaw Score | 0.20 | KBO에 올 수 있는 이유가 되는 결함이 SSG에서는 감당 가능한지 본다. |
| Raw Skill Score | 0.15 | 장타, 타구질, 출루 능력의 기본 수준. 단, OPS 순위표가 되지 않도록 낮게 둔다. |
| Availability Score | 0.10 | 현실적으로 올 수 있어야 한다. |
| Risk Score | 0.10 | 부상, 타구속도 하락, 극단적 split을 제어한다. |

타자 후보는 1차적으로 외야수를 우선한다. 1루/DH 전용 선수는 장타 upside가 압도적이거나 SSG의 수비 배치상 외야 수비 결함을 감당할 수 있다는 근거가 있을 때만 보조 후보로 둔다.

### Foreign starter

| component | weight | reason |
|---|---:|---|
| SSG Need Fit Score | 0.20 | 선발 이닝/국내 선발 뎁스와 직접 연결. |
| Raw Skill Score | 0.25 | 패스트볼/주무기/헛스윙/구종 조합. |
| Command Score | 0.20 | KBO 전환에서 볼넷은 가장 치명적인 리스크 중 하나. |
| Durability/Inning Score | 0.15 | 외국인 선발은 120-150이닝 기대가 핵심. |
| KBO/ABS Translation Score | 0.10 | ABS, 존 공략, KBO 투타 스타일 적응. |
| Availability/Risk Score | 0.10 | 계약/부상/구속 하락 관리. |

### Asian quota reliever

| component | weight | reason |
|---|---:|---|
| SSG Bullpen Need Fit Score | 0.25 | 불펜의 구체적 결함과 맞아야 한다. |
| Short Burst Stuff Score | 0.25 | 짧은 이닝에서 헛스윙을 만들 수 있어야 한다. |
| Low Walk Relief Score | 0.20 | 고레버리지 볼넷은 즉시 실점으로 연결된다. |
| Durability/Leverage Score | 0.15 | 연투와 7-9회 역할 적응. |
| Availability Score | 0.15 | NPB 1군/팜/독립리그에서 실제 이동 가능성. |

## 3. Baseline Ladder

복잡한 모델보다 해석 가능한 baseline부터 시작한다.

1. Rule-based ranking
2. Z-score weighted ranking
3. Similarity-based ranking to historical KBO successes
4. Logistic regression / Ridge
5. RandomForest / ExtraTrees
6. LightGBM / CatBoost / XGBoost
7. Ensemble ranking

데이터가 작으면 1-4번의 설명 가능성과 ranking stability를 우선한다.

## 4. Historical Transfer Backtest

원칙:

- 2023년에 KBO에 온 선수를 평가할 때는 2022년까지의 MLB/MiLB/NPB 데이터만 feature로 사용한다.
- KBO 입단 후 성적은 `success`, `strong_success`, `failure` label로만 사용한다.
- 선수 단위 GroupKFold와 arrival year holdout을 함께 고려한다.

Validation modes:

| mode | purpose |
|---|---|
| Leave-One-Year-Out | 특정 연도 foreign class에 과적합됐는지 확인 |
| Arrival year holdout | 실제 영입 시점의 미래 예측 상황 모사 |
| GroupKFold by player | 동일 선수 multi-stint leakage 방지 |
| Position-specific validation | 타자/선발/불펜 성공 기준 분리 |
| League holdout | MLB/MiLB/NPB 출신별 일반화 확인 |

Evaluation:

- 실제 성공 선수를 ranking 상위 몇 %에 올렸는가?
- Top 5/Top 10 안에 실제 성공자가 있었는가?
- 실패 선수를 high-risk로 걸러냈는가?
- 특정 리그, 나이, 스킬 유형에 과적합됐는가?
- CV와 실제 KBO 결과가 다른 segment는 무엇인가?

## 5. Leakage Rules

사용 금지 feature:

- KBO 입단 후 첫 시즌 WAR, wRC+, ERA+, IP, PA
- 재계약 여부
- 시즌 중 교체 여부
- KBO 입단 후 부상 이탈 여부
- KBO 입단 후 인터뷰/평가

허용 feature:

- 입단 이전 MLB/MiLB/NPB/기타 리그 성적
- 입단 이전 부상/로스터/계약 상태
- 입단 당시 나이, 포지션, 투타
- 영입 전 scouting/public article metadata

## 6. Missing Data Strategy

데이터가 없으면 추측하지 않고 proxy를 둔다.

| missing_data | proxy |
|---|---|
| KBO pitch-level data | K%, BB%, K-BB%, FIP, pitch-type article tags |
| KBO ABS edge command | Statcast zone%, edge%, called strike%, BB% |
| NPB pitch movement | velocity reports, whiff/K%, pitch mix articles |
| NPB farm leverage | role tags, saves/holds, appearances, late-inning usage |
| contract details | 40-man status, roster block, recent DFA/FA, age, option context |
| Korean summer adaptation | June-Aug splits, southern US experience, injury/fatigue trend |
| SSG defensive coverage | team position defensive metrics if available, otherwise position WAR/UZR proxy |

## 7. First-Priority Hitter Feature Family

대체 외국인 외야수 후보는 다음 feature family를 먼저 만든다. 각 feature는 "평범한 좋은 선수"보다 "SSG라서 더 가치 있는 선수"를 찾기 위한 장치다.

| feature_family | question | candidate_signal |
|---|---|---|
| `outfield_power_gap_fit` | SSG 외야/중심타선 장타 결핍을 실제로 메우는가? | OF 출전 가능 + ISO/Barrel/maxEV/pull-air 지표 |
| `munhak_pull_air_fit` | 문학 구장 구조에서 뜬공 장타가 더 살아나는가? | Pull% x FB% x Barrel%, HR distance, launch angle |
| `kbo_pitch_ecology_fit` | KBO의 변화구/낮은 구속/유인구 환경에 맞는가? | breaking/offspeed xwOBA, whiff%, chase%, low-velo damage |
| `abs_zone_decision_fit` | ABS 환경에서 볼넷과 존 판단으로 무너질 가능성이 낮은가? | zone swing, chase, BB%, called strike profile |
| `acquirable_flaw_type` | 왜 MLB에서는 애매하지만 KBO에서는 살 수 있는가? | 40-man 밖, AAA 반복, 수비/삼진/나이/부상 결함 |
| `flaw_maskability` | 그 결함을 SSG가 실제로 가릴 수 있는가? | SSG OF/DH depth, platoon need, defensive tolerance |
| `summer_body_risk` | 한국 여름과 시즌 중 대체 합류에 버틸 수 있는가? | June-Aug split, recent PA trend, IL/absence history |

## 8. Error Analysis Checklist

모델 점수가 마음에 들지 않을 때 모델부터 바꾸지 않는다. 먼저 다음을 본다.

- 성공했는데 낮게 평가한 선수
- 실패했는데 높게 평가한 선수
- 타자/선발/불펜 중 약한 영역
- MLB/MiLB/NPB 출신별 오류
- 나이대별 오류
- 부상 이력 판단 오류
- K%, BB%, 타구 질, 구속, 리그 레벨의 과대평가 여부
- 특정 한두 사례에 맞춘 규칙인지 여부
