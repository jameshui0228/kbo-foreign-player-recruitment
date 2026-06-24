# Ensemble Final Report Source Notes v1

Generated: 2026-06-23

## Delivery surface

- HTML report: `outputs/reports/ensemble_final_report_v1.html`
- Chart assets: `outputs/reports/ensemble_final_report_v1_assets`

## Source tables

- `outputs/tables/team_opinion_candidate_matrix_v1.csv`
- `outputs/tables/data_mining_recommendations_top3_v1.csv`
- `outputs/tables/data_mining_model_audit_v1.csv`

## Chart map

1. `ensemble_signal_weights.png`
   - Question: how does the ensemble combine base learners differently by slot?
   - Form: grouped horizontal bar.
   - Claim: hitter relies more on promoted classifier; pitcher relies more on consensus/filter signals.
2. `hitter_ensemble_ranking.png`
   - Question: which hitter candidates survive the ensemble?
   - Form: ranked horizontal bar.
   - Claim: Nolan Jones combines classifier and consensus; Luis Matos is model-discovery.
3. `pitcher_ensemble_ranking.png`
   - Question: which pitcher candidates should be verified first?
   - Form: ranked horizontal bar.
   - Claim: Josh Fleming is the strongest consensus verification candidate.
4. `model_validation_auc.png`
   - Question: why are hitter and pitcher recommendation strengths different?
   - Form: benchmark bar with 0.5 random baseline.
   - Claim: hitter models are promoted; pitcher model remains watch-grade.

## Omitted or bounded evidence

- Articles, interviews, and text-derived variables were excluded from model input by user instruction.
- Pitcher final recommendation is intentionally downgraded to diagnostic board because the pitcher classifier AUC is 0.603.
- Salary and buyout variables are named as next hard gates, not fully embedded in the current ensemble score.
