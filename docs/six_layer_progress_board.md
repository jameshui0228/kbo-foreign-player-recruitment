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
| 2 | KBO foreign-player success/failure archetype mining | partial pass | 55% | `outputs/tables/kbo_foreign_archetype_summary_v0_1.csv` | expand historical pre-KBO MiLB/NPB/CPBL features and ID crosswalk |
| 3 | Candidate market construction | partial plus NPB official stats context | 72% | `outputs/tables/npb_player_market_features_2026_v1.csv` | add NPB nationality and salary/contract/buyout proxies, ABL roster/stats, news/manual availability checks, and market-watch MiLB coverage |
| 4 | KBO translation model | pass to pilot with new candidate context | 56% | `outputs/tables/mlb_market_pool_milb_role_context_v1.csv` | backfill comparable historical MiLB role/level context for prior KBO foreign players and rerun repeated CV |
| 5 | Failure risk model | pass to pilot with role context | 53% | `outputs/tables/mlb_market_pool_milb_role_context_v1.csv` | add injury/news/adaptation text plus contract and willingness variables |
| 6 | SSG fit ranking | locked with context inputs | 25% | `docs/candidate_release_gates_v1.md` | build layer-weighted ranking only after market, translation, and risk joins are validated |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names can be used only as `research_lead` or `market_watch`.

The labels `shortlist_candidate` and `recommendation` remain locked until all six layers pass.
