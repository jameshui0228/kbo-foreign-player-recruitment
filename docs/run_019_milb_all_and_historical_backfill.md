# Run 019 MiLB All-Candidate And Historical Backfill

Date: 2026-06-14 KST

Layer focus:

- 2. KBO foreign-player success/failure archetype mining
- 3. Candidate market construction
- 4. KBO translation model
- 5. Failure risk model

Candidate policy: locked. This run expands data coverage but does not release recommendations or shortlist labels.

## Purpose

The previous MiLB layer covered the research-lead and medical-hold subset, but not the full current market. It also did not backfill comparable pre-KBO MiLB features for historical KBO foreign-player labels.

Run 019 does two things:

1. Expands MiLB year-by-year stats from the partial candidate scope to all current MLB replacement-market rows.
2. Collects pre-KBO MiLB history for historical KBO foreign-player rows that already have MLBAM/Savant ID matches.

## New And Updated Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/milb_market_pool_stats_all_v1.csv` | 18,258 | AAA/AA/High-A/Single-A/Rookie year-by-year stats for all 1,745 current market rows |
| `outputs/tables/milb_market_pool_stats_request_audit_all_v1.csv` | 8,725 | Request audit for 1,745 market rows x 5 minor-league levels |
| `outputs/tables/mlb_market_pool_milb_role_context_v1.csv` | 1,745 | Current market rows with refreshed MiLB role/level continuity features |
| `outputs/tables/mlb_market_pool_milb_role_context_summary_v1.csv` | 50 | Current market MiLB role-context summary |
| `outputs/tables/historical_kbo_prearrival_milb_stats_v1.csv` | 981 | Pre-KBO MiLB year-by-year rows for historical KBO foreign-player MLBAM matches |
| `outputs/tables/historical_kbo_prearrival_milb_request_audit_v1.csv` | 280 | Historical request audit |
| `outputs/tables/historical_kbo_prearrival_milb_features_v1.csv` | 71 | Historical pre-KBO MiLB feature rows |
| `src/data/collect_historical_kbo_milb_stats.py` | script | Reproducible historical MiLB backfill collector |

## Current Market Coverage Improvement

Before this run:

- MiLB current-market scope: 883 candidate rows requested.
- MiLB request audit: 4,415 requests.
- MiLB stat rows: 9,560.
- Market rows with MiLB stat track: 848.
- Rows outside Run 013 scope: 862.

After this run:

- MiLB current-market scope: all 1,745 market rows requested.
- MiLB request audit: 8,725 requests.
- MiLB request status: 8,725 of 8,725 HTTP 200.
- MiLB stat rows: 18,258.
- Market rows with MiLB stat track: 1,664.
- Rows outside collection scope: 0.

## Role Context After Full MiLB Refresh

| bucket | rows |
|---|---:|
| no 2026 MiLB track | 815 |
| recent 2025-2026 track, noncurrent | 158 |
| current AAA bullpen track | 134 |
| current AAA regular hitter | 128 |
| current AAA part-time hitter | 124 |
| current AAA swing/multi-inning pitcher | 107 |
| current AAA starter load | 94 |
| current AAA tiny sample | 88 |
| no MiLB stats found | 81 |
| current lower-level risk | 16 |

These are market-context buckets, not recommendations.

## Historical KBO Backfill

The historical backfill covers KBO foreign-player rows already matched to MLBAM/Savant IDs.

| item | count |
|---|---:|
| historical KBO rows requested | 71 |
| unique player/stat groups | 56 |
| MiLB requests | 280 |
| successful requests | 280 |
| raw stat rows | 981 |
| feature rows | 71 |
| rows with pre-KBO MiLB features | 71 |

By role:

| role | rows | rows with pre-KBO MiLB |
|---|---:|---:|
| hitter | 22 | 22 |
| pitcher | 49 | 49 |

By KBO season:

| season | rows | rows with pre-KBO MiLB |
|---:|---:|---:|
| 2023 | 19 | 19 |
| 2024 | 26 | 26 |
| 2025 | 26 | 26 |

## Why This Helps The Model

Layer 3 improves because every current MLB replacement-market row now has an attempted AAA/AA/minors lookup, rather than only the research-lead subset.

Layer 4 improves because historical KBO labels now have comparable pre-arrival MiLB level/role variables for the matched MLBAM subset.

Layer 2 improves because success/failure archetypes can now be described using pre-KBO level and role context, not only KBO outcome labels and public MLB Statcast matches.

Layer 5 improves slightly because stale-track, current-role, no-current-track, and lower-level-risk flags are now attached across the full current MLB market.

## Remaining Gaps

- KBO/STATIZ current refresh after 2026-06-11 still requires local `STATIZ_API_KEY` and `STATIZ_API_SECRET` environment variables.
- Historical backfill covers MLBAM-matched KBO rows, not every 2017-2022 KBO foreign player.
- MiLB data is official year-by-year basic stats, not full MiLB Statcast pitch/play-level or batted-ball data.
- NPB salary, contract, buyout, universal nationality, medical/news, and Korea-willingness remain unresolved.
- Candidate names remain locked until the fit-ranking gates clear.

## Six-Layer Progress After Run 019

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 62% | 55% -> 62% |
| 3 | Candidate market construction | 80% | 72% -> 80% |
| 4 | KBO translation model | 64% | 56% -> 64% |
| 5 | Failure risk model | 58% | 53% -> 58% |
| 6 | SSG fit ranking | 28% | 25% -> 28% |

Candidate release remains locked.
