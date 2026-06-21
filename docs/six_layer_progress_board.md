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
| 2 | KBO foreign-player success/failure archetype mining | partial plus feature-family archetypes v0.3 | 70% | `outputs/tables/kbo_translation_failure_feature_family_decisions_v0_3.csv` | expand historical ID crosswalk to 2017-2022, add NPB/CPBL context, and convert promoted feature families into candidate-side tags |
| 3 | Candidate market construction | partial plus full MiLB and NPB context | 80% | `outputs/tables/milb_market_pool_stats_all_v1.csv` | add NPB nationality and salary/contract/buyout proxies, ABL roster/stats, and news/manual availability checks |
| 4 | KBO translation model | pilot feature-family promoted for hitters | 73% | `outputs/tables/kbo_translation_failure_feature_family_cv_comparison_v0_3.csv` | build candidate-side hitter Savant pilot component and keep pitcher translation diagnostic until more context is added |
| 5 | Failure risk model | pitcher MiLB damage/command diagnostic only | 64% | `outputs/tables/kbo_translation_failure_feature_family_decisions_v0_3.csv` | add injury/news/adaptation text plus contract and willingness variables, then retest pitcher risk families |
| 6 | SSG fit ranking | locked with hitter pilot component | 32% | `docs/run_021_feature_family_ablation_v0_3.md` | build layer-weighted ranking only after hitter pilot component, pitcher diagnostics, market feasibility, risk context, and release gates are joined |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names can be used only as `research_lead` or `market_watch`.

The labels `shortlist_candidate` and `recommendation` remain locked until all six layers pass.
