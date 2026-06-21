# Run 025 Candidate News Pilot v0.1

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run collects candidate-specific news metadata for a small market-realism pilot, but it does not create a final ranking, shortlist, or recommendation.

## Purpose

Run 024 built the market-realism queue. Run 025 starts the next slow layer:

> Do public news signals confirm contract, injury, adaptation, or Korea/overseas context for the highest-priority manual-check candidates?

This matters because a candidate can look good in Statcast/MiLB/market data and still be unusable because of medical, contract, willingness, or role-fit context.

## Source Strategy

| source lane | status | note |
|---|---|---|
| English news | collected | Google News RSS, no Google API key required for this pilot |
| Korean news | skipped | Naver credentials were not loaded in the shell environment |
| Google API | not needed yet | useful later only if we want stable large-scale search with quota/control |
| Full article text | not collected | metadata only: title, description, date, source, link |

## Pilot Scope

The first pass intentionally stayed small:

| slot | pilot rows |
|---|---:|
| Foreign hitter | 8 |
| Foreign pitcher | 8 |
| Asian quota | 10 |
| Total | 26 |

The scope uses Run 024 market-realism priority:

- MLB hitter/pitcher rows with `manual_contact_priority_locked`;
- top Asian-quota rows with `buyout_salary_agent_check_needed`.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/candidate_news_pilot_scope_v0_1.csv` | 26 | pilot candidates selected from Run 024 manual queue |
| `data/raw/articles/candidate_news_pilot_v0_1/candidate_news_metadata.csv` | 182 | raw candidate-specific news metadata |
| `outputs/tables/candidate_news_collection_audit_v0_1.csv` | 78 | provider/query audit, including Naver skipped status |
| `outputs/tables/candidate_news_article_relevance_v0_1.csv` | 182 | article-level tag/relevance table |
| `outputs/tables/candidate_news_signal_summary_v0_1.csv` | 26 | candidate-level news signal summary |
| `outputs/tables/candidate_news_slot_summary_v0_1.csv` | 7 | slot/status summary |
| `outputs/tables/ssg_market_realism_news_join_v0_1.csv` | 2,723 | Run 024 manual worklist with pilot news signals attached |

## Collection Result

| metric | value |
|---|---:|
| pilot candidates | 26 |
| article metadata rows | 182 |
| candidate-name matched rows | 118 |
| usable news-signal rows | 119 |
| Naver status | skipped, missing shell env |
| Google API needed | no |

## Candidate-News Status

| slot | news status | candidates | usable articles |
|---|---|---:|---:|
| Asian quota | no candidate-specific news found | 7 | 0 |
| Asian quota | medical news review needed | 2 | 9 |
| Asian quota | candidate news review available | 1 | 1 |
| Foreign hitter | medical news review needed | 6 | 47 |
| Foreign hitter | market/contract news review needed | 2 | 14 |
| Foreign pitcher | medical news review needed | 7 | 48 |
| Foreign pitcher | no candidate-specific news found | 1 | 0 |

## Signal Counts

| signal | usable article rows |
|---|---:|
| injury/medical | 34 |
| contract/market | 61 |
| Korea/overseas context | 1 |

The tagger uses only article title and description, not the search query, so an `injury` query does not automatically become an injury signal.

## Interpretation

The pilot shows that English news metadata can materially improve the market-realism queue:

- MLB manual-contact candidates often have contract and medical context in public news.
- Asian-quota candidates, especially CPBL rows, are not well-covered by English Google News RSS alone.
- Korean/Naver and possibly local Asian-league sources are necessary before treating Asian-quota news gaps as true absence of risk.

## Gate Audit

Allowed:

- Use candidate news tags as research-only risk context.
- Use `ssg_market_realism_news_join_v0_1.csv` as the next manual-review queue.

Not allowed:

- No final shortlist.
- No recommendation labels.
- No candidate-name release.
- No score release.

Every joined row remains locked:

- `is_final_recommendation = False`
- `shortlist_label_allowed = False`
- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `candidate_news_score_release_allowed = False`

## Six-Layer Progress After Run 025

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | unchanged |
| 3 | Candidate market construction | 89% | 88% -> 89% |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 78% | 76% -> 78% |
| 6 | SSG fit ranking | 63% | 60% -> 63% |

Candidate release remains locked.

## Next Step

Run 026 should load Naver credentials into the shell environment and repeat the same pilot for Korean candidate-specific news.

Google Custom Search API is optional later, not required for the current English-news workflow.
