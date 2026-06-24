# Unified Recommendation Model Structured-Only v2

Generated: 2026-06-22 KST

## 한 줄 요약

1~6번 분석을 각각 따로 결론 내지 않고, 하나의 `SSG Foreign Player Fit Model`로 통합했다.

**중요 변경:** 기사, 인터뷰, 뉴스, 스카우팅 문장, 글 기반 텍스트 변수는 최종 모델 input에서 제외했다. 이 v2는 숫자형 성적 데이터와 구조화된 로스터/포지션/나이/계약 접근성/메디컬 상태 데이터만 사용한다.

모델의 목적은 다음과 같다.

> 여러 데이터 블록을 input으로 넣고, SSG에 맞는 외인투수 3명과 외인타자 3명을 output으로 뽑는다.

## 데이터 마이닝 과정

1. **SSG 숨은 약점 마이닝**: 2026 SSG 상황별/역할별 split에서 팀 고유 병목을 찾았다.
2. **KBO 외인 성공/실패 유형 마이닝**: 과거 외국인 선수의 성공/실패 유형을 feature block으로 바꿨다.
3. **후보 시장 구축**: MLB/AAA/AA/NPB/CPBL 성적, 로스터, 포지션, 계약 접근성으로 실제 후보 시장을 만들었다.
4. **KBO 번역 모델**: 해외 성과가 KBO에서 통할 가능성을 보수적으로 반영했다.
5. **실패 리스크 모델**: 구조화된 메디컬/계약/로스터 위험만 penalty로 반영했다.
6. **SSG fit ranking**: 모든 feature block을 하나의 점수로 통합하고 Top 3를 출력했다.

이 결과는 구조화 데이터 기반 추천 후보이며, 계약 확정 추천은 아니다. 계약 조건과 메디컬 세부 확인은 마지막 수동 검토로 남는다.

## 통합 점수 공식

```text
Unified Fit Score =
  weighted feature-block score
+ role/position adjustment
+ sample adjustment
+ age adjustment
- categorical risk penalty
```

타자는 외야 우선순위를 반영해 포수/내야수 후보를 Top 3에서 제외했다. 투수는 SSG 메시지에 맞춰 선발/멀티이닝 지속성을 추가 보정했다.

## Feature Blocks

| slot | slot_label | feature_block | source_layer | input_column | weight | plain_explanation |
| --- | --- | --- | --- | --- | --- | --- |
| foreign_pitcher | 외인투수 | SSG Need Fit | Layer 1 | ssg_fit_component | 0.32 | SSG 상황별 병목과 후보 능력의 직접 적합도 |
| foreign_pitcher | 외인투수 | KBO Translation | Layer 4 | kbo_translation_component | 0.22 | 해외 성과가 KBO에서 통할 가능성 |
| foreign_pitcher | 외인투수 | Market Realism | Layer 3 | market_realism_component | 0.17 | 로스터/계약/접근 가능성 |
| foreign_pitcher | 외인투수 | Tool Process | Layer 2/4 | tool_process_component | 0.09 | KBO 외인 유형과 후보 세부 지표의 연결성 |
| foreign_pitcher | 외인투수 | Surplus Access | Layer 3 | surplus_access_component | 0.1 | 비용 대비 접근성과 시장 비효율 |
| foreign_pitcher | 외인투수 | Failure Resilience | Layer 5 | failure_resilience_component | 0.1 | 실패 리스크를 버틸 가능성 |
| foreign_hitter | 외인타자 | SSG Need Fit | Layer 1 | ssg_fit_component | 0.34 | SSG 상황별 병목과 후보 능력의 직접 적합도 |
| foreign_hitter | 외인타자 | KBO Translation | Layer 4 | kbo_translation_component | 0.24 | 해외 성과가 KBO에서 통할 가능성 |
| foreign_hitter | 외인타자 | Market Realism | Layer 3 | market_realism_component | 0.15 | 로스터/계약/접근 가능성 |
| foreign_hitter | 외인타자 | Tool Process | Layer 2/4 | tool_process_component | 0.08 | KBO 외인 유형과 후보 세부 지표의 연결성 |
| foreign_hitter | 외인타자 | Surplus Access | Layer 3 | surplus_access_component | 0.09 | 비용 대비 접근성과 시장 비효율 |
| foreign_hitter | 외인타자 | Failure Resilience | Layer 5 | failure_resilience_component | 0.1 | 실패 리스크를 버틸 가능성 |

## 최종 Top 3 Output

| slot_label | recommendation_rank | player_name | team_or_org | primary_position | age | unified_fit_score | data_mining_reason | structured_risk_check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 외인타자 | 1 | Luis Matos | MIL | Outfielder | 24.0 | 81.367 | SSG runner-on-first 전환 병목을 겨냥한 OF/DH 후보; SSG fit 72.0; KBO translation 75.2; market 93.7; recent PA 205, wOBA 0.300 | market_realism_status=contract_verification_needed (-0.5) |
| 외인타자 | 2 | Will Brennan | SF | Outfielder | 28.0 | 80.52 | SSG runner-on-first 전환 병목을 겨냥한 OF/DH 후보; SSG fit 80.4; KBO translation 85.0; market 99.6; recent PA 36, wOBA 0.116 | market_realism_status=manual_contact_priority_locked (-2.5) / medical_risk_bucket=medical_history_watch (-3) / contract_access_bonus=recent_dfa_high_access (+1.5) |
| 외인타자 | 3 | Dominic Fletcher | PIT | Outfielder | 28.0 | 78.945 | SSG runner-on-first 전환 병목을 겨냥한 OF/DH 후보; SSG fit 75.4; KBO translation 80.3; market 93.8; recent PA 34, wOBA 0.310 | market_realism_status=contract_verification_needed (-0.5) |
| 외인투수 | 1 | Josh Fleming | TOR | Pitcher | 30.0 | 80.886 | SSG 선발 runway/불펜 tax 문제에 맞춘 SP/multi-inning 후보; SSG fit 76.4; KBO translation 77.0; market 93.2; 2026 MiLB 53.0 IP/10 GS | market_realism_status=contract_verification_needed (-0.5) |
| 외인투수 | 2 | Bruce Zimmermann | STL | Pitcher | 31.0 | 76.935 | SSG 선발 runway/불펜 tax 문제에 맞춘 SP/multi-inning 후보; SSG fit 72.2; KBO translation 71.3; market 93.1; 2026 MiLB 67.7 IP/13 GS | market_realism_status=contract_verification_needed (-0.5) |
| 외인투수 | 3 | Yariel Rodríguez | TOR | Pitcher | 29.0 | 76.318 | SSG 선발 runway/불펜 tax 문제에 맞춘 SP/multi-inning 후보; SSG fit 74.1; KBO translation 70.2; market 99.6; 2026 MiLB 13.7 IP/1 GS | market_realism_status=manual_contact_priority_locked (-2.5) / contract_access_bonus=recent_dfa_high_access (+1.5) |

## Presentation Message

We did not use articles or text-derived variables in the final model. The structured-only model first mines SSG's hidden needs, translates those needs into numeric candidate-side feature blocks, filters the market by acquisition realism, penalizes structured failure risk, and only then outputs three pitchers and three hitters.
