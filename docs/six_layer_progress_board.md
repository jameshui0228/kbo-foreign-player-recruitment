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
| 1 | SSG hidden weakness mining | presentation bridge ready pending refresh | 93% | `outputs/tables/ssg_layer1_candidate_feature_blueprint_v4.csv` | refresh STATIZ/current-game data and attach stronger play-by-play/defense/baserunning proxies; then freeze Layer 1 or move effort to layers 2-5 |
| 2 | KBO foreign-player success/failure archetype mining | archetype validation and rule stability built | 86% | `outputs/tables/layer2_archetype_validation_matrix_v0_1.csv` | close the 56-row historical backfill queue and rerun archetype stability validation |
| 3 | Candidate market construction | fit source-fill packet built | 95% | `outputs/tables/ssg_fit_source_fill_packet_v0_1.csv` | fill exact salary, opt-out, transfer-fee, buyout, agent, passport, medical, and Korea-willingness source values |
| 4 | KBO translation model | locked pitcher translation proxy built | 88% | `outputs/tables/layer4_pitcher_translation_proxy_component_v0_1.csv` | attach source evidence to pitcher proxy groups and validate proxy against historical archetype rule tiers |
| 5 | Failure risk model | source evidence prefill readiness attached | 93% | `outputs/tables/layer5_6_source_readiness_recalibration_v0_1.csv` | fill remaining contract, medical, Korea-willingness, and video/report source rows and mark human-reviewed evidence strength |
| 6 | SSG fit ranking | locked source evidence prefill built | 93% | `outputs/tables/locked_source_evidence_prefill_template_v0_1.csv` | complete the remaining source URL backlog and transfer reviewed evidence into manual grades before unlock |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names can be used only as `research_inventory` or `market_watch`.

The labels `shortlist_candidate` and `recommendation` remain locked until all six layers pass.
