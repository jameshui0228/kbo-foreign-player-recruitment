# Run 041 Locked Source Evidence Prefill v0.1

Date: 2026-06-22 KST

Layer focus:

- 5. Failure risk model
- 6. SSG fit ranking

Candidate policy: locked. This run does not release candidate names, teams,
exact scores, exact ranks, shortlist labels, manual unlock labels, or
recommendations.

## Purpose

Run 039 created 473 blank source-intake rows. Run 041 fills the rows that can be
filled safely from ID-based public sources and existing article metadata:

- MLB Stats API URLs from MLBAM IDs;
- Baseball Savant statcast-search URLs from MLBAM IDs;
- existing article metadata links where already available.

This is not human review. It is a locked prefill that gives reviewers a starting
source file instead of a blank sheet.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/locked_source_evidence_prefill_template_v0_1.csv` | 473 | source evidence intake with safe URL prefill |
| `outputs/tables/locked_source_evidence_prefill_summary_v0_1.csv` | 17 | prefill coverage by slot/source type/status |
| `outputs/tables/layer5_6_source_readiness_recalibration_v0_1.csv` | 4 | card-level source readiness bands |
| `outputs/tables/locked_source_evidence_prefill_gate_audit_v0_1.csv` | 4 | prefill and release-lock audit |
| `src/modeling/build_locked_source_evidence_prefill_v0_1.py` | script | reproducible builder |

## Prefill Result

| metric | value |
|---|---:|
| total source rows | 473 |
| URL-prefilled source rows | 190 |
| remaining blank source rows | 283 |
| foreign hitter source rows filled | 65 |
| foreign pitcher source rows filled | 125 |

## Source Types Filled

| source type | filled rows |
|---|---:|
| current_stat_page | 72 |
| of_dh_role_and_defense_source | 31 |
| transaction_or_roster_status_source | 41 |
| workload_starter_runway_source | 41 |
| contract_access_source | 3 |
| medical_current_status_source | 2 |

## Readiness Recalibration

| slot | readiness band | cards |
|---|---|---:|
| Foreign hitter | thin_prefill | 29 |
| Foreign hitter | partial_prefill | 2 |
| Foreign pitcher | partial_prefill | 40 |
| Foreign pitcher | source_complete | 1 |

`source_complete` here means the automated source URL coverage is relatively
high for the required bundle. It still does not mean human review is complete.

## Gate Audit

| gate | result |
|---|---|
| prefill rows match intake rows | pass, 473 / 473 |
| source URLs prefilled | pass with visible gap, 190 / 473 |
| candidate identifiers and exact scores removed | pass |
| release locks preserved | pass, 473 / 473 |

## Six-Layer Progress After Run 041

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 86% | unchanged |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 88% | unchanged |
| 5 | Failure risk model | 93% | 90% -> 93% |
| 6 | SSG fit ranking | 93% | 90% -> 93% |

Candidate release remains locked.

## Current Message

The project can now measure source progress with actual filled rows:

> 190 of 473 required source rows have safe prefilled URLs. The remaining 283
> rows define the exact human source collection backlog.

## Remaining Gaps

- 283 source rows still need URLs.
- Contract, medical, Korea/overseas willingness, video/report, and manual
  extracted claims remain the biggest source gaps.
- All prefilled rows still require human review.
- Candidate names, scores, ranks, shortlist labels, manual unlock labels, and
  recommendations stay locked.
