# Assumptions

접근일: 2026-06-11 KST

## Current Assumptions

1. 이 프로젝트는 공개 데이터만 사용한다.
2. STATIZ, FanGraphs, Baseball Savant, KBO/NPB official, MyKBO, ProEyeKyuu, YakyuCosmo 등은 실제 수집 전 약관과 다운로드 가능성을 확인한다.
3. 수집 불가능하거나 유료인 데이터는 무단 사용하지 않고 proxy 변수를 만든다.
4. KBO 입단 후 성적은 historical transfer backtest의 label로만 사용한다.
5. 선수 추천은 최신 로스터/계약/부상/40-man 여부 확인 전에는 진행하지 않는다.
6. 아시아쿼터 불펜은 표본이 작을 수 있으므로 NPB 2군/독립리그/CPBL/ABL 기록과 KBO 외국인 불펜 사례를 proxy로 사용할 수 있다.
7. 문학 구장 치수는 현재 2차 출처에서 LF/RF 95m, CF 120m, wall 2.8m로 확인했으나 공식 자료로 교차검증한다.
8. 청라 돔구장은 단기 대체 외국인 영입에는 보조 변수로만 사용한다.

## Proxy Principles

- proxy는 실제 변수를 대체하는 임시 가정이므로 변수명과 한계를 문서화한다.
- proxy가 최종 순위에 큰 영향을 주면 ablation으로 민감도를 확인한다.
- 기사/인터뷰는 정량 지표가 아니라 SSG의 공개적 니즈를 확인하는 보조 근거로 사용한다.

---

## 1단계 추가 가정 (src/scouting/ssg_weakness.py, 2026-06-22)

9. **파크팩터 프록시**: STATIZ API 스냅샷에 문학 구장 공식 파크팩터 수치가 없다. 홈/원정 OPS 격차(`home_away` context_family)를 임시 프록시로 사용한다. SSG 2026 홈-원정 OPS 격차 +0.035. 공식 파크팩터 수치 확보 시 대체한다.

10. **문학 구장 치수**: LF/RF 95m, LCF/RCF 115m, CF 120m, 담장 2.8m는 Wikipedia 2차 출처 기준(`source_log.md: ssg_field_dims_secondary`). 공식 자료 교차검증 전까지 방향성 판단에만 사용한다.

11. **상황별 약점 샘플 크기**: 2026 시즌은 2026-06-11 기준 61~63경기 진행 중이다. 만루, 3B_0S 등 특수 상황은 PA 수가 적어 OPS 추정이 불안정하다. 이 상황들은 보조 근거로만 사용하고, 핵심 약점 판단은 PA가 충분한 컨텍스트(전체/RISP/주자 상황) 중심으로 한다.

12. **runner_advancement_proxy**: "1루 주자만" OPS(SSG 리그 10위)를 주자 진루 능력 결핍 지표로 사용한다. 실제로는 번트 성공률, 진루 타격 성공률이 필요하나 현재 스냅샷에 없어 OPS를 대리 지표로 쓴다.

13. **two_out_contact_proxy**: 2사 OPS(SSG 리그 8위)를 chase_pct/zone_contact_pct의 proxy로 해석한다. 후보 평가 단계(3단계)에서 Statcast 수치로 대체한다.

14. **early_inning_support**: 초반(1~3이닝) OPS 리그 8위를 상대 선발투수 공략력 부재로 해석한다. 선발투수 확보 우선도를 높이는 보조 근거로 활용한다.

---

## 3단계 추가 가정 (src/scouting/candidate_market.py, 2026-06-22)

15. **AAA OPS proxy → KBO wRC+ 변환**: AAA OPS ≥ 0.780을 KBO 솔리드급(wRC+ 108+) 도달 가능성의 사전 필터로 사용한다. 리그 인플레이션 보정 없이 raw OPS를 쓰므로 과잉 선발 위험이 있다. 4단계 번역 모델(league factor 적용)로 보정한다.

16. **AAA ERA proxy → KBO ERA 변환**: AAA ERA ≤ 4.80을 KBO 고려 선발 최저 기준으로 설정한다. PCL(태평양 연안 리그) 등 타자 유리 구장이 포함된 팀은 ERA가 부풀려지므로 팀 파크팩터로 보정 필요(4단계). 현재는 raw 값만 사용한다.

17. **가용성 판단 기준**: 2025-10-01~2026-06-13 트랜잭션 중 DFA, Released, Declared Free Agency, Outrighted로 분류된 선수를 "획득 가능"으로 간주한다. 단, 이미 다른 팀과 계약을 맺었을 수 있으며 이 스크립트는 최신 계약 상태를 추적하지 못한다. 선수 확정 전 에이전트/KBO 규정 확인 필수.

18. **SSG Fit 점수 proxy**: 3단계 fit 점수는 1단계 약점(runner_advancement, early_inning, two_out_contact, abs_discipline)의 pre-arrival proxy 측정값이다. Statcast xwOBA/whiff% 등을 Savant에서 합칠 경우 MLB 출장 기록이 있는 선수에게만 적용된다. MiLB 전용 선수는 Savant 컬럼이 NULL로 남는다.

19. **Inning-eating proxy**: AAA GS/GP 비율 ≥ 0.30을 선발 역할 확인 기준으로 사용한다. GP에 등판 없이 명단만 올라있는 경우(부상 복귀 전 등)는 오탐 가능. 상위 후보는 개인 기록을 수동 확인한다.

20. **PCL 인플레이션 플래그**: Albuquerque, El Paso, Salt Lake, Reno, Sugar Land, Las Vegas, Round Rock 소속 선수는 `pcl_inflated=True`로 마킹한다. PCL 구장은 고도·기후로 OPS +0.050~+0.100 인플레이션이 추정된다. 4단계 번역 모델에서 park factor(추정 PF ~1.06~1.10)를 적용해 보정한다. raw OPS를 직접 KBO 예측에 사용하면 안 된다.

21. **Savant xwOBA/whiff% 활용 범위**: Savant Statcast 데이터는 MLB 경기 기반이므로, 이 연구 풀에서 Savant 매칭이 되는 선수는 MLB 출장 기록이 있는 선수다. MiLB-only 선수는 Savant 컬럼이 NULL로 남으며 `fit_savant_bonus=0` 처리된다. Savant 미보유 선수가 불이익을 받지 않도록, savant_bonus는 보조 지표(최대 10pt)로만 사용한다.

22. **Acquisition tier 분류 기준**: KBO 영입 현실성을 5등급으로 분류한다.
    - `A_mlb_reject`: DFA/Released + Savant 피치 500구 이상 → MLB 실패가 확인된 선수. 핵심 타깃.
    - `A_dfa_milb`: DFA/Released + MLB 경험 미미 → MiLB가 한계 ceiling, KBO가 적합한 시장.
    - `B_fa_veteran/mid`: 자유계약, 나이 25+ → 협상 가능, FA 에이전트 접촉 가능.
    - `C_outrighted`: Outrighted → 40인 로스터 제외됐지만 소속 조직 옵션 가능, 협상 복잡.
    - `D_*`: 프로스펙트, 40인 잔류, 포지션 부적합, 한국 국적 → 영입 불가 또는 비현실적.

23. **KBO 외국인 자격 불가**: KBO 규정상 한국 국적 선수는 외국인 선수 등록 불가다. birth_country가 'Republic of Korea', 'South Korea', 'Korea'로 표기된 선수는 `D_kbo_ineligible`로 분류한다. (Ji Hwan Bae 등 해당)

24. **포지션 필터**: SSG 외국인 타자 포지션은 외야(LF/CF/RF), 코너 내야(1B/3B), DH에 한정한다. C(포수), 2B(2루수), SS(유격수)는 KBO에서 외국인 배치가 없으므로 `D_wrong_position`으로 제외한다.

25. **SSG 약점 보완 점수 재설계 (2026-06-23)**: 스코어 함수를 "좋은 선수 일반 지표" → "SSG 특정 약점 대응 + KBO 내성 결함" 기반으로 재설계했다.
    - 타자 S1(runner_advancement): SSG "1루주자" OPS 10위 보완 = ISO + BB% + hard_hit_pct
    - 타자 S2(two_out_abs_discipline): SSG "2사" OPS 8위 + ABS 적응 = chase_pct + whiff_pct + BB%
    - 타자 S3(early_inning_pressure): SSG "초반" OPS 8위 보완 = xwOBA(park-neutral) + OPS
    - 타자 S4(kbo_masked_flaw): MLB 실패 원인이 KBO에서 완화되는 케이스 보너스
      - 케이스 A: K% 24-32% + xwOBA ≥ 0.380 → KBO 투수 수준↓로 K% 자연 감소
      - 케이스 B: 낮은 avg + 높은 ISO → DH 기용으로 수비 약점 무관
      - 케이스 C: PCL 인플레이션 + park-neutral xwOBA 양호 → 실제 파워 존재
    - 선발 P1(early_inning_support): SSG 초반 OPS 8위 → 선발이 초반 장악 필요 = ERA + WHIP
    - 선발 P2(inning_depth): SSG 불펜 보호 = IP/GS + GS비율
    - 선발 P3(contact_management): KBO 타자 특성 대응 = BB9 + K9 + whiff%
    - 선발 P4(kbo_masked_flaw): 저구속(89-92) + 좋은 커맨드 → KBO 평균구속↓ 환경 생존 가능

