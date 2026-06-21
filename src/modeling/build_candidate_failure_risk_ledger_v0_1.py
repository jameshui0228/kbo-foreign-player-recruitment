#!/usr/bin/env python3
"""Build the SSG candidate failure-risk ledger.

This is Layer 5. It combines:

- Layer 2 KBO foreign-player archetype rules;
- Layer 3 market realism, official roster/transaction status, and news signals;
- candidate-side hitter/pitcher/Asian-quota diagnostic components.

The output is not a ranking or recommendation. It is a source-backed risk ledger
that explains why a candidate could fail before any shortlist can be released.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

DEFAULT_INPUT = OUTPUT_DIR / "manual_feasibility_source_worklist_v0_3.csv"
FIT_PREP = OUTPUT_DIR / "ssg_fit_preparation_mart_v0_1.csv"
HITTER_COMPONENT = OUTPUT_DIR / "candidate_side_hitter_savant_pilot_component_v0_1.csv"
PITCHER_COMPONENT = OUTPUT_DIR / "candidate_side_pitcher_milb_diagnostic_tags_v0_1.csv"
ASIAN_COMPONENT = OUTPUT_DIR / "candidate_side_asian_quota_feasibility_tags_v0_1.csv"
LAYER2_RULES = OUTPUT_DIR / "kbo_foreign_archetype_rule_lifts_v0_2.csv"
LAYER2_CONTRACT = OUTPUT_DIR / "kbo_foreign_archetype_feature_contract_v0_2.csv"

RELEASE_POLICY = "candidate_failure_risk_research_only_no_recommendation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=str(DEFAULT_INPUT.relative_to(PROJECT_ROOT)))
    parser.add_argument("--output-suffix", default="v0_1")
    return parser.parse_args()


def norm_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def boolish(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def safe_num(frame: pd.DataFrame, col: str, default: float = np.nan) -> pd.Series:
    if col not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[col], errors="coerce")


def clip(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0).clip(0, 100).round(3)


def inv_score(series: pd.Series) -> pd.Series:
    return (100 - pd.to_numeric(series, errors="coerce").fillna(50)).clip(0, 100)


def contains_any(series: pd.Series, *needles: str) -> pd.Series:
    text = series.fillna("").astype(str).str.lower()
    return pd.concat([text.str.contains(needle.lower(), regex=False) for needle in needles], axis=1).any(axis=1)


def add_prefixed(base: pd.DataFrame, other: pd.DataFrame, keys: list[str], prefix: str, columns: list[str]) -> pd.DataFrame:
    keep = [key for key in keys if key in other.columns]
    use_cols = keep + [col for col in columns if col in other.columns]
    slim = other[use_cols].drop_duplicates(keep)
    rename = {col: f"{prefix}{col}" for col in use_cols if col not in keep}
    return base.merge(slim.rename(columns=rename), on=keep, how="left")


def load_base(input_path: Path) -> pd.DataFrame:
    base = pd.read_csv(input_path)
    fit = pd.read_csv(FIT_PREP)
    hitter = pd.read_csv(HITTER_COMPONENT)
    pitcher = pd.read_csv(PITCHER_COMPONENT)
    asian = pd.read_csv(ASIAN_COMPONENT)

    out = add_prefixed(
        base,
        fit,
        ["fit_slot", "player_name", "team_or_org", "position_or_role"],
        "fit_",
        [
            "market_access_score",
            "availability_gate_score",
            "candidate_side_primary_signal",
            "feature_coverage_score",
            "research_status",
            "manual_check_flags",
            "model_component_pct",
            "ssg_rhp_unlock_proxy_pct",
            "two_strike_survival_proxy_pct",
            "pitcher_diagnostic_pct",
            "starter_runway_proxy_pct",
            "traffic_command_proxy_pct",
            "asian_nationality_gate_score",
            "contract_unknown_penalty_score",
            "club_control_access_score",
            "asian_league_history_score",
            "npb_stat_context_score",
            "npb_performance_context_pct",
        ],
    )
    out = add_prefixed(
        out,
        hitter.rename(columns={"roster_team": "team_or_org"}),
        ["player_id", "player_name", "team_or_org"],
        "hitter_",
        [
            "recent_pa",
            "recent_woba",
            "recent_bb_pct",
            "recent_k_pct",
            "recent_whiff_per_swing",
            "recent_nonfast_whiff_per_swing",
            "recent_hardhit_rate",
            "recent_barrel_rate",
            "recent_hitter_count_xwoba",
            "hitter_savant_pilot_success_prob",
            "hitter_savant_pilot_failure_prob",
            "hitter_savant_pilot_net_signal",
            "hitter_savant_pilot_component_status",
            "hitter_model_feature_non_null_count",
        ],
    )
    out = add_prefixed(
        out,
        pitcher.rename(columns={"roster_team": "team_or_org"}),
        ["player_id", "player_name", "team_or_org"],
        "pitcher_",
        [
            "recent_starter_stabilizer_score",
            "recent_woba_allowed",
            "recent_three_ball_pitch_rate",
            "milb_role_continuity_bucket",
            "milb_role_context_score",
            "milb_2026_ip",
            "milb_2026_games_started",
            "milb_2026_k9",
            "milb_2026_bb9",
            "milb_2026_hr9",
            "pitcher_milb_damage_command_diagnostic_score",
            "pitcher_milb_diagnostic_tags",
            "pitcher_milb_diagnostic_status",
            "pitcher_diagnostic_use_allowed",
        ],
    )
    asian_join = asian.rename(columns={"team_name": "team_or_org", "position": "position_or_role"})
    out = add_prefixed(
        out,
        asian_join,
        ["player_name", "team_or_org", "position_or_role"],
        "asian_",
        [
            "asian_league_history_gate",
            "asian_quota_nationality_gate",
            "contract_status_gate",
            "new_signing_cost_gate",
            "availability_bucket",
            "asian_quota_feasibility_bucket",
            "club_control_risk_flag",
        ],
    )
    return out


def rule_catalog() -> tuple[pd.DataFrame, pd.DataFrame]:
    rules = pd.read_csv(LAYER2_RULES)
    contract = pd.read_csv(LAYER2_CONTRACT)
    promoted = rules[rules["rule_gate"].eq("promote_as_research_archetype_signal")].copy()
    return promoted, contract


def hitter_translation_risk(df: pd.DataFrame) -> pd.Series:
    failure_prob = safe_num(df, "hitter_hitter_savant_pilot_failure_prob", 0.5) * 100
    status_risk = np.select(
        [
            df.get("hitter_hitter_savant_pilot_component_status", "").astype(str).eq("negative_pilot_signal_risk"),
            df.get("hitter_hitter_savant_pilot_component_status", "").astype(str).eq("insufficient_savant_feature_coverage"),
        ],
        [75, 65],
        default=35,
    )
    k_risk = safe_num(df, "hitter_recent_k_pct", 0.25).fillna(0.25) * 140
    whiff_risk = safe_num(df, "hitter_recent_whiff_per_swing", 0.25).fillna(0.25) * 140
    contact_floor = (k_risk + whiff_risk) / 2
    return clip(pd.Series(failure_prob, index=df.index) * 0.45 + pd.Series(status_risk, index=df.index) * 0.30 + contact_floor * 0.25)


def pitcher_translation_risk(df: pd.DataFrame) -> pd.Series:
    diagnostic = inv_score(safe_num(df, "pitcher_pitcher_milb_damage_command_diagnostic_score", 50))
    role_continuity = inv_score(safe_num(df, "pitcher_milb_role_context_score", 50))
    damage = (
        safe_num(df, "pitcher_milb_2026_hr9", 1.2).fillna(1.2).clip(0, 4) / 4 * 100 * 0.45
        + safe_num(df, "pitcher_milb_2026_bb9", 4.0).fillna(4.0).clip(0, 8) / 8 * 100 * 0.35
        + safe_num(df, "pitcher_recent_woba_allowed", 0.33).fillna(0.33).clip(0.2, 0.55).sub(0.2).div(0.35).mul(100) * 0.20
    )
    return clip(diagnostic * 0.35 + role_continuity * 0.35 + damage * 0.30)


def asian_translation_risk(df: pd.DataFrame) -> pd.Series:
    nationality = inv_score(safe_num(df, "fit_asian_nationality_gate_score", 50))
    history = inv_score(safe_num(df, "fit_asian_league_history_score", 50))
    stat_context = inv_score(safe_num(df, "fit_npb_stat_context_score", 50))
    return clip(nationality * 0.35 + history * 0.30 + stat_context * 0.35)


def kbo_translation_risk(df: pd.DataFrame) -> pd.Series:
    out = pd.Series(55.0, index=df.index)
    hitter_mask = df["fit_slot"].eq("foreign_hitter")
    pitcher_mask = df["fit_slot"].eq("foreign_pitcher")
    asian_mask = df["fit_slot"].eq("asian_quota")
    out.loc[hitter_mask] = hitter_translation_risk(df[hitter_mask])
    out.loc[pitcher_mask] = pitcher_translation_risk(df[pitcher_mask])
    out.loc[asian_mask] = asian_translation_risk(df[asian_mask])
    return clip(out)


def medical_risk(df: pd.DataFrame) -> pd.Series:
    bucket = df.get("medical_risk_bucket", pd.Series("", index=df.index)).fillna("").astype(str)
    news_status = df.get("candidate_news_status", pd.Series("", index=df.index)).fillna("").astype(str)
    injury_articles = safe_num(df, "injury_medical_article_rows", 0)
    roster_note = df.get("current_roster_note", pd.Series("", index=df.index)).fillna("").astype(str)
    base = pd.Series(25.0, index=df.index)
    base += np.where(bucket.str.contains("medical_hold", case=False, na=False), 55, 0)
    base += np.where(bucket.str.contains("history", case=False, na=False), 25, 0)
    base += np.where(news_status.str.contains("medical", case=False, na=False), 25, 0)
    base += np.minimum(injury_articles.fillna(0), 5) * 4
    base += np.where(roster_note.str.contains("surgery|rehab|strain|sprain|fracture|illness|injur", case=False, regex=True, na=False), 20, 0)
    return clip(base)


def contract_cost_risk(df: pd.DataFrame) -> pd.Series:
    contract = df.get("contract_control_bucket", pd.Series("", index=df.index)).fillna("").astype(str)
    market_status = df.get("market_realism_status", pd.Series("", index=df.index)).fillna("").astype(str)
    cost = df.get("kbo_rule_cost_bucket", pd.Series("", index=df.index)).fillna("").astype(str)
    manual = df.get("manual_source_lanes", pd.Series("", index=df.index)).fillna("").astype(str)
    base = inv_score(safe_num(df, "market_realism_score", 50)) * 0.45
    base += np.where(contract.str.contains("active_mlb|40man|blocker|club_control|unknown", case=False, regex=True, na=False), 22, 0)
    base += np.where(market_status.str.contains("buyout|contract|blocker|nationality", case=False, regex=True, na=False), 14, 0)
    base += np.where(cost.str.contains("cap|cost", case=False, regex=True, na=False), 6, 0)
    base += np.where(manual.str.contains("contract|salary|buyout|option|transfer", case=False, regex=True, na=False), 10, 0)
    return clip(base)


def role_fit_risk(df: pd.DataFrame) -> pd.Series:
    out = inv_score(safe_num(df, "fit_preparation_index", 50)) * 0.55
    out += inv_score(safe_num(df, "market_realism_fit_blend_for_triage_only", 50)) * 0.20
    status = df.get("fit_research_status", pd.Series("", index=df.index)).fillna("").astype(str)
    signal = df.get("fit_candidate_side_primary_signal", pd.Series("", index=df.index)).fillna("").astype(str)
    out += np.where(status.str.contains("risk|missing|coverage", case=False, regex=True, na=False), 20, 0)
    out += np.where(signal.str.contains("risk|negative|missing|insufficient", case=False, regex=True, na=False), 20, 0)
    return clip(out)


def adaptation_willingness_risk(df: pd.DataFrame) -> pd.Series:
    korean = safe_num(df, "korean_article_rows", 0)
    korea_context = safe_num(df, "korea_willingness_article_rows", 0)
    adaptation = safe_num(df, "adaptation_context_article_rows", 0)
    lanes = df.get("manual_source_lanes", pd.Series("", index=df.index)).fillna("").astype(str)
    news_status = df.get("candidate_news_status", pd.Series("", index=df.index)).fillna("").astype(str)
    base = pd.Series(35.0, index=df.index)
    base += np.where(korean.eq(0), 8, -8)
    base += np.where(korea_context.gt(0), -8, 6)
    base += np.where(adaptation.gt(0), -4, 3)
    base += np.where(lanes.str.contains("willingness|intent", case=False, regex=True, na=False), 12, 0)
    base += np.where(news_status.str.contains("korea_or_overseas", case=False, regex=True, na=False), -8, 0)
    return clip(base)


def data_gap_risk(df: pd.DataFrame) -> pd.Series:
    lanes = safe_num(df, "manual_source_lane_count", 0).fillna(0)
    usable_news = safe_num(df, "usable_article_rows", 0).fillna(0)
    feature_cov = safe_num(df, "fit_feature_coverage_score", np.nan)
    base = pd.Series(25.0, index=df.index) + lanes.clip(0, 6) * 8
    base += np.where(usable_news.eq(0), 25, 0)
    base += np.where(feature_cov.notna(), inv_score(feature_cov) * 0.25, 15)
    return clip(base)


def layer2_candidate_flags(df: pd.DataFrame) -> pd.Series:
    flags = []
    for row in df.to_dict("records"):
        slot = row.get("fit_slot", "")
        row_flags: list[str] = []
        if slot == "foreign_pitcher":
            raw_miss_high = pd.notna(row.get("pitcher_milb_2026_k9")) and float(row.get("pitcher_milb_2026_k9")) >= 9.0
            role_low = pd.notna(row.get("pitcher_milb_role_context_score")) and float(row.get("pitcher_milb_role_context_score")) < 45
            if raw_miss_high and role_low:
                row_flags.append("L2_raw_miss_without_role_continuity_success_suppression")
            if pd.notna(row.get("pitcher_milb_role_context_score")) and float(row.get("pitcher_milb_role_context_score")) >= 65:
                row_flags.append("L2_role_continuity_replacement_risk_suppression")
            if norm_text(row.get("pitcher_pitcher_milb_diagnostic_tags")).find("volatile_stuff_profile") >= 0:
                row_flags.append("L2_volatile_stuff_profile_review")
        elif slot == "foreign_hitter":
            if norm_text(row.get("hitter_hitter_savant_pilot_component_status")) == "negative_pilot_signal_risk":
                row_flags.append("L2_hitter_pilot_negative_translation_risk")
            if pd.notna(row.get("hitter_recent_k_pct")) and float(row.get("hitter_recent_k_pct")) >= 0.28:
                row_flags.append("L2_hitter_contact_floor_review")
        elif slot == "asian_quota":
            row_flags.append("L2_asian_quota_historical_translation_gap")
        flags.append("|".join(row_flags) if row_flags else "no_layer2_specific_candidate_flag")
    return pd.Series(flags, index=df.index)


def build_reason_tags(df: pd.DataFrame) -> pd.Series:
    tags = []
    for row in df.to_dict("records"):
        row_tags = []
        for field, label in [
            ("medical_availability_risk", "medical_availability"),
            ("contract_cost_access_risk", "contract_cost_access"),
            ("role_fit_risk", "role_fit"),
            ("kbo_translation_risk", "kbo_translation"),
            ("adaptation_willingness_risk", "adaptation_willingness"),
            ("data_gap_risk", "data_gap"),
        ]:
            value = float(row.get(field, 0) or 0)
            if value >= 70:
                row_tags.append(f"{label}_high")
            elif value >= 55:
                row_tags.append(f"{label}_watch")
        layer2 = str(row.get("layer2_candidate_flags", ""))
        if layer2 and layer2 != "no_layer2_specific_candidate_flag":
            row_tags.append("layer2_archetype_flag")
        if not row_tags:
            row_tags.append("no_high_risk_bucket_yet")
        tags.append("|".join(dict.fromkeys(row_tags)))
    return pd.Series(tags, index=df.index)


def build_priority(df: pd.DataFrame) -> pd.Series:
    high_count = (
        df[
            [
                "medical_availability_risk",
                "contract_cost_access_risk",
                "role_fit_risk",
                "kbo_translation_risk",
                "adaptation_willingness_risk",
                "data_gap_risk",
            ]
        ]
        .ge(70)
        .sum(axis=1)
    )
    return pd.Series(
        np.select(
            [
                df["failure_risk_index"].ge(75) | high_count.ge(3),
                df["failure_risk_index"].ge(60) | high_count.ge(2),
                df["failure_risk_index"].ge(45),
            ],
            ["tier_1_blocker_review", "tier_2_multi_risk_review", "tier_3_watch_review"],
            default="tier_4_low_current_risk",
        ),
        index=df.index,
    )


def build_ledger(input_path: Path) -> pd.DataFrame:
    promoted_rules, _ = rule_catalog()
    out = load_base(input_path)
    out["layer2_promoted_rule_count"] = len(promoted_rules)
    out["layer2_candidate_flags"] = layer2_candidate_flags(out)
    out["medical_availability_risk"] = medical_risk(out)
    out["contract_cost_access_risk"] = contract_cost_risk(out)
    out["role_fit_risk"] = role_fit_risk(out)
    out["kbo_translation_risk"] = kbo_translation_risk(out)
    out["adaptation_willingness_risk"] = adaptation_willingness_risk(out)
    out["data_gap_risk"] = data_gap_risk(out)
    out["failure_risk_index"] = clip(
        out["medical_availability_risk"] * 0.18
        + out["contract_cost_access_risk"] * 0.18
        + out["role_fit_risk"] * 0.16
        + out["kbo_translation_risk"] * 0.22
        + out["adaptation_willingness_risk"] * 0.12
        + out["data_gap_risk"] * 0.14
    )
    out["failure_risk_reason_tags"] = build_reason_tags(out)
    out["failure_risk_review_tier"] = build_priority(out)
    out["failure_risk_release_policy"] = RELEASE_POLICY
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False
    out["score_release_allowed"] = False
    out["failure_risk_score_release_allowed"] = False
    out["recommendation_label"] = "locked_not_allowed"
    return out.sort_values(["fit_slot", "failure_risk_review_tier", "failure_risk_index"], ascending=[True, True, False])


def build_slot_summary(ledger: pd.DataFrame) -> pd.DataFrame:
    return (
        ledger.groupby(["fit_slot", "failure_risk_review_tier"], dropna=False)
        .agg(
            rows=("fit_slot", "size"),
            median_failure_risk=("failure_risk_index", "median"),
            p75_failure_risk=("failure_risk_index", lambda s: s.quantile(0.75)),
            high_medical_rows=("medical_availability_risk", lambda s: int((s >= 70).sum())),
            high_contract_rows=("contract_cost_access_risk", lambda s: int((s >= 70).sum())),
            high_translation_rows=("kbo_translation_risk", lambda s: int((s >= 70).sum())),
            layer2_flag_rows=("layer2_candidate_flags", lambda s: int((s != "no_layer2_specific_candidate_flag").sum())),
            release_allowed=("failure_risk_score_release_allowed", "any"),
        )
        .reset_index()
        .sort_values(["fit_slot", "failure_risk_review_tier"])
    )


def build_bucket_summary(ledger: pd.DataFrame) -> pd.DataFrame:
    rows = []
    buckets = [
        "medical_availability_risk",
        "contract_cost_access_risk",
        "role_fit_risk",
        "kbo_translation_risk",
        "adaptation_willingness_risk",
        "data_gap_risk",
    ]
    for bucket in buckets:
        for slot, group in ledger.groupby("fit_slot", dropna=False):
            rows.append(
                {
                    "fit_slot": slot,
                    "risk_bucket": bucket,
                    "rows": len(group),
                    "median_risk": float(group[bucket].median()),
                    "p75_risk": float(group[bucket].quantile(0.75)),
                    "high_risk_rows": int(group[bucket].ge(70).sum()),
                    "watch_or_high_rows": int(group[bucket].ge(55).sum()),
                }
            )
    return pd.DataFrame(rows).sort_values(["fit_slot", "high_risk_rows", "risk_bucket"], ascending=[True, False, True])


def build_gate_audit(ledger: pd.DataFrame) -> pd.DataFrame:
    lock_cols = [
        "is_final_recommendation",
        "shortlist_label_allowed",
        "candidate_name_release_allowed",
        "score_release_allowed",
        "failure_risk_score_release_allowed",
    ]
    return pd.DataFrame(
        [
            {
                "gate": "R1",
                "check": "all_candidates_receive_failure_risk_buckets",
                "pass_rows": int(ledger["failure_risk_index"].notna().sum()),
                "total_rows": len(ledger),
                "status": "pass",
                "blocking_gap": "Risk buckets are research-only and not calibrated as public final scores",
            },
            {
                "gate": "R2",
                "check": "layer2_archetype_flags_attached",
                "pass_rows": int(ledger["layer2_candidate_flags"].ne("no_layer2_specific_candidate_flag").sum()),
                "total_rows": len(ledger),
                "status": "partial_pass",
                "blocking_gap": "Layer 2 flags are only available where candidate-side proxies exist",
            },
            {
                "gate": "R3",
                "check": "manual_source_lane_integration",
                "pass_rows": int(pd.to_numeric(ledger.get("manual_source_lane_count", 0), errors="coerce").fillna(0).gt(0).sum()),
                "total_rows": len(ledger),
                "status": "pass_visible_gap",
                "blocking_gap": "Many risk rows still require manual contract, medical, agent, salary, buyout, or willingness source values",
            },
            {
                "gate": "R4",
                "check": "release_locks_preserved",
                "pass_rows": int((ledger[lock_cols].eq(False).all(axis=1)).sum()),
                "total_rows": len(ledger),
                "status": "pass",
                "blocking_gap": "No candidate names, scores, rankings, shortlist labels, or recommendations are released",
            },
        ]
    )


def main() -> None:
    args = parse_args()
    suffix = args.output_suffix
    input_path = PROJECT_ROOT / args.input
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ledger = build_ledger(input_path)
    slot_summary = build_slot_summary(ledger)
    bucket_summary = build_bucket_summary(ledger)
    gate_audit = build_gate_audit(ledger)

    ledger.to_csv(OUTPUT_DIR / f"candidate_failure_risk_ledger_{suffix}.csv", index=False)
    slot_summary.to_csv(OUTPUT_DIR / f"candidate_failure_risk_slot_summary_{suffix}.csv", index=False)
    bucket_summary.to_csv(OUTPUT_DIR / f"candidate_failure_risk_bucket_summary_{suffix}.csv", index=False)
    gate_audit.to_csv(OUTPUT_DIR / f"candidate_failure_risk_gate_audit_{suffix}.csv", index=False)

    print(f"ledger_rows={len(ledger)}")
    print(slot_summary.to_string(index=False))
    print(bucket_summary.to_string(index=False))
    print(gate_audit.to_string(index=False))


if __name__ == "__main__":
    main()
