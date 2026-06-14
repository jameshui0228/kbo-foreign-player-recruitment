# Message Discovery Protocol

업데이트: 2026-06-11 KST

## Principle

프로젝트 메시지는 사람이 먼저 고르지 않는다. 메시지는 세 종류의 증거가 같은 방향을 가리킬 때만 채택한다.

1. SSG 정량 데이터에서 반복되는 결핍 또는 비효율
2. 뉴스/기사/인터뷰 텍스트에서 반복되는 니즈 신호
3. 후보군 데이터에서 그 결핍을 메울 수 있는 비전형적 스킬 신호

이 셋 중 하나만 있으면 메시지가 아니라 가설이다.

## Current Text Corpus

Naver Search News API로 인터뷰에 한정하지 않고 SSG 관련 뉴스/기사 메타데이터를 넓게 수집했다.

- collection script: `src/data/collect_naver_news.py`
- tag script: `src/features/build_text_need_signals.py`
- raw jsonl: `data/raw/articles/naver_news/ssg_need_news_raw.jsonl`
- metadata csv: `data/raw/articles/naver_news/ssg_need_news_metadata.csv`
- relevance-labeled csv: `outputs/tables/ssg_news_need_relevance_labeled.csv`
- tag summary: `outputs/tables/ssg_news_need_tag_summary.csv`
- keyword summary: `outputs/tables/ssg_news_need_keyword_summary.csv`
- message candidates: `outputs/tables/ssg_message_candidates_from_text.csv`

수집 결과:

| scope | records |
|---|---:|
| broad recall set | 7,884 |
| strict SSG/랜더스 snippet set | 7,630 |
| high-value SSG + 외국인/타자/외야/타선 context set | 5,378 |

Naver API는 기사 본문 전문이 아니라 제목, 요약, 링크, 날짜를 제공한다. 따라서 현재 corpus는 본문 의미 분석이 아니라 기사/인터뷰 신호 발견용이다.

## First Text Signals

Strict SSG/랜더스 snippet set 기준 첫 신호는 다음과 같다.

| signal | article_count | interpretation |
|---|---:|---|
| `power` | 2,358 | 장타/홈런 언급이 반복된다. |
| `injury_depth` | 1,692 | 부상/공백/뎁스 맥락이 반복된다. |
| `run_creation` | 1,611 | 타선/득점권/해결사 언급이 반복된다. |
| `onbase_discipline` | 1,192 | 출루/선구안/존/삼진 맥락이 반복된다. |
| `foreign_hitter` | 1,155 | 외국인 타자/교체 맥락이 반복된다. |
| `outfield` | 988 | 외야 포지션 언급이 반복된다. |

이 표는 결론이 아니다. 다음 단계에서 STATIZ/Savant로 교차검증해야 하는 후보 메시지 목록이다.

## Promotion Rule

텍스트 신호가 최종 발표 메시지로 승격되려면 다음을 통과해야 한다.

| check | requirement |
|---|---|
| Quant check | STATIZ에서 같은 방향의 SSG 결핍/비효율이 확인된다. |
| Candidate check | Savant 후보군에서 그 결핍을 메울 수 있는 선수가 존재한다. |
| Uniqueness check | 단순 OPS/HR 상위가 아니라 SSG 맥락에서만 더 가치 있는 설명이 가능하다. |
| Robustness check | 특정 기사 몇 개나 특정 시즌 한 해에만 의존하지 않는다. |
| Counterexample check | 반대 지표가 있으면 같이 설명한다. |

## Current Leading Hypothesis To Test

현재 텍스트에서는 `power`, `run_creation`, `foreign_hitter`, `outfield`가 동시에 강하다. STATIZ 첫 진단에서는 SSG 외야가 홈런/ISO는 강하지만 wRC+와 OPS는 중위권으로 나타났다.

따라서 다음 검증 질문은 다음이다.

> SSG 외야의 진짜 문제는 장타 부족인가, 아니면 장타가 출루/득점 생산성으로 번역되지 않는 구조인가?

이 질문이 검증되기 전까지는 발표 메시지를 확정하지 않는다.
