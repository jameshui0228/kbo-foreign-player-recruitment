# Run 011 Historical Feature Expansion And Pilot Modeling

Generated: 2026-06-12 KST

## What Changed

Run 011 fixed the main blocker found in Run 010: too few historical KBO foreign-player rows had pre-KBO features.

Added data and scripts:

| artifact | purpose |
|---|---|
| `data/processed/mlb_milb/savant/savant_statcast_2022.parquet` | added 2022 MLB Savant events |
| `src/data/combine_savant_statcast_year.py` | prevents cross-season contamination when combining Savant chunks |
| `outputs/tables/savant_statcast_mlb_2022_clean_combine_manifest.json` | clean 2022 combine audit |
| `outputs/tables/savant_pitcher_feature_summary_2022_2026.csv` | expanded pitcher feature table |
| `outputs/tables/savant_hitter_feature_summary_2022_2026.csv` | expanded hitter feature table |
| `src/modeling/train_kbo_translation_failure_models_v0_1.py` | pilot KBO translation and failure-risk models |

The first 2022 combine attempt exposed a real data-quality risk: the generic downloader combined every raw chunk in the shared folder, mixing 2022 with 2023-2026. The new combine helper filters by file year and `game_year`, then writes a clean yearly parquet. The corrected 2022 table contains 710,210 rows and only `game_year=2022`.

## Readiness Improvement

Pre-KBO Savant coverage improved sharply:

| version | eligible rows | pre-KBO Savant rows | hitter matched | pitcher matched |
|---|---:|---:|---:|---:|
| Run 010, 2023-2026 only | 87 | 27 | 7 / 29 | 20 / 58 |
| Run 011, 2022-2026 expanded | 128 | 55 | 22 / 42 | 33 / 86 |

Role-level training thresholds are now met:

| role | eligible rows | trainable rows | success rows | failure rows | training ready |
|---|---:|---:|---:|---:|---|
| hitter | 42 | 22 | 13 | 8 | yes |
| pitcher | 86 | 33 | 14 | 17 | yes |
| all roles | 128 | 55 | 27 | 25 | no, below 60-row overall threshold |

Interpretation: role-specific pilot models are now allowed. A single pooled all-role model is still not preferred.

## Model Validation Design

Only pre-KBO Savant features were used.

Validation layers:

1. `time_forward_holdout`: train on prior KBO arrival seasons, validate on the next season.
2. `repeated_stratified_cv`: 3-fold, 30-repeat stability check. This is supplemental and not the primary deployment validation.

Outputs:

| output | purpose |
|---|---|
| `outputs/tables/kbo_translation_failure_model_comparison_v0_1.csv` | time-forward model comparison |
| `outputs/tables/kbo_translation_failure_repeated_cv_comparison_v0_1.csv` | repeated CV stability check |
| `outputs/tables/kbo_translation_failure_feature_signals_v0_1.csv` | feature-direction audit |
| `outputs/tables/kbo_translation_failure_oof_predictions_v0_1.csv` | time-forward out-of-fold predictions |

## Key Modeling Result

The model did not say "just find the best public Savant pitcher."

It said something more useful:

1. Hitter translation/failure signals are relatively learnable from public pre-KBO Savant features.
2. Pitcher time-forward holdout improves over role prior, but repeated CV does not support a stable public-Savant-only pitcher model.
3. Therefore, SSG's foreign-pitcher thesis should not be finalized from MLB public Statcast alone. It needs MiLB/NPB/CPBL role context, availability, workload history, medical/health, and scouting/news features.

## Time-Forward Holdout Summary

| role | target | promoted model | mean AUC | mean Brier | Brier lift vs role prior |
|---|---|---|---:|---:|---:|
| hitter | success | balanced ridge logistic | 0.850 | 0.125 | +0.126 |
| hitter | failure | ridge logistic | 0.722 | 0.207 | +0.018 |
| pitcher | success | balanced ridge logistic | 0.762 | 0.202 | +0.082 |
| pitcher | failure | balanced ridge logistic | 0.575 | 0.254 | +0.029 |

## Repeated CV Stability Summary

| role | target | stability result |
|---|---|---|
| hitter success | promoted | ridge logistic AUC 0.772, Brier lift +0.048 |
| hitter failure | promoted/watch | ridge logistic AUC 0.716, Brier lift +0.015 |
| pitcher success | not promoted | ridge logistic AUC 0.482, worse Brier than role prior |
| pitcher failure | not promoted | ridge logistic AUC 0.464, worse Brier than role prior |

## Feature Signals

These are not causal claims. They are small-sample feature directions to guide the next data collection.

Hitter:

- Success rises with larger pre-KBO MLB sample size and lower whiff profile.
- Failure rises with whiff, over-optimized "flawed profile" screen score, and low-velocity damage without enough stable volume.
- This supports a market-inefficiency idea: do not chase highlight-tool hitters if the swing-and-miss/volume profile is fragile.

Pitcher:

- Failure direction is most strongly tied to pre-KBO wOBA allowed and three-ball count pressure.
- Public whiff/K features are unstable and sometimes point in the wrong direction across validation schemes.
- For SSG, this strengthens the traffic-command thesis but warns that public Savant alone is insufficient for pitcher selection.

## Updated Project Implication

The SSG message should now be framed more carefully:

> SSG's biggest import slot should still be pitcher-first, but the selection edge is not "more strikeouts" or a simple stuff score. The edge has to be a traffic-command and workload-stability profile that survives non-public context checks: role history, availability, medical risk, and adaptation signals.

Hitter remains a secondary but more model-stable path:

> If SSG uses the hitter slot, the model says to avoid the tempting flawed-power profile and prefer a hitter whose pre-KBO performance volume and contact stability make the KBO translation safer.

Asian quota remains locked because the NPB/CPBL/ABL market table is not built.

## Current Gate Status After Run 011

| gate | status | reason |
|---|---|---|
| G1 SSG hidden need | pass | pitcher-first SSG need survives context validation |
| G2 KBO archetype | partial pass | outcome archetypes exist |
| G3 candidate market | partial | MLB current-org exists; Asian quota/free-agent/contract layers missing |
| G4 KBO translation | pass to pilot | role-specific trainable rows and pilot models exist |
| G5 failure risk | pass to pilot | role-specific failure-risk models exist |
| G6 final shortlist | locked | market gate and manual verification still incomplete |

## Next Run

Run 012 should build the market layers that still block shortlist release:

1. Asian quota market: NPB, CPBL, ABL, nationality, prior/current Asian league eligibility, salary/contract estimate.
2. Current replacement market: DFA/released/free-agent/MiLB transaction layer.
3. Pitcher context expansion: MiLB/NPB/CPBL workload, injuries, role continuity, and scouting/news text.

No candidate should be called a final recommendation until those layers are built.
