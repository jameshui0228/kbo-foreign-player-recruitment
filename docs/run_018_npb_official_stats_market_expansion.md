# Run 018 NPB Official Stats Market Expansion

Date: 2026-06-14 KST

Layer focus: 3. Candidate market construction.

Candidate policy: locked. This run expands the NPB market layer but does not recommend or shortlist players.

## Purpose

Before this run, the Asian market layer had NPB official rosters but not current NPB performance context. That was too shallow for realistic candidate-market construction.

Run 018 expands NPB coverage by collecting official NPB 2026 player stats for:

- regular-season batting;
- regular-season pitching;
- farm-league batting;
- farm-league pitching.

The collection uses official NPB English stat pages with the pattern:

- `https://npb.jp/bis/eng/2026/stats/idb1_{team}.html`
- `https://npb.jp/bis/eng/2026/stats/idp1_{team}.html`
- `https://npb.jp/bis/eng/2026/stats/idb2_{team}.html`
- `https://npb.jp/bis/eng/2026/stats/idp2_{team}.html`

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/npb_official_player_stats_2026_v1.csv` | 2,186 | Unified official NPB 2026 first-team/farm batting and pitching stats |
| `outputs/tables/npb_official_stats_source_inventory_2026_v1.csv` | 48 | Source inventory for 12 teams x 4 official stat pages |
| `outputs/tables/npb_player_market_features_2026_v1.csv` | 2,186 | NPB stats joined to roster/nationality seed and market role features |
| `outputs/tables/npb_market_depth_summary_2026_v1.csv` | 24 | NPB market depth by level, stat type, league, and role bucket |
| `src/data/collect_npb_official_stats_2026.py` | script | Reproducible collector |

## Coverage

| level | stat type | rows |
|---|---|---:|
| NPB first team | batting | 617 |
| NPB first team | pitching | 313 |
| NPB farm | batting | 835 |
| NPB farm | pitching | 421 |

All 48 official pages were parsed successfully.

## Market Role Buckets

| level | stat type | bucket | rows |
|---|---|---|---:|
| first team | batting | regular batter, PA >= 100 | 118 |
| first team | batting | part-time batter, PA 40-99 | 65 |
| first team | pitching | pitcher 30+ IP | 70 |
| first team | pitching | pitcher 10-30 IP | 134 |
| farm | batting | regular batter, PA >= 100 | 108 |
| farm | batting | part-time batter, PA 40-99 | 144 |
| farm | pitching | pitcher 30+ IP | 60 |
| farm | pitching | pitcher 10-30 IP | 172 |

These are market-inventory buckets, not recommendation labels.

## Features Added

Batters:

- OPS
- ISO
- BB%
- SO%
- HR/PA
- SB success%
- GDP+CS run-kill proxy
- regular/part-time playing-time flags

Pitchers:

- innings converted to decimal innings
- calculated WHIP
- K%
- BB%
- K-BB%
- K/9
- BB/9
- HR/9
- 30+ IP workload proxy
- traffic-command proxy

## Why This Helps Layer 3

The NPB market is now deeper than a roster list. We can identify:

- players with current first-team performance;
- farm players with current playing-time signal;
- pitchers with workload and command signals;
- hitters with OBP/damage and run-kill proxies;
- known foreign-player seeds where nationality was available from the existing seed table.

This still does not unlock recommendations because NPB official pages do not provide:

- salary;
- contract length;
- buyout/release feasibility;
- universal nationality;
- Korea-willingness;
- medical context.

## Updated Layer 3 Conclusion

Layer 3 moves from 68% to 72%.

The NPB side now has official 2026 performance context. The next candidate-market gap is feasibility:

1. Add NPB nationality verification for non-foreign-seed players.
2. Add salary/contract/buyout or at least proxy tiers.
3. Add ABL roster and stats.
4. Add news/manual market feasibility checks.
5. Then connect NPB/CPBL market rows into SSG fit ranking.

## Six-Layer Progress After Run 018

| no. | layer | progress | movement | candidate status |
|---:|---|---:|---|---|
| 1 | SSG hidden weakness mining | 93% | unchanged | presentation/scoring-ready pending refresh |
| 2 | KBO foreign-player success/failure archetype mining | 55% | unchanged | not enough for final names |
| 3 | Candidate market construction | 72% | 68% -> 72% | research leads only |
| 4 | KBO translation model | 56% | unchanged | pilot only |
| 5 | Failure risk model | 53% | unchanged | pilot only |
| 6 | SSG fit ranking | 25% | unchanged | locked |

## Validation

- `src/data/collect_npb_official_stats_2026.py` was py-compiled.
- The collector was rerun.
- 48 source pages were parsed successfully.
- Output row counts were inspected:
  - official stats: 2,186 rows;
  - source inventory: 48 rows;
  - market features: 2,186 rows;
  - depth summary: 24 rows.

## Caveats

- This is official NPB performance data, not salary or contract data.
- Nationality remains incomplete for NPB players because the official English roster/stat pages do not expose nationality for all players.
- Candidate names remain locked until Layers 2-6 clear their gates.
