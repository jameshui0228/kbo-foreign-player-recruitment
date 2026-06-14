# Run 012 Market Layers And Context

Generated: 2026-06-14 KST  
Endpoint end date: 2026-06-13

## Objective

Run 012 does not release candidate names.

The goal is to unlock the weakest part of G3 candidate-market construction:

1. official MLB transaction movement for replacement foreign-player market access;
2. NPB and CPBL roster inventory for Asian-quota market construction;
3. a refreshed gate board showing what is now secured and what still blocks a shortlist.

## Sources Collected

| source | output | rows | role in model |
|---|---:|---:|---|
| MLB Stats API transactions, 2025-10-01 to 2026-06-13 | `outputs/tables/mlb_transactions_latest.csv` | 11,799 | DFA, release, declared free agency, minor-league contract, option, injury, rehab, and assignment movement |
| MLB replacement market join | `outputs/tables/mlb_replacement_market_status_v1.csv` | 1,745 | attaches transaction movement to current pitcher and outfield-priority hitter pools |
| NPB official English 2026 rosters | `outputs/tables/npb_official_roster_2026_v1.csv` | 810 | official current Asian-league affiliation |
| CPBL official English rosters and player pages | `outputs/tables/cpbl_official_roster_2026_v1.csv` | 168 | official current Asian-league affiliation plus nationality, birth date, height/weight, T/B |
| NPB foreign-player seed | `outputs/tables/npb_foreign_player_seed_wikipedia_v1.csv` | 42 | non-official nationality seed only |
| CPBL foreign-player seed | `outputs/tables/cpbl_foreign_player_seed_wikipedia_v1.csv` | 32 | non-official cross-check seed |
| Asian-quota market inventory | `outputs/tables/asian_quota_market_status_v1.csv` | 978 | current NPB/CPBL market watch board |
| Market coverage board | `outputs/tables/candidate_market_coverage_v0_3.csv` | 6 | G3 status board |

## MLB Transaction Findings

The official MLB transaction feed returned 11,799 rows.

Top movement types:

| type | rows | interpretation |
|---|---:|---|
| `ASG` Assigned | 3,009 | assignment movement; useful for current org/level status but not enough alone |
| `SC` Status Change | 2,172 | activation, injured list, other roster state changes |
| `SFA` Signed as Free Agent | 1,958 | 1,772 rows contain minor-league contract text |
| `OPT` Optioned | 790 | 40-man movement; medium/low access unless later released |
| `DES` Designated for Assignment | 353 | true DFA signal |
| `DFA` Declared Free Agency | 260 | not designated-for-assignment; this was explicitly separated in code |
| `OUT` Outrighted | 219 | useful high-follow signal after roster removal |

Quality correction:

- MLB API code `DES` is Designated for Assignment.
- MLB API code `DFA` is Declared Free Agency.
- `src/data/collect_mlb_transactions.py` was corrected so declared free agency is not confused with DFA.

## Replacement Market Status

The transaction layer now covers the existing 1,745 current candidate-pool rows:

| slot | rows | research-lead/manual-check rows | market-watch rows | medical-hold rows | recent release/DFA bucket |
|---|---:|---:|---:|---:|---:|
| regular foreign pitcher | 1,009 | 265 | 465 | 279 | 109 |
| outfield-priority foreign hitter | 736 | 176 | 397 | 163 | 73 |
| all replacement/injury-replacement pool rows | 1,745 | 441 | 862 | 442 | 182 |

Interpretation:

- This is now a real market-access screen, not just a Statcast leaderboard.
- It still cannot produce final recommendations because transaction status is not the same as contract feasibility.
- Pitcher names remain especially locked because Run 011 showed public Savant-only pitcher models are unstable under repeated CV.

## Asian-Quota Market Status

The NPB/CPBL inventory now has 978 current-roster rows:

| league | rows | nationality pass | nationality fail | nationality unknown |
|---|---:|---:|---:|---:|
| CPBL | 168 | 151 | 17 | 0 |
| NPB | 810 | 3 | 35 | 772 |
| total | 978 | 154 | 52 | 772 |

Interpretation:

- CPBL is stronger for immediate Asian-quota screening because official player pages expose nationality.
- NPB official roster pages verify current affiliation but do not expose nationality. NPB nationality therefore remains blocked for most rows unless verified from another official or manually trusted source.
- Active NPB/CPBL roster status should be treated as low-access until salary, buyout, contract, posting/release, and willingness checks are added.

## Gate Update

| gate | Run 012 status | decision |
|---|---|---|
| G1 SSG need | pass | pitcher-first SSG message remains usable |
| G2 KBO archetype | partial pass | archetypes exist but still need richer pre-arrival features |
| G3 market | partial plus secured initial layers | MLB transaction and NPB/CPBL inventory layers are now built |
| G4 KBO translation | pass to pilot | role-specific pilots exist |
| G5 failure risk | pass to pilot | failure-risk pilots exist |
| G6 final shortlist | locked | final names are still blocked |

## Remaining Blocks

The next run should not jump to names. It should add:

- current MiLB stats and level/role continuity for the 441 research-lead rows;
- injury/news/adaptation full-text features for the 442 medical-hold rows;
- contract, salary, opt-out, and Korea-willingness checks for market-access rows;
- ABL coverage and NPB nationality verification for Asian-quota rows;
- a player-level manual scouting queue with evidence links before any public shortlist wording.

## Source URLs

- MLB Stats API transactions: https://statsapi.mlb.com/api/v1/transactions?sportId=1&startDate=2025-10-01&endDate=2026-06-13
- NPB official roster example: https://npb.jp/bis/eng/teams/rst_g.html
- CPBL official team page example: https://en.cpbl.com.tw/team?ClubNo=AKP
- NPB foreign-player seed: https://en.wikipedia.org/wiki/List_of_current_foreign_Nippon_Professional_Baseball_players
- CPBL foreign-player seed: https://en.wikipedia.org/wiki/List_of_current_foreign_CPBL_players
