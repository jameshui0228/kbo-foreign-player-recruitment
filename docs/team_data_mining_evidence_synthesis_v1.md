# 팀원별 데이터 마이닝 근거 통합 정리 v1

작성일: 2026-06-23  
기준 브랜치: `main/Codex`, `origin/sewon`, `origin/jimini`, `origin/kyuho`  
목적: 네 명의 후보 추천을 "누가 맞다/틀리다"가 아니라, 어떤 데이터와 어떤 모델 근거에서 나온 결과인지 발표용으로 정리한다.

---

## 0. 최종 한 줄 결론

이번 프로젝트의 최종 메시지는 다음처럼 잡는 것이 가장 타당하다.

> 타자는 과거 KBO 외국인 성공/실패 데이터를 학습한 모델이 후보판을 실제로 바꿨고, Luis Matos, Nolan Jones, Dylan Carlson이 가장 강한 데이터 마이닝 후보로 올라왔다. 반면 투수는 현재 숫자 데이터만으로 확정 추천할 만큼 모델 성능이 강하지 않으므로, Josh Fleming, Bryse Wilson, Austin Gomber, Carson Spiers, Brian Van Belle을 추가 검증 board로 두는 것이 과학적으로 안전하다.

중요한 점은 타자와 투수를 같은 강도로 말하면 안 된다는 것이다.  
타자는 검증 수치가 있는 promoted model이고, 투수는 watch/diagnostic model이다.

---

## 1. 모델 신뢰도 계층

네 명의 결과는 모두 같은 수준의 모델이 아니다. 발표에서는 아래처럼 증거 계층을 나누면 훨씬 설득력이 있다.

| 계층 | 의미 | 해당 분석 | 발표에서의 사용 방식 |
|---|---|---|---|
| A | 과거 KBO 성공/실패 label을 직접 학습한 supervised model | Codex 타자 모델 | 최종 타자 후보를 밀어 올리는 핵심 근거 |
| B | KBO label/backtest와 SSG fit을 결합한 structured pipeline | sewon | 발표의 1-6번 전체 흐름과 SSG fit 설명 |
| C | 모델 shortlist에 KBO 환경 적응 filter를 얹은 rule-based mining | jimini | 후보 제거 사유와 KBO 적응성 설명 |
| D | 시장 비효율 feature engineering ranking | kyuho | upside 후보와 현장 스카우팅식 feature schema 설명 |
| E | 여러 분석에서 반복 등장한 consensus signal | 팀원 통합 | 최종 board에서 우선 검증할 선수 선별 |

따라서 최종 발표 문장은 "네 명이 각자 다른 후보를 뽑았다"가 아니라 다음이어야 한다.

> 네 모델은 서로 다른 위험을 본다. Codex는 과거 성공/실패 학습, sewon은 SSG 약점-번역-영입 현실성, jimini는 KBO 구종/ABS 적응성, kyuho는 시장 비효율과 tool translation을 본다.

---

## 2. Codex 모델: 순수 데이터 마이닝 결론

### 사용 데이터

기사, 인터뷰, 텍스트 변수는 모델 input에서 제외했다.  
숫자형 structured data만 사용했다.

타자:

- 과거 KBO 외국인 타자 중 pre-KBO Savant 지표가 있는 22명
- 주요 feature: `BB%`, `K%`, `wOBA`, `chase rate`, `zone swing rate`, `non-fastball chase`, `whiff`, `hard-hit`, `barrel`, `sweet spot`, `air BBE`, `low-velo xwOBA`, `high-velo xwOBA`, `breaking/off-speed xwOBA`, `hitter-count xwOBA`

투수:

- 과거 KBO 외국인 투수 중 pre-KBO MiLB 기록이 있는 49명
- 주요 feature: `IP`, `G`, `GS`, `K/9`, `BB/9`, `HR/9`, `ERA`, `WHIP`

### 사용 모델

| 슬롯 | 모델 | 목표 | 검증 결과 | 해석 |
|---|---|---|---:|---|
| 외인타자 | Ridge Logistic Regression | KBO 성공 확률 | AUC 0.833 | promoted |
| 외인타자 | Ridge Logistic Regression | KBO 실패 확률 | AUC 0.738 | promoted |
| 외인투수 | Sparse L1 Logistic Regression | KBO 성공 확률 | AUC 0.603 | watch |
| 외인투수 | Sparse L1 Logistic Regression | KBO 실패 경고 | not promoted | warning only |

### 모델 결론

#### 외인타자 Top 3

| 순위 | 선수 | 조직 | 40인 | 성공확률 | 실패확률 | 결론 |
|---:|---|---|---|---:|---:|---|
| 1 | Luis Matos | MIL | False | 92.4% | 8.2% | 모델 최우선 |
| 2 | Nolan Jones | CLE | False | 90.2% | 9.2% | 모델+팀원 교집합 |
| 3 | Dylan Carlson | PHI | False | 82.4% | 15.1% | 모델 후보 유지 |

핵심 해석:

- 이 모델은 기존 수동 SSG-fit 점수에서 높았던 일부 후보를 내렸다.
- 특히 표본이 작거나 성공/실패 패턴 신뢰도가 약한 후보는 낮아졌다.
- 그래서 타자 쪽은 "데이터 마이닝 모델이 후보판을 실제로 바꿨다"고 말할 수 있다.

#### 외인투수 Diagnostic Board

| 순위 | 선수 | 조직 | 40인 | 성공확률 | 실패위험 | 결론 |
|---:|---|---|---|---:|---:|---|
| 1 | Bryse Wilson | PHI | False | 50.5% | 46.9% | 진단 리드 |
| 2 | Austin Gomber | ATL | False | 52.6% | 49.2% | 진단 리드 |
| 3 | Dietrich Enns | BAL | False | 39.5% | 56.7% | 추천 아님 |

핵심 해석:

- 투수 모델 AUC 0.603은 "확정 추천"으로 쓰기에는 약하다.
- 따라서 투수는 모델 결론을 과장하면 안 된다.
- 오히려 "현재 숫자 데이터만으로는 투수 확정 추천이 어렵다"는 사실이 중요한 발견이다.

발표 문장:

> 타자 모델은 과거 KBO 성공/실패 패턴을 어느 정도 분리했지만, 투수 모델은 아직 진단용이다. 따라서 타자는 추천 후보를 제시하고, 투수는 추가 검증 후보판으로 제시한다.

---

## 3. sewon 모델: SSG 약점에서 출발한 6단계 파이프라인

### 사용 데이터

- STATIZ 2026 SSG 상황별 타격 데이터
- 2017-2025 KBO 외국인 선수 성공/실패 패턴
- DFA, FA, outrighted 후보 시장
- AAA/MLB/Savant 지표
- PCL 파크팩터, AAA to KBO 리그팩터
- KBO 첫해 라벨: 타자 42명, 선발 86명

### 분석 구조

| 단계 | 내용 |
|---|---|
| 1 | STATIZ 2026 상황별 타격으로 SSG 약점 도출 |
| 2 | KBO 외국인 성공/실패 archetype 추출 |
| 3 | DFA/FA/Outrighted 558명 스크리닝 |
| 4 | PCL 파크팩터 + AAA to KBO 번역 |
| 5 | KBO 첫해 실적 라벨로 backtest |
| 6 | SSG Fit 40% + KBO 성과 40% + 영입 등급 20% |

### SSG 약점 정의

| 약점 | 리그 순위 | 의미 |
|---|---:|---|
| 1루 주자 상황 OPS | 10위 | 득점권 이전 단계에서 공격 흐름이 끊김 |
| 1-3이닝 OPS | 8위 | 초반 주도권을 못 잡음 |
| 2사 OPS | 8위 | 이닝을 이어가는 능력이 약함 |
| 문학 홈/원정 OPS 차이 | 홈 +0.035 | 문학 환경에 맞는 갭 파워/선구안 필요 |

### 후보 결론

타자:

- Weston Wilson
- Christopher Morel
- Jack Suwinski
- Michael Toglia
- Nolan Jones

선발:

- Carson Spiers
- Brian Van Belle
- Victor Mederos
- Cooper Criswell
- Brandon Leibrandt

### 발표에서의 역할

sewon 모델은 "최종 정답 모델"이라기보다 발표의 구조를 잡아주는 backbone으로 쓰는 것이 좋다.

강점:

- SSG 약점에서 후보 시장까지 이어지는 흐름이 가장 명확하다.
- 1번부터 6번까지 발표 구조를 설명하기 좋다.
- 후보마다 SSG Fit, KBO 예상 성과, 영입 등급을 분리해서 말할 수 있다.

주의점:

- 종합 점수 산식이 `0.40/0.40/0.20`이라서 교수님이 "왜 이 가중치인가?"라고 물을 수 있다.
- 따라서 "학습 모델의 최종 결론"이라고 말하기보다는 "structured scoring pipeline"이라고 말해야 한다.

---

## 4. jimini 모델: KBO 적응성 filter

### 사용 데이터

- 전체 후보군: 타자 736명, 투수 1,009명
- 모델 lane_2 + stable_top25 shortlist
- Savant 구종별 xwOBA
- 투수 MiLB `K/9`, `BB/9`, `HR/9`
- `third-time wOBA`
- roster/contract status
- medical risk flag

### 분석 구조

1차:

- lane_2 + stable_top25 후보만 남김
- 타자 22명, 투수 23명으로 압축

2차:

- 타자: `breaking/off-speed xwOBA >= 0.20`, `low-velo xwOBA >= 0.20`
- 타자: 좌타/스위치 우선
- 투수: `BB/9 <= 3.5`
- 투수: `third-time wOBA` 낮은 선수 우선
- 부상 flag는 자동 제외

### 후보 결론

타자:

- Trey Mancini
- Dominic Fletcher
- Nolan Jones
- Abraham Toro
- Luis Rengifo

투수:

- Josh Fleming
- Ian Hamilton
- Noah Murdock
- Jhonathan Diaz
- Matt Bowman

### 발표에서의 역할

jimini 모델은 "왜 어떤 후보를 탈락시키는가"를 설명할 때 가장 좋다.

강점:

- KBO 변화구/저속 구종 대응이라는 구체적 변수를 쓴다.
- 투수는 BB/9와 third-time wOBA로 KBO 선발 지속성을 본다.
- C.J. Stubbs처럼 데이터 연결 오류가 있는 후보를 제외한 점이 중요하다.

주의점:

- 일부 기준은 학습된 모델이 아니라 규칙 기반 filter다.
- `third-time wOBA`가 없는 투수는 결측 처리 방식에 따라 순위가 달라질 수 있다.

발표 문장:

> jimini 모델은 모델 점수가 높은 후보라도 KBO 변화구, 저속 구종, ABS 환경에서 무너질 위험이 있으면 제거하는 risk filter 역할을 한다.

---

## 5. kyuho 모델: 시장 비효율 feature model

### 사용 데이터

- KBO/STATIZ 팀 및 선수 기록
- MLB/MiLB official stats
- Statcast/Savant batted-ball data
- roster/transaction data

### 분석 구조

외국인 타자 1명, 외국인 선발투수 1명만 대상으로 한 two-slot model이다.

타자 feature:

- AAA OPS
- MLB recent/career OPS
- AAA-MLB translation gap
- max EV, EV90
- hard-hit%, barrel%, sweet-spot%
- ISO
- K%, BB%

투수 feature:

- AAA IP, GS, IP/GS
- K/9, BB/9, HR/9
- K/BB
- GB%
- MLB career BB/9, HR/9
- starter continuity

### 후보 결론

타자:

- Jack Suwinski
- Michael Toglia
- Matthew Lugo
- Rece Hinds
- Josh Lowe

투수:

- Josh Fleming
- Randy Dobnak
- Spencer Bivens
- Hunter Barco
- Bruce Zimmermann

### 발표에서의 역할

kyuho 모델은 시장 비효율을 설명할 때 좋다.

강점:

- "MLB에서는 결함 때문에 밀렸지만, KBO에서는 장점이 살아날 수 있는 선수"라는 관점이 명확하다.
- Jack Suwinski, Michael Toglia처럼 장타 upside 후보를 잘 포착한다.
- Josh Fleming을 투수 쪽 핵심 후보로 반복해서 잡아낸다.

주의점:

- KBO 성공/실패 label을 직접 학습한 모델은 아니다.
- 따라서 최종 추천의 핵심 근거라기보다 upside board와 scouting schema로 쓰는 것이 좋다.

발표 문장:

> kyuho 모델은 성적 상위 선수를 찾는 것이 아니라, MLB에서 저평가된 장점이 KBO에서 더 크게 번역될 수 있는 시장 비효율을 찾는 모델이다.

---

## 6. 네 명 결과의 교집합

팀원별 후보가 달라도 반복 등장하는 선수는 중요하다.  
반복 등장은 학습 모델의 성능 지표는 아니지만, 서로 다른 가정에서 살아남았다는 consensus signal이다.

| 선수 | 슬롯 | 등장 횟수 | 등장 분석 | 해석 |
|---|---|---:|---|---|
| Nolan Jones | 타자 | 3 | Codex, sewon, jimini | 모델+SSG fit+KBO 적응성 교집합 |
| Josh Fleming | 투수 | 3 | Codex 통합모델, jimini, kyuho | 가장 강한 투수 consensus 후보 |
| Dominic Fletcher | 타자 | 2 | Codex 통합모델, jimini | 안정형 좌타/전환형 후보 |
| Jack Suwinski | 타자 | 2 | sewon, kyuho | 좌타 장타 upside 후보 |
| Michael Toglia | 타자 | 2 | sewon, kyuho | 스위치 장타 upside 후보 |
| Bruce Zimmermann | 투수 | 2 | Codex 통합모델, kyuho | 좌완 depth/커맨드 진단 후보 |

교집합 해석:

- Nolan Jones는 "모델 추천 + 팀원 합의"를 동시에 가진 가장 설명력 좋은 타자 후보다.
- Luis Matos는 팀원 교집합은 약하지만, pure supervised data-mining 모델에서 가장 강하게 올라온 후보다.
- Josh Fleming은 투수 쪽에서 가장 강한 팀원 합의 후보지만, pure supervised pitcher model이 약하기 때문에 최종 추천보다 "1차 검증 후보"로 표현하는 것이 안전하다.

---

## 7. 최종 후보 board

### 외국인 타자

최종 타자 board는 두 층으로 제시하는 것이 좋다.

#### A. 데이터 마이닝 핵심 후보

| 순위 | 선수 | 핵심 근거 | 발표 표현 |
|---:|---|---|---|
| 1 | Luis Matos | 성공확률 92.4%, 실패확률 8.2%, 24세, 40인 외 | 모델이 가장 강하게 밀어 올린 후보 |
| 2 | Nolan Jones | 성공확률 90.2%, 실패확률 9.2%, 팀원 3개 분석 반복 등장 | 모델+합의 교집합 후보 |
| 3 | Dylan Carlson | 성공확률 82.4%, 실패확률 15.1%, 40인 외 | 모델상 유지 후보 |

#### B. 보조 검증 후보

| 후보 | 이유 | 주의점 |
|---|---|---|
| Dominic Fletcher | 좌타, KBO 적응 filter, SSG fit 안정형 | supervised model Top 3는 아님 |
| Jack Suwinski | 좌타 장타, ABS/chase 관점, sewon/kyuho 반복 | 삼진/whiff risk 확인 필요 |
| Michael Toglia | 스위치 장타, quality contact | PCL inflation, chase/K risk 확인 필요 |
| Trey Mancini | 즉시 접근 가능, 구종 대응 우수 | 나이/수비/지속성 확인 필요 |

최종 타자 발표 문장:

> 최종 타자 결론은 Nolan Jones를 consensus 후보로 두되, 순수 데이터 마이닝 모델은 Luis Matos를 1순위로 제시한다. Dylan Carlson은 모델상 3순위지만 팀원 합의가 약하므로 추가 검증 후보로 둔다.

---

### 외국인 투수

투수는 "최종 추천 Top 3"라고 말하면 위험하다.  
현재 모델 성능상 "추가 검증 board"라고 말해야 한다.

#### A. 모델 diagnostic 후보

| 선수 | 근거 | 해석 |
|---|---|---|
| Bryse Wilson | pitcher diagnostic model 1위, 성공확률 50.5% | 모델상 진단 리드 |
| Austin Gomber | 성공확률 52.6%, 실패위험 49.2% | 모델상 진단 리드 |
| Dietrich Enns | 실패위험 56.7%, margin 음수 | 추천 아님, hold |

#### B. 팀원 consensus/translation 후보

| 선수 | 등장 분석 | 근거 | 해석 |
|---|---|---|---|
| Josh Fleming | jimini, kyuho, Codex 통합모델 | BB/9, 좌완, 선발/스윙맨, 40인 외 | 가장 강한 투수 검증 후보 |
| Carson Spiers | sewon | 선발 안정성, KBO ERA translation | 선발 depth 후보 |
| Brian Van Belle | sewon | 이닝, 커맨드, contact management | medical/시장 확인 필요 |
| Bruce Zimmermann | Codex 통합, kyuho | 좌완 depth, 커맨드 | 진단 후보 |

최종 투수 발표 문장:

> 투수는 아직 데이터 마이닝 모델이 확정 추천을 할 만큼 강하지 않다. 따라서 Josh Fleming을 consensus 검증 1순위로 두고, Bryse Wilson과 Austin Gomber는 pure model diagnostic lead, Carson Spiers와 Brian Van Belle은 번역/이닝형 대안으로 둔다.

---

## 8. 1번부터 6번까지 최종 정리

### 1. SSG 숨은 약점 마이닝

SSG의 핵심 약점은 단순 장타 부족이 아니라 game-state conversion 실패다.

- 1루 주자 상황 OPS 10위
- 초반 1-3이닝 OPS 8위
- 2사 OPS 8위

따라서 필요한 타자는 "홈런만 치는 선수"가 아니라 주자 있는 상황에서 볼넷, 갭파워, 낮은 chase로 공격 흐름을 살리는 선수다.  
필요한 투수는 "구속만 빠른 투수"가 아니라 BB/9, HR/9, 이닝 지속성으로 초반 실점과 불펜 소모를 줄이는 선발이다.

### 2. KBO 외인 성공/실패 유형 마이닝

타자는 과거 KBO 성공/실패 classifier가 유의미하게 작동했다.

- 성공 모델 AUC 0.833
- 실패 모델 AUC 0.738

투수는 낮은 성능이었다.

- 성공 모델 AUC 0.603
- watch/diagnostic only

따라서 타자는 모델 기반 결론, 투수는 보수적 후보판으로 가야 한다.

### 3. 후보 시장 구축

공통 시장은 다음이다.

- 40인 로스터 밖
- DFA
- outrighted
- minor contract
- AAA/MLB fringe
- MLB에서는 결함이 드러났지만 KBO에서는 장점이 살아날 수 있는 선수

### 4. KBO 번역 모델

AAA 성적을 그대로 쓰지 않는다.

- 타자: Savant quality contact, chase, 구종별 xwOBA, low-velo 대응, breaking/off-speed 대응
- 투수: BB/9, HR/9, WHIP, IP/GS, starter continuity, third-time wOBA
- sewon 쪽에서는 PCL 파크팩터와 AAA to KBO 번역식도 반영했다.

### 5. 실패 리스크 모델

최종 후보는 점수가 높은 선수가 아니라 탈락 사유를 버틴 선수다.

- 40인 여부
- 계약 상태
- 부상/medical risk
- 연봉/바이아웃/옵트아웃
- 선발 역할 가능성
- KBO 구종/ABS 적응성

### 6. SSG Fit Ranking

최종 board는 아래처럼 발표하는 것이 안전하다.

| 슬롯 | 1차 결론 | 2차 검증 |
|---|---|---|
| 외인타자 | Luis Matos, Nolan Jones, Dylan Carlson | Dominic Fletcher, Jack Suwinski, Michael Toglia |
| 외인투수 | 확정 추천 보류 | Josh Fleming, Bryse Wilson, Austin Gomber, Carson Spiers, Brian Van Belle |

---

## 9. 팀원들에게 보낼 수 있는 최종 요약문

이번에 네 명의 후보 추천을 다시 정리해보면, 후보명이 서로 다른 것은 분석이 흔들렸다는 뜻이 아니라 각 모델이 서로 다른 위험을 봤기 때문이라고 정리할 수 있습니다.

Codex 모델은 과거 KBO 외국인 성공/실패 데이터를 직접 학습한 supervised data-mining 모델입니다. 기사나 인터뷰 같은 텍스트 변수는 제외하고 숫자형 structured data만 사용했습니다. 타자는 pre-KBO Savant 지표가 있는 22명을 Ridge Logistic Regression으로 학습했고, 성공 모델 AUC 0.833, 실패 모델 AUC 0.738이 나왔습니다. 이 기준에서는 Luis Matos, Nolan Jones, Dylan Carlson이 최종 Top 3입니다. 특히 타자는 모델 성능이 어느 정도 확보됐기 때문에 "데이터 마이닝 모델이 후보판을 바꿨다"고 말할 수 있습니다.

반면 투수는 pre-KBO MiLB 기록 49명으로 Sparse L1 Logistic Regression을 돌렸지만 성공 모델 AUC가 0.603에 그쳤습니다. 따라서 Bryse Wilson, Austin Gomber가 모델상 diagnostic lead로 나오더라도, 투수는 확정 추천이 아니라 추가 검증 board로 보는 것이 맞습니다. 이건 실패가 아니라 중요한 결론입니다. 숫자 데이터만으로 투수를 확정 추천하면 오히려 과학적으로 과장입니다.

sewon 분석은 SSG 약점에서 출발한 6단계 파이프라인입니다. STATIZ 2026 상황별 타격에서 1루 주자 OPS 10위, 초반 OPS 8위, 2사 OPS 8위라는 약점을 잡고, KBO 외국인 성공/실패 패턴, 후보 시장, KBO 번역, backtest, 최종 점수화를 연결했습니다. 발표의 1번부터 6번 흐름을 설명하는 backbone으로 쓰기 좋습니다.

jimini 분석은 KBO 적응성 filter가 강합니다. 단순 성적이 아니라 breaking/off-speed xwOBA, low-velo xwOBA, 투수 BB/9, third-time wOBA를 통해 KBO 변화구/저속 구종과 ABS 환경에서 살아남을 수 있는지를 봤습니다. 그래서 후보 제거 사유를 설명할 때 가장 유용합니다.

kyuho 분석은 시장 비효율을 잘 잡습니다. MLB에서는 결함 때문에 밀렸지만 KBO에서는 장점이 살아날 수 있는 AAA-MLB translation gap, hard-hit, barrel, BB/K, GB%, BB/9, HR/9 같은 feature를 봤습니다. Jack Suwinski, Michael Toglia 같은 upside 후보를 설명하는 데 좋습니다.

최종적으로 타자는 Luis Matos, Nolan Jones, Dylan Carlson을 데이터 마이닝 핵심 후보로 두고, Dominic Fletcher, Jack Suwinski, Michael Toglia를 보조 검증 후보로 두는 것이 좋습니다. 특히 Nolan Jones는 Codex, sewon, jimini에서 반복 등장하므로 모델+팀원 합의 교집합 후보로 가장 설명력이 좋습니다.

투수는 Josh Fleming이 팀원 분석에서 가장 많이 반복 등장한 consensus 검증 후보입니다. 다만 순수 데이터 마이닝 투수 모델은 아직 약하기 때문에 Josh Fleming을 확정 추천이라고 말하기보다는, Bryse Wilson, Austin Gomber, Carson Spiers, Brian Van Belle과 함께 추가 검증 board로 제시하는 것이 맞습니다.

최종 발표 메시지는 이겁니다.

> 우리는 한 명의 선수를 찍은 것이 아니라, SSG의 숨은 약점에서 출발해 과거 KBO 외국인 성공/실패 데이터, KBO 번역 모델, 시장 현실성, 실패 리스크를 단계적으로 통과한 후보 board를 만들었다. 타자는 모델 확신도가 있으므로 Luis Matos, Nolan Jones, Dylan Carlson까지 추천 가능하고, 투수는 현재 숫자 데이터만으로 확정 추천하기 어렵기 때문에 Josh Fleming 중심의 추가 검증 board로 제시한다.

