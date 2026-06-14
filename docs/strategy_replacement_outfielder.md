# Replacement Foreign Outfielder Strategy

업데이트: 2026-06-11 KST

## 1. Decision

1차 우선순위는 `대체 외국인 선수`이며, 포지션 우선순위는 `외야수 타자`로 둔다.

최종 프로젝트는 외국인 타자 1명, 외국인 선발투수 1명, 아시아쿼터 불펜투수 1명을 제안하지만, 분석의 첫 번째 승부처는 SSG에 특화된 대체 외국인 외야수 발굴이다.

## 2. Working Thesis, Not Final Message

평범한 결론은 피한다. 이 프로젝트의 타자 추천은 OPS, 홈런, wRC+ 상위권 선수를 줄 세우는 방식이 아니다. 다만 아래 문장은 최종 발표 메시지가 아니라, 데이터를 파고들기 위한 작업 가설이다.

작업 가설은 다음이다.

> MLB/MiLB에서는 결함 때문에 저평가되지만, KBO와 SSG 환경에서는 그 결함이 감당 가능하고 특정 장점이 더 크게 살아나는 외야수가 있다.

즉, 우리가 찾는 선수는 완벽한 선수가 아니라 `살 수 있는 결함`과 `SSG에서 증폭되는 장점`을 동시에 가진 선수다.

## 3. What Makes This Different

일반적인 스카우팅 문장:

- 장타력이 좋다.
- OPS가 높다.
- 외야 수비가 된다.
- 삼진이 적으면 좋다.

이 프로젝트의 데이터 질문:

- SSG 외야와 중심타선에서 실제로 부족한 생산성은 장타인가, 출루인가, 좌우 split인가, 특정 카운트 생산성인가?
- 문학 구장에서는 어떤 타구 방향/각도/속도 조합이 과대평가 또는 과소평가되는가?
- MLB에서 삼진이 많아 저평가된 선수가 KBO의 낮은 평균 구속과 투구 패턴에서는 장타를 유지할 수 있는가?
- 수비가 약한 외야수를 SSG가 DH/코너 외야/1루 로테이션으로 감당할 수 있는가?
- 시즌 중 대체 영입이라는 맥락에서 최근 30-60일 스킬이 살아 있는가?
- 기사/인터뷰에서 드러나는 SSG의 공개 니즈와 실제 데이터 결핍이 일치하는가?

## 4. Hidden Feature Candidates

| feature | intuition | possible inputs |
|---|---|---|
| `SSG Outfield Power Gap` | SSG 외야 포지션에서 리그 대비 부족한 장타를 정량화한다. | STATIZ team/player split, OF PA/OPS/ISO/wRC+ |
| `Munhak Pull-Air Bonus` | 문학에서 당겨친 뜬공 장타가 얼마나 가치 있는지 본다. | Savant pull%, FB%, Barrel%, LA, EV, HR distance |
| `KBO Low-Velo Damage` | MLB 빠른 공에는 약하지만 KBO 속도대에서는 강한 타자를 찾는다. | Savant pitch speed bucket xwOBA/SLG |
| `Breaking Ball Survivability` | KBO 변화구 환경에서 무너질 pure fastball hitter를 걸러낸다. | breaking/offspeed whiff%, chase%, xwOBA |
| `ABS Patience Fit` | ABS 환경에서 존 판단과 볼넷 생산이 유지될지 본다. | chase%, zone%, BB%, called strike profile |
| `3-0 Green Light Strength` | 자기 스윙에 확신이 있고 유리한 카운트에서 장타를 만드는지 본다. | count split, swing%, damage on hitter counts |
| `Acquirable Flaw Type` | 영입 가능한 이유가 되는 결함을 분류한다. | 40-man status, AAA repeat, K%, defense, injury, age |
| `Flaw Maskability` | 그 결함을 SSG 로스터가 가릴 수 있는지 본다. | SSG OF/DH depth, defensive proxy, platoon need |
| `Summer Body Risk` | 한국 여름과 시즌 중 합류에 버틸 수 있는지 본다. | June-Aug split, PA trend, IL/absence history |
| `Text-Need Agreement` | 프런트/감독/기사 니즈와 데이터 니즈가 같은 방향인지 본다. | Naver news metadata, official interviews, keyword tags |

## 5. Candidate Archetypes

### A. Pull-Air Power Outfielder

강점:

- 당겨친 뜬공과 배럴이 많다.
- maxEV와 hard-hit quality가 살아 있다.
- 문학의 좌우 펜스/낮은 담장과 궁합이 날 수 있다.

감당 가능한 결함:

- 삼진이 많다.
- 수비 범위가 넓지 않다.
- MLB fastball velocity에는 약하다.

검증 포인트:

- 낮은 구속대와 변화구 상대로도 장타를 만들었는가?
- 수비 결함을 SSG가 코너 외야/DH로 가릴 수 있는가?

### B. Breaking-Ball Translator

강점:

- 변화구/오프스피드에 헛스윙이 적다.
- KBO 투수들의 유인구 패턴에 덜 속는다.
- OPS는 평범해도 KBO 전환성이 높을 수 있다.

감당 가능한 결함:

- raw power가 최상급은 아니다.
- MLB에서 압도적 장타자는 아니다.

검증 포인트:

- SSG가 필요한 것이 홈런만인지, 변화구 대응이 되는 중심타선 안정성인지 먼저 확인한다.

### C. Damaged-Value Rebound Outfielder

강점:

- 최근 이름값은 낮지만 타구속도, 배럴, 선구안의 핵심 신호가 아직 살아 있다.
- 부상 또는 로스터 사정으로 시장가가 낮아졌을 가능성이 있다.

감당 가능한 결함:

- 최근 출장 수가 적다.
- 부상 이력이 있다.
- 나이가 아주 어리지는 않다.

검증 포인트:

- 단순 부진인지, 스킬 자체가 죽었는지 분리한다.
- 최근 30-60일 rolling trend로 반등 신호를 확인한다.

## 6. Analysis Order

1. STATIZ로 SSG 외야/중심타선/장타 결핍을 계량화한다.
2. Naver/공식 기사로 SSG가 공개적으로 말한 니즈를 태깅한다.
3. Savant에서 MLB/MiLB 외야수 후보의 타구질, 구종 대응, 카운트별 공격성을 만든다.
4. `Acquirable Flaw`와 `Flaw Maskability`로 "살 수 있는 선수"만 남긴다.
5. 과거 KBO 외국인 타자 성공/실패 사례와 유사도 backtest를 한다.
6. 최종 후보는 점수뿐 아니라 "왜 이 결함이 SSG에서는 감당 가능한가"를 한 문장으로 설명한다.

## 7. Message Discovery Rule

발표의 핵심 문장은 사람이 먼저 고르지 않는다. 인터뷰/기사 텍스트와 SSG 정량 데이터가 반복해서 같은 방향을 가리킬 때만 메시지로 승격한다.

메시지 후보가 되려면 아래 세 조건을 모두 만족해야 한다.

- 정량 데이터에서 리그 대비 SSG의 결핍 또는 비효율이 보여야 한다.
- 기사/인터뷰에서 같은 니즈가 반복적으로 언급되어야 한다.
- Savant 후보군에서 그 결핍을 메울 수 있는 비전형적 feature가 발견되어야 한다.

최종 후보마다 아래 세 문장이 데이터로 채워져야 한다.

- 데이터가 발견한 SSG의 숨은 메시지는 무엇인가?
- 이 선수의 시장가를 낮추는 결함은 무엇인가?
- 그 결함이 SSG에서는 왜 감당 가능하거나 오히려 활용 가능한가?
