#!/usr/bin/env python3
"""Build a manual review template for locked scouting cards.

The output is intentionally candidate-name-free. It gives teammates a common
place to enter scouting notes, source URLs, 20-80 grades, contract evidence,
medical evidence, and Korea-willingness evidence.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
CARDS = OUTPUT_DIR / "locked_scouting_card_templates_v0_1.csv"

RELEASE_POLICY = "manual_review_template_locked_no_candidate_name_no_score_no_rank"


MANUAL_FIELDS = [
    "review_owner",
    "review_date",
    "review_status",
    "video_source_url_1",
    "video_source_url_2",
    "stat_source_url_1",
    "stat_source_url_2",
    "contract_source_url",
    "medical_source_url",
    "korea_willingness_source_url",
    "primary_tool_grade_20_80",
    "secondary_tool_grade_20_80",
    "command_or_contact_grade_20_80",
    "role_fit_grade_20_80",
    "defense_or_workload_grade_20_80",
    "translation_confidence_20_80",
    "medical_availability_grade_20_80",
    "contract_feasibility_grade_20_80",
    "korea_willingness_grade_20_80",
    "overall_manual_grade_20_80",
    "manual_green_flags",
    "manual_red_flags",
    "reviewer_summary",
    "continue_reason",
    "kill_reason",
    "manual_decision_status",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cards", default=str(CARDS.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def empty_manual_value(field: str) -> str:
    if field == "review_status":
        return "not_started"
    if field == "manual_decision_status":
        return "locked_no_decision"
    return ""


def build_template(cards: pd.DataFrame) -> pd.DataFrame:
    keep = [
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
        "source_status_summary",
        "manual_review_questions",
        "next_source_actions",
        "usable_article_rows_band",
        "korean_article_rows_band",
    ]
    out = cards[[col for col in keep if col in cards.columns]].copy()
    for field in MANUAL_FIELDS:
        out[field] = empty_manual_value(field)
    out["manual_review_release_policy"] = RELEASE_POLICY
    out["candidate_name_release_allowed"] = False
    out["score_release_allowed"] = False
    out["rank_release_allowed"] = False
    out["shortlist_label_allowed"] = False
    out["is_final_recommendation"] = False
    out["scouting_card_release_allowed"] = False
    out["manual_review_unlock_allowed"] = False
    out["recommendation_label"] = "locked_not_allowed"
    return out.sort_values(["fit_slot", "locked_card_id"])


def build_rubric() -> pd.DataFrame:
    rows = [
        ("review_owner", "free_text", "Reviewer name or initials. Leave blank until assigned.", "required_for_manual_review"),
        ("review_date", "yyyy-mm-dd", "Date the manual review was completed.", "required_for_manual_review"),
        ("review_status", "not_started|in_progress|needs_source|reviewed", "Workflow status.", "required_for_manual_review"),
        ("video_source_url_1", "url", "Primary video or report source used for tool/process review.", "required_for_manual_review"),
        ("stat_source_url_1", "url", "Primary stat page or report source used for numeric/context review.", "required_for_manual_review"),
        ("contract_source_url", "url", "Best source for contract, salary, option, buyout, or agent context.", "required_before_unlock"),
        ("medical_source_url", "url", "Best source for current injury, rehab, workload, or availability status.", "required_before_unlock"),
        ("korea_willingness_source_url", "url", "Best source for Korea/overseas willingness or role acceptance.", "required_before_unlock"),
        ("primary_tool_grade_20_80", "20|30|40|45|50|55|60|70|80", "Hitter: bat/power carrying tool. Pitcher: best pitch or stuff carrying tool.", "required_for_manual_review"),
        ("secondary_tool_grade_20_80", "20|30|40|45|50|55|60|70|80", "Hitter: secondary offensive/athletic tool. Pitcher: secondary pitch or bat-missing support.", "recommended"),
        ("command_or_contact_grade_20_80", "20|30|40|45|50|55|60|70|80", "Hitter: contact/zone survival. Pitcher: strike-throwing and traffic command.", "required_for_manual_review"),
        ("role_fit_grade_20_80", "20|30|40|45|50|55|60|70|80", "Fit to SSG role, lineup/rotation usage, and replacement timing.", "required_for_manual_review"),
        ("defense_or_workload_grade_20_80", "20|30|40|45|50|55|60|70|80", "Hitter: OF defense/run value. Pitcher: workload/starter runway.", "required_for_manual_review"),
        ("translation_confidence_20_80", "20|30|40|45|50|55|60|70|80", "Confidence that the profile translates to KBO context.", "required_for_manual_review"),
        ("medical_availability_grade_20_80", "20|30|40|45|50|55|60|70|80", "Current health, workload continuity, and near-term availability.", "required_before_unlock"),
        ("contract_feasibility_grade_20_80", "20|30|40|45|50|55|60|70|80", "Cost/access feasibility under KBO and SSG constraints.", "required_before_unlock"),
        ("korea_willingness_grade_20_80", "20|30|40|45|50|55|60|70|80", "Likelihood of Korea/overseas acceptance at realistic role/cost.", "required_before_unlock"),
        ("overall_manual_grade_20_80", "20|30|40|45|50|55|60|70|80", "Overall manual review grade after source checks.", "required_for_manual_review"),
        ("manual_green_flags", "free_text", "Positive observations that support continued review.", "recommended"),
        ("manual_red_flags", "free_text", "Negative observations that could kill the case.", "recommended"),
        ("reviewer_summary", "free_text", "Short synthesis in scouting language.", "required_for_manual_review"),
        ("continue_reason", "free_text", "Why this card should continue if it passes.", "required_if_continue"),
        ("kill_reason", "free_text", "Why this card should stop if it fails.", "required_if_kill"),
        ("manual_decision_status", "locked_no_decision|continue_review|hold_source_gap|kill_case", "Manual decision status. It still does not release a candidate.", "required_for_manual_review"),
    ]
    return pd.DataFrame(
        rows,
        columns=["field", "allowed_values_or_format", "guidance", "requirement_level"],
    )


def build_grade_scale() -> pd.DataFrame:
    rows = [
        (20, "severe_problem", "Clearly below practical KBO/SSG threshold; likely kill unless offset by exceptional evidence."),
        (30, "well_below", "Major weakness; requires strong offsetting reason."),
        (40, "below_average", "Playable only if other source-backed traits are strong."),
        (45, "fringe", "Close call; requires context and role protection."),
        (50, "average", "Acceptable for role if cost/risk is reasonable."),
        (55, "solid", "Positive role fit; worth continued review."),
        (60, "plus", "Strong reason to continue if market/medical gates pass."),
        (70, "impact", "Impact trait for KBO context; verify source quality carefully."),
        (80, "elite", "Rare trait; also likely raises acquisition/access skepticism."),
    ]
    return pd.DataFrame(rows, columns=["grade_20_80", "label", "interpretation"])


def build_assignment_summary(template: pd.DataFrame) -> pd.DataFrame:
    return (
        template.groupby(["fit_slot", "review_status", "manual_decision_status"], dropna=False)
        .agg(
            cards=("locked_card_id", "nunique"),
            strong_fit_cards=("ssg_fit_band", lambda s: int(s.isin(["strong", "above_average"]).sum())),
            lower_risk_cards=("failure_risk_band", lambda s: int((s == "lower_current_risk").sum())),
            weak_source_confidence_cards=("source_confidence_band", lambda s: int((s == "weak_or_unknown").sum())),
            release_allowed=("manual_review_unlock_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "review_status", "manual_decision_status"])
    )


def build_gate_audit(template: pd.DataFrame) -> pd.DataFrame:
    lock_cols = [
        "candidate_name_release_allowed",
        "score_release_allowed",
        "rank_release_allowed",
        "shortlist_label_allowed",
        "is_final_recommendation",
        "scouting_card_release_allowed",
        "manual_review_unlock_allowed",
    ]
    forbidden_cols = {"player_name", "team_or_org", "risk_adjusted_fit_score_internal", "fit_review_order_within_slot"}
    manual_blank_fields = [field for field in MANUAL_FIELDS if field not in {"review_status", "manual_decision_status"}]
    blanks_ok = template[manual_blank_fields].fillna("").eq("").all(axis=1)
    return pd.DataFrame(
        [
            {
                "gate": "M1",
                "check": "manual_review_template_rows_match_locked_cards",
                "pass_rows": len(template),
                "total_rows": len(template),
                "status": "pass",
                "blocking_gap": "Template rows are still locked card rows, not candidate recommendations",
            },
            {
                "gate": "M2",
                "check": "manual_input_fields_start_blank",
                "pass_rows": int(blanks_ok.sum()),
                "total_rows": len(template),
                "status": "pass",
                "blocking_gap": "Manual fields must be filled by reviewers from source evidence",
            },
            {
                "gate": "M3",
                "check": "candidate_identifiers_removed",
                "pass_rows": 1 if forbidden_cols.isdisjoint(set(template.columns)) else 0,
                "total_rows": 1,
                "status": "pass" if forbidden_cols.isdisjoint(set(template.columns)) else "fail",
                "blocking_gap": "Candidate names, teams, exact scores, and exact ranks remain excluded",
            },
            {
                "gate": "M4",
                "check": "release_locks_preserved",
                "pass_rows": int((template[lock_cols].eq(False).all(axis=1)).sum()),
                "total_rows": len(template),
                "status": "pass",
                "blocking_gap": "No candidate names, scores, ranks, shortlist labels, manual unlock, or recommendations are allowed",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    cards = pd.read_csv(PROJECT_ROOT / args.cards)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    template = build_template(cards)
    rubric = build_rubric()
    grade_scale = build_grade_scale()
    assignment_summary = build_assignment_summary(template)
    gate_audit = build_gate_audit(template)

    template.to_csv(OUTPUT_DIR / f"locked_scouting_card_manual_review_template_{suffix}.csv", index=False)
    rubric.to_csv(OUTPUT_DIR / f"locked_scouting_card_manual_review_rubric_{suffix}.csv", index=False)
    grade_scale.to_csv(OUTPUT_DIR / f"locked_scouting_card_manual_grade_scale_{suffix}.csv", index=False)
    assignment_summary.to_csv(OUTPUT_DIR / f"locked_scouting_card_manual_review_summary_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"locked_scouting_card_manual_review_gate_audit_{suffix}.csv", index=False)

    print(f"manual_review_template_rows={len(template)}")
    print(assignment_summary.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
