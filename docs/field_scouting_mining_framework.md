# Field-Style Scouting Mining Framework

Generated: 2026-06-12 KST

## Principle

The project should imitate how a real club would work, not how a public stat ranking article would work.

That means the workflow is:

1. Diagnose SSG's roster problem.
2. Translate that problem into scouting roles.
3. Use data to find player traits that fit those roles.
4. Cross-check with scouting language: tools, role, body, makeup, health, adaptation, availability.
5. Eliminate players who look good statistically but fail field constraints.

The candidate search should not mean "find the best player."

It should mean:

- find a player type that solves a specific SSG problem;
- make sure that type is undervalued by the market;
- test whether the type translates to KBO;
- remove players with known failure patterns;
- pass money, roster, rule, medical, and timing constraints before final scoring.

## The Five Mining Tracks

We will use five tracks, matching the user's selected scope.

| track | field-scouting equivalent | data-mining question | output |
|---|---|---|---|
| 1. SSG-only weakness mining | advance scouting / pro scouting need report | What is uniquely broken in SSG's game script? | message evidence cards |
| 2. Market inefficiency mining | undervalued player search | Which player shapes are ignored by surface stats or market labels? | undervalued archetypes |
| 3. KBO translation mining | league/role translation | Which MLB/AAA/NPB/CPBL traits actually translate to KBO? | translation factors |
| 4. Failure pattern mining | risk/removal board | What did failed foreign players have in common? | red-flag filters |
| 6. Availability mining | area scout / front office feasibility check | Who can actually be acquired under money, roster, visa, and rule constraints? | feasible shortlist |

Money and rules are a hard gate inside track 6, not a cosmetic final note. A candidate who fails the contract/regulation gate should be removed before baseball scoring.

## What We Borrow From Scouts

Public scouting references consistently use the 20-80 language, but real reports are not only numbers.

For hitters:

- hit tool: bat control, contact consistency, pitch recognition, adjustment ability;
- game power vs raw power;
- run, field, arm, position fit;
- swing decisions and chase;
- batted-ball quality and whether the contact plays in games.

For pitchers:

- fastball quality is velocity plus life, command, and role context;
- secondary pitch grades depend on bite, shape, and miss quality;
- starter/reliever role changes velocity expectations;
- delivery, arm action, body, durability, and pitch mix matter;
- modern pitch models separate stuff from location/command.

For KBO foreign players:

- adaptation is not soft background noise. It can affect performance and re-signing.
- internal adaptation factors such as teammates, team environment, baseball culture, trust, ball, field condition, and role are part of the risk model.
- a player with better tools but poor adaptation fit can be a worse acquisition than a lower-ceiling player with stable role/adaptation indicators.

## How Each Track Becomes Data

### 1. SSG-Only Weakness Mining

Inputs:

- STATIZ team/player situations.
- SSG role splits.
- SSG game-level pitching workload.
- Naver article metadata for external corroboration.

Mining:

- rank extremes: 1st and 10th simultaneously;
- gap extremes: large difference between adjacent game states;
- role concentration: team average hides a position or slot collapse;
- time instability: monthly or pre/post injury shifts;
- state dependency: count/base/out/score-specific weakness.

Current evidence:

- SSG RISP OPS rank 1 but runner-on-first OPS rank 10.
- SSG starters rank 10th in core stability metrics while bullpen carries league-high workload.
- Import-slot starters underperform domestic starters.

### 2. Market Inefficiency Mining

Inputs:

- MLB/AAA Savant features.
- FanGraphs and Baseball-Reference leaderboards.
- public scouting/tool grades when available.
- transaction/roster status.

Mining:

- players whose surface line is mediocre but role-specific traits fit SSG;
- pitchers with command/damage suppression hidden behind weak ERA/team context;
- hitters with lower HR totals but better runner-transition traits;
- players blocked in MLB but with KBO-relevant role fit;
- players undervalued because they are swingmen rather than clean starters.

Output:

- "cheap but useful for this exact SSG problem" archetypes.

### 3. KBO Translation Mining

Inputs:

- historical KBO foreign-player outcomes.
- pre-KBO MLB/MiLB/NPB/CPBL stats.
- projection methods: weighted recent performance, regression to mean, age adjustment, league/park adjustment.
- ABS environment data.

Mining:

- which pre-KBO features separate re-sign/success from failure;
- which MLB/AAA features are sticky enough to trust;
- whether stuff, command, batted-ball quality, or role history translate best;
- whether KBO ABS makes location/zone command more important than old scouting reports suggest.

Output:

- slot-specific translation multipliers and risk flags.

### 4. Failure Pattern Mining

Inputs:

- failed KBO foreign-player cases.
- injury/role-change/news data.
- pre-arrival stats.
- adaptation literature.

Mining:

- players with strong surface stats but poor workload stability;
- pitchers with strikeout stuff but high three-ball/BB/HR exposure;
- hitters with raw power but no swing-decision/contact adjustability;
- players whose transition/adaptation indicators are negative;
- players signed for a role they had not recently performed.

Output:

- hard elimination filters and caution labels.

### 6. Availability Mining

Inputs:

- 40-man roster / MLB option / DFA / free agency.
- NPB/CPBL/ABL contract status.
- Asian quota rule constraints.
- salary/buyout/visa timing.
- injury status.

Mining:

- available now vs available offseason;
- realistic salary band;
- replacement-rule eligible;
- Asian quota eligibility;
- player not blocked by long-term major-league role;
- team control and buyout feasibility.

Output:

- feasible shortlist, not dream list.

## Scoring Model Shape

Every candidate first passes hard gates:

| hard gate | meaning |
|---|---|
| regulation gate | foreign-player slot, Asian quota eligibility, replacement-player status, roster timing |
| economic gate | salary, option, transfer fee, buyout, sunk cost, remaining cap room |
| availability gate | current contract, 40-man/option status, release/DFA likelihood, NPB/CPBL/ABL status |
| medical gate | recent injury, failed medical risk, workload interruption |
| role gate | can perform the role SSG is actually buying |

Only gate-pass candidates should receive the five baseball scores:

| score | meaning |
|---|---|
| SSG fit score | solves the mined SSG problem |
| tool/process score | scouting-grade proxy: hit/power/run/field/arm or stuff/location/command/workload |
| translation score | likelihood that prior-league performance carries to KBO |
| failure-risk score | injury, role mismatch, adaptation, volatility |
| surplus-value score | expected value relative to contract and acquisition cost |

Final score should not be a simple average. For example:

- foreign hitter: SSG fit and translation are weighted high.
- foreign pitcher: workload, ABS-command, and failure-risk are weighted high.
- Asian quota: economic gate, eligibility, and role flexibility are weighted high because the price ceiling is tight.
- replacement foreign player: speed, medical clarity, and short-window readiness are weighted high.

## Immediate Next Experiment

Run `run_002_field_method_source_map`:

1. Create a source map of papers/scouting references.
2. Translate each reference into measurable features.
3. Expand `feature_ideas.csv` with field-scouting columns.
4. Define candidate-score schemas before collecting candidates.

Then run `run_003_contract_rule_gate`:

1. Encode KBO foreign-player, replacement-player, and Asian quota rules.
2. Build a current SSG foreign-player cost baseline.
3. Add a hard gate before candidate scoring.
4. Split the shortlist into realistic markets: regular foreign player, injury replacement, Asian quota, offseason watchlist.
