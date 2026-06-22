# Claude 세션 작업 요약 및 최종 후보 리스트

작성일: 2026-06-23

---

## 1. 세션에서 진행한 작업

### 저장소 연결 및 코드 파악
- GitHub 저장소 클론 및 전체 프로젝트 구조 파악
- 고려대학교 SDA 동아리의 SSG 랜더스 외국인 선수 영입 분석 프로젝트 확인

### 코드 분석
전체 파이프라인을 6개 레이어로 해부:

| 레이어 | 파일 | 역할 |
|---|---|---|
| L1 | `mine_ssg_hidden_state_needs.py` | SSG 팀 약점 진단 |
| L2 | `build_kbo_foreign_archetype_bridge_v0_2.py` | 역대 KBO 외국인 성공/실패 아카이프 발굴 |
| L3 | `build_market_realism_layer_v0_1.py` | 시장 현실성 평가 (계약·접근성) |
| L4 | `build_candidate_pool_v1.py` + `build_ssg_fit_preparation_mart_v0_1.py` | 후보 풀 구축 + SSG Fit 점수화 |
| L5 | `build_candidate_failure_risk_ledger_v0_1.py` | 6차원 실패 리스크 원장 |
| L6 | `build_ssg_risk_adjusted_fit_queue_v0_1.py` | 최종 리스크 조정 점수 + 리뷰 큐 |

### 모델링 알고리즘 분석
- KBO 적응 실패 예측 모델 (`train_kbo_translation_failure_models_v0_2/v0_3.py`)
  - 사용 모델: Ridge Logistic Regression, Balanced Ridge Logit, Shallow Random Forest (N≥24), HistGradientBoosting (N≥30)
  - 검증 방식: 시간 순방향 홀드아웃 + 반복 층화 교차검증 (3-fold × 30회 = 90 폴드)
  - 베이스라인: role_prior (역할별 사전 확률)

### 게이트 시스템 분석
- G1~G6 게이트 통과 조건 파악
- 현재 상태: G1~G5 실질적 통과, G6 정책적 LOCK 상태
- 전체 후보 풀: 외국인 타자 736명, 외국인 투수 1009명 → 스코어링 완료

### 최종 후보 필터링
- `ssg_risk_adjusted_fit_queue_v0_1.csv`에서 `lane_2_deep_review_candidate_locked` + `stable_top25_locked` 조건으로 필터링
- 외국인 타자 22명, 외국인 투수 23명 → 추가 분석으로 최종 후보 압축

---

## 2. 최종 추천 후보 리스트

> 아시아쿼터는 이번 분석 범위에서 제외.

### 외국인 타자

| 우선순위 | 선수 | 현 소속 | 계약 상태 | wOBA | Hardhit% | 배럴% | 실패리스크 | 추천 이유 |
|---|---|---|---|---|---|---|---|---|
| **1순위** | **Trey Mancini** | LAA | DFA (즉시 접근 가능) | .386 | 66.7% | 16.7% | 33.0 | 성적 22명 중 최고, 리스크 없음, 즉시 영입 가능 |
| **2순위** | **Dominic Fletcher** | PIT | 40인 외 | .310 | 40.0% | 3.3% | 36.1 | 타구 질 안정적, SSG Fit 상위 |
| **3순위** | **Abraham Toro** | KC | 40인 외 | .305 | 34.2% | 4.5% | 37.1 | 다재다능, 성공 확률 0.859 |
| **4순위** | **Omar Martinez** | LAA | DFA (즉시 접근 가능) | .300 | 50.0% | — | 31.5 | 접근 쉬움, K% 33%는 단점 |
| **5순위** | **Nolan Jones** | CLE | 40인 외 | .278 | 47.1% | 8.6% | 37.8 | BB% 9.7% 선구안 우수 |

**주의:** C.J. Stubbs (모델 점수 1위)는 Savant 데이터 미연결로 점수가 부풀려진 상태 — 실질 1순위에서 제외.

---

### 외국인 투수

| 우선순위 | 선수 | 현 소속 | 계약 상태 | 2026 AAA IP | K9 | BB9 | HR9 | 실패리스크 | 추천 이유 |
|---|---|---|---|---|---|---|---|---|---|
| **1순위** | **Josh Fleming** | TOR | 40인 외 | 53.0 | 7.5 | 1.4 | 0.51 | 38.8 | 커맨드 압도적 1위, 선발 이닝 안정적 유지 |
| **2순위** | **Ian Hamilton** | ATL | 40인 외 | 19.7 | 11.4 | 1.8 | 0.92 | 40.6 | 탈삼진 최고, 커맨드 양호 |
| **3순위** | **Kolby Allard** | CLE | 40인 외 | 25.3 | 7.5 | 3.2 | 0.36 | 41.1 | HR 거의 없음, 선발 이닝 유지 |
| **4순위** | **Shaun Anderson** | LAA | DFA (즉시 접근 가능) | 27.3 | 9.5 | 4.0 | 0.99 | 35.4 | DFA로 접근 쉬움, 삼진 많음 |
| **5순위** | **Jayden Murray** | HOU | DFA (즉시 접근 가능) | 15.3 | 11.2 | 3.5 | 0.0 | 37.8 | HR 0, 접근 쉬움 (샘플 적어 주의) |

**제외:** Yariel Rodriguez (모델 4위) — BB9=5.93으로 KBO 적합성 미달 판단.

---

## 3. 즉시 접촉 권장 대상 (DFA/방출 상태)

```
타자: Trey Mancini (LAA DFA) → 지금 당장 영입 가능
투수: Shaun Anderson (LAA DFA), Jayden Murray (HOU DFA) → 즉시 접근 가능
```

DFA 선수는 다른 팀에 클레임되거나 방출될 수 있어 시간이 중요합니다.

---

## 4. 다음 단계

1. 위 선수들의 에이전트 연락처 확인 및 KBO 의향 타진
2. 현재 부상 상태 최신 확인 (로스터 노트)
3. 연봉 협상 가능 범위 확인 (KBO 외국인 선수 연봉 한도 내 여부)
