# Final Project Handoff

작성일: 2026-06-25  
프로젝트: SDA 2기 SSG 랜더스 외국인 타자/선발투수 영입 제안

이 문서는 발표 이후 팀원이 GitHub 저장소에서 최종 산출물, 데이터, 모델, 발표 자료를 빠르게 찾기 위한 handoff 문서다.

## 1. 최종 결론

### 최종 접촉 1순위

| 슬롯 | 최종 1순위 | 핵심 이유 |
|---|---|---|
| 외국인 타자 | Will Brennan | 40인 로스터 밖 접근성, contact floor, 우투 상대 흐름 단절 완화, run-kill 위험 완화 |
| 외국인 선발투수 | Josh Fleming | AAA 선발 이력, BB/9 1.36, HR/9 0.51, traffic-command starter 유형 |

### Final Top 3

| 슬롯 | 1순위 | 2순위 | 3순위 |
|---|---|---|---|
| 타자 | Will Brennan | Dominic Fletcher | Dylan Carlson |
| 투수 | Josh Fleming | Keegan Thompson | Kolby Allard |

### 보류/Watch 후보

| 선수 | 구분 | 보류 이유 |
|---|---|---|
| Luis Matos | HOLD | 데이터 발견 신호는 강하지만 age 24와 MLB reset value 때문에 KBO행 가능성이 낮음 |
| Nolan Jones | COST HOLD | power/OBP/hard-hit 신호는 강하지만 cash trade와 salary signal로 비용 부담 큼 |
| Jack Suwinski | WATCHLIST | BB/barrel upside는 있으나 high-K와 실패 경고가 큼 |
| Bryse Wilson | CONTRACT HOLD | selected contract 이후 40-man/MLB 접근성 장벽 발생 |
| Bruce Zimmermann | WATCHLIST | K/9 매력은 있으나 HR/9 1.86으로 장타 경고 큼 |

## 2. 발표에서 밀고 간 핵심 메시지

### 타자 메시지

SSG의 문제는 단순 장타 부족이 아니라, 우투 선발 경기에서 OF/DH가 이닝을 다시 열지 못하고 run-kill 위험이 커지는 흐름 단절이다. 따라서 필요한 유형은 단순 거포가 아니라 `inning-transition OF/DH`다.

주요 근거:

| SSG 약점 규칙 | 평균 득실 |
|---|---:|
| RHP game-script lock | -5.10 |
| RHP OF/DH run-kill | -5.11 |
| Extra-out resilience | -4.50 |

### 투수 메시지

SSG의 선발 보강은 탈삼진 쇼케이스형보다 주자 허용 이후 볼넷과 장타 피해를 줄이고 5이닝 전후의 길이를 확보하는 `traffic-command starter`가 더 직접적이다.

주요 근거:

| SSG 약점 규칙 | 평균 득실 |
|---|---:|
| Starter length support / top-opponent short start | -5.83 |

## 3. 최종 산출물 위치

### 발표 자료

| 산출물 | 파일 |
|---|---|
| 최종 발표 PDF | `reports/presentation/SSG_final_presentation_2026-06-24.pdf` |
| 최종 발표 대본 | `reports/presentation/SSG_final_script_2026-06-24.docx` |
| 발표용 그래프 PNG | `outputs/ppt_graphs/` |
| 발표용 표 PNG | `outputs/ppt_tables_png/` |
| Canva/Gamma 보충 슬라이드 | `outputs/canva_supplement_pages/` |

### 최종 보고서

| 산출물 | 파일 |
|---|---|
| Overleaf 최종 PDF | `reports/ssg_overleaf_report_final.pdf` |
| Overleaf 원문 | `reports/overleaf_ssg_recruitment/main.tex` |
| Overleaf assets/tables | `reports/overleaf_ssg_recruitment/assets/`, `reports/overleaf_ssg_recruitment/tables/` |
| 발표 치트시트 PDF | `output/pdf/SSG_발표_핵심_인사이트_치트시트.pdf` |
| 보고서 생성 스크립트 | `scripts/build_overleaf_report.py` |

### 핵심 모델/검증 문서

| 목적 | 파일 |
|---|---|
| 통합 추천 모델 | `docs/unified_recommendation_model_structured_only_v2.md` |
| 현실성 반영 후보 보드 | `docs/realism_first_candidate_board_v3.md` |
| 최종 실행 후보 보드 | `docs/candidate_board_execution_v4.md` |
| KBO translation 단순 환산 | `docs/evidence_based_kbo_translation_coefficients_v2.md` |
| 최종 후보 검증 | `docs/final_candidate_validation_audit_v2.md` |
| 누수/과신/확률 보정 점검 | `docs/model_probability_calibration_audit_v1.md` |
| 마지막 검증 기록 | `docs/final_report_last_validation_v1.md` |

### 핵심 CSV

| 목적 | 파일 |
|---|---|
| 최종 실행 후보 보드 | `outputs/tables/final_candidate_board_execution_v4.csv` |
| 현실성 반영 후보 보드 | `outputs/tables/final_candidate_board_realism_v3.csv` |
| 통합 모델 Top 3 | `outputs/tables/unified_foreign_recommendations_top3_structured_only_v2.csv` |
| 통합 모델 전체 후보 pool | `outputs/tables/unified_foreign_recommendation_pool_structured_only_v2.csv` |
| feature block별 점수 | `outputs/tables/unified_recommendation_feature_blocks_structured_only_v2.csv` |
| KBO translation 계수 | `outputs/tables/evidence_based_kbo_translation_coefficients_v2.csv` |
| KBO translation 표본 | `outputs/tables/evidence_based_kbo_translation_sample_v2.csv` |
| 모델 calibration audit | `outputs/tables/model_probability_calibration_audit_v1.csv` |
| salary/contract/medical gate | `outputs/tables/final_candidate_salary_contract_gate_v1.csv` |

## 4. 모델 구조 요약

최종 모델은 6개 모듈을 합친 앙상블 구조다.

| 모듈 | 질문 | 역할 |
|---|---|---|
| A. Team Need | SSG는 어떤 경기 조건에서 무너지는가? | SSG 약점을 feature contract로 변환 |
| B. KBO History | 과거 KBO 성공/실패 외국인과 닮았는가? | 성공/실패 패턴 학습 |
| C. Archetype | 필요한 역할과 닮았는가? | 유형 유사도 계산 |
| D. Translation | 미국 성적이 KBO에서 유지될 수 있는가? | KBO 번역 리스크 평가 |
| E. Market | 실제 데려올 수 있는가? | 40-man, DFA, outright, salary, rights gate |
| F. Medical | 건강/역할/계약상 실행 가능한가? | PASS/YELLOW/HOLD/RED gate |

Raw Ranking은 데이터상 매력도이고, Final Ranking은 실행 가능성을 반영한 접촉 우선순위다.

## 5. Candidate Funnel

| 단계 | 타자 | 투수 | 의미 |
|---|---:|---:|---|
| Step 1. 전체 구조화 시장 | 736 | 1,009 | MLB/MiLB/roster 기반 모델 입력 후보 pool |
| Step 2. 후보 생성 모듈 | 16 | 18 | OR-screen: Market, Team Fit, Upside, Translation 중 하나 이상 강한 신호 |
| Step 3. 1차 검증 통과 | 6 | 3 | AND-gate: 표본, 역할, 40-man/계약, salary, medical, 데이터 결측 점검 |
| Step 4. Raw Ranking | Top 3 | Top 3 | SSG fit, KBO translation, archetype, failure resilience, consensus |
| Step 5. Final Ranking | Top 3 | Top 3 | 비용, 계약, 의료, KBO행 가능성 반영한 실행 순위 |

투수는 historical classifier 안정성이 낮았기 때문에 Step 3부터 더 보수적으로 줄였다.

## 6. 모델 신뢰도와 발표 시 주의점

| 모델 | 성능 | 발표 해석 |
|---|---:|---|
| 타자 success classifier | AUC 0.833 | 후보 간 성공 신호 분리력이 있다 |
| 타자 failure classifier | AUC 0.738 | 실패 위험 경고에 보조적으로 쓸 수 있다 |
| 투수 diagnostic classifier | AUC 0.603 | 확정 추천이 아니라 watch/diagnostic 신호로만 사용한다 |

주의:

- AUC를 "정확도"라고 부르지 않는다.
- 모델 score를 절대 성공확률처럼 말하지 않는다.
- 투수는 supervised classifier보다 BB/9, HR/9, starter floor, contract/medical gate를 더 강하게 본다.
- 기사/인터뷰 텍스트는 최종 모델 feature가 아니라 보조 확인 자료다.

## 7. KBO Translation 단순 환산 계수

`docs/evidence_based_kbo_translation_coefficients_v2.md` 기준.

| 대상 | 경험계수 | 해석 |
|---|---:|---|
| 타자 | KBO wRC+ ≈ MiLB OPS x 100 x 1.39 | KBO에 실제 온 외국인 타자 표본의 단순 baseline |
| 투수 | KBO ERA ≈ MiLB ERA x 0.80 | KBO에 실제 온 외국인 투수 표본의 단순 baseline |

이 값은 최종 예측 모델이 아니라 sanity check다. KBO에 실제 영입된 선수 표본이므로 selection bias가 있으며, 최종 ranking은 translation 계수, SSG fit, market/medical gate를 함께 사용한다.

## 8. 데이터 공개 정책

팀원 확인용 manifest:

- `docs/data_manifest_for_teammates.md`
- `outputs/tables/project_data_file_manifest_v1.csv`

GitHub에 올린 것:

- schema
- derived output tables
- 보고서, 발표 자료, notebook, 스크립트
- 재현 가능한 모델 산출물

GitHub에 올리지 않는 것:

- `.env` 및 API key/secret
- STATIZ API 원천 snapshot
- Naver API raw output
- 대용량 raw Baseball Savant/Statcast 원천 파일
- 라이선스/재배포가 불명확한 PDF 원문

필요하면 원천 파일은 Google Drive, Git LFS, private storage, 또는 재수집 스크립트로 공유한다.

## 9. 재현/확인 순서

1. `README.md`를 읽고 프로젝트 구조 확인
2. `docs/final_project_handoff_2026_06_25.md`에서 최종 파일 위치 확인
3. `reports/presentation/SSG_final_presentation_2026-06-24.pdf`로 발표 흐름 확인
4. `reports/ssg_overleaf_report_final.pdf`로 보고서 확인
5. `outputs/tables/final_candidate_board_execution_v4.csv`와 `outputs/tables/unified_foreign_recommendations_top3_structured_only_v2.csv`로 최종 후보 확인
6. `notebooks/11_layer_01_ssg_hidden_weakness_mining.ipynb`부터 `notebooks/17_unified_recommendation_model_structured_only_v2.ipynb`까지 모델 설명용 notebook 확인

## 10. 남은 후속 작업

- 발표 후 피드백 반영 여부 기록
- 최신 roster/transaction 재확인
- 의료/계약/권리 상태 추가 검증
- raw data를 공유해야 하는 팀원에게 private 경로 별도 제공
