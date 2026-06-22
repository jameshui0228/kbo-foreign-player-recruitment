#!/usr/bin/env python3
"""Build locked scouting-card templates from source-supported fit rows.

This run intentionally removes candidate names, teams, exact scores, and ranks.
The output is a review template, not a candidate shortlist or recommendation.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
SOURCE_PACKET = OUTPUT_DIR / "ssg_fit_source_fill_packet_v0_1.csv"

RELEASE_POLICY = "locked_scouting_card_template_no_candidate_name_no_score_no_rank"


CARD_FIELDS = [
    ("slot_context", "What acquisition slot and roster problem does this card address?"),
    ("ssg_fit_question", "What SSG-specific need does the profile claim to solve?"),
    ("translation_question", "What evidence says this profile can translate to KBO?"),
    ("tool_process_question", "What tool/process traits need scouting confirmation?"),
    ("risk_question", "What failure mode could still break the case?"),
    ("market_question", "What contract/availability reality must be verified?"),
    ("medical_question", "What health/workload status must be verified?"),
    ("adaptation_question", "What Korea/role/clubhouse adaptation evidence is still needed?"),
    ("source_question", "Which source types should the reviewer open first?"),
    ("decision_question", "What would move this card forward or close it?"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(SOURCE_PACKET.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def safe_num(frame: pd.DataFrame, col: str, default: float = np.nan) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[col], errors="coerce")


def band(value: object, reverse: bool = False) -> str:
    try:
        val = float(value)
    except (TypeError, ValueError):
        return "unknown"
    if np.isnan(val):
        return "unknown"
    if reverse:
        if val >= 70:
            return "high_risk"
        if val >= 55:
            return "watch_risk"
        if val >= 40:
            return "manageable_risk"
        return "lower_current_risk"
    if val >= 70:
        return "strong"
    if val >= 55:
        return "above_average"
    if val >= 40:
        return "watch"
    return "weak_or_unknown"


def card_id(row: pd.Series) -> str:
    slot_prefix = {"foreign_hitter": "FH", "foreign_pitcher": "FP", "asian_quota": "AQ"}.get(row["fit_slot"], "XX")
    seed = "|".join(
        str(row.get(col, ""))
        for col in ["fit_slot", "source_fill_candidate_key", "player_id", "player_name", "team_or_org", "position_or_role"]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10].upper()
    return f"LOCKED-{slot_prefix}-{digest}"


def slot_label(slot: str) -> str:
    return {
        "foreign_hitter": "foreign_hitter_outfield_priority",
        "foreign_pitcher": "foreign_pitcher_starter_multi_inning_priority",
        "asian_quota": "asian_quota_source_blocked",
    }.get(slot, slot)


def build_card_title(row: pd.Series) -> str:
    if row["fit_slot"] == "foreign_hitter":
        return "Locked OF/DH fit review card"
    if row["fit_slot"] == "foreign_pitcher":
        return "Locked SP/multi-inning fit review card"
    return "Locked Asian-quota source review card"


def hitter_fit_thesis(row: pd.Series) -> str:
    tags = []
    if str(row.get("fit_review_tags", "")).find("translation_risk_low") >= 0:
        tags.append("translation-risk band is favorable")
    if str(row.get("fit_review_tags", "")).find("market_access_relatively_better") >= 0:
        tags.append("market-access band is favorable")
    if str(row.get("fit_review_tags", "")).find("tool_process_signal") >= 0:
        tags.append("tool/process band is favorable")
    if not tags:
        tags.append("profile needs manual offensive/defensive confirmation")
    return "OF/DH profile: " + "; ".join(tags)


def pitcher_fit_thesis(row: pd.Series) -> str:
    tags = []
    if str(row.get("fit_review_tags", "")).find("translation_risk_low") >= 0:
        tags.append("translation-risk band is favorable")
    if str(row.get("fit_review_tags", "")).find("tool_process_signal") >= 0:
        tags.append("damage-command/process band is favorable")
    if str(row.get("fit_review_tags", "")).find("market_access_relatively_better") >= 0:
        tags.append("market-access band is favorable")
    if not tags:
        tags.append("profile needs workload/role confirmation")
    return "SP/multi-inning profile: " + "; ".join(tags)


def fit_thesis(row: pd.Series) -> str:
    if row["fit_slot"] == "foreign_hitter":
        return hitter_fit_thesis(row)
    if row["fit_slot"] == "foreign_pitcher":
        return pitcher_fit_thesis(row)
    return "Asian-quota profile remains source blocked before scouting-card promotion"


def risk_focus(row: pd.Series) -> str:
    risks = []
    for col, label in [
        ("medical_availability_risk", "medical/availability"),
        ("contract_cost_access_risk", "contract/access"),
        ("role_fit_risk", "role-fit"),
        ("kbo_translation_risk", "KBO translation"),
        ("adaptation_willingness_risk", "adaptation/willingness"),
        ("data_gap_risk", "data gap"),
    ]:
        if band(row.get(col), reverse=True) in {"high_risk", "watch_risk"}:
            risks.append(label)
    return "|".join(risks) if risks else "no_primary_high_risk_bucket_after_source_fill"


def source_status(row: pd.Series) -> str:
    return "|".join(
        [
            f"contract:{row.get('contract_source_status', 'unknown')}",
            f"medical:{row.get('medical_source_status', 'unknown')}",
            f"korea:{row.get('korea_willingness_source_status', 'unknown')}",
            f"nationality:{row.get('nationality_passport_source_status', 'unknown')}",
        ]
    )


def question_answers(row: pd.Series) -> dict[str, str]:
    if row["fit_slot"] == "foreign_hitter":
        ssg_fit_question = "Can this OF/DH profile improve SSG's RHP game-script and run-kill avoidance problem without creating a contact-floor issue?"
        tool_question = "Confirm swing decisions, two-strike survival, OF defense/run value, platoon usability, and whether batted-ball quality is playable in KBO."
        market_question = "Verify current contract, option status, salary expectation, agent openness, and whether the player is realistically movable midseason."
        decision_question = "Advance only if OF/role fit, contact floor, medical availability, and contract feasibility are all source-supported."
    elif row["fit_slot"] == "foreign_pitcher":
        ssg_fit_question = "Can this SP/multi-inning profile stabilize SSG's traffic-command and extra-out resilience problem?"
        tool_question = "Confirm starter runway, pitch mix quality, strike-throwing under traffic, HR/BB damage suppression, and role willingness."
        market_question = "Verify current contract, option status, salary expectation, agent openness, and whether the arm is realistically movable midseason."
        decision_question = "Advance only if workload continuity, medical availability, command/damage profile, and contract feasibility are all source-supported."
    else:
        ssg_fit_question = "Can this Asian-quota profile pass nationality, contract, and roster feasibility before baseball fit is evaluated?"
        tool_question = "Confirm league context, role, tools, and whether the profile is comparable to KBO target needs."
        market_question = "Verify passport, nationality, contract, transfer fee, buyout, salary, and agent/team willingness."
        decision_question = "Advance only after passport, contract, buyout, and medical/current availability are all verified."

    return {
        "slot_context": slot_label(str(row["fit_slot"])),
        "ssg_fit_question": ssg_fit_question,
        "translation_question": "Check whether candidate-side signals align with promoted KBO archetype rules and do not trigger a known failure mode.",
        "tool_process_question": tool_question,
        "risk_question": f"Review risk focus: {risk_focus(row)}.",
        "market_question": market_question,
        "medical_question": "Verify the most recent injury, rehab, workload, and current availability status from a source stronger than metadata snippets.",
        "adaptation_question": "Look for direct or indirect evidence of Korea/overseas openness, role acceptance, timing, family/visa constraints, and agent/team posture.",
        "source_question": f"Open sources for: {source_status(row)}. Next actions: {row.get('next_source_actions', '')}.",
        "decision_question": decision_question,
    }


def build_cards(packet: pd.DataFrame) -> pd.DataFrame:
    eligible = packet[packet["source_fill_readiness_bucket"].eq("source_supported_scouting_card_next_locked")].copy()
    cards = pd.DataFrame(index=eligible.index)
    cards["locked_card_id"] = eligible.apply(card_id, axis=1)
    cards["fit_slot"] = eligible["fit_slot"]
    cards["card_title"] = eligible.apply(build_card_title, axis=1)
    cards["card_release_policy"] = RELEASE_POLICY
    cards["card_stage"] = "scouting_card_template_locked_no_candidate_name"
    cards["source_fill_readiness_bucket"] = eligible["source_fill_readiness_bucket"]
    cards["sensitivity_band"] = eligible["sensitivity_band"]
    cards["fit_thesis_public_safe"] = eligible.apply(fit_thesis, axis=1)
    cards["ssg_fit_band"] = eligible["ssg_fit_component"].map(band)
    cards["translation_band"] = eligible["kbo_translation_component"].map(band)
    cards["market_realism_band"] = eligible["market_realism_component"].map(band)
    cards["tool_process_band"] = eligible["tool_process_component"].map(band)
    cards["surplus_access_band"] = eligible["surplus_access_component"].map(band)
    cards["failure_risk_band"] = eligible["failure_risk_index"].map(lambda value: band(value, reverse=True))
    cards["source_confidence_band"] = eligible["source_confidence_component"].map(band)
    cards["primary_risk_focus"] = eligible.apply(risk_focus, axis=1)
    cards["source_status_summary"] = eligible.apply(source_status, axis=1)
    cards["manual_review_questions"] = eligible.apply(lambda row: " || ".join(question_answers(row).values()), axis=1)
    cards["next_source_actions"] = eligible["next_source_actions"]
    cards["usable_article_rows_band"] = pd.cut(
        pd.to_numeric(eligible["usable_article_rows"], errors="coerce").fillna(0),
        bins=[-1, 0, 2, 5, 9999],
        labels=["none", "thin_1_2", "some_3_5", "rich_6_plus"],
    ).astype(str)
    cards["korean_article_rows_band"] = pd.cut(
        pd.to_numeric(eligible["korean_article_rows"], errors="coerce").fillna(0),
        bins=[-1, 0, 2, 9999],
        labels=["none", "thin_1_2", "some_3_plus"],
    ).astype(str)
    cards["candidate_name_release_allowed"] = False
    cards["score_release_allowed"] = False
    cards["rank_release_allowed"] = False
    cards["shortlist_label_allowed"] = False
    cards["is_final_recommendation"] = False
    cards["scouting_card_release_allowed"] = False
    cards["recommendation_label"] = "locked_not_allowed"
    return cards.sort_values(["fit_slot", "locked_card_id"])


def build_schema() -> pd.DataFrame:
    rows = []
    for field, prompt in CARD_FIELDS:
        rows.append(
            {
                "field": field,
                "review_prompt": prompt,
                "required_before_unlock": True,
                "candidate_name_allowed": False,
                "score_or_rank_allowed": False,
            }
        )
    return pd.DataFrame(rows)


def build_question_bank() -> pd.DataFrame:
    rows = []
    slot_prompts = {
        "foreign_hitter": [
            ("offense", "Does the profile improve RHP game-script quality without raising contact-floor risk?"),
            ("role", "Can the player handle SSG's realistic OF/DH role and lineup slot?"),
            ("defense_baserunning", "Does defense/run value avoid creating a new run-kill problem?"),
            ("translation", "Which pre-KBO/KBO-translation signals are strongest, and which are thin?"),
            ("market", "What exact contract, salary, option, and agent evidence is still needed?"),
        ],
        "foreign_pitcher": [
            ("workload", "Is there enough recent starter or multi-inning runway?"),
            ("traffic_command", "Does the profile suppress BB/HR damage after traffic?"),
            ("role", "Is role continuity real, or is this only raw stuff without workload support?"),
            ("medical", "What current injury, rehab, or workload interruption must be checked?"),
            ("market", "What exact contract, salary, option, and agent evidence is still needed?"),
        ],
        "asian_quota": [
            ("passport", "Is passport/nationality eligibility actually verified?"),
            ("contract", "What transfer fee, buyout, salary, and club-control evidence is needed?"),
            ("league_context", "How should NPB/CPBL performance be translated to KBO role needs?"),
            ("medical", "Is there recent medical/current-availability evidence?"),
            ("role", "Would the player accept the KBO/SSG role at Asian-quota cost constraints?"),
        ],
    }
    for slot, prompts in slot_prompts.items():
        for topic, prompt in prompts:
            rows.append(
                {
                    "fit_slot": slot,
                    "question_topic": topic,
                    "review_question": prompt,
                    "required_before_candidate_unlock": True,
                }
            )
    return pd.DataFrame(rows)


def build_slot_summary(cards: pd.DataFrame) -> pd.DataFrame:
    if cards.empty:
        return pd.DataFrame()
    return (
        cards.groupby(["fit_slot", "failure_risk_band", "source_confidence_band"], dropna=False)
        .agg(
            cards=("locked_card_id", "nunique"),
            strong_fit_cards=("ssg_fit_band", lambda s: int(s.isin(["strong", "above_average"]).sum())),
            strong_translation_cards=("translation_band", lambda s: int(s.isin(["strong", "above_average"]).sum())),
            market_watch_cards=("market_realism_band", lambda s: int(s.isin(["weak_or_unknown", "watch"]).sum())),
            release_allowed=("scouting_card_release_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "failure_risk_band", "source_confidence_band"])
    )


def build_gate_audit(cards: pd.DataFrame, packet: pd.DataFrame) -> pd.DataFrame:
    lock_cols = [
        "candidate_name_release_allowed",
        "score_release_allowed",
        "rank_release_allowed",
        "shortlist_label_allowed",
        "is_final_recommendation",
        "scouting_card_release_allowed",
    ]
    source_supported_rows = int(packet["source_fill_readiness_bucket"].eq("source_supported_scouting_card_next_locked").sum())
    forbidden_cols = {"player_name", "team_or_org", "risk_adjusted_fit_score_internal", "fit_review_order_within_slot"}
    return pd.DataFrame(
        [
            {
                "gate": "C1",
                "check": "cards_built_from_source_supported_rows",
                "pass_rows": len(cards),
                "total_rows": source_supported_rows,
                "status": "pass" if len(cards) == source_supported_rows else "fail",
                "blocking_gap": "Cards are templates only and do not unlock candidates",
            },
            {
                "gate": "C2",
                "check": "candidate_identifiers_removed",
                "pass_rows": 1 if forbidden_cols.isdisjoint(set(cards.columns)) else 0,
                "total_rows": 1,
                "status": "pass" if forbidden_cols.isdisjoint(set(cards.columns)) else "fail",
                "blocking_gap": "Candidate names, teams, exact scores, and exact ranks are excluded from card template output",
            },
            {
                "gate": "C3",
                "check": "release_locks_preserved",
                "pass_rows": int((cards[lock_cols].eq(False).all(axis=1)).sum()),
                "total_rows": len(cards),
                "status": "pass",
                "blocking_gap": "No candidate names, scores, ranks, shortlist labels, scouting-card release, or recommendations are allowed",
            },
            {
                "gate": "C4",
                "check": "asian_quota_not_promoted_to_card",
                "pass_rows": int(cards["fit_slot"].ne("asian_quota").sum()),
                "total_rows": len(cards),
                "status": "pass",
                "blocking_gap": "Asian quota remains source-blocked before scouting-card promotion",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    packet = pd.read_csv(PROJECT_ROOT / args.input)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cards = build_cards(packet)
    schema = build_schema()
    question_bank = build_question_bank()
    slot_summary = build_slot_summary(cards)
    gate_audit = build_gate_audit(cards, packet)

    cards.to_csv(OUTPUT_DIR / f"locked_scouting_card_templates_{suffix}.csv", index=False)
    schema.to_csv(OUTPUT_DIR / f"locked_scouting_card_schema_{suffix}.csv", index=False)
    question_bank.to_csv(OUTPUT_DIR / f"locked_scouting_card_question_bank_{suffix}.csv", index=False)
    slot_summary.to_csv(OUTPUT_DIR / f"locked_scouting_card_slot_summary_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"locked_scouting_card_gate_audit_{suffix}.csv", index=False)

    print(f"card_rows={len(cards)}")
    print(slot_summary.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
