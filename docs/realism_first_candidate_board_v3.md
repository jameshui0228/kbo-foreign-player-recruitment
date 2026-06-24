# Realism-first Candidate Board v3

## 핵심 수정

기존 보드는 data-mining score가 높은 젊은 MLB-depth 후보를 너무 적극적으로 올렸다. v3에서는 실제 KBO 영입 가능성을 hard gate로 앞에 둔다.

## 현실성 hard gate

- 40-man 또는 방금 claimed/selected/traded된 선수는 active Top 3에서 제외한다.
- age 25 이하의 MLB 재도전 가치가 큰 선수는 discovery 단계에서 좋아 보여도 hold로 둔다.
- 외국인 타자는 OF/DH 역할을 우선하고, 1B/3B 전용 후보는 role hold로 둔다.
- failure-score가 높거나 K%/run-kill risk가 큰 후보는 watchlist로 둔다.
- 최종 active board는 model score가 아니라 market reality를 통과한 후보 안에서 고른다.

## 재구성 결론

- 외국인 타자 현실형 Top 3: Will Brennan, Dominic Fletcher, Dylan Carlson
- Luis Matos: 초기 discovery 리드였지만 age 24와 MLB 재도전 가치 때문에 realism hold
- Nolan Jones: power/OBP discovery 신호는 강하지만 cash trade와 salary signal 때문에 cost/rights hold
- 외국인 투수 현실형 Top 3: Josh Fleming, Keegan Thompson, Kolby Allard
- Bryse Wilson: 6/18 selected contract 이후 contract blocker hold

## 발표용 한 줄

최종 모델은 '가장 점수가 높은 선수'가 아니라 'KBO로 실제 데려올 수 있는 선수 중 SSG 약점에 가장 잘 맞는 선수'를 고르는 realism-first ensemble로 수정했다.
