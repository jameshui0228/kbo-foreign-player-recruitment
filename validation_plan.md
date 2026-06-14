# Validation Plan

Updated: 2026-06-12 KST

## What Validation Means Here

This is not a Dacon-style train/test prediction task yet. The current target is a robust recruitment thesis. Therefore validation has two layers:

1. **Message validation**: does the claimed SSG need survive source, time, and segment checks?
2. **Candidate validation**: does a candidate profile match the validated need without relying on leakage, biased articles, or one noisy metric?

## Message Validation Splits

| split | use | risk controlled |
|---|---|---|
| Source split | STATIZ vs Savant vs articles vs research papers | avoids one-source storytelling |
| Time split | 2026 current season vs 2023-2025 historical context | avoids overfitting to a short 2026 window |
| Role split | team total vs role segment vs player segment | avoids team-average masking |
| Market split | regular foreign vs replacement foreign vs Asian quota | avoids mixing different acquisition constraints |

## Current Scoring Proxy

Until player outcome labels are built, use evidence-card scoring:

- novelty: is the signal non-obvious?
- SSG specificity: is it about SSG, not a generic baseball truth?
- actionability: does it translate to candidate filters?
- data strength: is the source quantitative, reproducible, and current?

Message score = sum of evidence-card scores.

## Future Candidate Validation

Candidate screens should be validated by:

- historical KBO foreign-player outcomes when available;
- candidate prior league translation;
- season-to-season stability of features;
- role-specific fit rather than overall WAR/stat lines;
- sensitivity to excluding 2026 partial data;
- injury/availability and contract risk.

## CV/Public LB Analogue

| competition term | project analogue |
|---|---|
| CV score | evidence score and backtest score |
| Public LB | external/news/coaching narrative agreement |
| Private LB | whether final recommendation survives hidden constraints: availability, health, visa, role, contract, team strategy |

## Mismatch Rules

- Evidence score up, external narrative agrees: promote.
- Evidence score up, external narrative disagrees: inspect source conflict.
- Article-only signal high, quantitative support weak: suspect message.
- STATIZ-only signal strong, candidate features unavailable: hold until candidate-level data exists.
- Candidate looks good overall but weak on slot-specific features: reject or downgrade.

## Dacon-Style Model Validation Upgrade

The project will now use a competition-style validation ladder before final candidate claims.

### Primary Validation Objects

| object | validation question | failure mode controlled |
|---|---|---|
| SSG message | Does the hidden weakness survive source/time/role checks? | clever but non-actionable storytelling |
| KBO translation model | Would the model have identified past successful foreign players before they arrived? | MLB/AAA stat translation error |
| failure-risk model | Would the model have warned us about past failed or replaced foreign players? | upside-only candidate selection |
| availability model | Does the market bucket match later transaction/contract status? | recommending impossible players |
| final ranking | Does the shortlist stay stable under weight and sample changes? | overfitting final weights |

### Historical Backtest Plan

Once historical foreign-player labels are built, use:

| split | train | valid | purpose |
|---|---|---|---|
| Fold A | 2017-2021 | 2022 | old-to-new transfer |
| Fold B | 2017-2022 | 2023 | post-foreign-market shift |
| Fold C | 2017-2023 | 2024 | ABS transition context |
| Fold D | 2017-2024 | 2025 | most recent completed season |

2026 is not treated as a normal completed label. It is used as current-season context and monitored with sensitivity checks.

### Historical Label Table Status

`run_007` built the first validation target:

| item | value |
|---|---:|
| total KBO foreign-player season rows | 406 |
| historical label-available rows | 353 |
| STATIZ outcome-attached rows | 128 |
| 2026 completed-season labels | 0 |

Label confidence is uneven by period:

| period | confidence | reason |
|---|---|---|
| 2017-2022 | medium-low | roster/release/renewal proxy only |
| 2023-2025 | medium-high | roster/release/renewal proxy plus STATIZ PA/IP/WAR/wRC+/ERA outcomes |
| 2026 | withheld | current-season context, not a completed target |

Backtest fold readiness:

| fold | valid year | status | caveat |
|---|---:|---|---|
| A | 2022 | usable | proxy-label-heavy validation |
| B | 2023 | usable | 41 of 42 rows have STATIZ outcomes |
| C | 2024 | usable | 43 of 43 rows have STATIZ outcomes |
| D | 2025 | usable | 44 of 44 rows have STATIZ outcomes |

Target-only columns from the label table must not enter candidate ranking features. They can be used only for training labels, validation scoring, threshold calibration, and error analysis.

### 2026 Sensitivity Rule

Every SSG message or candidate feature using 2026 data must be reported in two versions:

- `with_2026_current`: current-season form and urgency.
- `without_2026_current`: historical stability from 2023-2025.

Promotion rule:

- if both agree, promote;
- if only 2026 agrees, mark as urgent but unstable;
- if only history agrees, mark as structural but not currently urgent;
- if both disagree, reject.

### Candidate Ranking Robustness

Final shortlist candidates must pass:

- hard gates before baseball scoring;
- at least one model family beyond a trivial stat ranking;
- leave-one-feature-family-out sensitivity;
- 2026-included and 2026-excluded comparison;
- manual contradiction check for contract, injury, and role feasibility.
