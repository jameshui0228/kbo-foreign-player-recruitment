# External Message Discovery v1

Generated: 2026-06-12 KST

Scope: non-STATIZ evidence only, using papers, public research data, news/articles, Naver Search News metadata, and MLB Baseball Savant.

## Best New Message

The best breakthrough message from external data is not just "replace the foreign starter."

It is:

> SSG should build an ABS-native foreign pitcher screen. In the current KBO, "good command" can no longer mean reputation, catcher framing, or vague strike-throwing language. It has to mean measurable rule-book-zone strike creation: zone rate, first-pitch non-ball rate, low three-ball exposure, low BB+HBP%, and damage control when forced into the zone.

Korean presentation wording:

> SSG의 대체 외인투수 전략은 '150km', '빅리그 경력', '스트라이크를 잘 던진다' 같은 설명에서 멈추면 안 된다. KBO는 완전 ABS 리그이기 때문에, 후보의 커맨드는 평판이 아니라 룰북 존 안에서 실제로 스트라이크를 생산하는 능력으로 검증해야 한다. SSG가 찾아야 할 투수는 강한 공을 던지는 투수가 아니라, ABS가 봐도 스트라이크가 되는 공을 반복해서 던지고 3-ball 카운트와 장타 실투를 줄이는 투수다.

This is stronger than the prior message because it gives the project a distinctive data-analysis angle:

- It is not a generic "starter needed" claim.
- It uses the KBO-specific rule environment.
- It creates a concrete candidate-screening method.
- It can challenge official/press descriptions of a player rather than merely repeating them.

## Evidence Layer 1: KBO ABS Changed The Value Of Command

The Scientific Reports KBO ABS paper is the most important external source found so far.

The paper states that KBO became the first professional league to implement ABS in 2024 and analyzes 2,515 KBO games across multiple seasons. It reports that ABS creates a stricter, more consistent, more rule-book-like zone than human umpiring.

I also downloaded the authors' public result files from GitHub:

- `data/external/kbo_abs_paper/result/2021_umpire_params_and_intervals.csv`
- `data/external/kbo_abs_paper/result/2022_umpire_params_and_intervals.csv`
- `data/external/kbo_abs_paper/result/2023_umpire_params_and_intervals.csv`
- `data/external/kbo_abs_paper/result/2024_umpire_params_and_intervals.csv`
- `data/external/kbo_abs_paper/result/mlb_kbo.csv`

Key summary from the public result data:

| parameter | KBO 2023 | KBO 2024 | shift |
|---|---:|---:|---:|
| alpha | 0.898 | 0.890 | -0.9% |
| beta | 12.58 | 34.78 | +176.4% |
| r | 3.30 | 24.44 | +640.1% |
| x0 | 0.006 | 0.001 | closer to center |
| y0 | 2.511 | 2.527 | slightly higher |

Interpretation:

- `beta` rising sharply means the boundary became much stricter and clearer.
- `r` rising sharply means the zone became much more rectangular/rule-book-like.
- The zone became less forgiving to pitches that used to live in human-umpire ambiguity.

Recruitment translation:

- Do not overvalue "edge nibblers" unless their actual pitch locations enter the rule-book zone.
- Do not rely on catcher framing carryover.
- Value pitchers who can live in the zone without getting crushed.
- Value candidates who avoid 3-ball counts and keep HR/barrel rates down.

## Evidence Layer 2: The SSG News Narrative Already Points To This, But Needs Data Discipline

Recent articles frame SSG's problem as an ace/foreign-starter shortage.

Yonhap's June 4 article says SSG's post-13-game losing streak concern was finding a reliable ace starter. It notes Kim Kwang-hyun's shoulder surgery, foreign pitcher underperformance, low QS totals, Ginjiro's poor results, and early-control issues from domestic starters.

Yonhap's June 6 Hatch signing article emphasizes Hatch's Triple-A starter workload, NPB experience, ability to maintain around 150 km/h, stable mechanics, pitch mix, and immediate starter competitiveness.

Those are useful scouting claims, but the hidden analysis move is to verify them rather than accept them.

Using our local Savant pitcher table:

| group | zone rate | first-pitch non-ball | BB+HBP% | HR% | wOBA allowed | early 1-3 wOBA | RISP wOBA | 3-ball pitch% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Thomas Hatch 2025 MLB | 43.7% | 59.9% | 11.2% | 4.6% | .389 | .392 | .419 | 10.8% |
| Eligible 2025-2026 starter median | 49.6% | 61.9% | 8.9% | 3.1% | .324 | .319 | .328 | 8.2% |
| Top 100 stabilizer median | 50.5% | 63.4% | 7.4% | 2.2% | .283 | .277 | .284 | 7.3% |

This does not prove Hatch will fail in KBO. His Triple-A/NPB context, health, role, and sample size matter.

But it does show why the project message should be:

> We cannot scout SSG's replacement foreign pitcher by language like "efficient" or "strike thrower." We need an ABS-native command audit.

## Evidence Layer 3: Asian Quota Is An Option Slot, Not A Rotation Pillar

Korea Times reported that the 2026 Asian quota increases foreign-player capacity from three to four, allows one player from Asian Baseball Federation countries or Australia, and caps new-player financial commitment at $200,000.

This creates an important strategic distinction:

- A regular foreign pitcher slot can be a rotation pillar.
- An Asian quota slot is structurally a low-cost option/depth slot.

SSG's hidden roster-construction issue is that its 2026 injury/rotation crisis appears to have pushed Asian-quota and short-term replacement logic into a starter-pillar job.

Project message:

> SSG's mistake was not simply choosing the wrong Asian-quota player. It was asking the Asian-quota market to solve a full foreign-starter problem.

Recruitment translation:

- Asian quota: swingman, command-first depth, bullpen/starter bridge, or second-layer starter.
- Regular foreign replacement: workload-bearing starter.
- Do not mix the two jobs in the evaluation model.

## Evidence Layer 4: Temporary Replacement Rule Creates An Audition Market

Korea JoongAng Daily explains that the KBO short-term foreign replacement rule, introduced in 2024, lets clubs temporarily replace foreign players expected to miss more than six weeks, with the injured player placed on the rehabilitation list.

The article also notes precedent where temporary replacements later became full-time KBO options, such as Ryan Weiss.

This matters because SSG's process can be more innovative than "rank the best available player."

Project message:

> The replacement foreign-player market is now an option market. The club that wins is not the club that reacts fastest after injury, but the club that already has a pre-cleared, ABS-audited, role-specific audition pool.

Operational translation:

- Keep separate pools for regular foreign starter, Asian quota, and six-week injury replacement.
- Pre-grade visa feasibility, contract availability, recent workload, health, and pitch-shape translation.
- Track players who can be tested short-term and converted later.

## Candidate Message Ranking

| rank | message | score | why |
|---:|---|---:|---|
| 1 | ABS-native command screen | 14 | Most distinctive; strongly KBO-specific; directly testable with Savant and KBO ABS data |
| 2 | Asian quota optionality trap | 13 | Explains why SSG's roster construction may have misused the new rule |
| 3 | Replacement audition pipeline | 13 | Turns the project from player recommendation into process innovation |
| 4 | Nonlinear bullpen fatigue | 11 | Good support for starter priority, but less unique without internal workload data |
| 5 | Munhak summer damage control | 9 | Interesting, but needs weather/park-factor join before becoming a primary message |

## Recommendation

Use this as the next main project direction:

> SSG needs an ABS-native, workload-bearing foreign starter screen, and the club should separate three markets that are currently being blended together: regular foreign starter, Asian quota option, and six-week injury replacement audition.

This gives the project a stronger edge than "find a better pitcher" because it says the hidden inefficiency is in the evaluation frame itself.

## New Outputs

- `outputs/tables/external_abs_zone_shift_summary.csv`
- `outputs/tables/external_hatch_savant_context.csv`
- `outputs/tables/external_message_candidates_v1.csv`

## Key Sources

- Scientific Reports: `https://www.nature.com/articles/s41598-025-28142-y`
- ABS paper GitHub data: `https://github.com/eis-lab/where-do-the-robot-umpires-see`
- Baseball Savant Thomas Hatch: `https://baseballsavant.mlb.com/savant-player/thomas-hatch-641672`
- Korea Times Asian quota: `https://www.koreatimes.co.kr/sports/20250123/kbo-to-introduce-asia-quota-system-in-2026`
- Korea JoongAng Daily replacement rule: `https://www.koreajoongangdaily.com/sports/kbo-clubs-hold-steady-on-foreign-players-for-now/12000017`
- Yonhap SSG foreign pitcher concerns: `https://www.yna.co.kr/view/AKR20260604172400007`
- Yonhap Hatch signing: `https://www.yna.co.kr/view/AKR20260606021300007`
