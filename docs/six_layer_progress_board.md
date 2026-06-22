# Six Layer Progress Board

Generated: 2026-06-22 KST

From this point forward, every major update should report progress on these six layers:

1. SSG hidden weakness mining
2. KBO foreign-player success/failure archetype mining
3. Candidate market construction
4. KBO translation model
5. Failure risk model
6. SSG fit ranking

## Current Progress

| no. | layer | status | progress | latest evidence | next action |
|---:|---|---|---:|---|---|
| 1 | SSG hidden weakness mining | feature contract freeze ready pending final refresh | 95% | `outputs/tables/layer1_candidate_feature_join_audit_v0_1.csv` | refresh post-2026-06-11 STATIZ/current-game data and get human baseball signoff before public finalization |
| 2 | KBO foreign-player success/failure archetype mining | recent backfill training coverage ready | 95% | `outputs/tables/layer2_backfill_coverage_recalibration_v0_1.csv` | manually resolve the four non-MLB/ambiguous historical rows and rerun rule stability on the augmented mart |
| 3 | Candidate market construction | fit source-fill packet built | 95% | `outputs/tables/ssg_fit_source_fill_packet_v0_1.csv` | fill exact salary, opt-out, transfer-fee, buyout, agent, passport, medical, and Korea-willingness source values |
| 4 | KBO translation model | augmented translation retrain complete with conservative policy | 95% | `outputs/tables/kbo_translation_retrain_gate_audit_v0_3.csv` | use role-prior/feature-contract policy until larger labeled samples improve classifier stability |
| 5 | Failure risk model | failure risk recalibrated with translation uncertainty | 95% | `outputs/tables/layer5_6_augmented_recalibration_gate_audit_v0_1.csv` | complete human source review before any exact risk score or recommendation can be made public |
| 6 | SSG fit ranking | locked ranking stage gate complete | 95% | `outputs/tables/layer6_fit_ranking_v0_3_stage_summary_v0_1.csv` | use locked stage gates for internal review; keep names, ranks, exact scores, shortlist labels, and recommendations locked |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names, exact scores, exact ranks, shortlist labels, manual unlock labels,
and recommendations remain locked even though all six layers have reached 95%.

The current 95% state means the data/model/risk/ranking stage gates are built
and reproducible. It does not mean the public shortlist is unlocked.
