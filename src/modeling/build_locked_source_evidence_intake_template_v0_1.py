#!/usr/bin/env python3
"""Build a row-level source evidence intake template.

The template stays candidate-name-free. Each row is one anonymous card and one
required source type, so reviewers can fill URLs, extracted values, and evidence
quality before any manual unlock decision.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
SOURCE_PACKET = OUTPUT_DIR / "locked_source_rebuild_packet_v0_1.csv"

RELEASE_POLICY = "locked_source_evidence_intake_no_candidate_name_no_score_no_rank"

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


SOURCE_TO_MANUAL_FIELD = {
    "current_stat_page": "stat_source_url_1",
    "recent_video_or_scouting_report": "video_source_url_1",
    "contract_access_source": "contract_source_url",
    "medical_current_status_source": "medical_source_url",
    "of_dh_role_and_defense_source": "video_source_url_2",
    "transaction_or_roster_status_source": "stat_source_url_2",
    "workload_starter_runway_source": "stat_source_url_2",
    "korea_or_overseas_willingness_source_if_available": "korea_willingness_source_url",
    "passport_or_nationality_source": "korea_willingness_source_url",
    "contract_transfer_buyout_source": "contract_source_url",
    "role_willingness_source": "korea_willingness_source_url",
}


SOURCE_REVIEW_QUESTION = {
    "current_stat_page": "Does this source verify the current stat/role baseline and snapshot date?",
    "recent_video_or_scouting_report": "Does this source show current tools, role, or scouting traits rather than old reputation?",
    "contract_access_source": "Does this source clarify salary, option, buyout, club control, agent, or access feasibility?",
    "medical_current_status_source": "Does this source clarify injury, rehab, IL, workload interruption, or current availability?",
    "of_dh_role_and_defense_source": "Does this source clarify OF/DH role, defense, running, or platoon usability?",
    "transaction_or_roster_status_source": "Does this source verify current roster, transaction, option, or movement plausibility?",
    "workload_starter_runway_source": "Does this source verify recent workload, starter runway, pitch count, or multi-inning role?",
    "korea_or_overseas_willingness_source_if_available": "Does this source indicate Korea/overseas openness, role acceptance, or agent posture?",
    "passport_or_nationality_source": "Does this source verify passport/nationality eligibility?",
    "contract_transfer_buyout_source": "Does this source clarify transfer fee, buyout, salary, or club-control blocker?",
    "role_willingness_source": "Does this source clarify realistic role willingness and usage fit?",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-packet", default=str(SOURCE_PACKET.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def build_intake(packet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in packet.iterrows():
        source_types = str(row["required_source_bundle"]).split("|")
        for source_type in source_types:
            rows.append(
                {
                    "locked_card_id": row["locked_card_id"],
                    "fit_slot": row["fit_slot"],
                    "source_rebuild_priority": row["source_rebuild_priority"],
                    "source_rebuild_lane": row["source_rebuild_lane"],
                    "source_type": source_type,
                    "required_source": True,
                    "source_intake_status": "not_started_locked",
                    "target_manual_field": SOURCE_TO_MANUAL_FIELD.get(source_type, "reviewer_summary"),
                    "review_question": SOURCE_REVIEW_QUESTION.get(source_type, "Does this source materially affect the card?"),
                    "source_url": "",
                    "source_title": "",
                    "source_date": "",
                    "source_publisher": "",
                    "source_language": "",
                    "source_evidence_strength": "",
                    "extracted_value_or_claim": "",
                    "supports_or_blocks": "",
                    "reviewer_notes": "",
                    "reviewed_by": "",
                    "reviewed_date": "",
                    "source_release_policy": RELEASE_POLICY,
                    "candidate_name_release_allowed": False,
                    "score_release_allowed": False,
                    "rank_release_allowed": False,
                    "shortlist_label_allowed": False,
                    "is_final_recommendation": False,
                    "scouting_card_release_allowed": False,
                    "manual_review_unlock_allowed": False,
                    "recommendation_label": "locked_not_allowed",
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["source_rebuild_priority", "fit_slot", "source_rebuild_lane", "locked_card_id", "source_type"]
    )


def build_summary(intake: pd.DataFrame) -> pd.DataFrame:
    return (
        intake.groupby(["fit_slot", "source_rebuild_priority", "source_type"], dropna=False)
        .agg(
            required_rows=("locked_card_id", "size"),
            cards=("locked_card_id", "nunique"),
            not_started_rows=("source_intake_status", lambda s: int((s == "not_started_locked").sum())),
            url_filled_rows=("source_url", lambda s: int(s.fillna("").ne("").sum())),
            release_allowed=("manual_review_unlock_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "source_rebuild_priority", "source_type"])
    )


def build_manual_field_map(intake: pd.DataFrame) -> pd.DataFrame:
    return (
        intake.groupby(["fit_slot", "source_type", "target_manual_field"], dropna=False)
        .agg(required_rows=("locked_card_id", "size"), cards=("locked_card_id", "nunique"))
        .reset_index()
        .sort_values(["fit_slot", "source_type", "target_manual_field"])
    )


def build_rubric() -> pd.DataFrame:
    rows = [
        ("source_url", "url", "Reviewer must paste the source URL used for the claim."),
        ("source_title", "free_text", "Source title or page label."),
        ("source_date", "yyyy-mm-dd_or_source_date_text", "Publication or snapshot date; source date text is allowed if exact date is unclear."),
        ("source_publisher", "free_text", "Publisher, league site, transaction page, stat provider, outlet, or report owner."),
        ("source_language", "ko|en|ja|zh|other|unknown", "Language of the source."),
        ("source_evidence_strength", "primary|secondary|weak|conflicting|unusable", "Primary means direct and current; weak means snippet/indirect/old."),
        ("extracted_value_or_claim", "free_text", "Exact value, status, or claim taken from the source."),
        ("supports_or_blocks", "supports|blocks|mixed|context_only|unknown", "Whether this evidence supports or blocks continued review."),
        ("reviewer_notes", "free_text", "Short reviewer interpretation."),
        ("reviewed_by", "free_text", "Reviewer initials or name."),
        ("reviewed_date", "yyyy-mm-dd", "Date the source row was reviewed."),
    ]
    return pd.DataFrame(rows, columns=["field", "allowed_values_or_format", "guidance"])


def build_gate_audit(intake: pd.DataFrame, packet: pd.DataFrame) -> pd.DataFrame:
    forbidden_present = FORBIDDEN_COLUMNS.intersection(intake.columns)
    locks_ok = intake[LOCK_COLS].eq(False).all(axis=1)
    blank_cols = [
        "source_url",
        "source_title",
        "source_date",
        "source_publisher",
        "source_language",
        "source_evidence_strength",
        "extracted_value_or_claim",
        "supports_or_blocks",
        "reviewer_notes",
        "reviewed_by",
        "reviewed_date",
    ]
    blanks_ok = intake[blank_cols].fillna("").eq("").all(axis=1)
    expected_rows = sum(len(str(bundle).split("|")) for bundle in packet["required_source_bundle"])
    return pd.DataFrame(
        [
            {
                "gate": "I1",
                "check": "intake_rows_match_required_source_bundle",
                "pass_rows": len(intake),
                "total_rows": expected_rows,
                "status": "pass" if len(intake) == expected_rows else "fail",
                "blocking_gap": "Rows are source intake tasks, not candidate releases",
            },
            {
                "gate": "I2",
                "check": "candidate_identifiers_and_exact_scores_removed",
                "pass_rows": 1 if not forbidden_present else 0,
                "total_rows": 1,
                "status": "pass" if not forbidden_present else "fail",
                "blocking_gap": "Candidate names, teams, exact scores, and exact ranks remain excluded",
            },
            {
                "gate": "I3",
                "check": "source_input_fields_start_blank",
                "pass_rows": int(blanks_ok.sum()),
                "total_rows": len(intake),
                "status": "pass" if blanks_ok.all() else "fail",
                "blocking_gap": "Reviewers must fill URLs, titles, dates, claims, and notes from source evidence",
            },
            {
                "gate": "I4",
                "check": "release_locks_preserved",
                "pass_rows": int(locks_ok.sum()),
                "total_rows": len(intake),
                "status": "pass" if locks_ok.all() else "fail",
                "blocking_gap": "No candidate names, ranks, scores, shortlist labels, manual unlock labels, or recommendations are released",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    packet = pd.read_csv(PROJECT_ROOT / args.source_packet)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    intake = build_intake(packet)
    summary = build_summary(intake)
    manual_field_map = build_manual_field_map(intake)
    rubric = build_rubric()
    gate_audit = build_gate_audit(intake, packet)

    intake.to_csv(OUTPUT_DIR / f"locked_source_evidence_intake_template_{suffix}.csv", index=False)
    summary.to_csv(OUTPUT_DIR / f"locked_source_evidence_intake_summary_{suffix}.csv", index=False)
    manual_field_map.to_csv(OUTPUT_DIR / f"locked_source_evidence_manual_field_map_{suffix}.csv", index=False)
    rubric.to_csv(OUTPUT_DIR / f"locked_source_evidence_intake_rubric_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"locked_source_evidence_intake_gate_audit_{suffix}.csv", index=False)

    print(f"source_evidence_intake_rows={len(intake)}")
    print(summary.to_string(index=False))
    print(manual_field_map.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
