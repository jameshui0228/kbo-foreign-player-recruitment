# SSG Landers Foreign Player Recruitment Project

고려대학교 스포츠 데이터 분석 학술 동아리 SDA 2기 프로젝트.

이 프로젝트의 목표는 2023년 이후 KBO/STATIZ, MLB/MiLB, NPB/CPBL, roster/transaction, public salary/contract/medical signal 데이터를 활용해 SSG 랜더스의 현재 전력 구조를 진단하고, SSG에 맞는 외국인 타자와 외국인 선발투수 후보군을 데이터 기반으로 제안하는 것이다.

- 외국인 타자 1명
- 외국인 선발투수 1명

최종 발표에서는 SSG의 `대체 외국인 타자`와 `대체 외국인 선발투수`를 우선 과제로 두었다. 최종 추천은 좋은 누적 성적을 가진 선수를 나열하는 방식이 아니라, SSG의 약점, KBO 번역 가능성, 시장 접근성, 비용/계약/메디컬 gate를 함께 통과하는 접촉 우선순위를 도출하는 방식으로 설계했다.

단순히 좋은 선수를 찾는 프로젝트가 아니다. 핵심 질문은 다음과 같다.

> KBO에 올 수 있을 정도의 결함은 있지만, 그 결함이 KBO와 SSG 환경에서는 감당 가능하거나 가려질 수 있는 선수는 누구인가?

따라서 이 프로젝트는 OPS 상위권, ERA 하위권 선수를 단순 나열하지 않는다. SSG 전력 구조, KBO/ABS 환경, MLB/MiLB 성적의 KBO 번역 가능성, 40-man/DFA/outright/계약 상태 안에서 "남들은 결함으로 보지만 SSG에서는 쓸모가 더 분명한 선수"를 찾는 것이 핵심 전략이다. 최종 후보 모델에는 기사/인터뷰 텍스트를 직접 feature로 넣지 않고, 숫자형 structured data와 roster/transaction/contract/medical signal만 사용했다.

## Final Status

발표와 최종 산출물 정리가 완료된 상태다. 현재 repo의 기준 결론은 다음과 같다.

- 외국인 타자 최종 접촉 1순위: **Will Brennan**
- 외국인 선발투수 최종 접촉 1순위: **Josh Fleming**
- 타자 Final Top 3: **Will Brennan, Dominic Fletcher, Dylan Carlson**
- 투수 Final Top 3: **Josh Fleming, Keegan Thompson, Kolby Allard**

최종 handoff 문서: `docs/final_project_handoff_2026_06_25.md`

최종 발표 자료:

- `reports/presentation/SSG_final_presentation_2026-06-24.pdf`
- `reports/presentation/SSG_final_script_2026-06-24.docx`

최종 보고서:

- `reports/ssg_overleaf_report_final.pdf`
- `output/pdf/SSG_발표_핵심_인사이트_치트시트.pdf`

## Quick Start For Collaborators

```bash
git clone <repo-url>
cd kbo-foreign-player-recruitment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에는 개인별 STATIZ/Naver API 키를 로컬에만 입력한다. 실제 키와 secret은 GitHub에 올리지 않는다.

협업 규칙은 `COLLABORATION.md`, PR 체크리스트는 `CONTRIBUTING.md`를 따른다.

분석 과정의 6개 layer 진행 기록은 `docs/six_layer_progress_board.md`와 `outputs/tables/six_layer_progress_v1.csv`에서 확인한다.

## Directory Map

```text
data/
  raw/
    kbo/
    mlb_milb/
    npb/
    articles/
    weather/
    park/
  interim/
  processed/
  schemas/
notebooks/
src/
  data/
  features/
  models/
  scouting/
  visualization/
  utils/
outputs/
  figures/
  tables/
  ppt_graphs/
  ppt_tables_png/
  reports/
docs/
reports/
  presentation/
  overleaf_ssg_recruitment/
  templates/
```

## Key Documents And Artifacts

- `docs/final_project_handoff_2026_06_25.md`: 팀원용 최종 산출물/데이터/모델 위치 안내
- `docs/unified_recommendation_model_structured_only_v2.md`: 숫자형 structured data 기반 통합 추천 모델
- `docs/realism_first_candidate_board_v3.md`: 현실성 gate 반영 후보 보드
- `docs/candidate_board_execution_v4.md`: 최종 실행 후보 보드와 gate 결과
- `docs/evidence_based_kbo_translation_coefficients_v2.md`: KBO translation 단순 환산 계수와 해석
- `docs/final_candidate_validation_audit_v2.md`: 최종 후보 검증 감사
- `docs/model_probability_calibration_audit_v1.md`: 모델 확률/과신/누수 가능성 점검
- `reports/overleaf_ssg_recruitment/main.tex`: Overleaf 형식 최종 보고서 원문
- `reports/presentation/`: 최종 발표 PDF와 대본
- `outputs/tables/final_candidate_board_execution_v4.csv`: 최종 후보 board
- `outputs/tables/unified_foreign_recommendations_top3_structured_only_v2.csv`: 통합 모델 Top 3
- `outputs/ppt_graphs/`, `outputs/ppt_tables_png/`: 발표 삽입용 그래프/표 PNG
- `notebooks/11_layer_01_ssg_hidden_weakness_mining.ipynb` ~ `notebooks/17_unified_recommendation_model_structured_only_v2.ipynb`: 학부생 설명용 layer별 notebook
- `docs/initial_project_plan.md`: 초기 전체 설계 문서
- `docs/source_log.md`: 데이터 출처, 접근 방식, 한계, 사용 목적
- `docs/data_manifest_for_teammates.md`: 팀원용 전체 데이터 파일 manifest 요약
- `docs/data_dictionary.md`: 최소 데이터셋 스키마
- `docs/methodology.md`: 점수 체계, validation, leakage 방지 원칙
- `docs/literature_log.md`: feature engineering 근거용 논문 로그
- `docs/assumptions.md`: 현재 단계의 가정과 프록시 변수
- `docs/experiment_log.md`: 실험/의사결정 로그

전체 local data/output 파일 목록은 `outputs/tables/project_data_file_manifest_v1.csv`에서 확인한다.

## Reproducibility Rules

- 모든 raw 데이터는 `data/raw/{domain}/`에 저장한다.
- 가공 중간 산출물은 `data/interim/`, 모델 입력은 `data/processed/`에 저장한다.
- `data/raw/`, `data/interim/`, `data/processed/`는 GitHub에 commit하지 않는다.
- 데이터 출처, 접근일, 수집 방식, 라이선스/약관 주의사항은 `docs/source_log.md`에 기록한다.
- KBO 입단 후 성적은 historical transfer backtest의 target/label로만 사용하고, 입단 전 ranking feature로 사용하지 않는다.
- 후보 추천 시 `skill`, `SSG fit`, `KBO translation`, `availability`, `risk`를 함께 제시한다.
- 최종 발표 모델에는 기사/인터뷰 텍스트를 직접 feature로 넣지 않는다. 기사/뉴스 수집물은 시장/메디컬/계약 확인용 보조 로그로만 보관한다.
