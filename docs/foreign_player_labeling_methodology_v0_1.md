# KBO Foreign-Player Labeling Methodology v0.1

Generated: 2026-06-12 KST

## Purpose

This table is the first supervised-validation target for the recruitment model.

It should answer:

> Would our model have identified past KBO foreign-player success and avoided past failure before seeing the KBO outcome?

It is not a candidate feature table. Every post-KBO performance column is target-only.

## Sources

| source | use | confidence |
|---|---|---:|
| Korean Wikipedia yearly KBO foreign-player templates | season roster, released-player list, release reasons | 3-4 |
| STATIZ season profiles | 2023-2025 KBO outcome stats: PA, IP, WAR, wRC+, ERA | 4 |
| next-year template appearance | renewal proxy | 2-3 |

Raw template HTML is cached under:

- `data/external/kbo_foreign_players/wiki_templates/`

## Output Tables

| table | purpose |
|---|---|
| `outputs/tables/kbo_foreign_player_season_labels_v0_1.csv` | player-season label table |
| `outputs/tables/kbo_foreign_label_coverage_v0_1.csv` | year-level coverage |
| `outputs/tables/kbo_foreign_label_metric_overview_v0_1.csv` | label QA overview |
| `outputs/tables/kbo_foreign_label_backtest_folds_v0_1.csv` | Dacon-style time folds |
| `outputs/tables/kbo_foreign_label_segment_balance_v0_1.csv` | season x role label balance |
| `outputs/tables/kbo_foreign_label_forbidden_feature_columns_v0_1.csv` | leakage guardrail |

## Label Definitions

### Renewal Proxy

`renewed_next_year = 1` when the same Korean template player name appears in the next season's active foreign-player template.

This is a useful but imperfect proxy:

- It captures club willingness to continue with the player.
- It can miss spelling variants.
- It should not be used as a pre-signing feature.

### Exit Flags

Release-list note text is converted into:

- `in_season_replaced`
- `injury_exit_flag`
- `performance_exit_flag`
- `temporary_foreign_flag`

### Hitter Success

Initial rule:

```text
success =
  renewed_next_year
  OR (PA >= 300 AND (WAR >= 2.0 OR wRC+ >= 115))
```

Strong success:

```text
strong_success =
  (PA >= 450 AND (WAR >= 4.0 OR wRC+ >= 135))
  OR (renewed_next_year AND WAR >= 3.0)
```

Failure:

```text
failure =
  in_season_replaced
  OR (not renewed AND (PA < 250 OR WAR < 0.5 OR wRC+ < 80))
```

### Pitcher Success

Initial rule:

```text
success =
  renewed_next_year
  OR (IP >= 100 AND (WAR >= 2.5 OR ERA <= 4.0))
```

Strong success:

```text
strong_success =
  (IP >= 140 AND (WAR >= 4.0 OR ERA <= 3.3))
  OR (renewed_next_year AND WAR >= 3.5)
```

Failure:

```text
failure =
  in_season_replaced
  OR (not renewed AND (IP < 70 OR WAR < 0.5 OR ERA >= 5.5))
```

## Current Coverage

| period | coverage |
|---|---|
| 2017-2022 | roster, release, renewal-proxy labels only; no local STATIZ outcome attached yet |
| 2023-2025 | roster plus STATIZ outcome coverage |
| 2026 | current-season context only; labels intentionally withheld |

Current QA:

- total rows: 406
- historical label-available rows: 353
- STATIZ outcome rows: 128
- 2026 label rows: 0

## Backtest Folds

| fold | train | valid |
|---|---|---|
| fold A | 2017-2021 | 2022 |
| fold B | 2017-2022 | 2023 |
| fold C | 2017-2023 | 2024 |
| fold D | 2017-2024 | 2025 |

Fold A is weak because 2022 has renewal/release proxy labels only.

Folds B-D are stronger because 2023-2025 have STATIZ outcome coverage.

## Leakage Rule

Forbidden as candidate features:

- `first_kbo_pa`
- `first_kbo_ip`
- `first_kbo_war`
- `first_kbo_wrc_plus`
- `first_kbo_era`
- `first_kbo_k_bb_pct`
- `renewed_next_year`
- `in_season_replaced`
- `injury_exit_flag`
- `performance_exit_flag`
- `temporary_foreign_flag`
- `success`
- `strong_success`
- `failure`

These columns can be used only for historical validation, metric checks, error analysis, and model labels.

## Known Gaps

- 2017-2022 still need full STATIZ/BRef/MyKBO outcome attachment.
- Player identity resolution is currently Korean-name based with a small alias map.
- Renewal is a proxy, not a formal contract database.
- Asian quota 2026 names are mixed into current foreign-player template but should be separated in candidate-market modeling.
- Replacement and temporary foreign-player rules need official KBO source cross-check before final deck.

## Next Step

Build `run_008_metric_reproduction`:

1. encode hard gates as deterministic checks;
2. train trivial baselines on the label table;
3. compare generic stat ranking with SSG-specific fit ranking;
4. start OOF prediction storage for historical validation.
