# Run 016 SSG Hidden Weakness Robustness Validation

Date: 2026-06-14 KST

Layer focus: 1. SSG hidden weakness mining only.

Candidate policy: locked. This run does not recommend or shortlist players.

## Purpose

Run 016 stress-tests the Run 015 context-friction messages before treating Layer 1 as a feature contract for later candidate scoring.

Instead of adding another new narrative, this run asks:

- Does the message survive time-split checks?
- Does it collapse if one opponent is removed?
- Is the rule worse than random masks with the same prevalence?
- Is it sharper than generic controls such as "OF HR zero" or "OF RBI < 3 only"?
- Which sub-message should be promoted to core and which should stay support-only?

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_hidden_weakness_robustness_rules_v3.csv` | 4 | Full-sample stats for the four Run 015 rules |
| `outputs/tables/ssg_hidden_weakness_negative_controls_v3.csv` | 5 | Generic or context-only controls |
| `outputs/tables/ssg_hidden_weakness_time_split_v3.csv` | 28 | Full, half-season, and month split checks |
| `outputs/tables/ssg_hidden_weakness_leave_one_opponent_v3.csv` | 36 | Leave-one-opponent-out sensitivity |
| `outputs/tables/ssg_hidden_weakness_bootstrap_permutation_v3.csv` | 4 | Bootstrap and permutation robustness |
| `outputs/tables/ssg_hidden_weakness_robustness_decisions_v3.csv` | 4 | Promote/support decision table |
| `outputs/tables/ssg_hidden_weakness_final_message_v3.csv` | 1 | Near-final Layer 1 message and feature contract |

## Core Results

| rule | games | win% | avg run diff | decision |
|---|---:|---:|---:|---|
| OF RBI < 3 + opponent 6+ runs + right-handed opponent starter | 20 | .100 | -5.10 | promote core |
| OF table-setter OBP <= .250 + right-handed opponent starter + OF/DH GDP or CS | 9 | .000 | -5.11 | promote core |
| high-leverage OF 0 RBI + at least 1 unearned run allowed | 8 | .000 | -4.50 | promote core |
| starter < 5 IP + high-leverage OF 0 RBI + opponent top-3 win pct | 6 | .000 | -5.83 | support only |

Interpretation: three rules are strong enough to become Layer 1 core evidence. The top-opponent rule remains useful, but sample size is 6, so it should stay support-only.

## Bootstrap And Permutation Check

| rule | bootstrap median win% | bootstrap median run diff | permutation p, win% as low or lower | permutation p, run diff as low or lower |
|---|---:|---:|---:|---:|
| RHP low OF conversion run trade | .091 | -5.11 | .000 | .000 |
| RHP OF/DH run-kill | .000 | -5.10 | .005 | .003 |
| extra-out high OF void | .000 | -4.50 | .008 | .012 |
| top opponent short start OF void | .000 | -5.86 | .030 | .007 |

Interpretation: the three promoted rules do not look like random prevalence artifacts. The support-only rule is directionally strong but still sample-limited.

## Negative Controls

The important control is that generic outfield power does not explain the pattern:

| control | win% | avg run diff |
|---|---:|---:|
| OF HR zero only | .405 | -1.29 |
| OF RBI < 3 only | .333 | -2.04 |

Interpretation: this is not simply "SSG lacks outfield home runs." The signal becomes much sharper when RHP starter context, run-killing outs, extra-out damage, and high-leverage OF conversion are attached.

## Near-Final Layer 1 Message

> SSG's Layer 1 hidden weakness is robust enough to use as a feature contract: the problem is not generic outfield power, but a RHP-side game-script lock where OF/DH low conversion, run-killing outs, and extra-out damage remove comeback paths.

## Feature Contract

Foreign pitcher:

- Traffic command.
- Starter length.
- Extra-out resilience.
- Low free-pass volatility.

Foreign hitter:

- RHP-resistant OF/DH OBP plus damage.
- Two-strike survival.
- GDP/CS run-kill avoidance.

## Updated Layer 1 Conclusion

Layer 1 moves from 88% to 91%.

Layer 1 is now near-freeze for candidate scoring. It should not be endlessly mined unless new data arrives. The next best work is:

1. Refresh post-2026-06-11 STATIZ/current-game data.
2. Attach stronger play-by-play, defense, and baserunning proxies if accessible.
3. Then freeze Layer 1 and shift focus to Layers 2-5.

## Six-Layer Progress After Run 016

| no. | layer | progress | movement | candidate status |
|---:|---|---:|---|---|
| 1 | SSG hidden weakness mining | 91% | 88% -> 91% | near-freeze pending refresh |
| 2 | KBO foreign-player success/failure archetype mining | 55% | unchanged | not enough for final names |
| 3 | Candidate market construction | 68% | unchanged | research leads only |
| 4 | KBO translation model | 56% | unchanged | pilot only |
| 5 | Failure risk model | 53% | unchanged | pilot only |
| 6 | SSG fit ranking | 25% | unchanged | locked |

## Validation

- `src/modeling/validate_ssg_hidden_weakness_robustness_v3.py` was py-compiled.
- The script was rerun and reproduced all seven output tables above.
- The bootstrap/permutation run used 3,000 iterations with fixed seed `20260614`.

## Caveats

- The game frame still has 61 SSG games.
- This is descriptive robustness, not causal proof.
- The snapshot ends at 2026-06-11.
- Play-by-play defense and full baserunning values are not yet attached.
- Candidate names remain locked until Layers 2-6 clear their gates.
