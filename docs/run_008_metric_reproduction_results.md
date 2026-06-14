# Run 008 Metric Reproduction Results

Generated: 2026-06-12 KST

## What Changed

This run moved the project from descriptive message drafting to reproducible data mining.

Three mining layers were built:

1. SSG hidden-state anomaly mining.
2. Historical KBO foreign-player archetype clustering.
3. Leakage-safe historical baseline and OOF prediction storage.

## Output Tables

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_hidden_state_mining_v0_1.csv` | 289 | SSG context anomaly evidence cards |
| `outputs/tables/ssg_hidden_state_message_candidates_v0_1.csv` | 9 | data-mined message themes |
| `outputs/tables/ssg_hidden_state_feature_contract_v0_1.csv` | 9 | maps each message to candidate features |
| `outputs/tables/kbo_foreign_archetype_assignments_v0_1.csv` | 128 | 2023-2025 foreign-player outcome cluster assignments |
| `outputs/tables/kbo_foreign_archetype_summary_v0_1.csv` | 7 | cluster-level success/failure archetypes |
| `outputs/tables/kbo_foreign_failure_patterns_v0_1.csv` | 3 | failure archetype summaries |
| `outputs/tables/kbo_foreign_baseline_scores_v0_1.csv` | 40 | fold x target x model metrics |
| `outputs/tables/kbo_foreign_oof_predictions_v0_1.csv` | 1,710 | auditable out-of-fold predictions |
| `outputs/tables/kbo_foreign_model_family_comparison_v0_1.csv` | 10 | baseline family comparison |

## Data-Mined SSG Message Priority

The strongest mined signal is not the hitter message. It is the foreign-pitcher need.

| rank | slot | message theme | priority score | top evidence |
|---:|---|---|---:|---|
| 1 | foreign pitcher | `run_prevention_stabilizer` | 58.49 | vs right orthodox, away, 0 out, 2 out contexts |
| 2 | foreign pitcher | `traffic_command_starter` | 51.72 | RISP, runner on base, on second, bases loaded |
| 3 | foreign hitter | `context_runway_bat` | 33.11 | 2 out, early inning, away, bases loaded |
| 4 | foreign pitcher | `abs_native_load_bearing_starter` | 26.08 | early 1-3 innings, starter role, short-start bullpen compression |
| 5 | foreign hitter | `first_base_traffic_converter` | 25.75 | runner on first, runner on base, OF high-leverage usage |
| 9 | Asian quota | `option_layer_shock_absorber` | 3.17 | bullpen workload stress only |

Interpretation:

- The first promoted message should be pitcher-led.
- Hitter remains a real second message, but it is not the strongest current anomaly.
- Asian quota is still conceptually important, but this run did not yet produce enough candidate-market data to claim it as a fully mined message.

## Historical KBO Foreign-Player Archetypes

### Hitter Archetypes

| archetype | rows | success rate | failure rate | median PA | median WAR | median wRC+ |
|---|---:|---:|---:|---:|---:|---:|
| `hitter_everyday_middle_order_anchor` | 30 | 76.7% | 16.7% | 512.5 | 3.50 | 132.4 |
| `hitter_failure_replacement_or_low_impact` | 12 | 0.0% | 100.0% | 236.5 | 0.03 | 98.1 |

The hitter lesson is not just "find power." The successful hitter cluster is an everyday-volume cluster with real run creation. The failure cluster is short-volume, near-replacement impact.

### Pitcher Archetypes

| archetype | rows | success rate | failure rate | median IP | median WAR | median ERA |
|---|---:|---:|---:|---:|---:|---:|
| `pitcher_load_bearing_rotation_anchor` | 20 | 100.0% | 0.0% | 154.7 | 3.96 | 3.28 |
| `pitcher_load_bearing_rotation_anchor` | 26 | 96.2% | 0.0% | 161.8 | 4.43 | 3.41 |
| `pitcher_failure_replacement_or_health_risk` | 37 | 0-5.3% | 84.2-100.0% | 47.0-66.0 | 0.76-1.15 | 4.29-4.76 |

The pitcher lesson is sharper than the hitter lesson. Recent successful KBO foreign pitchers are strongly volume-and-run-prevention clustered. That directly overlaps with SSG's current starter/bullpen compression problem.

## Baseline Board

The baseline board gives the minimum score that future SSG-fit and KBO-translation models must beat.

| target | best promoted baseline | mean AUC | mean Brier | top-25% precision | lift vs global Brier |
|---|---|---:|---:|---:|---:|
| success | `role_prior` | 0.559 | 0.236 | 0.523 | +0.0257 |
| success | `team_role_prior` | 0.580 | 0.252 | 0.591 | +0.0094 |
| failure | `recent_role_prior` | 0.632 | 0.239 | 0.545 | +0.0239 |
| failure | `prev_season_team_role_prior` | 0.559 | 0.246 | 0.455 | +0.0172 |

Interpretation:

- Role and recency matter even before player-level scouting features are added.
- Any strong model that cannot beat these simple priors should not be trusted.
- The next candidate model should optimize failure detection and shortlist precision, not just average accuracy.

## Current Message Decision

Promote this as the current primary SSG message:

> SSG's foreign-player priority should be a traffic-command, load-bearing starter: not the most famous arm, but a pitcher who prevents innings from exploding after traffic and repeatedly turns 4-inning games into 6-inning games.

Keep this as the secondary hitter message:

> If SSG replaces or adds a foreign hitter, the target should not be a generic slugger. The target should be a first-base traffic converter who turns runner-on-first states into scoring-position pressure without adding strikeout/GDP risk.

Keep this as a provisional Asian-quota message:

> The Asian quota slot should be treated as an option layer and shock absorber, but this still needs NPB/CPBL/ABL candidate-market data before it becomes a fully mined claim.

## Next Run

`run_009_candidate_fit_scoring` should:

1. join message themes to MLB candidate pool columns;
2. build a foreign-pitcher score around zone rate, BB+HBP, HR suppression, 80+ pitch workload, early-inning stability, and traffic command proxies;
3. build a hitter score around OBP floor, RHP stability, two-strike contact, low-GDP batted-ball shape, and OF/DH fit;
4. keep Asian quota separate until Asian-market data is collected;
5. compare final candidates against historical archetype distance and failure-risk similarity.
