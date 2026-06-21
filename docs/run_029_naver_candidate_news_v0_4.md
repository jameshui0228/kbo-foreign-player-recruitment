# Run 029 Naver Candidate News v0.4

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run adds Korean/Naver article metadata, but it does not create a final ranking, shortlist, recommendation label, candidate-name release, or score release.

## Purpose

Run 027 proved that Google Korean-locale RSS was not a reliable Korean-news substitute. Run 028 prepared a credential-safe local env workflow. Run 029 executes Naver News collection for the priority scope and joins it with the existing English candidate-news layer.

The practical question:

> Does Naver candidate-specific news reduce the Korean-source gap and add usable medical, contract, or Korea/overseas context?

## Credential Handling

Naver credentials were stored only in a local gitignored `.env.naver` file. They were not committed to Git and are not included in any output table.

## Collection Result

| metric | value |
|---|---:|
| Naver priority scope rows | 62 |
| Naver article metadata rows | 39 |
| Naver candidate-name matched rows | 31 |
| combined article rows | 652 |
| combined usable news-signal rows | 367 |
| usable English article rows | 340 |
| usable Korean article rows | 27 |
| candidates with usable Korean articles | 10 |

Raw Naver metadata remains local under `data/raw/articles/candidate_news_naver_v0_4/` and is ignored by Git. Derived research tables are tracked.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/candidate_news_scope_naver_v0_4.csv` | 62 | Naver priority scope |
| `outputs/tables/candidate_news_collection_audit_naver_v0_4.csv` | 310 | provider/query audit |
| `outputs/tables/candidate_news_article_relevance_v0_4.csv` | 652 | English + Naver article-level relevance |
| `outputs/tables/candidate_news_signal_summary_v0_4.csv` | 200 | combined candidate-level news signal summary |
| `outputs/tables/candidate_news_slot_summary_v0_4.csv` | 10 | combined slot/status summary |
| `outputs/tables/ssg_market_realism_news_join_v0_4.csv` | 2,723 | market-realism worklist joined with English + Naver news signals |
| `outputs/tables/manual_feasibility_source_worklist_v0_2.csv` | 2,723 | manual source worklist rebuilt on v0.4 news |
| `outputs/tables/manual_feasibility_source_summary_v0_2.csv` | 6 | slot and priority-tier summary |
| `outputs/tables/manual_feasibility_source_lane_summary_v0_2.csv` | 10 | source-lane summary |

## Signal Movement

Compared with Run 026/027:

| signal | before | after |
|---|---:|---:|
| combined article rows | 613 | 652 |
| usable news-signal rows | 340 | 367 |
| usable Korean article rows | 0 | 27 |
| candidates with usable Korean articles | 0 | 10 |
| manual Korean-news missing lane rows | 1,706 | 1,696 |

Interpretation:

- Naver does not eliminate the Korean-source gap, but it adds real candidate-level Korean context.
- The manual queue remains necessary because most candidates still need Korean/local source confirmation.
- Korean news is now a real source lane, not just a planned blocker.

## Gate Audit

Allowed:

- Use v0.4 news signals as research-only risk context.
- Use the v0.2 manual feasibility worklist as the next source-collection queue.

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

## Six-Layer Progress After Run 029

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | unchanged |
| 3 | Candidate market construction | 93% | 92% -> 93% |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 84% | 82% -> 84% |
| 6 | SSG fit ranking | 70% | 68% -> 70% |

Candidate release remains locked.

## Next Step

Fill the remaining manual feasibility source lanes: salary, contract terms, option status, Asian-league buyout/transfer fee, medical availability, agent signals, and Korea-willingness.
