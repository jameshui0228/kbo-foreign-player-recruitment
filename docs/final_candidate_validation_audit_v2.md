# Final Candidate Validation Audit v2

## Verdict

기존 최종 후보 보드는 그대로 최종본으로 쓰기에는 부족했다. 핵심 문제는 타자 3순위와 투수 결론의 표현 방식이다.

- 타자: Jack Suwinski는 반복 추천 신호와 BB/barrel upside가 있으나, strict data-mining model에서는 success-score 36.3%, failure-score 68.4%, margin -0.3205로 나타났다. 따라서 최종 Top 3가 아니라 upside watchlist가 타당하다.
- 타자 수정: strict data-mining Top 3는 Luis Matos, Nolan Jones, Dylan Carlson이다.
- 투수: Josh Fleming은 최종 접촉 1순위로 유지 가능하지만, 이것은 pitcher classifier가 강하게 뽑은 결론이 아니라 market/role/medical gate를 통과한 verification priority다.

## Corrected Final Board

| Slot | Final Top 3 | Contact 1st | Confidence |
|---|---|---|---|
| Foreign hitter | Luis Matos, Nolan Jones, Dylan Carlson | Luis Matos | Medium-high |
| Foreign pitcher | Josh Fleming, Bryse Wilson, Austin Gomber | Josh Fleming | Medium-low / verification-led |

## Why Suwinski Was Reclassified

아래 Success/Failure는 calibration된 절대 확률이 아니라 동일 모델 안에서 후보 간 우선순위와 margin을 비교하기 위한 ranking probability score다. 따라서 발표에서는 "이 선수가 실제로 KBO에서 성공할 확률이 92.4%"가 아니라 "과거 KBO 외인 성공/실패 패턴과 비교했을 때 모델 점수가 가장 높다"로 설명하는 것이 안전하다.

| Player | DM rank | Success | Failure | Margin | Decision |
|---|---:|---:|---:|---:|---|
| Luis Matos | 1 | 92.4% | 8.2% | 0.8418 | Final Top 3 |
| Nolan Jones | 2 | 90.2% | 9.2% | 0.8096 | Final Top 3 |
| Dylan Carlson | 3 | 82.4% | 15.1% | 0.6733 | Final Top 3 |
| Jack Suwinski | 6 | 36.3% | 68.4% | -0.3205 | Watchlist |

Suwinski의 강점은 BB% 13.5%와 barrel rate 11.8%다. 그러나 wOBA .253, K% 31.5%, failure ranking score 68.4%가 동시에 나오기 때문에 SSG가 정의한 run-kill avoidance hitter와 충돌한다. 이 결론은 후보를 싫어해서가 아니라 모델이 발견한 위험을 반영한 것이다.

## Pitcher Interpretation

Pitcher model은 training rows 49명, aggregate MiLB features 8개 기반이라 classifier 안정성이 낮다. 따라서 Bryse Wilson과 Austin Gomber는 diagnostic leads이고, Josh Fleming은 strict classifier lead가 아니라 다음 조건을 통과한 실행 우선 후보로 봐야 한다.

- 좌완 선발/스윙맨 role fit
- HR/9 0.79, BB/9 2.42 기반 damage-control signal
- minor-league contract/access signal
- medical red flag가 hard hold는 아닌 상태

## Report Action

보고서는 다음 방식으로 수정했다.

- 최종 타자 Top 3: 기존 보드의 Suwinski를 Carlson으로 교체
- Suwinski: 최종 후보가 아니라 watchlist로 재분류
- 투수: Josh Fleming을 contact 1st로 유지하되, classifier certainty가 아니라 gate-adjusted verification priority로 표현
- 후보 보드: `outputs/tables/final_candidate_board_validated_v2.csv` 생성

## Professor Defense Checklist

- "92.4%"는 실제 KBO 성공확률이 아니라 동일 모델 안에서 후보를 비교하기 위한 ranking probability score다.
- 타자 모델은 repeated stratified CV 기준 success AUC 0.833, failure AUC 0.738이라 후보 선별의 주요 근거로 사용할 수 있다.
- 투수 모델은 AUC 0.603이라 확정 추천 모델로 쓰지 않았고, command/starter floor/medical/market gate를 결합한 verification priority로만 사용했다.
- Jack Suwinski는 볼넷과 barrel upside가 있지만, failure-score와 K%가 SSG의 run-kill avoidance 조건과 충돌해 최종 Top 3에서 제외했다.
- Josh Fleming은 "모델이 압도적으로 뽑은 선수"가 아니라 시장 접근성, 역할 적합성, damage-control signal이 동시에 맞는 접촉 1순위다.
