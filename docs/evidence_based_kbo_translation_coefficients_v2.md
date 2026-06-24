# Evidence-Based KBO Translation Coefficients v2

## Method
- Source: `outputs/tables/kbo_translation_feature_family_ablation_mart_v0_3.csv`.
- Main estimates use one earliest available row per player to reduce repeated-player bias.
- Hitter main filter: KBO PA >= 100 and pre-KBO MiLB PA >= 100.
- Pitcher main filter: KBO IP >= 30 and pre-KBO MiLB IP >= 30.
- Reliability weights combine KBO and pre-KBO playing-time, capped so very large samples do not dominate.
- Confidence intervals are 2,000-replicate player-level bootstrap intervals for the weighted median ratio.
- These are empirical KBO-import-player coefficients, not universal MLB/MiLB-to-KBO league difficulty constants.

## Coefficients
| slot | recommended_formula | sample_policy | n_players | recommended_factor | bootstrap_wmedian_ci_low | bootstrap_wmedian_ci_high | weighted_reg_r2 | weighted_reg_mae |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| hitter | KBO wRC+ ≈ MiLB OPS*100 × factor | dedup earliest player; KBO PA>=100; MiLB PA>=100 | 15 | 1.388 | 1.201 | 1.751 | 0.200 | 15.759 |
| hitter_strict | KBO wRC+ ≈ MiLB OPS*100 × factor | dedup earliest player; KBO PA>=200; MiLB PA>=200 | 12 | 1.508 | 1.199 | 1.882 | 0.385 | 12.789 |
| pitcher | KBO ERA ≈ MiLB ERA × factor | dedup earliest player; KBO IP>=30; MiLB IP>=30 | 35 | 0.796 | 0.709 | 0.922 | 0.095 | 0.641 |
| pitcher_starterish | KBO ERA ≈ MiLB ERA × factor | dedup earliest player; KBO IP>=50; MiLB IP>=50; MiLB GS>=5 | 27 | 0.776 | 0.706 | 0.915 | 0.057 | 0.594 |

## Recommended presentation numbers
- Hitter: `KBO wRC+ ≈ MiLB OPS × 100 × 1.39`. Bootstrap 95% CI: `1.20 - 1.75`.
- Pitcher: `KBO ERA ≈ MiLB ERA × 0.80`. Bootstrap 95% CI: `0.71 - 0.92`.

## Why not use only OLS slope?
- OLS slopes are unstable because the historical KBO import sample is selected by clubs, small, and contains role/survivorship bias.
- The weighted median ratio is more presentation-safe for a simple translation coefficient because it is less sensitive to outliers and repeated playing-time extremes.
- Regression R2 remains low, so this coefficient is a baseline sanity check, not a standalone projection model.