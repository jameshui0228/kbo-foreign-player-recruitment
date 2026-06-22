# Run 035 Locked Scouting Cards v0.1

Date: 2026-06-22 KST

Layer focus:

- 6. SSG fit ranking

Candidate policy: locked. This run creates candidate-name-free scouting-card
templates. It does not release candidate names, teams, exact scores, exact
ranks, shortlist labels, scouting-card release, or recommendations.

## Purpose

Run 034 separated the Layer 6 queue into source-actionable rows and source-
blocked rows. Run 035 turns the source-supported rows into a review template.

The goal is not to name candidates. The goal is to give every reviewer the same
questions:

> What SSG need does this card claim to solve, what evidence supports that
> claim, and what would still kill the case?

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/locked_scouting_card_templates_v0_1.csv` | 72 | candidate-name-free locked card templates |
| `outputs/tables/locked_scouting_card_schema_v0_1.csv` | 10 | required card fields and prompts |
| `outputs/tables/locked_scouting_card_question_bank_v0_1.csv` | 15 | slot-specific manual review questions |
| `outputs/tables/locked_scouting_card_slot_summary_v0_1.csv` | 5 | slot and band summary |
| `outputs/tables/locked_scouting_card_gate_audit_v0_1.csv` | 4 | release-lock audit |
| `src/modeling/build_locked_scouting_cards_v0_1.py` | script | reproducible card builder |

## Card Scope

Cards were built only from rows with:

- `source_fill_readiness_bucket = source_supported_scouting_card_next_locked`

| slot | locked cards |
|---|---:|
| Foreign hitter | 31 |
| Foreign pitcher | 41 |
| Asian quota | 0 |

Asian quota was not promoted to scouting cards because it remains blocked by
passport/nationality, contract, buyout, medical, and source-confidence issues.

## Card Design

The card output removes:

- player name;
- team or organization;
- exact internal fit score;
- exact internal rank;
- shortlist/recommendation labels.

Each card keeps only review-safe information:

- locked card ID;
- slot;
- public-safe fit thesis;
- banded SSG fit, translation, market, tool/process, surplus, risk, and source
  confidence;
- primary risk focus;
- source-status summary;
- manual review questions;
- next source actions.

## Gate Audit

| gate | result |
|---|---|
| cards built from source-supported rows | pass, 72 / 72 |
| candidate identifiers removed | pass |
| release locks preserved | pass, 72 / 72 |
| Asian quota not promoted to card | pass, 72 / 72 |

All rows keep:

- `candidate_name_release_allowed = False`
- `score_release_allowed = False`
- `rank_release_allowed = False`
- `shortlist_label_allowed = False`
- `is_final_recommendation = False`
- `scouting_card_release_allowed = False`
- `recommendation_label = locked_not_allowed`

## Six-Layer Progress After Run 035

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 78% | unchanged |
| 3 | Candidate market construction | 95% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 90% | unchanged |
| 6 | SSG fit ranking | 85% | 83% -> 85% |

Candidate release remains locked.

## Current Message

Layer 6 now has a real scouting handoff:

> We can review profiles without leaking names or pretending we have a final
> shortlist. The model now hands scouts and teammates a structured card: SSG
> fit claim, translation question, tool/process question, failure mode, market
> reality, and source actions.

## Remaining Gaps

- Cards are templates, not recommendations.
- Candidate names remain locked.
- Exact scores and ranks remain locked.
- Manual scouting notes, contract values, medical status, and Korea-willingness
  evidence still need to be filled before final candidate discussion.
