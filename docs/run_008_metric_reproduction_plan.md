# Run 008 Metric Reproduction Plan

Generated: 2026-06-12 KST

## Goal

Turn the v0.1 historical KBO foreign-player label table into a Dacon-style validation board.

The next run should answer:

> Do our proposed SSG-specific, KBO-translation, failure-risk, and availability signals beat trivial historical baselines before we recommend final names?

## Why This Comes Next

`run_007` created the first supervised target table:

- 406 KBO foreign-player season rows.
- 353 historical label-available rows.
- 128 STATIZ outcome-attached rows.
- 4 time-based holdout folds from 2022 through 2025.

This is enough to stop arguing only from intuition. The project can now score whether a model would have avoided past failed foreign players and found past successful ones.

## CV And Public LB Analogue

| competition concept | this project |
|---|---|
| CV | time-fold validation on 2022, 2023, 2024, 2025 |
| Public LB | agreement with public articles, scouting reports, roster status, and contract feasibility |
| Private LB | whether candidates survive real-world health, money, role, and availability checks |

## Implement First

1. `baseline_renewal_rate`
   - Predict success from prior-year league-wide renewal/success rates by role.
   - Purpose: lowest bar.

2. `baseline_generic_stat`
   - Rank historical players by generic MLB/AAA-style surface stats where available.
   - Purpose: prove that simple stat shopping is not enough.

3. `failure_risk_gate`
   - Predict failure from release/replacement analogues, low workload, command volatility, injury flags, and role mismatch.
   - Purpose: avoid upside-only recommendations.

4. `slot_fit_score`
   - Foreign hitter: first-base traffic converter.
   - Foreign pitcher: ABS-native load-bearing starter.
   - Asian quota: option-layer shock absorber.
   - Purpose: test whether SSG-specific fit adds signal beyond overall talent.

5. `oof_prediction_store`
   - Save one row per historical player-season per fold with model score, label, role, year, and feature family.
   - Purpose: make every later claim auditable.

## Promotion Rule

Promote a model family only if it satisfies all three:

- beats the trivial majority baseline on at least two recent folds;
- improves failure detection or shortlist precision, not just average accuracy;
- remains interpretable enough to explain in a professor-facing presentation.

## Hold Back

Do not promote:

- a black-box ensemble before baselines are beaten;
- 2026-only features without a 2023-2025 stability check;
- any candidate ranking that uses post-KBO outcome columns;
- article-only signals without quantitative support;
- availability assumptions that are not checked against roster, transaction, contract, or injury context.

## Expected Output

- `src/modeling/run_kbo_foreign_baselines.py`
- `outputs/tables/kbo_foreign_baseline_scores_v0_1.csv`
- `outputs/tables/kbo_foreign_oof_predictions_v0_1.csv`
- `outputs/tables/kbo_foreign_model_family_comparison_v0_1.csv`
- `docs/run_008_metric_reproduction_results.md`
