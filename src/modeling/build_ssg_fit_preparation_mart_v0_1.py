#!/usr/bin/env python3
"""Build a locked SSG fit preparation mart.

This run is the bridge between candidate-side signal components and a future
SSG fit ranking. It intentionally does not create a shortlist or recommendations.

Slot policy:

1. foreign hitter: use the validated Savant pilot component as one research
   readiness input, then align it with the Layer 1 hitter feature contract.
2. foreign pitcher: keep MiLB damage/command evidence diagnostic-only because
   the pitcher model has not cleared promotion gates.
3. Asian quota: prioritize feasibility review with NPB official-stat context
   when available, not player-quality recommendations.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

HITTER_INPUT = OUTPUT_DIR / "candidate_side_hitter_savant_pilot_component_v0_1.csv"
PITCHER_INPUT = OUTPUT_DIR / "candidate_side_pitcher_milb_diagnostic_tags_v0_1.csv"
ASIAN_INPUT = OUTPUT_DIR / "candidate_side_asian_quota_feasibility_tags_v0_1.csv"
NPB_MARKET_FEATURES = OUTPUT_DIR / "npb_player_market_features_2026_v1.csv"
LAYER1_FEATURE_BLUEPRINT = OUTPUT_DIR / "ssg_layer1_candidate_feature_blueprint_v4.csv"
LAYER1_FINAL_MESSAGE = OUTPUT_DIR / "ssg_hidden_weakness_final_message_v3.csv"

MART_OUT = OUTPUT_DIR / "ssg_fit_preparation_mart_v0_1.csv"
SLOT_SUMMARY_OUT = OUTPUT_DIR / "ssg_fit_preparation_slot_summary_v0_1.csv"
GATE_AUDIT_OUT = OUTPUT_DIR / "ssg_fit_preparation_gate_audit_v0_1.csv"
FEATURE_CONTRACT_OUT = OUTPUT_DIR / "ssg_fit_preparation_feature_contract_v0_1.csv"

RELEASE_POLICY = "fit_preparation_research_only_no_recommendation"
LOCKED_STATUS = "locked_research_only"


def bool_score(series: pd.Series) -> pd.Series:
    values = series.astype(str).str.lower()
    return pd.Series(
        np.select([values.isin(["true", "1", "1.0"]), values.isin(["false", "0", "0.0"])], [100.0, 0.0], default=50.0),
        index=series.index,
    )


def gate_score(series: pd.Series, pass_values: set[str], fail_values: set[str] | None = None) -> pd.Series:
    fail_values = fail_values or set()
    values = series.fillna("unknown").astype(str)
    return pd.Series(
        np.select([values.isin(pass_values), values.isin(fail_values)], [100.0, 0.0], default=50.0),
        index=series.index,
    )


def safe_pct_rank(series: pd.Series, higher_is_better: bool = True, fill_value: float = 50.0) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().sum() <= 1 or numeric.nunique(dropna=True) <= 1:
        return pd.Series(fill_value, index=series.index)
    ranked = numeric.rank(pct=True, ascending=True) * 100
    if not higher_is_better:
        ranked = 100 - ranked
    return ranked.fillna(fill_value)


def weighted_mean(frame: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    columns = [col for col in weights if col in frame.columns]
    if not columns:
        return pd.Series(np.nan, index=frame.index)
    weight = pd.Series({col: weights[col] for col in columns}, dtype=float)
    values = frame[columns].astype(float)
    return values.mul(weight, axis=1).sum(axis=1) / weight.sum()


def clipped(values: pd.Series) -> pd.Series:
    return values.clip(lower=0, upper=100).round(3)


def first_existing(row: pd.Series, fields: list[str]) -> object:
    for field in fields:
        if field in row and pd.notna(row[field]):
            return row[field]
    return np.nan


def make_flags(flags: list[str]) -> str:
    clean = [flag for flag in flags if flag]
    return "|".join(clean) if clean else "no_immediate_data_flag"


def attach_common_locks(out: pd.DataFrame) -> pd.DataFrame:
    out["candidate_release_policy"] = RELEASE_POLICY
    out["fit_gate_status"] = LOCKED_STATUS
    out["is_final_recommendation"] = False
    out["shortlist_label_allowed"] = False
    out["candidate_name_release_allowed"] = False
    out["recommendation_label"] = "locked_not_allowed"
    return out


def build_hitter_mart() -> pd.DataFrame:
    hitters = pd.read_csv(HITTER_INPUT)
    out = pd.DataFrame(index=hitters.index)
    out["fit_slot"] = "foreign_hitter"
    out["source_pool"] = hitters["slot"]
    out["player_id"] = hitters["player_id"]
    out["player_name"] = hitters["player_name"]
    out["team_or_org"] = hitters["roster_team"]
    out["age"] = pd.to_numeric(hitters["age"], errors="coerce")
    out["throws_or_bats"] = hitters["bat_side"]
    out["birth_country"] = hitters["birth_country"]
    out["position_or_role"] = "OF/DH candidate pool"
    out["market_access_bucket"] = hitters["market_access_bucket"]
    out["market_access_score"] = pd.to_numeric(hitters["market_access_score"], errors="coerce").fillna(50.0)
    out["availability_gate_pass"] = hitters["availability_gate_pass"]
    out["first_pass_gate_pass"] = hitters["first_pass_gate_pass"]
    out["candidate_side_primary_signal"] = hitters["hitter_savant_pilot_component_status"]
    out["score_interpretation"] = "research_readiness_index_not_recommendation"
    out["score_release_allowed"] = False

    net_signal_pct = safe_pct_rank(hitters["hitter_savant_pilot_net_signal"], higher_is_better=True)
    success_pct = safe_pct_rank(hitters["hitter_savant_pilot_success_prob"], higher_is_better=True)
    failure_avoid_pct = safe_pct_rank(hitters["hitter_savant_pilot_failure_prob"], higher_is_better=False)
    model_component_pct = pd.concat([net_signal_pct, success_pct, failure_avoid_pct], axis=1).mean(axis=1)

    contact_floor_pct = pd.concat(
        [
            safe_pct_rank(hitters.get("recent_k_pct", pd.Series(index=hitters.index, dtype=float)), higher_is_better=False),
            safe_pct_rank(hitters.get("recent_whiff_per_swing", pd.Series(index=hitters.index, dtype=float)), higher_is_better=False),
            safe_pct_rank(
                hitters.get("recent_nonfast_whiff_per_swing", pd.Series(index=hitters.index, dtype=float)),
                higher_is_better=False,
            ),
        ],
        axis=1,
    ).mean(axis=1)

    rhp_unlock_proxy_pct = pd.concat(
        [
            safe_pct_rank(hitters.get("recent_hitter_count_xwoba", pd.Series(index=hitters.index, dtype=float)), True),
            safe_pct_rank(hitters.get("recent_bb_pct", pd.Series(index=hitters.index, dtype=float)), True),
            safe_pct_rank(hitters.get("recent_hardhit_rate", pd.Series(index=hitters.index, dtype=float)), True),
            safe_pct_rank(hitters.get("recent_barrel_rate", pd.Series(index=hitters.index, dtype=float)), True),
        ],
        axis=1,
    ).mean(axis=1)

    feature_count = pd.to_numeric(hitters["hitter_model_feature_count"], errors="coerce").replace(0, np.nan)
    non_null = pd.to_numeric(hitters["hitter_model_feature_non_null_count"], errors="coerce")
    feature_coverage_score = (non_null / feature_count * 100).fillna(50.0).clip(0, 100)

    components = pd.DataFrame(
        {
            "model_component_pct": model_component_pct,
            "ssg_rhp_unlock_proxy_pct": rhp_unlock_proxy_pct,
            "two_strike_survival_proxy_pct": contact_floor_pct,
            "market_access_component_score": out["market_access_score"],
            "availability_gate_score": bool_score(hitters["availability_gate_pass"]),
            "feature_coverage_score": feature_coverage_score,
        }
    )
    out = pd.concat([out, components], axis=1)
    out["fit_preparation_index"] = clipped(
        weighted_mean(
            components,
            {
                "model_component_pct": 0.30,
                "ssg_rhp_unlock_proxy_pct": 0.20,
                "two_strike_survival_proxy_pct": 0.15,
                "market_access_component_score": 0.15,
                "availability_gate_score": 0.10,
                "feature_coverage_score": 0.10,
            },
        )
    )

    out["research_status"] = np.select(
        [
            hitters["hitter_savant_pilot_component_status"].eq("positive_pilot_signal_unranked")
            & hitters["availability_gate_pass"].astype(str).str.lower().isin(["true", "1", "1.0"]),
            hitters["hitter_savant_pilot_component_status"].eq("negative_pilot_signal_risk"),
            hitters["hitter_savant_pilot_component_status"].eq("insufficient_savant_feature_coverage"),
        ],
        ["research_inventory_high_signal_locked", "risk_review_needed", "feature_coverage_gap_review"],
        default="research_inventory_neutral_locked",
    )

    flags = []
    for row in hitters.to_dict("records"):
        row_flags = []
        if str(row.get("availability_gate_pass", "")).lower() not in {"true", "1", "1.0"}:
            row_flags.append("availability_gate_failed_or_unknown")
        if str(row.get("first_pass_gate_pass", "")).lower() not in {"true", "1", "1.0"}:
            row_flags.append("first_pass_gate_failed_or_unknown")
        if row.get("hitter_savant_pilot_component_status") == "negative_pilot_signal_risk":
            row_flags.append("model_signal_risk")
        if row.get("hitter_savant_pilot_component_status") == "insufficient_savant_feature_coverage":
            row_flags.append("savant_feature_coverage_gap")
        row_flags.append("needs_contract_medical_news_manual_check")
        row_flags.append("needs_defense_baserunning_manual_check")
        flags.append(make_flags(row_flags))
    out["manual_check_flags"] = flags
    out["slot_fit_message"] = "RHP_game_script_OF_DH_unlocker_with_run_kill_avoidance"
    out["source_evidence_files"] = f"{HITTER_INPUT.name};{LAYER1_FEATURE_BLUEPRINT.name}"
    return attach_common_locks(out)


def build_pitcher_mart() -> pd.DataFrame:
    pitchers = pd.read_csv(PITCHER_INPUT)
    out = pd.DataFrame(index=pitchers.index)
    out["fit_slot"] = "foreign_pitcher"
    out["source_pool"] = pitchers["slot"]
    out["player_id"] = pitchers["player_id"]
    out["player_name"] = pitchers["player_name"]
    out["team_or_org"] = pitchers["roster_team"]
    out["age"] = pd.to_numeric(pitchers["age"], errors="coerce")
    out["throws_or_bats"] = pitchers["pitch_hand"]
    out["birth_country"] = pitchers["birth_country"]
    out["position_or_role"] = "SP/multi-inning pitcher candidate pool"
    out["market_access_bucket"] = pitchers["market_access_bucket"]
    out["market_access_score"] = pd.to_numeric(pitchers["market_access_score"], errors="coerce").fillna(50.0)
    out["availability_gate_pass"] = pitchers["availability_gate_pass"]
    out["first_pass_gate_pass"] = pitchers["first_pass_gate_pass"]
    out["candidate_side_primary_signal"] = pitchers["pitcher_milb_diagnostic_status"]
    out["score_interpretation"] = "diagnostic_research_triage_not_model_score"
    out["score_release_allowed"] = False

    diagnostic_pct = safe_pct_rank(
        pitchers["pitcher_milb_damage_command_diagnostic_score"],
        higher_is_better=True,
        fill_value=40.0,
    )
    starter_runway_pct = pd.concat(
        [
            safe_pct_rank(pitchers.get("recent_starter_stabilizer_score", pd.Series(index=pitchers.index, dtype=float)), True),
            safe_pct_rank(pitchers.get("milb_role_context_score", pd.Series(index=pitchers.index, dtype=float)), True),
            safe_pct_rank(pitchers.get("milb_2026_ip", pd.Series(index=pitchers.index, dtype=float)), True),
            safe_pct_rank(pitchers.get("milb_2026_games_started", pd.Series(index=pitchers.index, dtype=float)), True),
        ],
        axis=1,
    ).mean(axis=1)
    traffic_command_pct = pd.concat(
        [
            safe_pct_rank(pitchers.get("recent_woba_allowed", pd.Series(index=pitchers.index, dtype=float)), False),
            safe_pct_rank(pitchers.get("recent_three_ball_pitch_rate", pd.Series(index=pitchers.index, dtype=float)), False),
            safe_pct_rank(pitchers.get("milb_2026_bb9", pd.Series(index=pitchers.index, dtype=float)), False),
            safe_pct_rank(pitchers.get("milb_2026_hr9", pd.Series(index=pitchers.index, dtype=float)), False),
            safe_pct_rank(pitchers.get("milb_2026_k9", pd.Series(index=pitchers.index, dtype=float)), True),
        ],
        axis=1,
    ).mean(axis=1)

    components = pd.DataFrame(
        {
            "pitcher_diagnostic_pct": diagnostic_pct,
            "starter_runway_proxy_pct": starter_runway_pct,
            "traffic_command_proxy_pct": traffic_command_pct,
            "market_access_component_score": out["market_access_score"],
            "availability_gate_score": bool_score(pitchers["availability_gate_pass"]),
        }
    )
    out = pd.concat([out, components], axis=1)
    out["fit_preparation_index"] = clipped(
        weighted_mean(
            components,
            {
                "pitcher_diagnostic_pct": 0.25,
                "starter_runway_proxy_pct": 0.25,
                "traffic_command_proxy_pct": 0.25,
                "market_access_component_score": 0.15,
                "availability_gate_score": 0.10,
            },
        )
    )

    out["research_status"] = np.select(
        [
            pitchers["pitcher_milb_diagnostic_status"].eq("positive_diagnostic_watch_not_score"),
            pitchers["pitcher_milb_diagnostic_status"].eq("risk_diagnostic_review_needed"),
            pitchers["pitcher_milb_diagnostic_status"].eq("missing_or_stale_milb_context"),
        ],
        ["diagnostic_watch_locked", "risk_review_needed", "missing_or_stale_milb_context_review"],
        default="diagnostic_neutral_review",
    )

    flags = []
    for row in pitchers.to_dict("records"):
        row_flags = []
        if str(row.get("availability_gate_pass", "")).lower() not in {"true", "1", "1.0"}:
            row_flags.append("availability_gate_failed_or_unknown")
        if str(row.get("pitcher_milb_diagnostic_status", "")) == "risk_diagnostic_review_needed":
            row_flags.append("damage_command_risk_review")
        if "missing" in str(row.get("pitcher_milb_diagnostic_status", "")) or "stale" in str(
            row.get("pitcher_milb_diagnostic_status", "")
        ):
            row_flags.append("milb_context_gap")
        tags = str(row.get("pitcher_milb_diagnostic_tags", ""))
        if "walk_command_risk" in tags:
            row_flags.append("walk_command_risk")
        if "home_run_damage_risk" in tags:
            row_flags.append("home_run_damage_risk")
        if "volatile_stuff_profile" in tags:
            row_flags.append("volatile_stuff_profile")
        row_flags.append("needs_contract_medical_news_manual_check")
        row_flags.append("pitcher_model_not_promoted_score_locked")
        flags.append(make_flags(row_flags))
    out["manual_check_flags"] = flags
    out["slot_fit_message"] = "traffic_command_starter_length_extra_out_resilience"
    out["source_evidence_files"] = f"{PITCHER_INPUT.name};{LAYER1_FEATURE_BLUEPRINT.name}"
    return attach_common_locks(out)


def build_npb_context() -> pd.DataFrame:
    if not NPB_MARKET_FEATURES.exists():
        return pd.DataFrame()
    npb = pd.read_csv(NPB_MARKET_FEATURES)
    keys = ["source_league", "team_code", "normalized_player_name"]
    for key in keys:
        if key not in npb.columns:
            return pd.DataFrame()

    def max_where(frame: pd.DataFrame, value_col: str, stat_type: str | None = None, level: str | None = None) -> float:
        part = frame
        if stat_type is not None and "stat_type" in part.columns:
            part = part[part["stat_type"].eq(stat_type)]
        if level is not None and "level" in part.columns:
            part = part[part["level"].eq(level)]
        if value_col not in part.columns:
            return np.nan
        values = pd.to_numeric(part[value_col], errors="coerce")
        return float(values.max()) if values.notna().any() else np.nan

    rows: list[dict[str, object]] = []
    for keys_values, group in npb.groupby(keys, dropna=False):
        source_league, team_code, normalized_player_name = keys_values
        role_bucket_counts = group.get("npb_market_role_bucket", pd.Series(dtype=str)).dropna().astype(str).value_counts()
        role_bucket = role_bucket_counts.index[0] if len(role_bucket_counts) else "inventory_only"
        rows.append(
            {
                "source_league": source_league,
                "team_code": team_code,
                "normalized_player_name": normalized_player_name,
                "npb_official_stats_attached": True,
                "npb_stat_rows": len(group),
                "npb_market_role_bucket": role_bucket,
                "npb_max_first_team_pa": max_where(group, "PA", "batting", "npb_first_team"),
                "npb_max_farm_pa": max_where(group, "PA", "batting", "npb_farm"),
                "npb_max_ops": max_where(group, "ops", "batting"),
                "npb_max_iso": max_where(group, "iso", "batting"),
                "npb_min_so_pct": max_where(group.assign(_neg_so=-pd.to_numeric(group.get("so_pct"), errors="coerce")), "_neg_so", "batting")
                * -1,
                "npb_max_ip": max_where(group, "ip_float", "pitching"),
                "npb_max_k_minus_bb_pct": max_where(group, "k_minus_bb_pct", "pitching"),
                "npb_min_hr_per_9": max_where(
                    group.assign(_neg_hr9=-pd.to_numeric(group.get("hr_per_9"), errors="coerce")),
                    "_neg_hr9",
                    "pitching",
                )
                * -1,
                "npb_max_traffic_command_proxy": max_where(group, "traffic_command_proxy", "pitching"),
            }
        )
    return pd.DataFrame(rows)


def build_asian_mart() -> pd.DataFrame:
    asian = pd.read_csv(ASIAN_INPUT)
    npb_context = build_npb_context()
    if not npb_context.empty:
        asian = asian.merge(
            npb_context,
            on=["source_league", "team_code", "normalized_player_name"],
            how="left",
            validate="many_to_one",
        )
    else:
        asian["npb_official_stats_attached"] = False

    out = pd.DataFrame(index=asian.index)
    out["fit_slot"] = "asian_quota"
    out["source_pool"] = asian["source_league"]
    out["player_id"] = np.nan
    out["player_name"] = asian["player_name"]
    out["team_or_org"] = asian["team_name"]
    out["age"] = np.nan
    out["throws_or_bats"] = asian.apply(lambda row: f"{row.get('throws', '')}/{row.get('bats', '')}", axis=1)
    out["birth_country"] = asian["nationality"]
    out["position_or_role"] = asian.apply(lambda row: first_existing(row, ["position_group", "position"]), axis=1)
    out["market_access_bucket"] = asian["availability_bucket"]
    out["market_access_score"] = np.where(asian["club_control_risk_flag"].astype(str).str.lower().isin(["true", "1"]), 30.0, 55.0)
    out["availability_gate_pass"] = False
    out["first_pass_gate_pass"] = asian["asian_quota_feasibility_bucket"].eq("nationality_pass_contract_unknown")
    out["candidate_side_primary_signal"] = asian["asian_quota_feasibility_bucket"]
    out["score_interpretation"] = "manual_feasibility_priority_not_player_quality"
    out["score_release_allowed"] = False

    nationality_score = gate_score(
        asian["asian_quota_nationality_gate"],
        pass_values={"pass"},
        fail_values={"fail"},
    )
    contract_score = np.select(
        [
            asian["contract_status_gate"].fillna("").astype(str).str.contains("unknown", na=False),
            asian["contract_status_gate"].fillna("").astype(str).str.contains("free|released|available", regex=True, na=False),
        ],
        [45.0, 100.0],
        default=50.0,
    )
    control_score = np.where(asian["club_control_risk_flag"].astype(str).str.lower().isin(["true", "1"]), 20.0, 70.0)
    league_history_score = gate_score(asian["asian_league_history_gate"], pass_values={"pass_current_roster"})
    npb_stat_attached_score = bool_score(asian.get("npb_official_stats_attached", pd.Series(False, index=asian.index)))

    npb_batter_context_pct = pd.concat(
        [
            safe_pct_rank(asian.get("npb_max_ops", pd.Series(index=asian.index, dtype=float)), True),
            safe_pct_rank(asian.get("npb_max_iso", pd.Series(index=asian.index, dtype=float)), True),
            safe_pct_rank(asian.get("npb_min_so_pct", pd.Series(index=asian.index, dtype=float)), False),
            safe_pct_rank(asian.get("npb_max_first_team_pa", pd.Series(index=asian.index, dtype=float)), True),
        ],
        axis=1,
    ).mean(axis=1)
    npb_pitcher_context_pct = pd.concat(
        [
            safe_pct_rank(asian.get("npb_max_ip", pd.Series(index=asian.index, dtype=float)), True),
            safe_pct_rank(asian.get("npb_max_k_minus_bb_pct", pd.Series(index=asian.index, dtype=float)), True),
            safe_pct_rank(asian.get("npb_min_hr_per_9", pd.Series(index=asian.index, dtype=float)), False),
            safe_pct_rank(asian.get("npb_max_traffic_command_proxy", pd.Series(index=asian.index, dtype=float)), True),
        ],
        axis=1,
    ).mean(axis=1)

    is_pitcher = out["position_or_role"].fillna("").astype(str).str.contains("pitch", case=False, na=False)
    performance_context_pct = np.where(is_pitcher, npb_pitcher_context_pct, npb_batter_context_pct)
    components = pd.DataFrame(
        {
            "asian_nationality_gate_score": nationality_score,
            "contract_unknown_penalty_score": contract_score,
            "club_control_access_score": control_score,
            "asian_league_history_score": league_history_score,
            "npb_stat_context_score": npb_stat_attached_score,
            "npb_performance_context_pct": performance_context_pct,
            "market_access_component_score": out["market_access_score"],
        }
    )
    out = pd.concat([out, components], axis=1)
    out["fit_preparation_index"] = clipped(
        weighted_mean(
            components,
            {
                "asian_nationality_gate_score": 0.25,
                "contract_unknown_penalty_score": 0.15,
                "club_control_access_score": 0.15,
                "asian_league_history_score": 0.10,
                "npb_stat_context_score": 0.10,
                "npb_performance_context_pct": 0.15,
                "market_access_component_score": 0.10,
            },
        )
    )
    out.loc[asian["asian_quota_feasibility_bucket"].eq("nationality_fail_regular_foreign_only"), "fit_preparation_index"] = 0.0
    out["research_status"] = np.select(
        [
            asian["asian_quota_feasibility_bucket"].eq("nationality_pass_contract_unknown"),
            asian["asian_quota_feasibility_bucket"].eq("nationality_unknown"),
            asian["asian_quota_feasibility_bucket"].eq("nationality_fail_regular_foreign_only"),
        ],
        ["manual_contract_salary_buyout_check_locked", "nationality_manual_check_needed", "regular_foreign_only_not_asian_quota"],
        default="manual_feasibility_review_needed",
    )

    flags = []
    for row in asian.to_dict("records"):
        row_flags = []
        bucket = str(row.get("asian_quota_feasibility_bucket", ""))
        if bucket == "nationality_unknown":
            row_flags.append("nationality_unknown")
        if bucket == "nationality_fail_regular_foreign_only":
            row_flags.append("not_asian_quota_eligible")
        if "unknown" in str(row.get("contract_status_gate", "")):
            row_flags.append("contract_salary_buyout_unknown")
        if bool(row.get("club_control_risk_flag", False)):
            row_flags.append("active_roster_low_access")
        if not bool(row.get("npb_official_stats_attached", False)) and row.get("source_league") == "NPB":
            row_flags.append("npb_stats_join_gap")
        if row.get("source_league") == "CPBL":
            row_flags.append("cpbl_current_stat_layer_not_yet_attached")
        row_flags.append("needs_manual_agent_willingness_check")
        flags.append(make_flags(row_flags))
    out["manual_check_flags"] = flags
    out["slot_fit_message"] = "asian_quota_feasibility_first_with_current_league_context"
    out["source_evidence_files"] = f"{ASIAN_INPUT.name};{NPB_MARKET_FEATURES.name}"
    return attach_common_locks(out)


def build_feature_contract(mart: pd.DataFrame) -> pd.DataFrame:
    blueprint = pd.read_csv(LAYER1_FEATURE_BLUEPRINT)
    rows: list[dict[str, object]] = []
    for row in blueprint.to_dict("records"):
        slot = row["slot"]
        candidate_feature = str(row["candidate_feature"])
        if slot == "foreign_hitter":
            available_columns = [
                "model_component_pct",
                "ssg_rhp_unlock_proxy_pct",
                "two_strike_survival_proxy_pct",
                "market_access_component_score",
            ]
            status = "candidate_side_proxy_attached"
        elif slot == "foreign_pitcher":
            available_columns = [
                "pitcher_diagnostic_pct",
                "starter_runway_proxy_pct",
                "traffic_command_proxy_pct",
                "market_access_component_score",
            ]
            status = "diagnostic_proxy_attached_score_locked"
        else:
            available_columns = ["asian_nationality_gate_score", "contract_unknown_penalty_score", "npb_performance_context_pct"]
            status = "manual_feasibility_proxy_attached"
        rows.append(
            {
                **row,
                "run_023_candidate_side_status": status,
                "mart_columns_used": "|".join([col for col in available_columns if col in mart.columns]),
                "release_policy": RELEASE_POLICY,
                "candidate_release_allowed": False,
            }
        )
    return pd.DataFrame(rows)


def build_slot_summary(mart: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for slot, group in mart.groupby("fit_slot", dropna=False):
        rows.append(
            {
                "fit_slot": slot,
                "rows": len(group),
                "research_status_count": group["research_status"].nunique(dropna=False),
                "top_research_status": group["research_status"].value_counts(dropna=False).index[0],
                "median_fit_preparation_index": float(group["fit_preparation_index"].median()),
                "p75_fit_preparation_index": float(group["fit_preparation_index"].quantile(0.75)),
                "release_locked_rows": int(
                    (
                        group["is_final_recommendation"].eq(False)
                        & group["shortlist_label_allowed"].eq(False)
                        & group["candidate_name_release_allowed"].eq(False)
                    ).sum()
                ),
                "candidate_release_policy": RELEASE_POLICY,
            }
        )
    return pd.DataFrame(rows).sort_values("fit_slot")


def build_gate_audit(mart: pd.DataFrame) -> pd.DataFrame:
    checks = [
        {
            "gate": "R1",
            "check": "no_final_recommendations",
            "pass_rows": int(mart["is_final_recommendation"].eq(False).sum()),
            "total_rows": len(mart),
            "status": "pass" if mart["is_final_recommendation"].eq(False).all() else "fail",
            "blocking_gap": "unlock requires all six layers, manual contract/news checks, and final review",
        },
        {
            "gate": "R2",
            "check": "no_shortlist_labels",
            "pass_rows": int(mart["shortlist_label_allowed"].eq(False).sum()),
            "total_rows": len(mart),
            "status": "pass" if mart["shortlist_label_allowed"].eq(False).all() else "fail",
            "blocking_gap": "shortlist labels remain prohibited in Run 023",
        },
        {
            "gate": "R3",
            "check": "candidate_name_release_locked",
            "pass_rows": int(mart["candidate_name_release_allowed"].eq(False).sum()),
            "total_rows": len(mart),
            "status": "pass" if mart["candidate_name_release_allowed"].eq(False).all() else "fail",
            "blocking_gap": "names stay research inventory only",
        },
        {
            "gate": "R4",
            "check": "pitcher_score_not_promoted",
            "pass_rows": int(
                mart.loc[mart["fit_slot"].eq("foreign_pitcher"), "score_interpretation"]
                .eq("diagnostic_research_triage_not_model_score")
                .sum()
            ),
            "total_rows": int(mart["fit_slot"].eq("foreign_pitcher").sum()),
            "status": "pass",
            "blocking_gap": "pitcher failure/translation model still needs injury/news/adaptation and larger historical context",
        },
        {
            "gate": "R5",
            "check": "asian_quota_contract_gap_visible",
            "pass_rows": int(
                mart.loc[mart["fit_slot"].eq("asian_quota"), "manual_check_flags"]
                .str.contains("contract_salary_buyout_unknown", na=False)
                .sum()
            ),
            "total_rows": int(mart["fit_slot"].eq("asian_quota").sum()),
            "status": "pass_visible_gap",
            "blocking_gap": "Asian-quota contract/salary/buyout and agent willingness remain manual checks",
        },
    ]
    return pd.DataFrame(checks)


def main() -> None:
    hitter = build_hitter_mart()
    pitcher = build_pitcher_mart()
    asian = build_asian_mart()
    mart = pd.concat([hitter, pitcher, asian], ignore_index=True, sort=False)
    mart["research_triage_order_within_slot"] = (
        mart.groupby("fit_slot")["fit_preparation_index"].rank(method="first", ascending=False).astype(int)
    )
    mart = mart.sort_values(["fit_slot", "research_triage_order_within_slot"]).reset_index(drop=True)
    mart.to_csv(MART_OUT, index=False)

    build_slot_summary(mart).to_csv(SLOT_SUMMARY_OUT, index=False)
    build_gate_audit(mart).to_csv(GATE_AUDIT_OUT, index=False)
    build_feature_contract(mart).to_csv(FEATURE_CONTRACT_OUT, index=False)

    print(f"wrote {MART_OUT.relative_to(PROJECT_ROOT)} rows={len(mart)}")
    print(f"wrote {SLOT_SUMMARY_OUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {GATE_AUDIT_OUT.relative_to(PROJECT_ROOT)}")
    print(f"wrote {FEATURE_CONTRACT_OUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
