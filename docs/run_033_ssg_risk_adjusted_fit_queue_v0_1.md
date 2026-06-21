# Run 033 SSG Risk-Adjusted Fit Queue v0.1

Date: 2026-06-22 KST

Layer focus:

- 6. SSG fit ranking

Candidate policy: locked. This run creates an internal risk-adjusted review
queue, not a public ranking, shortlist, or recommendation.

## Purpose

Run 032 decomposed candidate failure risk. Run 033 connects that risk layer back
to SSG fit.

The goal is to answer:

> If a candidate looks like an SSG fit, does that still hold after market,
> translation, failure-risk, and data-gap penalties?

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_risk_adjusted_fit_queue_v0_1.csv` | 2,723 | locked candidate-level risk-adjusted SSG fit queue |
| `outputs/tables/ssg_risk_adjusted_fit_slot_summary_v0_1.csv` | 13 | lane counts and score/risk summaries by slot |
| `outputs/tables/ssg_risk_adjusted_fit_factor_summary_v0_1.csv` | 91 | component medians by slot and review lane |
| `outputs/tables/ssg_risk_adjusted_fit_sensitivity_v0_1.csv` | 15 | weight-variant sensitivity summary |
| `outputs/tables/ssg_risk_adjusted_fit_gate_audit_v0_1.csv` | 4 | release-lock and queue audit |
| `src/modeling/build_ssg_risk_adjusted_fit_queue_v0_1.py` | script | reproducible builder |

## Model Stack

The internal fit queue uses the Dacon-style final-score structure from
`docs/modeling_strategy_dacon_style_v1.md`.

Positive components:

- SSG fit component;
- KBO translation readiness component;
- market realism component;
- slot-specific tool/process component;
- surplus/access component.

Penalty and confidence components:

- failure-risk penalty from Run 032;
- source-confidence adjustment from data-gap risk;
- sensitivity bands across alternate weight sets.

The score is internal only. It is not a public recommendation score.

## Review Lanes

| slot | blocked / medical | source-fill priority | deep review | market watch | low priority |
|---|---:|---:|---:|---:|---:|
| Asian quota | 0 | 18 | 0 | 132 | 828 |
| Foreign hitter | 366 | 4 | 37 | 74 | 255 |
| Foreign pitcher | 730 | 2 | 47 | 86 | 144 |

Interpretation:

- Foreign hitter now has a small locked deep-review pool where SSG fit,
  translation readiness, market realism, and failure-risk controls align.
- Foreign pitcher also has a locked deep-review pool, but most pitcher rows are
  blocked by medical, role-fit, data-gap, or contract-access risk.
- Asian quota has no clean deep-review lane yet. The best rows are still
  source-fill priorities because nationality, contract, buyout, and source
  confidence remain the real blockers.

## Sensitivity Result

The model tests five weight variants:

- default Dacon-style;
- SSG-fit heavy;
- risk-conservative;
- market-realism heavy;
- translation-heavy.

Stable rows across those variants:

| slot | stable top 25 | stable top 50 |
|---|---:|---:|
| Asian quota | 11 | 18 |
| Foreign hitter | 23 | 49 |
| Foreign pitcher | 24 | 50 |

This means the queue is not only a one-weight ranking. It separates candidates
whose review priority survives reasonable scoring changes from candidates whose
priority is weight-sensitive.

## Gate Audit

| gate | result |
|---|---|
| all candidates receive internal risk-adjusted fit score | pass, 2,723 / 2,723 |
| sensitivity variants attached | pass, 2,723 / 2,723 |
| release locks preserved | pass, 2,723 / 2,723 |
| source gaps visible | pass with visible gap, 1,120 / 2,723 |

All rows keep:

- `is_final_recommendation = False`
- `shortlist_label_allowed = False`
- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `rank_release_allowed = False`
- `recommendation_label = locked_not_allowed`

## Six-Layer Progress After Run 033

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 94% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 89% | unchanged |
| 6 | SSG fit ranking | 80% | 72% -> 80% |

Candidate release remains locked.

## Current Message

Layer 6 is now a real decision queue:

> The project is no longer sorting by surface talent. It is asking which
> candidates still look like SSG fits after KBO translation risk, failure mode,
> market access, source confidence, and weight sensitivity are all applied.

## Remaining Gaps

- Scores are internal and not calibrated final surplus-value estimates.
- Salary, opt-out, buyout, agent, medical-file, and Korea-willingness source
  values still need manual fill.
- Asian quota still needs stronger nationality/passport and contract-source
  verification.
- Candidate names, ranks, scores, shortlist labels, and recommendations stay
  locked.
