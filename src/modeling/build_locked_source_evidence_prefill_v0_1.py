#!/usr/bin/env python3
"""Prefill locked source-evidence rows with public ID-based source URLs.

The output remains candidate-name-free. It uses internal player ids only to
build MLB/Savant source URLs and to attach existing article metadata to the
anonymous locked card ids.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
INTAKE = OUTPUT_DIR / "locked_source_evidence_intake_template_v0_1.csv"
SOURCE_PACKET = OUTPUT_DIR / "ssg_fit_source_fill_packet_v0_1.csv"

RELEASE_POLICY = "locked_source_evidence_prefill_no_candidate_name_no_score_no_rank"

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
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intake", default=str(INTAKE.relative_to(PROJECT_ROOT)))
    parser.add_argument("--source-packet", default=str(SOURCE_PACKET.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def locked_card_id(row: pd.Series) -> str:
    slot_prefix = {"foreign_hitter": "FH", "foreign_pitcher": "FP", "asian_quota": "AQ"}.get(row["fit_slot"], "XX")
    seed = "|".join(
        str(row.get(col, ""))
        for col in ["fit_slot", "source_fill_candidate_key", "player_id", "player_name", "team_or_org", "position_or_role"]
    )
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10].upper()
    return f"LOCKED-{slot_prefix}-{digest}"


def id_string(value: object) -> str:
    try:
        return str(int(float(value)))
    except (TypeError, ValueError):
        return ""


def statsapi_url(player_id: str, group: str) -> str:
    return f"https://statsapi.mlb.com/api/v1/people/{player_id}?hydrate=currentTeam,stats(group=[{group}],type=[yearByYear])"


def savant_url(player_id: str, player_type: str) -> str:
    return f"https://baseballsavant.mlb.com/statcast_search?player_type={player_type}&player_id={player_id}"


def split_links(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def split_titles(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def build_card_source_map(source_packet: pd.DataFrame) -> pd.DataFrame:
    packet = source_packet[source_packet["source_fill_readiness_bucket"].eq("source_supported_scouting_card_next_locked")].copy()
    packet["locked_card_id"] = packet.apply(locked_card_id, axis=1)
    packet["player_id_text"] = packet["player_id"].map(id_string)
    keep = [
        "locked_card_id",
        "fit_slot",
        "player_id_text",
        "top_candidate_news_links_source_fill",
        "top_candidate_news_titles_source_fill",
        "latest_candidate_news_date_source_fill",
        "contract_market_article_rows_source_fill",
        "injury_medical_article_rows_source_fill",
        "korea_willingness_article_rows_source_fill",
    ]
    return packet[[col for col in keep if col in packet.columns]].drop_duplicates("locked_card_id")


def prefill_official_source(row: pd.Series, card: pd.Series) -> dict[str, str] | None:
    player_id = str(card.get("player_id_text", ""))
    if not player_id:
        return None
    source_type = str(row["source_type"])
    fit_slot = str(row["fit_slot"])
    if source_type == "current_stat_page":
        group = "pitching" if fit_slot == "foreign_pitcher" else "hitting,fielding"
        return {
            "source_url": statsapi_url(player_id, group),
            "source_title": "MLB Stats API player endpoint by MLBAM id",
            "source_publisher": "MLB Stats API",
            "source_language": "en",
            "source_evidence_strength": "primary",
            "extracted_value_or_claim": "Official player id endpoint available for current stat baseline; reviewer must verify snapshot.",
            "supports_or_blocks": "context_only",
            "reviewer_notes": "Auto-prefilled from MLBAM id; human review still required.",
        }
    if source_type == "transaction_or_roster_status_source":
        return {
            "source_url": statsapi_url(player_id, "pitching"),
            "source_title": "MLB Stats API current-team roster context by MLBAM id",
            "source_publisher": "MLB Stats API",
            "source_language": "en",
            "source_evidence_strength": "primary",
            "extracted_value_or_claim": "Official endpoint can verify current-team context; reviewer must check transaction/access status.",
            "supports_or_blocks": "context_only",
            "reviewer_notes": "Auto-prefilled from MLBAM id; human review still required.",
        }
    if source_type == "workload_starter_runway_source" and fit_slot == "foreign_pitcher":
        return {
            "source_url": savant_url(player_id, "pitcher"),
            "source_title": "Baseball Savant statcast search by MLBAM id",
            "source_publisher": "Baseball Savant",
            "source_language": "en",
            "source_evidence_strength": "primary",
            "extracted_value_or_claim": "Statcast source can support workload/starter-runway review; reviewer must extract role and usage evidence.",
            "supports_or_blocks": "context_only",
            "reviewer_notes": "Auto-prefilled from MLBAM id; human review still required.",
        }
    if source_type == "of_dh_role_and_defense_source" and fit_slot == "foreign_hitter":
        return {
            "source_url": statsapi_url(player_id, "fielding"),
            "source_title": "MLB Stats API fielding context by MLBAM id",
            "source_publisher": "MLB Stats API",
            "source_language": "en",
            "source_evidence_strength": "primary",
            "extracted_value_or_claim": "Official endpoint can support OF/DH role and defense-source review; reviewer must verify role context.",
            "supports_or_blocks": "context_only",
            "reviewer_notes": "Auto-prefilled from MLBAM id; human review still required.",
        }
    return None


def article_prefill(row: pd.Series, card: pd.Series) -> dict[str, str] | None:
    source_type = str(row["source_type"])
    links = split_links(card.get("top_candidate_news_links_source_fill", ""))
    titles = split_titles(card.get("top_candidate_news_titles_source_fill", ""))
    if not links:
        return None
    contract_rows = int(float(card.get("contract_market_article_rows_source_fill", 0) or 0))
    medical_rows = int(float(card.get("injury_medical_article_rows_source_fill", 0) or 0))
    korea_rows = int(float(card.get("korea_willingness_article_rows_source_fill", 0) or 0))
    allowed = (
        (source_type == "contract_access_source" and contract_rows > 0)
        or (source_type == "medical_current_status_source" and medical_rows > 0)
        or (source_type == "korea_or_overseas_willingness_source_if_available" and korea_rows > 0)
    )
    if not allowed:
        return None
    return {
        "source_url": links[0],
        "source_title": titles[0] if titles else "Candidate article metadata link",
        "source_date": str(card.get("latest_candidate_news_date_source_fill", "") or ""),
        "source_publisher": "article_metadata",
        "source_language": "unknown",
        "source_evidence_strength": "secondary",
        "extracted_value_or_claim": f"Article metadata suggests {source_type}; reviewer must open and verify claim.",
        "supports_or_blocks": "context_only",
        "reviewer_notes": "Auto-prefilled from prior candidate-news metadata; human review still required.",
    }


def apply_prefill(intake: pd.DataFrame, source_map: pd.DataFrame) -> pd.DataFrame:
    source_by_card = source_map.set_index("locked_card_id").to_dict("index")
    out = intake.copy()
    text_cols = [
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
        "source_release_policy",
    ]
    for col in text_cols:
        if col in out.columns:
            out[col] = out[col].fillna("").astype(str)
    out["source_intake_status"] = out["source_intake_status"].fillna("not_started_locked")
    out["prefill_method"] = ""
    for idx, row in out.iterrows():
        card = source_by_card.get(row["locked_card_id"])
        if not card:
            continue
        update = prefill_official_source(row, pd.Series(card))
        method = "official_id_source"
        if update is None:
            update = article_prefill(row, pd.Series(card))
            method = "article_metadata_source"
        if update is None:
            continue
        for key, value in update.items():
            out.at[idx, key] = value
        out.at[idx, "source_intake_status"] = "prefilled_needs_human_review"
        out.at[idx, "reviewed_by"] = "automation_prefill"
        out.at[idx, "reviewed_date"] = "2026-06-22"
        out.at[idx, "source_release_policy"] = RELEASE_POLICY
        out.at[idx, "prefill_method"] = method
    return out


def build_summary(prefilled: pd.DataFrame) -> pd.DataFrame:
    return (
        prefilled.groupby(["fit_slot", "source_type", "source_intake_status"], dropna=False)
        .agg(
            rows=("locked_card_id", "size"),
            cards=("locked_card_id", "nunique"),
            url_filled_rows=("source_url", lambda s: int(s.fillna("").ne("").sum())),
            release_allowed=("candidate_name_release_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "source_type", "source_intake_status"])
    )


def build_readiness(prefilled: pd.DataFrame) -> pd.DataFrame:
    summary = (
        prefilled.groupby(["fit_slot", "locked_card_id"], dropna=False)
        .agg(
            required_source_rows=("source_type", "size"),
            filled_source_rows=("source_url", lambda s: int(s.fillna("").ne("").sum())),
            contract_filled=("source_type", lambda s: 0),
        )
        .reset_index()
    )
    contract = prefilled[prefilled["source_type"].eq("contract_access_source")].groupby("locked_card_id")["source_url"].apply(
        lambda s: int(s.fillna("").ne("").any())
    )
    medical = prefilled[prefilled["source_type"].eq("medical_current_status_source")].groupby("locked_card_id")["source_url"].apply(
        lambda s: int(s.fillna("").ne("").any())
    )
    stat = prefilled[prefilled["source_type"].eq("current_stat_page")].groupby("locked_card_id")["source_url"].apply(
        lambda s: int(s.fillna("").ne("").any())
    )
    for name, series in [("contract_filled", contract), ("medical_filled", medical), ("stat_filled", stat)]:
        summary[name] = summary["locked_card_id"].map(series).fillna(0).astype(int)
    summary["source_fill_rate"] = summary["filled_source_rows"] / summary["required_source_rows"].replace(0, pd.NA)
    summary["readiness_band"] = pd.cut(
        summary["source_fill_rate"].fillna(0),
        bins=[-0.01, 0.0, 0.34, 0.67, 1.0],
        labels=["no_sources", "thin_prefill", "partial_prefill", "source_complete"],
    ).astype(str)
    return (
        summary.groupby(["fit_slot", "readiness_band"], dropna=False)
        .agg(
            cards=("locked_card_id", "nunique"),
            median_source_fill_rate=("source_fill_rate", "median"),
            stat_filled_cards=("stat_filled", "sum"),
            contract_filled_cards=("contract_filled", "sum"),
            medical_filled_cards=("medical_filled", "sum"),
        )
        .reset_index()
        .sort_values(["fit_slot", "readiness_band"])
    )


def build_gate_audit(prefilled: pd.DataFrame, intake: pd.DataFrame) -> pd.DataFrame:
    forbidden_present = FORBIDDEN_COLUMNS.intersection(prefilled.columns)
    locks_ok = prefilled[LOCK_COLS].eq(False).all(axis=1)
    filled = prefilled["source_url"].fillna("").ne("")
    return pd.DataFrame(
        [
            {
                "gate": "P1",
                "check": "prefill_rows_match_intake_rows",
                "pass_rows": len(prefilled),
                "total_rows": len(intake),
                "status": "pass" if len(prefilled) == len(intake) else "fail",
                "blocking_gap": "Prefill is source evidence work, not candidate release",
            },
            {
                "gate": "P2",
                "check": "source_urls_prefilled",
                "pass_rows": int(filled.sum()),
                "total_rows": len(prefilled),
                "status": "pass_visible_gap",
                "blocking_gap": "Remaining blank source rows still need human source collection",
            },
            {
                "gate": "P3",
                "check": "candidate_identifiers_and_exact_scores_removed",
                "pass_rows": 1 if not forbidden_present else 0,
                "total_rows": 1,
                "status": "pass" if not forbidden_present else "fail",
                "blocking_gap": "Candidate names, teams, exact scores, and exact ranks remain excluded",
            },
            {
                "gate": "P4",
                "check": "release_locks_preserved",
                "pass_rows": int(locks_ok.sum()),
                "total_rows": len(prefilled),
                "status": "pass" if locks_ok.all() else "fail",
                "blocking_gap": "No candidate names, ranks, scores, shortlist labels, manual unlock labels, or recommendations are released",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    intake = pd.read_csv(PROJECT_ROOT / args.intake)
    source_packet = pd.read_csv(PROJECT_ROOT / args.source_packet)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    source_map = build_card_source_map(source_packet)
    prefilled = apply_prefill(intake, source_map)
    summary = build_summary(prefilled)
    readiness = build_readiness(prefilled)
    gate_audit = build_gate_audit(prefilled, intake)

    prefilled.to_csv(OUTPUT_DIR / f"locked_source_evidence_prefill_template_{suffix}.csv", index=False)
    summary.to_csv(OUTPUT_DIR / f"locked_source_evidence_prefill_summary_{suffix}.csv", index=False)
    readiness.to_csv(OUTPUT_DIR / f"layer5_6_source_readiness_recalibration_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"locked_source_evidence_prefill_gate_audit_{suffix}.csv", index=False)

    print(f"prefill_rows={len(prefilled)}")
    print(f"filled_source_url_rows={int(prefilled['source_url'].fillna('').ne('').sum())}")
    print(summary.to_string(index=False))
    print(readiness.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
