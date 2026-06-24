from __future__ import annotations

import json
import math
import textwrap
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables"
DOCS = ROOT / "docs"
NOTEBOOKS = ROOT / "notebooks"


SLOT_LABEL = {
    "foreign_pitcher": "외인투수",
    "foreign_hitter": "외인타자",
}

WEIGHTS = {
    "foreign_pitcher": {
        "ssg_fit_component": 0.32,
        "kbo_translation_component": 0.22,
        "market_realism_component": 0.17,
        "tool_process_component": 0.09,
        "surplus_access_component": 0.10,
        "failure_resilience_component": 0.10,
    },
    "foreign_hitter": {
        "ssg_fit_component": 0.34,
        "kbo_translation_component": 0.24,
        "market_realism_component": 0.15,
        "tool_process_component": 0.08,
        "surplus_access_component": 0.09,
        "failure_resilience_component": 0.10,
    },
}

MARKET_STATUS_PENALTY = {
    "contract_verification_needed": 0.5,
    "manual_contact_priority_locked": 2.5,
    "low_access_or_unknown_market_status": 5.0,
    "contract_blocker_watch": 7.0,
    "medical_hold_before_scouting": 10.0,
}

CONTRACT_ACCESS_ADJUSTMENT = {
    "recent_free_agent_or_released_high_access": 2.0,
    "recent_dfa_high_access": 1.5,
    "non40man_or_outrighted_medium_access": 0.0,
    "40man_nonactive_contract_blocker": -6.0,
    "active_mlb_contract_blocker": -10.0,
}

MEDICAL_PENALTY = {
    "no_public_medical_signal_from_roster_transactions": 0.0,
    "medical_history_watch": 3.0,
    "medical_hold_current_or_recent": 9.0,
}


def cell_md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in textwrap.dedent(source).strip().splitlines()],
    }


def cell_code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in textwrap.dedent(source).strip().splitlines()],
    }


def value(row: pd.Series, column: str, default: float = 0.0) -> float:
    raw = row.get(column, default)
    if pd.isna(raw):
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def text(row: pd.Series, column: str) -> str:
    raw = row.get(column, "")
    if pd.isna(raw):
        return ""
    return str(raw)


def title_name(name: object) -> str:
    if pd.isna(name):
        return ""
    name = str(name).strip()
    if not name:
        return ""
    if "," in name:
        last, first = [part.strip() for part in name.split(",", 1)]
        return f"{first} {last}".strip()
    return " ".join(part.capitalize() if part.islower() else part for part in name.split())


def weighted_component_score(row: pd.Series, slot: str) -> float:
    weights = WEIGHTS[slot]
    return sum(value(row, col, 50.0) * weight for col, weight in weights.items())


def hitter_position_adjustment(row: pd.Series) -> tuple[float, str]:
    position = text(row, "primary_position").lower()
    abbrev = text(row, "primary_position_abbrev").upper()
    if "outfield" in position or abbrev in {"LF", "CF", "RF", "OF"}:
        return 4.0, "OF 우선순위 충족"
    if "first base" in position or "third base" in position or "second base" in position:
        return -5.0, "외야 우선순위 미충족: 코너/내야 보조 후보"
    if "catcher" in position:
        return -12.0, "외야 우선순위 미충족: 포수"
    return -4.0, "외야 적합성 확인 필요"


def hitter_sample_adjustment(row: pd.Series) -> tuple[float, str]:
    pa = value(row, "hitter_recent_pa", 0.0)
    if pa >= 150:
        return 3.0, f"타격 표본 안정: recent PA {pa:.0f}"
    if pa >= 50:
        return 1.0, f"타격 표본 보통: recent PA {pa:.0f}"
    if pa >= 25:
        return -1.5, f"타격 표본 작음: recent PA {pa:.0f}"
    return -4.0, f"타격 표본 매우 작음: recent PA {pa:.0f}"


def pitcher_role_adjustment(row: pd.Series) -> tuple[float, str]:
    bucket = text(row, "pitcher_milb_role_continuity_bucket")
    starts = value(row, "pitcher_milb_2026_games_started", 0.0)
    ip = value(row, "pitcher_milb_2026_ip", 0.0)
    if bucket == "current_aaa_starter_load":
        return 5.0, f"AAA 선발 지속성: {starts:.0f} GS, {ip:.1f} IP"
    if bucket == "current_aaa_swing_or_multi_inning":
        return 2.0, f"AAA 스윙/멀티이닝: {starts:.0f} GS, {ip:.1f} IP"
    if bucket == "current_aaa_bullpen_track":
        return -4.0, f"불펜 트랙 주의: {starts:.0f} GS, {ip:.1f} IP"
    if "noncurrent" in bucket:
        return -3.0, f"현행 2026 트랙 약함: {bucket}"
    return -2.0, "선발/멀티이닝 지속성 확인 필요"


def age_adjustment(row: pd.Series, slot: str) -> tuple[float, str]:
    age = value(row, "age", 0.0)
    if age <= 0:
        return 0.0, "나이 정보 없음"
    if slot == "foreign_pitcher":
        if age >= 36:
            return -3.0, f"연령 리스크: {age:.0f}세"
        if age <= 27:
            return 1.0, f"연령 upside: {age:.0f}세"
    if slot == "foreign_hitter":
        if age >= 33:
            return -3.0, f"연령 리스크: {age:.0f}세"
        if age <= 27:
            return 1.0, f"연령 upside: {age:.0f}세"
    return 0.0, f"연령 정상권: {age:.0f}세"


def categorical_penalty(row: pd.Series) -> tuple[float, list[str]]:
    penalty = 0.0
    reasons: list[str] = []
    checks = [
        ("market_realism_status", MARKET_STATUS_PENALTY),
        ("medical_risk_bucket", MEDICAL_PENALTY),
    ]
    for column, mapping in checks:
        key = text(row, column)
        points = mapping.get(key, 1.0 if key else 0.0)
        if points:
            penalty += points
            reasons.append(f"{column}={key} (-{points:g})")

    contract_key = text(row, "contract_control_bucket")
    contract_adj = CONTRACT_ACCESS_ADJUSTMENT.get(contract_key, 0.0)
    if contract_adj > 0:
        penalty -= contract_adj
        reasons.append(f"contract_access_bonus={contract_key} (+{contract_adj:g})")
    elif contract_adj < 0:
        penalty += abs(contract_adj)
        reasons.append(f"contract_access_risk={contract_key} ({contract_adj:g})")
    return penalty, reasons


def build_reason(row: pd.Series, slot: str) -> str:
    if slot == "foreign_pitcher":
        parts = [
            "SSG 선발 runway/불펜 tax 문제에 맞춘 SP/multi-inning 후보",
            f"SSG fit {value(row, 'ssg_fit_component'):.1f}",
            f"KBO translation {value(row, 'kbo_translation_component'):.1f}",
            f"market {value(row, 'market_realism_component'):.1f}",
        ]
        if not math.isnan(value(row, "pitcher_milb_2026_ip", float("nan"))):
            parts.append(
                f"2026 MiLB {value(row, 'pitcher_milb_2026_ip'):.1f} IP/{value(row, 'pitcher_milb_2026_games_started'):.0f} GS"
            )
        return "; ".join(parts)

    parts = [
        "SSG runner-on-first 전환 병목을 겨냥한 OF/DH 후보",
        f"SSG fit {value(row, 'ssg_fit_component'):.1f}",
        f"KBO translation {value(row, 'kbo_translation_component'):.1f}",
        f"market {value(row, 'market_realism_component'):.1f}",
    ]
    if not math.isnan(value(row, "hitter_recent_pa", float("nan"))):
        parts.append(
            f"recent PA {value(row, 'hitter_recent_pa'):.0f}, wOBA {value(row, 'hitter_recent_woba'):.3f}"
        )
    return "; ".join(parts)


def score_pool(packet: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    df = packet.merge(roster, on="player_id", how="left", suffixes=("", "_roster"))
    df = df[df["fit_slot"].isin(["foreign_pitcher", "foreign_hitter"])].copy()

    records: list[dict] = []
    for _, row in df.iterrows():
        slot = text(row, "fit_slot")
        base = weighted_component_score(row, slot)
        categorical, categorical_reasons = categorical_penalty(row)
        role_adj, role_note = pitcher_role_adjustment(row) if slot == "foreign_pitcher" else hitter_position_adjustment(row)
        sample_adj, sample_note = (0.0, "") if slot == "foreign_pitcher" else hitter_sample_adjustment(row)
        age_adj, age_note = age_adjustment(row, slot)
        unified_score = base + role_adj + sample_adj + age_adj - categorical

        if slot == "foreign_hitter":
            position = text(row, "primary_position").lower()
            abbrev = text(row, "primary_position_abbrev").upper()
            hard_gate = "pass" if ("outfield" in position or abbrev in {"LF", "CF", "RF", "OF"}) else "position_hold"
        else:
            hard_gate = "pass" if text(row, "primary_position") == "Pitcher" else "position_hold"

        records.append(
            {
                "fit_slot": slot,
                "slot_label": SLOT_LABEL[slot],
                "player_id": row.get("player_id"),
                "player_name": title_name(row.get("player_name_roster") or row.get("player_name")),
                "team_or_org": row.get("team_or_org"),
                "primary_position": row.get("primary_position"),
                "primary_position_abbrev": row.get("primary_position_abbrev"),
                "age": row.get("age"),
                "bat_side": row.get("bat_side"),
                "pitch_hand": row.get("pitch_hand"),
                "birth_country": row.get("birth_country"),
                "unified_fit_score": round(unified_score, 3),
                "weighted_component_score": round(base, 3),
                "categorical_risk_penalty": round(categorical, 3),
                "role_or_position_adjustment": round(role_adj, 3),
                "sample_adjustment": round(sample_adj, 3),
                "age_adjustment": round(age_adj, 3),
                "hard_gate": hard_gate,
                "role_or_position_note": role_note,
                "sample_note": sample_note,
                "age_note": age_note,
                "data_mining_reason": build_reason(row, slot),
                "structured_risk_check": " | ".join(categorical_reasons) or "structured-data low current risk",
                "market_realism_status": row.get("market_realism_status"),
                "contract_control_bucket": row.get("contract_control_bucket"),
                "medical_risk_bucket": row.get("medical_risk_bucket"),
                "sensitivity_band": row.get("sensitivity_band"),
                "ssg_fit_component": round(value(row, "ssg_fit_component"), 3),
                "kbo_translation_component": round(value(row, "kbo_translation_component"), 3),
                "market_realism_component": round(value(row, "market_realism_component"), 3),
                "tool_process_component": round(value(row, "tool_process_component"), 3),
                "surplus_access_component": round(value(row, "surplus_access_component"), 3),
                "failure_resilience_component": round(value(row, "failure_resilience_component"), 3),
                "internal_prior_score": round(value(row, "risk_adjusted_fit_score_internal"), 3),
                "hitter_recent_pa": row.get("hitter_recent_pa"),
                "hitter_recent_woba": row.get("hitter_recent_woba"),
                "hitter_recent_bb_pct": row.get("hitter_recent_bb_pct"),
                "hitter_recent_k_pct": row.get("hitter_recent_k_pct"),
                "hitter_recent_hardhit_rate": row.get("hitter_recent_hardhit_rate"),
                "hitter_recent_barrel_rate": row.get("hitter_recent_barrel_rate"),
                "pitcher_milb_role_continuity_bucket": row.get("pitcher_milb_role_continuity_bucket"),
                "pitcher_milb_2026_ip": row.get("pitcher_milb_2026_ip"),
                "pitcher_milb_2026_games_started": row.get("pitcher_milb_2026_games_started"),
                "pitcher_milb_2026_k9": row.get("pitcher_milb_2026_k9"),
                "pitcher_milb_2026_bb9": row.get("pitcher_milb_2026_bb9"),
                "pitcher_milb_2026_hr9": row.get("pitcher_milb_2026_hr9"),
            }
        )

    scored = pd.DataFrame(records)
    scored["unified_rank_within_slot"] = (
        scored.sort_values(["hard_gate", "unified_fit_score"], ascending=[True, False])
        .groupby("fit_slot")
        .cumcount()
        + 1
    )
    scored = scored.sort_values(["fit_slot", "hard_gate", "unified_fit_score"], ascending=[True, True, False])

    # Final output uses position hard-gate. Non-OF hitter rows remain in the pool
    # for audit but are not allowed into the top-three hitter output.
    top_rows = []
    for slot, sub in scored.groupby("fit_slot"):
        eligible = sub[sub["hard_gate"].eq("pass")].copy()
        eligible = eligible.sort_values("unified_fit_score", ascending=False).head(3)
        eligible["recommendation_rank"] = range(1, len(eligible) + 1)
        top_rows.append(eligible)
    top3 = pd.concat(top_rows, ignore_index=True)
    front_cols = [
        "slot_label",
        "recommendation_rank",
        "player_name",
        "team_or_org",
        "primary_position",
        "primary_position_abbrev",
        "age",
        "bat_side",
        "pitch_hand",
        "birth_country",
        "unified_fit_score",
        "weighted_component_score",
        "categorical_risk_penalty",
        "role_or_position_adjustment",
        "sample_adjustment",
        "age_adjustment",
        "data_mining_reason",
        "role_or_position_note",
        "sample_note",
        "structured_risk_check",
    ]
    top3 = top3[front_cols + [c for c in top3.columns if c not in front_cols]]
    return scored, top3


def feature_blocks() -> pd.DataFrame:
    rows = []
    block_map = [
        ("SSG Need Fit", "Layer 1", "SSG 상황별 병목과 후보 능력의 직접 적합도", "ssg_fit_component"),
        ("KBO Translation", "Layer 4", "해외 성과가 KBO에서 통할 가능성", "kbo_translation_component"),
        ("Market Realism", "Layer 3", "로스터/계약/접근 가능성", "market_realism_component"),
        ("Tool Process", "Layer 2/4", "KBO 외인 유형과 후보 세부 지표의 연결성", "tool_process_component"),
        ("Surplus Access", "Layer 3", "비용 대비 접근성과 시장 비효율", "surplus_access_component"),
        ("Failure Resilience", "Layer 5", "실패 리스크를 버틸 가능성", "failure_resilience_component"),
    ]
    for slot, weights in WEIGHTS.items():
        for block, source_layer, explanation, column in block_map:
            rows.append(
                {
                    "slot": slot,
                    "slot_label": SLOT_LABEL[slot],
                    "feature_block": block,
                    "source_layer": source_layer,
                    "input_column": column,
                    "weight": weights[column],
                    "plain_explanation": explanation,
                }
            )
    return pd.DataFrame(rows)


def write_docs(top3: pd.DataFrame, blocks: pd.DataFrame) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    def markdown_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "_No rows._"
        display = df.fillna("").astype(str)
        headers = list(display.columns)
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        for _, row in display.iterrows():
            values = [str(row[col]).replace("\n", " ").replace("|", "/") for col in headers]
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)

    lines = [
        "# Unified Recommendation Model Structured-Only v2",
        "",
        "Generated: 2026-06-22 KST",
        "",
        "## 한 줄 요약",
        "",
        "1~6번 분석을 각각 따로 결론 내지 않고, 하나의 `SSG Foreign Player Fit Model`로 통합했다.",
        "",
        "**중요 변경:** 기사, 인터뷰, 뉴스, 스카우팅 문장, 글 기반 텍스트 변수는 최종 모델 input에서 제외했다. 이 v2는 숫자형 성적 데이터와 구조화된 로스터/포지션/나이/계약 접근성/메디컬 상태 데이터만 사용한다.",
        "",
        "모델의 목적은 다음과 같다.",
        "",
        "> 여러 데이터 블록을 input으로 넣고, SSG에 맞는 외인투수 3명과 외인타자 3명을 output으로 뽑는다.",
        "",
        "## 데이터 마이닝 과정",
        "",
        "1. **SSG 숨은 약점 마이닝**: 2026 SSG 상황별/역할별 split에서 팀 고유 병목을 찾았다.",
        "2. **KBO 외인 성공/실패 유형 마이닝**: 과거 외국인 선수의 성공/실패 유형을 feature block으로 바꿨다.",
        "3. **후보 시장 구축**: MLB/AAA/AA/NPB/CPBL 성적, 로스터, 포지션, 계약 접근성으로 실제 후보 시장을 만들었다.",
        "4. **KBO 번역 모델**: 해외 성과가 KBO에서 통할 가능성을 보수적으로 반영했다.",
        "5. **실패 리스크 모델**: 구조화된 메디컬/계약/로스터 위험만 penalty로 반영했다.",
        "6. **SSG fit ranking**: 모든 feature block을 하나의 점수로 통합하고 Top 3를 출력했다.",
        "",
        "이 결과는 구조화 데이터 기반 추천 후보이며, 계약 확정 추천은 아니다. 계약 조건과 메디컬 세부 확인은 마지막 수동 검토로 남는다.",
        "",
        "## 통합 점수 공식",
        "",
        "```text",
        "Unified Fit Score =",
        "  weighted feature-block score",
        "+ role/position adjustment",
        "+ sample adjustment",
        "+ age adjustment",
        "- categorical risk penalty",
        "```",
        "",
        "타자는 외야 우선순위를 반영해 포수/내야수 후보를 Top 3에서 제외했다. 투수는 SSG 메시지에 맞춰 선발/멀티이닝 지속성을 추가 보정했다.",
        "",
        "## Feature Blocks",
        "",
        markdown_table(blocks),
        "",
        "## 최종 Top 3 Output",
        "",
        markdown_table(top3[
            [
                "slot_label",
                "recommendation_rank",
                "player_name",
                "team_or_org",
                "primary_position",
                "age",
                "unified_fit_score",
                "data_mining_reason",
        "structured_risk_check",
            ]
        ]),
        "",
        "## Presentation Message",
        "",
        "We did not use articles or text-derived variables in the final model. The structured-only model first mines SSG's hidden needs, translates those needs into numeric candidate-side feature blocks, filters the market by acquisition realism, penalizes structured failure risk, and only then outputs three pitchers and three hitters.",
        "",
    ]
    (DOCS / "unified_recommendation_model_structured_only_v2.md").write_text("\n".join(lines), encoding="utf-8")


def write_notebook() -> None:
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    nb = {
        "cells": [
            cell_md(
                """
                # Tutorial: Unified SSG Foreign Player Recommendation Model Structured-Only v2

                이 노트북은 1~6번 레이어를 하나의 input-output 모델로 통합해서
                외인투수 3명, 외인타자 3명을 출력하는 최종 설명용 노트북이다.

                기사/뉴스/인터뷰/문장형 데이터는 최종 모델 input에서 제외했다.
                """
            ),
            cell_md(
                """
                ## 핵심 아이디어

                6개의 분석은 따로 노는 모델이 아니라 하나의 추천 모델 안에 들어가는 feature block이다.

                - Layer 1: SSG Need Fit
                - Layer 2: KBO Archetype / Tool Process
                - Layer 3: Market Realism
                - Layer 4: KBO Translation
                - Layer 5: Structured Failure Resilience / Risk Penalty
                - Layer 6: Unified Ranking
                """
            ),
            cell_code(
                """
                from pathlib import Path
                import pandas as pd

                ROOT = Path.cwd()
                if not (ROOT / "outputs").exists():
                    ROOT = ROOT.parent
                OUT = ROOT / "outputs" / "tables"

                pd.set_option("display.max_columns", 80)
                pd.set_option("display.max_colwidth", 140)
                """
            ),
            cell_code(
                """
                blocks = pd.read_csv(OUT / "unified_recommendation_feature_blocks_structured_only_v2.csv")
                blocks
                """
            ),
            cell_md(
                """
                ## 최종 후보 출력

                아래 표가 통합 모델의 최종 output이다.

                단, 이 표는 계약 확정 추천이 아니라 **데이터 기반 Top 3 검토 후보**다.
                """
            ),
            cell_code(
                """
                top3 = pd.read_csv(OUT / "unified_foreign_recommendations_top3_structured_only_v2.csv")
                display_cols = [
                    "slot_label",
                    "recommendation_rank",
                    "player_name",
                    "team_or_org",
                    "primary_position",
                    "age",
                    "unified_fit_score",
                    "data_mining_reason",
                    "structured_risk_check",
                ]
                top3[display_cols]
                """
            ),
            cell_md(
                """
                ## 후보 풀이 어떻게 줄어들었는가

                전체 후보 풀에서 포지션/역할 hard gate를 통과한 선수만 Top 3에 들어간다.
                """
            ),
            cell_code(
                """
                pool = pd.read_csv(OUT / "unified_foreign_recommendation_pool_structured_only_v2.csv")
                pool.groupby(["slot_label", "hard_gate"]).size().reset_index(name="rows")
                """
            ),
            cell_code(
                """
                pool.sort_values(["slot_label", "unified_fit_score"], ascending=[True, False]).groupby("slot_label").head(8)[
                    ["slot_label", "player_name", "primary_position", "unified_fit_score", "hard_gate", "role_or_position_note", "structured_risk_check"]
                ]
                """
            ),
            cell_md(
                """
                ## 발표용 해석

                이 모델은 "좋은 선수 순위표"가 아니라 "SSG의 숨은 문제에 맞고, KBO에서 통할 가능성이 있으며, 실제 시장에서 접근 가능하고, 구조화된 실패 리스크가 과도하지 않은 선수"를 찾는다.

                기사/뉴스/인터뷰 텍스트는 최종 점수에 사용하지 않는다.

                그래서 final score는 다음 네 가지를 동시에 반영한다.

                1. SSG에게 필요한 능력인가?
                2. KBO로 번역될 가능성이 있는가?
                3. 실제로 데려올 수 있는 시장인가?
                4. 실패 리스크가 감당 가능한가?
                """
            ),
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path = NOTEBOOKS / "17_unified_recommendation_model_structured_only_v2.ipynb"
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    packet = pd.read_csv(OUT / "ssg_fit_source_fill_packet_v0_1.csv")
    roster = pd.read_csv(OUT / "mlb_roster_status_latest.csv")
    roster_cols = [
        "player_id",
        "player_name",
        "primary_position",
        "primary_position_type",
        "primary_position_abbrev",
        "bat_side",
        "pitch_hand",
        "age",
        "birth_country",
    ]
    roster = roster[roster_cols].drop_duplicates("player_id")

    scored, top3 = score_pool(packet, roster)
    blocks = feature_blocks()

    OUT.mkdir(parents=True, exist_ok=True)
    scored.to_csv(OUT / "unified_foreign_recommendation_pool_structured_only_v2.csv", index=False)
    top3.to_csv(OUT / "unified_foreign_recommendations_top3_structured_only_v2.csv", index=False)
    blocks.to_csv(OUT / "unified_recommendation_feature_blocks_structured_only_v2.csv", index=False)
    write_docs(top3, blocks)
    write_notebook()

    print("wrote outputs/tables/unified_foreign_recommendation_pool_structured_only_v2.csv")
    print("wrote outputs/tables/unified_foreign_recommendations_top3_structured_only_v2.csv")
    print("wrote outputs/tables/unified_recommendation_feature_blocks_structured_only_v2.csv")
    print("wrote docs/unified_recommendation_model_structured_only_v2.md")
    print("wrote notebooks/17_unified_recommendation_model_structured_only_v2.ipynb")
    print(top3[["slot_label", "recommendation_rank", "player_name", "unified_fit_score"]].to_string(index=False))


if __name__ == "__main__":
    main()
