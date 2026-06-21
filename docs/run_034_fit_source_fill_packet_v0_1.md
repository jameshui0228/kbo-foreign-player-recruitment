# Run 034 Fit Source-Fill Packet v0.1

Date: 2026-06-22 KST

Layer focus:

- 3. Candidate market construction
- 5. Failure risk model
- 6. SSG fit ranking

Candidate policy: locked. This run builds a source-fill packet for the locked
Layer 6 queue. It does not release candidate names, scores, ranks, shortlist
labels, or recommendations.

## Purpose

Run 033 created a risk-adjusted SSG fit queue. Run 034 asks the next practical
question:

> Which missing sources still block the high-interest queue from becoming a
> real shortlist?

## Scope

The source-fill scope was built from the locked Layer 6 queue:

- all lane 1 source-fill priority rows;
- all lane 2 deep-review rows;
- five top-scored lane 0 medical/blocker rows per foreign-player slot.

Total scope: 118 rows.

## Fresh Collection

Naver Search News was recollected for the source-fill scope with compact
candidate queries.

| metric | value |
|---|---:|
| scope rows | 118 |
| Naver query attempts | 236 |
| fresh Naver article metadata rows | 3 |
| fresh candidate-name matched rows | 2 |

Interpretation:

- Fresh Korean public-news search does not solve the source gap.
- The high-interest queue still needs manual/local source work for contract,
  medical, passport, agent, and Korea-willingness evidence.
- Existing English/Google metadata remains useful, but it is not enough to
  unlock a final shortlist.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_fit_source_news_scope_v0_1.csv` | 118 | Layer 6 source-fill scope |
| `outputs/tables/ssg_fit_source_news_collection_audit_v0_1.csv` | 236 | Naver query audit |
| `outputs/tables/ssg_fit_source_news_article_relevance_v0_1.csv` | 257 | prior + fresh article relevance for scope |
| `outputs/tables/ssg_fit_source_news_signal_summary_v0_1.csv` | 118 | candidate-level source news summary |
| `outputs/tables/ssg_fit_source_fill_packet_v0_1.csv` | 118 | source status and next actions |
| `outputs/tables/ssg_fit_source_fill_lane_summary_v0_1.csv` | 13 | slot/lane/readiness summary |
| `outputs/tables/ssg_fit_source_fill_action_summary_v0_1.csv` | 8 | manual action counts |
| `outputs/tables/ssg_fit_source_fill_gate_audit_v0_1.csv` | 4 | lock and source audit |
| `src/data/collect_fit_queue_source_news_v0_1.py` | script | reproducible source news collector |
| `src/modeling/build_fit_source_fill_packet_v0_1.py` | script | reproducible packet builder |

Raw Naver metadata remains local under
`data/raw/articles/fit_queue_source_news_v0_1/` and is ignored by Git.

## Source-Fill Readiness

| slot | major gap | targeted gap | manual verification needed | scouting card next |
|---|---:|---:|---:|---:|
| Asian quota | 1 | 15 | 2 | 0 |
| Foreign hitter | 8 | 6 | 1 | 31 |
| Foreign pitcher | 5 | 8 | 0 | 41 |

Interpretation:

- Foreign hitter and foreign pitcher now have 72 locked rows that can move to
  manual scouting-card review.
- Those rows are not recommendations. They are rows where public source
  blockers are less severe after the current evidence pass.
- Asian quota remains source-blocked because passport/nationality, contract,
  buyout, and medical/current-availability confirmation are not sufficiently
  solved by public metadata.

## Next Manual Actions

| action | rows |
|---|---:|
| ready for manual scouting-card review | 72 |
| search Korean/local and agent-willingness sources | 29 |
| verify salary/contract/option/buyout/agent | 27 |
| manual medical-file review | 24 |
| request/find recent medical availability source | 22 |
| extract exact contract terms from source | 19 |
| confirm passport against Asian-quota rules | 18 |
| read Korea/overseas intent context | 17 |

## Gate Audit

| gate | result |
|---|---|
| source-fill scope built from Layer 6 queue | pass, 118 / 118 |
| source evidence status attached | pass, 118 / 118 |
| fresh Naver collection attempted | visible gap, 118 / 118 |
| release locks preserved | pass, 118 / 118 |

All rows keep:

- `is_final_recommendation = False`
- `shortlist_label_allowed = False`
- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `rank_release_allowed = False`
- `source_fill_unlock_allowed = False`
- `recommendation_label = locked_not_allowed`

## Six-Layer Progress After Run 034

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 95% | 94% -> 95% |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 90% | 89% -> 90% |
| 6 | SSG fit ranking | 83% | 80% -> 83% |

Candidate release remains locked.

## Current Message

Layer 6 now has a source-fill bridge:

> The project can now separate "model-interesting" candidates from "source-
> actionable" candidates. The next unlock is not another score. It is contract,
> medical, passport, agent, and Korea-willingness verification.

## Remaining Gaps

- Fresh Korean public news returned very few candidate-specific rows.
- Exact salary, option, buyout, transfer-fee, and agent values remain manual.
- Medical status remains a file-level/source-level review, not solved by public
  article metadata.
- Asian quota remains blocked by passport/nationality and contract-source
  verification.
