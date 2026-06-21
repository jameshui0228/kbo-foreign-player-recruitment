# Run 021 Feature-Family Ablation v0.3

Date: 2026-06-21 KST

Layer focus:

- 2. KBO foreign-player success/failure archetype mining
- 4. KBO translation model
- 5. Failure risk model
- 6. SSG fit ranking lock status

Candidate policy: locked. This run promotes model components, not player names.

## Purpose

Run 020 showed that the all-feature v0.2 model was too wide for the historical sample. Run 021 tests compact, scout-readable feature families to decide which signal groups can enter later SSG fit ranking.

The tested feature families are:

1. `savant_only`
2. `milb_level_role`
3. `milb_damage_command`
4. `recent_track_continuity`
5. `compact_mixed`

Each family is tested by role and target against a role-prior baseline using repeated stratified CV.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/kbo_translation_feature_family_ablation_mart_v0_3.csv` | 128 | v0.2 mart plus recent-level MiLB continuity feature |
| `outputs/tables/kbo_translation_failure_feature_family_sets_v0_3.csv` | 10 | feature-family registry by role |
| `outputs/tables/kbo_translation_failure_feature_family_cv_scores_v0_3.csv` | 7,200 | fold-level repeated-CV scores |
| `outputs/tables/kbo_translation_failure_feature_family_cv_comparison_v0_3.csv` | 80 | summarized family/model comparison |
| `outputs/tables/kbo_translation_failure_feature_family_decisions_v0_3.csv` | 4 | target-level promotion decision |
| `src/modeling/run_kbo_feature_family_ablation_v0_3.py` | script | reproducible ablation runner |

## Feature-Family Coverage

| family | hitter rows | hitter usable features | pitcher rows | pitcher usable features |
|---|---:|---:|---:|---:|
| `savant_only` | 22 | 18 | 33 | 18 |
| `milb_level_role` | 22 | 6 | 49 | 8 |
| `milb_damage_command` | 22 | 7 | 49 | 8 |
| `recent_track_continuity` | 22 | 5 | 49 | 6 |
| `compact_mixed` | 22 | 10 | 49 | 9 |

## Promotion Results

| role | target | promoted family | model | AUC | Brier | Brier lift | top-25 precision lift | decision |
|---|---|---|---|---:|---:|---:|---:|---|
| hitter | failure | `savant_only` | ridge logit | 0.738 | 0.212 | +0.023 | +0.344 | pilot score component |
| hitter | success | `savant_only` | ridge logit | 0.833 | 0.170 | +0.073 | +0.222 | pilot score component |
| pitcher | failure | `milb_damage_command` | sparse L1 logit | 0.590 | 0.248 | -0.003 | +0.048 | do not use for ranking |
| pitcher | success | `milb_damage_command` | sparse L1 logit | 0.603 | 0.243 | +0.007 | +0.118 | diagnostic only |

## Interpretation

This run separates the hitter and pitcher modeling stories.

For foreign hitters:

- `savant_only` clearly outperformed role priors for both success and failure.
- This restores the Run 011 hitter signal after Run 020's all-feature widening weakened it.
- The practical implication is that hitter screening should not simply mix every available MiLB variable into the score. The first promoted model component should be pre-KBO MLB/Savant quality: swing-and-miss, contact quality, count leverage, and approach variables.

For foreign pitchers:

- No pitcher feature family cleared the strict pilot-promotion gate.
- `milb_damage_command` did reach watch status for pitcher success, with positive AUC and top-bucket precision lift.
- Pitcher failure still failed the Brier gate, even though top-bucket precision improved.
- The practical implication is that pitcher variables should remain diagnostic until medical/news, role fit, contract feasibility, and stronger command/shape context are added.

## Project Message Update

The model-supported message is now sharper:

> Hitter fit can use MLB/Savant skill translation as a pilot scoring component, but pitcher fit should not be reduced to one model score yet. For pitchers, the best current evidence is a scouting question: can the arm suppress damage and avoid command friction while carrying a recent usable role track?

This avoids the generic "find good OPS" or "find high strikeouts" trap.

## Gate Decision

Allowed:

- Use `savant_only` hitter model output as a pilot feature component later.
- Use pitcher `milb_damage_command` as a diagnostic note, not a ranking score.
- Keep candidate names locked.

Not allowed:

- No final shortlist.
- No recommendation label.
- No pitcher model score in final ranking yet.
- No Asian quota ranking yet.

## Next Step

Build the next candidate-market scoring join only after adding:

- hitter `savant_only` pilot component;
- pitcher `milb_damage_command` diagnostic tags;
- NPB salary/contract/buyout and nationality feasibility;
- injury/news/adaptation and Korea-willingness text features;
- refreshed KBO/STATIZ data if credentials are available.

## Six-Layer Progress After Run 021

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 70% | 66% -> 70% |
| 3 | Candidate market construction | 80% | unchanged |
| 4 | KBO translation model | 73% | 67% -> 73% |
| 5 | Failure risk model | 64% | 61% -> 64% |
| 6 | SSG fit ranking | 32% | 29% -> 32% |

Candidate release remains locked.
