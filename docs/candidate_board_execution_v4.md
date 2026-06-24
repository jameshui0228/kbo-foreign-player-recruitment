# Candidate Board Execution v4

## 핵심 수정

기존 보드는 data-mining score가 높은 젊은 MLB-depth 후보를 너무 적극적으로 올렸다. v4에서는 실제 KBO 영입 가능성을 후보 축소 단계에 포함한다.

## 현실성 반영 게이트

- 40-man 또는 방금 claimed/selected/traded된 선수는 active Top 3에서 제외한다.
- age 25 이하의 MLB 재도전 가치가 큰 선수는 discovery 단계에서 좋아 보여도 hold로 둔다.
- 외국인 타자는 OF/DH 역할을 우선하고, 1B/3B 전용 후보는 role hold로 둔다.
- 실패 경고 신호가 높거나 K%/run-kill risk가 큰 후보는 watchlist로 둔다.
- 최종 active board는 모델 지지 신호, 시장 접근성, 역할 적합성을 함께 통과한 후보 안에서 고른다.

## 재구성 결론

- 외국인 타자 현실형 Top 3: Will Brennan, Dominic Fletcher, Dylan Carlson
- Luis Matos: 초기 discovery 리드였지만 age 24와 MLB 재도전 가치 때문에 접촉 보류
- Nolan Jones: power/OBP discovery 신호는 강하지만 cash trade와 salary signal 때문에 cost/rights hold
- 외국인 투수 현실형 Top 3: Josh Fleming, Keegan Thompson, Kolby Allard
- Bryse Wilson: 6/18 selected contract 이후 contract blocker hold

## 발표용 한 줄

최종 모델은 '가장 점수가 높은 선수'가 아니라 'KBO로 실제 데려올 수 있는 선수 중 SSG 약점에 가장 잘 맞는 선수'를 고르는 현실성 반영 통합 모델로 수정했다.
