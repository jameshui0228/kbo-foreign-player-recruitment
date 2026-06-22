# Run 036 Locked Manual Review Template v0.1

Date: 2026-06-22 KST

Layer focus:

- 6. SSG fit ranking

Candidate policy: locked. This run creates a manual scouting and source-review
input template for the locked scouting cards. It does not release candidate
names, teams, exact scores, exact ranks, shortlist labels, manual unlock labels,
or recommendations.

## Purpose

Run 035 created candidate-name-free scouting-card templates. Run 036 gives
reviewers a controlled place to fill the missing human/source evidence:

- video/report sources;
- stat/source URLs;
- contract/salary/option/buyout evidence;
- medical/current availability evidence;
- Korea/overseas willingness evidence;
- 20-80 manual grades;
- green flags, red flags, and reviewer summary.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/locked_scouting_card_manual_review_template_v0_1.csv` | 72 | blank manual input template matched to locked card IDs |
| `outputs/tables/locked_scouting_card_manual_review_rubric_v0_1.csv` | 24 | field-level guidance and allowed values |
| `outputs/tables/locked_scouting_card_manual_grade_scale_v0_1.csv` | 9 | 20-80 grade interpretation |
| `outputs/tables/locked_scouting_card_manual_review_summary_v0_1.csv` | 2 | slot/status counts |
| `outputs/tables/locked_scouting_card_manual_review_gate_audit_v0_1.csv` | 4 | template and release-lock audit |
| `src/modeling/build_locked_scouting_card_manual_review_template_v0_1.py` | script | reproducible builder |

## Template Scope

| slot | cards | review status |
|---|---:|---|
| Foreign hitter | 31 | not started |
| Foreign pitcher | 41 | not started |

All manual input fields intentionally start blank. The default decision status is
`locked_no_decision`.

## Manual Fields

The template includes:

- reviewer and date;
- video/report/stat source URLs;
- contract, medical, and Korea-willingness source URLs;
- 20-80 grades for tool/process, contact/command, role fit, workload/defense,
  KBO translation confidence, medical availability, contract feasibility,
  Korea-willingness, and overall manual grade;
- green flags, red flags, reviewer summary, continue reason, kill reason;
- manual decision status.

## Gate Audit

| gate | result |
|---|---|
| template rows match locked cards | pass, 72 / 72 |
| manual input fields start blank | pass, 72 / 72 |
| candidate identifiers removed | pass |
| release locks preserved | pass, 72 / 72 |

The template excludes:

- `player_name`
- `team_or_org`
- exact internal fit score
- exact internal rank

All rows keep:

- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `rank_release_allowed = False`
- `shortlist_label_allowed = False`
- `is_final_recommendation = False`
- `scouting_card_release_allowed = False`
- `manual_review_unlock_allowed = False`
- `recommendation_label = locked_not_allowed`

## Six-Layer Progress After Run 036

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 90% | unchanged |
| 6 | SSG fit ranking | 87% | 85% -> 87% |

Candidate release remains locked.

## Current Message

Layer 6 now has a real manual-review workflow:

> The model has handed off anonymous cards. The next work is human evidence:
> video, scouting notes, contract proof, medical proof, and Korea-willingness
> proof. No card becomes a candidate until those fields are filled.

## Remaining Gaps

- Manual review fields are blank by design.
- Exact contract, medical, and willingness values are still missing.
- Candidate names, scores, ranks, shortlist labels, manual unlock labels, and
  recommendations stay locked.
