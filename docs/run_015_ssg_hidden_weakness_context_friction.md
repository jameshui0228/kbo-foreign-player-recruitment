# Run 015 SSG Hidden Weakness Context Friction

Date: 2026-06-14 KST

Layer focus: 1. SSG hidden weakness mining only.

Candidate policy: locked. This run does not recommend or shortlist players.

## Purpose

Run 014 found a game-script double bind: starter/bullpen stress plus OF/DH run-conversion failure. Run 015 tests whether that message still holds after adding context frictions that are closer to how games actually break:

- opponent starter handedness;
- unearned runs and extra-out damage;
- team and OF/DH GDP/CS run-kill events;
- opponent current strength;
- opponent current team pitching/offense ranks;
- park run environment.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_hidden_weakness_context_frame_v2.csv` | 61 | Run 014 game frame enriched with fielding, unearned, baserunning, opponent, park, and starter-hand context |
| `outputs/tables/ssg_hidden_weakness_context_interactions_v2.csv` | 688 | single, pair, and triple context-friction rules |
| `outputs/tables/ssg_hidden_weakness_context_message_upgrade_v2.csv` | 4 | upgraded Layer 1 message candidates |
| `outputs/tables/ssg_hidden_weakness_context_feature_contract_v2.csv` | 4 | refined candidate feature contract for later scoring |

Source snapshot: local STATIZ-derived 2026 data through the repository snapshot dated 2026-06-11.

## Upgraded Core Message

The SSG hidden weakness is now better described as:

> SSG's hidden weakness is a context-amplified game-script lock: right-handed-starter run conversion, extra-out damage, and run-killing OF/DH events combine with starter-length stress to remove the team's comeback path.

This is sharper than "needs more power" and also sharper than "needs a starter." It says:

- The pitcher target should be a load-bearing starter with traffic command and extra-out resilience.
- The hitter target should be a RHP-resistant OF/DH bat that avoids run-killing outs while keeping OBP plus damage.

## Evidence 1: RHP Context Double Bind

| rule | games | win% | avg run diff | interpretation |
|---|---:|---:|---:|---|
| OF RBI < 3 + opponent runs >= 6 + opponent starter right-handed | 20 | .100 | -5.10 | The OF run-conversion problem survives after attaching opponent starter handedness. |

This is the strongest broad support for the SSG-specific hitter message. The issue is not only that OF production is low; it is low in a game script that often needs a run trade.

## Evidence 2: RHP-Side Run-Killing Outs

| rule | games | win% | avg run diff | interpretation |
|---|---:|---:|---:|---|
| OF table-setter OBP <= .250 + opponent starter right-handed + OF/DH GDP or CS >= 1 | 9 | .000 | -5.11 | The hitter filter should punish run-killing outs, not only low OPS. |
| replacement-slot RBI < 3 + opponent starter right-handed + OF/DH GDP or CS >= 1 | 9 | .000 | -4.89 | OF/DH conversion and run-kill friction show up together. |

Candidate implication: the hitter screen should add GDP avoidance, baserunning decision quality, chase/whiff control, and contact shape. A home-run-only screen is too blunt.

## Evidence 3: Extra-Out Damage

| rule | games | win% | avg run diff | avg unearned runs | interpretation |
|---|---:|---:|---:|---:|---|
| high-leverage OF 0 RBI + unearned runs >= 1 | 8 | .000 | -4.50 | 2.00 | When extra-out damage appears, SSG often lacks OF/DH rescue value. |
| starter < 5 IP + OF RBI < 3 + unearned runs >= 1 | 6 | .000 | -5.67 | 2.50 | Short starts plus extra-out damage require a comeback profile SSG often does not have. |
| starter < 5 IP + opponent starter right-handed + unearned runs >= 1 | 5 | .000 | -6.40 | 2.80 | The pitcher need is also about surviving messy innings, not just clean ERA. |

Candidate implication: the foreign pitcher should have a command floor, low free-pass traffic, and enough workload stability to absorb imperfect defensive innings.

## Evidence 4: Top-Opponent Margin Of Error

| rule | games | win% | avg run diff | interpretation |
|---|---:|---:|---:|---|
| starter < 5 IP + high-leverage OF 0 RBI + opponent top-3 win% | 6 | .000 | -5.83 | Against good opponents, SSG has almost no margin for both a short start and OF silence. |

Candidate implication: this supports reliability over one-dimensional upside. The player type should retain value in playoff-like opponent contexts.

## What Changed From Run 014

Run 014 message:

- SSG has a game-script double bind: starter/bullpen stress plus OF/DH run-conversion failure.

Run 015 upgrade:

- The bind is context-amplified by right-handed starters, run-killing OF/DH outs, unearned-run states, and top-opponent stress.
- The hitter target is no longer just "RHP-resistant OBP plus damage"; it is "RHP-resistant OBP plus damage without run-kill events."
- The pitcher target is no longer just "traffic command"; it is "traffic command and extra-out resilience."

## Updated Layer 1 Conclusion

Layer 1 moves from 84% to 88%.

The message is now strong enough to freeze a first feature contract for later candidate scoring. It is not yet final-presentation locked because the dataset still needs a refreshed post-2026-06-11 snapshot and stronger public defensive/baserunning or play-by-play validation.

## Six-Layer Progress After Run 015

| no. | layer | progress | movement | candidate status |
|---:|---|---:|---|---|
| 1 | SSG hidden weakness mining | 88% | 84% -> 88% | feature-contract ready, still needs refresh |
| 2 | KBO foreign-player success/failure archetype mining | 55% | unchanged | not enough for final names |
| 3 | Candidate market construction | 68% | unchanged | research leads only |
| 4 | KBO translation model | 56% | unchanged | pilot only |
| 5 | Failure risk model | 53% | unchanged | pilot only |
| 6 | SSG fit ranking | 25% | unchanged | locked |

## Validation

- `src/modeling/mine_ssg_hidden_weakness_context_v2.py` was py-compiled.
- The script was rerun and reproduced all four output tables above.
- CSV row counts were checked after generation.

## Caveats

- The game frame still has 61 SSG games.
- Inning-line `E` and pitcher `R - ER` are useful proxies, but not a substitute for true play-by-play defense.
- GDP/CS are useful run-kill proxies, but not a full baserunning model.
- Park run environment is estimated from current 2026 `s_code` game totals and should be refreshed.
- Opponent quality is snapshot-based, not game-date rolling strength.
- The local STATIZ-derived snapshot ends at 2026-06-11. A refresh is needed before final presentation.
- Candidate names remain locked until layers 2-6 clear their gates.
