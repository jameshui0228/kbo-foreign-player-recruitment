# SSG 2026 Hidden Context Findings

Generated: 2026-06-11 KST

## Data Status

- The previous STATIZ `players_day_batting.csv` covered only 30 SSG games in 2026.
- Refetched 2026 `playerDay` from the STATIZ API for 514 roster/lineup players.
- New file: `data/raw/kbo/statiz/live_delta_20260611_from_api_v1/organized/players/players_day_batting_2026_refetched.csv`
- Refetched 2026 file contains 7,786 batting rows across 10 teams and 310 games.
- Context analysis filters to completed 2026 regular-season games through 2026-06-10. The refetched raw file can include 2026-06-11 player rows, but those are not used in completed-game context ranks.
- Added current 2026 STATIZ `playerSituation` for 21 SSG batters with at least 10 PA: 105 API calls, 1,769 normalized situation rows.
- Added current 2026 STATIZ `teamRecord` situation ranks: 27 contexts, 270 team-context rows.
- New situation files:
  - `data/raw/kbo/statiz/live_delta_20260611_from_api_v1/organized/player_situations/ssg_player_situation_batting_2026_refetched.csv`
  - `outputs/tables/ssg_2026_situation_role_splits.csv`
  - `outputs/tables/ssg_2026_situation_count_class_splits.csv`
  - `outputs/tables/ssg_2026_replacement_context_flags.csv`
  - `outputs/tables/ssg_2026_player_situation_focus.csv`
  - `outputs/tables/kbo_2026_team_situation_ranks.csv`

Note: `playerSituation` is player-level cumulative context data, not position-at-PA-level data. The analysis classifies each SSG hitter by actual 2026 daily PA usage first, then attaches his cumulative situation splits.

## Stronger Message Candidates

### 0. The most SSG-specific message: the offense stalls before scoring position.

SSG is not a poor RISP team. It is the opposite:

- Team RISP OPS: .831, rank 1st.
- Team RISP OBP: .392, rank 1st.
- Team runner-on-first OPS: .649, rank 10th.
- Team runner-on-first OBP: .304, rank 10th.
- RISP minus runner-on-first OPS gap: +.182, the largest gap in the league.

Implication: the hidden need is not a generic "clutch hitter." SSG needs a hitter who converts first-base traffic into scoring-position pressure. For a replacement foreign OF/DH, that means runner-on-first advancement, low GDP risk, RHP contact quality, and two-strike survival matter as much as raw home-run power.

### 1. The outfield problem is not the bottom of the lineup. It is the high-leverage outfield roles.

SSG 2026 OF overall is not a simple "no power" group:

- OF overall: HR rank 3, ISO rank 4, but OBP rank 9 and OPS rank 8.
- OF 1-2 lineup role: 103 PA, .243 OBP, .606 OPS, BB% 1.9%; OBP, OPS, and BB% all rank 10th.
- OF 3-5 lineup role: 285 PA, .693 OPS, .359 SLG, .118 ISO; OPS and SLG rank 10th, ISO rank 9th.
- OF 6-9 lineup role: 405 PA, .751 OPS, 12 HR; PA, HR, R, RBI all rank 1st and OPS ranks 4th.

Implication: the hidden need is not "any productive outfielder." SSG needs an outfielder who can survive the top or middle lineup job. The lower-lineup OF production is already doing more than expected.

### 2. The sharpest matchup crack is against right-handed starters.

Against opponent right-handed starters:

- OF 1-2: 83 PA, .205 OBP, .526 OPS, 1 BB; OBP, OPS, and BB% rank 10th.
- OF 3-5: 187 PA, .294 OBP, .301 SLG, .595 OPS, .084 ISO; OBP, SLG, OPS, and ISO all rank 10th.

Against opponent left-handed starters:

- OF 3-5: 82 PA, .463 OBP, .585 SLG, 1.048 OPS; OPS/OBP/SLG rank 2nd.

Implication: the replacement profile should not be defined only by handedness label. The priority is a hitter whose damage and plate discipline hold against RHP, because the current high-leverage OF roles collapse there.

### 3. DH is a separate roster leak, but the shape is contact/damage failure despite walks.

2026 SSG DH:

- 263 PA, .185 AVG, .323 OBP, .310 SLG, .633 OPS.
- AVG rank 10, SLG rank 10, OPS rank 9, K% rank 10.
- BB% ranks 2nd.

Implication: the DH hole is not "no patience." It is a walk-heavy, strikeout-heavy profile where contact quality and slug translation fail. A foreign OF who can also cover DH would solve two roster pressures at once.

### 4. Humid-game and May signals point to durability/context sensitivity, not just talent level.

SSG OF in humid games:

- 143 PA, .254 OBP, .277 SLG, .530 OPS, .085 ISO.
- OBP and OPS rank 9th; BB% rank 9th.

Month x humidity check:

- May humid games: 107 PA, .224 OBP, .265 SLG, .490 OPS.
- June normal-humidity games: 63 PA, 1.056 OPS.

Implication: this is not yet a causal weather claim. But it is a useful screen: prioritize candidates whose swing decisions and contact quality do not disappear under fatigue, heat/humidity, travel, or schedule stress.

### 5. Team results are highly sensitive to OF run conversion.

Game-level SSG outcomes by OF RBI bucket:

- OF 0 RBI: 19 games, .263 win%, 3.11 team runs/game.
- OF 1-2 RBI: 26 games, .385 win%, 4.35 team runs/game.
- OF 3+ RBI: 16 games, .688 win%, 8.94 team runs/game.

This is descriptive, not causal. Still, it shows why the target role matters: when the OF does not convert runners, the whole scoring environment collapses.

### 6. The newest situation data says the hidden issue is not "SSG cannot hit with runners on."

Team-level 2026 STATIZ `teamRecord` says SSG is actually excellent in scoring position:

- SSG team RISP: .285 AVG / .392 OBP / .439 SLG / .831 OPS.
- RISP ranks: OPS 1st, OBP 1st, BB% 1st.

But the player-role split shows this strength is not distributed evenly:

- IF/C core in RISP: .430 OBP, .905 OPS, .340 RBI/PA.
- High-leverage OF usage in RISP: .367 OBP, .879 OPS, .494 RBI/PA.
- Lower/mixed OF usage in RISP: .324 OBP, .675 OPS, .261 RBI/PA.

Implication: do not pitch the project as "SSG needs clutch hitting." The better message is that SSG already has a team RISP strength, but the strength is concentrated in IF/C and one high-leverage OF bat. The replacement target should widen that run-conversion base into the rest of the OF/DH allocation.

### 7. Close-game plate quality is a sharper hidden signal than generic RISP.

The largest role gaps appear in tied and one-run contexts:

- Tied game:
  - IF/C core: .389 OBP, .864 OPS.
  - High-leverage OF usage: .247 OBP, .575 OPS.
  - Lower/mixed OF usage: .345 OBP, .682 OPS.
  - DH bridge: .250 OBP, .420 OPS.
- Within one run:
  - IF/C core: .372 OBP, .823 OPS.
  - High-leverage OF usage: .300 OBP, .693 OPS.
  - Lower/mixed OF usage: .330 OBP, .680 OPS.
  - DH bridge: .301 OBP, .532 OPS.

Implication: "late-game" alone is too broad; the screen should focus on plate quality when game state is still tight. This points toward candidates with RHP production, chase control, and two-strike contact stability rather than only raw exit velocity.

### 8. Two-strike survival is a real OF/DH filter, even though the team looks fine overall.

Team-level STATIZ count ranks do not scream a team-wide two-strike problem:

- SSG team 0B-2S OPS: .445, rank 2nd.
- SSG team 2B-2S OPS: .567, rank 1st.

But replacement-relevant role segments are much weaker:

- Two-strike count class:
  - IF/C core: .300 OBP, .632 OPS, 34.8% K%.
  - High-leverage OF usage: .221 OBP, .466 OPS, 41.6% K%.
  - Lower/mixed OF usage: .282 OBP, .573 OPS, 33.6% K%.
  - DH bridge: .277 OBP, .459 OPS, 51.5% K%.
- Specific 1B-2S bucket:
  - High-leverage OF usage: .143 OBP, .355 OPS.
  - Lower/mixed OF usage: .161 OBP, .391 OPS.
  - DH bridge: .184 OBP, .447 OPS.

Implication: the candidate screen needs a "two-strike damage/survival" component. This is a better hidden requirement than simply "low strikeout rate" because it ties the flaw to the exact contexts where the current OF/DH allocation thins out.

### 9. Against RHP, the team average hides a role-specific shortage.

SSG team vs RHP is around middle of the league:

- Team vs RHP: .338 OBP, .410 SLG, .748 OPS.
- OPS rank 5th, SLG rank 4th, OBP rank 7th.

Role-level splits are more revealing:

- IF/C core vs RHP: .365 OBP, .468 SLG, .833 OPS.
- High-leverage OF usage vs RHP: .294 OBP, .395 SLG, .688 OPS.
- Lower/mixed OF usage vs RHP: .322 OBP, .330 SLG, .653 OPS.
- DH bridge vs RHP: .309 OBP, .321 SLG, .630 OPS, 33.3% K%.

Implication: the replacement foreign hitter should be evaluated first as a right-handed-pitching solution, not as a generic "OF bat." The target can be left-handed or right-handed, but the required skill is RHP OBP plus damage in close-game and two-strike states.

## Working Recruitment Message

SSG does not simply need "more outfield power." The 2026 data points to a narrower and more interesting need:

> SSG already owns team-level RISP strength, but the offense leaks value before runners become true scoring-position chances. A replacement foreign outfielder should be a first-base traffic converter: an OF/DH bat who can handle RHP, tied/one-run games, and two-strike counts while turning runner-on-first states into scoring-position pressure.

## Candidate Screen Translation

For MLB/Savant candidate filtering, prioritize:

- vs RHP: xwOBA, xSLG, hard-hit/Barrel, chase, whiff, K-BB.
- role fit: corner OF plus DH tolerance, not only defensive OF label.
- contact floor: avoid profiles that depend only on walks with high strikeout and low in-play damage.
- two-strike survival: 0-2/1-2/2-2 xwOBA, K%, whiff, foul/contact ability, and in-play damage.
- close-game stability: proxy with leverage index, score differential, late-and-close, and RHP sub-splits where available.
- context stability: month-to-month consistency, travel/park translation, and platoon split risk.
- lineup translation: top/middle order skill set, not only lower-lineup power.

## Files Created Or Updated

- `src/data/collect_statiz_2026_player_day.py`
- `src/data/collect_statiz_2026_ssg_player_situation.py`
- `src/data/collect_statiz_2026_team_situation.py`
- `src/features/build_ssg_context_signals.py`
- `src/features/build_ssg_bottleneck_tables.py`
- `src/features/build_ssg_advanced_context_tables.py`
- `src/features/build_ssg_situation_context_tables.py`
- `outputs/tables/ssg_2026_narrative_context_candidates.csv`
- `outputs/tables/ssg_2026_of_role_by_opponent_starter_hand.csv`
- `outputs/tables/ssg_2026_of_hitter_hand_role_splits.csv`
- `outputs/tables/ssg_2026_of_humidity_month_splits.csv`
- `outputs/tables/ssg_2026_team_result_by_of_rbi_bucket.csv`
- `outputs/tables/ssg_2026_situation_role_splits.csv`
- `outputs/tables/ssg_2026_situation_count_class_splits.csv`
- `outputs/tables/ssg_2026_replacement_context_flags.csv`
- `outputs/tables/ssg_2026_player_situation_focus.csv`
- `outputs/tables/kbo_2026_team_situation_ranks.csv`
