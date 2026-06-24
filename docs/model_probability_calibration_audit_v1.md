# Model Probability Calibration Audit v1

## 결론

- 직접적인 label leakage는 발견되지 않았다. 학습 피처에 success/failure/first_kbo/renewal/outcome/player id 계열 컬럼이 들어가지 않았다.
- 후보 입력 매핑도 success/failure/outcome 계열 컬럼을 쓰지 않았다.
- 다만 타자 학습 표본은 22행, 선수 단위 고유 그룹은 더 적고 일부 선수가 여러 시즌 반복된다. 따라서 full-fit predict_proba를 절대 성공확률로 표기하면 과신 위험이 크다.
- 보고서에서는 `성공확률 98.1%`가 아니라 `성공 모델 지지 점수`, `실패 경고 점수`, `후보 간 순위 신호`로 표현해야 한다.

## Audit Table

| target | historical_rows | unique_player_groups | positive_rows | feature_count | forbidden_feature_hits | candidate_mapping_forbidden_hits | train_candidate_player_id_overlap_count | train_candidate_player_id_overlap | full_fit_auc | full_fit_brier | full_fit_logloss | full_fit_max_pred | full_fit_p90_pred | full_fit_mean_pred | full_fit_mean_pred_positive | full_fit_mean_pred_negative | leave_one_player_group_auc | leave_one_player_group_brier | leave_one_player_group_logloss | leave_one_player_group_max_pred | leave_one_player_group_p90_pred | leave_one_player_group_mean_pred | leave_one_player_group_mean_pred_positive | leave_one_player_group_mean_pred_negative |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| success | 22 | 17 | 13 | 18 |  |  | 2 | 621550|676724 | 1.0000 | 0.0610 | 0.2331 | 0.9789 | 0.8976 | 0.5909 | 0.8407 | 0.2301 | 0.6496 | 0.2899 | 0.8113 | 0.9990 | 0.9086 | 0.4909 | 0.5605 | 0.3904 |
| failure | 22 | 17 | 8 | 18 |  |  | 2 | 621550|676724 | 0.9911 | 0.0615 | 0.2425 | 0.9145 | 0.8812 | 0.3636 | 0.7295 | 0.1546 | 0.5000 | 0.3302 | 0.9905 | 0.9723 | 0.8984 | 0.4916 | 0.5375 | 0.4654 |

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
