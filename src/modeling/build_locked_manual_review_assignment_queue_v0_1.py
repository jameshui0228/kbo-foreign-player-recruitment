#!/usr/bin/env python3
"""Build an assignment queue for locked manual scouting reviews.

The queue stays candidate-name-free. It turns the anonymous manual review
template into reviewer lanes, evidence tasks, and review waves without
publishing candidate names, teams, exact scores, exact ranks, shortlist labels,
or recommendations.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
TEMPLATE = OUTPUT_DIR / "locked_scouting_card_manual_review_template_v0_1.csv"

RELEASE_POLICY = "locked_manual_review_assignment_queue_no_candidate_name_no_score_no_rank"


LOCK_COLS = [
    "candidate_name_release_allowed",
    "score_release_allowed",
    "rank_release_allowed",
    "shortlist_label_allowed",
    "is_final_recommendation",
    "scouting_card_release_allowed",
    "manual_review_unlock_allowed",
]

FORBIDDEN_COLUMNS = {
    "player_name",
    "team_or_org",
    "risk_adjusted_fit_score_internal",
    "fit_review_order_within_slot",
    "score_default_dacon_style",
    "rank_default_dacon_style",
    "score_ssg_fit_heavy",
    "rank_ssg_fit_heavy",
    "score_risk_conservative",
    "rank_risk_conservative",
    "score_market_realism_heavy",
    "rank_market_realism_heavy",
    "score_translation_heavy",
    "rank_translation_heavy",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", default=str(TEMPLATE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def positive_band(value: object) -> int:
    text = str(value)
    if text == "strong":
        return 3
    if text == "above_average":
        return 2
    if text == "watch":
        return 1
    return 0


def risk_band(value: object) -> int:
    text = str(value)
    if text == "lower_current_risk":
        return 3
    if text == "manageable_risk":
        return 2
    if text == "watch_risk":
        return 1
    return 0


def article_support_band(row: pd.Series) -> int:
    usable = str(row.get("usable_article_rows_band", "none"))
    korean = str(row.get("korean_article_rows_band", "none"))
    score = 0
    if usable == "rich_6_plus":
        score += 3
    elif usable == "some_3_5":
        score += 2
    elif usable == "thin_1_2":
        score += 1
    if korean == "some_3_plus":
        score += 2
    elif korean == "thin_1_2":
        score += 1
    return score


def review_strength(row: pd.Series) -> int:
    return (
        positive_band(row.get("ssg_fit_band"))
        + positive_band(row.get("translation_band"))
        + positive_band(row.get("market_realism_band"))
        + positive_band(row.get("tool_process_band"))
        + positive_band(row.get("surplus_access_band"))
        + risk_band(row.get("failure_risk_band"))
        + article_support_band(row)
    )


def source_search_intensity(row: pd.Series) -> str:
    source_conf = str(row.get("source_confidence_band", ""))
    usable = str(row.get("usable_article_rows_band", "none"))
    korean = str(row.get("korean_article_rows_band", "none"))
    if usable == "none" and korean == "none" and source_conf in {"weak_or_unknown", "watch"}:
        return "cold_start_source_build"
    if usable == "none" and korean == "none":
        return "source_search_required"
    if usable in {"thin_1_2", "some_3_5"} or korean in {"thin_1_2", "some_3_plus"}:
        return "source_expand_then_review"
    return "existing_source_review"


def review_lane(row: pd.Series) -> str:
    risk = str(row.get("primary_risk_focus", ""))
    source_need = source_search_intensity(row)
    slot = str(row.get("fit_slot", ""))
    if source_need == "cold_start_source_build":
        if slot == "foreign_pitcher":
            return "pitcher_source_and_workload_rebuild"
        return "source_rebuild_before_video"
    if "medical" in risk:
        return "medical_availability_check"
    if "contract/access" in risk:
        return "contract_access_check"
    if "role-fit" in risk:
        return "role_fit_video_check"
    if "KBO translation" in risk:
        return "translation_disproof_check"
    if slot == "foreign_hitter":
        return "hitter_video_and_contact_floor_check"
    if slot == "foreign_pitcher":
        return "pitcher_video_and_command_check"
    return "source_feasibility_check"


def review_wave(row: pd.Series) -> str:
    strength = int(row["review_strength_internal"])
    source_need = str(row["source_search_intensity"])
    risk = str(row.get("failure_risk_band", ""))
    if source_need == "existing_source_review" and strength >= 14:
        return "wave_1_evidence_read_now"
    if source_need in {"source_expand_then_review", "source_search_required"} and strength >= 12:
        return "wave_1_source_then_video"
    if source_need == "cold_start_source_build" and strength >= 12 and risk in {"lower_current_risk", "manageable_risk"}:
        return "wave_1_rebuild_source_first"
    if strength >= 10:
        return "wave_2_review_after_core_sources"
    return "wave_3_hold_until_gap_closes"


def first_reviewer_role(row: pd.Series) -> str:
    lane = str(row["review_lane"])
    if "source" in lane or "contract" in lane:
        return "source_contract_reviewer"
    if "medical" in lane or "workload" in lane:
        return "medical_workload_reviewer"
    if "translation" in lane:
        return "translation_model_reviewer"
    if "hitter" in lane:
        return "hitter_video_reviewer"
    if "pitcher" in lane:
        return "pitcher_video_reviewer"
    return "general_scouting_reviewer"


def second_reviewer_role(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    first = str(row["first_reviewer_role"])
    if first != "source_contract_reviewer" and str(row["source_search_intensity"]) in {
        "cold_start_source_build",
        "source_search_required",
    }:
        return "source_contract_reviewer"
    if slot == "foreign_pitcher" and first != "medical_workload_reviewer":
        return "medical_workload_reviewer"
    if slot == "foreign_hitter" and first != "hitter_video_reviewer":
        return "hitter_video_reviewer"
    return "translation_model_reviewer"


def first_fields(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    common = [
        "review_owner",
        "review_date",
        "video_source_url_1",
        "stat_source_url_1",
        "contract_source_url",
        "medical_source_url",
        "reviewer_summary",
    ]
    if slot == "foreign_hitter":
        role_fields = [
            "primary_tool_grade_20_80",
            "command_or_contact_grade_20_80",
            "defense_or_workload_grade_20_80",
            "translation_confidence_20_80",
            "contract_feasibility_grade_20_80",
        ]
    elif slot == "foreign_pitcher":
        role_fields = [
            "primary_tool_grade_20_80",
            "secondary_tool_grade_20_80",
            "command_or_contact_grade_20_80",
            "defense_or_workload_grade_20_80",
            "medical_availability_grade_20_80",
        ]
    else:
        role_fields = [
            "contract_feasibility_grade_20_80",
            "korea_willingness_grade_20_80",
            "translation_confidence_20_80",
        ]
    return "|".join(common + role_fields)


def evidence_gap_statement(row: pd.Series) -> str:
    source_need = str(row["source_search_intensity"])
    slot = str(row.get("fit_slot", ""))
    risk = str(row.get("primary_risk_focus", ""))
    if source_need == "cold_start_source_build":
        return "No usable public article band is attached; build source file before any unlock discussion."
    if source_need == "source_search_required":
        return "Public source band is empty; find at least one stat/video and one feasibility source."
    if "contract/access" in risk:
        return "Contract/access risk is still the first disproof target."
    if slot == "foreign_pitcher":
        return "Pitcher card needs workload, command, medical, and role-continuity confirmation."
    if slot == "foreign_hitter":
        return "Hitter card needs contact-floor, OF/DH role, defense/run value, and contract confirmation."
    return "Feasibility evidence is required before baseball fit can be discussed."


def kill_switch_question(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    source_need = str(row["source_search_intensity"])
    if source_need == "cold_start_source_build":
        return "Can we find two independent sources that confirm current role, status, and availability?"
    if slot == "foreign_pitcher":
        return "Does recent workload or medical context break the starter/multi-inning runway thesis?"
    if slot == "foreign_hitter":
        return "Does video/stat review show a contact-floor or defensive-role flaw that cancels the SSG fit?"
    return "Does passport, contract, or transfer feasibility fail before baseball evaluation starts?"


def build_queue(template: pd.DataFrame) -> pd.DataFrame:
    base_cols = [
        "locked_card_id",
        "fit_slot",
        "card_title",
        "card_stage",
        "sensitivity_band",
        "fit_thesis_public_safe",
        "ssg_fit_band",
        "translation_band",
        "market_realism_band",
        "tool_process_band",
        "surplus_access_band",
        "failure_risk_band",
        "source_confidence_band",
        "primary_risk_focus",
        "usable_article_rows_band",
        "korean_article_rows_band",
        "manual_review_questions",
        "next_source_actions",
    ]
    queue = template[[col for col in base_cols if col in template.columns]].copy()
    queue["review_strength_internal"] = queue.apply(review_strength, axis=1)
    queue["source_search_intensity"] = queue.apply(source_search_intensity, axis=1)
    queue["review_lane"] = queue.apply(review_lane, axis=1)
    queue["review_wave"] = queue.apply(review_wave, axis=1)
    queue["first_reviewer_role"] = queue.apply(first_reviewer_role, axis=1)
    queue["second_reviewer_role"] = queue.apply(second_reviewer_role, axis=1)
    queue["manual_fields_to_complete_first"] = queue.apply(first_fields, axis=1)
    queue["evidence_gap_statement"] = queue.apply(evidence_gap_statement, axis=1)
    queue["kill_switch_question"] = queue.apply(kill_switch_question, axis=1)
    queue["assignment_release_policy"] = RELEASE_POLICY
    queue["candidate_name_release_allowed"] = False
    queue["score_release_allowed"] = False
    queue["rank_release_allowed"] = False
    queue["shortlist_label_allowed"] = False
    queue["is_final_recommendation"] = False
    queue["scouting_card_release_allowed"] = False
    queue["manual_review_unlock_allowed"] = False
    queue["recommendation_label"] = "locked_not_allowed"
    queue = queue.drop(columns=["review_strength_internal"])
    return queue.sort_values(["fit_slot", "review_wave", "review_lane", "locked_card_id"])


def build_summary(queue: pd.DataFrame) -> pd.DataFrame:
    return (
        queue.groupby(["fit_slot", "review_wave", "review_lane"], dropna=False)
        .agg(
            cards=("locked_card_id", "nunique"),
            cold_start_source_cards=("source_search_intensity", lambda s: int((s == "cold_start_source_build").sum())),
            source_search_required_cards=("source_search_intensity", lambda s: int(s.isin(["source_search_required", "source_expand_then_review"]).sum())),
            lower_risk_cards=("failure_risk_band", lambda s: int((s == "lower_current_risk").sum())),
            strong_or_above_fit_cards=("ssg_fit_band", lambda s: int(s.isin(["strong", "above_average"]).sum())),
            release_allowed=("manual_review_unlock_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "review_wave", "review_lane"])
    )


def build_reviewer_workload(queue: pd.DataFrame) -> pd.DataFrame:
    primary = queue[["locked_card_id", "fit_slot", "first_reviewer_role"]].rename(
        columns={"first_reviewer_role": "reviewer_role"}
    )
    primary["reviewer_position"] = "primary"
    secondary = queue[["locked_card_id", "fit_slot", "second_reviewer_role"]].rename(
        columns={"second_reviewer_role": "reviewer_role"}
    )
    secondary["reviewer_position"] = "secondary"
    stacked = pd.concat([primary, secondary], ignore_index=True)
    return (
        stacked.groupby(["reviewer_role", "reviewer_position", "fit_slot"], dropna=False)
        .agg(cards=("locked_card_id", "nunique"))
        .reset_index()
        .sort_values(["reviewer_role", "reviewer_position", "fit_slot"])
    )


def build_checklist() -> pd.DataFrame:
    rows = [
        ("source_contract_reviewer", "source", "Find primary stat/video page and one contract/access source before assigning a manual grade."),
        ("source_contract_reviewer", "contract", "Record salary, option, buyout, transfer, club-control, and agent uncertainty as text evidence."),
        ("medical_workload_reviewer", "medical", "Check injury, rehab, IL, recent workload, pitch count, role continuity, and current availability."),
        ("hitter_video_reviewer", "hitter_video", "Grade swing decision, contact floor, two-strike survival, OF/DH role, defense, and baserunning fit."),
        ("pitcher_video_reviewer", "pitcher_video", "Grade pitch mix, command under traffic, HR/BB damage shape, starter runway, and role willingness."),
        ("translation_model_reviewer", "translation", "Compare manual notes against KBO archetype and failure-risk rules before any unlock discussion."),
        ("general_scouting_reviewer", "decision", "Write continue or kill reason, but keep recommendation locked until all gates pass."),
    ]
    return pd.DataFrame(rows, columns=["reviewer_role", "check_topic", "check_instruction"])


def build_gate_audit(queue: pd.DataFrame, template: pd.DataFrame) -> pd.DataFrame:
    manual_status_ok = True
    if "manual_decision_status" in template.columns:
        manual_status_ok = template["manual_decision_status"].fillna("").eq("locked_no_decision").all()
    forbidden_present = FORBIDDEN_COLUMNS.intersection(queue.columns)
    locks_ok = queue[LOCK_COLS].eq(False).all(axis=1)
    return pd.DataFrame(
        [
            {
                "gate": "A1",
                "check": "assignment_queue_rows_match_manual_template",
                "pass_rows": len(queue),
                "total_rows": len(template),
                "status": "pass" if len(queue) == len(template) else "fail",
                "blocking_gap": "Assignment queue is still anonymous card workflow, not a shortlist",
            },
            {
                "gate": "A2",
                "check": "candidate_identifiers_and_exact_scores_removed",
                "pass_rows": 1 if not forbidden_present else 0,
                "total_rows": 1,
                "status": "pass" if not forbidden_present else "fail",
                "blocking_gap": "Candidate names, teams, exact scores, and exact ranks are not allowed",
            },
            {
                "gate": "A3",
                "check": "release_locks_preserved",
                "pass_rows": int(locks_ok.sum()),
                "total_rows": len(queue),
                "status": "pass" if locks_ok.all() else "fail",
                "blocking_gap": "No candidate names, ranks, scores, shortlist labels, manual unlock labels, or recommendations are released",
            },
            {
                "gate": "A4",
                "check": "manual_decision_status_still_locked",
                "pass_rows": int(len(template) if manual_status_ok else 0),
                "total_rows": len(template),
                "status": "pass" if manual_status_ok else "fail",
                "blocking_gap": "Manual decision remains locked_no_decision until reviewers fill evidence",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    template = pd.read_csv(PROJECT_ROOT / args.template)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    queue = build_queue(template)
    summary = build_summary(queue)
    workload = build_reviewer_workload(queue)
    checklist = build_checklist()
    gate_audit = build_gate_audit(queue, template)

    queue.to_csv(OUTPUT_DIR / f"locked_manual_review_assignment_queue_{suffix}.csv", index=False)
    summary.to_csv(OUTPUT_DIR / f"locked_manual_review_assignment_summary_{suffix}.csv", index=False)
    workload.to_csv(OUTPUT_DIR / f"locked_manual_review_reviewer_workload_{suffix}.csv", index=False)
    checklist.to_csv(OUTPUT_DIR / f"locked_manual_review_checklist_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"locked_manual_review_assignment_gate_audit_{suffix}.csv", index=False)

    print(f"assignment_queue_rows={len(queue)}")
    print(summary.to_string(index=False))
    print(workload.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
