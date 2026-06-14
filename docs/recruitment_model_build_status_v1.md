# Recruitment Model Build Status v1

Generated: 2026-06-12 KST

## Core Decision

Final candidate selection is still locked.

This is not because there is no candidate pool. After Run 011, role-specific KBO translation and failure-risk pilot models are trainable. After Run 012, MLB transaction movement and NPB/CPBL roster inventory also exist. After Run 013, research-lead and medical-hold rows have MiLB role/level continuity context. The remaining blocker is that contract, salary, medical/news text, willingness, ABL, NPB nationality, and historical MiLB backfill layers are still incomplete.

The project should continue in this order:

1. expand market and non-MLB player context;
2. add Asian quota eligibility and contract feasibility;
3. add pitcher role/medical/adaptation context;
4. only then reopen candidate ranking.

## What Run 010 Built

Run 010 created the gate-level data marts needed before serious candidate selection:

| output | purpose |
|---|---|
| `outputs/tables/historical_kbo_savant_name_match_audit_v0_1.csv` | audit historical KBO foreign-player names against MLB Savant feature tables |
| `outputs/tables/kbo_translation_feature_mart_v0_1.csv` | historical KBO outcome rows with pre-KBO Savant features where available |
| `outputs/tables/failure_risk_feature_mart_v0_1.csv` | failure-risk target mart using the same leakage-safe pre-arrival features |
| `outputs/tables/kbo_translation_readiness_v0_1.csv` | training-readiness thresholds by role |
| `outputs/tables/candidate_market_coverage_v0_2.csv` | current market coverage and missing market layers |
| `outputs/tables/recruitment_gate_status_v1.csv` | G1-G6 release gate status |

## Current Training Readiness

Run 011 improved historical supervised modeling coverage by adding clean 2022 Savant data:

| role | eligible labeled rows | pre-KBO Savant matched rows | coverage rate | success rows | failure rows | training ready |
|---|---:|---:|---:|---:|---:|---|
| hitter | 42 | 22 | 52.4% | 13 | 8 | yes |
| pitcher | 86 | 33 | 38.4% | 14 | 17 | yes |
| all roles | 128 | 55 | 43.0% | 27 | 25 | no, below 60-row pooled threshold |

The main issue is no longer whether role-specific pilots can be trained. They can. The issue is whether those pilots are stable enough to release candidate names.

Model validation says the hitter signal is more stable than the pitcher signal. For pitchers, public Savant-only models improve on the one-step time holdout but fail the repeated CV stability check. That means the pitcher thesis needs more context: MiLB/NPB/CPBL workload, role continuity, medical risk, adaptation evidence, and current market access.

## Gate Status

| gate | status | interpretation |
|---|---|---|
| G1 SSG hidden-need mining | pass | pitcher-first SSG message can define target features |
| G2 KBO success/failure archetype mining | partial pass | outcome-side archetypes exist, but pre-arrival explanation is not built |
| G3 candidate market construction | partial plus | MLB official transactions and NPB/CPBL roster inventory now exist; contract/manual feasibility layers missing |
| G4 KBO translation model | pass to pilot | role-specific trainable rows and pilot models exist |
| G5 failure-risk model | pass to pilot | role-specific failure-risk models exist |
| G6 final fit and shortlist | locked | all candidate names remain research leads only |

## What This Means For The Project Message

The current pitcher-first SSG message is still the best promoted message:

> SSG should prioritize a traffic-command, load-bearing foreign starter who prevents innings from exploding after traffic and turns short-start games into 5-6 inning games.

But this is not yet a final recruitment model. It is the SSG need hypothesis that the next modeling layers should test against historical KBO success/failure and current market feasibility.

The hitter and Asian-quota messages are not ready for final wording because the market and translation layers are weaker:

- Hitter: only 7 historical pre-KBO Savant-matched rows are available.
- Asian quota: no NPB/CPBL/ABL candidate market table exists yet.

## Run 012 Market Update

Run 012 added:

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/mlb_transactions_latest.csv` | 11,799 | official MLB transaction movement from 2025-10-01 to 2026-06-13 |
| `outputs/tables/mlb_replacement_market_status_v1.csv` | 1,745 | transaction-aware market status for pitcher and outfield-priority hitter pools |
| `outputs/tables/npb_official_roster_2026_v1.csv` | 810 | official current NPB roster inventory |
| `outputs/tables/cpbl_official_roster_2026_v1.csv` | 168 | official current CPBL roster inventory with nationality details |
| `outputs/tables/asian_quota_market_status_v1.csv` | 978 | NPB/CPBL Asian-quota market watch board |
| `outputs/tables/candidate_market_coverage_v0_3.csv` | 6 | updated G3 market coverage board |

Run 012 also fixed a transaction-code issue: MLB `DES` means Designated for Assignment, while MLB `DFA` means Declared Free Agency.

## Run 013 MiLB Context Update

Run 013 added:

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/milb_market_pool_stats_research_plus_medical_v1.csv` | 9,560 | raw MiLB year-by-year rows for research-lead and medical-hold candidates |
| `outputs/tables/milb_market_pool_stats_request_audit_research_plus_medical_v1.csv` | 4,415 | request-level audit across AAA/AA/High-A/Single-A/Rookie |
| `outputs/tables/mlb_market_pool_milb_role_context_v1.csv` | 1,745 | candidate-side role/level context joined to the market pool |
| `outputs/tables/mlb_market_pool_milb_role_context_summary_v1.csv` | 31 | summary by slot, policy, and role-continuity bucket |

The main new modeling variables are:

- current AAA starter load;
- current AAA swing/multi-inning role;
- current AAA bullpen-only track;
- no live 2026 MiLB track;
- hitter current AAA PA bucket;
- stale or not-collected scope labels.

This improves candidate-side realism but does not yet retrain the historical KBO translation/failure-risk models.

## Required Next Data

To unlock G4-G5, collect or build these tables:

| priority | data | why it matters |
|---:|---|---|
| 1 | historical pre-KBO MLB/MiLB batting/pitching stats for 2017-2025 KBO foreign players | improves pitcher stability beyond public MLB Statcast |
| 1 | MLBAM/FanGraphs/Baseball-Reference ID crosswalk for KBO foreign players | reduces name-matching misses and lets us join older data safely |
| 1 | MiLB level/role and current assignment for transaction-screened players | separates real availability from transaction noise |
| 1 | NPB/CPBL/ABL 2025-2026 roster, nationality, salary/contract status | NPB/CPBL roster exists; ABL, salary, buyout, and NPB nationality remain |
| 2 | full-text article/interview corpus with medical/adaptation quotes | adds failure-risk variables that public stat lines cannot capture |
| 2 | pitch mix/stuff pre-arrival data beyond MLB Savant where possible | improves pitcher translation model |
| 3 | Munhak weather/park context and KBO ABS/pitch-location data | improves fine-grained SSG fit explanation |

## Candidate Policy After Run 010

No player should be called a recommendation, shortlist member, or final candidate.

The correct labels are:

- `research_lead`: can be manually investigated but not presented as an answer.
- `market_watch`: interesting but blocked by access, role, sample, or context gaps.
- `shortlist_candidate`: not allowed until G1-G6 pass.

## Next Modeling Step

The next serious run should be:

`run_012`: build the market and non-MLB context layers that still lock candidate release.

Minimum acceptable target:

- Asian quota market table with nationality, prior/current Asian league status, salary/contract status;
- replacement market table with DFA/released/free-agent/MiLB transaction status;
- pitcher context features for workload continuity, injury, role, and adaptation.

Only after that should candidate ranking be reopened.
