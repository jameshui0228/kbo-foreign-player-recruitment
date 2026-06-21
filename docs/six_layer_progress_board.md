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
| 3 | Candidate market construction | manual feasibility source worklist built | 92% | `outputs/tables/manual_feasibility_source_worklist_v0_1.csv` | load Naver credentials for Korean candidate news and fill salary, opt-out, transfer-fee, buyout, agent, and Korea-willingness source lanes |
| 4 | KBO translation model | hitter component in fit-prep mart | 80% | `outputs/tables/ssg_fit_preparation_mart_v0_1.csv` | keep hitter component as pilot input and build pitcher translation only after stronger risk/context variables |
| 5 | Failure risk model | manual risk source lanes built | 82% | `outputs/tables/manual_feasibility_source_lane_summary_v0_1.csv` | run Korean/Naver candidate news and fill medical/adaptation/Korea-willingness source lanes |
| 6 | SSG fit ranking | locked manual feasibility queue built | 68% | `docs/run_027_korean_news_and_feasibility_worklist_v0_1.md` | fill feasibility source lanes before any shortlist/recommendation labels |

## Reporting Rule

Every future work update should include:

- which layer is being worked on;
- before/after progress if a layer moves;
- whether candidate names are still locked;
- the next blocking gap.

## Current Candidate Policy

Candidate names can be used only as `research_inventory` or `market_watch`.

The labels `shortlist_candidate` and `recommendation` remain locked until all six layers pass.
