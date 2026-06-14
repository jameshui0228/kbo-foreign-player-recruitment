# Source Coverage Audit V1

Generated: 2026-06-12 KST

## Direct Answer

The project has enough data to begin the full mining workflow, but it is not yet fair to say every related paper and every candidate-market dataset is fully secured.

What is solid:

- KBO/STATIZ SSG context data.
- MLB Baseball Savant pitch/play data for 2023-2026.
- MLB official roster status for 40-man, active, and full organization rosters.
- Naver article metadata corpus for SSG needs and pitching/depth narratives.
- KBO ABS public research result data.
- Core KBO foreign-player labor-market, foreign-pitcher renewal, adaptation, ABS, scouting, and projection references.
- KBO/SSG rule and contract constraint table for first-pass hard gates.

What is still incomplete:

- Full-text article corpus, not only metadata.
- MLB/MiLB roster, 40-man, options, DFA, release, and salary/contract status.
- MLB/MiLB transaction, DFA, release, and free-agent status.
- Complete MiLB Statcast or minor-league batted-ball/pitch-model data.
- NPB/NPB Farm, CPBL, ABL performance and availability data for Asian quota.
- Exact latest downloadable KBO regulation text for all foreign-player cap edge cases.
- Official SSG/KBO confirmation for the current Asian quota contract details.
- Paid/full-text literature that may be needed for final presentation-level citations.

## Data Readiness By Workstream

| workstream | readiness | reason |
|---|---|---|
| SSG-only weakness mining | high | STATIZ 2026 team/player/situation/context tables already exist |
| market inefficiency mining | medium | Savant features and MLB roster status exist, but transactions/salary/options are not yet complete |
| KBO translation mining | medium | ABS, STATIZ, and KBO foreign-pitcher papers exist; historical transfer labels need building |
| failure pattern mining | medium-low | literature and articles exist; KBO historical foreign failure dataset still needs construction |
| availability mining | medium | rules, SSG cost baseline, and MLB roster status exist; transaction/salary/Asian-market data still missing |
| field-style scouting cards | medium | 20-80 and process sources exist; candidate-level tool proxies need schema implementation |

## Practical Decision

Proceed with the full workflow, but separate two layers:

1. Evidence-mining layer: ready now.
2. Candidate-finalization layer: blocked until availability, contract, and market-status data are filled.

That means the next correct action is not naming final candidates. It is building the candidate scoring table and then collecting candidate-market data by bucket.

## Next Data Collection Priority

1. MLB/AAA/AA candidate availability:
   - current organization;
   - 40-man status;
   - option status;
   - minor-league contract / release / DFA status;
   - recent MLB playing-time block.
2. Asian quota market:
   - NPB 1군/2군 free agents and releases;
   - CPBL and ABL eligible players;
   - nationality and prior/current Asian league qualification;
   - expected cost under 200k USD.
3. Historical KBO foreign-player labels:
   - pre-KBO stats;
   - KBO first-year outcomes;
   - renewal/release/replacement labels;
   - injury/adaptation article signals.
4. Full-text article extraction:
   - interviews;
   - scouting comments;
   - medical status;
   - manager/front-office quotes.
