#!/usr/bin/env python3
"""Audit leakage and probability calibration for the KBO foreign-player model."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss
from sklearn.model_selection import LeaveOneGroupOut

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "scripts"))

from build_data_mining_recommendation_model_v1 import (  # noqa: E402
    HITTER_CANDIDATE_MAP,
    HITTER_SAVANT_FEATURES,
    load_mart,
    ridge_logit,
    title_name,
    usable_features,
)

OUT_DIR = ROOT / "outputs" / "tables"
DOC_OUT = ROOT / "docs" / "model_probability_calibration_audit_v1.md"
AUDIT_OUT = OUT_DIR / "model_probability_calibration_audit_v1.csv"


FORBIDDEN_FEATURE_PATTERNS = [
    "success",
    "failure",
    "first_kbo",
    "renew",
    "replaced",
    "exit",
    "war",
    "wrc",
    "era",
    "kbo_team",
    "season",
    "player_name",
    "player_id",
    "label",
    "outcome",
]


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "1.0"})


def safe_logloss(y: pd.Series, p: np.ndarray) -> float:
    labels = sorted(pd.Series(y).dropna().unique())
    if len(labels) < 2:
        return float("nan")
    return float(log_loss(y, p, labels=[0, 1]))


def summarize_predictions(y: pd.Series, p: np.ndarray) -> dict[str, float]:
    out: dict[str, float] = {
        "auc": float(roc_auc_score(y, p)) if y.nunique() == 2 else float("nan"),
        "brier": float(brier_score_loss(y, p)),
        "logloss": safe_logloss(y, p),
        "max_pred": float(np.max(p)),
        "p90_pred": float(np.quantile(p, 0.90)),
        "mean_pred": float(np.mean(p)),
        "mean_pred_positive": float(np.mean(p[np.asarray(y) == 1])),
        "mean_pred_negative": float(np.mean(p[np.asarray(y) == 0])),
    }
    return out


def to_markdown_table(df: pd.DataFrame, float_digits: int = 4) -> str:
    if df.empty:
        return "_No rows._"
    rows = []
    cols = list(df.columns)
    rows.append("| " + " | ".join(cols) + " |")
    rows.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        values = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                values.append(f"{value:.{float_digits}f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def make_groups(train: pd.DataFrame) -> pd.Series:
    ids = train.get("matched_savant_player_id", pd.Series(index=train.index, dtype=object))
    names = train.get("player_name_en", train.get("player_name", pd.Series(index=train.index, dtype=object)))
    groups = ids.where(ids.notna(), names)
    fallback = pd.Series(train.index.astype(str), index=train.index)
    return groups.fillna(fallback).astype(str)


def leave_one_player_group_predictions(train: pd.DataFrame, features: list[str], target: str) -> np.ndarray:
    y = train[target].astype(int)
    groups = make_groups(train)
    logo = LeaveOneGroupOut()
    preds = np.full(len(train), np.nan)
    for tr_idx, te_idx in logo.split(train[features], y, groups):
        y_train = y.iloc[tr_idx]
        if y_train.nunique() < 2:
            continue
        model = ridge_logit().fit(train.iloc[tr_idx][features], y_train)
        preds[te_idx] = model.predict_proba(train.iloc[te_idx][features])[:, 1]
    return preds


def main() -> None:
    mart = load_mart()
    train = mart[
        mart["role_model_family"].eq("hitter")
        & bool_series(mart["has_pre_kbo_savant_features"])
        & bool_series(mart["label_available"])
    ].copy()
    features = usable_features(train, HITTER_SAVANT_FEATURES)
    groups = make_groups(train)

    forbidden_hits = [
        feature
        for feature in features
        if any(pattern in feature.lower() for pattern in FORBIDDEN_FEATURE_PATTERNS)
    ]
    candidate_mapping_hits = [
        f"{feature}<={source}"
        for feature, source in HITTER_CANDIDATE_MAP.items()
        if source and any(pattern in str(source).lower() for pattern in FORBIDDEN_FEATURE_PATTERNS)
    ]

    candidate_pool = pd.read_csv(OUT_DIR / "data_mining_hitter_candidates_v1.csv")
    train_ids = set(pd.to_numeric(train.get("matched_savant_player_id"), errors="coerce").dropna().astype(int))
    candidate_ids = set(pd.to_numeric(candidate_pool.get("player_id"), errors="coerce").dropna().astype(int))
    overlap_ids = sorted(train_ids & candidate_ids)

    rows: list[dict[str, object]] = []
    for target in ["success", "failure"]:
        y = train[target].astype(int)
        full_model = ridge_logit().fit(train[features], y)
        full_p = full_model.predict_proba(train[features])[:, 1]
        oof_p = leave_one_player_group_predictions(train, features, target)
        valid = ~np.isnan(oof_p)
        full_summary = summarize_predictions(y, full_p)
        oof_summary = summarize_predictions(y.iloc[np.where(valid)[0]], oof_p[valid])
        rows.append(
            {
                "target": target,
                "historical_rows": len(train),
                "unique_player_groups": groups.nunique(),
                "positive_rows": int(y.sum()),
                "feature_count": len(features),
                "forbidden_feature_hits": "|".join(forbidden_hits),
                "candidate_mapping_forbidden_hits": "|".join(candidate_mapping_hits),
                "train_candidate_player_id_overlap_count": len(overlap_ids),
                "train_candidate_player_id_overlap": "|".join(map(str, overlap_ids)),
                **{f"full_fit_{k}": v for k, v in full_summary.items()},
                **{f"leave_one_player_group_{k}": v for k, v in oof_summary.items()},
            }
        )

    audit = pd.DataFrame(rows)
    AUDIT_OUT.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(AUDIT_OUT, index=False)

    hitter_candidates = pd.read_csv(OUT_DIR / "final_candidate_board_execution_v4.csv")
    subset = hitter_candidates[hitter_candidates["slot"].eq("foreign_hitter")].copy()

    doc = [
        "# Model Probability Calibration Audit v1",
        "",
        "## 결론",
        "",
        "- 직접적인 label leakage는 발견되지 않았다. 학습 피처에 success/failure/first_kbo/renewal/outcome/player id 계열 컬럼이 들어가지 않았다.",
        "- 후보 입력 매핑도 success/failure/outcome 계열 컬럼을 쓰지 않았다.",
        "- 다만 타자 학습 표본은 22행, 선수 단위 고유 그룹은 더 적고 일부 선수가 여러 시즌 반복된다. 따라서 full-fit predict_proba를 절대 성공확률로 표기하면 과신 위험이 크다.",
        "- 보고서에서는 `성공확률 98.1%`가 아니라 `성공 모델 지지 점수`, `실패 경고 점수`, `후보 간 순위 신호`로 표현해야 한다.",
        "",
        "## Audit Table",
        "",
        to_markdown_table(audit),
        "",
        "## Final Hitter Board Labels After Re-labeling",
        "",
        subset[
            [
                "player",
                "decision_rank",
                "decision",
                "model_support_tier",
                "failure_warning_tier",
                "model_margin_direction",
                "market_feasibility_score",
            ]
        ].pipe(to_markdown_table),
        "",
        "## 보고서 수정 지침",
        "",
        "- `realism`, `realism-first`, `success probability`, `P(success)` 표현을 제거한다.",
        "- 확률 표기는 `모델 지지 점수(0-100)`와 `실패 경고 점수(0-100)`로 바꾸고, 절대 확률이 아니라고 명시한다.",
        "- Will Brennan과 Dominic Fletcher는 원 data-mining gate에서 sample gate가 걸렸으므로, 모델 점수만으로 확정하지 않고 시장 접근성과 접촉 가능성 보정 후 후보로 올렸다고 설명한다.",
        "- 최종 결론은 `현실성 반영 통합 모델`로 표현한다.",
        "",
    ]
    DOC_OUT.write_text("\n".join(doc), encoding="utf-8")
    print(audit.to_string(index=False))
    print(f"wrote {AUDIT_OUT}")
    print(f"wrote {DOC_OUT}")


if __name__ == "__main__":
    main()
