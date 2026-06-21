# Six Layer Progress Board

Generated: 2026-06-21 KST

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
| 2 | KBO foreign-player success/failure archetype mining | candidate-side archetype tags joined | 72% | `outputs/tables/candidate_side_hitter_savant_pilot_model_audit_v0_1.csv` | expand historical ID crosswalk to 2017-2022, add NPB/CPBL context, and calibrate candidate-side tags against final fit-ranking rules |
| 3 | Candidate market construction | candidate-side signal and feasibility tags joined | 83% | `outputs/tables/candidate_side_signal_join_summary_v0_1.csv` | add NPB nationality and salary/contract/buyout proxies, ABL roster/stats, and news/manual availability checks |
| 4 | KBO translation model | hitter candidate component joined | 78% | `outputs/tables/candidate_side_hitter_savant_pilot_component_v0_1.csv` | build locked SSG fit preparation mart using hitter component as one input and keeping pitcher translation diagnostic |
| 5 | Failure risk model | pitcher diagnostic tags joined | 68% | `outputs/tables/candidate_side_pitcher_milb_diagnostic_tags_v0_1.csv` | add injury/news/adaptation text plus contract and willingness variables to the pitcher diagnostic layer |
| 6 | SSG fit ranking | locked with candidate-side signal components | 40% | `docs/run_022_candidate_side_signal_join_v0_1.md` | build a locked SSG fit ranking preparation mart with research-only labels after joining signal components, market feasibility, and risk context |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names can be used only as `research_lead` or `market_watch`.

The labels `shortlist_candidate` and `recommendation` remain locked until all six layers pass.
