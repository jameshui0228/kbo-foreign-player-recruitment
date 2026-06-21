# Run 027 Korean-News Fallback And Manual Feasibility Worklist v0.1

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run does not create a final ranking, shortlist, recommendation label, candidate-name release, or score release.

## Purpose

Run 026 expanded English candidate-news metadata to 200 priority candidates. Run 027 tests whether a no-key Korean-news fallback can reduce the remaining Korean-source gap, then builds a manual feasibility worklist for the reality checks that still block candidate release.

The practical question:

> Before scouts or team members spend time on names, which candidates need Korean news, medical file, contract/salary, buyout, agent, or Korea-willingness verification first?

## Korean-News Fallback Test

Naver credentials were still not loaded in the shell environment. To avoid blocking, this run added and tested a no-key Korean-locale Google News RSS provider:

- provider: `google_news_rss_ko`
- locale: `hl=ko`, `gl=KR`, `ceid=KR:ko`
- scope: 62 priority candidates
- query mode: compact, 2 Korean-style queries per candidate

Result:

| metric | value |
|---|---:|
| priority candidates searched | 62 |
| Google KR RSS attempted queries | 124 |
| returned article rows | 0 |
| error rows | 124 |
| Naver status | skipped, missing shell env |
| usable Korean article rows added | 0 |

Spot check showed Google KR RSS returning HTTP 503 for at least one candidate query. Therefore, Google KR RSS should not be treated as a reliable Korean-news substitute.

Decision:

- Keep `google_news_rss_ko` support in the collector as an optional fallback.
- Do not rely on it for Korean candidate-news coverage.
- Treat Naver News API or local Korean/Asian-league source search as required for the next real data gain.

## Combined News Layer v0.3

The final v0.3 news layer combines:

- Run 026 English Google News RSS metadata;
- Run 027 Google KR RSS fallback audit, which added no usable articles.

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/candidate_news_scope_ko_v0_3.csv` | 62 | Korean fallback priority scope |
| `outputs/tables/candidate_news_collection_audit_ko_v0_3.csv` | 186 | Google KR RSS and Naver skipped audit |
| `outputs/tables/candidate_news_article_relevance_v0_3.csv` | 613 | combined article relevance table |
| `outputs/tables/candidate_news_signal_summary_v0_3.csv` | 200 | combined candidate-level news signal summary |
| `outputs/tables/candidate_news_slot_summary_v0_3.csv` | 10 | combined slot/status summary |
| `outputs/tables/ssg_market_realism_news_join_v0_3.csv` | 2,723 | worklist joined with combined news signals and language counts |

Combined signal totals:

| signal | value |
|---|---:|
| usable news-signal rows | 340 |
| usable English article rows | 340 |
| usable Korean article rows | 0 |

## Manual Feasibility Worklist

Run 027 adds a source-lane worklist that says what must be checked manually before any shortlist decision.

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/manual_feasibility_source_worklist_v0_1.csv` | 2,723 | full manual feasibility queue with source lanes |
| `outputs/tables/manual_feasibility_source_summary_v0_1.csv` | 6 | slot and priority-tier summary |
| `outputs/tables/manual_feasibility_source_lane_summary_v0_1.csv` | 10 | source-lane summary |

Manual feasibility result:

| metric | value |
|---|---:|
| full worklist rows | 2,723 |
| rows needing manual source follow-up | 1,706 |
| rows outside manual feasibility scope | 1,017 |
| rows with medical + contract blocker tier | 1,706 |

Top source lanes:

| source lane | rows |
|---|---:|
| Korean news via Naver/local search | 1,706 |
| medical file and recent availability check | 1,706 |
| agent/Korea-willingness check | 1,552 |
| role/salary/KBO cost-fit check | 1,552 |
| MLB contract/salary/option check | 1,496 |
| Asian-league contract/buyout/transfer-fee check | 154 |
| local-league salary/agent source check | 154 |
| passport/nationality/quota eligibility check | 154 |

Interpretation:

- The bottleneck has moved from "can we find names?" to "can we verify reality?"
- For MLB-side foreign candidates, the dominant blockers are medical status, contract control, salary/KBO cost fit, and Korea-willingness.
- For Asian-quota candidates, the dominant blockers are buyout/transfer fee, salary/agent context, passport/nationality eligibility, and local-language source coverage.

## Gate Audit

Allowed:

- Use v0.3 news signals as research-only risk context.
- Use the manual feasibility worklist as the next source-collection queue.

Not allowed:

- No final shortlist.
- No recommendation labels.
- No candidate-name release.
- No score release.

Every joined/manual row remains locked:

- `is_final_recommendation = False`
- `shortlist_label_allowed = False`
- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `candidate_news_score_release_allowed = False`

## Six-Layer Progress After Run 027

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | unchanged |
| 3 | Candidate market construction | 92% | 91% -> 92% |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 82% | 81% -> 82% |
| 6 | SSG fit ranking | 68% | 66% -> 68% |

Candidate release remains locked.

## Next Step

Load Naver credentials into the shell environment and run candidate-specific Korean news. Then fill the manual feasibility source lanes: salary, contract terms, options, buyout/transfer-fee, agent signals, medical availability, and Korea-willingness.
