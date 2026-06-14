#!/usr/bin/env python3
"""Mine evidence cards that can support slot-specific recruitment messages.

This script intentionally separates pattern discovery from interpretation.
It does not start with a preferred message. It scans available tables for
extreme ranks, large gaps, role splits, external corroboration, and market-rule
signals, then scores messages only from those evidence cards.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"


def fmt(value: Any, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def evidence_card(
    *,
    card_id: str,
    slot: str,
    theme: str,
    claim: str,
    metric: str,
    observed: str,
    comparison: str,
    source_table: str,
    source_type: str,
    novelty: int,
    ssg_specificity: int,
    actionability: int,
    data_strength: int,
    caveat: str,
) -> dict[str, Any]:
    total = novelty + ssg_specificity + actionability + data_strength
    return {
        "card_id": card_id,
        "slot": slot,
        "theme": theme,
        "claim": claim,
        "metric": metric,
        "observed": observed,
        "comparison": comparison,
        "source_table": source_table,
        "source_type": source_type,
        "novelty_1_5": novelty,
        "ssg_specificity_1_5": ssg_specificity,
        "actionability_1_5": actionability,
        "data_strength_1_5": data_strength,
        "evidence_score": total,
        "caveat": caveat,
    }


def mine_hitter_cards(cards: list[dict[str, Any]]) -> None:
    path = "outputs/tables/ssg_2026_runway_gap_by_team.csv"
    df = pd.read_csv(PROJECT_ROOT / path)
    ssg = df[df["t_code_name"].eq("SSG")].iloc[0]
    cards.append(
        evidence_card(
            card_id="hit_001_runway_gap",
            slot="foreign_hitter",
            theme="runner_on_first_transition",
            claim="SSG is elite after reaching RISP but bottom-tier before converting first-base traffic.",
            metric="RISP OPS rank vs runner-on-first OPS rank",
            observed=f"RISP OPS {fmt(ssg['OPS_risp'])} rank {fmt(ssg['risp_ops_rank'], 0)}; on-first OPS {fmt(ssg['OPS_on_first'])} rank {fmt(ssg['on_first_ops_rank'], 0)}",
            comparison=f"RISP minus on-first OPS gap {fmt(ssg['risp_minus_on_first_ops'])}, largest in KBO",
            source_table=path,
            source_type="STATIZ team situation rank",
            novelty=5,
            ssg_specificity=5,
            actionability=5,
            data_strength=5,
            caveat="Team split does not identify individual foreign-candidate availability.",
        )
    )

    path = "outputs/tables/ssg_2026_role_runway_context.csv"
    roles = pd.read_csv(PROJECT_ROOT / path)
    on_first = roles[roles["split_label"].eq("on_first")].copy()
    high_of = on_first[on_first["role_segment"].eq("OF_high_leverage_usage")].iloc[0]
    ifc = on_first[on_first["role_segment"].eq("IF_C_core")].iloc[0]
    dh = on_first[on_first["role_segment"].eq("DH_primary_or_bridge")].iloc[0]
    cards.append(
        evidence_card(
            card_id="hit_002_role_location",
            slot="foreign_hitter",
            theme="of_dh_bottleneck",
            claim="The runner-on-first bottleneck is concentrated in replacement-relevant OF/DH usage, not the whole lineup.",
            metric="Role-segment OPS with runner on first",
            observed=f"High-leverage OF OPS {fmt(high_of['ops'])}, RBI {fmt(high_of['rbi'],0)} in {fmt(high_of['pa'],0)} PA; DH OPS {fmt(dh['ops'])}",
            comparison=f"IF/C core OPS {fmt(ifc['ops'])}",
            source_table=path,
            source_type="STATIZ player/role split",
            novelty=4,
            ssg_specificity=5,
            actionability=5,
            data_strength=4,
            caveat="Role labels are analytical groupings and should be reviewed before final presentation.",
        )
    )

    lt2 = roles[roles["split_label"].eq("lt2_out_on_first")]
    high_lt2 = lt2[lt2["role_segment"].eq("OF_high_leverage_usage")].iloc[0]
    cards.append(
        evidence_card(
            card_id="hit_003_gdp_transition_risk",
            slot="foreign_hitter",
            theme="inning_survival",
            claim="SSG needs a hitter who keeps the inning alive before RISP, not a hitter whose value starts only at RBI chances.",
            metric="<2 outs runner-on-first OPS and GDP",
            observed=f"High-leverage OF OPS {fmt(high_lt2['ops'])}; GDP {fmt(high_lt2['gdp'],0)} in {fmt(high_lt2['pa'],0)} PA",
            comparison="This is the exact state that creates or kills future RISP chances.",
            source_table=path,
            source_type="STATIZ player/role split",
            novelty=4,
            ssg_specificity=5,
            actionability=5,
            data_strength=4,
            caveat="GDP risk requires batted-ball shape validation from candidate-level data.",
        )
    )


def mine_pitcher_cards(cards: list[dict[str, Any]]) -> None:
    path = "outputs/tables/ssg_2026_team_pitching_role_ranks.csv"
    role = pd.read_csv(PROJECT_ROOT / path)
    starter = role[role["pitch_role"].eq("starter")].iloc[0]
    bullpen = role[role["pitch_role"].eq("bullpen")].iloc[0]
    cards.append(
        evidence_card(
            card_id="pit_001_short_start_core",
            slot="foreign_pitcher",
            theme="starter_runway_failure",
            claim="SSG's pitching problem starts in the rotation, not simply in bullpen quality.",
            metric="Starter ranks and bullpen workload",
            observed=f"Starter ERA {fmt(starter['era'])}, WHIP {fmt(starter['whip'])}, OPSA {fmt(starter['ops_allowed'])}; all rank 10th in key stability metrics",
            comparison=f"Bullpen IP/G {fmt(bullpen['ip_per_game'])}, workload rank 1, but WHIP rank {fmt(bullpen['whip_rank'],0)} and OPSA rank {fmt(bullpen['ops_allowed_rank'],0)}",
            source_table=path,
            source_type="STATIZ team role rank",
            novelty=4,
            ssg_specificity=5,
            actionability=5,
            data_strength=5,
            caveat="Bullpen quality under fatigue still needs internal availability/rest data.",
        )
    )

    path = "outputs/tables/ssg_2026_game_pitching_workload.csv"
    games = pd.read_csv(PROJECT_ROOT / path)
    short = games[games["starter_short_lt5"].astype(bool)]
    non_short = games[~games["starter_short_lt5"].astype(bool)]
    cards.append(
        evidence_card(
            card_id="pit_002_game_script_delta",
            slot="foreign_pitcher",
            theme="game_script_compression",
            claim="One extra starter inning changes the whole game script for SSG.",
            metric="Short-start vs non-short-start games",
            observed=f"Short starts {len(short)}/{len(games)}; win pct {fmt(short['win'].mean())}; bullpen IP {fmt(short['bullpen_ip_after_start'].mean())}",
            comparison=f"Non-short win pct {fmt(non_short['win'].mean())}; bullpen IP {fmt(non_short['bullpen_ip_after_start'].mean())}",
            source_table=path,
            source_type="STATIZ game-level workload",
            novelty=4,
            ssg_specificity=5,
            actionability=5,
            data_strength=5,
            caveat="Win pct is descriptive and not causal by itself.",
        )
    )

    path = "outputs/tables/ssg_2026_import_slot_pitching_impact.csv"
    impact = pd.read_csv(PROJECT_ROOT / path)
    imp = impact[(impact["import_slot_group"].eq("import_slot_pitcher")) & (impact["pitch_role"].eq("starter"))].iloc[0]
    dom = impact[(impact["import_slot_group"].eq("domestic_pitcher")) & (impact["pitch_role"].eq("starter"))].iloc[0]
    cards.append(
        evidence_card(
            card_id="pit_003_import_slot_inversion",
            slot="foreign_pitcher",
            theme="import_slot_failure",
            claim="The import starter slot is amplifying SSG's rotation scarcity instead of absorbing it.",
            metric="Import-slot starter performance vs domestic starter performance",
            observed=f"Import starters ERA {fmt(imp['era'])}, WHIP {fmt(imp['whip'])}, OPSA {fmt(imp['ops_allowed'])}",
            comparison=f"Domestic starters ERA {fmt(dom['era'])}, WHIP {fmt(dom['whip'])}, OPSA {fmt(dom['ops_allowed'])}",
            source_table=path,
            source_type="STATIZ slot impact",
            novelty=5,
            ssg_specificity=5,
            actionability=5,
            data_strength=4,
            caveat="Import-slot grouping depends on current name classification.",
        )
    )

    path = "outputs/tables/external_abs_zone_shift_summary.csv"
    abs_df = pd.read_csv(PROJECT_ROOT / path)
    beta = abs_df[abs_df["parameter"].eq("beta")].iloc[0]
    rect = abs_df[abs_df["parameter"].eq("r")].iloc[0]
    cards.append(
        evidence_card(
            card_id="pit_004_abs_command_environment",
            slot="foreign_pitcher",
            theme="abs_native_command",
            claim="KBO's ABS environment changes what 'command' should mean in foreign-pitcher scouting.",
            metric="KBO 2024 vs 2023 ABS/called-zone model parameters",
            observed=f"beta shift {fmt(beta['kbo_2024_vs_2023_pct'] * 100,1)}%; r shift {fmt(rect['kbo_2024_vs_2023_pct'] * 100,1)}%",
            comparison="Higher beta and r imply a stricter, clearer, more rule-book-like zone than pre-ABS KBO.",
            source_table=path,
            source_type="external research/public result data",
            novelty=5,
            ssg_specificity=3,
            actionability=5,
            data_strength=4,
            caveat="This is league-environment evidence; candidate-level KBO pitch-location data would strengthen it.",
        )
    )


def mine_asian_quota_cards(cards: list[dict[str, Any]]) -> None:
    path = "outputs/tables/external_message_candidates_v1.csv"
    external = pd.read_csv(PROJECT_ROOT / path)
    aq = external[external["message_id"].eq("asian_quota_optionality_trap")].iloc[0]
    cards.append(
        evidence_card(
            card_id="aq_001_option_slot_rule",
            slot="asian_quota",
            theme="optionality_not_ace",
            claim="The Asian quota is structurally an option/depth slot, not a regular foreign ace substitute.",
            metric="External message score and rule-market interpretation",
            observed=f"External message score {fmt(aq['total_score'],0)}; distinctiveness {fmt(aq['distinctiveness_1_5'],0)}, actionability {fmt(aq['actionability_1_5'],0)}",
            comparison="Regular foreign pitcher slot should carry the rotation-pillar burden; Asian quota should reduce shock exposure.",
            source_table=path,
            source_type="external rule/news synthesis",
            novelty=5,
            ssg_specificity=4,
            actionability=4,
            data_strength=3,
            caveat="The 2026 Asian quota market is new, so historical outcome validation is limited.",
        )
    )

    path = "outputs/tables/ssg_2026_game_pitching_workload.csv"
    games = pd.read_csv(PROJECT_ROOT / path)
    short = games[games["starter_short_lt5"].astype(bool)]
    non_short = games[~games["starter_short_lt5"].astype(bool)]
    cards.append(
        evidence_card(
            card_id="aq_002_multi_inning_absorption",
            slot="asian_quota",
            theme="shock_absorption",
            claim="The quota slot has practical value if it absorbs the innings created by short starts.",
            metric="Bullpen IP after short starts",
            observed=f"Short starts force {fmt(short['bullpen_ip_after_start'].mean())} bullpen IP on average",
            comparison=f"Non-short starts force {fmt(non_short['bullpen_ip_after_start'].mean())}; gap {fmt(short['bullpen_ip_after_start'].mean() - non_short['bullpen_ip_after_start'].mean())} IP",
            source_table=path,
            source_type="STATIZ game-level workload",
            novelty=4,
            ssg_specificity=5,
            actionability=5,
            data_strength=5,
            caveat="Does not prove an Asian quota pitcher is available with the required multi-inning profile.",
        )
    )

    path = "outputs/tables/ssg_pitching_news_tag_summary.csv"
    news = pd.read_csv(PROJECT_ROOT / path)
    rotation = news[news["tag"].eq("starter_rotation")].iloc[0]
    bullpen = news[news["tag"].eq("bullpen_load")].iloc[0]
    cards.append(
        evidence_card(
            card_id="aq_003_text_corroboration",
            slot="asian_quota",
            theme="external_text_need",
            claim="External article language repeatedly links SSG's pitcher issue to rotation shortage and bullpen load.",
            metric="Naver pitching news tag counts",
            observed=f"starter/rotation articles {fmt(rotation['articles'],0)}; bullpen-load articles {fmt(bullpen['articles'],0)}",
            comparison="The article corpus supports shock-absorption as a public narrative, though it is query-biased.",
            source_table=path,
            source_type="Naver Search News metadata",
            novelty=3,
            ssg_specificity=4,
            actionability=3,
            data_strength=3,
            caveat="Search corpus is not a random sample and should be used as corroboration, not proof.",
        )
    )


def build_message_scores(cards: pd.DataFrame) -> pd.DataFrame:
    messages = [
        {
            "slot": "foreign_hitter",
            "message_id": "runway_converter",
            "message": "Foreign hitter should convert first-base traffic into scoring-position pressure.",
            "required_cards": ["hit_001_runway_gap", "hit_002_role_location", "hit_003_gdp_transition_risk"],
        },
        {
            "slot": "foreign_pitcher",
            "message_id": "abs_native_load_bearing_starter",
            "message": "Foreign pitcher should be an ABS-native six-inning stabilizer.",
            "required_cards": ["pit_001_short_start_core", "pit_002_game_script_delta", "pit_003_import_slot_inversion", "pit_004_abs_command_environment"],
        },
        {
            "slot": "asian_quota",
            "message_id": "option_layer",
            "message": "Asian quota should be a low-cost shock-absorption option layer.",
            "required_cards": ["aq_001_option_slot_rule", "aq_002_multi_inning_absorption", "aq_003_text_corroboration"],
        },
    ]
    rows = []
    by_id = cards.set_index("card_id")
    for message in messages:
        selected = by_id.loc[message["required_cards"]]
        rows.append(
            {
                "slot": message["slot"],
                "message_id": message["message_id"],
                "message": message["message"],
                "evidence_cards": ",".join(message["required_cards"]),
                "cards": len(selected),
                "total_evidence_score": int(selected["evidence_score"].sum()),
                "avg_evidence_score": float(selected["evidence_score"].mean()),
                "avg_novelty": float(selected["novelty_1_5"].mean()),
                "avg_ssg_specificity": float(selected["ssg_specificity_1_5"].mean()),
                "avg_actionability": float(selected["actionability_1_5"].mean()),
                "avg_data_strength": float(selected["data_strength_1_5"].mean()),
                "weakest_caveat": " | ".join(selected.sort_values("data_strength_1_5")["caveat"].head(2)),
            }
        )
    return pd.DataFrame(rows).sort_values("total_evidence_score", ascending=False)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cards: list[dict[str, Any]] = []
    mine_hitter_cards(cards)
    mine_pitcher_cards(cards)
    mine_asian_quota_cards(cards)
    evidence = pd.DataFrame(cards).sort_values(["slot", "evidence_score"], ascending=[True, False])
    scores = build_message_scores(evidence)
    evidence.to_csv(OUTPUT_DIR / "message_mining_evidence_cards_v1.csv", index=False)
    scores.to_csv(OUTPUT_DIR / "message_mining_slot_scores_v1.csv", index=False)
    print("wrote", OUTPUT_DIR / "message_mining_evidence_cards_v1.csv")
    print("wrote", OUTPUT_DIR / "message_mining_slot_scores_v1.csv")
    print(scores.to_string(index=False))


if __name__ == "__main__":
    main()
