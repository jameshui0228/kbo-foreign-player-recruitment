# Candidate Release Gates v1

Generated: 2026-06-12 KST

## Purpose

This project should not jump from SSG need mining to player recommendations.

Candidate names can appear only as temporary research leads until all five model layers are built and checked:

1. SSG hidden-need mining.
2. KBO foreign-player success/failure archetype mining.
3. Candidate market construction.
4. KBO translation model.
5. Failure-risk model.

## Current Status

| layer | current status | candidate impact |
|---|---|---|
| SSG hidden-need mining | v0.2 pitcher message promoted | can define feature targets |
| KBO success/failure archetype mining | v0.1 built from 2023-2025 outcome-attached rows | can define historical archetype targets, but needs deeper features |
| Candidate market construction | MLB roster/Savant v1 only | incomplete; names are not final |
| KBO translation model | not built | no candidate can be recommended yet |
| Failure-risk model | not built | no candidate can be recommended yet |

## Rule

No player can be called a recommendation, shortlist member, or final candidate until all gates below pass.

## Required Gates

| gate | required output | pass condition |
|---|---|---|
| G1 SSG need | `ssg_hidden_state_*` tables | message survives time, segment, and game-impact checks |
| G2 KBO archetype | `kbo_foreign_archetype_*` tables | target success/failure archetypes are defined by role |
| G3 market | candidate market tables by MLB/MiLB, NPB, CPBL, ABL | active/40-man/contract/injury/age/slot feasibility is verified |
| G4 KBO translation | translation score tables | pre-arrival features explain or separate historical KBO outcomes better than baselines |
| G5 failure risk | failure-risk score tables | model flags historical failures and current medical/role/sample risks |
| G6 final fit | slot ranking tables | player solves SSG need, matches KBO success archetype, avoids failure archetype, and passes market gate |

## Candidate Name Policy

Use these labels only:

| label | meaning |
|---|---|
| `research_lead` | a name worth checking manually; not a recommendation |
| `market_watch` | interesting profile but gate failure or access issue |
| `unavailable_benchmark` | useful for calibration, not realistic |
| `shortlist_candidate` | allowed only after G1-G6 pass |
| `recommendation` | allowed only after manual verification |

## Immediate Correction

`run_009` generated pitcher research leads too early for final candidate discussion. Those names should be treated only as a sandbox test proving that the promoted SSG pitcher message can be mapped to candidate features.

The next real work is not final player selection. The next real work is:

1. expand candidate market data beyond MLB Savant and roster status;
2. build a KBO translation model;
3. build a failure-risk model;
4. then reopen candidate scoring.

## Run 010 Gate Audit

`run_010` built the first gate-level marts and confirmed that final candidate selection is still locked.

| gate | run_010 status | evidence |
|---|---|---|
| G1 SSG need | pass | pitcher-first decision table passed |
| G2 KBO archetype | partial pass | outcome-side archetypes exist |
| G3 market | partial | MLB current-org pools exist, but Asian quota/free-agent/transaction layers are missing |
| G4 KBO translation | blocked by sample | only 27 of 87 eligible historical rows have pre-KBO Savant features |
| G5 failure risk | blocked by sample/context | failure-risk mart exists, but training is not defensible yet |
| G6 final fit | locked | no shortlist/recommendation labels allowed |

Training-readiness thresholds were not met:

| role | eligible rows | pre-KBO Savant rows | training-ready |
|---|---:|---:|---|
| hitter | 29 | 7 | no |
| pitcher | 58 | 20 | no |
| all roles | 87 | 27 | no |

The next unlock step is historical pre-arrival feature expansion, not candidate naming.

## Run 011 Gate Audit

`run_011` added clean 2022 Savant data and trained role-specific pilot KBO translation/failure-risk models.

| gate | run_011 status | evidence |
|---|---|---|
| G1 SSG need | pass | pitcher-first decision table passed |
| G2 KBO archetype | partial pass | outcome-side archetypes exist |
| G3 market | partial | MLB current-org pools exist, but Asian quota/free-agent/transaction layers are still missing |
| G4 KBO translation | pass to pilot | hitter and pitcher role-specific trainable rows now meet minimum thresholds |
| G5 failure risk | pass to pilot | role-specific failure-risk models now exist |
| G6 final fit | locked | candidate ranking remains blocked by market and manual verification gaps |

Updated training-readiness:

| role | eligible rows | pre-KBO Savant rows | training-ready |
|---|---:|---:|---|
| hitter | 42 | 22 | yes |
| pitcher | 86 | 33 | yes |
| all roles | 128 | 55 | no, below pooled 60-row threshold |

Model caution:

- Hitter models are stable enough for pilot translation/failure-risk use.
- Pitcher models need extra non-public-style context before candidate release; repeated CV does not promote public-Savant-only pitcher models.
- Final names stay locked until G3 is complete and pitcher context is expanded.

## Run 012 Gate Audit

`run_012` added the first real market-access layers beyond MLB roster status.

| gate | run_012 status | evidence |
|---|---|---|
| G1 SSG need | pass | pitcher-first decision table remains the promoted need hypothesis |
| G2 KBO archetype | partial pass | archetypes exist, but pre-arrival explanation still needs MiLB/NPB/CPBL context |
| G3 market | partial plus secured initial layers | MLB official transaction feed and NPB/CPBL roster inventory now exist |
| G4 KBO translation | pass to pilot | role-specific pilots remain available |
| G5 failure risk | pass to pilot | failure-risk pilots remain available, but medical/adaptation context is still missing |
| G6 final fit | locked | no shortlist/recommendation labels allowed |

Run 012 market coverage:

| market layer | rows | secured status | blocker |
|---|---:|---|---|
| MLB replacement pitcher pool | 1,009 | official transactions attached | contract/salary, medical, Korea-willingness, manual scouting |
| MLB outfield-priority hitter pool | 736 | official transactions attached | contract/salary, medical, Korea-willingness, manual scouting |
| injury/replacement transaction pool | 1,745 | transaction movement secured | non-MLB free agents, opt-outs, current assignment, real-time news |
| Asian-quota NPB/CPBL inventory | 978 | official roster inventory secured | NPB nationality, ABL, salary/buyout/contract feasibility |

Important data-quality correction:

- MLB Stats API code `DES` is Designated for Assignment.
- MLB Stats API code `DFA` is Declared Free Agency.
- Run 012 separates these codes so free agency is not misread as a true DFA signal.

Candidate policy is unchanged:

- `research_lead_only_manual_check_required` is allowed for internal investigation.
- `shortlist_candidate` and `recommendation` are still not allowed.

## Run 013 Gate Audit

`run_013` added MiLB role/level continuity for the rows most worth immediate follow-up.

| gate | run_013 status | evidence |
|---|---|---|
| G1 SSG need | pass | no change |
| G2 KBO archetype | partial pass | no direct historical backfill yet |
| G3 market | partial plus with MiLB context | research-lead and medical-hold rows now have MiLB role/level context |
| G4 KBO translation | pass to pilot with new candidate context | candidate-side MiLB variables exist; historical comparable features still need backfill |
| G5 failure risk | pass to pilot with role context | stale-track, role-mismatch, starter-stretch, and PA-sample risks are now measurable |
| G6 final fit | locked | no shortlist/recommendation labels allowed |

Run 013 coverage:

| item | value |
|---|---:|
| candidate rows requested | 883 |
| level-by-player requests | 4,415 |
| MiLB stat rows | 9,560 |
| MiLB feature rows | 1,745 |
| pitcher `current_aaa_starter_load` rows | 76 |
| pitcher `current_aaa_swing_or_multi_inning` rows | 79 |
| hitter `current_aaa_regular` rows | 85 |
| hitter `current_aaa_part_time` rows | 79 |

Important scope label:

- `not_collected_in_run_013_scope` means the row was outside the collection scope.
- `no_milb_stats_found` means the row was requested but no MiLB split was returned.

Final candidate names remain locked because contract, medical/news, adaptation, willingness, ABL, and historical MiLB backfill are still incomplete.
