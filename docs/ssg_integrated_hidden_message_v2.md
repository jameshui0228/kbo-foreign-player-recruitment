# SSG Integrated Hidden Message v2

Generated: 2026-06-12 KST

## Current Best Thesis

The priority should move from "replacement foreign outfielder" to "replacement foreign starter" unless the roster rule/slot constraint makes a hitter the only actionable move.

Korean presentation wording:

> SSG의 진짜 문제는 단순히 방망이가 약하거나 불펜이 무너졌다는 것이 아니다. 이 팀은 경기를 길게 끌고 가야 득점권 강점이 살아나는 구조인데, 외국인 선발 슬롯이 오히려 경기를 너무 일찍 짧게 만들고 있다. 그래서 대체 외국인은 화려한 탈삼진형보다, 초반 실점과 볼넷/피홈런을 줄이고 5이닝 초반을 6이닝으로 바꾸는 로테이션 안정화형 선발이어야 한다.

Short version:

> SSG needs a load-bearing starter more than a generic power bat.

## Why This Is More SSG-Specific

This is not just "SSG pitching is bad." The role split says the burden is structurally located in the rotation and especially in the foreign/import pitcher slot.

- SSG starters: 4.55 IP/G, ERA 5.68, WHIP 1.60, OPS allowed .783.
- Starter ERA, WHIP, OPS allowed, IP/G, and outs/start all rank 10th among KBO teams.
- SSG bullpen: 4.25 IP/G, the highest workload in the league.
- Despite that workload, the bullpen ranks 3rd in WHIP and 2nd in OPS allowed.
- Therefore the hidden problem is not simply "bullpen quality." It is "starter runway failure creating bullpen tax."

Game-level split:

- Short starts under 5 IP: 26 of 61 games, 42.6%.
- SSG win rate after short starts: .308.
- SSG win rate after non-short starts: .514.
- Disaster starts: 20 of 61 games, 32.8%, win rate .250.
- Quality starts: 7 of 61 games, 11.5%, win rate .714.
- Short-start games force 5.36 bullpen IP on average; non-short games force 3.43 bullpen IP.

## Import Slot Inversion

The foreign/import starter slot is not absorbing scarcity; it is amplifying the scarcity.

| group | starts | IP/start | ERA | WHIP | OPS allowed |
|---|---:|---:|---:|---:|---:|
| Import-slot starters | 33 | 4.69 | 6.17 | 1.73 | .821 |
| Domestic starters | 28 | 4.38 | 5.06 | 1.44 | .731 |
| Domestic bullpen | 61 games | 4.25 IP/G | 5.10 | 1.52 | .736 |

This creates a sharper recruitment insight:

> SSG should not evaluate the replacement pitcher as a ceiling bet. The first screen should ask whether the pitcher can reliably remove one bullpen inning and one early traffic inning from the game script.

## The Game-State Problem

The situational table shows where the starter profile must help.

- Early innings 1-3: ERA 5.81, WHIP 1.64, OPS allowed .790; all rank 10th.
- Runners on base: ERA 9.75, WHIP 1.56, OPS allowed .800; all bottom-tier.
- RISP allowed: ERA 15.13, WHIP 1.78, OPS allowed .847; all rank 10th.
- Away games: ERA 5.80, WHIP 1.65; both rank 10th.
- Three-ball counts remain dangerous, especially 3B-1S and 3B-2S contexts.

This points toward a profile:

- fewer free baserunners, not only more strikeouts;
- HR suppression and barrel suppression;
- early-inning command;
- ability to survive runner-on-base/RISP states without a multi-run inning;
- enough workload history to reach 80-90 pitches.

## External Text Signal

The Naver Search News pitching corpus was recollected with 14 pitcher-focused SSG queries.

- Metadata articles collected: 3,822.
- Strategy-relevant article signals: 3,724.
- Tag counts among strategy signals:
  - starter/rotation: 2,527
  - run prevention: 1,311
  - replacement decision: 1,293
  - injury/depth: 1,165
  - foreign pitcher: 1,086
  - bullpen load: 795

This is not treated as a statistical truth by itself because the corpus is query-biased. It is useful because the external narrative is aligned with the quantitative pattern: foreign starter instability, rotation shortage, and bullpen burden appear together.

## Savant Translation

The Savant pitcher table was built from 2023-2026 pitch-level MLB data. The current score is for profile learning, not final candidate availability.

Among 2025-2026 starter-stabilizer eligible pitcher seasons:

| group | pitches/game | BB+HBP% | HR% | wOBA allowed | early 1-3 wOBA | RISP wOBA | hard-hit% | barrel% | 3-ball pitch% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Eligible median | 85.8 | 8.9% | 3.1% | .324 | .319 | .328 | 41.3% | 8.7% | 8.2% |
| Top 100 stabilizer median | 90.3 | 7.4% | 2.2% | .283 | .277 | .284 | 38.4% | 7.1% | 7.3% |

Practical first-pass filters:

- recent starter/opening workload: 80+ pitches per game or clear 20+ PA per game history;
- BB+HBP% preferably below 8%;
- HR% preferably near or below 2.5%;
- wOBA allowed and early-inning wOBA allowed clearly better than the eligible median;
- RISP/on-base damage suppression;
- hard-hit and barrel rates not inflated;
- low three-ball pitch rate.

## Hitter Thesis Is Still Useful, But Secondary

The hitter-side hidden message still has value if the actionable replacement slot is a hitter.

- SSG RISP OPS: .831, rank 1st.
- SSG runner-on-first OPS: .649, rank 10th.
- The RISP minus runner-on-first OPS gap is +.182, the largest in KBO 2026.
- The bottleneck is concentrated in OF/DH runner-on-first states.

So the hitter profile should not be a generic slugger. It should be a first-base traffic converter: OF/DH, RHP production, low GDP risk, two-strike survival, and gap/line-drive damage.

But the combined pitcher-plus-hitter read says:

> The hitter can improve how SSG converts traffic. The pitcher can change whether SSG gets enough stable innings for that traffic conversion to matter.

## Project Priority

1. Primary: replacement foreign starter, load-bearing and command/damage-control oriented.
2. Secondary: if the foreign hitter slot is the only realistic replacement path, target a first-base traffic converter rather than a pure power bat.
3. Asian quota angle: if available, prioritize pitcher depth with command/workload traits before chasing a redundant offensive archetype.

## Tables

- `outputs/tables/ssg_2026_team_pitching_role_ranks.csv`
- `outputs/tables/ssg_2026_game_pitching_workload.csv`
- `outputs/tables/ssg_2026_import_slot_pitching_impact.csv`
- `outputs/tables/ssg_2026_pitcher_summary.csv`
- `outputs/tables/kbo_2026_team_pitching_situation_ranks.csv`
- `outputs/tables/ssg_pitching_news_tag_summary.csv`
- `outputs/tables/ssg_pitching_news_name_summary.csv`
- `outputs/tables/savant_pitcher_feature_summary_2023_2026.csv`
- `outputs/tables/savant_pitcher_stabilizer_screen_top.csv`
- `outputs/tables/ssg_2026_runway_gap_by_team.csv`
- `outputs/tables/ssg_2026_role_runway_context.csv`
