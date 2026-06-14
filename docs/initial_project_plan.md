# Initial Project Plan

접근일: 2026-06-11 KST

## 1. 프로젝트 목표 재정의

이 프로젝트는 2023년 이후 KBO, MLB/MiLB, NPB, 기사/인터뷰, 구장/날씨 데이터를 결합해 SSG 랜더스의 전력 니즈를 먼저 진단한 뒤, 그 니즈에 맞는 외국인/아시아쿼터 후보를 랭킹하는 시스템을 구축한다.

현재 운영 우선순위는 다음과 같다.

1. 대체 외국인 선수
2. 대체 외국인 중 외야수 타자
3. 외국인 선발투수
4. 아시아쿼터 불펜투수

최종 산출물은 특정 선수의 이름만 나열하는 추천표가 아니다. 다음 질문에 답하는 데이터 기반 영입 제안서다.

- SSG는 타자, 선발, 불펜 중 어디의 marginal value가 가장 큰가?
- KBO에서 성공한 외국인 선수는 입단 전 어떤 패턴을 가졌는가?
- 후보의 결함은 KBO와 SSG 환경에서 감당 가능한가?
- SSG 홈구장, ABS, 투타 스타일, 로스터 구조가 후보의 장단점과 맞는가?
- 영입 가능성까지 고려했을 때 최종 1순위/2순위/3순위는 누구인가?
- 남들이 단점으로 보는 요소 중 SSG에서는 감당 가능하거나 오히려 가치가 커지는 특색은 무엇인가?

첫 단계에서는 선수 추천을 하지 않는다. 먼저 데이터 소스, 스키마, success label, feature hypothesis, validation 설계를 고정한다.

## 2. 데이터 소스 요약

| domain | data_source | access | years/leagues | main_columns | strengths | limits | collection_plan | project_use |
|---|---|---|---|---|---|---|---|---|
| KBO | STATIZ | https://www.statiz.co.kr/ | KBO current/historical | WAR, wRC+, OPS, ERA, FIP, K%, BB%, team/player splits | KBO 분석에 가장 유용한 고급지표 | 공식 API 없음, 자동 수집 약관 확인 필요 | 우선 수동 다운로드/소량 확인, source log 필수 | SSG 전력 진단, 외국인 성공 label 보강 |
| KBO | KBO official | https://eng.koreabaseball.com/ | KBO official records | team/player basic stats, roster, standings | 공식성 높음 | 고급지표 제한 | 공식 페이지/기록 확인 중심 | 최신 로스터, 공식 성적 검증 |
| KBO | MyKBO Stats | https://mykbostats.com/ | KBO 2014-2026 등 | standings, team splits, foreign player stats | 영어 기반, daily update, team split 확인 용이 | 비공식, 고급지표 제한 | 표 단위 수집 가능성 검토 | 리그 환경, 팀 split 보조 |
| KBO | FanGraphs International KBO | https://www.fangraphs.com/leaders/international/kbo | KBO international leaders | wRC+, WAR, K%, BB%, team stats | 일관된 리더보드 포맷 | 업데이트/컬럼 범위 확인 필요 | export 가능 범위 확인 | KBO 고급지표 cross-check |
| MLB/MiLB | Baseball Savant Statcast | https://baseballsavant.mlb.com/statcast_search | MLB and some MiLB Statcast | EV, maxEV, barrel%, xwOBA, pitch velocity, movement, whiff%, chase%, zone% | 후보 스킬의 핵심 원천 | MiLB coverage/기간 제한, 쿼리량 관리 필요 | CSV export/API-like query 사용 | 타구 질, 구위, ABS 적응 feature |
| MLB/MiLB | FanGraphs MLB/MiLB | https://www.fangraphs.com/leaders/minor-league | MLB/MiLB | wRC+, WAR, K%, BB%, ISO, FIP, xFIP | 후보군 필터링에 강함 | 일부 다운로드/멤버십 제한 가능 | leaderboards export 확인 | 후보 pool 및 baseline skill |
| MLB/MiLB | Baseball-Reference Register | https://www.baseball-reference.com/register/ | MLB/MiLB/foreign register | player history, age, level, teams | 이력과 레벨 추적에 좋음 | scraping 제한, 고급지표 제한 | 수동/허용 범위 내 저장 | 선수 이력, 나이, 포지션, 레벨 |
| MLB/MiLB | MLB/MiLB official roster | https://www.mlb.com/ and https://www.milb.com/ | current roster | 40-man, IL, roster status, transactions | availability 판단에 필수 | 계약 세부 조건 제한 | 공식 roster/transactions 확인 | 영입 가능성, 40-man outside 여부 |
| NPB | NPB official | https://npb.jp/eng/ | NPB 1군/팜 | official batting/pitching, roster | 공식성 높음 | 고급지표 제한 | 공식 stats/players 확인 | 아시아쿼터 후보 검증 |
| NPB | FanGraphs International NPB | https://www.fangraphs.com/leaders/international/npb | NPB | WAR, wRC+, FIP style metrics | 미국/KBO 지표와 비교 용이 | 업데이트/coverage 확인 필요 | export 가능 범위 확인 | NPB 후보 baseline skill |
| NPB | ProEyeKyuu | https://proeyekyuu.com/ | NPB historical/current | downloadable player/team stats | 영어/일본어, 다운로드 지원 명시 | 세부 약관 확인 필요 | 다운로드 기능 우선 사용 | NPB/팜 후보 pool |
| NPB | Yakyu Cosmopolitan | https://www.yakyucosmo.com/ | NPB and Farm | batting/pitching, farm stats, K%, BB%, wRC+ style columns | 팜 기록 접근성 좋음 | 비공식, 컬럼 정의 확인 필요 | 표 단위 저장 후 정의 검증 | 아시아쿼터 불펜 후보 발굴 |
| NPB | 1point02 | https://1point02.jp/ | NPB/Farm | advanced NPB/farm metrics | NPB 고급지표 가능성 | 회원/유료 범위 존재 | 무료 범위 확인, 유료 자료 무단 사용 금지 | 접근 가능 시 고급지표 보강 |
| articles | Naver News Search API | https://developers.naver.com/docs/serviceapi/search/news/news.md | Korean news | title, originallink, pubDate, description | API와 호출 한도 명확 | API key 필요, 본문 전문 제한 | API key가 있으면 메타/링크 수집 | SSG 니즈 텍스트 분석 |
| articles | BIGKinds | https://www.bigkinds.or.kr/ | Korean news archive | media, date, keywords, entities | 공신력 있는 국내 뉴스 DB | 계정/API/이용조건 확인 필요 | 허용 범위 내 검색/다운로드 | 인터뷰/기사 corpus |
| articles | SSG/KBO official news | https://www.ssglanders.com/ and https://eng.koreabaseball.com/ | official team/league news | title, date, body, category | 공식 발언 확인 | 사이트 구조 변동 | 공식 보도자료 수집 | 프런트/감독 발언 근거 |
| weather/park | KMA | https://www.weather.go.kr/neng/index.do | Korea weather | temp, humidity, wind, precipitation | 공식 기상 원천 | API 신청/포맷 확인 필요 | 인천 경기일 weather table 생성 | climate adaptation, park context |
| weather/park | Open-Meteo KMA API | https://open-meteo.com/en/docs/kma-api | Korea forecast/weather proxy | hourly temp, humidity, wind, precip | 공개 API 접근성 | 관측 원자료가 아닌 모델/보간 가능 | KMA 대체/보조 | 날씨 feature proxy |
| weather/park | Incheon SSG Landers Field public dimensions | https://en.wikipedia.org/wiki/Incheon_SSG_Landers_Field | park dimensions | LF/LCF/CF/RCF/RF, wall height | 빠른 기초 정보 | 2차 출처, 공식 확인 필요 | 공식/구장 자료로 교차검증 | park fit feature |

## 3. SSG 전력 분석 최소 데이터셋 스키마

최소 스키마는 “팀 약점 진단 -> 후보가 그 약점을 메우는가”를 연결하기 위해 설계한다.

### 3.1 Team batting season

`kbo_team_batting_season`

| column | type | meaning | why_for_ssg |
|---|---|---|---|
| season | int | 연도 | 2023-현재 비교 축 |
| team | str | 팀명 | SSG vs league |
| games | int | 경기 수 | 표본 크기 |
| runs | int | 득점 | 공격 결과 |
| wrc_plus | float | 리그 조정 득점 생산 | 표면 OPS보다 상대 비교에 적합 |
| ops | float | OPS | 공개 데이터 접근성이 높음 |
| obp | float | 출루율 | 중심/하위 타선 연결성 |
| slg | float | 장타율 | 외국인 타자 니즈 |
| iso | float | 순장타율 | 장타 결핍 진단 |
| hr | int | 홈런 | 문학/외인 타자 fit |
| bb_pct | float | 볼넷률 | ABS 시대 존 판단 |
| k_pct | float | 삼진률 | KBO 적응 리스크 |
| risp_ops | float | 득점권 OPS | 클러치보다 타선 병목 탐지 |
| vs_lhp_ops | float | 좌투 상대 OPS | 플래툰 약점 |
| vs_rhp_ops | float | 우투 상대 OPS | 후보 handedness fit |
| rank_* | int | 각 지표 리그 순위 | 발표용 직관성 |
| source | str | 출처 | 재현성 |

### 3.2 Team pitching by role

`kbo_team_pitching_role_season`

| column | type | meaning | why_for_ssg |
|---|---|---|---|
| season | int | 연도 | 2023-현재 추세 |
| team | str | 팀명 | SSG vs league |
| role | str | starter/bullpen | 선발과 불펜 분리 |
| ip | float | 이닝 | workload |
| era | float | 평균자책점 | 결과 지표 |
| fip | float | 수비/운 보정 proxy | 투수 본질 성능 |
| whip | float | 출루 허용 | 실점 위험 |
| k_pct | float | 삼진률 | 구위/헛스윙 |
| bb_pct | float | 볼넷률 | KBO 전환 핵심 리스크 |
| k_bb_pct | float | K%-BB% | 가장 간단한 투수 skill proxy |
| hr9 | float | 피홈런 억제 | 문학 park fit |
| qs_pct | float | QS 비율 | 선발 안정성 |
| avg_ip_per_start | float | 선발 평균 이닝 | 이닝 소화 니즈 |
| gmli | float | 평균 등판 leverage | 불펜 역할 강도 |
| wpa | float | 승리확률 기여 | 고레버리지 결과 |
| back_to_back_ip | float | 연투 workload | 불펜 과부하 |
| source | str | 출처 | 재현성 |

### 3.3 Position and lineup production

`kbo_team_position_lineup_season`

| column | type | meaning | why_for_ssg |
|---|---|---|---|
| season | int | 연도 | 추세 |
| team | str | 팀명 | SSG |
| split_type | str | position/lineup_slot/handedness | 결핍 위치 |
| split_value | str | OF/1B/DH/3-5/7-9/LHP/RHP 등 | 후보 역할 매칭 |
| pa | int | 표본 | 안정성 |
| wrc_plus | float | 생산성 | 포지션별 니즈 |
| ops | float | 접근성 높은 대체 지표 | 데이터 결측 대체 |
| iso | float | 장타 결핍 | 외국인 타자 fit |
| defense_proxy | float | 수비 보정 proxy | 수비 약한 외인 허용 여부 |
| source | str | 출처 | 재현성 |

### 3.4 Park and weather by game

`kbo_game_park_weather`

| column | type | meaning | why_for_ssg |
|---|---|---|---|
| game_id | str | 경기 ID | join key |
| date | date | 경기일 | weather join |
| stadium | str | 구장 | 문학 home split |
| home_team | str | 홈팀 | SSG home |
| temp_c | float | 기온 | summer adaptation |
| humidity_pct | float | 습도 | fatigue/ball carry |
| wind_speed_ms | float | 풍속 | HR/FB context |
| wind_direction | str | 방향 | park factor |
| precipitation_mm | float | 강수 | 경기 환경 |
| source | str | 출처 | 재현성 |

### 3.5 Article/interview corpus

`ssg_article_mentions`

| column | type | meaning | why_for_ssg |
|---|---|---|---|
| article_id | str | 기사 ID/hash | 중복 제거 |
| published_at | datetime | 발행일 | 최신성 |
| media | str | 매체 | 신뢰도/편향 |
| url | str | 링크 | 검증 |
| title | str | 제목 | 검색 |
| speaker | str | 감독/단장/선수/기자 추정 | 니즈 출처 |
| category | str | hitting/starter/bullpen/operation/injury | 니즈 태깅 |
| keywords | str | 추출 키워드 | TF-IDF/BM25 |
| summary_proxy | str | 키워드 기반 요약 | LLM 없이 요약 |
| source | str | 수집원 | 재현성 |

## 4. Success Metric 초안

Historical transfer backtest에서 KBO 입단 후 성적은 label로만 사용한다. 후보 랭킹 feature에는 입단 후 KBO 성적을 절대 넣지 않는다.

### 4.1 Foreign hitter labels

| label | draft_rule | interpretation |
|---|---|---|
| `hitter_success` | first_kbo_war >= 2.0 and pa >= 350 and wrc_plus >= 110 | 주전급으로 시즌을 버틴 성공 |
| `hitter_strong_success` | first_kbo_war >= 3.0 and pa >= 450 and wrc_plus >= 125 | 중심타선급 성공 |
| `hitter_failure` | pa < 250 or wrc_plus < 90 or in_season_replaced == 1 | 교체/부진/부상 실패 |
| `hitter_durability_flag` | pa >= 450 | 성적과 별개로 시즌 완주 |

초기 가설: SSG의 1차 타깃은 대체 외국인 외야수다. 단순히 `SLG/ISO/Barrel`이 높은 선수가 아니라, KBO 투구 스타일과 문학 구장에서는 장점이 더 살아나고 결함은 덜 치명적인 선수를 찾아야 한다. 따라서 `pull-air power`, `breaking/offspeed recognition`, `low-velocity damage`, `outfield/DH defensive tolerance`, `acquirable flaw`를 함께 본다.

### 4.2 Foreign starter labels

| label | draft_rule | interpretation |
|---|---|---|
| `starter_success` | ip >= 120 and era_plus >= 105 | KBO 로테이션 성공 |
| `starter_strong_success` | ip >= 150 and era_plus >= 120 and k_bb_pct >= league_avg | 1-2선발급 성공 |
| `starter_failure` | ip < 80 or era_plus < 90 or in_season_replaced == 1 | 교체/부상/부진 실패 |
| `starter_inning_eater` | avg_ip_per_start >= 5.7 and qs_pct >= league_avg | SSG 선발진 안정성 기여 |

초기 가설: KBO 선발 전환은 raw stuff보다 `BB%`, `first_pitch_strike`, `full_count_zone`, `third_pitch_quality`, `summer_velocity_retention`이 실패 방지에 중요하다.

### 4.3 Asian quota reliever labels

아시아쿼터 표본이 작으면 NPB/CPBL/ABL 출신 KBO 불펜 사례와 KBO 외국인 불펜 사례를 보조 proxy로 사용한다.

| label | draft_rule | interpretation |
|---|---|---|
| `reliever_success` | appearances >= 45 and k_bb_pct >= league_avg and wpa > 0 | 시즌 내내 쓸 수 있는 불펜 |
| `reliever_strong_success` | high_leverage_role == 1 and wpa > 0 and bb_pct <= league_avg | 필승조급 성공 |
| `reliever_failure` | appearances < 25 or bb_pct >= league_avg + 3pp or in_season_replaced == 1 | 활용 어려운 실패 |
| `reliever_durability_flag` | back_to_back_games >= role_avg and injury_days == 0 | 연투/내구성 |

초기 가설: 아시아쿼터 불펜은 선발보다 표본이 작기 때문에 `low_walk_relief`, `short_burst_stuff`, `back_to_back_durability`, `high_leverage_translation`의 해석 가능성이 중요하다.

## 5. Core Feature Hypotheses 20

각 feature는 “왜 SSG 외인 영입에 도움이 되는가”를 함께 정의한다.

| no | feature_hypothesis | why_it_matters_for_ssg | proxy_if_missing |
|---:|---|---|---|
| 1 | `SSG Need Fit Score` | 후보 강점이 SSG의 실제 약점과 맞아야 marginal value가 생긴다. | 팀 순위 z-score와 포지션 split |
| 2 | `KBO Translation Index` | 미국/일본 성적이 KBO에서 번역될 가능성을 분리해야 한다. | 과거 성공자 유사도 |
| 3 | `Acquirable Flaw Score` | KBO에 올 수 있는 선수는 반드시 결함이 있으므로 감당 가능한 결함을 찾아야 한다. | 40-man outside, AAA 반복, 수비/삼진/나이 flaw |
| 4 | `Availability Score` | 아무리 좋아도 MLB/NPB 기회가 크면 영입 가능성이 낮다. | 40-man, option, roster block, 최근 DFA/FA |
| 5 | `Risk Penalty` | 부상/구속 하락/볼넷 과다는 KBO 전환 실패의 주요 원인이다. | IL days, recent playing time, velo trend |
| 6 | `Munhak Park Fit Score` | 문학의 좌우 95m, 중앙 120m, 낮은 펜스 구조는 타구 방향/피홈런 리스크와 연결된다. | home/away HR factor, pull-air%, HR/FB |
| 7 | `ABS Adaptation Score` | 2024년 이후 KBO ABS는 프레이밍보다 존 공략/판단 능력의 가치를 키운다. | zone%, chase%, called_strike, BB%, shadow decision |
| 8 | `Pitch Clock/Tempo Fit` | 템포 변화는 제구 불안 투수와 긴 루틴 타자에게 리스크가 된다. | Savant pitch tempo, violation/news proxy |
| 9 | `Climate Adaptation Score` | 인천 여름의 고온다습 환경은 내구성, 구속 유지, 타격 컨디션에 영향을 줄 수 있다. | southern US experience, June-Aug split |
| 10 | `Recent Trend Stability` | 최근 1-2년 스킬이 유지되는지 보지 않으면 과거 이름값에 속는다. | rolling 2-year z-score slope |
| 11 | `Contact Quality vs Low Velocity` | KBO 평균 구속은 MLB보다 낮으므로 낮은 구속/변화구를 때릴 수 있는지가 중요하다. | Savant pitch velocity bucket splits |
| 12 | `Breaking Ball Recognition` | KBO 투수들은 변화구/유인구 비중이 높아 pure fastball hitter는 실패할 수 있다. | whiff/chase vs breaking/offspeed |
| 13 | `Pull-Air Power Fit` | 장타형 외야/1루 후보는 문학 펜스와 당겨친 뜬공의 궁합이 중요하다. | Pull% * FB% * Barrel% |
| 14 | `Defensive Tolerance Score` | 수비 약한 외인 타자를 SSG가 감당할 수 있는지 포지션 뎁스로 판단한다. | team OF/1B/DH defensive proxy |
| 15 | `Platoon Survivability` | KBO는 엔트리와 외인 슬롯이 제한되어 극단적 플래툰 약점은 위험하다. | vs L/R OPS, K%, xwOBA |
| 16 | `Inning Eating Score` | 외국인 선발은 좋은 4이닝보다 안정적 6이닝이 가치 있다. | GS, IP/start, TBF, pitch count |
| 17 | `First Inning Stability` | 초반 실점이 잦은 선발은 불펜 과부하와 연결된다. | inning split ERA/FIP |
| 18 | `Times Through Order Penalty` | MLB에서 3순번 약점이 KBO에서는 감당 가능한지 판단해야 한다. | TTO split |
| 19 | `Low Walk Relief Score` | 불펜은 볼넷 하나가 leverage에서 크게 손실되므로 BB 억제가 중요하다. | BB%, first_pitch_strike, zone% |
| 20 | `High Leverage Translation Score` | 아시아쿼터 불펜은 7-9회 승부처에서 가치가 커야 한다. | gmLI, pLI, WPA, inherited runner proxy |

## 6. 발표에서 강력한 독창 변수 10

1. `Acquirable Flaw Score`: “왜 MLB에서 애매하지만 KBO에서는 살 수 있는가”를 설명하는 핵심 변수.
2. `KBO Translation Index`: 단순 성적이 아니라 리그/나이/스킬/유사 성공자를 통합한 전환 점수.
3. `SSG Need Fit Score`: SSG의 약점과 후보 장점의 결합으로 “SSG만을 위한 추천”을 만든다.
4. `Munhak Park Fit Score`: 타구 방향/피홈런 위험을 홈구장 특성과 연결한다.
5. `ABS Adaptation Score`: KBO의 제도 변화와 선수 선택을 직접 연결한다.
6. `Climate Adaptation Score`: 한국 여름 적응을 단순 감상이 아니라 proxy로 계량화한다.
7. `Breaking Ball Recognition Score`: KBO식 투구 패턴 적응 가능성을 타자 평가에 반영한다.
8. `Inning Eating Score`: 외국인 선발의 실제 팀 기여를 이닝/피로 관리와 연결한다.
9. `Low Walk Relief Score`: 아시아쿼터 불펜에서 구속보다 먼저 확인할 실패 방지 변수.
10. `High Leverage Translation Score`: NPB/팜/독립리그 성적이 KBO 필승조로 번역되는지 평가한다.

## 7. 전체 분석 로드맵

| phase | goal | inputs | outputs |
|---|---|---|---|
| 00_problem_definition | 문제와 metric 정의 | 프로젝트 요구사항 | scoring framework, leakage rules |
| 01_data_audit | 수집 가능성/약관/컬럼 확인 | source list | source_log, data dictionary |
| 02_ssg_team_analysis | SSG 약점 진단 | KBO team/player/split stats | SSG need report |
| 03_kbo_foreign_success_dataset | 외국인 성공/실패 dataset 구축 | KBO foreign history, pre-arrival stats | labeled historical transfer table |
| 04_hitter_candidate_pool | 외국인 타자 후보군 생성 | MLB/MiLB stats, Statcast, roster | hitter longlist |
| 05_pitcher_candidate_pool | 외국인 선발 후보군 생성 | MLB/MiLB pitching, Statcast, roster | starter longlist |
| 06_asian_quota_candidate_pool | 아시아쿼터 불펜 후보군 생성 | NPB/Farm/CPBL/ABL/public data | reliever longlist |
| 07_feature_engineering | SSG/KBO 특화 변수 생성 | longlists + team need | feature matrix |
| 08_modeling_ranking_validation | baseline ladder와 backtest | historical transfer feature matrix | OOF predictions, ranking metrics |
| 09_error_analysis_ablation | 실패 사례/과대평가 변수 점검 | model outputs | ablation table, error taxonomy |
| 10_final_shortlist_report | 최종 shortlist와 scouting report | validated ranking + latest availability | Top 5-10 per role, final 3 |

## 8. 바로 다음 단계

1. `01_data_audit.ipynb`에서 실제 접근 가능한 표/CSV/API를 확인한다.
2. `data/schemas/`의 최소 스키마를 기준으로 수집 템플릿을 확정한다.
3. 2023-2026 SSG 팀 타격/선발/불펜 지표를 먼저 채우되, 우선순위는 외야/중심타선/장타 결핍 진단에 둔다.
4. SSG 기사/인터뷰 corpus는 키워드 사전 기반으로 시작하고, 본문 접근이 제한되면 제목/요약/공식 보도자료 중심 proxy로 진행한다.
5. 후보 추천은 SSG need report와 historical foreign success dataset이 만들어진 뒤 시작한다.
