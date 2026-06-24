from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def md(source: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip().splitlines()],
    }


COMMON_SETUP = r"""
from pathlib import Path
import pandas as pd

pd.set_option("display.max_columns", 80)
pd.set_option("display.max_colwidth", 120)

ROOT = Path.cwd()
if not (ROOT / "outputs").exists():
    ROOT = ROOT.parent

OUT = ROOT / "outputs" / "tables"

def read_table(filename):
    path = OUT / filename
    if not path.exists():
        print(f"[missing] {path}")
        return pd.DataFrame()
    return pd.read_csv(path)

def take_cols(df, cols, n=10):
    keep = [c for c in cols if c in df.columns]
    if not keep:
        return df.head(n)
    return df.loc[:, keep].head(n)

def count_by(df, cols):
    keep = [c for c in cols if c in df.columns]
    if not keep or df.empty:
        return pd.DataFrame()
    return df.groupby(keep, dropna=False).size().reset_index(name="rows").sort_values("rows", ascending=False)

def assert_candidate_names_locked(df):
    sensitive_cols = {"player_name", "search_name", "team_or_org", "player_id"}
    exposed = sensitive_cols.intersection(df.columns)
    if exposed:
        print(f"Candidate-sensitive columns exist but are not displayed here: {sorted(exposed)}")
"""


def write_notebook(path: Path, title: str, cells: list[dict]) -> None:
    nb = {
        "cells": [md(f"# Tutorial: {title}"), *cells],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def layer1() -> list[dict]:
    return [
        md(
            """
            ## 1. 목적

            이 노트북은 1번 레이어인 **SSG 숨은 약점 마이닝**을 학부생에게 설명하기 위한 자료다.

            핵심 질문은 단순히 "SSG가 못하는 게 무엇인가?"가 아니다.

            > SSG에서만 특이하게 나타나는 병목이 무엇이고, 그 병목을 외국인/아시아쿼터 후보의 어떤 능력으로 번역할 수 있는가?

            ## 사용한 모델/방법

            - 단순 기준선: OPS, ERA, 득점, 실점 같은 일반 지표로 먼저 설명 가능한지 확인
            - z-score composite: 팀/역할/상황별 순위 차이를 표준화해서 숨은 약점 점수화
            - anomaly mining: 다른 팀과 비교했을 때 SSG만 튀는 상황을 탐색
            - text corroboration: 기사/인터뷰 메타데이터로 현장 언어가 같은 방향을 가리키는지 확인
            - feature contract: 메시지를 후보 평가에 연결 가능한 변수 목록으로 고정
            """
        ),
        md(
            """
            ## 2. 오늘 배울 흐름

            1. 전체 6개 레이어 중 1번의 현재 상태를 확인한다.
            2. 모델 청사진에서 1번에 해당하는 모델만 뽑아본다.
            3. 메시지 후보와 증거 카드를 확인한다.
            4. 메시지가 후보 평가 변수로 번역됐는지 확인한다.
            """
        ),
        code(COMMON_SETUP),
        code(
            r"""
gate = read_table("recruitment_gate_status_v33.csv")
take_cols(gate, ["gate", "layer", "progress_pct", "status", "decision", "blocking_gap"], n=6)
"""
        ),
        code(
            r"""
blueprint = read_table("modeling_blueprint_registry_v1.csv")
layer1_models = blueprint[
    blueprint["layer"].astype(str).str.contains("ssg_need|text_mining|gate", case=False, regex=True, na=False)
]
take_cols(layer1_models, ["model_id", "model_family", "target_or_score", "main_features", "validation", "promotion_rule"])
"""
        ),
        md(
            """
            ## 3. 메시지 마이닝 결과

            아래 표는 후보 이름이 아니라 **슬롯별 메시지**를 점수화한 결과다.

            해석 포인트:

            - evidence_score가 높을수록 데이터 카드가 많이 붙었다.
            - novelty는 뻔하지 않은 정도다.
            - SSG specificity는 다른 팀에도 통하는 말이 아니라 SSG에 특화된 정도다.
            - weakest_caveat는 발표에서 먼저 방어해야 할 약점이다.
            """
        ),
        code(
            r"""
slot_scores = read_table("message_mining_slot_scores_v1.csv")
take_cols(
    slot_scores.sort_values("total_evidence_score", ascending=False),
    ["slot", "message_id", "message", "cards", "total_evidence_score", "avg_novelty", "avg_ssg_specificity", "avg_actionability", "weakest_caveat"],
    n=10,
)
"""
        ),
        code(
            r"""
cards = read_table("message_mining_evidence_cards_v1.csv")
evidence_summary = (
    cards.groupby("slot", dropna=False)
    .agg(
        cards=("card_id", "count"),
        total_evidence=("evidence_score", "sum"),
        avg_evidence=("evidence_score", "mean"),
        avg_novelty=("novelty_1_5", "mean"),
        avg_ssg_specificity=("ssg_specificity_1_5", "mean"),
    )
    .reset_index()
    .sort_values("total_evidence", ascending=False)
)
evidence_summary
"""
        ),
        md(
            """
            ## 4. 메시지를 후보 변수로 바꾸기

            데이터 마이닝에서 가장 중요한 단계는 "멋진 문장"을 "측정 가능한 변수"로 바꾸는 것이다.

            예를 들어 "ABS-native load-bearing starter"는 다음처럼 바뀐다.

            - workload proxy: 최근 80-90구 이상 던진 경기 경험
            - command proxy: 3-ball 비율, BB+HBP%, first-pitch non-ball
            - damage control proxy: HR%, hard-hit%, barrel%, RISP/on-base damage
            """
        ),
        code(
            r"""
audit = read_table("layer1_candidate_feature_join_audit_v0_1.csv")
take_cols(
    audit,
    ["slot", "message_feature", "candidate_proxy_column", "candidate_proxy_status", "join_status", "blocking_gap"],
    n=12,
)
"""
        ),
        code(
            r"""
closure = read_table("layer1_freeze_closure_matrix_v0_1.csv")
take_cols(closure, closure.columns.tolist(), n=12)
"""
        ),
        md(
            """
            ## 5. 발표용 한 줄

            1번 레이어는 결론을 미리 정한 것이 아니라, SSG의 상황별 병목을 찾고 그 병목을 후보 평가 변수로 번역한 단계다.

            **핵심 메시지:** SSG의 약점은 단순 공격/수비 총량이 아니라, 경기 흐름의 특정 구간에서 끊기는 구조다. 그래서 후보도 일반적인 좋은 선수가 아니라 그 구조를 복구하는 능력을 기준으로 봐야 한다.

            ## 연습문제

            `message_mining_evidence_cards_v1.csv`에서 evidence_score가 높은 카드 3개를 골라, 각 카드가 어떤 후보 평가 변수로 번역될 수 있는지 한 줄씩 적어보자.
            """
        ),
        code(
            r"""
top_cards = cards.sort_values("evidence_score", ascending=False).head(3)
take_cols(top_cards, ["card_id", "slot", "theme", "claim", "metric", "observed", "comparison", "evidence_score", "caveat"], n=3)
"""
        ),
    ]


def layer2() -> list[dict]:
    return [
        md(
            """
            ## 1. 목적

            2번 레이어는 **KBO 외국인 선수 성공/실패 유형 마이닝**이다.

            여기서의 질문은 이렇다.

            > 과거 KBO 외국인 선수 중 어떤 사전 프로필이 성공/실패와 반복적으로 연결됐는가?

            ## 사용한 모델/방법

            - historical label mart: 과거 외국인 선수 시즌을 성공/실패/교체/재계약 관점으로 라벨링
            - archetype clustering/profile: 입단 전 특성으로 유형을 나눔
            - association rule lift: 특정 특성 조합이 성공/실패율을 얼마나 올리는지 계산
            - permutation p-value: 작은 표본에서 우연히 나온 규칙인지 점검
            - backfill coverage audit: 모델이 배울 수 있는 과거 데이터가 충분한지 확인
            """
        ),
        md(
            """
            ## 2. 중요한 태도

            이 레이어는 "이 유형이면 무조건 성공"을 말하지 않는다.

            작은 표본의 외국인 선수 시장에서는 오히려 다음 문장이 더 중요하다.

            > 규칙은 후보 점수를 바로 만들기보다, 어떤 질문을 스카우팅 카드에 반드시 넣어야 하는지를 정한다.
            """
        ),
        code(COMMON_SETUP),
        code(
            r"""
gate = read_table("recruitment_gate_status_v33.csv")
take_cols(gate[gate["gate"].eq("G2")], ["gate", "layer", "progress_pct", "status", "decision", "blocking_gap"])
"""
        ),
        code(
            r"""
blueprint = read_table("modeling_blueprint_registry_v1.csv")
layer2_models = blueprint[
    blueprint["layer"].astype(str).str.contains("archetype|translation|failure", case=False, regex=True, na=False)
]
take_cols(layer2_models, ["model_id", "layer", "model_family", "target_or_score", "main_features", "validation", "promotion_rule"], n=12)
"""
        ),
        md(
            """
            ## 3. 과거 선수 유형 프로필

            아래 표는 선수 이름이 아니라 유형 단위 요약이다.

            핵심 컬럼:

            - rows: 해당 유형에 속한 과거 사례 수
            - success_rate/failure_rate: KBO 입성 후 결과
            - prearrival_*_fingerprint: 입단 전 강점/위험 특성 요약
            """
        ),
        code(
            r"""
profiles = read_table("kbo_foreign_archetype_prearrival_profile_v0_2.csv")
take_cols(
    profiles,
    ["role_model_family", "archetype_cluster_id", "archetype_name", "rows", "model_ready_rows", "success_rate", "failure_rate", "prearrival_strength_fingerprint", "prearrival_risk_fingerprint", "prearrival_profile_gate"],
    n=10,
)
"""
        ),
        md(
            """
            ## 4. 규칙 기반 lift 확인

            lift는 "전체 평균보다 특정 조건 안에서 목표 비율이 얼마나 달라졌는가"를 본다.

            예시:

            - target이 failure라면 lift가 높을수록 위험 신호다.
            - support_rows가 너무 작으면 우연일 수 있으므로 바로 후보 점수로 쓰지 않는다.
            - rule_gate가 research_only이면 발표에서는 질문/검증 포인트로만 사용한다.
            """
        ),
        code(
            r"""
rules = read_table("kbo_foreign_archetype_rule_lifts_v0_2.csv")
rules_view = rules.sort_values(["rule_gate", "abs_rate_delta"], ascending=[True, False])
take_cols(
    rules_view,
    ["role_model_family", "signal_type", "rule", "target", "support_rows", "target_rate_inside_rule", "role_base_target_rate", "rate_delta_vs_role_base", "lift_vs_role_base", "permutation_p_value", "rule_gate", "release_policy"],
    n=12,
)
"""
        ),
        code(
            r"""
coverage = read_table("layer2_backfill_coverage_recalibration_v0_1.csv")
take_cols(coverage, coverage.columns.tolist(), n=10)
"""
        ),
        md(
            """
            ## 5. 발표용 한 줄

            2번 레이어는 과거 외국인 선수 사례를 사용해 "KBO에서 먹히는 유형과 위험한 유형"을 찾는 단계다. 하지만 표본이 작기 때문에, 복잡한 규칙은 최종 점수보다 스카우팅 질문으로 사용한다.

            ## 연습문제

            rule_lifts 표에서 support_rows가 충분하고 permutation_p_value가 낮은 규칙을 하나 고른 뒤, 그 규칙을 후보 검토 질문으로 바꿔보자.
            """
        ),
        code(
            r"""
candidate_rules = rules[
    (rules["support_rows"] >= 5)
    & (rules["permutation_p_value"] <= 0.20)
].copy()
take_cols(
    candidate_rules.sort_values("abs_rate_delta", ascending=False),
    ["role_model_family", "rule", "target", "support_rows", "rate_delta_vs_role_base", "permutation_p_value", "semantic_alignment", "rule_gate"],
    n=8,
)
"""
        ),
    ]


def layer3() -> list[dict]:
    return [
        md(
            """
            ## 1. 목적

            3번 레이어는 **후보 시장 구축**이다.

            여기서 중요한 질문은 "누가 잘하냐"가 아니라 먼저 이것이다.

            > 실제로 SSG가 영입 가능한 시장 안에 있는가?

            ## 사용한 모델/방법

            - deterministic gate: KBO 규정, 샐러리, 로스터, 국적/아시아쿼터 조건
            - market realism composite: 40-man/active/DFA/FA/마이너 계약/부상 신호를 합친 현실성 점수
            - source-fill packet: 계약, 의료, 한국행 의사, 여권/국적, 뉴스 근거를 채우는 작업표
            - data coverage audit: 어떤 리그/데이터가 얼마나 확보됐는지 추적
            """
        ),
        md(
            """
            ## 2. 왜 모델 전에 gate가 필요한가

            외국인 영입 문제에서는 좋은 선수를 찾는 것보다, **너무 좋아서 못 데려오는 선수**와 **정보가 부족해서 위험한 선수**를 먼저 거르는 것이 중요하다.

            그래서 3번 레이어는 ML 모델이라기보다, 스카우팅 부서의 현실 필터를 데이터화한 단계에 가깝다.
            """
        ),
        code(COMMON_SETUP),
        code(
            r"""
gate = read_table("recruitment_gate_status_v33.csv")
take_cols(gate[gate["gate"].eq("G3")], ["gate", "layer", "progress_pct", "status", "decision", "blocking_gap"])
"""
        ),
        code(
            r"""
coverage = read_table("data_coverage_by_league_v1.csv")
take_cols(coverage.sort_values("rows", ascending=False), ["league_bucket", "files", "size_mb", "rows", "detail"], n=12)
"""
        ),
        md(
            """
            ## 3. 시장별 확보 상태

            아래는 후보 시장을 어느 정도 채웠는지 보는 표다. 이 단계에서 후보명은 보지 않고, 슬롯/시장/상태 단위로만 본다.
            """
        ),
        code(
            r"""
market_coverage = read_table("candidate_market_coverage_v0_3.csv")
take_cols(
    market_coverage,
    ["market_layer", "slot", "market_scope", "rows", "secured_rows", "research_lead_rows", "market_watch_rows", "medical_hold_rows", "data_status", "blocking_gap"],
    n=12,
)
"""
        ),
        code(
            r"""
packet = read_table("ssg_fit_source_fill_packet_v0_1.csv")
assert_candidate_names_locked(packet)
slot_status = count_by(packet, ["fit_slot", "market_realism_status"])
slot_status.head(20)
"""
        ),
        md(
            """
            ## 4. source-fill readiness

            3번의 최종 산출물은 "최종 후보"가 아니라, 어떤 후보군에 어떤 추가 근거가 필요한지 알려주는 작업표다.

            대표적으로 필요한 수동 확인:

            - 계약/바이아웃/옵트아웃
            - 메디컬/부상 이력
            - 한국행 의사
            - 국적/아시아쿼터 조건
            - 기사/현지 소스 신뢰도
            """
        ),
        code(
            r"""
readiness = count_by(packet, ["fit_slot", "source_fill_readiness_bucket"])
readiness.head(30)
"""
        ),
        code(
            r"""
manual = count_by(packet, ["fit_slot", "manual_feasibility_priority_tier"])
manual.head(30)
"""
        ),
        md(
            """
            ## 5. 발표용 한 줄

            3번 레이어는 후보 시장을 "스탯 좋은 선수 목록"에서 "실제로 데려올 수 있는 선수 검토판"으로 바꾼 단계다.

            ## 연습문제

            source_fill_readiness_bucket이 낮은 슬롯을 하나 고르고, 그 슬롯에서 가장 먼저 채워야 할 정보가 무엇인지 적어보자.
            """
        ),
    ]


def layer4() -> list[dict]:
    return [
        md(
            """
            ## 1. 목적

            4번 레이어는 **KBO 번역 모델**이다.

            핵심 질문은 이것이다.

            > MLB/AAA/AA/NPB에서 보인 능력이 KBO에서 얼마나 그대로 먹히는가?

            ## 사용한 모델/방법

            - role prior baseline: 포지션/역할별 과거 평균 성공률
            - ridge logistic regression: 작은 표본에서 과적합을 줄이는 설명 가능한 분류 모델
            - balanced ridge logistic: 성공/실패 불균형을 보정한 로지스틱 모델
            - shallow random forest: 비선형 상호작용을 약하게 허용한 모델
            - repeated stratified CV: 작은 표본에서 fold 운을 줄이기 위해 반복 교차검증
            - Brier/logloss/AUC/top-k precision: 확률 예측과 순위 성능을 함께 확인
            """
        ),
        md(
            """
            ## 2. 가장 중요한 결론

            이 레이어의 결론은 "복잡한 모델이 최고다"가 아니다.

            오히려 현재 데이터에서는 복잡한 classifier를 직접 후보 점수로 승격하지 않는다는 판단이 핵심이다.

            > KBO 번역 모델은 후보 점수 엔진이 아니라, 성공/실패 가능성을 조심스럽게 보정하는 진단 장치다.
            """
        ),
        code(COMMON_SETUP),
        code(
            r"""
gate = read_table("recruitment_gate_status_v33.csv")
take_cols(gate[gate["gate"].eq("G4")], ["gate", "layer", "progress_pct", "status", "decision", "blocking_gap"])
"""
        ),
        code(
            r"""
audit = read_table("kbo_translation_retrain_gate_audit_v0_3.csv")
take_cols(audit, ["gate", "layer", "check", "pass_rows", "total_rows", "status", "blocking_gap"], n=10)
"""
        ),
        md(
            """
            ## 3. 반복 교차검증 결과 읽기

            promotion_status가 핵심이다.

            - baseline: 비교 기준
            - do_not_promote: 연구 참고로는 쓰지만 후보 점수로 직접 쓰지 않음
            - promote가 없다는 것은 모델링 실패가 아니라 과대해석 방지다.
            """
        ),
        code(
            r"""
cv = read_table("kbo_translation_failure_repeated_cv_comparison_v0_3.csv")
summary = count_by(cv, ["role_model_family", "target", "promotion_status"])
summary
"""
        ),
        code(
            r"""
take_cols(
    cv.sort_values(["role_model_family", "target", "model"]),
    ["role_model_family", "target", "model", "folds", "total_valid_rows", "mean_auc", "mean_brier", "mean_precision_top_25pct", "brier_lift_vs_role_prior", "top25_precision_lift_vs_role_prior", "promotion_status"],
    n=18,
)
"""
        ),
        md(
            """
            ## 4. v0.2와 v0.3 비교

            새 데이터를 추가했을 때 모델이 좋아지는지, 아니면 표본은 늘었지만 안정성은 떨어지는지 확인한다.
            """
        ),
        code(
            r"""
compare = read_table("kbo_translation_failure_v0_2_vs_v0_3_comparison.csv")
take_cols(
    compare,
    ["role_model_family", "target", "model", "total_valid_rows_delta_v0_3_minus_v0_2", "mean_auc_delta_v0_3_minus_v0_2", "mean_brier_delta_v0_3_minus_v0_2", "brier_direction", "promotion_status_v0_3"],
    n=18,
)
"""
        ),
        md(
            """
            ## 5. 발표용 한 줄

            4번 레이어는 해외 기록을 KBO 성과로 번역하려 했지만, 작은 표본에서 복잡한 모델이 안정적으로 승격되지 않았기 때문에 보수적으로 role-prior와 feature-contract 진단을 사용했다.

            ## 연습문제

            mean_auc가 높아도 promotion_status가 do_not_promote인 이유를 Brier/logloss와 표본 크기 관점에서 설명해보자.
            """
        ),
    ]


def layer5() -> list[dict]:
    return [
        md(
            """
            ## 1. 목적

            5번 레이어는 **실패 리스크 모델**이다.

            핵심 질문은 이렇다.

            > 좋아 보이는 후보가 왜 실패할 수 있는가?

            ## 사용한 모델/방법

            - risk-band model: 정확한 실패 확률 대신 위험 구간으로 분류
            - translation uncertainty propagation: 4번 모델의 불확실성을 리스크에 반영
            - medical/contract/source/manual gates: 숫자로 잡히지 않는 실패 원인을 별도 게이트로 관리
            - locked recalibration: 후보명과 점수를 공개하지 않고 슬롯/리스크 밴드만 공개
            """
        ),
        md(
            """
            ## 2. 왜 확률 대신 risk band인가

            외국인 선수 데이터는 표본이 작고, 계약/부상/적응 같은 숨은 변수가 많다.

            그래서 "실패확률 37.2%"처럼 보이는 숫자는 오히려 위험하다.

            이 프로젝트에서는 다음처럼 더 방어 가능한 표현을 쓴다.

            - risk_screen_pass
            - watch_source_context
            - manual_review_required
            - block_until_source_or_medical_cleared
            """
        ),
        code(COMMON_SETUP),
        code(
            r"""
gate = read_table("recruitment_gate_status_v33.csv")
take_cols(gate[gate["gate"].eq("G5")], ["gate", "layer", "progress_pct", "status", "decision", "blocking_gap"])
"""
        ),
        code(
            r"""
audit = read_table("layer5_6_augmented_recalibration_gate_audit_v0_1.csv")
take_cols(audit, ["gate", "layer", "check", "pass_rows", "total_rows", "status", "blocking_gap"], n=20)
"""
        ),
        md(
            """
            ## 3. 슬롯별 실패 리스크 분포

            아래 표는 후보명을 숨긴 상태에서 슬롯별 리스크 밴드만 보여준다.
            """
        ),
        code(
            r"""
risk_summary = read_table("layer5_failure_risk_v0_3_slot_summary_v0_1.csv")
take_cols(risk_summary, ["fit_slot", "failure_risk_band_v0_3", "manual_review_tier_v0_3", "locked_rows", "release_allowed"], n=20)
"""
        ),
        code(
            r"""
pivot = risk_summary.pivot_table(
    index="fit_slot",
    columns="failure_risk_band_v0_3",
    values="locked_rows",
    aggfunc="sum",
    fill_value=0,
)
pivot
"""
        ),
        md(
            """
            ## 4. 잠금된 리스크 원장

            실제 후보별 리스크 원장은 존재하지만, 발표 전에는 후보명/정확한 점수/순위를 공개하지 않는다.
            """
        ),
        code(
            r"""
locked = read_table("layer5_failure_risk_v0_3_locked_recalibration_v0_1.csv")
assert_candidate_names_locked(locked)
count_by(locked, ["fit_slot", "failure_risk_band_v0_3", "manual_review_tier_v0_3"]).head(30)
"""
        ),
        md(
            """
            ## 5. 발표용 한 줄

            5번 레이어는 좋은 후보를 찾기 전에, 실패할 수 있는 경로를 계약/메디컬/번역불확실성/출처 부족으로 나눠 잠근 단계다.

            ## 연습문제

            한 후보가 statistical fit은 높지만 medical source가 비어 있다면, 왜 rank를 바로 공개하면 안 되는지 설명해보자.
            """
        ),
    ]


def layer6() -> list[dict]:
    return [
        md(
            """
            ## 1. 목적

            6번 레이어는 **SSG fit ranking**이다.

            단, 현재 결과물은 공개 추천 리스트가 아니다.

            > 후보명을 공개하기 전, 어떤 후보군이 수동 검토/출처 보강/시장 관찰/보류에 들어가는지 정하는 잠금된 리뷰 퍼널이다.

            ## 사용한 모델/방법

            - multi-objective score: SSG fit, KBO translation, market realism, tool/process, surplus access, failure resilience
            - sensitivity analysis: 가중치를 바꿔도 살아남는지 확인
            - stage gate ranking: 순위 공개 전 수동 검토 단계를 배정
            - locked release policy: 후보명/정확 점수/정확 순위/추천 라벨 비공개
            """
        ),
        md(
            """
            ## 2. 최종 점수의 사고방식

            최종 점수는 단순히 좋은 스탯의 평균이 아니다.

            ```text
            FinalScore =
                SSGFit
              + KBOTranslation
              + MarketRealism
              + ToolProcess
              + SurplusAccess
              + FailureResilience
            ```

            그리고 hard gate를 통과하지 못하면, 점수가 높아도 공개 추천으로 가지 않는다.
            """
        ),
        code(COMMON_SETUP),
        code(
            r"""
gate = read_table("recruitment_gate_status_v33.csv")
take_cols(gate[gate["gate"].eq("G6")], ["gate", "layer", "progress_pct", "status", "decision", "blocking_gap"])
"""
        ),
        code(
            r"""
stage_summary = read_table("layer6_fit_ranking_v0_3_stage_summary_v0_1.csv")
take_cols(stage_summary, ["fit_slot", "ranking_stage_gate_v0_3", "locked_rows", "release_allowed"], n=20)
"""
        ),
        code(
            r"""
stage_pivot = stage_summary.pivot_table(
    index="fit_slot",
    columns="ranking_stage_gate_v0_3",
    values="locked_rows",
    aggfunc="sum",
    fill_value=0,
)
stage_pivot
"""
        ),
        md(
            """
            ## 3. sensitivity band

            특정 가중치에서만 좋아 보이는 후보는 위험하다.

            그래서 여러 가중치 조합에서 순위가 얼마나 흔들리는지 보고, 먼저 리뷰할 lane을 나눈다.
            """
        ),
        code(
            r"""
packet = read_table("ssg_fit_source_fill_packet_v0_1.csv")
assert_candidate_names_locked(packet)
take_cols(
    count_by(packet, ["fit_slot", "sensitivity_band", "fit_review_lane"]),
    ["fit_slot", "sensitivity_band", "fit_review_lane", "rows"],
    n=30,
)
"""
        ),
        md(
            """
            ## 4. 왜 아직 추천 리스트가 아닌가

            release_allowed가 False라는 것은 모델이 망했다는 뜻이 아니다.

            오히려 교수님 앞에서는 다음 논리가 더 강하다.

            - 모델은 후보를 좁히는 데 성공했다.
            - 하지만 계약/의료/한국행 의사/출처 근거가 잠겨 있으므로 공개 추천은 보류한다.
            - 따라서 현재 산출물은 "최종 답"이 아니라 "현장 검토용 우선순위 큐"다.
            """
        ),
        code(
            r"""
release_check = stage_summary.groupby("release_allowed", dropna=False)["locked_rows"].sum().reset_index()
release_check
"""
        ),
        md(
            """
            ## 5. 발표용 한 줄

            6번 레이어는 후보를 무리하게 발표하지 않고, SSG fit이 높은 후보군을 수동 검토 큐로 정렬한 단계다. 이게 현장 스카우팅 흐름과 가장 비슷한 최종 형태다.

            ## 연습문제

            `manual_review_candidate_locked`와 `source_fill_before_rank_locked`의 차이를 설명해보자. 어떤 경우에 팀원이 먼저 기사를 찾아야 할까?
            """
        ),
    ]


def main() -> None:
    notebooks = [
        ("11_layer_01_ssg_hidden_weakness_mining.ipynb", "Layer 1 SSG Hidden Weakness Mining", layer1()),
        ("12_layer_02_kbo_foreign_archetype_mining.ipynb", "Layer 2 KBO Foreign Archetype Mining", layer2()),
        ("13_layer_03_candidate_market_construction.ipynb", "Layer 3 Candidate Market Construction", layer3()),
        ("14_layer_04_kbo_translation_model.ipynb", "Layer 4 KBO Translation Model", layer4()),
        ("15_layer_05_failure_risk_model.ipynb", "Layer 5 Failure Risk Model", layer5()),
        ("16_layer_06_ssg_fit_ranking.ipynb", "Layer 6 SSG Fit Ranking", layer6()),
    ]
    for filename, title, cells in notebooks:
        write_notebook(NOTEBOOK_DIR / filename, title, cells)
        print(f"wrote notebooks/{filename}")


if __name__ == "__main__":
    main()
