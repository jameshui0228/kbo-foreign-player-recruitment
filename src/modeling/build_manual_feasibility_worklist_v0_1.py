#!/usr/bin/env python3
"""Build a manual source worklist for contract, salary, buyout, and willingness checks.

This layer is deliberately not a ranking. It translates the market-realism and
candidate-news tables into the next source lanes a scout/analyst should verify
before any candidate can be shortlisted.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT = PROJECT_ROOT / "outputs/tables/ssg_market_realism_news_join_v0_3.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

RELEASE_POLICY = "manual_feasibility_research_only_no_recommendation"


def text_contains(value: object, *needles: str) -> bool:
    text = "" if pd.isna(value) else str(value).lower()
    return any(needle.lower() in text for needle in needles)


def build_lanes(row: pd.Series) -> list[str]:
    lanes: list[str] = []
    slot = row["fit_slot"]
    status = str(row.get("market_realism_status", ""))
    contract_bucket = row.get("contract_control_bucket", "")
    medical_bucket = row.get("medical_risk_bucket", "")
    news_status = row.get("candidate_news_status", "")
    korean_rows = int(row.get("korean_article_rows", 0) or 0)

    in_priority_scope = status in {
        "manual_contact_priority_locked",
        "buyout_salary_agent_check_needed",
        "medical_hold_before_scouting",
        "contract_blocker_watch",
    }
    if not in_priority_scope:
        return lanes

    if korean_rows == 0:
        lanes.append("korean_news_naver_or_local_search")
    if slot in {"foreign_hitter", "foreign_pitcher"}:
        lanes.append("agent_korea_willingness_check")
        if text_contains(contract_bucket, "contract_blocker", "40man", "active_mlb"):
            lanes.append("mlb_contract_salary_option_check")
        if text_contains(row.get("run024_manual_check_flags", ""), "korea_willingness"):
            lanes.append("role_salary_kbo_cost_fit_check")
    if slot == "asian_quota":
        lanes.append("asian_league_contract_buyout_transfer_fee_check")
        lanes.append("passport_nationality_and_quota_eligibility_check")
        lanes.append("local_league_salary_agent_source_check")

    if text_contains(medical_bucket, "medical", "hold") or text_contains(news_status, "medical"):
        lanes.append("medical_file_and_recent_availability_check")
    if text_contains(news_status, "market_contract"):
        lanes.append("public_contract_market_news_review")
    if text_contains(news_status, "korea_or_overseas") or int(row.get("korea_willingness_article_rows", 0) or 0) > 0:
        lanes.append("korea_overseas_intent_context_review")

    return list(dict.fromkeys(lanes))


def priority_tier(lanes: list[str], row: pd.Series) -> str:
    if not lanes:
        return "not_in_manual_feasibility_scope"
    has_medical = "medical_file_and_recent_availability_check" in lanes
    has_contract = any("contract" in lane or "salary" in lane or "buyout" in lane for lane in lanes)
    has_willingness = any("willingness" in lane or "intent" in lane for lane in lanes)
    if has_medical and has_contract:
        return "tier_1_medical_and_contract_blocker"
    if has_contract and has_willingness:
        return "tier_1_contract_and_willingness_blocker"
    if len(lanes) >= 4:
        return "tier_2_multi_source_manual_check"
    return "tier_3_single_source_followup"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT)
    out = df.copy()
    out["manual_source_lanes_list"] = out.apply(build_lanes, axis=1)
    out["manual_source_lanes"] = out["manual_source_lanes_list"].map(lambda lanes: "|".join(lanes))
    out["manual_source_lane_count"] = out["manual_source_lanes_list"].map(len)
    out["manual_feasibility_priority_tier"] = out.apply(lambda row: priority_tier(row["manual_source_lanes_list"], row), axis=1)
    out["manual_feasibility_release_policy"] = RELEASE_POLICY
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False
    out["score_release_allowed"] = False

    drop_cols = ["manual_source_lanes_list"]
    out = out.drop(columns=[col for col in drop_cols if col in out.columns])
    out.to_csv(OUTPUT_DIR / "manual_feasibility_source_worklist_v0_1.csv", index=False)

    summary = (
        out.groupby(["fit_slot", "manual_feasibility_priority_tier"], dropna=False)
        .agg(
            rows=("fit_slot", "size"),
            unique_players=("player_name", "nunique"),
            avg_source_lanes=("manual_source_lane_count", "mean"),
            korean_news_missing_rows=("korean_article_rows", lambda s: int((pd.to_numeric(s, errors="coerce").fillna(0) == 0).sum())),
            medical_review_rows=("manual_source_lanes", lambda s: int(s.str.contains("medical_file", na=False).sum())),
            contract_review_rows=("manual_source_lanes", lambda s: int(s.str.contains("contract|salary|buyout", na=False).sum())),
        )
        .reset_index()
        .sort_values(["fit_slot", "manual_feasibility_priority_tier"])
    )
    summary["avg_source_lanes"] = summary["avg_source_lanes"].round(2)
    summary.to_csv(OUTPUT_DIR / "manual_feasibility_source_summary_v0_1.csv", index=False)

    lane_rows = []
    for lane, group in out[out["manual_source_lanes"].ne("")].assign(
        manual_source_lane=out["manual_source_lanes"].str.split("|", regex=False)
    ).explode("manual_source_lane").groupby("manual_source_lane"):
        lane_rows.append(
            {
                "manual_source_lane": lane,
                "rows": len(group),
                "unique_players": group["player_name"].nunique(),
                "foreign_hitter_rows": int(group["fit_slot"].eq("foreign_hitter").sum()),
                "foreign_pitcher_rows": int(group["fit_slot"].eq("foreign_pitcher").sum()),
                "asian_quota_rows": int(group["fit_slot"].eq("asian_quota").sum()),
            }
        )
    lane_summary = pd.DataFrame(lane_rows).sort_values(["rows", "manual_source_lane"], ascending=[False, True])
    lane_summary.to_csv(OUTPUT_DIR / "manual_feasibility_source_lane_summary_v0_1.csv", index=False)

    print(f"worklist_rows={len(out)}")
    print(f"manual_scope_rows={int(out['manual_source_lane_count'].gt(0).sum())}")
    print(summary.to_string(index=False))
    print(lane_summary.to_string(index=False))


if __name__ == "__main__":
    main()
