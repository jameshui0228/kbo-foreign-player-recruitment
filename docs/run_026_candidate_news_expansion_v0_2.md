# Run 026 Candidate News Expansion v0.2

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run expands candidate-specific news metadata from the Run 025 pilot, but it does not create a final ranking, shortlist, recommendation label, or candidate-name release.

## Purpose

Run 025 proved the article-metadata workflow on a 26-candidate pilot. Run 026 expands the same workflow to the full high-priority market-realism review queue:

> Can public English news metadata attach medical, contract, market-access, and Korea/overseas context to enough candidates to support a realistic scouting worklist?

This is not a replacement for scouting reports. It is a scalable screening layer that tells us where manual review should spend time first.

## Source Strategy

| source lane | status | note |
|---|---|---|
| English news | collected | Google News RSS; no Google API key required |
| Korean news | skipped | Naver credentials were not loaded in the shell environment |
| Google API | not needed | optional later for quota-controlled search, not required for this run |
| Full article text | not collected | metadata only: title, description, date, source, link |

## Expanded Scope

The run expands from 26 pilot candidates to 200 market-realism priority candidates.

| slot | rows |
|---|---:|
| Foreign hitter | 16 |
| Foreign pitcher | 30 |
| Asian quota | 154 |
| Total | 200 |

The scope uses Run 024 market-realism priority:

- MLB hitter/pitcher rows with `manual_contact_priority_locked`;
- Asian-quota rows with `buyout_salary_agent_check_needed`.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/candidate_news_scope_v0_2.csv` | 200 | expanded candidate news scope |
| `data/raw/articles/candidate_news_expanded_v0_2/candidate_news_metadata.csv` | 613 | raw article metadata, local ignored raw data |
| `outputs/tables/candidate_news_collection_audit_v0_2.csv` | 600 | provider/query audit, including Naver skipped status |
| `outputs/tables/candidate_news_article_relevance_v0_2.csv` | 613 | article-level tag/relevance table |
| `outputs/tables/candidate_news_signal_summary_v0_2.csv` | 200 | candidate-level news signal summary |
| `outputs/tables/candidate_news_slot_summary_v0_2.csv` | 10 | slot/status summary |
| `outputs/tables/ssg_market_realism_news_join_v0_2.csv` | 2,723 | Run 024 manual worklist with expanded news signals attached |

## Collection Result

| metric | value |
|---|---:|
| scoped candidates | 200 |
| article metadata rows | 613 |
| candidate-name matched rows | 339 |
| usable news-signal rows | 340 |
| usable English article rows | 340 |
| usable Korean article rows | 0 |
| Naver status | skipped, missing shell env |
| Google API needed | no |

## Candidate-News Status

| slot | news status | candidates | usable articles |
|---|---|---:|---:|
| Asian quota | no candidate-specific news found | 138 | 0 |
| Asian quota | medical news review needed | 11 | 25 |
| Asian quota | candidate news review available | 2 | 2 |
| Asian quota | Korea/overseas context found | 1 | 2 |
| Asian quota | market/contract news review needed | 1 | 3 |
| Foreign hitter | medical news review needed | 13 | 105 |
| Foreign hitter | market/contract news review needed | 3 | 20 |
| Foreign pitcher | medical news review needed | 19 | 142 |
| Foreign pitcher | no candidate-specific news found | 6 | 0 |
| Foreign pitcher | market/contract news review needed | 5 | 41 |

## Signal Counts

| signal | usable article rows |
|---|---:|
| injury/medical | 87 |
| contract/market | 167 |
| Korea/overseas context | 15 |

The tagger uses only article title and description, not the search query, so an `injury` query does not automatically become an injury signal.

## Interpretation

The expanded run gives a more realistic market-screening layer:

- Foreign hitter and foreign pitcher pools are reasonably covered by English public news metadata for medical and contract-market screening.
- Asian-quota rows remain under-covered by English Google News RSS. A missing English news signal should not be treated as low risk for Asian-quota candidates.
- The next material data gain is Korean/Naver news plus local Asian-league salary, posting, buyout, transfer-fee, and agent/willingness context.

## Gate Audit

Allowed:

- Use `v0_2` news tags as research-only manual-review context.
- Use `ssg_market_realism_news_join_v0_2.csv` as the expanded news-enriched work queue.

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

## Six-Layer Progress After Run 026

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | unchanged |
| 3 | Candidate market construction | 91% | 89% -> 91% |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 81% | 78% -> 81% |
| 6 | SSG fit ranking | 66% | 63% -> 66% |

Candidate release remains locked.

## Next Step

Load Naver credentials into the shell environment and run the same candidate-specific collection for Korean news. After that, add salary/contract/buyout/agent feasibility sources before any candidate can move from research inventory to shortlist.
