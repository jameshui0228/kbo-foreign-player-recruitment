# Run 017 SSG Layer 1 Presentation Bridge

Date: 2026-06-14 KST

Layer focus: 1. SSG hidden weakness mining only.

Candidate policy: locked. This run does not recommend or shortlist players.

## Purpose

Run 017 does not create a new SSG hidden-weakness message. It turns the Run 016 message into a bridge that can survive presentation questions and flow into candidate scoring.

The goal is to connect four things:

- what a general audience should understand;
- why the message is not the obvious "SSG needs more outfield power" claim;
- which objections a professor or evaluator may raise;
- how the message becomes player-level features for the foreign hitter, foreign pitcher, and Asian quota slots.

## New Data Products

| output | rows | purpose |
|---|---:|---|
| `outputs/tables/ssg_layer1_plain_language_story_v4.csv` | 5 | General-public, presentation, professor, scout, and modeling-team versions of the message |
| `outputs/tables/ssg_layer1_objection_response_v4.csv` | 5 | Objection-response table for likely presentation challenges |
| `outputs/tables/ssg_layer1_candidate_feature_blueprint_v4.csv` | 10 | Candidate feature blueprint across foreign hitter, foreign pitcher, and Asian quota slots |
| `outputs/tables/ssg_layer1_evidence_to_message_trace_v4.csv` | 9 | Trace table from evidence source to message component and decision use |
| `outputs/tables/ssg_layer1_freeze_checklist_v4.csv` | 8 | Remaining checks before final Layer 1 freeze |

## Final Plain-Language Message

SSG's problem is not simply that the outfield lacks home runs.

The sharper message is:

> Against right-handed opponent starters, when SSG's OF/DH group cannot keep the inning alive and run-killing outs or extra-out damage appear, the team loses its comeback path.

Korean presentation wording:

> SSG의 문제는 외야 홈런 부족이 아니라 경기 복구 루트의 잠김이다. 상대 우투 선발에게 외야와 지명타자 쪽에서 출루와 타점 전환이 막히고, 병살/도루자 같은 공격 단절이나 비자책 실점이 겹치면 SSG는 따라갈 길이 급격히 사라진다.

## Why This Is Not A Generic Power Claim

The negative controls are the key defense:

| control | win% | avg run diff | interpretation |
|---|---:|---:|---|
| OF HR zero only | .405 | -1.29 | Too broad to explain the hidden weakness |
| OF RBI < 3 only | .333 | -2.04 | Directional, but still much weaker than the promoted interaction rules |

The promoted interaction rules are much sharper:

| rule | games | win% | avg run diff | decision |
|---|---:|---:|---:|---|
| RHP low OF conversion run trade | 20 | .100 | -5.10 | promote core |
| RHP OF/DH run-kill | 9 | .000 | -5.11 | promote core |
| Extra-out high OF void | 8 | .000 | -4.50 | promote core |
| Top-opponent short start OF void | 6 | .000 | -5.83 | support only |

Interpretation: if we only say "outfield power," the message is too easy and not very distinctive. The data says SSG's real problem appears when opponent starter hand, OF/DH conversion, run-killing outs, and extra-out damage combine.

## Candidate Feature Contract

Foreign hitter:

- vs RHP on-base plus damage.
- Two-strike contact floor.
- Low GDP/CS run-kill risk.
- Corner OF/DH role continuity.

Foreign pitcher:

- Low free-pass volatility.
- Five-inning floor.
- Damage control after traffic or extra outs.
- Zone command that is not too dependent on called-strike luck.

Asian quota:

- Multi-inning or spot-start shock absorption.
- Contract-realistic market access and role acceptance.

## Objection Handling

Likely presentation objections and the answer:

| objection | answer |
|---|---|
| "Isn't this just outfield power?" | No. OF HR zero is much weaker than the RHP + OF/DH conversion interaction. |
| "Did you just select low RBI games?" | No. OF RBI < 3 alone is weaker; the signal sharpens only with RHP, run-kill, and extra-out context. |
| "Isn't this only pitching?" | No. The message is a hitter-pitcher interaction: if runs allowed rise and OF/DH conversion also disappears, the game locks. |
| "Is the sample too small?" | The six-game top-opponent rule is support-only. The three core rules survived Run 016 robustness checks. |
| "How does it find actual players?" | It becomes observable candidate features and is passed to Layers 2-5 before final SSG fit ranking. |

## Updated Layer 1 Conclusion

Layer 1 moves from 91% to 93%.

It is now presentation/scoring-ready pending refreshed data. It should not be endlessly mined unless new data materially changes the pattern.

The remaining Layer 1 gap is not "find another clever message." The remaining gap is verification:

1. Refresh post-2026-06-11 STATIZ/current-game data.
2. Attach stronger play-by-play, defense, and baserunning proxies.
3. Manually review the promoted rules for baseball plausibility.
4. Then freeze Layer 1 and spend the main modeling effort on Layers 2-5.

## Six-Layer Progress After Run 017

| no. | layer | progress | movement | candidate status |
|---:|---|---:|---|---|
| 1 | SSG hidden weakness mining | 93% | 91% -> 93% | presentation/scoring-ready pending refresh |
| 2 | KBO foreign-player success/failure archetype mining | 55% | unchanged | not enough for final names |
| 3 | Candidate market construction | 68% | unchanged | research leads only |
| 4 | KBO translation model | 56% | unchanged | pilot only |
| 5 | Failure risk model | 53% | unchanged | pilot only |
| 6 | SSG fit ranking | 25% | unchanged | locked |

## Validation

- `src/modeling/build_ssg_layer1_presentation_bridge_v4.py` was py-compiled.
- The script was rerun and produced five output tables.
- Output row counts were inspected:
  - plain-language story: 5 rows;
  - objection response: 5 rows;
  - candidate feature blueprint: 10 rows;
  - evidence trace: 9 rows;
  - freeze checklist: 8 rows.

## Caveats

- The quantitative snapshot still ends at 2026-06-11.
- This is descriptive mining, not causal proof.
- News metadata is corroboration only, not the controlling evidence.
- Candidate names remain locked until Layers 2-6 clear their gates.
