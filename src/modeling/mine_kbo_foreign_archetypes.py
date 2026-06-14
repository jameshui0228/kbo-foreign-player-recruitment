#!/usr/bin/env python3
"""Mine historical KBO foreign-player success and failure archetypes.

This is an outcome-side mining step. The post-KBO columns used here are not
candidate features; they define what past KBO outcomes looked like so later
candidate screens can search for pre-arrival analogues.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"
LABEL_PATH = OUTPUT_DIR / "kbo_foreign_player_season_labels_v0_1.csv"


HITTER_FEATURES = [
    "first_kbo_pa",
    "first_kbo_war",
    "first_kbo_wrc_plus",
    "in_season_replaced",
    "injury_exit_flag",
    "performance_exit_flag",
    "renewed_next_year",
]

PITCHER_FEATURES = [
    "first_kbo_ip",
    "first_kbo_war",
    "first_kbo_era",
    "first_kbo_k_bb_pct",
    "in_season_replaced",
    "injury_exit_flag",
    "performance_exit_flag",
    "renewed_next_year",
]


def numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for col in cols:
        if col not in out.columns:
            out[col] = np.nan
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def choose_cluster_count(x: np.ndarray, max_k: int = 5) -> int:
    if len(x) < 8:
        return 2
    upper = min(max_k, len(x) - 1)
    best_k = 2
    best_score = -1.0
    for k in range(2, upper + 1):
        labels = KMeans(n_clusters=k, random_state=42, n_init=30).fit_predict(x)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(x, labels)
        if score > best_score:
            best_score = score
            best_k = k
    return best_k


def name_hitter_cluster(row: pd.Series) -> str:
    failure_rate = row.get("failure_rate", 0)
    success_rate = row.get("success_rate", 0)
    pa = row.get("median_first_kbo_pa", np.nan)
    war = row.get("median_first_kbo_war", np.nan)
    wrc = row.get("median_first_kbo_wrc_plus", np.nan)
    replaced = row.get("in_season_replaced_rate", 0)
    if failure_rate >= 0.55 or replaced >= 0.40:
        return "hitter_failure_replacement_or_low_impact"
    if success_rate >= 0.65 and pa >= 420 and (war >= 2.5 or wrc >= 120):
        return "hitter_everyday_middle_order_anchor"
    if success_rate >= 0.55 and wrc >= 110:
        return "hitter_offense_first_survivor"
    if pa < 300:
        return "hitter_availability_or_role_fragility"
    return "hitter_marginal_regular"


def name_pitcher_cluster(row: pd.Series) -> str:
    failure_rate = row.get("failure_rate", 0)
    success_rate = row.get("success_rate", 0)
    ip = row.get("median_first_kbo_ip", np.nan)
    war = row.get("median_first_kbo_war", np.nan)
    era = row.get("median_first_kbo_era", np.nan)
    replaced = row.get("in_season_replaced_rate", 0)
    if failure_rate >= 0.55 or replaced >= 0.40:
        return "pitcher_failure_replacement_or_health_risk"
    if success_rate >= 0.65 and ip >= 140 and (war >= 3.0 or era <= 3.8):
        return "pitcher_load_bearing_rotation_anchor"
    if ip >= 120 and era >= 4.7:
        return "pitcher_innings_without_run_prevention"
    if success_rate >= 0.50 and ip >= 100:
        return "pitcher_stabilizer_survivor"
    return "pitcher_low_workload_uncertain"


def safe_median(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return np.nan
    return float(values.median())


def cluster_role(df: pd.DataFrame, role_group: str, features: list[str]) -> pd.DataFrame:
    role = df[df["role_group"].eq(role_group) & df["outcome_available"].eq(True)].copy()
    role = numeric(role, features + ["success", "strong_success", "failure"])
    if role.empty:
        return pd.DataFrame()

    model_df = role[features].copy()
    for col in features:
        median = safe_median(model_df[col])
        fill_value = 0 if pd.isna(median) else median
        model_df[col] = model_df[col].fillna(fill_value)

    x = StandardScaler().fit_transform(model_df)
    k = choose_cluster_count(x)
    labels = KMeans(n_clusters=k, random_state=42, n_init=50).fit_predict(x)
    role["archetype_cluster_id"] = labels
    role["archetype_model_role"] = role_group
    role["archetype_input_features"] = ";".join(features)
    return role


def summarize(assignments: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (role, cluster_id), group in assignments.groupby(["archetype_model_role", "archetype_cluster_id"]):
        row = {
            "archetype_model_role": role,
            "archetype_cluster_id": cluster_id,
            "rows": len(group),
            "seasons": f"{int(group['season'].min())}-{int(group['season'].max())}",
            "success_rate": group["success"].mean(),
            "strong_success_rate": group["strong_success"].mean(),
            "failure_rate": group["failure"].mean(),
            "in_season_replaced_rate": group["in_season_replaced"].mean(),
            "injury_exit_rate": group["injury_exit_flag"].mean(),
            "performance_exit_rate": group["performance_exit_flag"].mean(),
            "renewed_next_year_rate": group["renewed_next_year"].mean(),
            "example_players": " | ".join(group.sort_values("season")["player_name"].astype(str).head(8)),
        }
        for metric in ["first_kbo_pa", "first_kbo_ip", "first_kbo_war", "first_kbo_wrc_plus", "first_kbo_era", "first_kbo_k_bb_pct"]:
            if metric in group.columns:
                row[f"median_{metric}"] = safe_median(group[metric])
        rows.append(row)

    summary = pd.DataFrame(rows)
    names = []
    for _, row in summary.iterrows():
        if row["archetype_model_role"] == "hitter":
            names.append(name_hitter_cluster(row))
        else:
            names.append(name_pitcher_cluster(row))
    summary["archetype_name"] = names
    return summary.sort_values(["archetype_model_role", "failure_rate", "success_rate"], ascending=[True, False, False])


def build_failure_patterns(assignments: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    merged = assignments.merge(
        summary[["archetype_model_role", "archetype_cluster_id", "archetype_name"]],
        on=["archetype_model_role", "archetype_cluster_id"],
        how="left",
    )
    failure = merged[merged["failure"].eq(1)].copy()
    if failure.empty:
        return pd.DataFrame()

    rows = []
    for (role, archetype), group in failure.groupby(["archetype_model_role", "archetype_name"]):
        rows.append(
            {
                "role_group": role,
                "failure_archetype": archetype,
                "failure_rows": len(group),
                "share_of_role_failures": len(group) / len(failure[failure["archetype_model_role"].eq(role)]),
                "injury_exit_rate": group["injury_exit_flag"].mean(),
                "performance_exit_rate": group["performance_exit_flag"].mean(),
                "in_season_replaced_rate": group["in_season_replaced"].mean(),
                "median_pa": safe_median(group["first_kbo_pa"]),
                "median_ip": safe_median(group["first_kbo_ip"]),
                "median_war": safe_median(group["first_kbo_war"]),
                "median_wrc_plus": safe_median(group["first_kbo_wrc_plus"]),
                "median_era": safe_median(group["first_kbo_era"]),
                "example_failures": " | ".join(group.sort_values("season")["player_name"].astype(str).head(8)),
            }
        )
    return pd.DataFrame(rows).sort_values(["role_group", "failure_rows"], ascending=[True, False])


def build_proxy_label_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    proxy = df[df["label_available"].eq(True)].copy()
    for (period, role), group in proxy.assign(
        period=np.where(proxy["outcome_available"].eq(True), "statiz_outcome_attached", "renewal_release_proxy_only")
    ).groupby(["period", "role_group"]):
        rows.append(
            {
                "period": period,
                "role_group": role,
                "rows": len(group),
                "success_rate": group["success"].mean(),
                "failure_rate": group["failure"].mean(),
                "strong_success_rate": group["strong_success"].mean(),
                "source_confidence_median": group["source_confidence_1_5"].median(),
            }
        )
    return pd.DataFrame(rows).sort_values(["period", "role_group"])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    labels = pd.read_csv(LABEL_PATH)
    labels["outcome_available"] = labels["outcome_available"].astype(str).str.lower().isin(["true", "1"])
    labels["label_available"] = labels["label_available"].astype(str).str.lower().isin(["true", "1"])

    hitter = cluster_role(labels, "hitter", HITTER_FEATURES)
    pitcher = cluster_role(labels, "starter", PITCHER_FEATURES)
    assignments = pd.concat([hitter, pitcher], ignore_index=True, sort=False)
    summary = summarize(assignments)
    failure = build_failure_patterns(assignments, summary)
    proxy = build_proxy_label_summary(labels)

    assignments.to_csv(OUTPUT_DIR / "kbo_foreign_archetype_assignments_v0_1.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "kbo_foreign_archetype_summary_v0_1.csv", index=False)
    failure.to_csv(OUTPUT_DIR / "kbo_foreign_failure_patterns_v0_1.csv", index=False)
    proxy.to_csv(OUTPUT_DIR / "kbo_foreign_proxy_label_summary_v0_1.csv", index=False)

    print("wrote", OUTPUT_DIR / "kbo_foreign_archetype_assignments_v0_1.csv", assignments.shape)
    print("wrote", OUTPUT_DIR / "kbo_foreign_archetype_summary_v0_1.csv", summary.shape)
    print("wrote", OUTPUT_DIR / "kbo_foreign_failure_patterns_v0_1.csv", failure.shape)
    print("wrote", OUTPUT_DIR / "kbo_foreign_proxy_label_summary_v0_1.csv", proxy.shape)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
