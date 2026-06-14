#!/usr/bin/env python3
"""Attach recent MLB transaction signals to current candidate pools.

The output is deliberately a market-research table. It should not be treated as
a recommendation list until contract, medical, willingness, and KBO translation
gates are separately passed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"
TRANSACTIONS = OUT_DIR / "mlb_transactions_latest.csv"
PITCHER_POOL = OUT_DIR / "mlb_pitcher_availability_candidate_pool_v1.csv"
HITTER_POOL = OUT_DIR / "mlb_outfielder_availability_candidate_pool_v1.csv"

RECENT_CUTOFF = pd.Timestamp("2026-03-01")


def join_unique(values: pd.Series, max_items: int = 5) -> str:
    cleaned = [str(value).strip() for value in values.dropna().unique() if str(value).strip()]
    if not cleaned:
        return ""
    if len(cleaned) > max_items:
        return " | ".join(cleaned[:max_items]) + f" | +{len(cleaned) - max_items}"
    return " | ".join(cleaned)


def safe_bool(series: pd.Series) -> pd.Series:
    return series.astype("boolean").fillna(False).astype(bool)


def load_candidates() -> pd.DataFrame:
    pitcher = pd.read_csv(PITCHER_POOL)
    hitter = pd.read_csv(HITTER_POOL)
    df = pd.concat([pitcher, hitter], ignore_index=True, sort=False)
    df["player_id"] = pd.to_numeric(df["player_id"], errors="coerce").astype("Int64")
    return df


def add_recent_flags(tx: pd.DataFrame) -> pd.DataFrame:
    out = tx.copy()
    out["player_id"] = pd.to_numeric(out["player_id"], errors="coerce").astype("Int64")
    out["transaction_date"] = pd.to_datetime(out["date"], errors="coerce")
    for column in out.columns:
        if column.endswith("_flag"):
            out[column] = safe_bool(out[column])
    out["recent_window_flag"] = out["transaction_date"].ge(RECENT_CUTOFF)
    out["transaction_line"] = (
        out["date"].fillna("")
        + " "
        + out["type_code"].fillna("")
        + ": "
        + out["description"].fillna("")
    )
    return out


def summarize_transactions(tx: pd.DataFrame) -> pd.DataFrame:
    flag_columns = [column for column in tx.columns if column.endswith("_flag")]
    latest = (
        tx.sort_values(["player_id", "transaction_date", "transaction_id"], na_position="last")
        .groupby("player_id", dropna=False)
        .tail(1)
        .set_index("player_id")
    )

    records = []
    for player_id, group in tx.groupby("player_id", dropna=False):
        recent = group[group["recent_window_flag"]].copy()
        row = {
            "player_id": player_id,
            "transaction_count_since_20251001": len(group),
            "recent_transaction_count_since_20260301": len(recent),
            "latest_transaction_date": latest.loc[player_id, "date"] if player_id in latest.index else np.nan,
            "latest_transaction_type_code": latest.loc[player_id, "type_code"] if player_id in latest.index else "",
            "latest_transaction_type_desc": latest.loc[player_id, "type_desc"] if player_id in latest.index else "",
            "latest_transaction_description": latest.loc[player_id, "description"] if player_id in latest.index else "",
            "transaction_type_codes": join_unique(group["type_code"]),
            "recent_transaction_timeline": join_unique(recent.sort_values("transaction_date", ascending=False)["transaction_line"]),
        }
        for column in flag_columns:
            row[column] = bool(group[column].max())
            row[f"recent_{column}"] = bool(recent[column].max()) if not recent.empty else False
        records.append(row)
    return pd.DataFrame(records)


def classify_market(row: pd.Series) -> str:
    if row.get("recent_released_flag") or row.get("recent_dfa_flag"):
        return "recently_released_or_dfa_high_access"
    if row.get("recent_injured_list_flag") or row.get("recent_rehab_flag") or row.get("injury_flag"):
        return "medical_watch_hold"
    if row.get("recent_minor_league_contract_flag") or row.get("recent_outrighted_flag"):
        return "minor_contract_or_outright_follow"
    if row.get("recent_optioned_flag") or row.get("recent_assigned_flag"):
        return "optional_movement_watch"
    if row.get("market_access_bucket") == "non40man_org_candidate":
        return "non40man_org_candidate"
    if row.get("market_access_bucket") == "dfa_designated_high_signal":
        return "dfa_designated_high_signal"
    if row.get("market_access_bucket") == "medical_red_flag":
        return "medical_watch_hold"
    if row.get("is_active"):
        return "active_or_mlb_locked_low_access"
    if row.get("is_40man"):
        return "40man_locked_medium_low_access"
    if pd.isna(row.get("transaction_count_since_20251001")):
        return "no_recent_transaction_unknown"
    return "transaction_seen_no_access_signal"


def score_market(row: pd.Series) -> float:
    base = pd.to_numeric(row.get("market_access_score"), errors="coerce")
    if pd.isna(base):
        base = 45.0
    score = float(base)
    if row.get("recent_released_flag") or row.get("recent_dfa_flag"):
        score += 18
    if row.get("recent_minor_league_contract_flag") or row.get("recent_outrighted_flag"):
        score += 10
    if row.get("recent_optioned_flag") or row.get("recent_assigned_flag"):
        score += 4
    if row.get("recent_injured_list_flag") or row.get("recent_rehab_flag") or row.get("injury_flag"):
        score = min(score, 28)
    if row.get("is_active"):
        score = min(score, 30)
    if row.get("is_40man") and not row.get("recent_released_flag") and not row.get("recent_dfa_flag"):
        score = min(score, 45)
    return max(0.0, min(100.0, score))


def classify_release_policy(row: pd.Series) -> str:
    if row["market_availability_bucket"] == "medical_watch_hold":
        return "hold_medical_context_required"
    if row["market_access_score_v2"] < 35:
        return "market_watch_low_access"
    if row["market_availability_bucket"] in {
        "recently_released_or_dfa_high_access",
        "minor_contract_or_outright_follow",
        "non40man_org_candidate",
        "optional_movement_watch",
    }:
        return "research_lead_only_manual_check_required"
    return "market_watch_manual_check_required"


def build_layers() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    candidates = load_candidates()
    transactions = add_recent_flags(pd.read_csv(TRANSACTIONS))
    summary = summarize_transactions(transactions)

    merged = candidates.merge(summary, on="player_id", how="left")
    for column in merged.columns:
        if column.endswith("_flag") or column.startswith("recent_") and column.endswith("_flag"):
            merged[column] = safe_bool(merged[column])
    merged["market_availability_bucket"] = merged.apply(classify_market, axis=1)
    merged["market_access_score_v2"] = merged.apply(score_market, axis=1)
    merged["candidate_release_policy_v2"] = merged.apply(classify_release_policy, axis=1)
    merged["is_final_recommendation"] = False
    merged["candidate_name_release_allowed"] = False

    sort_cols = ["slot", "market_access_score_v2", "final_priority_score"]
    existing_sort_cols = [column for column in sort_cols if column in merged.columns]
    merged = merged.sort_values(existing_sort_cols, ascending=[True, False, False], na_position="last")

    summary_table = (
        merged.groupby(["slot", "market_availability_bucket", "candidate_release_policy_v2"], dropna=False)
        .agg(
            rows=("player_id", "count"),
            median_market_access_score_v2=("market_access_score_v2", "median"),
            median_final_priority_score=("final_priority_score", "median"),
            recent_release_or_dfa=("recent_released_flag", "sum"),
            recent_minor_contract=("recent_minor_league_contract_flag", "sum"),
            recent_medical_signal=("recent_injured_list_flag", "sum"),
        )
        .reset_index()
        .sort_values(["slot", "rows"], ascending=[True, False])
    )

    type_summary = (
        transactions.groupby(["type_code", "type_desc"], dropna=False)
        .agg(
            rows=("transaction_id", "count"),
            players=("player_id", "nunique"),
            first_date=("date", "min"),
            last_date=("date", "max"),
            released=("released_flag", "sum"),
            declared_free_agency=("declared_free_agency_flag", "sum"),
            dfa=("dfa_flag", "sum"),
            minor_contract=("minor_league_contract_flag", "sum"),
            injured_list=("injured_list_flag", "sum"),
        )
        .reset_index()
        .sort_values(["rows", "players"], ascending=False)
    )
    return merged, summary_table, type_summary


def main() -> None:
    market, summary, type_summary = build_layers()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    market_path = OUT_DIR / "mlb_replacement_market_status_v1.csv"
    summary_path = OUT_DIR / "mlb_replacement_market_summary_v1.csv"
    type_path = OUT_DIR / "mlb_transaction_type_summary_v1.csv"
    market.to_csv(market_path, index=False)
    summary.to_csv(summary_path, index=False)
    type_summary.to_csv(type_path, index=False)
    print(f"wrote {market_path} ({len(market)} rows)")
    print(f"wrote {summary_path} ({len(summary)} rows)")
    print(f"wrote {type_path} ({len(type_summary)} rows)")


if __name__ == "__main__":
    main()
