# Data-Mining Recommendation Conclusion v1

Generated from structured numeric data only. News, interviews, article counts, and text-derived fields were excluded from model inputs.

## Core Conclusion

The data-mining model changed the recommendation board. The strongest defendable conclusion is:

> SSG should prioritize a foreign outfielder whose historical-KBO translation pattern looks like a low-failure, everyday-volume hitter. For pitchers, the current historical model is weaker, so the model does not yet justify a firm final recommendation; it only creates diagnostic leads.

## Model Stack

| Slot | Historical rows | Feature family | Model | Target | Decision |
|---|---:|---|---|---|---|
| foreign_hitter | 22 | savant_only | ridge_logit | success | promoted |
| foreign_hitter | 22 | savant_only | ridge_logit | failure | promoted |
| foreign_pitcher | 49 | milb_damage_command | sparse_l1_logit | success | watch/diagnostic |
| foreign_pitcher | 49 | milb_damage_command | sparse_l1_logit | failure | not promoted; warning only |

## Validation Evidence Used

| Role | Target | Feature family | Model | AUC | Brier lift | Top-25 precision lift | Promotion status |
|---|---|---|---|---:|---:|---:|---|
| hitter | failure | savant_only | ridge_logit | 0.738 | 0.023 | 0.344 | pilot_promote |
| hitter | success | savant_only | ridge_logit | 0.833 | 0.073 | 0.222 | pilot_promote |
| pitcher | success | milb_damage_command | sparse_l1_logit | 0.603 | 0.007 | 0.118 | watch |

## Top 3 Foreign Hitter Leads

| Rank | Player | Org | Age | 40-man | P(success) | P(failure) | Margin |
|---:|---|---|---:|---|---:|---:|---:|
| 1 | Luis Matos | MIL | 24 | False | 92.4% | 8.2% | 0.842 |
| 2 | Nolan Jones | CLE | 28 | False | 90.2% | 9.2% | 0.810 |
| 3 | Dylan Carlson | PHI | 27 | False | 82.4% | 15.1% | 0.673 |

## Top 3 Foreign Pitcher Diagnostic Leads

| Rank | Player | Org | Age | 40-man | P(success) | P(failure warning) | Margin | Strength |
|---:|---|---|---:|---|---:|---:|---:|---|
| 1 | Bryse Wilson | PHI | 28 | False | 50.5% | 46.9% | 0.036 | diagnostic_lead |
| 2 | Austin Gomber | ATL | 32 | False | 52.6% | 49.2% | 0.034 | diagnostic_lead |
| 3 | Dietrich Enns | BAL | 35 | False | 39.5% | 56.7% | -0.171 | hold_negative_model_margin |

## Interpretation

1. Hitter conclusion is model-supported: hitter Savant-only success/failure classifiers passed the v0.3 pilot promotion gate.
2. The model no longer favors tiny-sample hitters just because a manual SSG-fit score was high. Brennan/Fletcher drop behind larger-sample candidates.
3. Pitcher conclusion is not as strong as hitter conclusion. The pitcher historical model is watch-grade, not a fully promoted classifier; negative-margin rows are holds, not recommendations.
4. Salary is still a required next hard gate. This run uses roster/market access but does not yet have complete actual salary for the full candidate market.

## Output Files

- `outputs/tables/data_mining_hitter_candidates_v1.csv`
- `outputs/tables/data_mining_pitcher_candidates_v1.csv`
- `outputs/tables/data_mining_recommendations_top3_v1.csv`
- `outputs/tables/data_mining_model_audit_v1.csv`
