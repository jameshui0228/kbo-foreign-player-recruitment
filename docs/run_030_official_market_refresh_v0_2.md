# Run 030 Official Market Refresh v0.2

Date: 2026-06-22 KST

## Purpose

Refresh the practical market-availability layer with current official MLB roster
and transaction data, then rejoin it to the candidate news and manual feasibility
queues.

This run does not select or recommend candidates. It only improves the source
grounding for Layers 3, 5, and 6.

## Actions

- Collected MLB transactions from 2025-10-01 through 2026-06-22.
- Collected MLB roster status as of 2026-06-22.
- Updated the market-realism builder to accept `--run-date` and
  `--output-suffix`.
- Built `ssg_market_realism_layer_v0_2.csv` from the refreshed official data.
- Rejoined the refreshed market worklist to the combined English plus Naver
  candidate news layer as `ssg_market_realism_news_join_v0_5.csv`.
- Rebuilt the manual feasibility source worklist as v0.3.

## New Or Updated Outputs

| output | rows | note |
|---|---:|---|
| `outputs/tables/mlb_transactions_20251001_20260622.csv` | 12,155 | official MLB transaction refresh |
| `outputs/tables/mlb_transactions_latest.csv` | 12,155 | latest pointer refreshed |
| `outputs/tables/mlb_roster_status_20260622.csv` | 8,198 | official MLB roster/status refresh |
| `outputs/tables/mlb_roster_status_latest.csv` | 8,198 | latest pointer refreshed |
| `outputs/tables/ssg_market_realism_layer_v0_2.csv` | 2,723 | refreshed market-realism layer |
| `outputs/tables/ssg_market_realism_manual_worklist_v0_2.csv` | 2,723 | refreshed market worklist |
| `outputs/tables/ssg_market_realism_news_join_v0_5.csv` | 2,723 | refreshed market plus news join |
| `outputs/tables/candidate_news_signal_summary_v0_5.csv` | 200 | news signals, same raw news corpus |
| `outputs/tables/manual_feasibility_source_worklist_v0_3.csv` | 2,723 | latest manual source-lane queue |
| `outputs/tables/manual_feasibility_source_lane_summary_v0_3.csv` | 10 | manual source-lane summary |

## Validation

- All 2,723 market rows carry `market_realism_run_date = 2026-06-22`.
- The refreshed official data changed:
  - market realism score for 16 rows;
  - market realism status for 10 rows;
  - contract-control bucket for 7 rows;
  - medical-risk bucket for 5 rows;
  - latest transaction type for 10 rows.
- Release locks remain closed for all 2,723 market rows:
  - `is_final_recommendation = False`;
  - `shortlist_label_allowed = False`;
  - `candidate_name_release_allowed = False`;
  - `score_release_allowed = False`;
  - `blend_release_allowed = False`.
- Python compile check passed for:
  - `src/modeling/build_market_realism_layer_v0_1.py`;
  - `src/features/build_candidate_news_signals.py`;
  - `src/modeling/build_manual_feasibility_worklist_v0_1.py`.

## Market-Realism Movement

| slot | rows | median score | p75 score | contact/buyout priority | blocker/low access | medical hold |
|---|---:|---:|---:|---:|---:|---:|
| asian_quota | 978 | 9.0 | 9.0 | 154 | 0 | 0 |
| foreign_hitter | 736 | 0.0 | 13.5 | 14 | 432 | 215 |
| foreign_pitcher | 1,009 | 0.0 | 20.0 | 29 | 525 | 356 |

Interpretation:

- The official refresh slightly reduced optimistic access labels for foreign
  hitters and pitchers.
- This is useful because the model is becoming less likely to treat controlled,
  recently selected, active, or medically flagged players as easy acquisition
  targets.

## Manual Feasibility Queue v0.3

| lane | rows | unique players |
|---|---:|---:|
| medical file and recent availability check | 1,703 | 1,695 |
| Korean/Naver/local news search | 1,694 | 1,686 |
| agent Korea-willingness check | 1,549 | 1,542 |
| role/salary/KBO cost fit check | 1,549 | 1,542 |
| MLB contract/salary/option check | 1,495 | 1,488 |
| Asian-league buyout/transfer fee check | 154 | 153 |
| local league salary/agent source check | 154 | 153 |
| passport/nationality/quota eligibility check | 154 | 153 |
| Korea/overseas intent context review | 18 | 17 |
| public contract market news review | 8 | 8 |

## Six-Layer Progress

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | unchanged |
| 3 | Candidate market construction | 94% | +1 |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 85% | +1 |
| 6 | SSG fit ranking | 71% | +1 |

## Candidate Policy

Candidate names remain locked. This run improves the market and risk queue, but
does not allow shortlist, recommendation, ranking-label, or score release.

## Remaining Gaps

- Salary and opt-out details are not available from the public MLB roster and
  transaction feeds.
- Buyout, transfer-fee, salary, and agent-willingness values remain missing for
  Asian-quota candidates.
- Medical signals are still roster/news proxies and must be verified with
  injury-history and availability review.
- Candidate release remains blocked until source lanes are filled and final
  review gates pass.
