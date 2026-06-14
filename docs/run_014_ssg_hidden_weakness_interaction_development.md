# Run 014 SSG Hidden Weakness Interaction Development

Date: 2026-06-14 KST

Layer focus: 1. SSG hidden weakness mining only.

Candidate policy: locked. This run does not recommend or shortlist players.

## Decision Frame

The goal of this run was to make the SSG-specific message sharper than a generic "needs power" or "needs pitching" claim. The analysis therefore looked for a weakness that appears only after combining:

- game-level run prevention stress;
- starter length and bullpen workload;
- OF/DH run-conversion outcomes;
- role-by-context hitter splits;
- count-pressure survival;
- pitcher context concentration.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_hidden_weakness_game_frame_v1.csv` | 61 | SSG 2026 game frame with batting role aggregates and pitching workload flags |
| `outputs/tables/ssg_hidden_weakness_game_interactions_v1.csv` | 150 | single and pairwise game-state rules scored by loss lift and interaction lift |
| `outputs/tables/ssg_hidden_weakness_role_context_v1.csv` | 17 | role/context evidence that translates hidden weaknesses into target features |
| `outputs/tables/ssg_hidden_weakness_message_candidates_v1.csv` | 4 | candidate SSG hidden-weakness messages |
| `outputs/tables/ssg_hidden_weakness_need_contract_v1.csv` | 4 | feature contract for later player scoring |

Source snapshot: local STATIZ-derived 2026 data through the repository snapshot dated 2026-06-11.

## Core Finding

The sharper message is:

> SSG's hidden weakness is not generic outfield power. It is a game-script double bind: when starter length or bullpen command collapses, SSG does not have enough high-leverage OF/DH run conversion, especially against right-handed starters, to reopen the game.

This keeps the pitcher-first priority, but it changes why pitcher is first and what type of hitter should be pursued.

## Evidence 1: Game-Script Double Bind

Top interaction rules:

| rule | games | win% | complement win% | avg run diff | why it matters |
|---|---:|---:|---:|---:|---|
| bullpen 4+ BB and high-leverage OF 0 RBI | 7 | .000 | .481 | -4.86 | command traffic plus OF/DH conversion void creates a no-recovery script |
| bullpen 3+ ER and OF RBI < 3 | 17 | .000 | .591 | -5.82 | run prevention failure becomes unrecoverable when OF run conversion is low |
| starter < 5 IP and team runs <= 3 | 12 | .000 | .531 | -5.67 | short starts need offensive rescue that SSG often does not supply |
| starter disaster and OF RBI < 3 | 15 | .067 | .543 | -5.20 | starting-pitching failure plus OF conversion failure is worse than either alone |
| OF RBI < 3 and opponent runs >= 6 | 24 | .083 | .649 | -5.00 | SSG does not reliably trade runs when the game gets high-scoring |

Interpretation: the hidden problem is an interaction, not a single leaderboard rank. A new foreign pitcher reduces the frequency of the bad game script. A new foreign hitter should reduce the OF/DH low-conversion tail when that script appears.

## Evidence 2: Hitter Message Is RHP-Specific

The outfield weakness is not "all outfield offense." It concentrates in specific roles and opponent-starter handedness:

| context | sample | observed | rank context |
|---|---:|---|---|
| OF 3-5 run-production vs right-handed starter | 187 PA | OPS .595, OBP .294, SLG .301, ISO .084 | OPS rank 10/10, OBP rank 10/10, SLG rank 10/10 |
| OF 1-2 table-setters vs right-handed starter | 83 PA | OPS .526, OBP .205, SLG .321, ISO .123 | OPS rank 10/10, OBP rank 10/10, SLG rank 8/10 |
| OF 3-5 run-production vs left-handed starter | 82 PA | OPS 1.048, OBP .463, SLG .585, ISO .231 | OPS rank 2/10, OBP rank 2/10, SLG rank 2/10 |

Interpretation: this is a right-handed-starter problem in high-leverage OF roles, not a blanket OF problem. The hitter screen should therefore penalize empty power and platoon-only lefty-mashing profiles.

## Evidence 3: Count-Pressure Survival

Replacement-relevant OF/DH roles leak value after count pressure:

| context | sample | observed |
|---|---:|---|
| OF lower or mixed usage in two strikes | 277 PA | OPS .573, OBP .282, K% .336, RBI/PA .087 |
| DH primary or bridge in two strikes | 130 PA | OPS .459, OBP .277, K% .515, RBI/PA .077 |
| OF high-leverage usage in two strikes | 113 PA | OPS .466, OBP .221, K% .416, RBI/PA .142 |

Interpretation: the hitter target is not just home-run upside. It is RHP-resistant OBP plus damage with two-strike survival and chase/contact stability.

## Evidence 4: Pitcher Need Is Traffic Command

The pitcher message remains strong, but now the wording is more specific:

| context | sample | observed | rank context |
|---|---:|---|---|
| vs right-handed orthodox pitcher context | 1,281 TBF | ERA 5.85, WHIP 1.60, OPSA .806 | ERA/WHIP/OPSA rank 10/10 |
| early innings 1-3 | 859 TBF | ERA 5.81, WHIP 1.64, OPSA .790 | ERA/WHIP/OPSA rank 10/10 |
| runners in scoring position | 754 TBF | ERA 15.13, WHIP 1.78, OPSA .847 | ERA/WHIP/OPSA rank 10/10 |
| runners on base | 1,274 TBF | ERA 9.75, WHIP 1.56, OPSA .800 | ERA/WHIP/OPSA rank 10/10 |

Interpretation: SSG should prefer a load-bearing starter with traffic command, first-pitch/zone stability, walk suppression, and damage control with runners on. Pure strikeout ceiling is not enough if it comes with traffic volatility.

## Message Candidates

| id | priority | message score | message |
|---|---|---:|---|
| L1_M01 | foreign hitter | 19 | SSG's outfield problem is not generic power; it is high-leverage OF/DH run conversion against right-handed starters. |
| L1_M03 | foreign pitcher then hitter | 19 | SSG's game script breaks when starter length and outfield run conversion fail together. |
| L1_M04 | foreign pitcher | 19 | SSG needs a starter who prevents traffic from becoming crooked innings in the ABS-era strike-zone environment. |
| L1_M02 | foreign hitter | 16 | The replacement-relevant OF/DH slots leak value after count pressure; SSG needs two-strike survival, not only first-pitch damage. |

## Updated Layer 1 Conclusion

Layer 1 moves from 75% to 84%.

The message is now strong enough to define player-screening features, but not strong enough to unlock final names. The next confidence jump should come from adding defense, baserunning, park, opponent quality, and a refreshed 2026 STATIZ/current-game snapshot.

## Six-Layer Progress After Run 014

| no. | layer | progress | movement | candidate status |
|---:|---|---:|---|---|
| 1 | SSG hidden weakness mining | 84% | 75% -> 84% | target-feature ready, still refining |
| 2 | KBO foreign-player success/failure archetype mining | 55% | unchanged | not enough for final names |
| 3 | Candidate market construction | 68% | unchanged | research leads only |
| 4 | KBO translation model | 56% | unchanged | pilot only |
| 5 | Failure risk model | 53% | unchanged | pilot only |
| 6 | SSG fit ranking | 25% | unchanged | locked |

## Validation

- `src/modeling/mine_ssg_hidden_weakness_interactions_v1.py` was py-compiled.
- The script was rerun and reproduced all five output tables above.
- Row counts were checked after generation.

## Caveats

- The game frame has 61 games, so interaction rules should be treated as descriptive evidence rather than causal proof.
- Defense, baserunning, park, exact game state, pitch-by-pitch sequencing, and opponent quality are not fully attached yet.
- The local STATIZ-derived snapshot ends at 2026-06-11. A refresh is needed before final presentation.
- Candidate names remain locked until layers 2-6 clear their gates.
