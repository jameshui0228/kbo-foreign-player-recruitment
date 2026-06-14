# Literature Log

업데이트: 2026-06-11 KST

이 문서는 후보 추천의 결론을 대신하지 않는다. 논문은 feature engineering과 검증 설계의 근거로만 사용한다.

## Foreign Player Market / Replacement Context

| paper | why relevant | project use |
|---|---|---|
| Kim & Yoon, "Market Inefficiencies in the KBO League Players' Labor Market: The Effects of Strict Regulations on Foreign Players" (2022), DOI: `10.5762/kais.2022.23.10.546` | KBO 외국인 선수 제도와 연봉/성과 시장 비효율을 다룬다. | `Acquirable Flaw`와 외국인 슬롯의 시장 제약 설명 근거. |
| Kawaura & La Croix, "The very short tenure of foreign players in Japanese professional baseball, 1951-2004" (2016), DOI: `10.4337/9781784719951.00009` | 일본 프로야구에서 외국인 선수가 짧은 기간 핵심 포지션을 메우는 quick fix로 활용됐다는 분석. | 대체 외국인 영입을 장기 육성이 아니라 즉시 결핍 해결 문제로 모델링. |
| Park & Kim, "A predictive model for a contract renewal of foreign pitchers in KBO using machine learning" (2022), DOI: `10.7465/jkdi.2022.33.6.963` | 외국인 선수 성공을 재계약 여부로 예측하는 KBO ML 접근. | historical transfer backtest에서 재계약/잔류를 label 후보로 검토. |

## Run Creation / Batting Order / Replacement Value

| paper | why relevant | project use |
|---|---|---|
| Kim & Kim, "한국 프로야구에서 가중수정OPS를 이용한 득점력 설명" (2014) | KBO 득점력 설명에서 출루율과 장타율의 가중 조합을 제안. | SSG가 홈런/ISO는 강하지만 득점 생산성이 중위권인 현상을 검증할 때 출루/장타 조합을 분리. |
| Shin, Lee & Kim, "Improving Team's Scoring Ability in KBO League using Each Batting Order's Statistics and Regression Model of Machine Learning" (2023), DOI: `10.24826/kscs.12.11.17` | KBO 팀 득점력이 타순별 OPS와 연결될 수 있음을 다룬다. | 외국인 외야수 후보를 단순 개인 OPS가 아니라 SSG 타순 병목에 배치하는 문제로 확장. |
| Baumer, Jensen & Matthews, "openWAR: An Open Source System for Evaluating Overall Player Performance in Major League Baseball" (2015), DOI: `10.1515/JQAS-2014-0098` | replacement player 개념과 공개 데이터 기반 WAR 산식을 논의. | 대체 외인 후보를 replacement baseline 대비 marginal value로 설명. |

## Park / Batted Ball Physics

| paper | why relevant | project use |
|---|---|---|
| Konaka, "Park factor estimation improvement using pairwise comparison method" (2021), arXiv: `2109.09287` | 구장 효과를 타자/투수/구장 매치업으로 분리해 추정. | `Munhak Park Fit`을 단순 구장 크기가 아니라 타구/매치업 조건과 함께 설계. |
| Levine, "Personnel-adjustment for home run park effects in Major League Baseball" (2025), arXiv: `2506.22350` | 홈런 구장 효과가 선수 구성과 좌우 매치업에 따라 달라질 수 있음을 다룬다. | 문학 홈런 친화도를 후보 handedness와 pull-air profile에 연결. |
| Kagan, "What Is the Best Launch Angle To Hit a Home Run" (2010), DOI: `10.1119/1.3361995` | 홈런은 발사각뿐 아니라 타구속도, 공기저항, 스핀, 날씨, 구장 크기의 영향을 받는다고 설명. | `launch angle`, `exit velocity`, `humidity/weather`, `park dimension`을 함께 보게 하는 근거. |

## Plate Discipline / Swing Decision

| paper | why relevant | project use |
|---|---|---|
| Yee & Deshpande, "Evaluating plate discipline in Major League Baseball with Bayesian Additive Regression Trees" (2023), DOI: `10.1515/jqas-2023-0048` | 스윙/기다림 결정을 존 안팎만이 아니라 count, out, 주자, 점수 맥락과 함께 평가. | `ABS Patience Fit`과 `3-0 Green Light Strength`를 단순 chase%가 아니라 상황별 의사결정으로 확장. |
| Vock & Vock, "Estimating the effect of plate discipline using a causal inference framework" (2018), DOI: `10.1515/JQAS-2016-0029` | plate discipline이 타격 성과에 미치는 효과를 타격 능력/상대한 투구와 분리하려는 접근. | 선구안 지표를 후보 raw hitting skill과 분리해서 평가. |
| Lee et al., "A measure of the importance of moment for ball-strike counts in a baseball plate appearance" (2024), DOI: `10.1080/02640414.2024.2355423` | 볼카운트 상황의 중요도를 Markov Chain으로 계량화. | 유리한 카운트와 중요한 카운트에서의 swing/damage feature 설계. |

## Search Gaps

추가로 찾아야 할 문헌:

- KBO 외국인 타자 성공/실패를 직접 다룬 논문
- KBO ABS 도입 이후 타자/투수 의사결정 변화 연구
- KBO 또는 NPB 구장 효과/타구질 관련 실증 연구
- 마이너리그 타구질 지표가 상위 리그 성과로 번역되는 정도에 관한 논문

원문 접근이 막히는 논문이 실제 feature에 중요해지면 고려대 도서관 접근을 요청한다.
