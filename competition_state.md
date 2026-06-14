# Competition State

Updated: 2026-06-12 KST

## Project Type

- Type: sports analytics / player acquisition recommendation.
- Decision unit: one recruitment slot and one candidate profile.
- Required slots: foreign hitter, foreign pitcher, Asian quota player.
- Output artifact: evidence-backed recruitment message, candidate screen, and final shortlist.

## Current Objective

Build the project like a competition workflow:

1. Audit data and source risk.
2. Mine unusual SSG-specific signals.
3. Convert signals into feature hypotheses.
4. Score slot-specific messages using evidence cards.
5. Apply contract, rule, medical, and availability gates before candidate scoring.
6. Build candidate screens only after the message has evidence support and the market bucket is realistic.
7. Keep a reproducible experiment log.

## Current Best Messages

| slot | current message | evidence status |
|---|---|---|
| Foreign hitter | The Runway Converter | Strong SSG-specific STATIZ evidence; needs candidate-level batted-ball validation |
| Foreign pitcher | ABS-Native Load-Bearing Starter | Strongest total evidence score; needs candidate-level KBO/ABS pitch-location validation |
| Asian quota | The Option Layer | Plausible and actionable; market outcome history limited because 2026 is the first year |

## Current Evidence Scores

Source: `outputs/tables/message_mining_slot_scores_v1.csv`

| slot | message_id | evidence cards | total score |
|---|---|---:|---:|
| Foreign pitcher | `abs_native_load_bearing_starter` | 4 | 74 |
| Foreign hitter | `runway_converter` | 3 | 56 |
| Asian quota | `option_layer` | 3 | 48 |

## Next Milestone

Move from message mining to realistic candidate mining:

- hitter candidate screen: OF/DH runway-converter features.
- pitcher candidate screen: ABS-native six-inning stabilizer features.
- Asian quota candidate screen: option-layer swingman/long-bridge features.
- hard gate layer: KBO rules, cost ceiling, current SSG foreign-player baseline, medical risk, availability timing.

The next deliverable is a candidate scoring schema, not a final candidate list.
