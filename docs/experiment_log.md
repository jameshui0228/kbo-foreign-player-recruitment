# Experiment Log

## 2026-06-11

Stage: project initialization and methodology design.

Actions:

- Created reproducible directory structure for raw/interim/processed data, notebooks, source code, outputs, reports, and docs.
- Defined initial data source audit across KBO, MLB/MiLB, NPB, articles/interviews, weather, and park context.
- Designed minimum SSG team analysis schema.
- Drafted success labels for foreign hitters, foreign starters, and Asian quota relievers.
- Drafted 20 feature hypotheses and selected 10 presentation-strength variables.
- Defined initial ranking methodology, validation strategy, and leakage rules.

Decisions:

- Do not recommend players before SSG need analysis and historical transfer backtest are built.
- Treat KBO post-arrival performance only as target labels.
- Start with interpretable baseline ladder before tree boosting/ensemble models.

Next:

- Audit actual downloadable tables/API access for each source.
- Build first SSG 2023-2026 team diagnosis table.
- Create historical KBO foreign player transfer dataset schema and fill pilot rows.

## 2026-06-11 Data Acquisition

Stage: KBO/Savant data acquisition.

Actions:

- Located prior STATIZ contest project under `/Users/jameshui/스탯티즈/스탯티즈 공모전`.
- Found reusable HMAC-based STATIZ client code, but current shell environment has no `STATIZ_API_KEY` or `STATIZ_API_SECRET` loaded.
- Copied existing local STATIZ API snapshot from `/Users/jameshui/New project/tmp/live_delta_20260611_from_api_v1` into `data/raw/kbo/statiz/live_delta_20260611_from_api_v1`.
- Generated `outputs/tables/statiz_20260611_snapshot_inventory.csv`.
- Added resumable Baseball Savant downloader at `src/data/download_savant_statcast.py`.
- Downloaded MLB Statcast pitch/play-level raw chunks for:
  - 2023 regular season: 720,684 rows
  - 2024 regular season: 710,631 rows
  - 2025 regular season: 711,897 rows
  - 2026 through 2026-06-11: 296,322 rows
- Added `src/data/build_savant_inventory.py`.
- Built yearly parquet files under `data/processed/mlb_milb/savant/`.

Decisions:

- Keep Savant raw as gzip CSV chunks for reproducibility and resume safety.
- Use yearly parquet files for faster feature engineering.
- Treat 2026-06-10 to 2026-06-11 Savant 0-row chunk as source-state limitation at collection time; do not impute.

Next:

- Normalize STATIZ snapshot into SSG team batting/pitching role tables.
- Aggregate Savant raw into hitter and pitcher season-level feature tables.
- Load STATIZ credentials via environment variables if additional API calls are needed.

## 2026-06-11 Strategy Pivot

Stage: role prioritization and project identity.

Actions:

- Read expanded project brief describing SSG replacement foreign player context, public-data approach, Dacon-style experiment discipline, and desire for non-obvious feature engineering.
- Updated README and methodology to set the first-priority analysis target as replacement foreign outfielder.
- Added `docs/strategy_replacement_outfielder.md`.

Decisions:

- First priority is replacement foreign player, not Asian quota.
- First role priority is foreign hitter/outfielder.
- Final deliverable can still include foreign starter and Asian quota reliever, but the first analytical edge should come from SSG-specific outfielder selection.
- Avoid obvious OPS/home-run ranking. The project identity is to find a player with an acquirable flaw whose strengths are amplified by SSG context.
- Weight `Hidden SSG Edge` and `Acquirable Flaw` heavily for hitter ranking.

Next:

- Build SSG outfield/lineup/power gap diagnostic from STATIZ.
- Build SSG article/interview need tags from Naver Search API and official sources.
- Aggregate Savant hitter features for OF candidates, especially pull-air power, low-velocity damage, breaking-ball survivability, ABS zone discipline, and recent skill trend.

## 2026-06-11 First SSG Outfield Diagnostic

Stage: first priority role diagnosis.

Actions:

- Added `src/features/build_ssg_outfield_diagnostic.py`.
- Built team batting rank table: `outputs/tables/kbo_team_batting_rank_2023_2026.csv`.
- Built team outfield batting table: `outputs/tables/kbo_team_outfield_batting_2023_2026.csv`.
- Built SSG outfield gap summary: `outputs/tables/ssg_outfield_gap_summary.csv`.

Findings:

- 2023-2025 SSG outfield HR rank: 3rd, 1st, 1st.
- 2023-2025 SSG outfield ISO rank: 3rd, 1st, 3rd.
- 2023-2025 SSG outfield OPS rank: 5th each year.
- 2023-2025 SSG outfield PA-weighted wRC+ rank: 5th, 8th, 7th.
- Early read: SSG outfield problem may not be pure power shortage. The more interesting gap is that power indicators are not translating into consistently elite run creation.

Next:

- Split SSG outfield production by handedness, lineup slot, and player to find the translation bottleneck.
- Compare article/interview needs against this first quantitative finding.

## 2026-06-11 Message Discovery And Literature

Stage: text/literature evidence layer.

Actions:

- Updated replacement outfielder strategy so the project does not pre-select a presentation message.
- Added `docs/message_discovery_protocol.md`.
- Added `src/data/collect_naver_news.py` for Naver Search News metadata collection.
- Added `src/features/build_text_need_signals.py` for relevance labeling and keyword/tag signal extraction.
- Collected broad SSG-related news/article metadata across 30 queries, not limited to interviews.
- Added `docs/literature_log.md` with initial academic support for foreign-player market constraints, replacement context, park effects, run creation, and plate discipline.

Data:

- Broad recall news set: 7,884 records.
- Strict SSG/랜더스 snippet set: 7,630 records.
- High-value SSG + foreign/hitter/outfield/lineup context set: 5,378 records.

First text signals:

- `power`: 2,358 strict records.
- `injury_depth`: 1,692 strict records.
- `run_creation`: 1,611 strict records.
- `onbase_discipline`: 1,192 strict records.
- `foreign_hitter`: 1,155 strict records.
- `outfield`: 988 strict records.

Decisions:

- Treat text signals as hypotheses only.
- A message becomes presentation-ready only after it is supported by STATIZ team diagnostics and Savant candidate features.
- No Korea University library login is needed yet; request it only if a paywalled full text becomes essential.

Next:

- Build SSG player-level and lineup-slot batting bottleneck tables.
- Cross-check whether text signals about power/run creation/outfield match STATIZ splits.
- Use literature log to map each final feature to at least one empirical or methodological rationale.

## 2026-06-11 Text x STATIZ x Savant Cross-Check

Stage: first message discovery pass.

Actions:

- Added `src/features/build_ssg_bottleneck_tables.py`.
- Built STATIZ daily batting split table: `outputs/tables/kbo_team_batting_splits_from_day.csv`.
- Built SSG split bottleneck table: `outputs/tables/ssg_batting_bottleneck_by_split.csv`.
- Built SSG OF player contribution table: `outputs/tables/ssg_of_player_contributions.csv`.
- Built text x quantitative crosswalk: `outputs/tables/ssg_text_quant_signal_crosswalk.csv`.
- Added `src/features/build_savant_hitter_features.py`.
- Built Savant hitter feature summary: `outputs/tables/savant_hitter_feature_summary_2023_2026.csv`.
- Built Savant message screen: `outputs/tables/savant_hitter_message_screen_top.csv`.
- Built flawed-profile screen: `outputs/tables/savant_hitter_flawed_profile_screen.csv`.
- Added `docs/message_discovery_findings.md`.

Findings:

- Text says power is a major SSG topic, but STATIZ does not support a simple "SSG lacks OF power" message.
- 2023-2025 SSG OF HR ranks: 3rd, 1st, 1st.
- 2023-2025 SSG OF BB% ranks: 9th, 10th, 9th.
- 2023-2025 SSG OF OPS ranks: 4th, 5th, 5th.
- Stronger current message candidate: SSG OF has power, but power is not translating into elite OBP/run creation.
- Savant confirms that power + patience + flaw profiles exist, but the current screen is not yet an acquisition shortlist because it lacks OF eligibility, 40-man/contract/availability filters.

Next:

- Add position/roster/40-man status to Savant hitter screen.
- Filter to realistic OF/DH replacement candidates.
- Backtest whether "disciplined power with an acquirable flaw" maps to prior KBO foreign hitter success.

## 2026-06-11 Current-Season Correction

Stage: 2026 current-season correction.

Actions:

- Found that the prior STATIZ split script joined `players_day_batting` to `games_boxscore_gameinfo`, which excluded most 2026 regular-season rows.
- Switched the join source to `games_schedule`, which contains 2026 regular-season games through 2026-06-11 schedule and completed games through 2026-06-10.
- Regenerated SSG batting bottleneck tables with 2026 included.
- Added `docs/ssg_2026_current_findings.md`.
- Updated `docs/message_discovery_findings.md` to mark the first pass as too broad and less current.

Findings:

- 2026 SSG OF: ISO rank 1st, OPS rank 5th, OBP rank 7th.
- 2026 SSG IF/C: OPS rank 1st and SLG rank 1st, suggesting the offense is being carried outside the OF/DH problem area.
- 2026 SSG DH: OPS rank 10th, SLG rank 10th, K% rank 10th.
- 2026 SSG OF 3-5 lineup role: BB% rank 2nd, but OPS rank 9th and SLG rank 9th.
- Better current message candidate: the issue is not a generic OF power shortage, but a DH and OF middle-order role problem.

Next:

- Treat replacement foreign hitter target as `OF/DH flexible 3-5 lineup bat`, not just "outfielder with power."
- Analyze 2026 May slump vs June rebound before deciding whether the OF issue is persistent.

## 2026-06-11 STATIZ Player-Day Refetch And Hidden Context Pass

Stage: current-season data quality fix and deeper context analysis.

Actions:

- Found that the copied live-delta `players_day_batting.csv` covered only 30 SSG batting games in 2026, while the schedule had 61 completed SSG games through 2026-06-10.
- Added `src/data/collect_statiz_2026_player_day.py`.
- Refetched 2026 `playerDay` rows from the STATIZ API for 514 roster/lineup players.
- Wrote `data/raw/kbo/statiz/live_delta_20260611_from_api_v1/organized/players/players_day_batting_2026_refetched.csv`.
- Updated `src/features/build_ssg_bottleneck_tables.py` and `src/features/build_ssg_context_signals.py` to use the refetched 2026 batting file.
- Added `src/features/build_ssg_advanced_context_tables.py`.
- Added `docs/ssg_2026_hidden_context_findings.md`.

Findings:

- Refetched 2026 batting file has 7,786 rows across 10 teams and 310 games.
- Completed-game context analysis filters through 2026-06-10.
- 2026 SSG OF overall: HR rank 3rd and ISO rank 4th, but OBP rank 9th and OPS rank 8th.
- 2026 SSG OF 1-2 lineup role: .243 OBP, .606 OPS, 1.9% BB%; OBP, OPS, and BB% rank 10th.
- 2026 SSG OF 3-5 lineup role: .693 OPS, .359 SLG, .118 ISO; OPS and SLG rank 10th.
- 2026 SSG OF 6-9 lineup role: .751 OPS and 12 HR; PA, HR, R, and RBI rank 1st.
- Against right-handed starters, SSG OF 3-5 has .595 OPS, .301 SLG, and .084 ISO, all rank 10th.
- SSG OF humid-game split: .530 OPS and .254 OBP, both bottom-tier.

Decision:

- Replace the earlier broad message with a narrower one: SSG needs a high-leverage OF/DH bat whose RHP production, OBP, and damage hold in top/middle lineup roles and tougher context splits.

## 2026-06-11 STATIZ Situation-Level Context Refresh

Stage: hidden signal search beyond offense/defense totals.

Actions:

- Added `src/data/collect_statiz_2026_ssg_player_situation.py`.
- Refetched current 2026 STATIZ `playerSituation` for 21 SSG batters with at least 10 PA.
- Wrote `data/raw/kbo/statiz/live_delta_20260611_from_api_v1/organized/player_situations/ssg_player_situation_batting_2026_refetched.csv`.
- Added `src/data/collect_statiz_2026_team_situation.py`.
- Refetched current 2026 STATIZ `teamRecord` batting splits for 27 situation contexts.
- Wrote `outputs/tables/kbo_2026_team_situation_ranks.csv`.
- Added `src/features/build_ssg_situation_context_tables.py`.
- Built:
  - `outputs/tables/ssg_2026_player_role_context.csv`
  - `outputs/tables/ssg_2026_situation_role_splits.csv`
  - `outputs/tables/ssg_2026_situation_count_class_splits.csv`
  - `outputs/tables/ssg_2026_replacement_context_flags.csv`
  - `outputs/tables/ssg_2026_player_situation_focus.csv`
- Updated `docs/ssg_2026_hidden_context_findings.md`.

Findings:

- SSG team RISP is not the problem: .831 OPS, OPS rank 1st, OBP rank 1st, BB% rank 1st.
- The hidden issue is distribution: IF/C core RISP OPS is .905, while lower/mixed OF usage RISP OPS is .675.
- Close-game context is sharper than generic RISP:
  - Tied game IF/C core OPS .864.
  - Tied game high-leverage OF usage OPS .575.
  - Tied game DH bridge OPS .420.
- Team two-strike ranks look fine overall, but replacement-relevant role segments thin out:
  - IF/C core two-strike OPS .632.
  - High-leverage OF usage two-strike OPS .466.
  - Lower/mixed OF usage two-strike OPS .573.
  - DH bridge two-strike OPS .459.
- SSG team vs RHP is mid-pack, but the role split is the problem:
  - IF/C core vs RHP OPS .833.
  - High-leverage OF usage vs RHP OPS .688.
  - Lower/mixed OF usage vs RHP OPS .653.
  - DH bridge vs RHP OPS .630.

Decision:

- New working message: SSG already owns team-level RISP strength, but it is concentrated in IF/C and one high-leverage OF bat. A replacement foreign OF/DH should broaden that run-conversion base with RHP production, close-game plate quality, and two-strike survival.

## 2026-06-12 SSG-Specific Message Development

Stage: move from broad hidden signals to a distinctive recruitment thesis.

Actions:

- Added `src/features/build_ssg_message_development_tables.py`.
- Built `outputs/tables/ssg_2026_runway_gap_by_team.csv`.
- Built `outputs/tables/ssg_2026_role_runway_context.csv`.
- Added `docs/ssg_hidden_message_development.md`.
- Updated `docs/ssg_2026_hidden_context_findings.md`.

Findings:

- SSG has the league's biggest gap between RISP performance and runner-on-first performance.
- SSG RISP: .831 OPS, .392 OBP, OPS rank 1st, OBP rank 1st.
- SSG runner on first: .649 OPS, .304 OBP, OPS rank 10th, OBP rank 10th.
- The +.182 OPS gap between RISP and runner-on-first is the largest in KBO 2026.
- Internally, the runner-on-first bottleneck is visible in OF/DH:
  - High-leverage OF usage, runner on first: .383 OPS, 52 PA, 0 RBI.
  - Lower/mixed OF usage, runner on first: .637 OPS.
  - DH bridge, runner on first: .463 OPS.
  - IF/C core, runner on first: .757 OPS.
- Less than two outs with runner on first, high-leverage OF usage has .384 OPS and 6 GDP in 58 PA.

Decision:

- Refine the project message again: SSG does not need a generic clutch hitter because the team is already elite in RISP. The foreign replacement should be framed as a "first-base traffic converter" who turns runner-on-first states into scoring-position pressure through RHP contact quality, low-GDP batted-ball shape, and two-strike survival.

## 2026-06-12 Integrated Hitter/Pitcher Message Revision

Stage: respond to the need for a broader, more practical hidden message that includes foreign pitchers.

Actions:

- Added `src/data/collect_statiz_2026_ssg_player_day_pitching.py`.
- Refetched 2026 SSG `playerDay` pitching rows from the STATIZ API.
- Added `src/data/collect_statiz_2026_team_pitching_situation.py`.
- Refetched 2026 KBO pitching `teamRecord` situation contexts.
- Added `src/features/build_ssg_pitching_context_tables.py`.
- Built:
  - `outputs/tables/kbo_2026_pitching_with_context.csv`
  - `outputs/tables/kbo_2026_team_pitching_role_ranks.csv`
  - `outputs/tables/ssg_2026_team_pitching_role_ranks.csv`
  - `outputs/tables/ssg_2026_game_pitching_workload.csv`
  - `outputs/tables/ssg_2026_pitcher_summary.csv`
  - `outputs/tables/ssg_2026_import_slot_pitching_impact.csv`
- Recollected Naver Search News metadata with pitcher-focused SSG queries.
- Added `src/features/build_pitching_news_signals.py`.
- Built:
  - `outputs/tables/ssg_pitching_news_relevance_labeled.csv`
  - `outputs/tables/ssg_pitching_news_tag_summary.csv`
  - `outputs/tables/ssg_pitching_news_name_summary.csv`
  - `outputs/tables/ssg_pitching_news_query_summary.csv`
- Added `src/features/build_savant_pitcher_features.py`.
- Built:
  - `outputs/tables/savant_pitcher_feature_summary_2023_2026.csv`
  - `outputs/tables/savant_pitcher_stabilizer_screen_top.csv`
- Added `docs/ssg_integrated_hidden_message_v2.md`.

Findings:

- SSG starters rank 10th in ERA, WHIP, OPS allowed, IP/G, and outs/start.
- SSG bullpen has the league's heaviest workload at 4.25 IP/G, but ranks 3rd in WHIP and 2nd in OPS allowed.
- Short starts under 5 IP occurred in 26 of 61 games; SSG win rate in those games was .308.
- Non-short-start games had a .514 win rate.
- Disaster starts occurred in 20 of 61 games; quality starts occurred in only 7 of 61.
- Import-slot starters were worse than domestic starters: 6.17 ERA, 1.73 WHIP, .821 OPS allowed versus domestic starter 5.06 ERA, 1.44 WHIP, .731 OPS allowed.
- Situation splits point to early innings and traffic states:
  - early 1-3 ERA 5.81, WHIP 1.64, OPS allowed .790, all rank 10th.
  - RISP ERA 15.13, WHIP 1.78, OPS allowed .847, all rank 10th.
- Naver pitcher-focused article metadata produced 3,822 rows and 3,724 strategy-relevant signals. The largest tags were starter/rotation, run prevention, replacement decision, injury/depth, foreign pitcher, and bullpen load.
- Savant profile learning shows that top starter-stabilizer seasons separate most clearly through workload, BB+HBP suppression, HR suppression, early-inning wOBA allowed, RISP wOBA allowed, and barrel/hard-hit suppression.

Decision:

- Promote replacement foreign starter to the primary project priority unless the roster/slot constraint makes a hitter the only actionable move.
- Keep the hitter thesis as a secondary path: if replacing a hitter, target a first-base traffic converter rather than a generic slugger.

## 2026-06-12 External Evidence Message Discovery

Stage: search for a more distinctive message using non-STATIZ sources.

Actions:

- Searched current articles, KBO rule coverage, Baseball Savant, and academic papers.
- Downloaded public result CSVs from the KBO ABS paper GitHub repository into `data/external/kbo_abs_paper/result`.
- Added `src/features/build_external_message_tables.py`.
- Built:
  - `outputs/tables/external_abs_zone_shift_summary.csv`
  - `outputs/tables/external_hatch_savant_context.csv`
  - `outputs/tables/external_message_candidates_v1.csv`
- Added `docs/external_message_discovery_v1.md`.

Findings:

- The strongest external message is an ABS-native foreign pitcher screen.
- Scientific Reports' KBO ABS paper and public result files show the 2024 KBO zone became much stricter and more rectangular:
  - `beta` rose from 12.58 in 2023 to 34.78 in 2024.
  - `r` rose from 3.30 in 2023 to 24.44 in 2024.
- This changes the meaning of "command" in KBO scouting. The project can argue that command must be validated by rule-book-zone strike creation, not reputation or catcher framing.
- Using MLB Savant, Thomas Hatch's 2025 MLB profile does not automatically support a "strike-throwing stabilizer" label:
  - Hatch 2025 MLB zone rate: 43.7%.
  - Eligible 2025-2026 starter median: 49.6%.
  - Top 100 stabilizer median: 50.5%.
  - Hatch 2025 MLB BB+HBP%: 11.2% versus top 100 stabilizer median 7.4%.
- This does not prove Hatch will fail, but it proves the project needs an ABS-native command audit.
- The second message is that SSG should treat the Asian quota as option/depth value, not as a rotation-pillar substitute.
- The third message is that the KBO temporary replacement rule creates an audition market. A strong club should maintain a pre-cleared replacement pool rather than react after injury.

Decision:

- Move the next research track to "ABS-native, workload-bearing foreign starter screen."
- Separate three acquisition markets in all future candidate work: regular foreign starter, Asian quota option, and six-week injury replacement audition.

## 2026-06-12 Three Slot Message Framework

Stage: separate the project thesis by required acquisition slot.

Actions:

- Added `docs/three_slot_core_messages_v1.md`.
- Added `src/features/build_three_slot_message_framework.py`.
- Built `outputs/tables/three_slot_message_framework_v1.csv`.

Findings:

- The three slots should not be treated as three generic "good player" searches.
- Foreign hitter message: The Runway Converter.
  - Tagline: 득점권 해결사가 아니라, 득점권을 만들어주는 타자.
  - Solves the runner-on-first transition bottleneck.
- Foreign pitcher message: The ABS-Native Load-Bearing Starter.
  - Tagline: 강한 공보다, ABS가 스트라이크로 인정하는 공을 6이닝 반복하는 투수.
  - Solves short-start compression and ABS-era command risk.
- Asian quota message: The Option Layer.
  - Tagline: 아쿼는 1선발 복권이 아니라, 시즌 중 붕괴를 막는 옵션 보험.
  - Solves roster shock absorption and prevents overloading a low-cost quota slot.

Decision:

- Use the three-slot framework as the candidate-screening spine:
  - foreign hitter = offensive transition,
  - foreign pitcher = weekly stability,
  - Asian quota = optionality and shock absorption.

## 2026-06-12 Field-Style And Contract Gate Framework

Stage: convert the user's preferred mining tracks into a realistic pro-scout/front-office workflow.

Actions:

- Added `docs/field_scouting_mining_framework.md`.
- Added `docs/contract_rule_constraints_v1.md`.
- Added `outputs/tables/field_scouting_source_map_v1.csv`.
- Added `outputs/tables/kbo_contract_constraints_v1.csv`.
- Expanded `feature_ideas.csv` with tool-grade, pitch-process, adaptation-risk, contract-gate, Asian-quota surplus, and replacement-readiness features.
- Logged `run_002` in `experiments.csv`.

Findings:

- The selected mining tracks should be treated as one acquisition funnel:
  - SSG-specific need mining.
  - market inefficiency mining.
  - KBO translation mining.
  - failure pattern mining.
  - availability and contract-rule mining.
- Money and rules should be hard gates before baseball scoring.
- 2026 Asian quota rules create a distinct low-cost market: eligibility and 200k USD cost ceiling define the search before performance metrics.
- Injury replacement foreign players require a separate six-week/short-window market model with a 100k USD monthly cost ceiling.
- SSG's confirmed 2026 regular foreign-player contract baseline is already substantial, so any regular foreign replacement must model sunk cost, remaining cap room, medical risk, and acquisition timing.

Decision:

- Do not name final candidates until a candidate-scoring schema exists.
- Build final candidate cards in a field-style format: 20-80 proxy grades, SSG fit, KBO translation, failure risks, medical/availability, and contract feasibility.

## 2026-06-12 Source Coverage Audit And Candidate Schema

Stage: verify whether enough data/literature exists to proceed into full mining.

Actions:

- Downloaded open/full-text PDFs for core references where available:
  - KBO foreign-player labor-market inefficiency.
  - KBO foreign-pitcher renewal ML model.
  - KBO foreign-player adaptation thesis.
  - KBO ABS arXiv preprint.
  - KBO ABS Scientific Reports article.
- Added `src/data/build_project_source_audit.py`.
- Built `outputs/tables/project_data_coverage_audit_v1.csv`.
- Added `outputs/tables/literature_source_inventory_v1.csv`.
- Added `data/schemas/candidate_scoring_schema_v1.csv`.
- Added `docs/source_coverage_audit_v1.md`.
- Logged `run_003` in `experiments.csv`.

Findings:

- The quantitative core is adequate for message mining:
  - STATIZ/KBO context data.
  - MLB Savant pitch/play data.
  - Naver article metadata.
  - KBO ABS result data.
  - rule/contract constraints.
- The candidate-finalization layer is not complete:
  - MLB/MiLB roster and contract availability are missing.
  - NPB/CPBL/ABL Asian quota market data is missing.
  - historical KBO foreign-player success/failure labels still need to be built.
  - article full-text extraction is still needed for quote-level evidence.

Decision:

- Proceed with full pipeline setup.
- Do not present final candidates until market availability and historical outcome labels are added.

## 2026-06-12 MLB Roster Status Collection

Stage: begin candidate-market availability data collection.

Actions:

- Added `src/data/collect_mlb_roster_status.py`.
- Collected MLB official roster status from MLB Stats API.
- Built:
  - `outputs/tables/mlb_roster_status_20260612.csv`
  - `outputs/tables/mlb_roster_status_latest.csv`
  - `data/raw/mlb/roster_status/mlb_roster_status_raw_20260612.json`
- Added `outputs/tables/candidate_market_collection_plan_v1.csv`.
- Logged `run_004` in `experiments.csv`.

Findings:

- 8,181 organization roster rows collected.
- 1,345 rows have a 40-man flag.
- 777 rows have an active-roster flag.
- 4,278 pitchers are in MLB organizations but not active at the MLB level.

Decision:

- Use roster status as the first "too good / blocked / available enough" gate.
- Next step is joining MLB roster status to Savant pitcher/hitter feature summaries.

## 2026-06-12 Availability-Aware Candidate Pool V1

Stage: connect performance mining to realistic acquisition filtering.

Actions:

- Added `src/features/build_candidate_pool_v1.py`.
- Joined 2025-2026 Savant pitcher/hitter feature summaries to MLB official roster status.
- Built:
  - `outputs/tables/mlb_pitcher_availability_candidate_pool_v1.csv`
  - `outputs/tables/mlb_outfielder_availability_candidate_pool_v1.csv`
  - `outputs/tables/candidate_pool_summary_v1.csv`
- Logged `run_005` in `experiments.csv`.

Findings:

- Pitcher pool: 1,009 recent MLB Statcast pitchers, 4 passed the conservative first-pass gate.
- Outfield-priority hitter pool: 736 recent MLB Statcast hitters, 6 passed the conservative first-pass gate.
- The gate now rejects current MLB active players, 40-man low-access cases, medical red flags, unknown current-organization cases, wrong-role cases, and age-outlier cases before final ranking.

Decision:

- Treat the gate-pass names as research leads, not recommendations.
- Next step is manual availability verification: transactions, DFA/release/minor-league contract status, salary/option constraints, recent health, and Korea willingness signals.

## 2026-06-12 Dacon-Style Modeling Blueprint

Stage: make the data-mining model defensible for a computer-science professor audience.

Actions:

- Added `docs/modeling_strategy_dacon_style_v1.md`.
- Added `outputs/tables/modeling_blueprint_registry_v1.csv`.
- Updated `validation_plan.md` with:
  - historical backtest folds;
  - CV/Public LB/Private LB analogue;
  - 2026 current-season sensitivity rule;
  - candidate-ranking robustness checks.
- Logged `run_006` in `experiments.csv`.

Findings:

- The project should not use a single candidate score as the main model.
- The defensible model stack is:
  - SSG-only hidden-need mining;
  - KBO translation modeling;
  - failure-risk modeling;
  - market/contract availability gating;
  - slot-specific final ranking ensemble.
- 2026 data should be emphasized, but every claim must be compared against 2023-2025 stability to avoid partial-season overfitting.

Decision:

- Promote this blueprint as the modeling contract.
- Next modeling work should build the historical KBO foreign-player label table and metric checker before training strong ML models.

## 2026-06-12 Historical KBO Foreign-Player Label Table

Stage: create the first supervised validation target for KBO translation modeling.

Actions:

- Added `src/data/build_kbo_foreign_player_labels.py`.
- Scraped and cached Korean Wikipedia yearly KBO foreign-player templates for 2017-2026.
- Parsed active foreign-player rows, released-player rows, release reasons, and next-year renewal proxy.
- Attached local STATIZ season outcomes for 2023-2025 where available.
- Added `src/modeling/check_kbo_foreign_label_metrics.py`.
- Built:
  - `data/processed/kbo/kbo_foreign_player_season_labels_v0_1.csv`
  - `outputs/tables/kbo_foreign_player_season_labels_v0_1.csv`
  - `outputs/tables/kbo_foreign_label_coverage_v0_1.csv`
  - `outputs/tables/kbo_foreign_label_metric_overview_v0_1.csv`
  - `outputs/tables/kbo_foreign_label_backtest_folds_v0_1.csv`
  - `outputs/tables/kbo_foreign_label_segment_balance_v0_1.csv`
  - `outputs/tables/kbo_foreign_label_forbidden_feature_columns_v0_1.csv`
- Added `docs/foreign_player_labeling_methodology_v0_1.md`.
- Logged `run_007` in `experiments.csv`.

Findings:

- Total foreign-player season rows: 406.
- Historical label-available rows: 353.
- STATIZ outcome-attached rows: 128.
- 2026 labels are intentionally withheld because the season is current.
- 2023-2025 outcome coverage is nearly complete: 128 of 129 rows matched to STATIZ. The only unmatched row is 2023 SSG pitcher Enny Romero, who was released for injury before recording a local STATIZ outcome.
- Backtest folds are now usable:
  - Fold A: train 2017-2021, validate 2022.
  - Fold B: train 2017-2022, validate 2023.
  - Fold C: train 2017-2023, validate 2024.
  - Fold D: train 2017-2024, validate 2025.

Decision:

- Promote the label table as v0.1 validation infrastructure, not as a final truth table.
- Treat 2017-2022 rows as lower-confidence renewal/release proxy labels until full outcome attachment is added.
- Do not use post-KBO outcome fields as candidate features. They are target-only fields for historical validation and error analysis.
- Next run should implement trivial baselines, hard-gate reproduction, and out-of-fold prediction storage before strong ML models.

## 2026-06-12 Run 008 Metric Reproduction And Mining

Stage: move from message drafting to data-mined message priority and baseline validation.

Actions:

- Added `src/modeling/mine_ssg_hidden_state_needs.py`.
- Added `src/modeling/mine_kbo_foreign_archetypes.py`.
- Added `src/modeling/run_kbo_foreign_baselines.py`.
- Built:
  - `outputs/tables/ssg_hidden_state_mining_v0_1.csv`
  - `outputs/tables/ssg_hidden_state_message_candidates_v0_1.csv`
  - `outputs/tables/ssg_hidden_state_feature_contract_v0_1.csv`
  - `outputs/tables/kbo_foreign_archetype_assignments_v0_1.csv`
  - `outputs/tables/kbo_foreign_archetype_summary_v0_1.csv`
  - `outputs/tables/kbo_foreign_failure_patterns_v0_1.csv`
  - `outputs/tables/kbo_foreign_baseline_scores_v0_1.csv`
  - `outputs/tables/kbo_foreign_oof_predictions_v0_1.csv`
  - `outputs/tables/kbo_foreign_model_family_comparison_v0_1.csv`
- Added `docs/run_008_metric_reproduction_results.md`.
- Logged `run_008` in `experiments.csv`.

Findings:

- The strongest SSG hidden-state messages are pitcher-led:
  - `run_prevention_stabilizer`: message priority score 58.49.
  - `traffic_command_starter`: message priority score 51.72.
  - `abs_native_load_bearing_starter`: message priority score 26.08.
- Hitter still has a real mined message, but it is secondary:
  - `first_base_traffic_converter`: message priority score 25.75.
- Asian quota remains under-mined:
  - `option_layer_shock_absorber`: message priority score 3.17, based only on bullpen workload stress.
- Historical KBO pitcher archetypes support the pitcher message:
  - successful load-bearing starter clusters: 154.7-161.8 median IP, 3.96-4.43 median WAR, 3.28-3.41 median ERA.
  - failure/replacement starter patterns: 47.0-66.0 median IP, 0.76-1.15 median WAR, 4.29-4.76 median ERA.
- Historical KBO hitter archetypes show that successful foreign hitters are everyday-volume run creators:
  - successful hitter cluster: 512.5 median PA, 3.50 median WAR, 132.4 median wRC+.
  - failure hitter cluster: 236.5 median PA, 0.03 median WAR, 98.1 median wRC+.
- Baseline board is now available:
  - success `role_prior`: mean Brier 0.236, top-25% precision 0.523.
  - success `team_role_prior`: top-25% precision 0.591.
  - failure `recent_role_prior`: mean AUC 0.632, mean Brier 0.239, top-25% precision 0.545.

Decision:

- Promote the primary project message to a pitcher-first frame:
  - SSG should prioritize a traffic-command, load-bearing foreign starter who prevents innings from exploding after traffic and turns short-start games into 5-6 inning games.
- Keep the hitter message as a secondary path:
  - If adding/replacing a hitter, target a first-base traffic converter rather than a generic slugger.
- Hold the Asian quota message as provisional until Asian-market candidate data is collected.
- Next run should score actual MLB candidate pools against the promoted message themes and historical archetype distances.

## 2026-06-12 Run 009 Pitcher Message Validation And Candidate Fit

Stage: validate the pitcher-first message and connect it to realistic candidate leads.

Actions:

- Added `src/modeling/validate_ssg_pitching_message_v0_2.py`.
- Added `src/modeling/score_mlb_pitcher_fit_v0_1.py`.
- Built:
  - `outputs/tables/ssg_pitching_message_v0_2_monthly_role_ranks.csv`
  - `outputs/tables/ssg_pitching_message_v0_2_monthly_summary.csv`
  - `outputs/tables/ssg_pitching_message_v0_2_game_impact.csv`
  - `outputs/tables/ssg_pitching_message_v0_2_context_validation.csv`
  - `outputs/tables/ssg_pitching_message_v0_2_decision_table.csv`
  - `outputs/tables/mlb_pitcher_ssg_fit_scores_v0_1.csv`
  - `outputs/tables/mlb_pitcher_ssg_fit_top_research_leads_v0_1.csv`
  - `outputs/tables/mlb_pitcher_ssg_fit_unavailable_benchmark_v0_1.csv`
  - `outputs/tables/mlb_pitcher_ssg_fit_summary_v0_1.csv`
- Added `docs/run_009_pitcher_message_validation_and_candidate_fit.md`.
- Logged `run_009` in `experiments.csv`.

Findings:

- The pitcher-first message passed all v0.2 promotion criteria.
- SSG starters showed bottom-three core monthly signals in 3 of 4 observed months.
- SSG starter summary:
  - mean ERA rank: 8.75.
  - mean WHIP rank: 8.75.
  - mean outs/start rank: 8.5.
  - median outs/start: 13.67, or about 4.56 IP.
- Game impact:
  - short starts under 5 IP: 26 games, .308 win rate versus .514 otherwise, -20.7 percentage points.
  - disaster starts: 20 games, .250 win rate versus .512 otherwise, -26.2 percentage points.
  - 5+ IP starts: .514 win rate versus .308 otherwise, +20.7 percentage points.
  - quality starts: .714 win rate versus .389 otherwise, +32.5 percentage points.
- Severe context concentration:
  - vs right orthodox, early 1-3, RISP, away games, runner on base, 0 out, and 2 out contexts all show severe rank problems.
- Candidate fit scoring produced 1,009 scored MLB pitcher rows.
- First realistic research leads:
  - A: Dietrich Enns, fit score 62.74.
  - B: Bailey Falter, fit score 60.56.
  - B: Austin Gomber, fit score 57.18.
  - B: Bryse Wilson, fit score 51.35.
- Gate-review watchlist:
  - Tobias Myers, Carlos Carrasco, Jacob Lopez, Brayan Bello, Kyle Hart.

Decision:

- Promote the pitcher message to v0.2 and use it as the primary candidate-ranking spine.
- Do not treat any candidate as final until current transaction, 40-man/option, salary, medical, and Korea-willingness checks are performed.
- Next step should manually verify the A/B leads and then add the secondary hitter model.

Correction:

- Candidate names from run_009 are sandbox research leads, not shortlist candidates.
- Added `docs/candidate_release_gates_v1.md`.
- Freeze final player selection until SSG hidden-need mining, KBO success/failure archetype mining, candidate market construction, KBO translation modeling, and failure-risk modeling are all built and checked.

## 2026-06-12 Run 010 Recruitment Model Mart And Gate Audit

Stage: build the modeling gates that must pass before candidate names are reopened.

Actions:

- Added `src/modeling/build_recruitment_model_marts_v1.py`.
- Built:
  - `outputs/tables/historical_kbo_savant_name_match_audit_v0_1.csv`
  - `outputs/tables/kbo_translation_feature_mart_v0_1.csv`
  - `outputs/tables/failure_risk_feature_mart_v0_1.csv`
  - `outputs/tables/kbo_translation_readiness_v0_1.csv`
  - `outputs/tables/candidate_market_coverage_v0_2.csv`
  - `outputs/tables/recruitment_gate_status_v1.csv`
- Added `docs/recruitment_model_build_status_v1.md`.
- Updated `docs/candidate_release_gates_v1.md`.
- Logged `run_010` in `experiments.csv`.

Findings:

- Historical supervised rows eligible for pre-KBO Savant joining: 87.
- Rows with pre-KBO Savant features: 27, or 31.0%.
- Hitter readiness:
  - 29 eligible rows.
  - 7 pre-KBO Savant rows.
  - 2 success rows and 5 failure rows.
  - training-ready: no.
- Pitcher readiness:
  - 58 eligible rows.
  - 20 pre-KBO Savant rows.
  - 11 success rows and 7 failure rows.
  - training-ready: no.
- Candidate market coverage:
  - regular foreign pitcher MLB current-org pool: 1,009 rows, 4 first-pass gate-pass rows.
  - outfielder-priority hitter MLB current-org pool: 736 rows, 6 first-pass gate-pass rows.
  - injury replacement, Asian quota, article full text, and weather/park context layers are not started.

Gate decision:

- G1 SSG hidden-need mining: pass.
- G2 KBO archetype mining: partial pass.
- G3 candidate market: partial.
- G4 KBO translation: blocked by sample.
- G5 failure risk: blocked by sample and context.
- G6 final shortlist: locked.

Decision:

- Promote the gate mart as the current control board.
- Do not train final KBO translation or failure-risk models yet.
- Do not present any player as a shortlist candidate or recommendation.
- Next run should expand historical pre-arrival player features using MLB/MiLB/NPB/CPBL sources and a stronger ID crosswalk.

## 2026-06-12 Run 011 Historical Feature Expansion And Pilot Modeling

Stage: expand pre-KBO feature coverage and train role-specific pilot models without releasing candidate names.

Actions:

- Downloaded and repaired 2022 MLB Savant coverage.
- Added `src/data/combine_savant_statcast_year.py` after finding that the generic downloader's combine step can mix multiple seasons in a shared raw folder.
- Rebuilt:
  - `outputs/tables/savant_pitcher_feature_summary_2022_2026.csv`
  - `outputs/tables/savant_hitter_feature_summary_2022_2026.csv`
  - `outputs/tables/kbo_translation_feature_mart_v0_1.csv`
  - `outputs/tables/failure_risk_feature_mart_v0_1.csv`
  - `outputs/tables/kbo_translation_readiness_v0_1.csv`
- Added `src/modeling/train_kbo_translation_failure_models_v0_1.py`.
- Built:
  - `outputs/tables/kbo_translation_failure_model_comparison_v0_1.csv`
  - `outputs/tables/kbo_translation_failure_repeated_cv_comparison_v0_1.csv`
  - `outputs/tables/kbo_translation_failure_feature_signals_v0_1.csv`
  - `outputs/tables/kbo_translation_failure_oof_predictions_v0_1.csv`
- Added `docs/run_011_historical_feature_expansion_and_modeling.md`.
- Updated `docs/recruitment_model_build_status_v1.md` and `docs/candidate_release_gates_v1.md`.
- Logged `run_011` in `experiments.csv`.

Findings:

- Clean 2022 Savant parquet:
  - 710,210 rows.
  - only `game_year=2022`.
- Trainable historical rows improved:
  - Run 010: 27 of 87 rows.
  - Run 011: 55 of 128 rows.
  - hitter: 22 of 42 rows, 13 success, 8 failure.
  - pitcher: 33 of 86 rows, 14 success, 17 failure.
- Time-forward holdout:
  - hitter success: AUC 0.850, Brier lift +0.126 vs role prior.
  - hitter failure: AUC 0.722, Brier lift +0.018.
  - pitcher success: AUC 0.762, Brier lift +0.082.
  - pitcher failure: AUC 0.575, Brier lift +0.029.
- Repeated CV stability:
  - hitter success promoted: AUC 0.772, Brier lift +0.048.
  - hitter failure promoted/watch: AUC 0.716, Brier lift +0.015.
  - pitcher success and failure are not promoted under repeated CV.

Decision:

- Role-specific KBO translation/failure-risk pilot modeling is now allowed.
- Hitter pre-KBO public Savant signals are model-stable enough for pilot use.
- Pitcher public-Savant-only models are not stable enough for candidate release.
- Keep final shortlist locked until market feasibility and pitcher context layers are built.

## 2026-06-14 Run 012 Market Layers And Context

Stage: build replacement-market and Asian-quota market-access layers before candidate release.

Actions:

- Added `src/data/collect_mlb_transactions.py`.
- Added `src/features/build_replacement_market_layers_v1.py`.
- Added `src/data/collect_asian_market_rosters.py`.
- Added `src/features/build_market_coverage_v0_3.py`.
- Built:
  - `outputs/tables/mlb_transactions_latest.csv`
  - `outputs/tables/mlb_replacement_market_status_v1.csv`
  - `outputs/tables/mlb_replacement_market_summary_v1.csv`
  - `outputs/tables/mlb_transaction_type_summary_v1.csv`
  - `outputs/tables/npb_official_roster_2026_v1.csv`
  - `outputs/tables/cpbl_official_roster_2026_v1.csv`
  - `outputs/tables/asian_quota_market_status_v1.csv`
  - `outputs/tables/asian_market_source_inventory_v1.csv`
  - `outputs/tables/candidate_market_coverage_v0_3.csv`
  - `outputs/tables/recruitment_gate_status_v2.csv`
- Added `docs/run_012_market_layers_and_context.md`.
- Updated `docs/recruitment_model_build_status_v1.md` and `docs/candidate_release_gates_v1.md`.

Findings:

- MLB official transaction feed returned 11,799 rows from 2025-10-01 to 2026-06-13.
- Transaction-aware market status now covers 1,745 candidate-pool rows:
  - 1,009 pitcher rows.
  - 736 outfield-priority hitter rows.
- Manual-check research-lead rows:
  - 265 pitcher rows.
  - 176 hitter rows.
- Medical-hold rows:
  - 279 pitcher rows.
  - 163 hitter rows.
- Recent release/DFA bucket:
  - 109 pitcher rows.
  - 73 hitter rows.
- Asian-quota inventory:
  - 810 NPB official roster rows.
  - 168 CPBL official roster rows.
  - 978 combined NPB/CPBL rows.
  - 154 nationality-pass rows.
  - 772 nationality-unknown rows, mostly because NPB official English rosters do not expose nationality.

Data-quality correction:

- MLB `DES` is Designated for Assignment.
- MLB `DFA` is Declared Free Agency.
- The collector separates the two so free agency is not counted as DFA.

Decision:

- Promote G3 from partial to partial-plus secured initial market layers.
- Do not release final candidates.
- Next run should add MiLB role/level continuity, medical/news/adaptation full text, contract/salary/willingness checks, ABL coverage, and NPB nationality verification.

## 2026-06-14 Run 013 MiLB Role Continuity Context

Stage: add MiLB role/level continuity for research-lead and medical-hold market candidates.

Actions:

- Added `src/data/collect_milb_stats_for_market_pool.py`.
- Added `src/features/build_milb_role_continuity_features_v1.py`.
- Collected official MLB Stats API MiLB year-by-year stats for:
  - AAA
  - AA
  - High-A
  - Single-A
  - Rookie
- Built:
  - `outputs/tables/milb_market_pool_stats_research_plus_medical_v1.csv`
  - `outputs/tables/milb_market_pool_stats_request_audit_research_plus_medical_v1.csv`
  - `outputs/tables/mlb_market_pool_milb_role_context_v1.csv`
  - `outputs/tables/mlb_market_pool_milb_role_context_summary_v1.csv`
  - `docs/run_013_milb_role_continuity_context.md`
- Updated:
  - `outputs/tables/six_layer_progress_v1.csv`
  - `docs/six_layer_progress_board.md`

Findings:

- Collection scope:
  - 883 candidate rows.
  - 4,415 level-by-player requests.
  - 9,560 MiLB stat rows.
- Coverage:
  - hitter research leads: 176 requested, 175 with MiLB stat track.
  - hitter medical holds: 163 requested, 161 with MiLB stat track.
  - pitcher research leads: 265 requested, 245 with MiLB stat track.
  - pitcher medical holds: 279 requested, 267 with MiLB stat track.
- Pitcher live-role buckets:
  - `current_aaa_starter_load`: 76.
  - `current_aaa_swing_or_multi_inning`: 79.
  - `current_aaa_bullpen_track`: 100.
  - `no_2026_milb_track`: 135.
- Hitter live-role buckets:
  - `current_aaa_regular`: 85.
  - `current_aaa_part_time`: 79.
  - `current_aaa_tiny_sample`: 78.
  - `no_2026_milb_track`: 79.

Data-quality correction:

- Rows outside the Run 013 collection scope are marked `not_collected_in_run_013_scope`, not `no_milb_stats_found`.
- This avoids confusing uncollected market-watch rows with true missing MiLB records.

Six-layer progress update:

- Layer 3 candidate market construction: 60% -> 68%.
- Layer 4 KBO translation model: 50% -> 56%.
- Layer 5 failure risk model: 45% -> 53%.
- Layer 6 SSG fit ranking: 20% -> 25%, still locked.

Decision:

- Promote MiLB role/level context as a candidate-side feature layer.
- Do not release final candidates.
- Next run should backfill comparable historical MiLB context for prior KBO foreign players or mine injury/news/adaptation full text.

## 2026-06-14 Run 014 SSG Hidden Weakness Interaction Development

Stage: develop Layer 1 hidden-weakness mining before candidate release.

Actions:

- Added and ran `src/modeling/mine_ssg_hidden_weakness_interactions_v1.py`.
- Built game-level SSG 2026 interaction mining with starter length, bullpen workload, OF/DH run conversion, weather buckets, and role aggregates.
- Built role-context evidence for hitter and pitcher target-feature translation.
- Created:
  - `outputs/tables/ssg_hidden_weakness_game_frame_v1.csv`
  - `outputs/tables/ssg_hidden_weakness_game_interactions_v1.csv`
  - `outputs/tables/ssg_hidden_weakness_role_context_v1.csv`
  - `outputs/tables/ssg_hidden_weakness_message_candidates_v1.csv`
  - `outputs/tables/ssg_hidden_weakness_need_contract_v1.csv`
  - `docs/run_014_ssg_hidden_weakness_interaction_development.md`
- Updated:
  - `outputs/tables/six_layer_progress_v1.csv`
  - `docs/six_layer_progress_board.md`
  - `outputs/tables/recruitment_gate_status_v4.csv`

Findings:

- The sharpest hidden message is a game-script double bind, not a generic OF power gap.
- Top pair rule: bullpen 4+ walks plus high-leverage OF 0 RBI, 7 games, .000 win%, -4.86 average run differential.
- Broader pair rule: bullpen 3+ ER plus OF RBI under 3, 17 games, .000 win%, -5.82 average run differential.
- Hitter need is RHP-specific:
  - OF 3-5 run-production vs right-handed starters: OPS .595, OBP .294, SLG .301, ISO .084, OPS/OBP/SLG rank 10/10.
  - The same OF 3-5 role vs left-handed starters: OPS 1.048, OBP .463, SLG .585, ISO .231, rank 2/10.
- Pitcher need is traffic command:
  - RISP: ERA 15.13, WHIP 1.78, OPSA .847, rank 10/10.
  - runners on base: ERA 9.75, WHIP 1.56, OPSA .800, rank 10/10.

Six-layer progress update:

- Layer 1 SSG hidden weakness mining: 75% -> 84%.
- Layers 2-6 unchanged.
- Candidate names remain locked.

Decision:

- Promote Layer 1 to `pass_with_interaction_messages`.
- Use the new target contract for later player screening:
  - foreign pitcher: load-bearing starter with traffic command and early-count/zone stability.
  - foreign hitter: RHP-resistant OF/DH bat with OBP plus damage and two-strike survival.
- Next Layer 1 work should add defense, baserunning, park, opponent quality, and refreshed post-2026-06-11 data.

## 2026-06-14 Run 015 SSG Hidden Weakness Context Friction

Stage: continue Layer 1 hidden-weakness mining with context-friction variables.

Actions:

- Added and ran `src/modeling/mine_ssg_hidden_weakness_context_v2.py`.
- Attached:
  - opponent starter handedness;
  - unearned runs;
  - inning-line error proxies;
  - team and OF/DH GDP/CS run-kill events;
  - opponent current win percentage and rank;
  - opponent batting/pitching rank context;
  - park run environment.
- Created:
  - `outputs/tables/ssg_hidden_weakness_context_frame_v2.csv`
  - `outputs/tables/ssg_hidden_weakness_context_interactions_v2.csv`
  - `outputs/tables/ssg_hidden_weakness_context_message_upgrade_v2.csv`
  - `outputs/tables/ssg_hidden_weakness_context_feature_contract_v2.csv`
  - `docs/run_015_ssg_hidden_weakness_context_friction.md`
- Updated:
  - `outputs/tables/six_layer_progress_v1.csv`
  - `docs/six_layer_progress_board.md`
  - `outputs/tables/recruitment_gate_status_v5.csv`

Findings:

- RHP context double bind:
  - OF RBI < 3 + opponent runs >= 6 + opponent starter right-handed: 20 games, .100 win%, -5.10 average run differential.
- RHP-side run-killing outs:
  - OF table-setter OBP <= .250 + opponent starter right-handed + OF/DH GDP or CS >= 1: 9 games, .000 win%, -5.11 average run differential.
- Extra-out damage:
  - high-leverage OF 0 RBI + unearned runs >= 1: 8 games, .000 win%, -4.50 average run differential, 2.00 average unearned runs.
- Top-opponent stress:
  - starter < 5 IP + high-leverage OF 0 RBI + opponent top-3 win%: 6 games, .000 win%, -5.83 average run differential.

Six-layer progress update:

- Layer 1 SSG hidden weakness mining: 84% -> 88%.
- Layers 2-6 unchanged.
- Candidate names remain locked.

Decision:

- Promote Layer 1 to `pass_with_context_friction_messages`.
- Upgrade the feature contract:
  - foreign pitcher: traffic command plus extra-out resilience.
  - foreign hitter: RHP-resistant OBP plus damage with run-kill avoidance.
- Next Layer 1 step should refresh post-2026-06-11 STATIZ/current-game data and add stronger public play-by-play/defensive/baserunning proxies before final presentation lock.

## 2026-06-14 Run 016 SSG Hidden Weakness Robustness Validation

Stage: stress-test Layer 1 before treating it as a candidate-scoring feature contract.

Actions:

- Added and ran `src/modeling/validate_ssg_hidden_weakness_robustness_v3.py`.
- Tested Run 015 rules with:
  - half-season and month splits;
  - leave-one-opponent-out sensitivity;
  - 3,000-iteration bootstrap intervals;
  - 3,000-iteration permutation baselines;
  - negative controls.
- Created:
  - `outputs/tables/ssg_hidden_weakness_robustness_rules_v3.csv`
  - `outputs/tables/ssg_hidden_weakness_negative_controls_v3.csv`
  - `outputs/tables/ssg_hidden_weakness_time_split_v3.csv`
  - `outputs/tables/ssg_hidden_weakness_leave_one_opponent_v3.csv`
  - `outputs/tables/ssg_hidden_weakness_bootstrap_permutation_v3.csv`
  - `outputs/tables/ssg_hidden_weakness_robustness_decisions_v3.csv`
  - `outputs/tables/ssg_hidden_weakness_final_message_v3.csv`
  - `docs/run_016_ssg_hidden_weakness_robustness_validation.md`
- Updated:
  - `outputs/tables/six_layer_progress_v1.csv`
  - `docs/six_layer_progress_board.md`
  - `outputs/tables/recruitment_gate_status_v6.csv`

Findings:

- Promoted to core:
  - RHP low OF conversion run trade: 20 games, .100 win%, -5.10 run differential.
  - RHP OF/DH run-kill: 9 games, .000 win%, -5.11 run differential.
  - Extra-out high OF void: 8 games, .000 win%, -4.50 run differential.
- Kept support-only:
  - Top-opponent short start plus OF void: 6 games, .000 win%, -5.83 run differential.
- Negative controls:
  - OF HR zero only: .405 win%, -1.29 run differential.
  - OF RBI < 3 only: .333 win%, -2.04 run differential.

Six-layer progress update:

- Layer 1 SSG hidden weakness mining: 88% -> 91%.
- Layers 2-6 unchanged.
- Candidate names remain locked.

Decision:

- Promote Layer 1 to `near_freeze_after_robustness_validation`.
- Use Layer 1 as a near-final candidate-scoring feature contract after one refreshed-data check.
- Next work should move to Layers 2-5 unless refreshed 2026 data changes the Layer 1 message.

## 2026-06-14 Run 017 SSG Layer 1 Presentation Bridge

Stage: convert the near-final Layer 1 message into a presentation-ready and candidate-scoring-ready bridge.

Actions:

- Added and ran `src/modeling/build_ssg_layer1_presentation_bridge_v4.py`.
- Converted the Run 016 message into:
  - plain-language story versions;
  - likely objection responses;
  - candidate feature blueprint;
  - evidence-to-message trace;
  - final freeze checklist.
- Created:
  - `outputs/tables/ssg_layer1_plain_language_story_v4.csv`
  - `outputs/tables/ssg_layer1_objection_response_v4.csv`
  - `outputs/tables/ssg_layer1_candidate_feature_blueprint_v4.csv`
  - `outputs/tables/ssg_layer1_evidence_to_message_trace_v4.csv`
  - `outputs/tables/ssg_layer1_freeze_checklist_v4.csv`
  - `docs/run_017_ssg_layer1_presentation_bridge.md`
- Updated:
  - `outputs/tables/six_layer_progress_v1.csv`
  - `docs/six_layer_progress_board.md`
  - `outputs/tables/recruitment_gate_status_v7.csv`

Findings:

- Final plain-language message:
  - SSG's problem is not simply outfield home-run shortage.
  - The hidden weakness is a RHP-side game-script lock where OF/DH low conversion, run-killing outs, and extra-out damage remove comeback paths.
- Presentation defense:
  - OF HR zero only: .405 win%, -1.29 run differential.
  - OF RBI < 3 only: .333 win%, -2.04 run differential.
  - RHP low OF conversion run trade: 20 games, .100 win%, -5.10 run differential.
  - RHP OF/DH run-kill: 9 games, .000 win%, -5.11 run differential.
  - Extra-out high OF void: 8 games, .000 win%, -4.50 run differential.
- Candidate feature bridge:
  - foreign hitter: vs RHP on-base plus damage, two-strike contact floor, low GDP/CS run-kill risk, OF/DH role continuity.
  - foreign pitcher: low free-pass volatility, five-inning floor, damage control after traffic, ABS/zone-command stability.
  - Asian quota: multi-inning or spot-start shock absorption and contract-realistic optionality.

Six-layer progress update:

- Layer 1 SSG hidden weakness mining: 91% -> 93%.
- Layers 2-6 unchanged.
- Candidate names remain locked.

Decision:

- Promote Layer 1 to `presentation_bridge_ready_pending_refresh`.
- Use the Layer 1 feature blueprint as the handoff into Layers 2-5.
- Do not final-freeze Layer 1 until refreshed post-2026-06-11 data and stronger play-by-play/defense/baserunning proxies are attached.

## 2026-06-14 Run 018 NPB Official Stats Market Expansion

Stage: expand Layer 3 candidate-market construction with current NPB performance context.

Actions:

- Added and ran `src/data/collect_npb_official_stats_2026.py`.
- Collected official NPB 2026 player stats for all 12 teams across:
  - regular-season batting;
  - regular-season pitching;
  - farm-league batting;
  - farm-league pitching.
- Joined NPB official stat rows to existing official roster fields and foreign-player nationality seed hints where available.
- Created:
  - `outputs/tables/npb_official_player_stats_2026_v1.csv`
  - `outputs/tables/npb_official_stats_source_inventory_2026_v1.csv`
  - `outputs/tables/npb_player_market_features_2026_v1.csv`
  - `outputs/tables/npb_market_depth_summary_2026_v1.csv`
  - `docs/run_018_npb_official_stats_market_expansion.md`
- Updated:
  - `outputs/tables/six_layer_progress_v1.csv`
  - `docs/six_layer_progress_board.md`
  - `outputs/tables/recruitment_gate_status_v8.csv`

Findings:

- All 48 official NPB stat pages parsed successfully.
- Unified NPB official stats: 2,186 rows.
- Coverage:
  - first-team batting: 617 rows;
  - first-team pitching: 313 rows;
  - farm batting: 835 rows;
  - farm pitching: 421 rows.
- Added market-screening features:
  - batters: OPS, ISO, BB%, SO%, HR/PA, SB success%, GDP+CS run-kill proxy, playing-time buckets;
  - pitchers: decimal IP, WHIP, K%, BB%, K-BB%, K/9, BB/9, HR/9, 30+ IP workload proxy, traffic-command proxy.

Six-layer progress update:

- Layer 3 candidate market construction: 68% -> 72%.
- Layers 1, 2, 4, 5, and 6 unchanged.
- Candidate names remain locked.

Decision:

- Promote Layer 3 to `partial_plus_npb_official_stats_context`.
- Treat NPB as performance-context ready, not feasibility-ready.
- Next Layer 3 gaps:
  - NPB nationality verification beyond known foreign-player seed rows;
  - salary/contract/buyout or proxy tiers;
  - ABL roster/stats;
  - news/manual market feasibility checks;
  - NPB/CPBL integration into SSG fit ranking.

## 2026-06-14 Run 019 MiLB All-Candidate And Historical Backfill

Stage: expand current-market MiLB coverage and historical KBO pre-arrival MiLB features.

Actions:

- Reran `src/data/collect_milb_stats_for_market_pool.py` with `--scope all`.
- Rebuilt `src/features/build_milb_role_continuity_features_v1.py` after making season parsing robust to rare fractional season labels.
- Added and ran `src/data/collect_historical_kbo_milb_stats.py`.
- Created:
  - `outputs/tables/milb_market_pool_stats_all_v1.csv`
  - `outputs/tables/milb_market_pool_stats_request_audit_all_v1.csv`
  - `outputs/tables/historical_kbo_prearrival_milb_stats_v1.csv`
  - `outputs/tables/historical_kbo_prearrival_milb_request_audit_v1.csv`
  - `outputs/tables/historical_kbo_prearrival_milb_features_v1.csv`
  - `docs/run_019_milb_all_and_historical_backfill.md`
  - `outputs/tables/recruitment_gate_status_v9.csv`
- Updated:
  - `outputs/tables/mlb_market_pool_milb_role_context_v1.csv`
  - `outputs/tables/mlb_market_pool_milb_role_context_summary_v1.csv`
  - `outputs/tables/six_layer_progress_v1.csv`
  - `docs/six_layer_progress_board.md`

Findings:

- Current market MiLB requests: 8,725 of 8,725 HTTP 200.
- Current market MiLB stat rows: 18,258.
- Current market rows requested: 1,745 of 1,745.
- Current market rows with MiLB stat track: 1,664.
- Historical KBO pre-arrival MiLB requests: 280 of 280 HTTP 200.
- Historical pre-KBO MiLB feature rows: 71 of 71 matched rows.
- Historical role coverage:
  - hitters: 22 of 22 rows with pre-KBO MiLB features;
  - pitchers: 49 of 49 rows with pre-KBO MiLB features.

Six-layer progress update:

- Layer 2 KBO foreign-player success/failure archetype mining: 55% -> 62%.
- Layer 3 candidate market construction: 72% -> 80%.
- Layer 4 KBO translation model: 56% -> 64%.
- Layer 5 failure risk model: 53% -> 58%.
- Layer 6 SSG fit ranking: 25% -> 28%.
- Layer 1 unchanged at 93%.
- Candidate names remain locked.

Decision:

- Promote Layer 3 to `partial_plus_full_milb_and_npb_context`.
- Promote Layer 4 to `pilot_plus_historical_milb_backfill`.
- Do not release a shortlist until:
  - historical MiLB features are joined into model marts and repeated CV is rerun;
  - NPB contract/salary/buyout and nationality checks are added;
  - KBO/STATIZ current data is refreshed after 2026-06-11;
  - injury/news/adaptation and Korea-willingness variables are attached.

## 2026-06-21 Run 020 Translation And Failure-Risk v0.2 MiLB Modeling

Hypothesis:

- Historical pre-KBO MiLB features should expand model-ready rows and reveal whether KBO translation/failure-risk scores can be promoted into the SSG fit-ranking layer.

Actions:

- Added `src/modeling/build_recruitment_model_marts_v0_2.py`.
- Added `src/modeling/train_kbo_translation_failure_models_v0_2.py`.
- Built `outputs/tables/kbo_translation_feature_mart_v0_2.csv` and `outputs/tables/failure_risk_feature_mart_v0_2.csv`.
- Reran time-forward holdout and repeated stratified CV with a broader `has_model_pre_kbo_features` flag.
- Wrote v0.1 vs v0.2 comparison and v0.2 feature-signal audit.
- Updated six-layer progress and gate status in `outputs/tables/recruitment_gate_status_v10.csv`.

Validation:

- v0.2 model-ready rows: 71, up from 55.
- Hitter model-ready rows: 22, unchanged.
- Pitcher model-ready rows: 49, up from 33.
- MiLB-only pitcher rows added to model scope: 16.
- Repeated CV score rows: 1,440.
- Feature-signal rows: 146.

Findings:

- Strict repeated CV did not promote the all-feature v0.2 models.
- Hitter models lost v0.1 pilot-promote status because the row count stayed at 22 while the feature set widened.
- Pitcher models gained validation coverage but still did not reliably beat role-prior baselines.
- Pitcher risk signals suggest that raw bat-missing upside needs to be separated from damage suppression, command friction, and recent role continuity.

Decision:

- Promote Run 020 as a diagnostic and archetype-mining improvement.
- Do not promote v0.2 all-feature scores into final SSG fit ranking.
- Keep candidate names locked.

Next:

- Run compact feature-family ablations:
  Savant-only, MiLB level/role only, MiLB damage/command only, recent-track continuity only, and compact mixed models with at most 6-10 features per role/target.

## 2026-06-21 Run 021 Feature-Family Ablation v0.3

Hypothesis:

- Compact feature-family ablation should recover usable signal groups after all-feature v0.2 overfit.

Actions:

- Added `src/modeling/run_kbo_feature_family_ablation_v0_3.py`.
- Built `outputs/tables/kbo_translation_feature_family_ablation_mart_v0_3.csv`.
- Tested five feature families: `savant_only`, `milb_level_role`, `milb_damage_command`, `recent_track_continuity`, and `compact_mixed`.
- Wrote fold-level CV scores, feature-family comparison, and target-level gate decisions.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v11.csv`.

Validation:

- Feature-family CV score rows: 7,200.
- Comparison rows: 80.
- Decision rows: 4.
- Candidate release gate remained locked.

Findings:

- Hitter `savant_only` cleared the pilot-promotion gate for both success and failure.
- Hitter success: AUC 0.833, Brier lift +0.073, top-25 precision lift +0.222.
- Hitter failure: AUC 0.738, Brier lift +0.023, top-25 precision lift +0.344.
- Pitcher `milb_damage_command` reached watch status for success only: AUC 0.603, Brier lift +0.0068, top-25 precision lift +0.118.
- Pitcher failure did not clear the Brier gate, so pitcher model scoring remains diagnostic only.

Decision:

- Promote hitter `savant_only` as a future pilot score component.
- Keep pitcher `milb_damage_command` as diagnostic/watch only.
- Do not release candidate names or rankings.

Next:

- Build candidate-side hitter Savant pilot component.
- Convert pitcher MiLB damage/command into diagnostic tags.
- Add injury/news/adaptation, Korea-willingness, contract, salary, buyout, and NPB nationality feasibility before fit ranking.

## 2026-06-21 Run 022 Candidate-Side Signal Join v0.1

Hypothesis:

- Validated model families should be attached to candidate markets as locked signal components rather than recommendations.

Actions:

- Added `src/modeling/build_candidate_side_signal_join_v0_1.py`.
- Built hitter Savant pilot component for MLB outfielder/hitter candidates.
- Reran candidate-compatible hitter model audit with 17 available Savant features.
- Built pitcher MiLB damage/command diagnostic tags.
- Built Asian-quota feasibility tags from current NPB/CPBL roster and nationality gates.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v12.csv`.

Validation:

- Hitter candidate rows: 736.
- Pitcher candidate rows: 1,009.
- Asian-quota market rows: 978.
- Candidate-compatible hitter success model: AUC 0.808, Brier lift +0.065.
- Candidate-compatible hitter failure model: AUC 0.757, Brier lift +0.027.
- Pitcher positive diagnostic-watch rows: 79.
- Asian nationality-pass but contract-unknown rows: 154.
- Every row-level output keeps `is_final_recommendation = False`, `shortlist_label_allowed = False`, and `candidate_name_release_allowed = False`.

Decision:

- Promote hitter Savant pilot component into the next locked fit-preparation mart.
- Keep pitcher output as diagnostic tags only.
- Keep Asian-quota output as feasibility inventory only.
- Do not release recommendations or shortlist labels.

Next:

- Build locked SSG fit ranking preparation mart with research-only labels.
- Add contract, salary, buyout, injury/news/adaptation, Korea-willingness, and manual feasibility context before any candidate release.

## 2026-06-21 Run 023 Locked SSG Fit Preparation Mart v0.1

Hypothesis:

- Three acquisition slots should be consolidated into a locked SSG fit-preparation mart before any final candidate ranking.

Actions:

- Added `src/modeling/build_ssg_fit_preparation_mart_v0_1.py`.
- Built a single locked mart for foreign hitter, foreign pitcher, and Asian-quota candidates.
- Mapped the SSG Layer 1 feature contract to candidate-side proxy columns.
- Kept hitter Savant pilot component as a research input.
- Kept pitcher output as diagnostic-only, not a promoted model score.
- Added NPB official-stat context to Asian-quota feasibility where available.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v13.csv`.

Validation:

- Fit-preparation mart rows: 2,723.
- Foreign hitter rows: 736.
- Foreign pitcher rows: 1,009.
- Asian-quota rows: 978.
- Release locks passed for all 2,723 rows.
- Pitcher score gate stayed diagnostic-only for all 1,009 pitcher rows.
- Asian-quota contract/salary/buyout gap stayed visible for all 978 Asian-quota rows.

Decision:

- Promote the fit-preparation mart as the next working table.
- Do not release final names, shortlist labels, or recommendations.
- Treat `fit_preparation_index` as research triage only.

Next:

- Add manual contract, salary, buyout, medical/news/adaptation, and Korea-willingness checks.
- Refresh current SSG data when available.
- Only then build the final SSG fit ranking review.

## 2026-06-21 Run 024 Market Realism Layer v0.1

Hypothesis:

- Official roster, transaction, and Asian-quota feasibility gates should narrow the fit-prep mart into a realistic manual verification queue.

Actions:

- Refreshed official MLB transaction data through 2026-06-21.
- Refreshed official MLB roster status as of 2026-06-21.
- Added `src/modeling/build_market_realism_layer_v0_1.py`.
- Built contract-control buckets, medical proxy buckets, KBO cost-rule buckets, and manual check flags.
- Built a research-only manual verification worklist.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v14.csv`.

Validation:

- MLB transaction rows: 12,139.
- MLB roster rows: 8,197.
- Market-realism layer rows: 2,723.
- Foreign hitter manual-contact priority rows: 16.
- Foreign pitcher manual-contact priority rows: 30.
- Asian-quota buyout/salary/agent-check rows: 154.
- Release locks passed for all 2,723 rows.

Decision:

- Promote the market-realism layer as the current working queue.
- Do not release candidate recommendations or shortlist labels.
- Treat `market_realism_score` and the blended field as triage-only fields.

Next:

- Refresh candidate-specific news after loading Naver credentials in the shell.
- Add salary, opt-out, contract, transfer-fee, buyout, and agent/willingness sources.

## 2026-06-21 Run 025 Candidate News Pilot v0.1

Hypothesis:

- English candidate-specific news metadata should add medical, contract, and overseas-context signals to the market-realism queue without requiring Google API.

Actions:

- Added `src/data/collect_candidate_news.py`.
- Added `src/features/build_candidate_news_signals.py`.
- Collected a small Google News RSS pilot for 26 Run 024 priority candidates.
- Wrote candidate-level news signal summaries and joined them back to the full 2,723-row manual worklist.
- Recorded Naver as skipped because `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` were not loaded in the shell environment.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v15.csv`.

Validation:

- Pilot candidate rows: 26.
- News metadata rows: 182.
- Candidate-name matched article rows: 118.
- Usable news-signal rows: 119.
- Google API needed: no.
- Naver candidate-specific news: skipped, missing shell environment credentials.
- Release locks passed for all 2,723 joined rows.

Decision:

- Promote the English news pilot as a research-only risk layer.
- Do not release candidate recommendations or shortlist labels.
- Treat candidate-news status as a manual review signal only.

Next:

- Load Naver credentials in the shell and rerun the same pilot for Korean candidate-specific news.
- Expand the news scope after the Korean pilot validates precision.

## 2026-06-21 Run 026 Candidate News Expansion v0.2

Hypothesis:

- Expanded candidate-specific English news metadata should strengthen market realism and risk screening without requiring Google API.

Actions:

- Generalized the news collector and signal builder so candidate-news runs can be versioned without overwriting the Run 025 pilot.
- Expanded Google News RSS collection from 26 pilot candidates to 200 market-realism priority candidates.
- Joined expanded news signals back to the full 2,723-row manual worklist.
- Recorded Naver as skipped because `NAVER_CLIENT_ID` and `NAVER_CLIENT_SECRET` were not loaded in the shell environment.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v16.csv`.

Validation:

- Scoped candidate rows: 200.
- News metadata rows: 613.
- Candidate-name matched article rows: 339.
- Usable news-signal rows: 340.
- Usable English article rows: 340.
- Usable Korean article rows: 0.
- Google API needed: no.
- Naver candidate-specific news: skipped, missing shell environment credentials.
- Joined worklist rows: 2,723.
- Release locks passed for all 2,723 joined rows.

Decision:

- Promote the expanded English news layer as a research-only manual review queue.
- Do not release candidate recommendations or shortlist labels.
- Treat Asian-quota English-news gaps as source coverage gaps, not as evidence of low risk.

Next:

- Load Naver credentials in the shell and rerun candidate-specific Korean news.
- Add salary, opt-out, transfer-fee, buyout, agent, and Korea-willingness sources before any shortlist labels.

## 2026-06-21 Run 027 Korean-News Fallback And Manual Feasibility Worklist v0.1

Hypothesis:

- Korean no-key news fallback and manual feasibility source lanes should clarify remaining reality-check blockers before candidate release.

Actions:

- Added `google_news_rss_ko` support to the candidate-news collector.
- Tested Korean-locale Google News RSS on a 62-candidate priority scope.
- Combined Run 026 English news metadata with the Run 027 Korean fallback audit into v0.3 candidate-news outputs.
- Added `src/modeling/build_manual_feasibility_worklist_v0_1.py`.
- Built manual source lanes for Korean news, medical file review, contract/salary/options, Asian-league buyout/transfer fee, agent, and Korea-willingness checks.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v17.csv`.

Validation:

- Korean fallback scope rows: 62.
- Google KR RSS attempted queries: 124.
- Google KR RSS article rows: 0.
- Google KR RSS error rows: 124.
- Combined news article rows: 613.
- Combined usable news-signal rows: 340.
- Usable Korean article rows: 0.
- Manual feasibility worklist rows: 2,723.
- Manual source follow-up rows: 1,706.
- Release locks passed for all joined/manual rows.

Decision:

- Keep Google KR RSS as optional fallback only.
- Do not treat Google KR RSS as a substitute for Naver/local Korean news.
- Promote the manual feasibility source worklist as the next reality-check queue.
- Do not release candidate recommendations or shortlist labels.

Next:

- Load Naver credentials in the shell and run candidate-specific Korean news.
- Fill source-lane values for salary, contract terms, options, buyout/transfer fee, medical availability, agent signals, and Korea-willingness.

## 2026-06-21 Run 028 Naver News Ready State v0.1

Hypothesis:

- Naver collection should be executable without exposing secrets in commands, source files, Git, or output tables.

Actions:

- Added optional `--env-file` support to `src/data/collect_candidate_news.py`.
- Documented a local gitignored `.env.naver` workflow.
- Added `docs/run_028_naver_news_ready_state_v0_1.md`.
- Added `outputs/tables/recruitment_gate_status_v18.csv`.

Validation:

- Collector compiles successfully.
- `.env.*` files are gitignored.
- Current shell still has no `NAVER_CLIENT_ID` or `NAVER_CLIENT_SECRET`.
- No Naver rows were collected in this run.
- Progress remains unchanged until real Naver data is collected.

Decision:

- Ready to run Naver collection once local credentials are available.
- Do not put Naver keys in shell command text, source files, tracked docs, or committed outputs.

Next:

- Create local `.env.naver`, then run the documented Naver collection command and combine it with the existing English news layer.

## 2026-06-21 Run 029 Naver Candidate News v0.4

Hypothesis:

- Naver candidate-news metadata should reduce the Korean-source gap and add usable medical, contract, and Korea-overseas risk signals.

Actions:

- Created a local gitignored `.env.naver` file and verified Naver News API access without committing secrets.
- Collected Naver News metadata for the 62-candidate priority scope.
- Combined Naver metadata with the existing English v0.2 candidate-news layer into v0.4 outputs.
- Rebuilt the manual feasibility worklist on the v0.4 news join.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v19.csv`.

Validation:

- Naver priority scope rows: 62.
- Naver article metadata rows: 39.
- Naver candidate-name matched rows: 31.
- Combined article rows: 652.
- Combined usable news-signal rows: 367.
- Usable Korean article rows: 27.
- Candidates with usable Korean articles: 10.
- Manual Korean-news missing lane rows: 1,696.
- Joined worklist rows: 2,723.
- Release locks passed for all joined/manual rows.

Decision:

- Promote Naver candidate-news signals as research-only risk context.
- Do not release candidate recommendations, shortlist labels, scores, or names.
- Continue treating salary, contract, option, buyout, medical file, agent, and Korea-willingness checks as manual gates.

Next:

- Fill source-lane values for salary, contract terms, options, buyout/transfer fee, medical availability, agent signals, and Korea-willingness.

## 2026-06-22 Run 030 Official Market Refresh v0.2

Hypothesis:

- The candidate market layer should use the latest official MLB roster and
  transaction status before any feasibility or ranking work advances.

Actions:

- Collected MLB transactions from 2025-10-01 through 2026-06-22.
- Collected MLB roster status for 2026-06-22.
- Added `--run-date` and `--output-suffix` support to the market-realism builder.
- Rebuilt market realism as `outputs/tables/ssg_market_realism_layer_v0_2.csv`.
- Rejoined market realism to English plus Naver news as
  `outputs/tables/ssg_market_realism_news_join_v0_5.csv`.
- Rebuilt the manual feasibility source worklist as v0.3.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v20.csv`.

Validation:

- MLB transaction rows: 12,155.
- MLB roster/status rows: 8,198.
- Market realism rows: 2,723.
- All market rows carry `market_realism_run_date = 2026-06-22`.
- Market realism score changed for 16 rows.
- Market realism status changed for 10 rows.
- Manual source follow-up rows: 1,703.
- Release locks passed for all 2,723 market rows.

Decision:

- Promote v0.2 market realism and v0.5 market-news join as the current
  feasibility base.
- Do not release candidate recommendations, shortlist labels, scores, or names.

Next:

- Fill source-lane values for salary, contract terms, options, buyout/transfer
  fee, medical availability, agent signals, and Korea-willingness.

## 2026-06-22 Run 031 KBO Foreign Archetype Bridge v0.2

Hypothesis:

- Layer 2 should connect historical KBO success/failure archetypes to
  pre-arrival feature-family fingerprints, rather than relying on one blunt
  success/failure classifier.

Actions:

- Added `src/modeling/build_kbo_foreign_archetype_bridge_v0_2.py`.
- Joined KBO outcome archetypes to the v0.2 translation mart.
- Built pre-arrival feature-family scores from Savant and MiLB signals.
- Mined one-family and two-family rule lifts with permutation checks.
- Separated semantically aligned research rules from counterintuitive
  negative-control rules.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v21.csv`.

Validation:

- Outcome archetype rows joined: 127 / 127.
- Pre-arrival fingerprint rows available: 71 / 127.
- Cluster profiles created: 7 / 7.
- Rule lifts mined: 294.
- Semantically aligned research rules: 4.
- Counterintuitive negative-control rules: 15.
- Release locks passed for all bridge rows.

Decision:

- Promote the v0.2 archetype bridge as the current Layer 2 evidence base.
- Treat pitcher raw-miss-without-role-continuity as a research risk signal.
- Treat hitter archetype rules as not yet scoreable beyond pilot component
  status because the sample is thin and counterintuitive signals are present.
- Do not release candidate recommendations, shortlist labels, scores, or names.

Next:

- Backfill 2017-2022 historical IDs and pre-arrival features.
- Add historical NPB/CPBL pre-arrival context.
- Validate promoted Layer 2 rules against candidate-side source lanes before
  using them in Layer 6.

## 2026-06-22 Run 032 Candidate Failure Risk Ledger v0.1

Hypothesis:

- Before any SSG fit ranking can be trusted, every candidate should have a
  source-backed explanation of possible failure modes.

Actions:

- Added `src/modeling/build_candidate_failure_risk_ledger_v0_1.py`.
- Combined Layer 2 archetype flags, Layer 3 market/news context, candidate-side
  hitter/pitcher/Asian-quota signals, and manual source lanes.
- Attached candidate-side primary signal and feature-coverage values from the
  locked SSG fit-preparation mart.
- Built six failure-risk buckets: medical, contract/cost, role-fit, KBO
  translation, adaptation/willingness, and data/source gap.
- Added risk-tier summaries and gate audit outputs.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v22.csv`.

Validation:

- Failure-risk ledger rows: 2,723.
- All candidates receive six risk buckets: 2,723 / 2,723.
- Layer 2 flags attached: 1,654 / 2,723.
- Manual source lanes integrated: 1,703 / 2,723.
- Release locks passed for all 2,723 rows.
- Tier-1 blocker review rows: 355 foreign hitters and 722 foreign pitchers.

Decision:

- Promote the candidate failure-risk ledger as the current Layer 5 evidence
  base.
- Do not use `failure_risk_index` as a final public ranking score.
- Keep candidate recommendations, shortlist labels, scores, and names locked.

Next:

- Fill source values for medical files, salary, opt-out, buyout, agent, and
  Korea-willingness.
- Calibrate risk buckets against resolved cases before Layer 6 ranking.

## 2026-06-22 Run 033 SSG Risk-Adjusted Fit Queue v0.1

Hypothesis:

- A candidate should not move toward final SSG review unless SSG fit, KBO
  translation readiness, market realism, tool/process signal, surplus/access,
  failure-risk penalty, and source confidence survive together.

Actions:

- Added `src/modeling/build_ssg_risk_adjusted_fit_queue_v0_1.py`.
- Built an internal risk-adjusted SSG fit queue for all 2,723 candidates.
- Added default Dacon-style scoring plus four sensitivity variants:
  SSG-fit heavy, risk-conservative, market-realism heavy, and
  translation-heavy.
- Created slot/lane summary, factor summary, sensitivity summary, and gate
  audit outputs.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v23.csv`.

Validation:

- Risk-adjusted fit queue rows: 2,723.
- All candidates receive an internal score: 2,723 / 2,723.
- Sensitivity variants attached: 2,723 / 2,723.
- Release locks passed for all 2,723 rows.
- Locked deep-review lanes: 37 foreign hitters and 47 foreign pitchers.
- Asian quota has 18 source-fill priority rows and no clean deep-review lane.

Decision:

- Promote the risk-adjusted fit queue as the current Layer 6 evidence base.
- Treat all scores, ranks, lanes, and candidate names as internal locked review
  artifacts only.
- Do not release candidate names, rankings, shortlist labels, or
  recommendations.

Next:

- Fill source values for salary, opt-out, buyout, agent, medical files, and
  Korea-willingness.
- Calibrate internal scores against resolved cases and manual scouting notes.
- Only after that, consider unlocking candidate-name discussion for the final
  team shortlist.

## 2026-06-22 Run 034 Fit Source-Fill Packet v0.1

Hypothesis:

- The next unlock step after a risk-adjusted fit queue is not another score; it
  is source verification for contract, medical, passport, agent, and
  Korea-willingness blockers.

Actions:

- Added `src/data/collect_fit_queue_source_news_v0_1.py`.
- Collected fresh Naver Search News metadata for the Layer 6 source-fill scope.
- Added `src/modeling/build_fit_source_fill_packet_v0_1.py`.
- Combined prior article relevance with fresh Naver metadata.
- Built a 118-row source-fill packet with evidence statuses and next manual
  actions.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v24.csv`.

Validation:

- Source-fill scope rows: 118.
- Naver query attempts: 236.
- Fresh Naver article metadata rows: 3.
- Candidate-name matched fresh rows: 2.
- Source-fill packet rows: 118.
- Release locks passed for all 118 rows.

Decision:

- Promote the source-fill packet as the current bridge from Layer 6 modeling to
  manual scouting-card work.
- Keep all candidate names, ranks, scores, shortlist labels, and
  recommendations locked.

Next:

- Build locked scouting-card templates for source-supported rows.
- Fill exact salary, option, buyout, transfer-fee, agent, passport, medical, and
  Korea-willingness values.
- Recalibrate failure-risk and fit ranking only after those source values are
  attached.

## 2026-06-22 Run 035 Locked Scouting Cards v0.1

Hypothesis:

- The project can move from model queue to scouting workflow without releasing
  candidate names, exact scores, exact ranks, shortlist labels, or
  recommendations.

Actions:

- Added `src/modeling/build_locked_scouting_cards_v0_1.py`.
- Built candidate-name-free scouting-card templates from source-supported rows.
- Removed player names, team/org fields, exact internal scores, and exact ranks
  from the card output.
- Added a card schema, slot-specific question bank, slot summary, and gate
  audit.
- Updated six-layer progress and `outputs/tables/recruitment_gate_status_v25.csv`.

Validation:

- Locked scouting-card rows: 72.
- Foreign hitter cards: 31.
- Foreign pitcher cards: 41.
- Asian quota cards: 0 because the slot remains source-blocked.
- Candidate identifiers removed from card template output.
- Release locks passed for all 72 cards.

Decision:

- Promote the locked scouting-card templates as the current Layer 6 handoff
  artifact.
- Do not release candidate names, ranks, scores, shortlist labels, scouting-card
  release labels, or recommendations.

Next:

- Fill manual scouting notes into the card structure.
- Attach exact contract values, medical status, and Korea-willingness evidence.
- Recalibrate risk and fit only after the card evidence is filled.
