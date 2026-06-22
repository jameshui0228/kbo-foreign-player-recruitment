# Run 038 Locked Source Rebuild Packet v0.1

Date: 2026-06-22 KST

Layer focus:

- 6. SSG fit ranking

Candidate policy: locked. This run does not release candidate names, teams,
exact scores, exact ranks, shortlist labels, manual unlock labels, or
recommendations.

## Purpose

Run 037 created an anonymous assignment queue. Run 038 converts that queue into
a source-rebuild packet that says exactly what evidence bundle must exist before
manual scouting grades can matter.

This prevents a common recruiting-analysis failure:

> treating a model-interesting card as if it were already a scouting-ready
> candidate.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/locked_source_rebuild_packet_v0_1.csv` | 72 | anonymous card-level source rebuild tasks |
| `outputs/tables/locked_source_rebuild_summary_v0_1.csv` | 5 | priority/slot/lane summary |
| `outputs/tables/locked_source_rebuild_bundle_matrix_v0_1.csv` | 31 | required source bundle counts |
| `outputs/tables/locked_source_rebuild_checklist_v0_1.csv` | 11 | source-type checklist |
| `outputs/tables/locked_source_rebuild_gate_audit_v0_1.csv` | 4 | release-lock and source-status audit |
| `src/modeling/build_locked_source_rebuild_packet_v0_1.py` | script | reproducible builder |

## Source Rebuild Result

| priority | slot | lane | cards |
|---|---|---|---:|
| P0_read_existing_source_now | Foreign hitter | targeted_contract_access_read | 1 |
| P1_rebuild_source_file_before_video | Foreign hitter | hitter_full_source_file_rebuild | 29 |
| P1_rebuild_source_file_before_video | Foreign pitcher | pitcher_full_source_file_rebuild | 40 |
| P2_hold_until_core_source_file_exists | Foreign hitter | hitter_full_source_file_rebuild | 1 |
| P2_hold_until_core_source_file_exists | Foreign pitcher | pitcher_full_source_file_rebuild | 1 |

## Required Evidence Bundles

Foreign hitter cards require:

- current stat page;
- recent video or scouting report;
- contract/access source;
- medical/current-status source;
- OF/DH role and defense source;
- Korea/overseas willingness source if available.

Foreign pitcher cards require:

- current stat page;
- recent video or scouting report;
- transaction or roster-status source;
- workload/starter-runway source;
- medical/current-status source;
- contract/access source;
- Korea/overseas willingness source if available.

## Key Operational Finding

Layer 6 is no longer just a ranking output. It now has a pre-scouting evidence
gate:

- one anonymous card can be read from existing evidence now;
- 69 anonymous cards need source files rebuilt before video/manual grades;
- two anonymous cards should wait until a core source file exists.

This is a useful constraint because it makes the project more field-like:
source file first, scouting opinion second, model recalibration third, candidate
unlock last.

## Gate Audit

| gate | result |
|---|---|
| source rebuild rows match assignment queue | pass, 72 / 72 |
| candidate identifiers and exact scores removed | pass |
| release locks preserved | pass, 72 / 72 |
| source file status not started | pass, 72 / 72 |

The source rebuild packet excludes candidate names, teams, exact scores, exact
ranks, shortlist labels, manual unlock labels, and recommendations.

## Six-Layer Progress After Run 038

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 90% | unchanged |
| 6 | SSG fit ranking | 89% | 88% -> 89% |

Candidate release remains locked.

## Current Message

The project now has a clear pre-unlock rule:

> A candidate cannot become a recommendation until its anonymous source bundle
> is rebuilt, manual fields are filled, and the fit/risk model is recalibrated.

## Remaining Gaps

- The source rebuild packet is still blank operational work; it does not contain
  reviewed URLs yet.
- Source-file status is `not_started_locked` for all 72 cards.
- Contract, medical, workload, role, and Korea/overseas willingness evidence
  still need human-reviewed source URLs.
- Candidate names, scores, ranks, shortlist labels, manual unlock labels, and
  recommendations stay locked.
