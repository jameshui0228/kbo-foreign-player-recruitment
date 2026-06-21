# Run 020 Translation And Failure-Risk v0.2 MiLB Modeling

Date: 2026-06-21 KST

Layer focus:

- 2. KBO foreign-player success/failure archetype mining
- 4. KBO translation model
- 5. Failure risk model
- 6. SSG fit ranking lock status

Candidate policy: locked. This run retrains model gates but does not release recommendations or shortlist labels.

## Purpose

Run 019 added official historical pre-KBO MiLB features for MLBAM-matched KBO foreign-player rows. Run 020 tests whether those features can improve the KBO translation and failure-risk model layer.

The key change is model readiness:

- v0.1 allowed only rows with pre-KBO MLB/Savant features.
- v0.2 allows rows with either pre-KBO MLB/Savant features or official pre-KBO MiLB features.

## New And Updated Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/kbo_translation_feature_mart_v0_2.csv` | 128 | v0.1 translation mart plus historical MiLB features |
| `outputs/tables/failure_risk_feature_mart_v0_2.csv` | 128 | v0.1 failure-risk mart plus historical MiLB features |
| `outputs/tables/kbo_translation_readiness_v0_2.csv` | 3 | model-ready row counts by role |
| `outputs/tables/kbo_translation_feature_mart_v0_2_join_audit.csv` | 10 | feature-source join audit |
| `outputs/tables/kbo_translation_failure_repeated_cv_comparison_v0_2.csv` | 16 | repeated CV summary for v0.2 |
| `outputs/tables/kbo_translation_failure_v0_1_vs_v0_2_comparison.csv` | 16 | v0.1 vs v0.2 repeated CV comparison |
| `outputs/tables/kbo_translation_failure_feature_signals_v0_2.csv` | 146 | coefficient-level feature signal audit |
| `src/modeling/build_recruitment_model_marts_v0_2.py` | script | reproducible v0.2 mart builder |
| `src/modeling/train_kbo_translation_failure_models_v0_2.py` | script | reproducible v0.2 training and comparison |

## Model-Ready Coverage

| scope | rows | v0.1 Savant rows | v0.2 model-ready rows | success rows | failure rows | MiLB-only rows |
|---|---:|---:|---:|---:|---:|---:|
| all | 128 | 55 | 71 | 38 | 29 | 16 |
| hitter | 42 | 22 | 22 | 13 | 8 | 0 |
| pitcher | 86 | 33 | 49 | 25 | 21 | 16 |

Interpretation:

- The main gain is on foreign pitchers: 33 to 49 model-ready rows.
- The hitter sample did not gain rows, only extra MiLB features, so hitter v0.2 is mostly a feature-expansion stress test.
- The additional 16 MiLB-only rows make pitcher validation more realistic but also expose overfitting risk.

## Repeated CV Result

The strict repeated-CV gate did not promote the all-feature v0.2 models.

| role | target | best non-prior model | AUC | Brier | Brier lift vs role prior | top-25 precision lift | status |
|---|---|---|---:|---:|---:|---:|---|
| hitter | failure | ridge logit | 0.620 | 0.285 | -0.049 | +0.106 | do not promote |
| hitter | success | ridge logit | 0.683 | 0.256 | -0.013 | +0.078 | do not promote |
| pitcher | failure | hist gradient boosting | 0.500 | 0.245 | 0.000 | 0.000 | do not promote |
| pitcher | success | hist gradient boosting | 0.500 | 0.250 | 0.000 | 0.000 | do not promote |

This is an important negative result. Adding more features and rows is not automatically better. The current all-feature model is too wide for the available historical sample and should not be used as a final ranking score.

## v0.1 vs v0.2 Read

- Hitter v0.1 ridge/logit models had pilot-promote status in repeated CV.
- Hitter v0.2 lost that status because the sample stayed at 22 rows while feature count rose by about 12.
- Pitcher v0.2 gained 480 repeated-CV validation observations because the role sample expanded from 33 to 49 rows, but non-prior models still did not beat the role prior reliably.
- This means v0.2 should be treated as a diagnostic layer, not a ranking layer.

## Feature-Signal Read

The v0.2 signal audit is still useful for archetype mining.

Pitcher failure signals with the largest absolute coefficients:

- `pre_kbo_milb_hr9`: higher values raised failure probability.
- `pre_kbo_milb_k9`: higher values also raised failure probability in this sample, likely reflecting volatile power-arm profiles rather than a simple "strikeouts are bad" rule.
- `pre_woba_allowed`: higher MLB/Savant allowed quality raised failure probability.
- `pre_three_ball_pitch_rate`: higher command-friction raised failure probability.
- `pre_kbo_milb_latest_year`: more recent MiLB track lowered failure probability.

Pitcher success signals pointed in the opposite direction for several risk variables:

- lower MiLB HR/9;
- lower three-ball pitch rate;
- lower MLB/Savant wOBA allowed;
- more recent track continuity.

The pitcher-side working message is therefore not "find the highest strikeout arm." It is closer to:

> For KBO translation, raw bat-missing upside needs to be separated from damage suppression, command friction, and recent role continuity.

That message is not yet a candidate-ranking rule, but it is a stronger scouting-model question for the next ablation run.

## Decision

Do not promote v0.2 all-feature models into final SSG fit ranking.

Promote the following as validated next-step evidence:

- historical MiLB features successfully joined into translation and failure marts;
- model-ready rows improved from 55 to 71;
- pitcher rows improved from 33 to 49;
- repeated CV was rerun and stored;
- feature-signal audit identified pitcher risk variables that deserve compact ablation.

## Next Modeling Step

Run a compact feature-family ablation:

1. Savant-only baseline.
2. MiLB level/role only.
3. MiLB damage/command only.
4. Recent-track continuity only.
5. Compact mixed model with at most 6-10 features per role/target.

Only promote a model if it beats the role prior on repeated CV Brier score without sacrificing top-bucket precision.

## Six-Layer Progress After Run 020

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 66% | 62% -> 66% |
| 3 | Candidate market construction | 80% | unchanged |
| 4 | KBO translation model | 67% | 64% -> 67% |
| 5 | Failure risk model | 61% | 58% -> 61% |
| 6 | SSG fit ranking | 29% | 28% -> 29% |

Candidate release remains locked.
