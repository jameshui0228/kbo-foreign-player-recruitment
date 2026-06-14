# Dacon-Style Modeling Strategy For SSG Foreign Player Recruitment

Generated: 2026-06-12 KST

## Core Position

이 프로젝트의 모델링 목표는 "좋은 선수 순위표"를 만드는 것이 아니다.

목표는 다음 질문에 대한 재현 가능한 데이터 마이닝 파이프라인을 만드는 것이다.

> SSG가 실제로 돈을 쓰고 데려올 수 있는 시장 안에서, SSG만의 숨은 보완점에 가장 잘 맞는 선수 유형은 무엇인가?

따라서 최종 결과는 단일 모델 점수가 아니라 네 단계 모델 스택이다.

1. SSG-only need discovery model
2. KBO translation and failure-risk model
3. market, contract, roster availability gate
4. slot-specific candidate ranking ensemble

교수님 발표에서 방어해야 하는 핵심은 "모델을 많이 돌렸다"가 아니라 "각 모델이 서로 다른 오류 가능성을 통제한다"이다.

## Prediction Unit

일반 공모전과 다르게 예측 단위가 하나가 아니다.

| layer | prediction unit | target or score | why it matters |
|---|---|---|---|
| message mining | SSG split/role/game-script segment | hidden-need score | SSG만의 문제를 찾는다. |
| archetype mining | player trait cluster | undervalued-archetype score | 표면 성적보다 싸게 살 수 있는 유형을 찾는다. |
| translation model | historical foreign-player season | KBO success / renewal / survival | MLB/AAA/NPB/CPBL 성과가 KBO에서 먹히는지 검증한다. |
| failure model | historical foreign-player season | failure or replacement risk | 좋아 보이지만 망할 유형을 제거한다. |
| availability model | current candidate-player-date | feasible acquisition probability | 너무 잘하거나 막힌 선수를 제거한다. |
| final ranking | candidate-slot pair | SSG expected surplus value | SSG에 맞는 최종 우선순위를 만든다. |

## Metric Design

최종 점수는 단순 평균이 아니다. 먼저 hard gate를 통과해야 한다.

```text
candidate_eligible =
    regulation_gate
  * economic_gate
  * availability_gate
  * medical_gate
  * role_gate
```

게이트를 통과한 선수만 다음 점수를 받는다.

```text
FinalScore(slot) =
    w1 * SSGFitScore
  + w2 * KBOTranslationScore
  + w3 * MarketInefficiencyScore
  + w4 * ToolProcessScore
  + w5 * SurplusValueScore
  - w6 * FailureRiskScore
```

권장 초기 가중치:

| slot | SSG fit | translation | market inefficiency | tool/process | surplus value | failure risk penalty |
|---|---:|---:|---:|---:|---:|---:|
| foreign hitter / OF | 0.30 | 0.25 | 0.15 | 0.20 | 0.10 | 0.20 |
| foreign pitcher | 0.25 | 0.25 | 0.10 | 0.25 | 0.15 | 0.25 |
| Asian quota | 0.25 | 0.20 | 0.15 | 0.15 | 0.25 | 0.20 |

가중치는 나중에 historical backtest와 ablation으로 조정한다.

## CV And Public LB Analogue

데이콘식으로 보면 이 프로젝트의 CV/Public LB/Private LB는 다음과 같다.

| Dacon term | project analogue | use |
|---|---|---|
| CV | historical backtest and OOF prediction | 과거 외국인 선수 사례에서 모델이 성공/실패를 구분하는지 본다. |
| Public LB | recent holdout season plus article/scout narrative agreement | 겉으로 보이는 최근 시장/기사 신호와 맞는지 본다. |
| Private LB | unseen future outcome and hidden constraints | 실제 계약 가능성, 건강, 적응, 팀 전략에서 살아남는지 본다. |

초기 split:

| split | train | validation | purpose |
|---|---|---|---|
| time holdout A | 2017-2023 | 2024 | 시간 외삽 검증 |
| time holdout B | 2017-2024 | 2025 | 최근 시장 검증 |
| group CV | player/team/origin grouped folds | held-out groups | 특정 선수/리그/팀 패턴 암기 방지 |
| current-season sensitivity | 2023-2025 features | 2026 partial excluded/included comparison | 2026 부분 표본 과신 방지 |

CV와 Public analogue가 어긋날 때의 판단 규칙:

- CV도 좋고 recent holdout도 좋으면 promote.
- CV는 좋은데 recent holdout이 나쁘면 distribution shift 또는 시장 변화 의심.
- recent holdout만 좋으면 suspect. 기사/로스터/표본 편향 가능성 점검.
- fold별 분산이 크면 선수 출신 리그, 연도, 팀 단위 group leakage 의심.

## Baseline Ladder

모델은 아래 순서로 쌓는다. 한 번에 복잡한 모델로 가지 않는다.

### 0. Rule And Metric Reproduction

먼저 코드로 재현해야 하는 것:

- KBO 외국인 선수/대체 외국인/아시아쿼터 규정 gate.
- salary and cost ceiling.
- active roster / 40-man / DFA / injured status gate.
- candidate scoring schema.

이 단계가 안 되면 어떤 ML 모델도 발표용으로 약하다.

### 1. Trivial Baseline

목적: "그냥 좋은 선수" 기준보다 우리 모델이 나은지 확인.

| slot | baseline |
|---|---|
| hitter | OPS, wOBA, xwOBA, HR, Barrel% 단순 순위 |
| pitcher | ERA proxy, xwOBA allowed, K-BB%, pitch count/start history 단순 순위 |
| Asian quota | salary/eligibility/role availability rule ranking |

### 2. Simple Baseline

목적: 설명 가능성과 재현성 확보.

- z-score weighted composite.
- Ridge / Logistic Regression.
- ElasticNet.
- kNN successful-comps model.
- calibrated probability model.

### 3. Strong Tabular Models

목적: 비선형 상호작용 포착.

- LightGBM.
- XGBoost.
- CatBoost.
- ExtraTrees / RandomForest.

사용 target:

- KBO success label.
- renewal label.
- replacement/failure label.
- role-fit label.
- surplus-value bucket.

### 4. Survival And Risk Models

목적: "잘하냐"보다 "버티냐"를 모델링.

- Cox proportional hazards.
- Random Survival Forest.
- discrete-time survival model.
- replacement hazard model.

출력:

- season-survival probability.
- replacement risk.
- renewal probability.

### 5. Unsupervised And Anomaly Models

목적: "아무도 생각하지 못한 SSG의 숨은 약점" 발견.

- PCA / robust PCA on team split matrix.
- NMF topic-like decomposition for game-script weakness.
- IsolationForest / LocalOutlierFactor for unusual SSG split.
- clustering for player archetypes.
- association rule mining for repeated failure combinations.

이 레이어는 답을 확정하지 않는다. 후보 메시지를 만든 뒤 supervised/holdout으로 검증한다.

### 6. Text Mining

목적: 인터뷰/기사/뉴스에서 현장 니즈와 리스크 신호를 보강.

- TF-IDF/BM25 keyword retrieval.
- NMF topic model.
- sentence embedding clustering if full text is secured.
- entity extraction for player/team/role/injury/contract.

주의:

- 기사 신호는 target이 아니라 corroboration이다.
- 기사만 높은 메시지는 suspect로 둔다.

### 7. Learning-To-Rank And Multi-Objective Ranking

목적: 최종 후보 순위를 만들 때 단일 확률이 아니라 여러 목적을 동시에 반영.

- LambdaMART if enough historical labels exist.
- TOPSIS / Pareto frontier.
- rank average ensemble.
- weighted blend by slot.

최종 후보는 "예측 확률 1등"이 아니라 Pareto에서 살아남는 선수를 우선한다.

## Feature Families

### SSG Fit Features

- role split rank gaps.
- base/out/score state gap.
- month and humidity context.
- opponent starter hand.
- starter-to-bullpen workload transfer.
- import-slot marginal contribution.
- domestic replacement runway.

### Hitter Features

- BB%, K%, chase rate, non-fastball chase.
- barrel%, hard-hit%, sweet-spot%.
- low-velocity damage.
- breaking/offspeed xwOBA.
- hitter-count swing and damage.
- air-contact and gap-contact proxy.
- outfield position eligibility.
- platoon split and RHP/LHP role fit.

### Pitcher Features

- start-proxy games.
- 80/90/100-pitch game history.
- first-pitch non-ball rate.
- three-ball exposure.
- zone rate and chase generation.
- xwOBA allowed, hard-hit allowed, barrel allowed.
- early-inning stability.
- RISP / runner-on-base damage.
- third-time-through-order damage.
- ABS-command proxy.

### Market And Contract Features

- active roster flag.
- 40-man flag.
- DFA/designated flag.
- injury list and surgery notes.
- age band.
- handedness.
- position scarcity.
- minor-league/NPB/CPBL/ABL contract status.
- transfer fee / salary estimate.
- KBO rule eligibility.

### Adaptation And Failure Features

- prior Asia experience.
- role stability before arrival.
- age and career direction.
- injury history.
- workload interruption.
- public adaptation/news signals.
- country/language/team environment proxies where ethically and reliably usable.

## Ensemble Design

앙상블은 마지막에만 하는 장식이 아니다. 서로 다른 오류를 가진 모델을 결합한다.

| ensemble input | captures |
|---|---|
| rule-gate score | 현실 계약 가능성 |
| SSG hidden-need score | 팀 특수성 |
| KBO translation model | 리그 적응 가능성 |
| failure-risk model | 망할 확률 |
| market inefficiency model | 가격 대비 기회 |
| text corroboration score | 현장/기사 신호 |

초기 ensemble:

1. model별 rank를 만든다.
2. OOF/holdout 성능이 있는 모델만 가중치를 높인다.
3. 상관이 높은 모델끼리는 하나만 대표로 둔다.
4. final score뿐 아니라 rank stability를 같이 본다.

## Error Analysis

OOF prediction이 생기면 반드시 다음 segment별 error를 본다.

- hitter vs pitcher.
- MLB vs MiLB vs NPB/CPBL/ABL origin.
- age band.
- left/right handedness.
- 40-man vs non-40-man.
- high stuff / low command.
- high power / high chase.
- starter-to-reliever role conversion.
- prior Asia experience.
- replacement signing vs offseason signing.

에러가 큰 segment에서 다음 feature experiment를 시작한다.

## Model Promotion Rules

| situation | decision |
|---|---|
| backtest improves, holdout improves, rank stable | promote |
| backtest improves, holdout worsens | inspect validation mismatch |
| only recent narrative agrees | suspect |
| feature improves one slot and hurts another | split by slot |
| model finds good player but gate fails | reject before baseball scoring |
| model is accurate but not explainable | keep as scout, not final presenter |

## Immediate Experiment Sequence

| order | run | purpose | output |
|---:|---|---|---|
| 1 | run_006_modeling_blueprint | lock model families and validation logic | this document + model registry |
| 2 | run_007_historical_label_table | build KBO foreign-player success/failure labels | supervised target table |
| 3 | run_008_metric_reproduction | encode gates and final scoring function | metric checker |
| 4 | run_009_baseline_ladder | trivial/simple/strong baselines | OOF predictions |
| 5 | run_010_error_segments | find failure/error segments | error analysis |
| 6 | run_011_candidate_rank_ensemble | blend model ranks and generate cards | shortlist |

## What We Can Claim Now

We can claim:

- The data is sufficient to begin model-driven mining.
- The model target is not generic player quality but SSG-specific surplus value.
- Hard gates are applied before baseball scores.
- 2026 data is important but will be protected by historical/time-split validation.
- Multiple model families are planned for different error modes.

We cannot yet claim:

- final candidates are proven.
- the KBO translation model is validated.
- Asian quota candidates are fully covered.
- article full text has been mined completely.
- salary/contract feasibility is fully verified.
