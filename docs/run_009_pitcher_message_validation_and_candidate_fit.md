# Run 009 Pitcher Message Validation And Candidate Fit

Generated: 2026-06-12 KST

## Goal

Validate whether the run_008 pitcher-first message is strong enough to drive candidate ranking, then score MLB pitcher research leads against that message.

This run does not produce final recommendations. It produces a candidate research board that still requires current transaction, contract, medical, salary, and Korea-willingness verification.

Important correction:

The candidate names in this document are not a shortlist. They are a sandbox output used to confirm that the promoted SSG pitcher message can be translated into measurable candidate features. Final candidate search is frozen until the release gates in `docs/candidate_release_gates_v1.md` are satisfied.

## Message V0.2 Decision

The pitcher-first message is promoted.

> SSG should prioritize a traffic-command, load-bearing foreign starter: a pitcher who prevents innings from exploding after traffic and turns short-start games into repeatable 5-6 inning games.

All v0.2 validation criteria passed.

| criterion | value | threshold | status |
|---|---:|---|---|
| run_008 pitcher signal strength | 58.49 | >= 50 | pass |
| starter monthly stability | 3 bottom-three months | >= 2 | pass |
| short-start win-rate penalty | -20.7%p | <= -12%p | pass |
| disaster-start win-rate penalty | -26.2%p | <= -20%p | pass |
| severe context concentration | 8 contexts | >= 3 | pass |

## Why This Is Not Just A One-Month Pattern

SSG starter monthly ranks stayed poor after March.

| month | ERA | WHIP | OPS allowed | outs/start | ERA rank | WHIP rank | OPS allowed rank | outs/start rank |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 5.65 | 1.81 | .782 | 14.3 | 7 | 7 | 6 | 5 |
| 4 | 4.30 | 1.51 | .743 | 13.9 | 9 | 10 | 10 | 10 |
| 5 | 6.63 | 1.65 | .811 | 13.5 | 10 | 10 | 10 | 10 |
| 6 | 6.88 | 1.67 | .810 | 13.3 | 9 | 8 | 5 | 9 |

Starter summary:

- 4 months observed.
- 3 months had bottom-three core starter signals.
- Mean starter ERA rank: 8.75.
- Mean starter WHIP rank: 8.75.
- Mean starter outs/start rank: 8.5.
- Median starter outs/start: 13.67 outs, or about 4.56 innings.

## Game Impact

Short and damaging starts are materially tied to worse game outcomes.

| signal | games | win rate when signal happens | comparison win rate | delta | bullpen IP when signal happens |
|---|---:|---:|---:|---:|---:|
| starter short < 5 IP | 26 | .308 | .514 | -20.7%p | 5.36 |
| starter disaster | 20 | .250 | .512 | -26.2%p | 5.42 |
| starter ER >= 4 | 23 | .261 | .526 | -26.5%p | 4.93 |
| starter 5+ IP | 35 | .514 | .308 | +20.7%p | 3.43 |
| quality start | 7 | .714 | .389 | +32.5%p | 2.29 |

This is the strongest reason to keep the message pitcher-first. It connects the hidden weakness to wins and bullpen workload.

## Severe Contexts

The worst SSG pitching contexts are interpretable, not random.

| context | key rank signal |
|---|---|
| vs right orthodox | ERA, WHIP, OPS allowed all rank 10th |
| early 1-3 innings | ERA, WHIP, OPS allowed all rank 10th |
| RISP | ERA, WHIP, OPS allowed all rank 10th |
| away games | ERA rank 10th, WHIP rank 10th, OBP rank 10th |
| runner on base | ERA, WHIP, OPS allowed all rank 10th |
| 0 out | ERA rank 10th, OBP rank 10th |
| 2 out | ERA rank 10th, BB9 and HR9 rank 10th |

The candidate screen should therefore emphasize traffic command, early-inning stability, walk suppression, HR suppression, and repeatable starter workload.

## Candidate Fit Scoring

Candidate fit score was built from four model components:

| component | meaning |
|---|---|
| `traffic_command_score` | BB+HBP suppression, zone rate, RISP wOBA, first-pitch non-ball, three-ball avoidance |
| `load_bearing_score` | starter stabilizer score, 80+ pitch games, starter usage, recent sample |
| `damage_control_score_v2` | HR, barrel, hard-hit, wOBA, early-inning damage suppression |
| `availability_realism_score` | market access bucket, age, injury, active/40-man/economic gates |

## Sandbox Research Leads

These are not final recommendations. They are the first names worth manual verification.

| tier | player | fit score | main reason to inspect | verification need |
|---|---|---:|---|---|
| A | Dietrich Enns | 62.74 | best realistic fit blend; strong damage control and availability realism | verify 40-man option/access cost |
| B | Bailey Falter | 60.56 | strong load-bearing workload sample | verify 40-man option/access cost |
| B | Austin Gomber | 57.18 | workload plus traffic-command profile | verify 40-man option/access cost |
| B | Bryse Wilson | 51.35 | passes first gate, but weaker damage-control score | verify 40-man option/access cost |

Gate-review watchlist:

| player | fit score | why not first lead |
|---|---:|---|
| Tobias Myers | 65.52 | 40-man/not-active access and economic gate fail |
| Carlos Carrasco | 64.89 | DFA signal, but age gate fail |
| Jacob Lopez | 61.15 | 40-man/not-active access and economic gate fail |
| Brayan Bello | 60.58 | 40-man/not-active access and economic gate fail |
| Kyle Hart | 60.34 | 40-man/not-active access and economic gate fail |

Unavailable benchmark players were separated into `mlb_pitcher_ssg_fit_unavailable_benchmark_v0_1.csv`. These names help calibrate what a strong profile looks like, but they should not be treated as realistic targets.

## Output Tables

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_pitching_message_v0_2_monthly_role_ranks.csv` | 80 | monthly team-role ranks |
| `outputs/tables/ssg_pitching_message_v0_2_monthly_summary.csv` | 2 | SSG starter/bullpen stability summary |
| `outputs/tables/ssg_pitching_message_v0_2_game_impact.csv` | 7 | short-start and quality-start win impact |
| `outputs/tables/ssg_pitching_message_v0_2_context_validation.csv` | 25 | bad context concentration |
| `outputs/tables/ssg_pitching_message_v0_2_decision_table.csv` | 5 | message promotion decision |
| `outputs/tables/mlb_pitcher_ssg_fit_scores_v0_1.csv` | 1,009 | all MLB pitcher fit scores |
| `outputs/tables/mlb_pitcher_ssg_fit_top_research_leads_v0_1.csv` | 11 | realistic research leads |
| `outputs/tables/mlb_pitcher_ssg_fit_unavailable_benchmark_v0_1.csv` | 30 | unavailable benchmark profiles |
| `outputs/tables/mlb_pitcher_ssg_fit_summary_v0_1.csv` | 14 | candidate tiers by market bucket |

## Decision

Promote the pitcher message from v0.1 to v0.2.

Do not yet finalize a player. The next step is manual verification for the A/B leads:

1. current transaction status;
2. 40-man and option constraints;
3. contract/salary feasibility;
4. recent medical and velocity trend;
5. willingness or plausible path to Korea;
6. video/scouting check for ABS-zone command translation.
