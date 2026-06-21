# Run 022 Candidate-Side Signal Join v0.1

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 4. KBO translation model
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run attaches signal components and feasibility tags, but it does not create a shortlist or recommendations.

## Purpose

Run 021 decided which model signals can safely move downstream:

- hitter `savant_only`: allowed as a pilot score component;
- pitcher `milb_damage_command`: diagnostic/watch only;
- Asian quota/NPB market: feasibility inventory only until contract, salary, buyout, and nationality checks improve.

Run 022 applies those rules to current candidate pools.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/candidate_side_hitter_savant_pilot_component_v0_1.csv` | 736 | MLB outfielder/hitter pool with candidate-compatible Savant pilot probabilities |
| `outputs/tables/candidate_side_hitter_savant_pilot_model_audit_v0_1.csv` | 4 | repeated-CV audit for the 17 feature candidate-compatible hitter model |
| `outputs/tables/candidate_side_hitter_savant_feature_map_v0_1.csv` | 17 | historical `pre_*` to candidate `recent_*` feature map |
| `outputs/tables/candidate_side_pitcher_milb_diagnostic_tags_v0_1.csv` | 1,009 | MLB pitcher pool with MiLB damage/command diagnostic tags |
| `outputs/tables/candidate_side_asian_quota_feasibility_tags_v0_1.csv` | 978 | NPB/CPBL Asian-quota market with feasibility tags |
| `outputs/tables/candidate_side_signal_join_summary_v0_1.csv` | 4 | slot-level row counts and release policy summary |
| `src/modeling/build_candidate_side_signal_join_v0_1.py` | script | reproducible candidate-side signal join |

## Hitter Model Audit

The Run 021 hitter model used 18 Savant features. One feature was unavailable in the current hitter candidate pool, so Run 022 reran validation using the 17 candidate-compatible features.

| target | model | AUC | Brier | Brier lift | top-25 precision lift | status |
|---|---|---:|---:|---:|---:|---|
| failure | ridge logit | 0.757 | 0.208 | +0.027 | +0.394 | pilot promote |
| success | ridge logit | 0.808 | 0.178 | +0.065 | +0.133 | pilot promote |

Decision:

- The hitter Savant pilot component remains valid after candidate-side feature compatibility checks.
- It may be used later as one input to SSG fit ranking.
- It is not a final ranking by itself.

## Candidate-Side Signal Coverage

| scope | rows | primary signal | positive/watch rows | risk/gap rows | release policy |
|---|---:|---|---:|---:|---|
| MLB outfielder/hitter pool | 736 | hitter Savant pilot component | 370 | 263 | signal component only |
| MLB pitcher pool | 1,009 | MiLB damage/command diagnostic | 79 | 738 | diagnostic tags only |
| Asian-quota market | 978 | feasibility tags | 154 | 824 | feasibility inventory only |

All row-level outputs include:

- `is_final_recommendation = False`
- `shortlist_label_allowed = False`
- `candidate_name_release_allowed = False`

## Interpretation

This is the first point where model evidence touches the actual candidate market.

For hitters:

- The model is strong enough to become a pilot component.
- The output should be used as a filter or feature, not as a final answer.
- Strong hitter signals still need SSG fit, availability, contract, medical/news, and manual scouting context.

For pitchers:

- The model is not strong enough for scoring.
- The diagnostic tags are useful because they turn the vague question "is this pitcher good?" into more specific checks:
  - does the candidate suppress home-run damage?
  - is the walk/command risk manageable?
  - is there a current AAA/upper-minors role track?
  - is bat-missing upside paired with volatility?

For Asian quota:

- 154 rows currently pass nationality but still need contract/salary/buyout checks.
- 772 rows still have unknown nationality in the current public roster layer.
- 52 rows fail Asian-quota nationality and should be treated as regular foreign-player inventory only.

## Gate Decision

Allowed:

- Use hitter Savant pilot component as a downstream ranking input.
- Use pitcher MiLB tags as diagnostic context only.
- Use Asian-quota feasibility tags to prioritize manual checks.

Not allowed:

- No final shortlist.
- No recommendation labels.
- No pitcher score in final ranking.
- No Asian-quota recommendation until salary/contract/buyout and nationality checks improve.

## Next Step

Run 023 should build a locked `SSG fit ranking preparation mart` by joining:

- SSG Layer 1 target features;
- hitter Savant pilot component;
- pitcher MiLB diagnostic tags;
- market access and age/role gates;
- Asian-quota feasibility tags;
- NPB salary/contract/buyout and news/manual checks when available.

The output should still use research labels, not recommendations.

## Six-Layer Progress After Run 022

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 72% | 70% -> 72% |
| 3 | Candidate market construction | 83% | 80% -> 83% |
| 4 | KBO translation model | 78% | 73% -> 78% |
| 5 | Failure risk model | 68% | 64% -> 68% |
| 6 | SSG fit ranking | 40% | 32% -> 40% |

Candidate release remains locked.
