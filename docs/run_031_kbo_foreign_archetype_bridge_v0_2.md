# Run 031 KBO Foreign Archetype Bridge v0.2

Date: 2026-06-22 KST

Layer focus:

- 2. KBO foreign-player success/failure archetype mining

Candidate policy: locked. This run improves the historical archetype layer but
does not create a shortlist, final ranking, or recommendation.

## Purpose

The existing Layer 2 outcome archetypes described what happened after foreign
players arrived in KBO. This run adds the missing bridge:

> Which pre-arrival fingerprints tended to land in each KBO success/failure
> archetype?

This matters because a simple success/failure classifier is too blunt for the
project. The useful scouting question is not "who has the highest model score?"
It is "which failure mode are we trying to avoid, and which pre-arrival signals
warn us about that mode?"

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/kbo_foreign_archetype_bridge_v0_2.csv` | 127 | row-level bridge from KBO outcome archetype to pre-arrival family scores |
| `outputs/tables/kbo_foreign_archetype_prearrival_profile_v0_2.csv` | 7 | cluster-level pre-arrival fingerprints |
| `outputs/tables/kbo_foreign_archetype_rule_lifts_v0_2.csv` | 294 | one-family and two-family rule lifts with small-sample gates |
| `outputs/tables/kbo_foreign_archetype_feature_contract_v0_2.csv` | 7 | downstream feature contract for candidate evaluation |
| `outputs/tables/kbo_foreign_archetype_gate_audit_v0_2.csv` | 5 | Layer 2 gate audit |
| `src/modeling/build_kbo_foreign_archetype_bridge_v0_2.py` | script | reproducible builder |

## Coverage

| check | rows |
|---|---:|
| KBO outcome archetype rows joined | 127 / 127 |
| rows with pre-arrival model fingerprints | 71 / 127 |
| cluster profiles created | 7 / 7 |
| mined rule lifts | 294 |
| semantically aligned research rules | 4 |
| counterintuitive negative-control rules | 15 |

Release locks passed for all 127 bridge rows.

## Cluster Read

| role | archetype signature | rows | model-ready rows | success | failure | profile gate |
|---|---|---:|---:|---:|---:|---|
| hitter | hitter failure, low-impact/replacement | 12 | 5 | 0.000 | 1.000 | very thin, watch only |
| hitter | everyday middle-order anchor | 29 | 17 | 0.793 | 0.138 | usable descriptive profile |
| pitcher | failure, injury-exit cluster | 10 | 6 | 0.000 | 1.000 | thin, use with caution |
| pitcher | failure, performance-exit cluster | 11 | 7 | 0.000 | 1.000 | thin, use with caution |
| pitcher | failure, low-impact/replacement cluster | 19 | 10 | 0.053 | 0.842 | thin, use with caution |
| pitcher | load-bearing rotation anchor c1 | 20 | 9 | 1.000 | 0.000 | thin, use with caution |
| pitcher | load-bearing rotation anchor c4 | 26 | 17 | 0.962 | 0.000 | usable descriptive profile |

## Key Mining Messages

### 1. Pitcher failure is not one thing

The pitcher failure bucket split into at least three different failure modes:

- injury-exit;
- performance-exit;
- low-impact/replacement.

That means the foreign pitcher screen should not use one generic "risk" score.
Medical availability, damage suppression, command floor, raw-miss upside, and
role continuity should be separated before being recombined.

### 2. Raw bat-missing without role continuity is a warning, not a shortcut

One promoted research rule:

- `pitcher_raw_miss_upside=high` and
  `pitcher_role_continuity_workload=low`
- target: success
- inside-rule success rate: 0.200
- pitcher base success rate: 0.510
- delta: -0.310

Interpretation:

Raw miss is not enough. If it comes without recent starter workload or role
continuity, it becomes a volatility profile rather than a clean KBO translation
profile.

### 3. Role continuity suppresses replacement risk

One promoted research rule:

- `pitcher_role_continuity_workload=high`
- target: in-season replacement
- inside-rule replacement rate: 0.125
- pitcher base replacement rate: 0.306
- delta: -0.181

Interpretation:

For SSG's foreign pitcher slot, recent workload continuity should be treated as
a stabilizer gate, not just a descriptive stat.

### 4. Hitter results are not ready for a clean archetype score

The hitter sample produced useful warnings but also several counterintuitive
signals. Those were explicitly marked as `counterintuitive_watch_do_not_score`.

Interpretation:

The hitter Savant pilot can still feed Layer 4/6 as a component, but Layer 2
should not pretend hitter historical archetypes are fully solved. The correct
next action is more pre-arrival backfill and source validation, not overconfident
ranking.

### 5. Negative controls are now explicit

This run did not blindly promote every large lift. It separated:

- semantically aligned research rules: 4;
- counterintuitive negative-control rules: 15;
- small-sample watch rules: remaining rules.

That is important for presentation: the model is allowed to discover surprising
signals, but it is not allowed to turn every surprise into a scoring rule.

## Downstream Contract

Layer 2 now hands these instructions to candidate evaluation:

- foreign hitter: keep using hitter Savant pilot as a component, but do not
  overstate hitter archetype evidence yet;
- foreign pitcher: separate raw miss from damage suppression, command floor,
  and recent workload continuity;
- Asian quota: historical NPB/CPBL pre-arrival backfill is still required before
  archetype translation can be promoted.

## Six-Layer Progress After Run 031

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | 73% -> 78% |
| 3 | Candidate market construction | 94% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 85% | unchanged |
| 6 | SSG fit ranking | 71% | unchanged |

Candidate release remains locked.

## Remaining Gaps

- The pre-arrival fingerprint sample is still 71 / 127 rows.
- 2017-2022 historical ID and pre-arrival feature coverage remain incomplete.
- NPB/CPBL historical pre-arrival features are still thin.
- Hitter archetype rules need more backfill before being promoted beyond pilot
  component status.
- Pitcher rules are research signals only and must still be validated against
  candidate-side source lanes before Layer 6 can rank names.
