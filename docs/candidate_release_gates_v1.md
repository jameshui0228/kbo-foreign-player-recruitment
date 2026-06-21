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

## Run 023 Gate Audit

`run_023` built the locked SSG fit-preparation mart and confirmed that final candidate selection is still not allowed.

| gate | run_023 status | evidence |
|---|---|---|
| G1 SSG need | pass into fit-prep | Layer 1 feature contract is mapped to candidate-side proxy columns |
| G2 KBO archetype | fit-prep signal contract attached | hitter pilot component and diagnostic contexts are attached to the mart |
| G3 market | consolidated but partial | MLB hitter, MLB pitcher, and Asian-quota rows are in one mart |
| G4 KBO translation | hitter component only | hitter Savant pilot is usable; pitcher translation remains diagnostic only |
| G5 failure risk | visible but partial | pitcher damage/command and Asian feasibility gaps are visible, but medical/news/adaptation are missing |
| G6 final fit | locked fit-prep only | no shortlist or recommendation labels allowed |

Run 023 coverage:

| item | value |
|---|---:|
| fit-preparation mart rows | 2,723 |
| foreign hitter rows | 736 |
| foreign pitcher rows | 1,009 |
| Asian-quota rows | 978 |
| rows with final recommendation allowed | 0 |
| rows with shortlist label allowed | 0 |
| rows with candidate name release allowed | 0 |

Important interpretation:

- `fit_preparation_index` is a research triage index, not a recommendation score.
- Pitcher rows remain diagnostic-only.
- Asian-quota rows still need contract, salary, buyout, and agent/willingness checks.

## Run 024 Gate Audit

`run_024` added official roster, transaction, and market-realism gates to the locked fit-preparation mart.

| gate | run_024 status | evidence |
|---|---|---|
| G1 SSG need | unchanged | Layer 1 still feeds the fit-prep target features |
| G2 KBO archetype | unchanged | historical archetype context remains attached but not final |
| G3 market | market-realism gates attached | official MLB transaction and roster status are refreshed through 2026-06-21 |
| G4 KBO translation | unchanged | hitter component remains a pilot input; pitcher remains diagnostic |
| G5 failure risk | official proxies attached | roster/transaction medical signals and contract blockers are visible |
| G6 final fit | locked manual queue only | no shortlist or recommendation labels allowed |

Run 024 coverage:

| item | value |
|---|---:|
| official MLB transaction rows | 12,139 |
| official MLB roster rows | 8,197 |
| market-realism layer rows | 2,723 |
| foreign hitter manual-contact priority rows | 16 |
| foreign pitcher manual-contact priority rows | 30 |
| Asian-quota buyout/salary/agent-check rows | 154 |
| rows with final recommendation allowed | 0 |
| rows with shortlist label allowed | 0 |
| rows with candidate name release allowed | 0 |

Important interpretation:

- `market_realism_score` is a manual-verification triage field, not a recommendation score.
- Medical signals are public roster/transaction proxies only.
- Candidate-specific news, salary, opt-out, buyout, agent, and Korea-willingness checks remain blocking gaps.

## Run 025 Gate Audit

`run_025` added the first candidate-specific news pilot to the locked market-realism queue.

| gate | run_025 status | evidence |
|---|---|---|
| G1 SSG need | unchanged | Layer 1 still feeds fit-prep target features |
| G2 KBO archetype | unchanged | historical archetype context remains attached but not final |
| G3 market | English news pilot attached | 26 priority candidates searched through Google News RSS metadata |
| G4 KBO translation | unchanged | hitter component remains a pilot input; pitcher remains diagnostic |
| G5 failure risk | news-risk pilot attached | article title/description tags now flag medical, contract, overseas, and adaptation context |
| G6 final fit | locked news-enriched queue only | no shortlist or recommendation labels allowed |

Run 025 coverage:

| item | value |
|---|---:|
| pilot candidate rows | 26 |
| news metadata rows | 182 |
| candidate-name matched rows | 118 |
| usable news-signal rows | 119 |
| full worklist joined rows | 2,723 |
| rows with final recommendation allowed | 0 |
| rows with shortlist label allowed | 0 |
| rows with candidate name release allowed | 0 |

Important interpretation:

- English Google News RSS works for a small pilot and does not require Google API.
- Naver candidate-specific news is still missing because the shell environment does not contain Naver credentials.
- `candidate_news_status` is a manual-review signal, not a recommendation label.
