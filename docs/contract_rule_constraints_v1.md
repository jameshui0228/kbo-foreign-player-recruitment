# Contract And Rule Constraints V1

Generated: 2026-06-12 KST

## Why This Exists

This project should not recommend a player who is too good to be realistic, too expensive to fit the rule environment, or unavailable in the relevant market window.

The practical target is not "best player." It is:

> the best mispriced player type SSG can actually acquire under KBO rules, money, roster timing, medical risk, and market availability.

## Confirmed Rule Inputs

Sources:

- KBO 2026 major rule page: `https://www.koreabaseball.com/Kbo/League/GameManage2026.aspx`
- KBO 2026 rule-change article mirrored on KBO site: `https://www.koreabaseball.com/MediaNews/News/KboPhoto/View.aspx?bdSe=520974`
- KBO 2024 rule-change release for replacement foreign player system: `https://www.koreabaseball.com/MediaNews/Notice/View.aspx?bdSe=9984`
- SSG official 2026 foreign-player contract releases:
  - `https://www.ssglanders.com/media/news/detail?idx=19829&page=`
  - `https://www.ssglanders.com/media/news/detail?idx=19834&page=`

## Hard Constraints To Encode

| constraint | current rule signal | project implication |
|---|---|---|
| Asian quota eligibility | BFA-country or Australian player; no non-Asian dual nationality; must have belonged to an Asian league in the prior or current year; max one player; any position | Asian quota search must begin with eligibility, not performance |
| Asian quota cost | new signing cost cap is 200k USD including salary, signing bonus, paid options, and transfer fee excluding tax; monthly cap signal is 20k USD | A realistic Asian quota player is likely blocked, rehabbing, undervalued, older, or role-limited |
| Asian quota roster effect | KBO page lists 29 registered and 28 active game players after 2026 change | Asian quota should be scored as a roster-option layer, not only as a normal foreign starter |
| Injury replacement foreign player | if a current foreign player needs at least six weeks of treatment, club can place him on rehab list and sign replacement without using replacement count until return | Replacement-player list must be ready before injury, because timing is part of value |
| Injury replacement cost | replacement foreign player cost is capped at 100k USD per month | Short-window readiness and price efficiency matter more than pure long-term upside |
| Current SSG regular foreign cost baseline | White 1.20m, Heredia 1.30m, Veneziano 0.85m from official releases | regular foreign-player replacement must model sunk cost, remaining cap room, and whether the removed player is released or rehab-listed |
| Current SSG Asian quota baseline | Takeda Shota reported at 0.20m in public coverage; needs official SSG page or KBO registration confirmation | Asian quota replacement should assume little or no price flexibility until official contract details are confirmed |

## Modeling Rule

Candidate scoring must run in this order:

1. Market bucket: regular foreign hitter, regular foreign pitcher, injury replacement, Asian quota, offseason watchlist.
2. Rule gate: nationality, prior/current league, slot, roster, registration, replacement eligibility.
3. Economic gate: total cost, monthly cost, transfer fee, option cost, buyout likelihood, sunk cost.
4. Availability gate: current contract, 40-man/option status, DFA/release likelihood, NPB/CPBL/ABL timing.
5. Baseball score: SSG fit, tool/process, KBO translation, failure risk, surplus value.

No player should enter the final shortlist without passing steps 1-4.

## SSG-Specific Consequence

SSG's 2026 regular foreign-player baseline is not cheap: the two confirmed re-signings plus Veneziano sum to 3.35m USD in announced total value before considering detailed cap treatment. Therefore the candidate search must avoid fantasy-level names and should focus on:

- players whose MLB path is blocked but whose KBO role is clean;
- players with one elite KBO-relevant carrying trait and tolerable weaknesses;
- players whose market label is unattractive but whose process data fits SSG;
- players with verified medicals and immediate availability;
- Asian quota candidates whose cost ceiling is the point of the strategy, not a footnote.

## Open Checks

- Confirm exact 2026 KBO foreign-player salary cap text from the latest downloadable KBO regulation file if available.
- Confirm current SSG Asian quota contract from an official SSG or KBO registration source.
- Confirm whether option payouts and transfer fees count differently for midseason replacement versus full replacement in the current rulebook.
- Build a player-level cost field rather than treating salary as static: remaining-season salary matters for midseason decisions.
