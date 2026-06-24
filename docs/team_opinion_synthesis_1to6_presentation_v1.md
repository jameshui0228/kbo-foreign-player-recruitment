# 네 명 의견 통합 정리: 1-6번 데이터 마이닝 발표 구조

작성일: 2026-06-23  
기준 브랜치: `origin/sewon` 최신 커밋, `origin/jimini`, `origin/kyuho`, `main/Codex 통합모델`  
목적: 팀원별 후보 추천을 하나의 발표 흐름으로 통합한다.

---

## 0. 발표 전체 메시지

이번 프로젝트의 핵심은 "누가 제일 좋은 선수인가"가 아니라, SSG가 지금 어떤 문제를 해결해야 하고, 그 문제를 해결할 수 있는 외국인 선수 유형이 무엇인지 데이터로 좁혀가는 것이다.

네 명의 모델은 후보명은 다르지만 공통적으로 같은 시장을 보고 있다.

- 타자: MLB에서 완전히 자리 잡지 못했지만 KBO에서는 장점이 살아날 수 있는 좌타/스위치 또는 코너 OF/1B/3B 자원
- 투수: 40인 로스터 바깥 또는 접근 가능한 AAA/MLB fringe 선발·스윙맨
- 공통 gate: 계약 접근성, 40인/마이너 상태, 부상, 한국행 의사, KBO 번역 가능성

따라서 발표 결론은 단일 정답 후보가 아니라 다음 구조가 되어야 한다.

1. SSG의 숨은 약점을 정의한다.
2. KBO 외국인 성공/실패 유형으로 필요한 선수 유형을 번역한다.
3. 후보 시장을 구성한다.
4. KBO 번역 모델로 후보를 다시 평가한다.
5. 실패 리스크와 계약 현실성으로 걸러낸다.
6. 최종 SSG fit board를 제시한다.

---

## 1. SSG 숨은 약점 마이닝

### 팀원별 강조점

| 의견 | 핵심 약점 정의 | 발표에서의 의미 |
|---|---|---|
| Codex 통합모델 | RISP 자체보다 1루 주자 상황 전환 실패, 외인 선발 슬롯 안정성 부족 | "득점권 해결사"보다 "득점권 이전 단계 전환자"가 필요 |
| sewon | 1루 주자 상황 OPS 10위, 초반 OPS 8위, 2사 OPS 8위 | SSG fit을 runner advancement, ABS discipline, early pressure로 점수화 |
| jimini | KBO 변화구·저속 구종 대응, 좌타/스위치, 투수 BB9/third-time wOBA | 단순 타격 성적보다 KBO 환경에서 살아남을 skill을 강조 |
| kyuho | AAA 장점과 MLB 실패의 차이, quality of contact, 선발 지속성 | MLB에서는 부족했지만 KBO에서 장점이 살아날 후보를 찾음 |

### 통합 결론

SSG의 문제는 단순히 "외야 장타 부족"이 아니다.  
타자는 1루 주자 상황을 살리는 traffic converter가 필요하고, 투수는 5-6이닝을 버티는 traffic-command starter가 필요하다.

발표 문장:

> SSG의 보강 포인트는 장타 총량이 아니라, 공격 흐름이 끊기는 특정 game-state를 복구하는 것이다.

---

## 2. KBO 외인 성공/실패 유형 마이닝

### 팀원별 모델 관점

| 의견 | 성공/실패를 보는 방식 | 강점 | 주의점 |
|---|---|---|---|
| Codex 통합모델 | 과거 KBO 외인 성공/실패 classifier, 타자 모델은 promoted, 투수는 diagnostic | 모델의 해석 경계가 명확함 | 투수는 확정 추천보다 진단 리드로 표현해야 함 |
| sewon | 42명 타자/86명 선발 KBO 첫해 라벨 기반 backtest | 발표용 수치가 명확함 | 점수화 가중치가 임의로 보일 수 있어 설명 필요 |
| jimini | 변화구/저속 xwOBA, 좌타/스위치, BB9, third-time wOBA를 추가 필터로 사용 | KBO 환경 적응 논리가 선명함 | 일부 지표는 표본/결측 확인 필요 |
| kyuho | AAA-MLB translation gap, hard-hit/barrel, BB/K, GB/BB9/HR9 | 시장 비효율 관점이 좋음 | KBO 성공 label과 직접 연결되는 설명 보강 필요 |

### 통합 결론

타자는 "MLB에서 밀린 파워"만 보면 위험하다. KBO에서 실패하지 않을 컨택/선구/구종 대응 floor가 필요하다.  
투수는 구속이나 K/9보다 BB9, HR9, 이닝 지속성, 같은 타자 반복 상대 안정성이 더 중요하다.

발표 문장:

> KBO 외인 성공은 가장 화려한 tool이 아니라, KBO에서 사라지지 않는 장점과 치명적 결함의 부재로 결정된다.

---

## 3. 후보 시장 구축

### 팀원별 후보 시장

| 의견 | 후보 시장 범위 | 대표 후보 |
|---|---|---|
| Codex 통합모델 | 구조화 데이터 기반 736명 타자/1,009명 투수, 계약·의료·시장 gate 포함 | Luis Matos, Dominic Fletcher, Josh Fleming |
| sewon | DFA/FA/Outrighted 중심, 타자 28명/선발 21명 최종 A/B/C 후보군 | Weston Wilson, Jack Suwinski, Carson Spiers, Brian Van Belle |
| jimini | 모델 lane 후보 22명/23명에서 KBO 적응 필터 추가 | Trey Mancini, Nolan Jones, Josh Fleming, Jhonathan Diaz |
| kyuho | 외인타자 1명 + 외인선발 1명 two-slot 시장 | Jack Suwinski, Michael Toglia, Matthew Lugo, Josh Fleming |

### 공통 시장 정의

네 의견 모두 실제로는 같은 시장을 보고 있다.

- MLB 확고한 주전급은 제외
- 40인 밖, DFA, outrighted, minor contract, AAA 주전급 위주
- 나이는 대체로 타자 25-31세, 투수 28-33세
- 장점은 명확하지만 MLB에서는 결함이 노출된 선수

발표 문장:

> 우리는 스타를 사는 시장이 아니라, MLB에서는 결함 때문에 밀렸지만 KBO에서는 장점이 더 크게 번역될 수 있는 경계선 시장을 공략한다.

---

## 4. KBO 번역 모델

### 팀원별 번역 기준

| 의견 | 타자 번역 기준 | 투수 번역 기준 |
|---|---|---|
| Codex 통합모델 | SSG runner-on-first 전환, KBO translation, market realism | 선발 runway, MiLB IP/GS, BB9/HR9 |
| sewon | AAA->KBO 리그팩터, PCL 파크팩터, ABS 보너스, KBO wRC+ 추정 | AAA->KBO ERA 번역, ABS BB9 보정, early inning support |
| jimini | break/off-speed xwOBA, low-velo xwOBA, 좌타/스위치 가산 | BB9 <= 3.5, third-time wOBA |
| kyuho | AAA OPS와 MLB OPS의 translation gap, quality of contact | GB%, BB9, HR9, starter continuity |

### 통합 결론

KBO 번역은 단순히 AAA OPS나 ERA를 가져오는 것이 아니다.  
각 후보의 장점이 KBO 환경에서 유지되는지, 약점이 KBO에서 가려지는지, 그리고 SSG의 특정 약점과 맞는지를 함께 본다.

발표 문장:

> KBO 번역 모델은 성적을 예측하는 모델이 아니라, MLB에서 보였던 장점과 약점이 KBO에서 어떻게 재배치되는지 보는 모델이다.

---

## 5. 실패 리스크 모델

### 공통 실패 gate

| Gate | 의미 | 후보 판단에 미치는 영향 |
|---|---|---|
| 40인/계약 상태 | 실제로 데려올 수 있는가 | 40man 선수는 비용·협상 리스크 상승 |
| DFA/Outrighted/Minor | 접근 가능성 | 즉시 접촉 가능성 상승 |
| Medical | 부상/가동성 | 선발투수 후보에서 가장 큰 hard gate |
| Salary/Buyout/Opt-out | 현실적 비용 | 점수가 높아도 최종 후보에서 제외 가능 |
| Korea-willingness | 한국행 의사 | 최종 영입 전 필수 수동 확인 |
| Role fit | 타자는 OF/1B/DH, 투수는 starter/multi-inning | 역할이 어긋나면 후보 등급 하향 |

### 팀원별 리스크 인식

| 의견 | 리스크 처리 방식 |
|---|---|
| Codex 통합모델 | market realism, contract control, medical risk, sensitivity band를 별도 gate로 분리 |
| sewon | acquisition tier 20% 반영, warning flag 표기 |
| jimini | 부상 자동 제외, BB9/구종 대응 hard filter |
| kyuho | target/watch/reject 라벨로 결함과 시장성을 분리 |

### 통합 결론

후보 선정은 점수 상위 선수를 고르는 과정이 아니라, 탈락시킬 이유를 끝까지 확인하는 과정이다.

발표 문장:

> 최종 후보는 모델 점수가 높은 선수가 아니라, 모델 점수와 현실 gate를 동시에 통과한 선수다.

---

## 6. SSG Fit Ranking

### 타자 후보 의견 통합

| 후보군 | 포함 선수 | 근거 | 발표상 표현 |
|---|---|---|---|
| 공통/핵심 검증군 | Nolan Jones, Dominic Fletcher | 여러 모델에서 반복 등장, 좌타/OF, SSG fit | 가장 설득력 있는 SSG fit 후보군 |
| 파워 upside군 | Jack Suwinski, Michael Toglia, Matthew Lugo, James Outman, Christopher Morel | 장타, hard-hit, barrel, AAA 생산성 | 고위험 고보상 후보군 |
| 안정/전환군 | Abraham Toro, Dominic Fletcher, Luis Matos, Will Brennan | 낮은 K%, 전환력, 좌타/스위치 | 1루 주자 상황 보완 후보군 |
| 즉시 접근 후보군 | Trey Mancini, Luis Rengifo, Weston Wilson | DFA/접근성, 특정 모델 상위 | 계약 가능성 확인용 우선 접촉군 |

### 투수 후보 의견 통합

| 후보군 | 포함 선수 | 근거 | 발표상 표현 |
|---|---|---|---|
| 공통 1순위 검증군 | Josh Fleming | jimini, kyuho, Codex 통합모델에서 반복 등장 | 가장 강한 합의 후보 |
| 선발 안정성군 | Brian Van Belle, Carson Spiers, Randy Dobnak, Jake Woodford | IP/GS, 선발 지속성 | medical/BB9/HR9 gate 필요 |
| 좌완/커맨드군 | Josh Fleming, Kolby Allard, Jhonathan Diaz, Bruce Zimmermann | 좌완, BB9/HR9, 이닝 | SSG 선발 다양성 보완 |
| 구위/특수역할군 | Ian Hamilton, Noah Murdock, Yariel Rodriguez, Matt Bowman | K9, whiff, 단기 upside | 선발 슬롯과 맞는지 검증 필요 |

### 최종 발표용 후보 board

이 단계에서 하나의 최종 정답을 박기보다, 후보를 세 등급으로 제시하는 것이 안전하다.

#### 타자

| 등급 | 후보 | 이유 |
|---|---|---|
| 1차 consensus board | Nolan Jones, Dominic Fletcher | SSG fit과 KBO 번역 안정성의 교집합 |
| upside board | Jack Suwinski, Michael Toglia, Weston Wilson | 장타/출루/ABS 장점, 다만 삼진·포지션·모델 차이 검증 필요 |
| market/contact board | Trey Mancini, Luis Rengifo, Abraham Toro | 즉시 접근성 또는 변화구/저속 대응 장점 |

#### 투수

| 등급 | 후보 | 이유 |
|---|---|---|
| 1차 consensus board | Josh Fleming | 커맨드, 좌완, 선발/스윙맨, 여러 모델 반복 등장 |
| starter depth board | Carson Spiers, Brian Van Belle, Randy Dobnak | 선발 지속성/이닝 장점, medical 또는 BB9 확인 필요 |
| diagnostic board | Kolby Allard, Jhonathan Diaz, Ian Hamilton, Bruce Zimmermann | 좌완/구위/third-time/스윙맨 장점은 있으나 최종 gate 필요 |

---

## 발표 구성안

### Slide 1. 문제 정의

SSG는 외국인 타자와 선발투수를 보강해야 한다. 하지만 목표는 단순히 OPS/ERA가 좋은 선수를 찾는 것이 아니라, SSG의 특정 약점을 해결하는 선수 유형을 찾는 것이다.

### Slide 2. 네 명의 분석은 왜 다르게 나왔나

각 모델은 같은 시장을 보지만 강조점이 다르다.

- sewon: SSG fit + KBO 성과 번역 + 영입 등급
- jimini: KBO 변화구/저속 적응 + BB9/third-time 필터
- kyuho: AAA 장점과 MLB 실패 사이의 시장 비효율
- Codex: 6-layer structured model + hard gate 분리

### Slide 3. 1번 SSG 숨은 약점

타자는 1루 주자 상황 전환 실패, 투수는 외인 선발 슬롯 안정성 부족이 핵심이다.

### Slide 4. 2번 KBO 성공/실패 유형

KBO 외인은 화려한 tool보다 결함이 덜 치명적이고, 장점이 KBO에서 유지되는 유형이 성공한다.

### Slide 5. 3번 후보 시장

우리는 40인 바깥, DFA, outrighted, minor contract, AAA 주전급 시장을 본다.

### Slide 6. 4번 KBO 번역

AAA OPS/ERA를 그대로 믿지 않고, 파크팩터, ABS, 구종 대응, BB9/HR9, starter continuity로 번역한다.

### Slide 7. 5번 실패 리스크

계약, 부상, 40인, buyout, 한국행 의사, 역할 적합성을 hard gate로 둔다.

### Slide 8. 6번 최종 board

최종 단일 후보가 아니라 consensus board, upside board, diagnostic board로 제시한다.

### Slide 9. 최종 메시지

네 명의 의견은 충돌하는 것이 아니라 서로 다른 위험을 보는 보완적 모델이다.  
우리의 최종 전략은 "한 모델의 1위"가 아니라, 여러 모델이 반복해서 가리키는 후보와 각 후보의 실패 조건을 함께 제시하는 것이다.

---

## 회의에서 바로 말할 수 있는 결론

현재 팀원 의견을 통합하면, 타자는 Nolan Jones/Dominic Fletcher가 SSG fit 안정형으로 가장 설명력이 좋고, Jack Suwinski/Michael Toglia/Weston Wilson은 장타 upside 후보로 분리하는 것이 좋다. 투수는 Josh Fleming이 가장 강한 공통 후보이고, Carson Spiers/Brian Van Belle/Randy Dobnak은 선발 지속성 후보군, Kolby Allard/Jhonathan Diaz/Ian Hamilton은 진단 후보군으로 두는 것이 안전하다.

따라서 발표에서는 "우리가 한 명을 찍었다"가 아니라 "SSG 약점에서 출발해 여러 모델의 합의와 반박 조건을 거쳐 후보 board를 만들었다"라고 말해야 한다.
