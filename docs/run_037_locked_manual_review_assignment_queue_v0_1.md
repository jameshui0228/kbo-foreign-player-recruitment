# Run 037 Locked Manual Review Assignment Queue v0.1

Date: 2026-06-22 KST

Layer focus:

- 6. SSG fit ranking

Candidate policy: locked. This run does not release candidate names, teams,
exact scores, exact ranks, shortlist labels, manual unlock labels, or
recommendations.

## Purpose

Run 036 created the blank manual review template. Run 037 turns that template
into a field-style review queue:

- which anonymous cards should start now;
- which cards need source rebuilding before video review;
- which reviewer role should own the first pass;
- which fields must be filled first;
- which kill-switch question should stop a weak case early.

This is an operating workflow, not a candidate list.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/locked_manual_review_assignment_queue_v0_1.csv` | 72 | anonymous card-level review assignment queue |
| `outputs/tables/locked_manual_review_assignment_summary_v0_1.csv` | 5 | slot/wave/lane count summary |
| `outputs/tables/locked_manual_review_reviewer_workload_v0_1.csv` | 4 | primary/secondary reviewer workload by role |
| `outputs/tables/locked_manual_review_checklist_v0_1.csv` | 7 | reviewer-role checklist |
| `outputs/tables/locked_manual_review_assignment_gate_audit_v0_1.csv` | 4 | candidate-release and queue-integrity audit |
| `src/modeling/build_locked_manual_review_assignment_queue_v0_1.py` | script | reproducible builder |

## Assignment Queue Result

| slot | review wave | review lane | cards |
|---|---|---|---:|
| Foreign hitter | wave_1_evidence_read_now | contract_access_check | 1 |
| Foreign hitter | wave_1_rebuild_source_first | source_rebuild_before_video | 29 |
| Foreign hitter | wave_2_review_after_core_sources | source_rebuild_before_video | 1 |
| Foreign pitcher | wave_1_rebuild_source_first | pitcher_source_and_workload_rebuild | 40 |
| Foreign pitcher | wave_2_review_after_core_sources | pitcher_source_and_workload_rebuild | 1 |

## Key Operational Finding

The model has created 72 anonymous cards, but the manual review queue says that
most cards should not jump straight into subjective scouting opinion.

Only one card has enough attached source support to start with evidence reading
immediately. The other 71 cards need source rebuilding first, mainly because the
current card output is anonymous and the source-confidence/article bands are
thin.

This is useful for the project because it separates:

- model-interesting cards;
- source-ready cards;
- scouting-ready cards;
- release-ready candidates.

Those should not be treated as the same thing.

## Reviewer Workload

| reviewer role | position | slot | cards |
|---|---|---|---:|
| source_contract_reviewer | primary | foreign_hitter | 31 |
| source_contract_reviewer | primary | foreign_pitcher | 41 |
| hitter_video_reviewer | secondary | foreign_hitter | 31 |
| medical_workload_reviewer | secondary | foreign_pitcher | 41 |

## Gate Audit

| gate | result |
|---|---|
| assignment rows match manual template | pass, 72 / 72 |
| candidate identifiers and exact scores removed | pass |
| release locks preserved | pass, 72 / 72 |
| manual decision status still locked | pass, 72 / 72 |

The assignment queue excludes candidate names, teams, exact scores, exact ranks,
shortlist labels, manual unlock labels, and recommendations.

## Six-Layer Progress After Run 037

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 90% | unchanged |
| 6 | SSG fit ranking | 88% | 87% -> 88% |

Candidate release remains locked.

## Current Message

Layer 6 now has a field-style operating rule:

> Do not let model ranking become scouting conviction. First rebuild the source
> file, then run video/manual grades, then recalibrate fit and risk, and only
> then consider unlocking candidate names.

## Remaining Gaps

- Manual review fields are still blank by design.
- Actual source URLs are not filled into the public-safe assignment queue.
- Contract, medical, and Korea-willingness values still need reviewed source
  evidence.
- Candidate names, scores, ranks, shortlist labels, manual unlock labels, and
  recommendations stay locked.
