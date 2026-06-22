#!/usr/bin/env python3
"""Build a locked source-rebuild packet for manual scouting cards.

This artifact is candidate-name-free. It converts the locked assignment queue
into concrete source bundles and done definitions before any manual scouting
grade, candidate unlock, shortlist label, or recommendation is allowed.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
ASSIGNMENT_QUEUE = OUTPUT_DIR / "locked_manual_review_assignment_queue_v0_1.csv"

RELEASE_POLICY = "locked_source_rebuild_packet_no_candidate_name_no_score_no_rank"

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
    parser.add_argument("--assignment-queue", default=str(ASSIGNMENT_QUEUE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def rebuild_priority(row: pd.Series) -> str:
    wave = str(row.get("review_wave", ""))
    source_need = str(row.get("source_search_intensity", ""))
    if wave == "wave_1_evidence_read_now":
        return "P0_read_existing_source_now"
    if source_need == "cold_start_source_build" and wave.startswith("wave_1"):
        return "P1_rebuild_source_file_before_video"
    if wave.startswith("wave_2"):
        return "P2_hold_until_core_source_file_exists"
    return "P3_defer_locked"


def required_bundle(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    if slot == "foreign_hitter":
        return "|".join(
            [
                "current_stat_page",
                "recent_video_or_scouting_report",
                "contract_access_source",
                "medical_current_status_source",
                "of_dh_role_and_defense_source",
                "korea_or_overseas_willingness_source_if_available",
            ]
        )
    if slot == "foreign_pitcher":
        return "|".join(
            [
                "current_stat_page",
                "recent_video_or_scouting_report",
                "transaction_or_roster_status_source",
                "workload_starter_runway_source",
                "medical_current_status_source",
                "contract_access_source",
                "korea_or_overseas_willingness_source_if_available",
            ]
        )
    return "|".join(
        [
            "passport_or_nationality_source",
            "current_stat_page",
            "contract_transfer_buyout_source",
            "medical_current_status_source",
            "role_willingness_source",
        ]
    )


def public_search_templates(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    base = [
        "[internal_card_name] stats 2026",
        "[internal_card_name] video 2026",
        "[internal_card_name] contract option salary",
        "[internal_card_name] injury rehab availability",
    ]
    if slot == "foreign_pitcher":
        base.extend(
            [
                "[internal_card_name] starter workload pitch count",
                "[internal_card_name] transaction roster status",
            ]
        )
    elif slot == "foreign_hitter":
        base.extend(
            [
                "[internal_card_name] outfield defense role",
                "[internal_card_name] platoon contact strikeout",
            ]
        )
    else:
        base.extend(
            [
                "[internal_card_name] passport nationality",
                "[internal_card_name] transfer fee buyout",
            ]
        )
    return "|".join(base)


def stat_video_done_definition(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    if slot == "foreign_pitcher":
        return "Attach one stat page, one recent video/report, one workload/role source, and note starter or multi-inning runway."
    if slot == "foreign_hitter":
        return "Attach one stat page, one recent video/report, and note contact floor plus OF/DH role evidence."
    return "Attach one stat page, one league-context source, and one role evidence source."


def feasibility_done_definition(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    if slot == "asian_quota":
        return "Verify passport/nationality, contract, transfer fee or buyout, medical status, and role willingness."
    return "Verify contract/access, current roster or transaction status, medical availability, and Korea/overseas openness if available."


def manual_unlock_minimum(row: pd.Series) -> str:
    slot = str(row.get("fit_slot", ""))
    if slot == "foreign_pitcher":
        return "|".join(
            [
                "stat_source_url_1",
                "video_source_url_1",
                "contract_source_url",
                "medical_source_url",
                "primary_tool_grade_20_80",
                "command_or_contact_grade_20_80",
                "defense_or_workload_grade_20_80",
                "medical_availability_grade_20_80",
                "reviewer_summary",
                "continue_or_kill_reason",
            ]
        )
    if slot == "foreign_hitter":
        return "|".join(
            [
                "stat_source_url_1",
                "video_source_url_1",
                "contract_source_url",
                "medical_source_url",
                "primary_tool_grade_20_80",
                "command_or_contact_grade_20_80",
                "defense_or_workload_grade_20_80",
                "translation_confidence_20_80",
                "reviewer_summary",
                "continue_or_kill_reason",
            ]
        )
    return "|".join(
        [
            "stat_source_url_1",
            "contract_source_url",
            "medical_source_url",
            "korea_willingness_source_url",
            "contract_feasibility_grade_20_80",
            "korea_willingness_grade_20_80",
            "reviewer_summary",
            "continue_or_kill_reason",
        ]
    )


def source_rebuild_lane(row: pd.Series) -> str:
    lane = str(row.get("review_lane", ""))
    if lane == "contract_access_check":
        return "targeted_contract_access_read"
    if lane == "pitcher_source_and_workload_rebuild":
        return "pitcher_full_source_file_rebuild"
    if lane == "source_rebuild_before_video":
        return "hitter_full_source_file_rebuild"
    return "general_locked_source_file_rebuild"


def build_packet(queue: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "locked_card_id",
        "fit_slot",
        "card_title",
        "review_wave",
        "review_lane",
        "source_search_intensity",
        "first_reviewer_role",
        "second_reviewer_role",
        "evidence_gap_statement",
        "kill_switch_question",
        "manual_fields_to_complete_first",
        "ssg_fit_band",
        "translation_band",
        "market_realism_band",
        "failure_risk_band",
        "source_confidence_band",
        "primary_risk_focus",
        "usable_article_rows_band",
        "korean_article_rows_band",
    ]
    packet = queue[[col for col in keep if col in queue.columns]].copy()
    packet["source_rebuild_priority"] = packet.apply(rebuild_priority, axis=1)
    packet["source_rebuild_lane"] = packet.apply(source_rebuild_lane, axis=1)
    packet["source_file_status"] = "not_started_locked"
    packet["required_source_bundle"] = packet.apply(required_bundle, axis=1)
    packet["public_search_templates"] = packet.apply(public_search_templates, axis=1)
    packet["stat_video_done_definition"] = packet.apply(stat_video_done_definition, axis=1)
    packet["feasibility_done_definition"] = packet.apply(feasibility_done_definition, axis=1)
    packet["manual_unlock_minimum_fields"] = packet.apply(manual_unlock_minimum, axis=1)
    packet["source_rebuild_release_policy"] = RELEASE_POLICY
    packet["candidate_name_release_allowed"] = False
    packet["score_release_allowed"] = False
    packet["rank_release_allowed"] = False
    packet["shortlist_label_allowed"] = False
    packet["is_final_recommendation"] = False
    packet["scouting_card_release_allowed"] = False
    packet["manual_review_unlock_allowed"] = False
    packet["recommendation_label"] = "locked_not_allowed"
    return packet.sort_values(["source_rebuild_priority", "fit_slot", "source_rebuild_lane", "locked_card_id"])


def build_summary(packet: pd.DataFrame) -> pd.DataFrame:
    return (
        packet.groupby(["source_rebuild_priority", "fit_slot", "source_rebuild_lane"], dropna=False)
        .agg(
            cards=("locked_card_id", "nunique"),
            cold_start_cards=("source_search_intensity", lambda s: int((s == "cold_start_source_build").sum())),
            existing_source_cards=("source_search_intensity", lambda s: int((s == "existing_source_review").sum())),
            lower_risk_cards=("failure_risk_band", lambda s: int((s == "lower_current_risk").sum())),
            strong_or_above_fit_cards=("ssg_fit_band", lambda s: int(s.isin(["strong", "above_average"]).sum())),
            release_allowed=("manual_review_unlock_allowed", "any"),
        )
        .reset_index()
        .sort_values(["source_rebuild_priority", "fit_slot", "source_rebuild_lane"])
    )


def build_bundle_matrix(packet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in packet.iterrows():
        for source_type in str(row["required_source_bundle"]).split("|"):
            rows.append(
                {
                    "locked_card_id": row["locked_card_id"],
                    "fit_slot": row["fit_slot"],
                    "source_rebuild_priority": row["source_rebuild_priority"],
                    "source_type": source_type,
                    "required": True,
                    "source_status": "not_started_locked",
                    "release_allowed": False,
                }
            )
    matrix = pd.DataFrame(rows)
    return (
        matrix.groupby(["fit_slot", "source_rebuild_priority", "source_type"], dropna=False)
        .agg(
            cards=("locked_card_id", "nunique"),
            source_rows=("source_type", "size"),
            required=("required", "all"),
            release_allowed=("release_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "source_rebuild_priority", "source_type"])
    )


def build_checklist() -> pd.DataFrame:
    rows = [
        ("current_stat_page", "Attach official/minor-league/stat provider URL and snapshot date."),
        ("recent_video_or_scouting_report", "Attach one recent video or scouting report and note date/context."),
        ("contract_access_source", "Attach evidence for salary, option, buyout, club control, or agent/access uncertainty."),
        ("medical_current_status_source", "Attach source for injury, rehab, workload interruption, IL, or current availability."),
        ("transaction_or_roster_status_source", "Attach roster/transaction status and whether movement is plausible."),
        ("workload_starter_runway_source", "For pitchers, attach recent IP, starts, pitch count, role, or ramp-up evidence."),
        ("of_dh_role_and_defense_source", "For hitters, attach OF/DH role, defense, run value, or platoon context evidence."),
        ("korea_or_overseas_willingness_source_if_available", "Attach Korea/overseas openness, agent posture, role acceptance, or local-context source if available."),
        ("passport_or_nationality_source", "For Asian-quota work, attach passport/nationality eligibility evidence."),
        ("contract_transfer_buyout_source", "For Asian-quota work, attach transfer fee, buyout, salary, or club-control source."),
        ("role_willingness_source", "Attach role acceptance and realistic usage-context source."),
    ]
    return pd.DataFrame(rows, columns=["source_type", "check_instruction"])


def build_gate_audit(packet: pd.DataFrame, queue: pd.DataFrame) -> pd.DataFrame:
    forbidden_present = FORBIDDEN_COLUMNS.intersection(packet.columns)
    locks_ok = packet[LOCK_COLS].eq(False).all(axis=1)
    return pd.DataFrame(
        [
            {
                "gate": "R1",
                "check": "source_rebuild_packet_rows_match_assignment_queue",
                "pass_rows": len(packet),
                "total_rows": len(queue),
                "status": "pass" if len(packet) == len(queue) else "fail",
                "blocking_gap": "Packet is anonymous source work, not a candidate release",
            },
            {
                "gate": "R2",
                "check": "candidate_identifiers_and_exact_scores_removed",
                "pass_rows": 1 if not forbidden_present else 0,
                "total_rows": 1,
                "status": "pass" if not forbidden_present else "fail",
                "blocking_gap": "Candidate names, teams, exact scores, and exact ranks remain excluded",
            },
            {
                "gate": "R3",
                "check": "release_locks_preserved",
                "pass_rows": int(locks_ok.sum()),
                "total_rows": len(packet),
                "status": "pass" if locks_ok.all() else "fail",
                "blocking_gap": "No candidate names, ranks, scores, shortlist labels, manual unlock labels, or recommendations are released",
            },
            {
                "gate": "R4",
                "check": "source_file_status_not_started",
                "pass_rows": int(packet["source_file_status"].eq("not_started_locked").sum()),
                "total_rows": len(packet),
                "status": "pass",
                "blocking_gap": "Source files still need reviewer-filled URLs and evidence before manual unlock",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    queue = pd.read_csv(PROJECT_ROOT / args.assignment_queue)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    packet = build_packet(queue)
    summary = build_summary(packet)
    bundle_matrix = build_bundle_matrix(packet)
    checklist = build_checklist()
    gate_audit = build_gate_audit(packet, queue)

    packet.to_csv(OUTPUT_DIR / f"locked_source_rebuild_packet_{suffix}.csv", index=False)
    summary.to_csv(OUTPUT_DIR / f"locked_source_rebuild_summary_{suffix}.csv", index=False)
    bundle_matrix.to_csv(OUTPUT_DIR / f"locked_source_rebuild_bundle_matrix_{suffix}.csv", index=False)
    checklist.to_csv(OUTPUT_DIR / f"locked_source_rebuild_checklist_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"locked_source_rebuild_gate_audit_{suffix}.csv", index=False)

    print(f"source_rebuild_packet_rows={len(packet)}")
    print(summary.to_string(index=False))
    print(bundle_matrix.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
