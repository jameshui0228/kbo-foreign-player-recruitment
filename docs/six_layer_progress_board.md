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
| 2 | KBO foreign-player success/failure archetype mining | fit-prep signal contract attached | 73% | `outputs/tables/ssg_fit_preparation_feature_contract_v0_1.csv` | expand historical ID crosswalk to 2017-2022, add NPB/CPBL pre-arrival context, and calibrate final fit rules |
| 3 | Candidate market construction | candidate-news pilot attached | 89% | `outputs/tables/ssg_market_realism_news_join_v0_1.csv` | load Naver credentials for Korean candidate news and add salary, opt-out, transfer-fee, buyout, agent, and Korea-willingness sources |
| 4 | KBO translation model | hitter component in fit-prep mart | 80% | `outputs/tables/ssg_fit_preparation_mart_v0_1.csv` | keep hitter component as pilot input and build pitcher translation only after stronger risk/context variables |
| 5 | Failure risk model | English candidate-news risk pilot attached | 78% | `outputs/tables/candidate_news_signal_summary_v0_1.csv` | run Korean/Naver candidate news and add full medical/adaptation/Korea-willingness checks |
| 6 | SSG fit ranking | locked news-enriched work queue pilot built | 63% | `docs/run_025_candidate_news_pilot_v0_1.md` | expand news and salary/contract verification before any shortlist/recommendation labels |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names can be used only as `research_inventory` or `market_watch`.

The labels `shortlist_candidate` and `recommendation` remain locked until all six layers pass.
