# Six Layer Progress Board

Generated: 2026-06-14 KST

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
| 2 | KBO foreign-player success/failure archetype mining | partial plus historical MiLB backfill | 62% | `outputs/tables/historical_kbo_prearrival_milb_features_v1.csv` | expand historical ID crosswalk to 2017-2022 and add NPB/CPBL pre-arrival context |
| 3 | Candidate market construction | partial plus full MiLB and NPB context | 80% | `outputs/tables/milb_market_pool_stats_all_v1.csv` | add NPB nationality and salary/contract/buyout proxies, ABL roster/stats, and news/manual availability checks |
| 4 | KBO translation model | pilot plus historical MiLB backfill | 64% | `outputs/tables/historical_kbo_prearrival_milb_features_v1.csv` | join historical MiLB features into model marts and rerun repeated CV |
| 5 | Failure risk model | pilot plus full MiLB role context | 58% | `outputs/tables/mlb_market_pool_milb_role_context_v1.csv` | add injury/news/adaptation text plus contract and willingness variables |
| 6 | SSG fit ranking | locked with stronger market inputs | 28% | `docs/run_019_milb_all_and_historical_backfill.md` | build layer-weighted ranking only after market, translation, and risk joins are validated |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names can be used only as `research_lead` or `market_watch`.

The labels `shortlist_candidate` and `recommendation` remain locked until all six layers pass.
