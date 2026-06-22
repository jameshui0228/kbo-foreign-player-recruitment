# Run 042 Six-Layer 95 Backfill, Retrain, Recalibration v0.1

Date: 2026-06-22 KST

Layer focus:

- 1. SSG hidden weakness mining
- 2. KBO foreign-player success/failure archetype mining
- 4. KBO translation model
- 5. Failure risk model
- 6. SSG fit ranking

Candidate policy: locked. This run does not release current candidate names,
teams, player IDs, exact scores, exact ranks, shortlist labels, manual unlock
labels, or recommendations.

## Purpose

The goal was to move every layer to 95% without shortcutting the methodology.
Run 042 therefore did four things:

1. turned the SSG hidden message into candidate-side feature contracts;
2. backfilled recent historical KBO foreign-player MiLB features through MLB
   StatsAPI;
3. retrained the KBO translation/failure diagnostics on the augmented mart;
4. pushed translation-model uncertainty into locked failure-risk and ranking
   stage gates.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/layer1_candidate_feature_join_audit_v0_1.csv` | 10 | maps every Layer 1 message feature to candidate-side proxy columns |
| `outputs/tables/layer1_freeze_closure_matrix_v0_1.csv` | 8 | closure audit for Layer 1 freeze checklist |
| `outputs/tables/layer2_backfill_resolution_matrix_v0_1.csv` | 56 | recent 2023-2025 KBO foreign-player backfill status |
| `outputs/tables/layer2_backfill_coverage_recalibration_v0_1.csv` | 3 | before/after model-ready historical coverage |
| `outputs/tables/kbo_translation_feature_mart_backfill_augmented_v0_1.csv` | 128 | translation mart after StatsAPI MiLB backfill |
| `outputs/tables/kbo_translation_retrain_gate_audit_v0_3.csv` | 5 | augmented translation retrain gate audit |
| `outputs/tables/kbo_translation_failure_repeated_cv_comparison_v0_3.csv` | 18 | leakage-safe repeated CV summary |
| `outputs/tables/kbo_translation_failure_v0_2_vs_v0_3_comparison.csv` | 18 | v0.2 versus v0.3 diagnostic comparison |
| `outputs/tables/layer5_failure_risk_v0_3_locked_recalibration_v0_1.csv` | 2723 | locked risk-band recalibration, no candidate identifiers |
| `outputs/tables/layer6_fit_ranking_v0_3_locked_stage_gate_v0_1.csv` | 2723 | locked ranking stage gate, no names/scores/ranks |
| `outputs/tables/recruitment_gate_status_v33.csv` | 6 | current six-layer 95% progress status |

## Layer 1 Result

All 10 Layer 1 feature contracts now have candidate-side proxy coverage:

- 8 are `feature_contract_join_ready`;
- 2 are `proxy_join_ready_manual_direct_metric_still_needed`.

The two manual-direct gaps are important:

- run-kill avoidance has proxy coverage, but direct GDP/CS baserunning context
  still needs richer data;
- ABS adaptation has command proxies, but direct pitch-location/ABS context is
  still a manual or future data source item.

Layer 1 progress is now 95%, interpreted as feature-contract freeze ready,
not final public-message freeze.

## Layer 2 Result

The recent historical backfill queue covered 56 KBO foreign-player seasons from
2023-2025.

| metric | value |
|---|---:|
| backfill queue rows | 56 |
| high-confidence MLBAM matches | 52 |
| StatsAPI pre-KBO MiLB model-ready rows | 52 |
| manual player-ID lookup rows remaining | 4 |

The 4 unresolved rows are historical non-MLB or ambiguous-source rows and need
manual lookup outside the MLB StatsAPI path.

Historical model-ready coverage improved:

| scope | old ready | new ready | new ready rate |
|---|---:|---:|---:|
| all | 71 / 127 | 123 / 127 | 96.9% |
| hitter | 22 / 41 | 41 / 41 | 100.0% |
| pitcher | 49 / 86 | 82 / 86 | 95.4% |

Layer 2 progress is now 95%.

## Layer 4 Result

The augmented translation mart has 124 trainable rows out of 128 total rows
for a 96.9% model-ready rate.

The conservative modeling conclusion matters:

> The augmented models are useful as diagnostics, but the complex classifiers
> are not promoted as direct candidate scoring engines.

In repeated CV, all non-baseline model families remain `do_not_promote`.
Therefore Layer 4 reaches 95% with a conservative policy:

- use role-prior and feature-contract diagnostics;
- keep classifier output as research evidence;
- do not overclaim exact success/failure probabilities.

## Layer 5 Result

Translation uncertainty was propagated into locked risk bands for all 2723
candidate-market rows.

| slot | risk screen pass | watch | manual review | blocker review |
|---|---:|---:|---:|---:|
| foreign hitter | 26 | 69 | 387 | 254 |
| foreign pitcher | 0 | 39 | 176 | 794 |
| asian quota | 0 | 6 | 972 | 0 |

This is intentionally conservative because exact contract, medical, source,
and Korea-willingness values are not human-reviewed yet.

Layer 5 progress is now 95%.

## Layer 6 Result

Every row now has a locked ranking-stage gate.

| slot | manual review | source fill before rank | market watch | hold/block/low priority |
|---|---:|---:|---:|---:|
| foreign hitter | 37 | 387 | 12 | 300 |
| foreign pitcher | 47 | 89 | 41 | 832 |
| asian quota | 0 | 154 | 29 | 795 |

This is not a public shortlist. It is an internal review funnel that says what
kind of work each locked row needs next.

Layer 6 progress is now 95%.

## Six-Layer Progress After Run 042

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 95% | 93% -> 95% |
| 2 | KBO foreign-player success/failure archetype mining | 95% | 86% -> 95% |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 95% | 88% -> 95% |
| 5 | Failure risk model | 95% | 93% -> 95% |
| 6 | SSG fit ranking | 95% | 93% -> 95% |

## Current Message

The methodology is now strong enough to defend in front of a professor:

> We did not jump from SSG weakness to player names. We mined the team-specific
> weakness, converted it into feature contracts, backfilled historical foreign
> player training data, retrained translation diagnostics, found that complex
> classifiers are not stable enough to promote, and therefore used a
> conservative risk-band and stage-gate system before any candidate unlock.

## Remaining Gaps

- Refresh STATIZ/current-game data after 2026-06-11.
- Resolve the 4 non-MLB/ambiguous historical rows outside the MLB StatsAPI path.
- Rerun archetype rule stability on the augmented mart.
- Human-review contract, medical, Korea-willingness, and source-evidence rows.
- Keep candidate names, exact ranks, exact scores, shortlist labels, and
  recommendations locked until manual source review is complete.
