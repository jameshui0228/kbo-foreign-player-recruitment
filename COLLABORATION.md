# Collaboration Guide

이 문서는 SDA 2기 SSG 외인/아시아쿼터 영입 프로젝트를 GitHub에서 같이 작업하기 위한 운영 규칙입니다.

## What Is Tracked

GitHub에 올리는 것:

- `src/`: 수집, feature engineering, modeling scripts
- `notebooks/`: 분석 notebook skeleton and experiments
- `docs/`: 방법론, 실험 로그, 진행률, 발표용 근거 문서
- `outputs/tables/`: 재현성과 논의에 필요한 핵심 결과 테이블
- `data/schemas/`: candidate scoring schema and table definitions

GitHub에 올리지 않는 것:

- `data/raw/`: 원천 데이터와 API 응답
- `data/external/`: 논문 PDF, 위키 HTML 등 외부 원문 자료
- `data/interim/`: 중간 가공물
- `data/processed/`: 대용량 parquet/processed data
- `.env`: 개인 API 키와 secret

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에는 각자 본인의 로컬 키를 넣습니다. 실제 키는 GitHub에 올리지 않습니다.

## Current Project Status

진행 상황은 아래 파일을 기준으로 봅니다.

- `docs/six_layer_progress_board.md`
- `outputs/tables/six_layer_progress_v1.csv`
- `docs/experiment_log.md`
- `experiments.csv`

현재 최종 후보명은 잠금 상태입니다. 후보 이름은 `research_lead` 수준으로만 다루고, 추천/shortlist는 1-6번 게이트가 더 통과한 뒤에만 사용합니다.

## Branch Workflow

`main`은 공유 가능한 기준 상태로 유지합니다.

작업 브랜치 이름:

```text
feature/{topic}
analysis/{layer-number}-{topic}
fix/{topic}
docs/{topic}
```

예시:

```text
analysis/layer2-foreign-archetypes
analysis/layer3-market-feasibility
docs/team-summary
```

## Pull Request Rules

PR에는 반드시 아래 내용을 적습니다.

- 어떤 layer를 건드렸는지
- 새로 만든/수정한 파일
- 사용한 데이터 소스
- 검증 방법
- 후보 추천 잠금 여부에 영향이 있는지

분석 결과가 바뀌면 다음 파일도 같이 업데이트합니다.

- `docs/experiment_log.md`
- `experiments.csv`
- `docs/six_layer_progress_board.md`
- `outputs/tables/six_layer_progress_v1.csv`

## Data Policy

원천 데이터는 repo 밖에서 관리합니다.

새 데이터를 수집하면:

1. `data/raw/...`에 저장합니다.
2. Git에는 올리지 않습니다.
3. `docs/source_log.md`에 출처, 접근일, 수집 방식, 제한사항을 기록합니다.
4. 분석에 필요한 요약 결과만 `outputs/tables/`에 남깁니다.

민감정보와 API 키는 절대 commit하지 않습니다.

팀원들이 사용 데이터 목록을 확인할 때는 아래 파일을 봅니다.

- `docs/data_manifest_for_teammates.md`
- `outputs/tables/project_data_file_manifest_v1.csv`

원천 파일 자체가 필요한 경우 public GitHub에 직접 올리기보다 Google Drive, GitHub Release, Git LFS, 또는 각자 재수집 스크립트를 사용합니다.

## Six-Layer Progress Contract

모든 주요 업데이트는 아래 6단계 진행률을 같이 보고합니다.

1. SSG 숨은 약점 마이닝
2. KBO 외인 성공/실패 유형 마이닝
3. 후보 시장 구축
4. KBO 번역 모델
5. 실패 리스크 모델
6. SSG fit ranking

후보 이름을 공개 추천으로 전환하려면 `docs/candidate_release_gates_v1.md`의 조건을 통과해야 합니다.
