# Run 023 Locked SSG Fit Preparation Mart v0.1

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 4. KBO translation model
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run creates a research-only fit preparation mart. It does not create a shortlist, final ranking, or recommendation.

## Purpose

Run 022 attached candidate-side signals separately by slot. Run 023 puts those signals onto one SSG-facing review table:

- foreign hitter: SSG Layer 1 hitter need + validated hitter Savant pilot component;
- foreign pitcher: SSG pitcher need + MiLB damage/command diagnostic only;
- Asian quota: nationality/contract feasibility + NPB official-stat context when available.

The output is meant to tell the team what to check next, not who to sign.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_fit_preparation_mart_v0_1.csv` | 2,723 | locked three-slot research mart |
| `outputs/tables/ssg_fit_preparation_slot_summary_v0_1.csv` | 3 | slot-level row counts and index summaries |
| `outputs/tables/ssg_fit_preparation_gate_audit_v0_1.csv` | 5 | release-lock and blocker audit |
| `outputs/tables/ssg_fit_preparation_feature_contract_v0_1.csv` | 10 | Layer 1 feature contract to candidate-side proxy map |
| `src/modeling/build_ssg_fit_preparation_mart_v0_1.py` | script | reproducible mart builder |

## Slot Coverage

| slot | rows | median fit-prep index | p75 fit-prep index | top status |
|---|---:|---:|---:|---|
| Asian quota | 978 | 54.854 | 56.799 | nationality manual check needed |
| Foreign hitter | 736 | 47.830 | 56.451 | neutral research inventory locked |
| Foreign pitcher | 1,009 | 38.294 | 47.217 | missing/stale MiLB context review |

## Research Status Counts

| slot | status | rows |
|---|---|---:|
| Asian quota | manual contract/salary/buyout check locked | 154 |
| Asian quota | nationality manual check needed | 772 |
| Asian quota | regular foreign only, not Asian quota | 52 |
| Foreign hitter | research inventory high signal locked | 27 |
| Foreign hitter | neutral research inventory locked | 446 |
| Foreign hitter | risk review needed | 261 |
| Foreign hitter | feature coverage gap review | 2 |
| Foreign pitcher | diagnostic watch locked | 79 |
| Foreign pitcher | diagnostic neutral review | 192 |
| Foreign pitcher | risk review needed | 271 |
| Foreign pitcher | missing/stale MiLB context review | 467 |

## Scoring Interpretation

The `fit_preparation_index` is not a player-quality score.

For hitters, the index combines:

- validated hitter Savant pilot component;
- SSG RHP game-script unlock proxy;
- two-strike/contact survival proxy;
- market access, availability gate, and feature coverage.

For pitchers, the index is diagnostic only:

- MiLB damage/command watch score;
- starter runway and current role context;
- traffic/command proxy;
- market access and availability.

For Asian quota, the index is a feasibility priority:

- nationality gate;
- contract/salary/buyout unknown status;
- club-control access;
- current Asian-league roster context;
- NPB official-stat context where available.

## Gate Audit

| gate | status | result |
|---|---|---|
| no final recommendations | pass | 2,723 / 2,723 locked |
| no shortlist labels | pass | 2,723 / 2,723 locked |
| candidate-name release locked | pass | 2,723 / 2,723 locked |
| pitcher score not promoted | pass | 1,009 / 1,009 diagnostic only |
| Asian-quota contract gap visible | pass with visible gap | 978 / 978 still need contract/salary/buyout checks |

Every row keeps:

- `is_final_recommendation = False`
- `shortlist_label_allowed = False`
- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `recommendation_label = locked_not_allowed`

## Interpretation

This is the first proper SSG fit table, but it is still a preparation mart.

What improved:

- The three acquisition slots now live in one table.
- The SSG Layer 1 feature contract is attached to candidate-side proxies.
- Hitter translation is usable as a pilot component.
- Pitcher risk is visible without pretending the pitcher model is promoted.
- Asian quota now separates nationality fail, nationality unknown, and nationality-pass/contract-unknown rows.

What is still blocked:

- No final candidate ranking until manual market checks are added.
- Pitcher translation/failure model is still not promoted.
- Asian quota needs salary, contract, buyout, and agent/willingness checks.
- Current STATIZ refresh and stronger play-by-play defense/baserunning proxies are still desirable before final presentation.

## Six-Layer Progress After Run 023

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | 72% -> 73% |
| 3 | Candidate market construction | 85% | 83% -> 85% |
| 4 | KBO translation model | 80% | 78% -> 80% |
| 5 | Failure risk model | 71% | 68% -> 71% |
| 6 | SSG fit ranking | 52% | 40% -> 52% |

Candidate release remains locked.

## Next Step

Run 024 should add the missing manual/market realism layer:

- MLB and NPB/CPBL contract, salary, buyout, and club-control checks;
- injury/news/adaptation and Korea-willingness text signals;
- pitcher-specific medical/role-risk context;
- Asian quota nationality verification and agent feasibility checks.
