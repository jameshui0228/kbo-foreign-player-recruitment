# Run 040 Layer 2/4 Validation Sprint v0.1

Date: 2026-06-22 KST

Layer focus:

- 2. KBO foreign-player success/failure archetype mining
- 4. KBO translation model

Candidate policy: locked. Candidate-side outputs do not release candidate
names, teams, exact scores, exact ranks, shortlist labels, or recommendations.

## Purpose

The previous workflow had a gap between historical KBO foreign-player archetypes
and current candidate-side translation signals:

- Layer 2 had outcome archetypes and rule lifts, but limited validation tiers.
- Layer 4 had a hitter translation component, while pitcher translation remained
  diagnostic-only.

Run 040 turns those gaps into measurable artifacts:

- an archetype validation matrix;
- rule stability tiers;
- a historical backfill queue;
- a locked pitcher translation proxy component.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/layer2_archetype_validation_matrix_v0_1.csv` | 7 | validation tier by historical archetype |
| `outputs/tables/layer2_rule_stability_tiers_v0_1.csv` | 294 | rule-level promotion/watch/do-not-promote tiers |
| `outputs/tables/layer2_historical_backfill_queue_v0_1.csv` | 56 | model-ready historical feature backfill queue |
| `outputs/tables/layer4_pitcher_translation_proxy_component_v0_1.csv` | 1009 | locked candidate-side pitcher translation proxy |
| `outputs/tables/layer4_pitcher_translation_proxy_summary_v0_1.csv` | 7 | pitcher proxy distribution summary |
| `outputs/tables/layer2_4_validation_sprint_gate_audit_v0_1.csv` | 5 | layer 2/4 gate audit |
| `src/modeling/build_layer2_4_validation_sprint_v0_1.py` | script | reproducible builder |

## Layer 2 Result

Archetype validation:

| tier | archetypes |
|---|---:|
| thin_but_trackable_archetype | 7 |

Rule stability:

| rule tier | rules |
|---|---:|
| promote_to_candidate_proxy | 7 |
| research_support_rule | 32 |
| thin_watch_rule | 116 |
| do_not_promote_rule | 139 |

Historical backfill:

| priority | rows |
|---|---:|
| P1_recent_outcome_backfill | 56 |

## Layer 4 Result

Pitcher translation proxy:

| status | rows |
|---|---:|
| usable_candidate_side_proxy | 175 |
| research_proxy_needs_manual_review | 586 |
| thin_proxy_needs_source_rebuild | 248 |

The pitcher proxy is built from candidate-side diagnostic, starter runway,
traffic command, availability, and market-access components. It is not a final
translation model and does not release names or recommendations.

## Key Operational Finding

Layer 2 and Layer 4 are now connected by explicit gates:

- historical archetype rules are tiered rather than treated as equally usable;
- 39 rules are strong enough to be research support or candidate-side proxy
  inputs;
- 56 recent historical rows need backfill before the archetype system can be
  considered near-final;
- pitcher candidate-side translation now exists as a locked proxy, so pitcher
  fit no longer depends only on generic risk/market filters.

## Gate Audit

| gate | result |
|---|---|
| archetype validation matrix built | pass with visible gap |
| rule stability tiers built | pass with visible gap |
| historical backfill queue built | pass |
| pitcher translation proxy component built | pass with visible gap |
| candidate release locks preserved | pass |

## Six-Layer Progress After Run 040

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 86% | 78% -> 86% |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 88% | 80% -> 88% |
| 5 | Failure risk model | 90% | unchanged |
| 6 | SSG fit ranking | 90% | unchanged |

Candidate release remains locked.

## Remaining Gaps

- Layer 2 still needs the 56-row historical backfill closed.
- Layer 4 pitcher proxy is usable as a locked research component, but still
  needs manual source evidence and outcome-calibrated final validation.
- Candidate names, scores, ranks, shortlist labels, and recommendations stay
  locked.
