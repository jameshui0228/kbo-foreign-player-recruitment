#!/usr/bin/env python3
"""Build the Run 012 market coverage board."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"


def count_policy(df: pd.DataFrame, slot: str, policy: str) -> int:
    mask = df["slot"].eq(slot) & df["candidate_release_policy_v2"].eq(policy)
    return int(mask.sum())


def count_bucket(df: pd.DataFrame, slot: str, bucket: str) -> int:
    mask = df["slot"].eq(slot) & df["market_availability_bucket"].eq(bucket)
    return int(mask.sum())


def build_coverage() -> pd.DataFrame:
    market = pd.read_csv(OUT_DIR / "mlb_replacement_market_status_v1.csv")
    asian = pd.read_csv(OUT_DIR / "asian_quota_market_status_v1.csv")

    rows: list[dict] = []
    for slot in ["regular_foreign_pitcher", "regular_foreign_hitter_outfield_priority"]:
        slot_df = market[market["slot"].eq(slot)]
        rows.append(
            {
                "market_layer": "regular_foreign_replacement_market",
                "slot": slot,
                "market_scope": "MLB Savant 2025-2026 plus MLB roster and official transactions since 2025-10-01",
                "rows": len(slot_df),
                "secured_rows": len(slot_df),
                "research_lead_rows": count_policy(
                    market,
                    slot,
                    "research_lead_only_manual_check_required",
                ),
                "market_watch_rows": count_policy(market, slot, "market_watch_low_access")
                + count_policy(market, slot, "market_watch_manual_check_required"),
                "medical_hold_rows": count_policy(market, slot, "hold_medical_context_required"),
                "recent_release_or_dfa_rows": count_bucket(market, slot, "recently_released_or_dfa_high_access"),
                "nationality_pass_rows": 0,
                "nationality_unknown_rows": 0,
                "data_status": "secured_initial_not_candidate_release_ready",
                "primary_output": "outputs/tables/mlb_replacement_market_status_v1.csv",
                "blocking_gap": "needs contract/salary, current assignment, medical review, Korea-willingness, and manual scouting before name release",
            }
        )

    rows.append(
        {
            "market_layer": "injury_replacement_regular_foreign",
            "slot": "injury_replacement",
            "market_scope": "MLB official transactions: recent DFA/released/minor contract/option/injury movement",
            "rows": len(market),
            "secured_rows": int(
                market["market_availability_bucket"].isin(
                    [
                        "recently_released_or_dfa_high_access",
                        "minor_contract_or_outright_follow",
                        "optional_movement_watch",
                    ]
                ).sum()
            ),
            "research_lead_rows": int(
                market["candidate_release_policy_v2"].eq("research_lead_only_manual_check_required").sum()
            ),
            "market_watch_rows": int(market["candidate_release_policy_v2"].str.contains("market_watch").sum()),
            "medical_hold_rows": int(market["candidate_release_policy_v2"].eq("hold_medical_context_required").sum()),
            "recent_release_or_dfa_rows": int(market["market_availability_bucket"].eq("recently_released_or_dfa_high_access").sum()),
            "nationality_pass_rows": 0,
            "nationality_unknown_rows": 0,
            "data_status": "secured_initial_pool_only",
            "primary_output": "outputs/tables/mlb_transactions_latest.csv",
            "blocking_gap": "still needs non-MLB free agents, contract opt-outs, agent/team intent, and real-time medical/news confirmation",
        }
    )

    rows.append(
        {
            "market_layer": "asian_quota_market",
            "slot": "asian_quota",
            "market_scope": "NPB and CPBL official 2026 rosters; CPBL official nationality details; NPB non-official foreign nationality seed",
            "rows": len(asian),
            "secured_rows": len(asian),
            "research_lead_rows": 0,
            "market_watch_rows": len(asian),
            "medical_hold_rows": 0,
            "recent_release_or_dfa_rows": 0,
            "nationality_pass_rows": int(asian["asian_quota_nationality_gate"].eq("pass").sum()),
            "nationality_unknown_rows": int(asian["asian_quota_nationality_gate"].eq("unknown").sum()),
            "data_status": "secured_initial_not_candidate_release_ready",
            "primary_output": "outputs/tables/asian_quota_market_status_v1.csv",
            "blocking_gap": "needs NPB official nationality verification, ABL coverage, salary/buyout/contract feasibility, and manual availability checks",
        }
    )

    rows.extend(
        [
            {
                "market_layer": "article_full_text",
                "slot": "all",
                "market_scope": "Naver/news/interview text, injury and adaptation quotes",
                "rows": 0,
                "secured_rows": 0,
                "research_lead_rows": 0,
                "market_watch_rows": 0,
                "medical_hold_rows": 0,
                "recent_release_or_dfa_rows": 0,
                "nationality_pass_rows": 0,
                "nationality_unknown_rows": 0,
                "data_status": "partial_snippet_only",
                "primary_output": "outputs/tables/ssg_news_need_relevance_labeled.csv",
                "blocking_gap": "full article pages, interview quotes, source authority, and player-specific adaptation text not yet mined",
            },
            {
                "market_layer": "weather_park_context",
                "slot": "all",
                "market_scope": "Munhak weather, park factors, KBO ABS and game environment",
                "rows": 0,
                "secured_rows": 0,
                "research_lead_rows": 0,
                "market_watch_rows": 0,
                "medical_hold_rows": 0,
                "recent_release_or_dfa_rows": 0,
                "nationality_pass_rows": 0,
                "nationality_unknown_rows": 0,
                "data_status": "not_started",
                "primary_output": "",
                "blocking_gap": "needed for park/weather fit but not required before first market-screen table",
            },
        ]
    )
    return pd.DataFrame(rows)


def main() -> None:
    coverage = build_coverage()
    path = OUT_DIR / "candidate_market_coverage_v0_3.csv"
    coverage.to_csv(path, index=False)
    print(f"wrote {path} ({len(coverage)} rows)")


if __name__ == "__main__":
    main()
