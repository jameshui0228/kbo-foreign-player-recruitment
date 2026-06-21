# Run 032 Candidate Failure Risk Ledger v0.1

Date: 2026-06-22 KST

Layer focus:

- 5. Failure risk model

Candidate policy: locked. This run builds a risk ledger, not a shortlist,
ranking, or recommendation.

## Purpose

Layer 2 now describes historical KBO success/failure archetypes. Layer 3 now
describes current market realism and source gaps. This run combines them into a
candidate-side failure-risk ledger.

The goal is not "highest score wins." The goal is to explain, before any
shortlist is released, why a candidate could fail.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/candidate_failure_risk_ledger_v0_1.csv` | 2,723 | candidate-level six-bucket failure-risk ledger |
| `outputs/tables/candidate_failure_risk_slot_summary_v0_1.csv` | 11 | slot and review-tier summary |
| `outputs/tables/candidate_failure_risk_bucket_summary_v0_1.csv` | 18 | bucket-level risk distribution by slot |
| `outputs/tables/candidate_failure_risk_gate_audit_v0_1.csv` | 4 | release-lock and integration audit |
| `src/modeling/build_candidate_failure_risk_ledger_v0_1.py` | script | reproducible builder |

## Risk Buckets

Each candidate now has six separate risk buckets:

- medical/availability risk;
- contract/cost/access risk;
- role-fit risk;
- KBO translation risk;
- adaptation/Korea-willingness risk;
- data/source-gap risk.

The final `failure_risk_index` is an internal research index only. It is not a
public ranking score and cannot be released as a candidate recommendation.

## Slot Risk-Tier Distribution

| slot | tier 1 blocker | tier 2 multi-risk | tier 3 watch | tier 4 low current risk |
|---|---:|---:|---:|---:|
| Asian quota | 0 | 154 | 410 | 414 |
| Foreign hitter | 355 | 303 | 31 | 47 |
| Foreign pitcher | 722 | 160 | 80 | 47 |

## Bucket Findings

### Foreign pitcher

The main blocker is not one thing:

- 722 tier-1 blocker rows;
- 359 high medical/availability rows;
- 829 high contract/cost/access rows;
- 722 high role-fit rows;
- 896 high data/source-gap rows;
- 351 rows with a Layer 2 pitcher archetype flag.

The important Layer 2 pitcher flags are:

- raw miss without role continuity;
- role continuity as a replacement-risk suppressor;
- volatile stuff profile review.

Interpretation:

For the pitcher slot, we should not chase strikeout upside by itself. The risk
model now asks whether raw miss is supported by workload continuity, role
continuity, damage suppression, and source-checked health/contract
availability.

### Foreign hitter

The hitter side is still less stable as a historical archetype model, but it now
has usable candidate-side warning tags:

- 355 tier-1 blocker rows;
- 219 high medical/availability rows;
- 623 high contract/cost/access rows;
- 262 high role-fit rows;
- 100 high KBO-translation rows;
- 325 rows with a Layer 2 hitter flag.

The main Layer 2 hitter flags are:

- negative hitter pilot translation signal;
- contact-floor review.

Interpretation:

The hitter model should continue to use the Savant pilot component, but not as a
final ranking score. It is most useful as a warning system for contact-floor and
translation risk.

### Asian quota

Asian-quota failure risk is dominated by source and feasibility gaps, not by a
promoted historical KBO translation model:

- 154 tier-2 multi-risk rows;
- 926 high contract/cost/access rows;
- 154 high data/source-gap rows;
- 978 rows carry the Layer 2 Asian-quota historical translation gap flag.

Interpretation:

Asian-quota evaluation still needs historical NPB/CPBL pre-arrival backfill,
contract/buyout source values, and nationality/passport verification before a
real ranking can be trusted.

## Gate Audit

| gate | result |
|---|---|
| all candidates receive six risk buckets | pass, 2,723 / 2,723 |
| Layer 2 archetype flags attached | partial pass, 1,654 / 2,723 |
| manual source lanes integrated | visible gap, 1,703 / 2,723 |
| release locks preserved | pass, 2,723 / 2,723 |

## Six-Layer Progress After Run 032

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 94% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 89% | 85% -> 89% |
| 6 | SSG fit ranking | 72% | 71% -> 72% |

Candidate release remains locked.

## Current Message

The project now has a real failure-risk layer:

> We are not just asking who looks good. We are asking which failure mode each
> candidate is exposed to, and whether that risk is a true baseball risk, a
> market/contract blocker, or simply a missing-source problem.

## Remaining Gaps

- Risk buckets are not calibrated final probabilities.
- Contract salary, opt-out, buyout, transfer-fee, and agent willingness values
  are still source lanes, not solved values.
- Medical flags are still public roster/news proxies and need file-level review.
- Asian-quota historical translation is still blocked by NPB/CPBL pre-arrival
  backfill.
- Candidate names, scores, rankings, shortlist labels, and recommendations stay
  locked.
