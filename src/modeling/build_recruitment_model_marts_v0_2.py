#!/usr/bin/env python3
"""Build v0.2 recruitment model marts with historical MiLB backfill.

The v0.1 marts were trainable only when a historical KBO foreign player had
pre-KBO MLB/Savant features. Run 019 added official MiLB year-by-year history
for the matched historical rows. This script joins those pre-arrival MiLB
features into the v0.1 marts and exposes a broader model-ready flag:

    has_model_pre_kbo_features = has_pre_kbo_savant_features OR has_pre_kbo_milb

The output still avoids current-player recommendations. It only upgrades the
training evidence base for translation and failure-risk modeling.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"

TRANSLATION_V0_1_PATH = OUTPUT_DIR / "kbo_translation_feature_mart_v0_1.csv"
FAILURE_V0_1_PATH = OUTPUT_DIR / "failure_risk_feature_mart_v0_1.csv"
MILB_FEATURE_PATH = OUTPUT_DIR / "historical_kbo_prearrival_milb_features_v1.csv"

TRANSLATION_V0_2_PATH = OUTPUT_DIR / "kbo_translation_feature_mart_v0_2.csv"
FAILURE_V0_2_PATH = OUTPUT_DIR / "failure_risk_feature_mart_v0_2.csv"
READINESS_V0_2_PATH = OUTPUT_DIR / "kbo_translation_readiness_v0_2.csv"
JOIN_AUDIT_PATH = OUTPUT_DIR / "kbo_translation_feature_mart_v0_2_join_audit.csv"

JOIN_KEYS = ["season", "player_key", "role_model_family"]


def to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "1.0"])


def load_milb_features() -> pd.DataFrame:
    milb = pd.read_csv(MILB_FEATURE_PATH)
    milb["has_pre_kbo_milb"] = to_bool(milb["has_pre_kbo_milb"])
    feature_cols = [
        col
        for col in milb.columns
        if col.startswith("pre_kbo_milb_") or col.startswith("pre_kbo_aaa_") or col.startswith("pre_kbo_aa_")
    ]
    cols = JOIN_KEYS + ["has_pre_kbo_milb", "milb_stat_group"] + feature_cols
    out = milb[cols].drop_duplicates(subset=JOIN_KEYS).copy()
    return out


def enrich_mart(path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    mart = pd.read_csv(path)
    milb = load_milb_features()
    before_rows = len(mart)
    enriched = mart.merge(milb, on=JOIN_KEYS, how="left", validate="many_to_one")
    enriched["has_pre_kbo_savant_features"] = to_bool(enriched["has_pre_kbo_savant_features"])
    enriched["label_available"] = to_bool(enriched["label_available"])
    enriched["has_pre_kbo_milb"] = to_bool(enriched["has_pre_kbo_milb"])
    enriched["has_model_pre_kbo_features"] = (
        enriched["has_pre_kbo_savant_features"] | enriched["has_pre_kbo_milb"]
    )
    enriched["model_feature_source"] = "none"
    enriched.loc[
        enriched["has_pre_kbo_savant_features"] & enriched["has_pre_kbo_milb"], "model_feature_source"
    ] = "savant_and_milb"
    enriched.loc[
        enriched["has_pre_kbo_savant_features"] & ~enriched["has_pre_kbo_milb"], "model_feature_source"
    ] = "savant_only"
    enriched.loc[
        ~enriched["has_pre_kbo_savant_features"] & enriched["has_pre_kbo_milb"], "model_feature_source"
    ] = "milb_only"

    audit = (
        enriched.groupby(["role_model_family", "model_feature_source"], dropna=False)
        .size()
        .reset_index(name="rows")
        .sort_values(["role_model_family", "model_feature_source"])
    )
    audit["input_file"] = path.name
    audit["input_rows"] = before_rows
    audit["output_rows"] = len(enriched)
    return enriched, audit


def build_readiness(translation: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for role_value in ["all", *sorted(translation["role_model_family"].dropna().unique())]:
        role_df = translation if role_value == "all" else translation[translation["role_model_family"].eq(role_value)]
        if role_df.empty:
            continue
        labeled = role_df[role_df["label_available"]]
        model_ready = labeled[labeled["has_model_pre_kbo_features"]]
        rows.append(
            {
                "scope": role_value,
                "rows": len(role_df),
                "label_available_rows": len(labeled),
                "pre_kbo_savant_rows": int(role_df["has_pre_kbo_savant_features"].sum()),
                "pre_kbo_milb_rows": int(role_df["has_pre_kbo_milb"].sum()),
                "model_ready_rows": int(role_df["has_model_pre_kbo_features"].sum()),
                "model_ready_labeled_rows": len(model_ready),
                "success_rows": int(model_ready["success"].fillna(0).astype(int).sum()) if "success" in model_ready else 0,
                "failure_rows": int(model_ready["failure"].fillna(0).astype(int).sum()) if "failure" in model_ready else 0,
                "milb_only_model_ready_rows": int(
                    (
                        role_df["has_model_pre_kbo_features"]
                        & ~role_df["has_pre_kbo_savant_features"]
                        & role_df["has_pre_kbo_milb"]
                    ).sum()
                ),
                "savant_and_milb_rows": int(
                    (role_df["has_pre_kbo_savant_features"] & role_df["has_pre_kbo_milb"]).sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    translation, translation_audit = enrich_mart(TRANSLATION_V0_1_PATH)
    failure, failure_audit = enrich_mart(FAILURE_V0_1_PATH)
    readiness = build_readiness(translation)
    join_audit = pd.concat([translation_audit, failure_audit], ignore_index=True)

    translation.to_csv(TRANSLATION_V0_2_PATH, index=False)
    failure.to_csv(FAILURE_V0_2_PATH, index=False)
    readiness.to_csv(READINESS_V0_2_PATH, index=False)
    join_audit.to_csv(JOIN_AUDIT_PATH, index=False)

    print("wrote", TRANSLATION_V0_2_PATH, translation.shape)
    print("wrote", FAILURE_V0_2_PATH, failure.shape)
    print("wrote", READINESS_V0_2_PATH, readiness.shape)
    print("wrote", JOIN_AUDIT_PATH, join_audit.shape)
    print()
    print(readiness.to_string(index=False))
    print()
    print(join_audit.to_string(index=False))


if __name__ == "__main__":
    main()
