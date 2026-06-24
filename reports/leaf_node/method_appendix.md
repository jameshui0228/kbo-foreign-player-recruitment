# Method Appendix

## 데이터마이닝 절차

본 프로젝트는 Business Understanding, Data Understanding, Data Preparation, Modeling, Evaluation, Ensemble Decision, Deployment 순서로 구성했다. 최종 의사결정은 raw ranking과 gate-adjusted ranking을 분리한다.

## Candidate Funnel

| 단계 | 타자 잔존 | 투수 잔존 | 판정 의미 |
| --- | --- | --- | --- |
| Step 1. 전체 구조화 시장 | 736 | 1,009 | MLB/MiLB/roster 기반으로 모델 입력 가능한 후보 pool 구성 |
| Step 2. 후보 생성 모듈 | 16 | 18 | Market Screen, Team Fit Screen, Upside Screen에서 후보 board로 이동 |
| Step 3. 기본 데이터마이닝 gate | 6 | 3 | 비40인/시장 접근성/표본/부상 flag를 1차 통과 |
| Step 4. Raw Top 3 | 3 | 3 | 순수 모델 점수와 모듈 반복 등장 신호 기준 |
| Step 5. Gate-adjusted Top 3 | 3 | 3 | 계약·의료·실행 가능성을 반영한 최종 접촉 board |

## Feature Engineering

### Hitter Feature Groups

| Feature Group | 주요 변수 | 해석 |
| --- | --- | --- |
| Contact Floor | K%, whiff%, zone contact, two-strike proxy | 이닝을 끊지 않는 최소 컨택 안정성 |
| On-base / Damage | OBP, wOBA/xwOBA, SLG/ISO, HardHit%, Barrel% | 출루와 장타가 함께 존재하는지 |
| RHP Game-Script Fit | vs RHP OBP/SLG/xwOBA, chase/whiff penalty | 우투 선발 경기에서 공격 흐름을 복구할 수 있는지 |
| Run-kill Avoidance | GB%, GDP proxy, chase%, weak contact% | 병살·삼진·약한 타구로 이닝을 끝낼 위험 |
| Role / Market Fit | OF/DH role, 40-man, DFA/outright/minor deal, salary signal | SSG가 실제로 쓸 수 있고 데려올 수 있는지 |

### Pitcher Feature Groups

| Feature Group | 주요 변수 | 해석 |
| --- | --- | --- |
| Command Stability | BB%, BB9, K-BB%, zone%, first-pitch proxy | 볼넷으로 이닝을 키우지 않는 안정성 |
| Damage Control | HR9, hard-hit allowed, GB%, LOB proxy | traffic 이후 장타/대량실점 억제 |
| Starter Floor | GS, IP/GS, pitch count proxy, recent workload | 5이닝 이상 버틸 수 있는 최소 근거 |
| KBO / ABS Translation | zone command, chase dependency, pitch mix stability | ABS 환경에서 볼넷 리스크가 커지지 않는지 |
| Market / Medical Fit | contract, salary, injury list, velocity trend | 점수와 별개로 실제 영입 가능한지 |

## 모델 구성

| 모델명 | 목적 | 입력 | 출력 | 사용 강도 |
| --- | --- | --- | --- | --- |
| Model A. Team Need Mining Model | SSG 약점을 game-state interaction으로 정의 | SSG 상황별 팀 성과, 상대 선발 유형, 주자 상황, 득실 | weakness rule, feature contract | 공통 기준 |
| Model B. Historical KBO Success/Failure Model | 입단 전 정보로 성공/실패 확률 추정 | pre-KBO Savant/MiLB feature | success/failure probability | 타자 강함, 투수 진단 |
| Model C. Similarity / Archetype Matching Model | KBO 성공 유형 또는 SSG 필요 유형과 유사도 계산 | 표준화 feature vector | archetype score, role similarity | 보조 |
| Model D. KBO Translation Risk Model | MLB/MiLB 성과가 KBO에서 유지되지 않을 위험 평가 | K%, chase, whiff, BB9, HR9, starter continuity | PASS/YELLOW/HOLD/RED | 강함 |
| Model E. Market Feasibility Model | 실제 영입 가능성 평가 | 40-man, DFA/outright, minor contract, salary signal | available/conditional/blocked | hard gate |
| Model F. Medical / Failure Gate | 점수 상위지만 실행 불가능한 후보 보류 | IL, surgery, workload, role mismatch | PASS/YELLOW/HOLD/RED | hard gate |

## 모델 성능과 사용 강도

| 모델명 | 대상 | 표본 수 | feature family | 주요 성능 | 해석 | 사용 강도 |
| --- | --- | --- | --- | --- | --- | --- |
| hitter_success_classifier | 타자 | 22 | savant_only | AUC 0.833 success / 0.738 failure | 주요 신호로 사용 | High |
| hitter_failure_classifier | 타자 | 22 | savant_only | AUC 0.833 success / 0.738 failure | 주요 신호로 사용 | High |
| pitcher_success_diagnostic | 투수 | 49 | milb_damage_command | AUC 0.603 diagnostic | 확정 신호가 아니라 보조 진단으로 사용 | Low/Diagnostic |
| pitcher_failure_warning_only | 투수 | 49 | milb_damage_command | AUC 0.603 diagnostic | 확정 신호가 아니라 보조 진단으로 사용 | Low/Diagnostic |

## Weight 근거

| 슬롯 | 모듈 | 가중치 | 근거 |
| --- | --- | --- | --- |
| 타자 | historical_success_failure_classifier | 0.40 | 타자 AUC가 성공 0.833, 실패 0.738로 promoted gate를 통과했기 때문에 가장 큰 base learner로 사용 |
| 타자 | ssg_fit_translation_pipeline | 0.25 | SSG 2026 상황별 약점, KBO 번역, 영입 등급을 동시에 반영하는 구조적 base learner |
| 타자 | kbo_adaptation_filter | 0.15 | 변화구/저속 구종 대응과 좌타/스위치 적합성을 통해 KBO 적응 실패를 줄이는 filter |
| 타자 | market_inefficiency_feature_model | 0.15 | AAA 장점과 MLB 결함의 translation gap, quality contact를 통해 시장 비효율을 탐색 |
| 타자 | cross_model_consensus | 0.05 | 서로 다른 가정의 base learner에서 반복 등장한 후보에 작은 안정성 보너스 |
| 투수 | historical_success_failure_classifier | 0.05 | 투수 AUC 0.603으로 watch 등급이므로 확정 추천이 아닌 약한 diagnostic signal로만 사용 |
| 투수 | ssg_fit_translation_pipeline | 0.25 | 선발 이닝, KBO ERA 번역, 영입 등급을 반영하는 구조적 base learner |
| 투수 | kbo_adaptation_filter | 0.25 | BB/9, HR/9, third-time wOBA로 KBO 선발 지속성과 ABS 적응 위험을 줄이는 filter |
| 투수 | market_inefficiency_feature_model | 0.20 | 선발 지속성, GB, HR 억제, command feature로 MLB fringe 선발 시장을 탐색 |
| 투수 | cross_model_consensus | 0.25 | 투수 supervised model이 약하기 때문에 여러 독립 분석에서 반복 등장하는지를 더 크게 반영 |

## Gate 기준

| Gate | 정의 | 처리 |
| --- | --- | --- |
| PASS | 시장·의료·역할 리스크가 관리 가능한 상태 | final board 유지 |
| YELLOW | 추가 확인 필요하지만 접촉 가능 | conditional ranking |
| HOLD | 현재 정보로는 active contact 부적합 | watch 또는 medical hold |
| RED | 계약·의료·역할 리스크가 hard block | 최종 board 제외 |

## Leakage 방지

과거 KBO 외국인 선수의 KBO 입단 후 성적은 label 또는 사후 검증에만 사용한다. 후보 평가 feature에는 KBO 입단 후 성과를 넣지 않는다. 모델은 입단 전 정보로 성공 가능성을 추정한다.

## 한계

| 한계 | 영향 | 보완 |
| --- | --- | --- |
| 투수 KBO 외국인 표본 수 | 학습 표본이 49명 수준이라 연도·리그·역할 변화에 민감함 | AUC만 보지 않고 후보 진단 신호로 제한 |
| 투수 성과 label noise | ERA/IP 같은 결과가 수비, 불펜 승계주자, 포수, 구장, 경기 운영 영향을 크게 받음 | BB9, HR9, starter floor 같은 직접 통제 가능 지표를 함께 사용 |
| 투수 역할 이질성 | 선발, 스윙맨, 불펜 전환 선수가 한 표본 안에 섞여 성공 기준이 흔들림 | 최종 판단에서 starter floor와 role fit gate를 별도 적용 |
| 투수 pitch-quality 결측 | 구속 추세, pitch shape, release, zone command 같은 핵심 변수가 일부 후보에서 빠짐 | public stat 모델은 낮은 weight로 두고 medical/구속/구종 확인을 협상 전 체크리스트로 둠 |
| salary/contract 공개 정보 | 잔여 부담액과 buyout은 비공개일 수 있음 | 접촉 전 agent/구단 확인 |
| medical public signal | full medical report 부재 | medical hold를 hard gate로 운용 |
| 2026 시즌 중 데이터 | SSG weakness rule이 갱신될 수 있음 | 주 단위 재빌드 |
| NPB/CPBL 보조 데이터 | 최종 타자·선발투수 후보에는 직접성이 낮음 | 아시아쿼터 별도 모델로 분리 |
