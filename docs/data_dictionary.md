# Data Dictionary

접근일: 2026-06-11 KST

이 문서는 첫 수집 단계의 최소 스키마를 정의한다. 실제 데이터 수집 후 컬럼 정의, 단위, 결측 처리, 출처별 컬럼 매핑을 계속 갱신한다.

## Naming Rules

- 날짜 컬럼은 `date` 또는 `*_at`를 사용한다.
- 비율 지표는 가능하면 0-100이 아니라 0-1 scale로 저장하고, 표시 단계에서 percent로 변환한다.
- 출처는 모든 테이블에 `source`, `accessed_at`, `raw_file`을 둔다.
- 선수 식별자는 출처별 ID가 다르므로 `player_key`를 내부 surrogate key로 만들고, `source_player_id`를 별도 저장한다.

## Core Tables

### `kbo_team_batting_season`

Grain: one row per `season` x `team`.

Required columns:

| column | type | nullable | description |
|---|---|---:|---|
| season | int | no | KBO season |
| team | string | no | KBO team name |
| games | int | yes | games played |
| pa | int | yes | plate appearances |
| runs | int | yes | runs scored |
| avg | float | yes | batting average |
| obp | float | yes | on-base percentage |
| slg | float | yes | slugging percentage |
| ops | float | yes | OPS |
| iso | float | yes | isolated power |
| wrc_plus | float | yes | park/league adjusted offense if available |
| hr | int | yes | home runs |
| bb_pct | float | yes | walk rate |
| k_pct | float | yes | strikeout rate |
| risp_ops | float | yes | OPS with runners in scoring position |
| vs_lhp_ops | float | yes | OPS vs LHP |
| vs_rhp_ops | float | yes | OPS vs RHP |
| league_rank_runs | int | yes | rank in KBO |
| league_rank_wrc_plus | int | yes | rank in KBO |
| league_rank_iso | int | yes | rank in KBO |
| source | string | no | source id |
| accessed_at | datetime | no | access timestamp |
| raw_file | string | yes | raw file path |

### `kbo_team_pitching_role_season`

Grain: one row per `season` x `team` x `role`, where `role` is `starter` or `bullpen`.

Required columns:

| column | type | nullable | description |
|---|---|---:|---|
| season | int | no | KBO season |
| team | string | no | KBO team name |
| role | string | no | starter/bullpen |
| games | int | yes | games |
| gs | int | yes | games started |
| ip | float | yes | innings pitched |
| era | float | yes | ERA |
| fip | float | yes | FIP if available |
| whip | float | yes | WHIP |
| k_pct | float | yes | strikeout rate |
| bb_pct | float | yes | walk rate |
| k_bb_pct | float | yes | K% minus BB% |
| hr9 | float | yes | home runs per nine |
| qs_pct | float | yes | quality start rate for starters |
| avg_ip_per_start | float | yes | starter workload |
| gmli | float | yes | average leverage at entry |
| pli | float | yes | average leverage |
| wpa | float | yes | win probability added |
| back_to_back_games | int | yes | relief back-to-back appearances |
| league_rank_era | int | yes | rank in KBO |
| league_rank_k_bb_pct | int | yes | rank in KBO |
| source | string | no | source id |
| accessed_at | datetime | no | access timestamp |
| raw_file | string | yes | raw file path |

### `foreign_transfer_history`

Grain: one row per foreign player x KBO arrival season x role group.

Required columns:

| column | type | nullable | description |
|---|---|---:|---|
| player_key | string | no | internal player key |
| player_name | string | no | player name |
| arrival_season | int | no | first KBO season in stint |
| kbo_team | string | no | signing team |
| role_group | string | no | hitter/starter/reliever |
| pre_arrival_primary_league | string | yes | MLB/MiLB/NPB/CPBL/ABL/etc |
| pre_arrival_level | string | yes | MLB/AAA/AA/NPB/Farm/etc |
| age_at_arrival | float | yes | age |
| bats | string | yes | hitter handedness |
| throws | string | yes | throwing hand |
| position_or_role | string | yes | position or pitching role |
| first_kbo_pa | int | yes | target-only for hitters |
| first_kbo_ip | float | yes | target-only for pitchers |
| first_kbo_war | float | yes | target-only |
| first_kbo_wrc_plus | float | yes | target-only for hitters |
| first_kbo_era_plus | float | yes | target-only for pitchers if available |
| first_kbo_k_bb_pct | float | yes | target-only |
| renewed_next_year | int | yes | target-only |
| in_season_replaced | int | yes | target-only |
| injury_exit_flag | int | yes | target-only |
| success | int | yes | label |
| strong_success | int | yes | label |
| failure | int | yes | label |
| source | string | no | source id |
| accessed_at | datetime | no | access timestamp |

Leakage note: columns beginning with `first_kbo_`, `renewed_next_year`, `in_season_replaced`, `injury_exit_flag`, `success`, `strong_success`, and `failure` are labels/outcomes only. They must not be used as candidate ranking features.

### `candidate_hitter_features`

Grain: one row per candidate hitter x evaluation date.

Required columns include:

- identity: `player_key`, `player_name`, `age`, `current_team`, `league`, `level`, `position`, `bats`, `throws`
- basic: `pa`, `avg`, `obp`, `slg`, `ops`, `iso`, `wrc_plus`, `hr`, `bb_pct`, `k_pct`, `bb_k`
- statcast: `avg_ev`, `max_ev`, `ev90`, `hard_hit_pct`, `barrel_pct`, `sweet_spot_pct`, `xwoba`, `xslg`, `xba`
- batted-ball: `gb_pct`, `fb_pct`, `ld_pct`, `pull_pct`, `pull_air_pct`
- discipline: `chase_pct`, `zone_swing_pct`, `zone_contact_pct`, `whiff_pct`, `called_strike_pct`
- SSG/KBO features: `kbo_translation_index`, `ssg_need_fit_score`, `munhak_park_fit_score`, `abs_zone_discipline_score`, `breaking_ball_damage_score`, `offspeed_recognition_score`, `low_velocity_punishment_score`, `acquirable_flaw_score`, `availability_score`, `risk_penalty`

### `candidate_starter_features`

Grain: one row per candidate pitcher x evaluation date.

Required columns include:

- identity: `player_key`, `player_name`, `age`, `current_team`, `league`, `level`, `throws`, `height_cm`, `weight_kg`
- basic: `gs`, `ip`, `era`, `fip`, `xfip`, `whip`, `k_pct`, `bb_pct`, `k_bb_pct`, `hr9`, `gb_pct`, `fb_pct`, `babip`, `lob_pct`
- arsenal: `ff_velo`, `si_velo`, `max_velo`, `spin_rate`, `ivb`, `hb`, `extension`, `release_height`, `release_side`, `pitch_mix_json`
- command/quality: `zone_pct`, `edge_pct`, `chase_pct`, `whiff_pct`, `csw_pct`, `first_pitch_strike_pct`, `full_count_zone_pct`
- SSG/KBO features: `inning_eating_score`, `walk_risk_score`, `abs_edge_command_score`, `summer_durability_score`, `first_inning_stability_score`, `times_through_order_penalty`, `munhak_hr_suppression_score`, `availability_score`, `risk_penalty`

### `candidate_asian_reliever_features`

Grain: one row per Asian quota relief candidate x evaluation date.

Required columns include:

- identity: `player_key`, `player_name`, `age`, `nationality`, `current_team`, `league`, `level`, `throws`
- basic: `appearances`, `ip`, `era`, `fip`, `whip`, `k_pct`, `bb_pct`, `k_bb_pct`, `hr9`, `gb_pct`
- role: `holds`, `saves`, `gmli`, `pli`, `wpa`, `inherited_runner_scored_pct`, `back_to_back_games`
- stuff: `avg_fastball_velo`, `max_velo`, `pitch_mix_json`, `whiff_pct`, `chase_pct`
- SSG/KBO features: `asia_quota_cost_efficiency_score`, `short_burst_stuff_score`, `low_walk_relief_score`, `back_to_back_durability_score`, `high_leverage_translation_score`, `npb_farm_dominance_score`, `kbo_bullpen_role_fit_score`, `availability_score`, `risk_penalty`

