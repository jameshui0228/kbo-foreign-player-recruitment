# Model Probability Calibration Audit v1

## 결론

- 직접적인 label leakage는 발견되지 않았다. 학습 피처에 success/failure/first_kbo/renewal/outcome/player id 계열 컬럼이 들어가지 않았다.
- 후보 입력 매핑도 success/failure/outcome 계열 컬럼을 쓰지 않았다.
- 다만 타자 학습 표본은 22행, 선수 단위 고유 그룹은 더 적고 일부 선수가 여러 시즌 반복된다. 따라서 full-fit predict_proba를 절대 성공확률로 표기하면 과신 위험이 크다.
- 보고서에서는 `성공확률 98.1%`가 아니라 `성공 모델 지지 점수`, `실패 경고 점수`, `후보 간 순위 신호`로 표현해야 한다.

## Audit Table

타자 학습 데이터는 22행, 고유 선수는 17명입니다. 아래는 학습 적합도와 선수 단위 제외 검증을 구분한 요약입니다.

| 대상 | 학습 AUC | 선수 단위 검증 AUC | 검증 Brier | 검증 Log Loss |
|---|---:|---:|---:|---:|
| success | 1.0000 | 0.6496 | 0.2899 | 0.8113 |
| failure | 0.9911 | 0.5000 | 0.3302 | 0.9905 |

[전체 검증 CSV](../outputs/tables/model_probability_calibration_audit_v1.csv)에는 표본 수, 피처 수, 선수 중복, 예측값 분포와 상세 지표가 보존되어 있습니다.

학습 성능을 일반화 성능으로 사용하지 않습니다. 선수 단위 검증 결과상 실패 모델은 충분한 판별력을 보였다고 보기 어렵고, 성공 모델 역시 작은 표본의 제한이 있습니다.

## Final Hitter Board Labels After Re-labeling

| player | decision_rank | decision | model_support_tier | failure_warning_tier | model_margin_direction | market_feasibility_score |
| --- | --- | --- | --- | --- | --- | --- |
| Will Brennan | 1 | CONTACT_1ST | 강함 | 낮음 | 긍정 | 100.0000 |
| Dominic Fletcher | 2 | CONTACT_2ND | 강함 | 낮음 | 긍정 | 60.0000 |
| Dylan Carlson | 3 | CONTACT_3RD | 중상 | 낮음 | 긍정 | 60.0000 |
| Luis Matos | HOLD | DISCOVERY_HOLD | 강함 | 낮음 | 긍정 | 60.0000 |
| Nolan Jones | HOLD | POWER_DISCOVERY_COST_HOLD | 강함 | 낮음 | 긍정 | 50.0000 |
| Jack Suwinski | WATCH | UPSIDE_WATCHLIST | 약함 | 높음 | 경고 | 60.0000 |

## 보고서 수정 지침

- `realism`, `realism-first`, `success probability`, `P(success)` 표현을 제거한다.
- 확률 표기는 `모델 지지 점수(0-100)`와 `실패 경고 점수(0-100)`로 바꾸고, 절대 확률이 아니라고 명시한다.
- Will Brennan과 Dominic Fletcher는 원 data-mining gate에서 sample gate가 걸렸으므로, 모델 점수만으로 확정하지 않고 시장 접근성과 접촉 가능성 보정 후 후보로 올렸다고 설명한다.
- 최종 결론은 `현실성 반영 통합 모델`로 표현한다.
