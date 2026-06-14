# SSG Landers Foreign Player Recruitment Project

고려대학교 스포츠 데이터 분석 학술 동아리 SDA 2기 프로젝트.

이 프로젝트의 목표는 2023년 이후 KBO, MLB/MiLB, NPB 및 공개 기사 데이터를 활용해 SSG 랜더스의 현재 전력 구조를 진단하고, SSG에 맞는 다음 영입 후보군을 데이터 기반으로 제안하는 것이다.

- 외국인 타자 1명
- 외국인 선발투수 1명
- 아시아쿼터 불펜투수 1명

2026-06-11 현재 1차 우선순위는 `대체 외국인 선수`, 그중에서도 `외야수 외국인 타자`다. 선발투수와 아시아쿼터 불펜은 최종 산출물에는 포함하되, 데이터 분석의 첫 번째 승부처는 SSG에 특화된 외야수 타자 발굴로 둔다.

단순히 좋은 선수를 찾는 프로젝트가 아니다. 핵심 질문은 다음과 같다.

> KBO에 올 수 있을 정도의 결함은 있지만, 그 결함이 KBO와 SSG 환경에서는 감당 가능하거나 가려질 수 있는 선수는 누구인가?

따라서 이 프로젝트는 OPS 상위권 선수를 나열하지 않는다. SSG 전력, 문학 구장, KBO 투구 생태계, ABS, 기사/인터뷰 텍스트, 날씨/피로 맥락 안에서 "남들은 단점으로 버리지만 SSG에서는 장점이 더 크게 살아나는 선수"를 찾는 것이 핵심 전략이다.

## Current Phase

현재 단계는 추천 전 사전 설계 단계다.

1. 문제 정의
2. 데이터 소스 감사
3. 최소 데이터셋 스키마 설계
4. success metric 초안 설계
5. feature hypothesis 설계
6. 검증 및 랭킹 로드맵 설계

선수 추천은 최신 로스터, 계약, 부상, 40-man 여부, 최근 성적을 확인한 뒤 진행한다.

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

현재 진행률은 `docs/six_layer_progress_board.md`와 `outputs/tables/six_layer_progress_v1.csv`를 기준으로 확인한다.

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
  candidates/
  reports/
docs/
reports/
  templates/
```

## Key Documents

- `docs/initial_project_plan.md`: 첫 단계 전체 설계 문서
- `docs/source_log.md`: 데이터 출처, 접근 방식, 한계, 사용 목적
- `docs/data_manifest_for_teammates.md`: 팀원용 전체 데이터 파일 manifest 요약
- `docs/data_dictionary.md`: 최소 데이터셋 스키마
- `docs/methodology.md`: 점수 체계, validation, leakage 방지
- `docs/strategy_replacement_outfielder.md`: 1차 우선순위인 대체 외국인 외야수 전략
- `docs/message_discovery_protocol.md`: 데이터/기사/후보군에서 메시지를 발견하는 절차
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
