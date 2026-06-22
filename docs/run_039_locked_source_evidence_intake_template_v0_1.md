# Run 039 Locked Source Evidence Intake Template v0.1

Date: 2026-06-22 KST

Layer focus:

- 6. SSG fit ranking

Candidate policy: locked. This run does not release candidate names, teams,
exact scores, exact ranks, shortlist labels, manual unlock labels, or
recommendations.

## Purpose

Run 038 defined the source bundles required before manual scouting can matter.
Run 039 expands those bundles into a row-level evidence intake template:

- one row per anonymous card and required source type;
- blank URL/title/date/publisher/evidence fields for reviewers;
- mapping from each source type to the manual review field it should fill;
- gate audit that keeps candidate release locked.

This is the first artifact that can be handed to teammates as a concrete
source-filling work queue.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/locked_source_evidence_intake_template_v0_1.csv` | 473 | row-level source evidence intake template |
| `outputs/tables/locked_source_evidence_intake_summary_v0_1.csv` | 32 | source-type count summary |
| `outputs/tables/locked_source_evidence_manual_field_map_v0_1.csv` | 13 | source type to manual-field mapping |
| `outputs/tables/locked_source_evidence_intake_rubric_v0_1.csv` | 11 | allowed values and reviewer guidance |
| `outputs/tables/locked_source_evidence_intake_gate_audit_v0_1.csv` | 4 | intake and release-lock audit |
| `src/modeling/build_locked_source_evidence_intake_template_v0_1.py` | script | reproducible builder |

## Intake Scope

| slot | cards | source rows |
|---|---:|---:|
| Foreign hitter | 31 | 186 |
| Foreign pitcher | 41 | 287 |
| Total | 72 | 473 |

## Manual Field Mapping

| source type | target manual field |
|---|---|
| current_stat_page | `stat_source_url_1` |
| recent_video_or_scouting_report | `video_source_url_1` |
| contract_access_source | `contract_source_url` |
| medical_current_status_source | `medical_source_url` |
| of_dh_role_and_defense_source | `video_source_url_2` |
| transaction_or_roster_status_source | `stat_source_url_2` |
| workload_starter_runway_source | `stat_source_url_2` |
| korea_or_overseas_willingness_source_if_available | `korea_willingness_source_url` |

## Key Operational Finding

Layer 6 now has a real source-filling unit of work:

- 473 total evidence rows;
- 473 rows start blank by design;
- 0 source URLs are currently filled;
- every row stays candidate-name-free and release-locked.

This is useful because the project can now measure source-work progress
directly instead of saying vaguely that more research is needed.

## Gate Audit

| gate | result |
|---|---|
| intake rows match required source bundle | pass, 473 / 473 |
| candidate identifiers and exact scores removed | pass |
| source input fields start blank | pass, 473 / 473 |
| release locks preserved | pass, 473 / 473 |

## Six-Layer Progress After Run 039

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 90% | unchanged |
| 6 | SSG fit ranking | 90% | 89% -> 90% |

Candidate release remains locked.

## Current Message

The project can now say:

> We do not need "more research" in the abstract. We need 473 specific source
> rows filled, mapped to the exact manual fields that would unlock recalibration.

## Remaining Gaps

- Source URLs, source titles, dates, publishers, extracted claims, and reviewer
  notes are still blank.
- Contract, medical, workload, role, and Korea/overseas willingness evidence
  still need human-reviewed source URLs.
- Candidate names, scores, ranks, shortlist labels, manual unlock labels, and
  recommendations stay locked.
