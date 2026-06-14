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

