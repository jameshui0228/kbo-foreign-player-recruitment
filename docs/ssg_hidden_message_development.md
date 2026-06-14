# SSG Hidden Message Development

Generated: 2026-06-12 KST

## Best Current Message

SSG does not need a generic "clutch hitter." The hidden 2026 message is sharper:

> SSG is already a league-best RISP team, but it has the league's biggest gap between "runner on first" and "runner in scoring position." The replacement foreign outfielder should be a runway bat: a hitter who turns first-base traffic into scoring-position pressure before the inning reaches a pure clutch/RBI state.

Korean presentation wording:

> SSG의 문제는 득점권 해결사가 없다는 것이 아니라, 1루 주자를 득점권으로 보내는 공격 경로가 외야/DH에서 끊긴다는 것이다. 그래서 필요한 대체 외인은 홈런형 거포가 아니라, 우완 상대와 접전 상황에서 1루 주자를 진루/장타/출루로 다음 단계에 올려놓는 OF/DH 브릿지형 타자다.

## Why This Is More SSG-Specific

Team-level context creates a strange contradiction:

- SSG RISP OPS: .831, rank 1st.
- SSG RISP OBP: .392, rank 1st.
- SSG runner-on-first OPS: .649, rank 10th.
- SSG runner-on-first OBP: .304, rank 10th.
- SSG has the league's largest RISP minus runner-on-first OPS gap: +.182.

This is not a generic "poor run production" story. It says SSG is strong once the offense reaches a true scoring-position state, but weak in the transition state that creates that scoring-position pressure.

## Where The Bottleneck Sits

The internal role split points to OF/DH, not the whole lineup.

Runner on first:

- IF/C core: .333 OBP, .424 SLG, .757 OPS.
- High-leverage OF usage: .250 OBP, .133 SLG, .383 OPS, 52 PA, 0 RBI.
- Lower/mixed OF usage: .293 OBP, .344 SLG, .637 OPS.
- DH bridge: .255 OBP, .208 SLG, .463 OPS.

Less than two outs, runner on first:

- IF/C core: .399 OBP, .545 SLG, .944 OPS.
- High-leverage OF usage: .220 OBP, .163 SLG, .384 OPS, 6 GDP in 58 PA.
- Lower/mixed OF usage: .309 OBP, .396 SLG, .705 OPS, 11 GDP in 111 PA.
- DH bridge: .333 OBP, .488 SLG, .821 OPS, but high K%.

The IF/C core can advance or punish these states. The OF/DH allocation is where the runway becomes unstable.

## Recruitment Translation

The target profile should be framed as a "runway converter," not just a "power bat."

Candidate filters:

- vs RHP production: OBP plus gap/damage, not only HR totals.
- Runner-on-first skill: low GDP risk, enough contact quality to avoid dead grounders, line-drive/gap contact.
- Two-strike survival: ability to keep PA alive and avoid empty strikeouts in transition states.
- Close-game plate quality: tied/one-run situations where one baserunner advancement changes the inning.
- OF/DH fit: corner OF enough to take real outfield PA, DH acceptable as secondary usage.

Savant/MLB data translation:

- Base-state splits from pitch-level Statcast: on_1b=present, on_2b/on_3b empty, outs_when_up 0 or 1.
- Events: GDP, strikeout, walk/HBP, extra-base hits, hard-hit balls, barrels.
- Contact shape: ground-ball rate, line-drive proxy, launch angle band, opposite/center field damage.
- RHP split: xwOBA, xSLG, Barrel%, Chase%, Whiff%, K-BB%.

## Message Hierarchy For The Project

1. Primary message: SSG needs a first-base traffic converter, not a generic clutch hitter.
2. Supporting message: The team RISP strength is real but concentrated; the replacement should spread it to OF/DH allocation.
3. Candidate thesis: prioritize an OF/DH bat whose RHP, two-strike, and runner-on-first profile survives translation to KBO.

## Tables

- `outputs/tables/ssg_2026_runway_gap_by_team.csv`
- `outputs/tables/ssg_2026_role_runway_context.csv`
- `outputs/tables/ssg_2026_situation_role_splits.csv`
- `outputs/tables/ssg_2026_player_situation_focus.csv`
