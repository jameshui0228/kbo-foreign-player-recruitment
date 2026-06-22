# Claude 세션 작업 요약 및 최종 후보 리스트 (수정판)

작성일: 2026-06-23

---

## 1. 세션에서 진행한 작업

### 저장소 연결 및 전체 파이프라인 파악

GitHub 저장소를 클론하고, 6개 레이어로 구성된 전체 분석 파이프라인을 코드 수준에서 해부했다.

| 레이어 | 파일 | 역할 |
|---|---|---|
| L1 | `mine_ssg_hidden_state_needs.py` | SSG 팀 약점 진단 |
| L2 | `build_kbo_foreign_archetype_bridge_v0_2.py` | 역대 KBO 외국인 성공/실패 아카이프 발굴 |
| L3 | `build_market_realism_layer_v0_1.py` | 시장 현실성 평가 (계약·접근성) |
| L4 | `build_candidate_pool_v1.py` + `build_ssg_fit_preparation_mart_v0_1.py` | 후보 풀 구축 + SSG Fit 점수화 |
| L5 | `build_candidate_failure_risk_ledger_v0_1.py` | 6차원 실패 리스크 원장 |
| L6 | `build_ssg_risk_adjusted_fit_queue_v0_1.py` | 최종 리스크 조정 점수 + 리뷰 큐 |

### KBO 적응 실패 예측 모델 분석

- 사용 모델: Ridge Logistic Regression, Balanced Ridge Logit, Shallow Random Forest (N≥24), HistGradientBoosting (N≥30)
- 검증: 시간 순방향 홀드아웃 + 반복 층화 교차검증 (3-fold × 30회 = 90 폴드)
- 현황: 타자 42행(성공 23/실패 17), 투수 86행(성공 46/실패 37) — G4 실질 통과

### 게이트 현황

G1~G5 실질적 통과 상태. G6만 정책적 LOCK 유지 중.
`ssg_risk_adjusted_fit_queue_v0_1.csv`에 타자 736명·투수 1,009명 스코어링 완료.

---

## 2. 1차 필터링 결과 (모델 기준)

`lane_2_deep_review_candidate_locked` + `stable_top25_locked` 조건 적용.

- 외국인 타자: 736명 → **22명**
- 외국인 투수: 1,009명 → **23명**

---

## 3. 추가 판단 기준 적용 (수정 필터링)

모델이 반영하지 못한 다음 두 가지 기준을 추가했다.

### 타자 추가 기준

| 기준 | 이유 |
|---|---|
| **좌타/스위치 우선** | SSG 선발진 우투 비율이 높으면 좌타자가 유리 |
| **`break_off_xwoba` + `low_velo_xwoba` 0.20 이상** | KBO 투수는 MLB보다 변화구·저속 의존도가 높음. 이 지표가 낮으면 KBO 적응 실패 위험 |
| **K% 기준 완화 (MLB → KBO 번역 고려)** | KBO는 MLB보다 투구 수준이 낮아 K%가 자연 감소하는 경향이 있음. 단순 패널티 대신 구종별 xwOBA로 약점 유형 구분 |

### 투수 추가 기준

| 기준 | 이유 |
|---|---|
| **BB9 ≤ 3.5 (기존 기준보다 타이트)** | KBO는 스트라이크존이 좁고 ABS 도입 이후 zone 판정이 엄격해져 MLB 대비 BB9 번역이 불리함 |
| **`third_time_woba_allowed` 낮을수록 우선** | KBO 선발은 5~6이닝 책임이 기본. 같은 타자를 여러 번 만나는 상황에서 약해지는 투수는 위험 |

---

## 4. 수정 후 최종 후보 리스트

### 외국인 타자 (수정 후)

| 순위 | 선수 | 소속 | 타석 | wOBA | break_off_xwoba | low_velo_xwoba | K% | 계약 상태 | 변경 사유 |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **Trey Mancini** | LAA | 우타 | .386 | **0.539** | **0.419** | 14.3% | DFA (즉시) | 유지 — 변화구·저속 대응 22명 중 압도적 1위 |
| **2** | **Dominic Fletcher** | PIT | 좌타 | .310 | 0.280 | 0.274 | 5.9% | 40인 외 | 유지 — 좌타 가산점, 구종별 xwOBA 안정적 |
| **3** | **Nolan Jones** | CLE | 좌타 | .278 | 0.361 | 0.344 | 28.0% | 40인 외 | **상승** (5위→3위) — 좌타 + 변화구·저속 대응 우수, BB% 9.7% |
| **4** | **Abraham Toro** | KC | 스위치 | .305 | 0.305 | 0.318 | 14.8% | 40인 외 | 유지 — 스위치히터 가산점 |
| **5** | **Luis Rengifo** | MIL | 스위치 | .283 | 0.319 | 0.318 | 17.0% | DFA (즉시) | **신규** — 스위치 + 즉시 접근 가능 |

**순위 변동 요약:**
- **Carter Kieboom 제외** (기존 3위 → 탈락): `break_off_xwoba=0.058`, `low_velo_xwoba=0.053`으로 KBO 변화구·저속 대응 능력 최하위. 구종별 약점이 뚜렷해 KBO 적응 실패 위험 높음
- **Omar Martinez 제외** (기존 4위 → 탈락): K%=33.3%가 KBO 번역 후에도 여전히 문제가 될 가능성이 높고 `break_off_xwoba` 데이터 미확인
- **Nolan Jones 상승** (5위→3위): 좌타 가산점 + 변화구·저속 xwOBA 모두 0.34 이상으로 KBO 환경 적합성 높음
- **Luis Rengifo 신규 진입**: 스위치히터 + DFA 즉시 접근 + 구종별 xwOBA 고른 분포

---

### 외국인 투수 (수정 후)

BB9 > 3.5 제외, `third_time_woba_allowed` 반영.

| 순위 | 선수 | 소속 | 2026 AAA IP | K9 | BB9 | HR9 | third_time_woba | 계약 상태 | 변경 사유 |
|---|---|---|---|---|---|---|---|---|---|
| **1** | **Josh Fleming** | TOR | 53.0 | 7.5 | **1.4** | 0.51 | 데이터 없음 | 40인 외 | 유지 — 커맨드·이닝 압도적 1위 |
| **2** | **Ian Hamilton** | ATL | 19.7 | **11.4** | 1.8 | 0.92 | 데이터 없음 | 40인 외 | 유지 — 탈삼진 최고, 커맨드 양호 |
| **3** | **Noah Murdock** | PIT | 23.0 | 10.6 | 2.3 | **0.39** | 데이터 없음 | 40인 외 | **신규** — HR9 최저, BB9 안정적 |
| **4** | **Jhonathan Díaz** | SEA | 60.3 | 7.2 | 3.1 | 1.34 | **0.225** | 40인 외 | **신규** — 3차전 wOBA 전체 1위, 이닝 많음 |
| **5** | **Matt Bowman** | TOR | 25.0 | 10.8 | 2.9 | 0.72 | 데이터 없음 | 40인 외 | **신규** — K9 높음, BB9 양호 |

**순위 변동 요약:**
- **Scott Blewett 제외** (기존 5위 → 탈락): BB9=3.93으로 BB9 ≤ 3.5 기준 미달
- **Shaun Anderson 제외** (기존 4위 → 탈락): BB9=3.95로 기준 미달. DFA 접근성은 좋으나 커맨드 불안
- **Noah Murdock 신규 3위**: BB9=2.35 + HR9=0.39로 피장타 억제 능력 전체 최고 수준
- **Jhonathan Díaz 신규 4위**: `third_time_woba_allowed=0.225`로 3차전 맞대결 강점 데이터 있는 선수 중 압도적 1위. 이닝(60.3)도 많음. HR9=1.34가 유일한 약점

---

## 5. 즉시 접촉 권장 (DFA/방출 상태)

```
타자: Trey Mancini (LAA DFA), Luis Rengifo (MIL DFA) → 지금 당장 가능
투수: 없음 (BB9 3.5 이하 선수 중 DFA 없음)
```

---

## 6. 다음 단계

1. **Trey Mancini / Luis Rengifo** DFA 클레임 또는 직접 영입 협상 즉시 시작
2. **Josh Fleming** — 현재 TOR 40인 외, 방출 타이밍 확인
3. **Jhonathan Díaz** — `third_time_woba` 추가 검증 후 접촉 검토
4. 각 선수 에이전트 확인 및 KBO 의향 타진
5. 현재 부상 상태 최신 확인 (특히 Díaz HR9=1.34 최근 원인 파악)
