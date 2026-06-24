#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd


BASE = Path(__file__).resolve().parents[1]
OUT_DIR = BASE / "reports" / "leaf_node"
ASSET_DIR = OUT_DIR / "assets"
TABLE_DIR = BASE / "outputs" / "tables"


def read_csv(name: str) -> pd.DataFrame:
    path = TABLE_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def pct(value, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value) * 100:.{digits}f}%"


def num(value, digits: int = 3) -> str:
    if pd.isna(value):
        return "-"
    return f"{float(value):.{digits}f}"


def money(value) -> str:
    if pd.isna(value) or value == "":
        return "-"
    value = float(value)
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}k"
    return f"${value:.0f}"


def md_table(rows, headers) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    return "\n".join(lines)


def as_source_path(path: str) -> str:
    return f"`{path}`"


def build_final_board() -> pd.DataFrame:
    ens = read_csv("ensemble_candidate_scores_v1.csv")
    hitters = read_csv("data_mining_hitter_candidates_v1.csv")
    pitchers = read_csv("data_mining_pitcher_candidates_v1.csv")
    salary = read_csv("final_candidate_salary_contract_gate_v1.csv")

    ens_idx = ens.set_index(["slot", "candidate"])
    hitter_idx = hitters.set_index("player_name")
    pitcher_idx = pitchers.set_index("player_name")
    salary_idx = salary.set_index(["slot", "candidate"])

    rows = []

    def add_hitter(player, gate_rank, decision, role, final_summary):
        e = ens_idx.loc[("foreign_hitter", player)] if ("foreign_hitter", player) in ens_idx.index else pd.Series(dtype=object)
        h = hitter_idx.loc[player] if player in hitter_idx.index else pd.Series(dtype=object)
        s = salary_idx.loc[("foreign_hitter", player)] if ("foreign_hitter", player) in salary_idx.index else pd.Series(dtype=object)
        rows.append(
            {
                "slot": "foreign_hitter",
                "player": player,
                "raw_ensemble_rank": int(e.get("rank", 0)) if pd.notna(e.get("rank", pd.NA)) else "",
                "raw_ensemble_score": round(float(e.get("ensemble_score", 0)), 4) if pd.notna(e.get("ensemble_score", pd.NA)) else "",
                "gate_adjusted_rank": gate_rank,
                "decision": decision,
                "organization": h.get("roster_team", ""),
                "age": h.get("age", ""),
                "hand_or_side": h.get("bat_side", ""),
                "position_or_role": h.get("primary_position_abbrev", ""),
                "model_success_prob": round(float(h.get("dm_success_prob", 0)), 4) if pd.notna(h.get("dm_success_prob", pd.NA)) else "",
                "model_failure_prob": round(float(h.get("dm_failure_prob", 0)), 4) if pd.notna(h.get("dm_failure_prob", pd.NA)) else "",
                "market_status": h.get("market_access_bucket", ""),
                "salary_signal_usd": s.get("structured_salary_signal_usd", ""),
                "economic_gate": s.get("economic_gate", ""),
                "risk_gate": s.get("medical_availability_status", ""),
                "ssg_role_fit": role,
                "final_summary": final_summary,
            }
        )

    def add_pitcher(player, raw_rank, raw_score, gate_rank, decision, role, final_summary):
        p = pitcher_idx.loc[player] if player in pitcher_idx.index else pd.Series(dtype=object)
        s = salary_idx.loc[("foreign_pitcher", player)] if ("foreign_pitcher", player) in salary_idx.index else pd.Series(dtype=object)
        rows.append(
            {
                "slot": "foreign_pitcher",
                "player": player,
                "raw_ensemble_rank": raw_rank,
                "raw_ensemble_score": raw_score,
                "gate_adjusted_rank": gate_rank,
                "decision": decision,
                "organization": p.get("roster_team", ""),
                "age": p.get("age", ""),
                "hand_or_side": p.get("pitch_hand", ""),
                "position_or_role": "SP/Swing" if player == "Josh Fleming" else "SP",
                "model_success_prob": round(float(p.get("dm_success_prob", 0)), 4) if pd.notna(p.get("dm_success_prob", pd.NA)) else "",
                "model_failure_prob": round(float(p.get("dm_failure_prob", 0)), 4) if pd.notna(p.get("dm_failure_prob", pd.NA)) else "",
                "market_status": p.get("market_access_bucket", ""),
                "salary_signal_usd": s.get("structured_salary_signal_usd", ""),
                "economic_gate": s.get("economic_gate", ""),
                "risk_gate": s.get("medical_availability_status", ""),
                "ssg_role_fit": role,
                "final_summary": final_summary,
            }
        )

    add_hitter(
        "Luis Matos",
        1,
        "CONTACT_1ST",
        "RHP 게임스크립트에서 이닝을 끊지 않는 코너 OF 전환형 타자",
        "데이터마이닝 확률은 가장 높고 계약 부담은 낮아 최종 접촉 1순위로 승격된다.",
    )
    add_hitter(
        "Nolan Jones",
        2,
        "MODEL_LEAD_CONDITIONAL",
        "좌타 코너 OF 파워와 출루를 동시에 가진 raw 모델 1위",
        "모델상 가장 강하지만 2026 현금 신호가 커서 비용 확인 후 1순위 또는 2순위가 갈린다.",
    )
    add_hitter(
        "Jack Suwinski",
        3,
        "UPSIDE_HOLD",
        "볼넷과 배럴이 살아 있는 고위험 장타 후보",
        "팀원 합의와 upside는 강하지만 삼진/실패확률/계약 신호 때문에 백업 보드에 둔다.",
    )

    add_pitcher(
        "Josh Fleming",
        1,
        0.6375,
        1,
        "CONTACT_1ST",
        "좌완 선발/스윙맨, 낮은 HR9와 관리 가능한 BB9로 traffic-command 역할",
        "여러 모델에서 반복 등장하고 계약 접근성이 좋아 최종 접촉 1순위다.",
    )
    add_pitcher(
        "Bryse Wilson",
        15,
        0.0643,
        2,
        "BACKUP_VERIFY",
        "선발 이닝 표본과 K9/BB9 균형을 가진 진단 후보",
        "투수 모델 확신도는 낮지만 의료 게이트가 깨끗해 Fleming 다음 비교 검증군이다.",
    )
    add_pitcher(
        "Austin Gomber",
        16,
        0.0642,
        3,
        "BACKUP_VERIFY",
        "좌완 선발 이닝 축적형 후보",
        "172이닝 표본과 좌완성은 장점이나 HR9와 낮은 margin 때문에 보조 검증군이다.",
    )
    add_pitcher(
        "Carson Spiers",
        2,
        0.3125,
        "HOLD",
        "MEDICAL_HOLD",
        "raw ensemble 2위였던 선발 후보",
        "의료 게이트에서 활성 후보가 아니라 보류 대상으로 이동한다.",
    )
    add_pitcher(
        "Brian Van Belle",
        3,
        0.2625,
        "HOLD",
        "MEDICAL_HOLD",
        "BB9와 이닝 지속성은 좋은 raw Top 3 후보",
        "full-season IL 신호로 활성 후보가 아니라 의료 확인 대상으로 이동한다.",
    )

    board = pd.DataFrame(rows)
    board.to_csv(TABLE_DIR / "final_candidate_board.csv", index=False)
    return board


def make_charts(board: pd.DataFrame) -> list[dict]:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    chart_map = []
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        return [{"chart": "not_created", "reason": f"matplotlib unavailable: {exc}"}]

    plt.rcParams["font.family"] = ["AppleGothic", "DejaVu Sans", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False

    def style_ax(ax):
        ax.set_facecolor("#FFFFFF")
        ax.grid(axis="x", color="#E6E8F0", linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D7DBE7")
        ax.spines["bottom"].set_color("#D7DBE7")
        ax.tick_params(colors="#464C55")

    # Chart 1: hidden SSG weakness rules.
    hidden = pd.DataFrame(
        [
            {"rule": "RHP game-script lock", "win_pct": 0.100, "run_diff": -5.10},
            {"rule": "Run-kill avoidance", "win_pct": 0.000, "run_diff": -5.11},
            {"rule": "Extra-out resilience", "win_pct": 0.000, "run_diff": -4.50},
            {"rule": "Starter length support", "win_pct": 0.000, "run_diff": -5.83},
        ]
    )
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=160)
    plot_df = hidden.sort_values("run_diff")
    y = range(len(plot_df))
    ax.barh(y, plot_df["run_diff"], color="#F0986E", edgecolor="#804126", linewidth=1.0)
    ax.set_yticks(list(y), plot_df["rule"])
    ax.axvline(0, color="#1F2430", lw=1)
    ax.set_title("SSG hidden weakness rules are game-script failures", loc="left", fontsize=13, weight="bold")
    ax.set_xlabel("Average run differential in flagged games")
    ax.set_ylabel("")
    style_ax(ax)
    for i, row in enumerate(plot_df.itertuples()):
        ax.text(row.run_diff - 0.1, i, f"{row.run_diff:.2f}", va="center", ha="right", fontsize=9)
    fig.tight_layout()
    path = ASSET_DIR / "hidden_weakness_rules.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    chart_map.append(
        {
            "chart": "hidden_weakness_rules",
            "path": str(path),
            "question": "SSG의 약점이 단순 장타 부족인지, 특정 경기 상태 실패인지",
            "takeaway": "RHP/이닝 단절/추가 출루 이후 상황에서 승률과 득실이 동시에 붕괴한다.",
        }
    )

    # Chart 2: hitter candidate model vs gate.
    hitter_chart = board.loc[board["slot"].eq("foreign_hitter")].copy()
    hitter_chart["success_pct"] = pd.to_numeric(hitter_chart["model_success_prob"], errors="coerce") * 100
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=160)
    plot_df = hitter_chart.sort_values("success_pct")
    y = range(len(plot_df))
    ax.barh(y, plot_df["success_pct"], color="#A3BEFA", edgecolor="#2E4780", linewidth=1.0)
    ax.set_yticks(list(y), plot_df["player"])
    ax.set_title("Hitter model lead changes after acquisition gates", loc="left", fontsize=13, weight="bold")
    ax.set_xlabel("Historical KBO success-model probability")
    ax.set_ylabel("")
    ax.set_xlim(0, 100)
    style_ax(ax)
    for i, row in enumerate(plot_df.itertuples()):
        ax.text(row.success_pct + 1, i, f"{row.success_pct:.1f}%", va="center", fontsize=9)
    fig.tight_layout()
    path = ASSET_DIR / "hitter_success_probabilities.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    chart_map.append(
        {
            "chart": "hitter_success_probabilities",
            "path": str(path),
            "question": "타자 후보의 데이터마이닝 성공확률과 최종 게이트가 어떻게 결합되는지",
            "takeaway": "Matos와 Jones는 모두 강하지만 Matos가 비용 게이트에서 최종 1순위가 된다.",
        }
    )

    # Chart 3: pitcher gate movement.
    pitcher_chart = board.loc[board["slot"].eq("foreign_pitcher")].copy()
    order_map = {"CONTACT_1ST": 3, "BACKUP_VERIFY": 2, "MEDICAL_HOLD": 1}
    pitcher_chart["decision_weight"] = pitcher_chart["decision"].map(order_map).fillna(0)
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=160)
    palette = {"CONTACT_1ST": "#A3D576", "BACKUP_VERIFY": "#A3BEFA", "MEDICAL_HOLD": "#F0986E"}
    plot_df = pitcher_chart.sort_values(["decision_weight", "raw_ensemble_rank"], ascending=[True, False])
    y = range(len(plot_df))
    colors = [palette.get(decision, "#C5CAD3") for decision in plot_df["decision"]]
    ax.barh(y, plot_df["decision_weight"], color=colors, edgecolor="#464C55", linewidth=1.0)
    ax.set_yticks(list(y), plot_df["player"])
    ax.set_title("Pitcher board is decided by risk gates, not raw rank alone", loc="left", fontsize=13, weight="bold")
    ax.set_xlabel("Gate-adjusted action level")
    ax.set_ylabel("")
    ax.set_xticks([1, 2, 3], ["Medical hold", "Backup verify", "Contact first"])
    style_ax(ax)
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=color, edgecolor="#464C55", label=label) for label, color in palette.items()]
    ax.legend(handles=handles, loc="lower right", frameon=True)
    fig.tight_layout()
    path = ASSET_DIR / "pitcher_gate_movement.png"
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    chart_map.append(
        {
            "chart": "pitcher_gate_movement",
            "path": str(path),
            "question": "투수 raw Top 3가 왜 최종 Top 3와 달라지는지",
            "takeaway": "Carson Spiers와 Brian Van Belle은 raw 상위지만 의료 게이트로 보류되고 Fleming이 접촉 1순위가 된다.",
        }
    )

    pd.DataFrame(chart_map).to_csv(OUT_DIR / "chart_map.csv", index=False)
    return chart_map


def build_report(board: pd.DataFrame, chart_map: list[dict]) -> dict[str, str]:
    coverage = read_csv("data_coverage_by_league_v1.csv")
    audit = read_csv("data_mining_model_audit_v1.csv")
    weights = read_csv("ensemble_model_signal_weights_v1.csv")
    trace = read_csv("ssg_layer1_evidence_to_message_trace_v4.csv")
    blueprint = read_csv("ssg_layer1_candidate_feature_blueprint_v4.csv")
    ens = read_csv("ensemble_candidate_scores_v1.csv")
    salary = read_csv("final_candidate_salary_contract_gate_v1.csv")

    coverage_rows = []
    for _, r in coverage.head(8).iterrows():
        coverage_rows.append(
            {
                "데이터 묶음": r["league_bucket"],
                "파일": int(r["files"]),
                "용량": f"{float(r['size_mb']):.1f}MB",
                "행 수": f"{int(r['rows']):,}" if pd.notna(r["rows"]) and float(r["rows"]) > 0 else "-",
                "해석": r["detail"],
            }
        )

    hidden_rows = []
    for _, r in trace.loc[
        trace["message_component"].isin(
            ["not_generic_power_gap", "rhp_game_script_lock", "run_kill_avoidance", "extra_out_resilience", "starter_length_support", "older_split_support"]
        )
    ].iterrows():
        hidden_rows.append(
            {
                "메시지 조각": r["message_component"],
                "근거 요약": r["evidence_summary"],
                "의사결정 사용": r["decision_use"],
                "신뢰도": r["confidence"],
            }
        )

    model_rows = []
    for _, r in audit.iterrows():
        model_rows.append(
            {
                "슬롯": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "모델 블록": r["model_block"],
                "학습 표본": int(r["historical_rows"]),
                "모델": r["model"],
                "목표": r["target"],
                "변수군": r["feature_family"],
                "판단": r["validation_summary"],
            }
        )

    weight_rows = []
    for _, r in weights.iterrows():
        weight_rows.append(
            {
                "슬롯": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "base learner": r["signal"],
                "가중치": f"{float(r['weight']):.2f}",
                "이유": r["reason"],
            }
        )

    feature_rows = []
    for _, r in blueprint.iterrows():
        feature_rows.append(
            {
                "슬롯": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "메시지": r["message_component"],
                "후보 변수": r["candidate_feature"],
                "방향": r["desired_direction"],
                "모델 사용": r["downstream_layer"],
                "해석": r["reason_ko"],
            }
        )

    hitter_raw = []
    for _, r in ens.loc[ens["slot"].eq("foreign_hitter")].head(5).iterrows():
        hitter_raw.append(
            {
                "Raw 순위": int(r["rank"]),
                "선수": r["candidate"],
                "앙상블": f"{float(r['ensemble_score']):.4f}",
                "성공확률": pct(r["dm_success_prob"]),
                "실패확률": pct(r["dm_failure_prob"]),
                "반복 등장": r["source_presence"],
                "해석": r["ensemble_tier"],
            }
        )

    pitcher_raw = []
    for _, r in ens.loc[ens["slot"].eq("foreign_pitcher")].head(6).iterrows():
        pitcher_raw.append(
            {
                "Raw 순위": int(r["rank"]),
                "선수": r["candidate"],
                "앙상블": f"{float(r['ensemble_score']):.4f}",
                "반복 등장": r["source_presence"],
                "해석": r["ensemble_tier"],
            }
        )

    hitter_gate = board.loc[board["slot"].eq("foreign_hitter")].copy()
    pitcher_gate = board.loc[board["slot"].eq("foreign_pitcher") & board["decision"].ne("MEDICAL_HOLD")].copy()
    hold_gate = board.loc[board["slot"].eq("foreign_pitcher") & board["decision"].eq("MEDICAL_HOLD")].copy()

    final_rows = []
    for _, r in board.loc[board["decision"].isin(["CONTACT_1ST", "MODEL_LEAD_CONDITIONAL", "UPSIDE_HOLD", "BACKUP_VERIFY"])].iterrows():
        final_rows.append(
            {
                "슬롯": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "선수": r["player"],
                "최종 단계": r["decision"],
                "게이트 순위": r["gate_adjusted_rank"],
                "성공확률": pct(r["model_success_prob"]),
                "실패확률": pct(r["model_failure_prob"]),
                "비용 신호": money(r["salary_signal_usd"]),
                "핵심 역할": r["ssg_role_fit"],
            }
        )

    source_rows = []
    for _, r in salary.iterrows():
        source_rows.append(
            {
                "선수": r["candidate"],
                "계약/의료 확인": r["source_note"],
                "출처": r["source_url"],
            }
        )

    final_report = f"""# SSG 랜더스 외국인 타자 및 외국인 선발투수 영입 전략

## Technical Summary

이번 최종 모델의 결론은 단순하다. **SSG는 가장 유명한 선수를 찾는 팀이 아니라, MLB 경계선 시장에서 결함이 가격을 낮췄지만 그 결함이 SSG와 KBO에서는 덜 치명적인 선수를 찾아야 한다.** 그래서 본 보고서는 네 명의 후보 의견을 단순 투표로 합치지 않고, `M1 숨은 약점`, `M2 KBO 성공/실패`, `M3 KBO 번역`, `M4 시장 접근성`, `M5 실패 리스크`, `M6 합의 신호`를 하나의 앙상블 데이터마이닝 파이프라인으로 통합했다.

**타자 최종 접촉 1순위는 Luis Matos다.** Raw ensemble 1위는 Nolan Jones였지만, 2026 현금 신호와 계약 게이트까지 통과시키면 Matos가 더 현실적인 1차 접촉 대상이 된다. Jones는 모델상 가장 강한 조건부 1순위, Jack Suwinski는 high-upside 보조 후보로 남긴다.

**투수 최종 접촉 1순위는 Josh Fleming이다.** 투수 모델은 타자보다 예측 확신이 낮기 때문에 확정형 추천이 아니라 `진단 + 게이트` 방식으로 읽어야 한다. Raw board에서 Carson Spiers와 Brian Van Belle이 높게 올라왔지만 의료 게이트에서 보류되면서, Fleming을 1순위로 두고 Bryse Wilson과 Austin Gomber를 비교 검증군으로 둔다.

**SSG의 숨은 메시지는 “장타 부족”이 아니다.** 데이터상 더 뾰족한 메시지는 우투 선발 경기, 1루 주자 이후 전환, 이닝 단절, 수비 실수 또는 추가 출루 이후의 복구 실패다. 따라서 외국인 타자는 `한 방`보다 `이닝을 다시 여는 코너 OF`, 외국인 선발은 `구위 총량`보다 `볼넷과 장타 허용을 억제하는 traffic-command starter`가 더 맞다.

## Key Findings

1. **SSG hidden weakness는 game-state interaction 문제다.** OF HR zero, OF RBI low 같은 단순 공격 지표보다 RHP game-script lock, run-kill avoidance, extra-out resilience rule에서 승률과 득실이 더 강하게 무너진다.
2. **타자 모델은 후보를 실제로 바꿨다.** Ridge Logistic 기반 KBO 성공/실패 모델은 Luis Matos와 Nolan Jones를 강하게 밀어 올렸고, 기존 팀원 후보 중 일부는 실패확률 또는 계약 게이트 때문에 보조 후보로 재배치됐다.
3. **투수는 모델 점수보다 리스크 게이트가 더 중요하다.** Sparse L1 Logistic 기반 투수 모델은 진단용 신호로 쓰고, 실제 board는 의료 상태, 선발 역할 지속성, BB9/HR9, 계약 접근성을 함께 통과한 선수만 남겼다.
4. **최종 board는 Raw Top 3와 다르다.** 이 차이가 이번 보고서의 핵심이다. 좋은 데이터마이닝 보고서는 점수표를 발표하는 것이 아니라, 점수가 현실 게이트와 만나면서 어떤 후보가 올라가고 내려가는지 설명해야 한다.

## Research Questions

| RQ | 질문 | 이번 보고서의 답 |
|---|---|---|
| RQ1 | SSG만의 보강 메시지는 무엇인가? | 장타 총량이 아니라 RHP/1루 주자/이닝 단절 상황에서 공격 흐름을 되살리는 문제다. |
| RQ2 | 어떤 유형의 외국인 선수가 SSG에 맞는가? | 타자는 이닝 전환형 OF, 투수는 traffic-command starter가 맞다. |
| RQ3 | 데이터마이닝 모델은 후보를 어떻게 바꿨는가? | 타자는 Matos/Jones를 상단으로 끌어올렸고, 투수는 raw 후보를 의료/계약 게이트로 재배치했다. |
| RQ4 | 최종 접촉 1순위는 누구인가? | 타자 Luis Matos, 투수 Josh Fleming이다. 단 Jones는 조건부 model lead로 별도 관리한다. |

## 1. SSG 문제는 장타 부족이 아니라 경기 흐름 단절이다

SSG의 보강 포인트를 `장타가 부족하니 거포를 사자`로 정의하면 후보군은 너무 평범해진다. 이 프로젝트의 데이터마이닝은 반대로 출발했다. 먼저 SSG가 어떤 경기 상태에서 반복적으로 무너지는지 찾고, 그 상태를 복구할 수 있는 선수 유형을 역으로 정의했다.

![SSG hidden weakness rules](assets/hidden_weakness_rules.png)

위 그래프의 핵심은 특정 상황이 걸렸을 때 평균 득실이 크게 음수로 밀린다는 점이다. 특히 RHP game-script lock은 20경기에서 승률 0.100, 평균 득실 -5.10으로 나타났고, run-kill avoidance와 extra-out resilience rule도 승률과 득실이 동시에 무너졌다. 이 패턴은 “외야 홈런이 모자라다”보다 훨씬 구체적이다. SSG는 득점권 이후보다 그 이전 단계, 즉 1루 주자 상황을 다음 득점 기회로 번역하는 과정에서 더 큰 병목을 보인다.

{md_table(hidden_rows, ["메시지 조각", "근거 요약", "의사결정 사용", "신뢰도"])}

### 보강 유형으로 번역

이 메시지를 선수 feature로 바꾸면 타자와 투수의 계약 조건이 달라진다. 타자는 OPS 순위표가 아니라 `vs RHP on-base damage`, `run-kill risk`, `two-strike survival`, `corner OF/DH continuity`를 봐야 한다. 투수는 ERA 순위표가 아니라 `low free-pass volatility`, `damage control after traffic`, `five-inning floor`, `ABS zone command`를 봐야 한다.

{md_table(feature_rows, ["슬롯", "메시지", "후보 변수", "방향", "모델 사용", "해석"])}

## 2. 하나의 앙상블 모델: 네 명의 의견을 투표가 아니라 base learner로 통합

네 명의 후보 추천은 겉으로 보면 서로 다르지만, 실제로는 서로 다른 base learner가 같은 시장을 다른 각도에서 본 결과다. 그래서 최종 통합은 “몇 명이 추천했는가”가 아니라, 어떤 모델 블록이 후보를 밀었고 어떤 게이트가 후보를 눌렀는지로 설계했다.

{md_table(model_rows, ["슬롯", "모델 블록", "학습 표본", "모델", "목표", "변수군", "판단"])}

타자는 historical success/failure classifier의 성능이 상대적으로 강하기 때문에 가장 큰 비중을 준다. 반면 투수는 과거 표본으로 만든 success diagnostic이 강한 확정 모델이라기보다 위험을 줄이는 보조 신호에 가깝다. 이 차이를 인정해야 결론이 과장되지 않는다.

{md_table(weight_rows, ["슬롯", "base learner", "가중치", "이유"])}

### 모델 작동 방식

1. **M1 Hidden Weakness Mining**: SSG 경기 상태별 약점을 찾아 선수에게 요구되는 feature contract를 만든다.
2. **M2 KBO Success/Failure Classifier**: 과거 KBO 외국인 선수의 입단 전 지표와 성공/실패 라벨을 연결해 후보의 성공/실패 확률을 추정한다.
3. **M3 KBO Translation Filter**: MLB/MiLB 성과가 KBO 환경에서 유지될 가능성을 구종 대응, K/BB, contact floor, BB9/HR9 등으로 점검한다.
4. **M4 Market Construction**: 40인 로스터 밖, DFA/outright/minor contract, AAA regular role 같은 접근 가능한 시장을 구성한다.
5. **M5 Failure Risk Gate**: 부상, 계약 부담, 역할 불일치, 극단적 삼진/볼넷 리스크를 따로 확인한다.
6. **M6 Consensus Ensemble**: 팀원별 후보, 구조화 모델 후보, historical model 후보가 반복 등장할 때 안정성 보너스를 준다.

## 3. 데이터 범위와 모델 입력

이번 보고서의 수치 근거는 STATIZ/KBO, MLB Savant, MiLB/roster/transaction, NPB 공식 수집 산출물에서 나온 구조화 테이블을 중심으로 구성했다. 후보 추천에는 KBO 입단 이후 성과를 feature로 넣지 않고, 과거 사례의 label과 backtest 평가에만 사용한다.

{md_table(coverage_rows, ["데이터 묶음", "파일", "용량", "행 수", "해석"])}

## 4. 타자 결론: Raw 1위와 최종 1순위가 갈리는 이유

타자 raw ensemble에서는 Nolan Jones가 1위다. 그는 좌타 코너 OF, 강한 hard-hit/barrel, SSG fit, 팀원 반복 등장 신호가 모두 겹친다. 그러나 최종 영입 board에서는 계약/비용 게이트가 들어오면서 Luis Matos가 최종 접촉 1순위로 올라온다. 이 순위 변화는 모델이 약해서가 아니라, 프런트 의사결정에 더 가까워졌다는 신호다.

![Hitter success probabilities](assets/hitter_success_probabilities.png)

{md_table(hitter_raw, ["Raw 순위", "선수", "앙상블", "성공확률", "실패확률", "반복 등장", "해석"])}

### Gate-adjusted Top 3

{md_table([
    {
        "최종 순위": int(r["gate_adjusted_rank"]) if isinstance(r["gate_adjusted_rank"], (int, float)) or str(r["gate_adjusted_rank"]).isdigit() else r["gate_adjusted_rank"],
        "선수": r["player"],
        "판단": r["decision"],
        "성공확률": pct(r["model_success_prob"]),
        "실패확률": pct(r["model_failure_prob"]),
        "비용 신호": money(r["salary_signal_usd"]),
        "핵심 해석": r["final_summary"],
    }
    for _, r in hitter_gate.iterrows()
], ["최종 순위", "선수", "판단", "성공확률", "실패확률", "비용 신호", "핵심 해석"])}

### 선수별 해석

**Luis Matos는 모델이 찾은 비용 효율형 1순위다.** 최근 표본에서 K% 16.6%로 접촉 floor가 가장 안정적이고, historical KBO success model은 성공확률 92.4%, 실패확률 8.2%로 평가했다. 장타 총량만 보면 Jones나 Suwinski보다 덜 화려하지만, SSG가 필요로 하는 것은 “이닝을 끊지 않는 외야수”라는 점에서 가장 현실적인 접촉 1순위다.

**Nolan Jones는 model lead지만 계약 게이트 확인이 필요하다.** 그는 raw ensemble 1위이고 성공확률 90.2%, 실패확률 9.2%로 강하다. 다만 2026 현금 신호가 $2.00M로 잡혀 있어, 실제 남은 부담액과 buyout 또는 cost-share 가능성을 확인해야 한다. 비용 문제가 해결되면 Matos와 1순위를 다시 경쟁할 수 있다.

**Jack Suwinski는 upside board다.** BB% 13.5%, barrel 11.8%는 매력적이지만 K% 31.5%와 failure model warning이 강하다. 즉 SSG가 필요로 하는 run-kill avoidance와 충돌할 가능성이 있다. 그래서 최종 발표에서는 “3순위 후보”라기보다 “조건이 맞을 때 upside를 사는 후보”로 표현하는 것이 정확하다.

## 5. 투수 결론: Raw Top 3를 그대로 쓰면 오판이 된다

투수는 타자보다 모델 확신도가 낮다. 따라서 투수 board는 예측확률 하나로 결론을 내리면 위험하고, raw signal과 risk gate를 분리해야 한다. 실제로 raw ensemble에서는 Josh Fleming, Carson Spiers, Brian Van Belle이 상단에 있지만, Spiers와 Van Belle은 의료 신호 때문에 활성 후보군에서 내려간다.

![Pitcher gate movement](assets/pitcher_gate_movement.png)

{md_table(pitcher_raw, ["Raw 순위", "선수", "앙상블", "반복 등장", "해석"])}

### Gate-adjusted Top 3

{md_table([
    {
        "최종 순위": int(r["gate_adjusted_rank"]) if isinstance(r["gate_adjusted_rank"], (int, float)) or str(r["gate_adjusted_rank"]).isdigit() else r["gate_adjusted_rank"],
        "선수": r["player"],
        "판단": r["decision"],
        "성공확률": pct(r["model_success_prob"]),
        "실패확률": pct(r["model_failure_prob"]),
        "비용 신호": money(r["salary_signal_usd"]),
        "핵심 해석": r["final_summary"],
    }
    for _, r in pitcher_gate.iterrows()
], ["최종 순위", "선수", "판단", "성공확률", "실패확률", "비용 신호", "핵심 해석"])}

### Raw 상위였지만 보류된 후보

{md_table([
    {
        "Raw 순위": r["raw_ensemble_rank"],
        "선수": r["player"],
        "판단": r["decision"],
        "보류 이유": r["final_summary"],
    }
    for _, r in hold_gate.iterrows()
], ["Raw 순위", "선수", "판단", "보류 이유"])}

### 선수별 해석

**Josh Fleming은 최종 접촉 1순위다.** 여러 팀원 모델과 구조화 모델에서 반복 등장했고, 좌완 선발/스윙맨 역할, 낮은 HR9, 관리 가능한 BB9, minor contract 접근성이 함께 맞는다. 투수 모델의 성공확률만으로 강하게 단정하기보다, SSG의 traffic-command starter 필요와 시장 접근성이 같이 맞는 후보라고 설명하는 것이 가장 타당하다.

**Bryse Wilson은 backup verify 후보다.** raw ensemble에서는 낮게 보였지만, 2025-2026 MiLB 103이닝, 19선발, K9 8.65, BB9 2.79, HR9 0.96으로 선발 역할 검증에 필요한 구조화 지표가 있다. 모델 margin은 작기 때문에 적극 추천이 아니라 비교 검증군이다.

**Austin Gomber는 좌완 이닝 축적형 보조 후보다.** 172이닝, 37선발 표본은 선발 지속성을 보여준다. 다만 HR9 1.46과 낮은 모델 margin 때문에 KBO에서 장타 억제가 가능한지 추가 확인이 필요하다.

## 6. 최종 후보 board

{md_table(final_rows, ["슬롯", "선수", "최종 단계", "게이트 순위", "성공확률", "실패확률", "비용 신호", "핵심 역할"])}

### 최종 1인 결론

| 슬롯 | 최종 1순위 | 이유 |
|---|---|---|
| 외국인 타자 | Luis Matos | KBO 성공확률, 낮은 실패확률, 접촉 floor, 낮은 비용 신호, 외야 역할 가능성이 동시에 맞는다. |
| 외국인 선발투수 | Josh Fleming | 팀원 합의, 좌완 선발/스윙맨 역할, low HR/BB damage profile, 계약 접근성이 동시에 맞는다. |

## 7. 논의: 왜 이 결론이 데이터마이닝인가

이번 결론은 임의 가중치 점수표가 아니다. 첫째, SSG의 필요를 먼저 데이터로 정의했다. 둘째, 과거 KBO 외국인 선수 성공/실패 라벨을 학습한 모델을 후보 평가에 사용했다. 셋째, 그 결과를 KBO translation filter와 market gate로 다시 통과시켰다. 넷째, 팀원들의 후보 추천을 단순 다수결이 아니라 서로 다른 base learner의 반복 등장 신호로 처리했다.

이 구조 때문에 Nolan Jones와 Luis Matos의 관계를 더 정확히 설명할 수 있다. Jones는 raw model lead이고, Matos는 gate-adjusted contact lead다. 마찬가지로 투수에서는 Carson Spiers와 Brian Van Belle이 raw 상위였지만, 의료 게이트 때문에 실제 접촉 board에서는 Fleming, Wilson, Gomber 순으로 재배치된다.

## 8. 한계와 다음 확인 과제

| 영역 | 현재 판단 | 다음 확인 |
|---|---|---|
| 타자 계약 | Matos는 비용 효율적, Jones는 비용 확인 필요 | 남은 보장액, buyout, release/cost-share 가능성 |
| 타자 역할 | Matos/Jones/Suwinski 모두 OF 축에 걸림 | 실제 수비 위치, KBO 합류 후 좌/우익수 가능성 |
| 투수 모델 | 투수 classifier는 진단용으로 사용 | TrackMan/구종별 command, 최근 구속, medical report |
| 투수 역할 | Fleming은 선발/스윙맨, Wilson/Gomber는 선발 표본 | 실제 5이닝 floor와 한국행 의사 |
| 발표 표현 | raw score와 최종 후보를 분리해야 함 | “왜 1위가 바뀌었나”를 의사결정 논리로 설명 |

## 9. Source Notes

{md_table(source_rows, ["선수", "계약/의료 확인", "출처"])}

## Appendix A. 산출물 경로

| 산출물 | 경로 |
|---|---|
| 최종 후보 board | {as_source_path("outputs/tables/final_candidate_board.csv")} |
| 앙상블 후보 점수 | {as_source_path("outputs/tables/ensemble_candidate_scores_v1.csv")} |
| 타자 데이터마이닝 후보 | {as_source_path("outputs/tables/data_mining_hitter_candidates_v1.csv")} |
| 투수 데이터마이닝 후보 | {as_source_path("outputs/tables/data_mining_pitcher_candidates_v1.csv")} |
| 계약/연봉 게이트 | {as_source_path("outputs/tables/final_candidate_salary_contract_gate_v1.csv")} |
| SSG 숨은 약점 trace | {as_source_path("outputs/tables/ssg_layer1_evidence_to_message_trace_v4.csv")} |
| SSG 후보 변수 blueprint | {as_source_path("outputs/tables/ssg_layer1_candidate_feature_blueprint_v4.csv")} |
"""

    executive = f"""# Executive Summary

## 최종 결론

**외국인 타자 최종 접촉 1순위는 Luis Matos, 외국인 선발투수 최종 접촉 1순위는 Josh Fleming이다.** Nolan Jones는 타자 raw 모델 1위지만 계약/비용 확인이 필요한 조건부 model lead로 관리하고, Jack Suwinski는 high-upside 보조 후보로 둔다. 투수는 Josh Fleming을 중심으로 Bryse Wilson, Austin Gomber를 비교 검증군으로 둔다.

## 왜 이 결론인가

- SSG의 약점은 단순 장타 부족이 아니라 `RHP game-script`, `1루 주자 이후 전환`, `이닝 단절`, `추가 출루 이후 복구 실패`로 정의된다.
- 타자 모델은 과거 KBO 외국인 성공/실패 패턴에서 Matos와 Jones를 강하게 밀어 올렸다.
- 투수 모델은 진단 신호로 사용하고, 의료/역할/계약 게이트를 더 크게 반영했다.
- 최종 후보는 raw 점수 1위가 아니라 `모델 점수 + SSG fit + KBO 번역 + 시장 접근성 + 실패 리스크`를 동시에 통과한 선수다.

## 최종 후보 board

{md_table(final_rows, ["슬롯", "선수", "최종 단계", "게이트 순위", "성공확률", "실패확률", "비용 신호", "핵심 역할"])}
"""

    method = f"""# Method Appendix

## 1. 모델 개요

최종 모델은 여섯 개 base learner/lens를 결합한 앙상블 구조다.

{md_table(weight_rows, ["슬롯", "base learner", "가중치", "이유"])}

## 2. Historical KBO Success/Failure Models

{md_table(model_rows, ["슬롯", "모델 블록", "학습 표본", "모델", "목표", "변수군", "판단"])}

## 3. SSG Feature Contract

{md_table(feature_rows, ["슬롯", "메시지", "후보 변수", "방향", "모델 사용", "해석"])}

## 4. 데이터 범위

{md_table(coverage_rows, ["데이터 묶음", "파일", "용량", "행 수", "해석"])}

## 5. 재현 경로

```bash
python3 scripts/build_leaf_node_report_artifacts_v1.py
```

생성 산출물:

| 산출물 | 경로 |
|---|---|
| Leaf node용 HTML | `reports/leaf_node/index.html` |
| 최종 보고서 Markdown | `reports/leaf_node/final_report.md` |
| 요약본 Markdown | `reports/leaf_node/executive_summary.md` |
| 방법론 부록 Markdown | `reports/leaf_node/method_appendix.md` |
| 최종 후보 CSV | `outputs/tables/final_candidate_board.csv` |
"""

    return {
        "final_report.md": final_report,
        "executive_summary.md": executive,
        "method_appendix.md": method,
    }


def markdown_to_html(markdown_text: str) -> str:
    try:
        import markdown as md  # type: ignore

        return md.markdown(markdown_text, extensions=["tables", "fenced_code"])
    except Exception:
        def inline(text: str) -> str:
            escaped = html.escape(text)
            escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
            escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
            return escaped

        def parse_table(block: list[str]) -> str:
            rows = []
            for line in block:
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                rows.append(cells)
            if len(rows) < 2:
                return "\n".join(f"<p>{inline(line)}</p>" for line in block)
            headers = rows[0]
            body = rows[2:]
            parts = ["<table>", "<thead><tr>"]
            parts.extend(f"<th>{inline(cell)}</th>" for cell in headers)
            parts.append("</tr></thead><tbody>")
            for row in body:
                parts.append("<tr>")
                parts.extend(f"<td>{inline(cell)}</td>" for cell in row)
                parts.append("</tr>")
            parts.append("</tbody></table>")
            return "\n".join(parts)

        lines = []
        in_ul = False
        in_code = False
        code_buf = []
        raw_lines = markdown_text.splitlines()
        i = 0
        while i < len(raw_lines):
            line = raw_lines[i]
            if line.startswith("```"):
                if not in_code:
                    in_code = True
                    code_buf = []
                else:
                    lines.append("<pre><code>" + html.escape("\n".join(code_buf)) + "</code></pre>")
                    in_code = False
                i += 1
                continue
            if in_code:
                code_buf.append(line)
                i += 1
                continue
            if line.startswith("|") and i + 1 < len(raw_lines) and raw_lines[i + 1].startswith("|"):
                block = []
                while i < len(raw_lines) and raw_lines[i].startswith("|"):
                    block.append(raw_lines[i])
                    i += 1
                if in_ul:
                    lines.append("</ul>")
                    in_ul = False
                lines.append(parse_table(block))
                continue
            if line.startswith("# "):
                lines.append(f"<h1>{inline(line[2:])}</h1>")
            elif line.startswith("## "):
                lines.append(f"<h2>{inline(line[3:])}</h2>")
            elif line.startswith("### "):
                lines.append(f"<h3>{inline(line[4:])}</h3>")
            elif line.startswith("!["):
                match = re.match(r"!\[(.*?)\]\((.*?)\)", line)
                if match:
                    lines.append(f'<img src="{html.escape(match.group(2))}" alt="{html.escape(match.group(1))}">')
            elif line.startswith("- "):
                if not in_ul:
                    lines.append("<ul>")
                    in_ul = True
                lines.append(f"<li>{inline(line[2:])}</li>")
            elif line.strip() == "":
                if in_ul:
                    lines.append("</ul>")
                    in_ul = False
            else:
                if in_ul:
                    lines.append("</ul>")
                    in_ul = False
                lines.append(f"<p>{inline(line)}</p>")
            i += 1
        if in_ul:
            lines.append("</ul>")
        return "\n".join(lines)


def build_html(final_report_md: str) -> str:
    body = markdown_to_html(final_report_md)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SSG 외국인 선수 영입 전략 보고서</title>
  <style>
    :root {{
      --ink: #20242d;
      --muted: #687084;
      --line: #dfe3ec;
      --panel: #ffffff;
      --wash: #f6f7fa;
      --accent: #b5121b;
      --accent-soft: #fff0f1;
    }}
    body {{
      margin: 0;
      background: var(--wash);
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Apple SD Gothic Neo", "Noto Sans KR", "Segoe UI", sans-serif;
      line-height: 1.68;
    }}
    main {{
      width: min(1080px, calc(100vw - 40px));
      margin: 44px auto 72px;
      background: var(--panel);
      border: 1px solid var(--line);
      box-shadow: 0 18px 48px rgba(28, 34, 45, .08);
      padding: 56px 64px;
    }}
    h1 {{
      font-size: clamp(30px, 4vw, 48px);
      line-height: 1.12;
      letter-spacing: 0;
      margin: 0 0 28px;
      padding-bottom: 20px;
      border-bottom: 4px solid var(--accent);
    }}
    h2 {{
      font-size: 26px;
      margin: 44px 0 16px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
    }}
    h3 {{
      font-size: 20px;
      margin: 30px 0 12px;
    }}
    p, li {{
      font-size: 16px;
    }}
    strong {{
      color: var(--accent);
    }}
    img {{
      max-width: 100%;
      display: block;
      margin: 22px 0 26px;
      border: 1px solid var(--line);
      background: #fff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0 28px;
      font-size: 14px;
    }}
    th {{
      background: #15171d;
      color: #fff;
      text-align: left;
      font-weight: 700;
    }}
    td, th {{
      border: 1px solid var(--line);
      padding: 9px 10px;
      vertical-align: top;
    }}
    tr:nth-child(even) td {{
      background: #fafbfe;
    }}
    code, pre {{
      font-family: "SF Mono", Menlo, Consolas, monospace;
      background: #f1f3f7;
      border-radius: 6px;
    }}
    code {{
      padding: 2px 5px;
    }}
    pre {{
      padding: 14px;
      overflow-x: auto;
    }}
    @media (max-width: 760px) {{
      main {{
        width: auto;
        margin: 0;
        padding: 28px 18px;
        border: 0;
        box-shadow: none;
      }}
      table {{
        display: block;
        overflow-x: auto;
        white-space: nowrap;
      }}
    }}
  </style>
</head>
<body>
  <main>
    {body}
  </main>
</body>
</html>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    board = build_final_board()
    chart_map = make_charts(board)
    reports = build_report(board, chart_map)

    for filename, content in reports.items():
        (OUT_DIR / filename).write_text(content, encoding="utf-8")

    html_text = build_html(reports["final_report.md"])
    (OUT_DIR / "index.html").write_text(html_text, encoding="utf-8")

    print(f"Wrote {OUT_DIR / 'final_report.md'}")
    print(f"Wrote {OUT_DIR / 'executive_summary.md'}")
    print(f"Wrote {OUT_DIR / 'method_appendix.md'}")
    print(f"Wrote {OUT_DIR / 'index.html'}")
    print(f"Wrote {TABLE_DIR / 'final_candidate_board.csv'}")
    print(f"Charts: {len(chart_map)}")


if __name__ == "__main__":
    main()
