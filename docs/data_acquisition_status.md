# Data Acquisition Status

업데이트: 2026-06-14 KST

## 확보 완료

### KBO / STATIZ

기존 STATIZ 공모전 API 스냅샷을 프로젝트 raw 영역으로 복사했다.

- source: `/Users/jameshui/New project/tmp/live_delta_20260611_from_api_v1`
- destination: `data/raw/kbo/statiz/live_delta_20260611_from_api_v1`
- size: 약 34MB
- coverage: 2023-2026, 2026-06-11까지
- inventory: `outputs/tables/statiz_20260611_snapshot_inventory.csv`

주요 파일:

| file | rows | columns |
|---|---:|---:|
| `organized/games/games_schedule.csv` | 2,959 | 39 |
| `organized/games/games_boxscore_gameinfo.csv` | 2,366 | 41 |
| `organized/games/games_lineup.csv` | 55,190 | 18 |
| `organized/players/players_day_batting.csv` | 58,647 | 60 |
| `organized/players/players_day_pitching.csv` | 23,202 | 60 |
| `organized/players/players_roster_daily.csv` | 168,171 | 7 |
| `organized/players/players_season_basic_batting.csv` | 906 | 58 |
| `organized/players/players_season_basic_pitching.csv` | 899 | 58 |
| `organized/players/players_season_deepen_batting.csv` | 907 | 17 |
| `organized/players/players_season_deepen_pitching.csv` | 898 | 17 |
| `organized/players/players_season_fielding.csv` | 1,913 | 9 |

2026-06-11에 제공받은 STATIZ key/secret 조합으로 HMAC 인증을 확인했다. `gameSchedule` 요청이 정상 응답했고, 2026-06-11 일정에서 5경기 row가 감지되었다. 키 값은 문서와 저장소에 기록하지 않는다.

추가로 2026-06-11에 STATIZ 최신 보강 수집을 수행했다.

| dataset | scope | rows | output |
|---|---|---:|---|
| `playerDay` batting refetch | 2026 KBO roster/lineup players 514명 | 7,786 | `organized/players/players_day_batting_2026_refetched.csv` |
| `playerDay` pitching refetch | 2026 SSG pitcher pool 51명 | 310 | `organized/players/players_day_pitching_2026_ssg_refetched.csv` |
| `playerSituation` batting refetch | 2026 SSG 10 PA 이상 타자 21명, si=1-5 | 1,769 | `organized/player_situations/ssg_player_situation_batting_2026_refetched.csv` |
| `teamRecord` batting situations | 2026 KBO 27개 상황 context | 270 | `organized/team_records/team_record_batting_situations_2026_refetched.csv` |
| `teamRecord` pitching situations | 2026 KBO 27개 투수 상황 context | 250 | `organized/team_records/team_record_pitching_situations_2026_refetched.csv` |

분석 산출물:

- `outputs/tables/kbo_2026_team_situation_ranks.csv`
- `outputs/tables/ssg_2026_player_role_context.csv`
- `outputs/tables/ssg_2026_situation_role_splits.csv`
- `outputs/tables/ssg_2026_situation_count_class_splits.csv`
- `outputs/tables/ssg_2026_replacement_context_flags.csv`
- `outputs/tables/ssg_2026_player_situation_focus.csv`
- `outputs/tables/kbo_2026_team_pitching_situation_ranks.csv`
- `outputs/tables/kbo_2026_pitching_with_context.csv`
- `outputs/tables/kbo_2026_team_pitching_role_ranks.csv`
- `outputs/tables/ssg_2026_team_pitching_role_ranks.csv`
- `outputs/tables/ssg_2026_game_pitching_workload.csv`
- `outputs/tables/ssg_2026_pitcher_summary.csv`
- `outputs/tables/ssg_2026_import_slot_pitching_impact.csv`

2026-06-12에 KBO 외국인 선수 과거 성공/실패 라벨 v0.1을 구축했다.

| dataset | scope | rows | output |
|---|---|---:|---|
| KBO foreign-player season labels | 2017-2026 foreign-player season rows | 406 | `outputs/tables/kbo_foreign_player_season_labels_v0_1.csv` |
| KBO foreign-player label coverage | year-level coverage and confidence | 10 | `outputs/tables/kbo_foreign_label_coverage_v0_1.csv` |
| Label metric overview | row-count, target leakage, current-season withholding checks | 6 | `outputs/tables/kbo_foreign_label_metric_overview_v0_1.csv` |
| Historical backtest folds | 2022-2025 holdout fold design | 4 | `outputs/tables/kbo_foreign_label_backtest_folds_v0_1.csv` |

요약:

- total player-season rows: 406
- historical label-available rows: 353
- STATIZ outcome-attached rows: 128
- 2023-2025 STATIZ coverage: 128 of 129 rows matched; the unmatched row is a no-appearance injury-release case
- 2026 labels: intentionally withheld because the season is current

수집/검증 스크립트:

- `src/data/build_kbo_foreign_player_labels.py`
- `src/modeling/check_kbo_foreign_label_metrics.py`
- `docs/foreign_player_labeling_methodology_v0_1.md`

### Naver Search API

2026-06-11에 제공받은 Naver Developers client id/secret 조합으로 Search News API 인증을 확인했다. `SSG 외국인 선수` 검색 요청이 HTTP 200으로 정상 응답했고, 뉴스 검색 결과가 반환되었다. 키 값은 문서와 저장소에 기록하지 않는다.

2026-06-12에 투수/대체외국인 중심 쿼리로 뉴스 metadata corpus를 재수집했다.

| corpus | scope | rows | output |
|---|---|---:|---|
| SSG need news | hitter/offense/foreign-player discovery | 7,884 | `data/raw/articles/naver_news/ssg_need_news_metadata.csv` |
| SSG pitching news | foreign pitcher, starter, bullpen load, injury/depth discovery | 3,822 | `data/raw/articles/naver_news_pitching/ssg_need_news_metadata.csv` |

투수 기사 corpus에서 태그 기반 분석 산출물을 생성했다.

- `outputs/tables/ssg_pitching_news_relevance_labeled.csv`
- `outputs/tables/ssg_pitching_news_tag_summary.csv`
- `outputs/tables/ssg_pitching_news_name_summary.csv`
- `outputs/tables/ssg_pitching_news_query_summary.csv`

### MLB / Baseball Savant

`pybaseball.statcast`를 사용해 MLB Statcast pitch/play-level raw를 7일 단위로 다운로드했다.

- raw destination: `data/raw/mlb_milb/savant/statcast_mlb`
- processed destination: `data/processed/mlb_milb/savant`
- inventory: `outputs/tables/savant_statcast_inventory.csv`
- downloader: `src/data/download_savant_statcast.py`
- inventory/parquet builder: `src/data/build_savant_inventory.py`

| year | chunk_files | rows | columns | processed_file |
|---:|---:|---:|---:|---|
| 2023 | 27 | 720,684 | 119 | `data/processed/mlb_milb/savant/savant_statcast_2023.parquet` |
| 2024 | 27 | 710,631 | 119 | `data/processed/mlb_milb/savant/savant_statcast_2024.parquet` |
| 2025 | 27 | 711,897 | 119 | `data/processed/mlb_milb/savant/savant_statcast_2025.parquet` |
| 2026 | 12 | 296,322 | 119 | `data/processed/mlb_milb/savant/savant_statcast_2026.parquet` |

2026 data covers `2026-03-25` through `2026-06-11`, but the final chunk `2026-06-10` to `2026-06-11` returned 0 rows from the source at collection time. Up to `2026-06-09` was populated.

Savant pitch-level data에서 타자/투수 feature summary를 생성했다.

- hitter features: `outputs/tables/savant_hitter_feature_summary_2023_2026.csv`
- hitter screen: `outputs/tables/savant_hitter_message_screen_top.csv`
- pitcher features: `outputs/tables/savant_pitcher_feature_summary_2023_2026.csv`
- starter stabilizer screen: `outputs/tables/savant_pitcher_stabilizer_screen_top.csv`

2026-06-12에 MLB 공식 Stats API를 사용해 후보 가용성 1차 필터용 로스터 상태도 수집했다.

| dataset | rows | output |
|---|---:|---|
| MLB organization roster status | 8,181 | `outputs/tables/mlb_roster_status_20260612.csv` |
| MLB organization roster status latest alias | 8,181 | `outputs/tables/mlb_roster_status_latest.csv` |
| MLB roster raw JSON | - | `data/raw/mlb/roster_status/mlb_roster_status_raw_20260612.json` |

요약:

- 40-man flag: 1,345 rows
- active roster flag: 777 rows
- full organization roster flag: 8,181 rows
- non-active pitchers in MLB organizations: 4,278 rows

수집 스크립트:

- `src/data/collect_mlb_roster_status.py`

MLB 로스터 상태와 Savant 성과 요약을 결합해 가용성 1차 후보 풀도 생성했다.

| candidate pool | rows | first-pass gate pass | output |
|---|---:|---:|---|
| regular foreign pitcher | 1,009 | 4 | `outputs/tables/mlb_pitcher_availability_candidate_pool_v1.csv` |
| regular foreign hitter / outfield priority | 736 | 6 | `outputs/tables/mlb_outfielder_availability_candidate_pool_v1.csv` |

요약 output:

- `outputs/tables/candidate_pool_summary_v1.csv`

후보 풀 생성 스크립트:

- `src/features/build_candidate_pool_v1.py`

### NPB / CPBL Asian Market

2026-06-14에 NPB/CPBL 아시아 시장 1차 roster layer를 구축했고, NPB는 공식 2026 1군/팜 성적까지 확장했다.

| dataset | scope | rows | output |
|---|---|---:|---|
| NPB official roster | 2026 NPB 12개 구단 공식 영문 roster | 810 | `outputs/tables/npb_official_roster_2026_v1.csv` |
| CPBL official roster | 2026 CPBL 공식 roster | 168 | `outputs/tables/cpbl_official_roster_2026_v1.csv` |
| NPB+CPBL Asian market status | NPB/CPBL roster, nationality seed, 아시아쿼터 gate | 978 | `outputs/tables/asian_quota_market_status_v1.csv` |
| NPB official player stats | 2026 NPB 1군/팜 타격·투구 공식 성적 | 2,186 | `outputs/tables/npb_official_player_stats_2026_v1.csv` |
| NPB player market features | NPB official stats joined to roster/nationality seed and market role buckets | 2,186 | `outputs/tables/npb_player_market_features_2026_v1.csv` |
| NPB market depth summary | NPB league/level/stat type/role bucket depth | 24 | `outputs/tables/npb_market_depth_summary_2026_v1.csv` |
| NPB official stats source inventory | 12 teams x 4 official stat page audit | 48 | `outputs/tables/npb_official_stats_source_inventory_2026_v1.csv` |

NPB 공식 성적 수집 coverage:

| level | stat type | rows |
|---|---|---:|
| NPB first team | batting | 617 |
| NPB first team | pitching | 313 |
| NPB farm | batting | 835 |
| NPB farm | pitching | 421 |

수집/검증 스크립트:

- `src/data/collect_asian_market_rosters.py`
- `src/data/collect_npb_official_stats_2026.py`

요약:

- 2026 NPB 공식 1군/팜 성적 페이지 48개가 모두 정상 파싱되었다.
- NPB 성적 기반 시장 변수는 확보됐지만, 공식 NPB 페이지에는 salary, contract length, buyout, universal nationality, medical/news context, Korea-willingness가 없으므로 feasibility layer는 아직 미완성이다.
- NPB의 `*` 표시는 공식 페이지상 좌타자 표시이므로 외국인/가용성 flag로 쓰지 않는다.

### External Research / Articles

2026-06-12에 STATIZ 외부 자료를 메시지 발굴용으로 수집했다.

| source | type | scope | local output |
|---|---|---|---|
| Scientific Reports KBO ABS paper GitHub | public research result data | KBO 2021-2024 umpire/ABS zone model summaries | `data/external/kbo_abs_paper/result/*.csv` |
| Baseball Savant | MLB pitch/player public data | Thomas Hatch and starter-stabilizer profile comparison | `outputs/tables/external_hatch_savant_context.csv` |
| Naver Search News / web articles | article metadata and source links | SSG foreign pitcher, replacement, Asian quota, temporary replacement rule | `outputs/tables/external_message_candidates_v1.csv` |

분석 산출물:

- `outputs/tables/external_abs_zone_shift_summary.csv`
- `outputs/tables/external_hatch_savant_context.csv`
- `outputs/tables/external_message_candidates_v1.csv`
- `docs/external_message_discovery_v1.md`

2026-06-12에 논문/스카우팅/규정 자료를 후보평가용으로 보강했다.

| source | status | local output |
|---|---|---|
| KBO foreign-player labor-market inefficiency paper | full-text PDF secured | `data/external/literature/kbo_market_inefficiency_2022_kais.pdf` |
| KBO foreign-pitcher renewal ML paper | full-text PDF secured | `data/external/literature/kbo_foreign_pitcher_renewal_ml_2022_jkdi.pdf` |
| KBO foreign-player adaptation thesis | full-text PDF secured | `data/external/literature/kbo_foreign_player_adaptation_snu_thesis.pdf` |
| KBO ABS impact arXiv preprint | full-text PDF secured | `data/external/literature/kbo_abs_impact_arxiv_2024.pdf` |
| KBO ABS impact Scientific Reports article | full-text PDF secured | `data/external/literature/kbo_abs_impact_scientific_reports_2025.pdf` |
| Baseball America/FanGraphs scouting and projection references | web source secured | `outputs/tables/literature_source_inventory_v1.csv` |

감사/스키마 산출물:

- `outputs/tables/project_data_coverage_audit_v1.csv`
- `outputs/tables/literature_source_inventory_v1.csv`
- `data/schemas/candidate_scoring_schema_v1.csv`
- `docs/source_coverage_audit_v1.md`
- `outputs/tables/candidate_market_collection_plan_v1.csv`

## 아직 해야 할 수집

- MLB/MiLB 후보의 DFA, release, minor-league contract, option, salary, Korea-willingness status
- MiLB Statcast coverage audit
- FanGraphs MiLB/MLB leaderboard export 또는 대체 수집
- NPB salary/contract/buyout proxy, universal nationality verification, medical/news context, Korea-willingness
- ABL roster/stats and Asian market feasibility references
- 기사/인터뷰 full text corpus 및 인용 가능한 원문 링크 정리
- KBO/ABS pitch-location raw data의 팀/선수 단위 접근 가능성 확인
- 인천/문학 구장·날씨 데이터
- MLB/MiLB transaction, DFA, release, free-agent feed
- 2017-2022 KBO 외국인 선수의 full STATIZ/BRef/MyKBO outcome attachment
- 최신 KBO 규약 원문 PDF/docx의 외국인 선수 비용/교체 edge case 확인
- SSG 아시아쿼터 계약 세부사항의 공식 출처 확인
