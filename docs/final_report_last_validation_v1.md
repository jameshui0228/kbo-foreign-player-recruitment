# Final Report Last Validation v1

## 결론

최종 보고서는 발표용으로 마무리 가능한 상태다. 다만 모델 산출값을 절대 성공확률로 해석하지 않는다는 전제를 명확히 유지해야 한다. 최종본은 과도한 확률 표현을 제거했고, 후보 비교는 `모델 지지`, `실패 경고`, `시장 접근성`, `의료/실행 검증`, `최종 접촉 순위`로 설명한다.

## 누수 검증

- 학습 feature에 success, failure, first-KBO 결과, renewal, player id, outcome 계열 직접 누수 feature는 발견되지 않았다.
- 후보 입력 매핑도 success/failure/outcome 계열 컬럼을 사용하지 않았다.
- train-candidate player id overlap은 2명 있었지만 최종 후보 보드와 무관하다.
- 따라서 직접적인 label leakage 근거는 발견되지 않았다.

## 과적합 및 보정 검증

- 타자 모델 full-fit AUC는 success 1.000, failure 0.991로 매우 높아 절대 확률로 쓰기에는 과신 위험이 있다.
- 선수 단위 leave-one-player-group 검증에서는 success AUC 0.650, failure AUC 0.500으로 낮아졌다.
- 이 때문에 최종 PDF에서는 `98% 성공확률`류 표현을 제거했다.
- 보고서에서는 확률이 아니라 후보 간 비교 신호와 접촉 우선순위로만 해석한다.

## 현실성 검증

- 최종 접촉 후보 6명 중 40-man blocker는 없다.
- Bryse Wilson, Randy Dobnak처럼 40-man 또는 현 구단 통제력이 강한 후보는 hold로 내려갔다.
- Luis Matos는 모델상 강하지만 age 24와 MLB 재도전 가치 때문에 active Top 3에서 제외했다.
- Nolan Jones는 모델상 강하지만 cash trade와 salary/cost-share 확인 필요성 때문에 hold로 분류했다.

## 최종 후보

타자:

1. Will Brennan
2. Dominic Fletcher
3. Dylan Carlson

투수:

1. Josh Fleming
2. Keegan Thompson
3. Kolby Allard

최종 접촉 1순위:

- 외국인 타자: Will Brennan
- 외국인 선발투수: Josh Fleming

## PDF QA

- PDF 페이지 수: 23
- `realism`, `realistic`, `Gate-adjusted`, `success probability`, `98.1`, `92.4%`, `36.3%` 등 부적절하거나 과도한 표현은 최종 PDF 본문에서 발견되지 않았다.
- 핵심 섹션인 모델 누수 및 보정 검증, 선수 단위 그룹 검증, 확률 표기 제거, 최종 접촉 1순위, 시장 접근성 모형, 의료/실행 검증이 모두 포함되어 있다.
- 주요 페이지 렌더링 확인 결과 표와 그래프는 읽을 수 있는 수준이다.

