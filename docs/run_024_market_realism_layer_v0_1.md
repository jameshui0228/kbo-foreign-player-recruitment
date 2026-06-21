# Run 024 Market Realism Layer v0.1

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run adds market-realism checks to the locked fit-preparation mart, but it does not create a final ranking, shortlist, or recommendation.

## Purpose

Run 023 answered: "Can we put hitter, pitcher, and Asian-quota candidates on one SSG fit-preparation table?"

Run 024 answers the next front-office question:

> Which candidates are even realistic enough to call, price, medically review, or verify?

The point is to prevent model scores from outrunning contract, roster, medical, and Asian-quota rule reality.

## Source Refresh

| source | prior state | Run 024 state |
|---|---:|---:|
| MLB official transactions | 11,799 rows through 2026-06-13 | 12,139 rows through 2026-06-21 |
| MLB official roster status | 8,181 rows from 2026-06-12 | 8,197 rows from 2026-06-21 |
| Asian-quota market | 978 rows | unchanged; contract/salary/buyout still unknown |
| Candidate-specific news | not refreshed | not refreshed because Naver credentials are not loaded in the shell environment |

Official MLB transaction source:

`https://statsapi.mlb.com/api/v1/transactions?sportId=1&startDate=2025-10-01&endDate=2026-06-21`

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_market_realism_layer_v0_1.csv` | 2,723 | fit-prep mart with contract, roster, medical, and market-realism gates |
| `outputs/tables/ssg_market_realism_slot_summary_v0_1.csv` | 3 | slot-level market-realism summary |
| `outputs/tables/ssg_market_realism_manual_worklist_v0_1.csv` | 2,723 | research-only manual verification queue |
| `outputs/tables/ssg_market_realism_gate_audit_v0_1.csv` | 5 | source, risk, news-gap, and release-lock audit |
| `src/modeling/build_market_realism_layer_v0_1.py` | script | reproducible Run 024 layer builder |

## Market-Realism Status

| slot | status | rows |
|---|---|---:|
| Asian quota | buyout/salary/agent check needed | 154 |
| Asian quota | nationality verification needed | 772 |
| Asian quota | not Asian-quota eligible, regular foreign only | 52 |
| Foreign hitter | manual contact priority locked | 16 |
| Foreign hitter | contract verification needed | 73 |
| Foreign hitter | contract blocker watch | 421 |
| Foreign hitter | medical hold before scouting | 218 |
| Foreign hitter | low access or unknown market status | 8 |
| Foreign pitcher | manual contact priority locked | 30 |
| Foreign pitcher | contract verification needed | 97 |
| Foreign pitcher | contract blocker watch | 509 |
| Foreign pitcher | medical hold before scouting | 358 |
| Foreign pitcher | low access or unknown market status | 15 |

## Contract-Control Buckets

| slot | bucket | rows |
|---|---|---:|
| Foreign hitter | recent DFA high access | 25 |
| Foreign hitter | recent free agent or released high access | 6 |
| Foreign hitter | non-40-man or outrighted medium access | 83 |
| Foreign hitter | 40-man non-active contract blocker | 176 |
| Foreign hitter | active MLB contract blocker | 446 |
| Foreign pitcher | recent DFA high access | 43 |
| Foreign pitcher | recent free agent or released high access | 8 |
| Foreign pitcher | non-40-man or outrighted medium access | 130 |
| Foreign pitcher | 40-man non-active contract blocker | 306 |
| Foreign pitcher | active MLB contract blocker | 522 |
| Asian quota | eligible but contract/buyout unknown | 154 |
| Asian quota | nationality unknown, contract unusable | 772 |
| Asian quota | Asian-quota nationality fail | 52 |

## Medical-Risk Buckets

| slot | bucket | rows |
|---|---|---:|
| Foreign hitter | current or recent medical hold | 218 |
| Foreign hitter | medical history watch | 55 |
| Foreign hitter | no public roster/transaction medical signal | 463 |
| Foreign pitcher | current or recent medical hold | 358 |
| Foreign pitcher | medical history watch | 87 |
| Foreign pitcher | no public roster/transaction medical signal | 564 |
| Asian quota | candidate medical news not collected | 978 |

## Interpretation

The practical market narrows sharply before baseball ranking:

- Foreign hitter: only 16 rows are current manual-contact priority after official roster and transaction gates.
- Foreign pitcher: only 30 rows are current manual-contact priority after official roster and transaction gates.
- Asian quota: 154 rows pass nationality but still require salary, buyout, agent, and role-acceptance checks.

This is not the final shortlist. It is the work queue for human market verification.

## Gate Audit

| gate | status | meaning |
|---|---|---|
| M1 MLB official sources joined | partial pass | official roster/transaction data are joined for MLB candidates, but salary and opt-out details are absent |
| M2 medical signals visible | pass visible risk layer | roster/transaction medical proxies are visible, but full medical review remains manual |
| M3 Asian contract gap visible | pass visible gap | salary, transfer fee, buyout, and agent willingness are still manual |
| M4 candidate news gap visible | pass visible gap | candidate-specific news was not refreshed because Naver credentials are not loaded |
| M5 release locks preserved | pass | no recommendation labels allowed |

Every row keeps:

- `is_final_recommendation = False`
- `shortlist_label_allowed = False`
- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `blend_release_allowed = False`

## Six-Layer Progress After Run 024

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | unchanged |
| 3 | Candidate market construction | 88% | 85% -> 88% |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 76% | 71% -> 76% |
| 6 | SSG fit ranking | 60% | 52% -> 60% |

Candidate release remains locked.

## Next Step

Run 025 should either:

- refresh candidate-specific news with Naver credentials loaded in the shell, then build injury/adaptation/Korea-willingness text signals; or
- add salary/contract/buyout sources for MLB, NPB, and CPBL to turn the market-realism queue into a release-gate review.
