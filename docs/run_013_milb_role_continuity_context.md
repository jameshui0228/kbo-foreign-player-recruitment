# Run 013 MiLB Role Continuity Context

Generated: 2026-06-14 KST

## Objective

Run 013 adds a MiLB role/level continuity layer before candidate ranking.

The purpose is to answer scouting-process questions that public MLB Statcast and roster status do not answer well:

- Is the pitcher currently stretched out as a starter or only working as a bullpen arm?
- Is the player performing at AAA/AA or only showing lower-level activity?
- Does the candidate have a live 2026 track, or is the profile stale?
- For hitters, is there enough current AAA PA to treat the offensive line as more than a tiny sample?

This is still not a final recommendation layer.

## Six-Layer Progress After Run 013

| no. | layer | before | after | movement |
|---:|---|---:|---:|---|
| 1 | SSG hidden weakness mining | 75% | 75% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 55% | 55% | unchanged |
| 3 | Candidate market construction | 60% | 68% | MiLB role/level context added to research-lead and medical-hold rows |
| 4 | KBO translation model | 50% | 56% | new candidate-side MiLB variables exist; historical backfill still needed |
| 5 | Failure risk model | 45% | 53% | role continuity and current-staleness risk are now measurable |
| 6 | SSG fit ranking | 20% | 25% | ranking inputs improved, but final ranking remains locked |

## Data Collected

| source | output | rows |
|---|---:|---:|
| MLB Stats API player MiLB year-by-year stats | `outputs/tables/milb_market_pool_stats_research_plus_medical_v1.csv` | 9,560 |
| MiLB request audit | `outputs/tables/milb_market_pool_stats_request_audit_research_plus_medical_v1.csv` | 4,415 |
| MiLB role continuity feature mart | `outputs/tables/mlb_market_pool_milb_role_context_v1.csv` | 1,745 |
| MiLB role continuity summary | `outputs/tables/mlb_market_pool_milb_role_context_summary_v1.csv` | 31 |

Collection scope:

- candidate policies collected:
  - `research_lead_only_manual_check_required`
  - `hold_medical_context_required`
- candidate policies not collected in this run:
  - `market_watch_low_access`
  - `market_watch_manual_check_required`
- levels collected:
  - AAA `sportId=11`
  - AA `sportId=12`
  - High-A `sportId=13`
  - Single-A `sportId=14`
  - Rookie `sportId=16`

## Coverage

| slot | policy | rows | requested | has MiLB stat track |
|---|---|---:|---:|---:|
| hitter OF-priority | hold medical | 163 | 163 | 161 |
| hitter OF-priority | research lead | 176 | 176 | 175 |
| pitcher | hold medical | 279 | 279 | 267 |
| pitcher | research lead | 265 | 265 | 245 |

Rows outside the Run 013 scope are explicitly marked:

- `not_collected_in_run_013_scope`

This prevents confusion between "not collected" and "no MiLB stats found."

## Main Bucket Signals

Pitcher buckets:

| bucket | rows | interpretation |
|---|---:|---|
| `current_aaa_starter_load` | 76 | currently stretched out at AAA; most useful for foreign-starter screening |
| `current_aaa_swing_or_multi_inning` | 79 | possible swingman/multi-inning track |
| `current_aaa_bullpen_track` | 100 | available arm but not a starter-fit proof |
| `no_2026_milb_track` | 135 | stale or non-current MiLB track; needs news/medical/context review |
| `recent_2025_2026_track_noncurrent` | 114 | recent track exists but not a live 2026 MiLB row |
| `no_milb_stats_found` | 32 | requested, but no MiLB split returned |

Hitter buckets:

| bucket | rows | interpretation |
|---|---:|---|
| `current_aaa_regular` | 85 | enough current AAA PA to be a more usable hitter-screen input |
| `current_aaa_part_time` | 79 | current AAA activity but sample or role is smaller |
| `current_aaa_tiny_sample` | 78 | current AAA row exists, but sample risk remains high |
| `no_2026_milb_track` | 79 | stale/non-current track; needs context review |
| `recent_2025_2026_track_noncurrent` | 11 | recent but not live 2026 activity |
| `no_milb_stats_found` | 3 | requested, but no MiLB split returned |

## Modeling Use

Run 013 adds candidate-side variables for:

- market realism;
- role continuity;
- sample freshness;
- starter-stretch risk;
- AAA/AA level quality;
- hitter current-PA sample sufficiency.

These variables should feed:

1. KBO translation model candidate scoring;
2. failure-risk model;
3. eventual SSG fit ranking.

But they are not yet enough to unlock final names because historical KBO foreign-player rows still need comparable MiLB role/level backfill.

## Remaining Blocks

Next work should add:

- historical MiLB role/level context for prior KBO foreign players;
- injury/news/adaptation full-text features;
- contract, opt-out, salary, and Korea-willingness checks;
- ABL roster and Asian-quota gaps;
- market-watch MiLB collection if the project wants full 1,745-row coverage.

## Source URLs

- MLB Stats API sports list: https://statsapi.mlb.com/api/v1/sports
- MLB Stats API player stats pattern: https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=yearByYear&group=pitching&sportId=11
