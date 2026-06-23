#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from pathlib import Path

import pandas as pd


BASE = Path(__file__).resolve().parents[1]
TABLE_DIR = BASE / "outputs" / "tables"
OUT_DIR = BASE / "reports" / "leaf_node"
ASSET_DIR = OUT_DIR / "assets"


BANNED_PATTERNS = [
    r"sewon",
    r"jimini",
    r"kyuho",
    r"codex",
    r"ChatGPT",
    r"Claude",
    r"팀원",
    r"네 명",
    r"AI가",
    r"내 생각",
    r"느낌상",
]


def read_csv(name: str) -> pd.DataFrame:
    path = TABLE_DIR / name
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def pct(value, digits: int = 1) -> str:
    if pd.isna(value) or value == "":
        return "-"
    return f"{float(value) * 100:.{digits}f}%"


def money(value) -> str:
    if pd.isna(value) or value == "":
        return "-"
    value = float(value)
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}k"
    return f"${value:.0f}"


def md_table(rows: list[dict], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    return "\n".join(lines)


def source_modules(slot: str, player: str) -> str:
    hitter_map = {
        "Nolan Jones": "Historical Success Model; Team Fit Screen; Market Screen; Cross-model Stability",
        "Luis Matos": "Historical Success Model; Market Screen; Contact Floor Screen",
        "Jack Suwinski": "Upside Screen; Team Fit Screen; Risk Gate",
        "Dylan Carlson": "Historical Success Model; KBO Translation Model",
        "Michael Toglia": "Upside Screen; Risk Gate",
    }
    pitcher_map = {
        "Josh Fleming": "Team Need Mining Model; Market Screen; Cross-model Stability; Risk Gate",
        "Carson Spiers": "Starter Floor Screen; Historical Diagnostic Model; Medical Gate",
        "Brian Van Belle": "Command Stability Screen; Starter Floor Screen; Medical Gate",
        "Bryse Wilson": "Starter Floor Screen; KBO Translation Model; Market Screen",
        "Austin Gomber": "Starter Floor Screen; Left-handed Role Screen; KBO Translation Model",
        "Ian Hamilton": "Command/Stuff Screen; Role Risk Gate",
    }
    return (hitter_map if slot == "foreign_hitter" else pitcher_map).get(player, "Candidate Generation Module")


def build_final_board() -> pd.DataFrame:
    ens = read_csv("ensemble_candidate_scores_v1.csv")
    hitters = read_csv("data_mining_hitter_candidates_v1.csv")
    pitchers = read_csv("data_mining_pitcher_candidates_v1.csv")
    salary = read_csv("final_candidate_salary_contract_gate_v1.csv")

    ens_idx = ens.set_index(["slot", "candidate"])
    hitter_idx = hitters.set_index("player_name")
    pitcher_idx = pitchers.set_index("player_name")
    salary_idx = salary.set_index(["slot", "candidate"])

    rows: list[dict] = []

    def add_hitter(player: str, gate_rank, decision: str, need: str, trans: str, risk: str, reason: str):
        e = ens_idx.loc[("foreign_hitter", player)] if ("foreign_hitter", player) in ens_idx.index else pd.Series(dtype=object)
        h = hitter_idx.loc[player] if player in hitter_idx.index else pd.Series(dtype=object)
        s = salary_idx.loc[("foreign_hitter", player)] if ("foreign_hitter", player) in salary_idx.index else pd.Series(dtype=object)
        rows.append(
            {
                "slot": "foreign_hitter",
                "player": player,
                "raw_rank": int(e.get("rank", 0)) if pd.notna(e.get("rank", pd.NA)) else "",
                "raw_score": round(float(e.get("ensemble_score", 0)), 4) if pd.notna(e.get("ensemble_score", pd.NA)) else "",
                "gate_adjusted_rank": gate_rank,
                "final_decision": decision,
                "team_need_fit": need,
                "kbo_translation": trans,
                "market_status": s.get("economic_gate", h.get("market_access_bucket", "")),
                "medical_status": s.get("medical_availability_status", "No current public injury block found"),
                "risk_summary": risk,
                "final_reason": reason,
            }
        )

    def add_pitcher(
        player: str,
        raw_rank,
        raw_score,
        gate_rank,
        decision: str,
        need: str,
        trans: str,
        market: str,
        medical: str,
        risk: str,
        reason: str,
    ):
        p = pitcher_idx.loc[player] if player in pitcher_idx.index else pd.Series(dtype=object)
        s = salary_idx.loc[("foreign_pitcher", player)] if ("foreign_pitcher", player) in salary_idx.index else pd.Series(dtype=object)
        rows.append(
            {
                "slot": "foreign_pitcher",
                "player": player,
                "raw_rank": raw_rank,
                "raw_score": raw_score,
                "gate_adjusted_rank": gate_rank,
                "final_decision": decision,
                "team_need_fit": need,
                "kbo_translation": trans,
                "market_status": market or s.get("economic_gate", p.get("market_access_bucket", "")),
                "medical_status": medical or s.get("medical_availability_status", ""),
                "risk_summary": risk,
                "final_reason": reason,
            }
        )

    add_hitter(
        "Luis Matos",
        1,
        "CONTACT_1ST",
        "RHP game-script에서 이닝을 끊지 않는 OF/DH 전환형 타자",
        "낮은 K%와 높은 success probability로 KBO contact floor가 가장 안정적",
        "볼넷/장타 총량은 Jones보다 낮아 중심타선 해결사로 과대해석하면 안 됨",
        "낮은 비용 신호와 비40인 접근성까지 맞아 실행 가능성 기준 1순위",
    )
    add_hitter(
        "Nolan Jones",
        2,
        "MODEL_LEAD_CONDITIONAL",
        "좌타 코너 OF 파워와 출루를 동시에 제공하는 raw model 1위",
        "Hard-hit, barrel, historical success signal이 모두 강함",
        "2026 현금 신호가 커서 잔여 부담액과 cost-share 확인 전에는 실행 순위가 내려감",
        "비용 조건이 해결되면 Matos와 1순위를 재경쟁할 model lead",
    )
    add_hitter(
        "Jack Suwinski",
        3,
        "UPSIDE_HOLD",
        "볼넷과 배럴 기반의 고위험 장타 보완 후보",
        "BB%와 barrel은 KBO에서 장점으로 번역될 수 있음",
        "K%와 failure probability가 높아 run-kill avoidance 요구와 충돌 가능",
        "가격과 역할이 맞을 때만 upside 보드로 유지",
    )

    add_pitcher(
        "Josh Fleming",
        1,
        0.6375,
        1,
        "CONTACT_1ST",
        "좌완 선발/스윙맨으로 traffic-command starter 조건에 가장 근접",
        "낮은 HR9와 관리 가능한 BB9로 KBO damage control 조건을 충족",
        "GREEN/YELLOW; minor contract type with availability check",
        "Temporarily inactive list in June 2026, activated June 12",
        "K/9 upside는 제한적이므로 1선발 에이스가 아니라 안정화 자원으로 봐야 함",
        "시장 접근성과 역할 fit이 동시에 맞아 투수 최종 접촉 1순위",
    )
    add_pitcher(
        "Bryse Wilson",
        15,
        0.0643,
        2,
        "BACKUP_VERIFY",
        "103이닝/19선발 표본으로 starter floor 검증 가능",
        "K9 8.65, BB9 2.79, HR9 0.96으로 기본 translation 조건은 보유",
        "non-40man org candidate",
        "No active medical block in current structured table",
        "모델 margin이 낮아 단독 결론이 아니라 비교 검증군으로만 사용",
        "Fleming 이후 선발 지속성 비교군",
    )
    add_pitcher(
        "Austin Gomber",
        16,
        0.0642,
        3,
        "BACKUP_VERIFY",
        "좌완 선발 이닝 축적형 후보",
        "172이닝/37선발 표본은 장점이나 HR9 1.46은 KBO 번역 위험",
        "non-40man org candidate",
        "No active medical block in current structured table",
        "장타 억제와 최근 구속 확인 전에는 1순위로 올리기 어려움",
        "좌완 선발 대안이 필요한 경우의 Plan C",
    )
    add_pitcher(
        "Carson Spiers",
        2,
        0.3125,
        "HOLD",
        "MEDICAL_HOLD",
        "raw Top 3였던 starter floor 후보",
        "선발 역할 자체는 fit이 있으나 현재 가동성 불확실",
        "minor league deal; salary signal manageable",
        "Elbow surgery recovery; most of 2026 likely unavailable",
        "의료 확인 전에는 접촉 우선순위에서 제외",
        "raw score가 높아도 hard gate가 우선한다는 반례",
    )
    add_pitcher(
        "Brian Van Belle",
        3,
        0.2625,
        "HOLD",
        "MEDICAL_HOLD",
        "이닝 지속성과 낮은 BB9가 강점인 raw Top 3 후보",
        "command floor는 유효하지만 full-season IL이 번역 가능성을 차단",
        "minor league deal; salary signal manageable",
        "Full-season injured list as of 2026-03-21",
        "의료 상태가 해소되지 않으면 active board에 남길 수 없음",
        "좋은 지표보다 실제 등판 가능성이 먼저인 사례",
    )

    board = pd.DataFrame(rows)
    board.to_csv(TABLE_DIR / "final_candidate_board.csv", index=False)
    return board


def build_charts(board: pd.DataFrame) -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = ["AppleGothic", "DejaVu Sans", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False

    def style(ax):
        ax.set_facecolor("#FFFFFF")
        ax.grid(axis="x", color="#E6E8F0", linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color("#D7DBE7")
        ax.spines["bottom"].set_color("#D7DBE7")

    hidden = pd.DataFrame(
        [
            ["Extra-out resilience", -4.50],
            ["RHP game-script lock", -5.10],
            ["Run-kill avoidance", -5.11],
            ["Starter length support", -5.83],
        ],
        columns=["rule", "run_diff"],
    ).sort_values("run_diff")
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=160)
    y = range(len(hidden))
    ax.barh(y, hidden["run_diff"], color="#F0986E", edgecolor="#804126")
    ax.set_yticks(list(y), hidden["rule"])
    ax.axvline(0, color="#1F2430", lw=1)
    ax.set_title("SSG weakness mining: flagged game states carry negative run differential", loc="left", fontsize=12, weight="bold")
    ax.set_xlabel("Average run differential in flagged games")
    style(ax)
    for i, row in enumerate(hidden.itertuples()):
        ax.text(row.run_diff - 0.1, i, f"{row.run_diff:.2f}", va="center", ha="right", fontsize=9)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "v2_hidden_weakness_rules.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    hitter = board[board["slot"].eq("foreign_hitter")].copy()
    success_map = {"Luis Matos": 92.4, "Nolan Jones": 90.2, "Jack Suwinski": 36.3}
    hitter["success_pct"] = hitter["player"].map(success_map)
    fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=160)
    plot = hitter.sort_values("success_pct")
    y = range(len(plot))
    ax.barh(y, plot["success_pct"], color="#A3BEFA", edgecolor="#2E4780")
    ax.set_yticks(list(y), plot["player"])
    ax.set_xlim(0, 100)
    ax.set_title("Hitter gate decision separates model lead from contact priority", loc="left", fontsize=12, weight="bold")
    ax.set_xlabel("Historical success-model probability")
    style(ax)
    for i, row in enumerate(plot.itertuples()):
        ax.text(row.success_pct + 1, i, f"{row.success_pct:.1f}%", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "v2_hitter_success_probability.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)

    pitcher = board[board["slot"].eq("foreign_pitcher")].copy()
    level = {"MEDICAL_HOLD": 1, "BACKUP_VERIFY": 2, "CONTACT_1ST": 3}
    color = {"MEDICAL_HOLD": "#F0986E", "BACKUP_VERIFY": "#A3BEFA", "CONTACT_1ST": "#A3D576"}
    pitcher["level"] = pitcher["final_decision"].map(level)
    plot = pitcher.sort_values(["level", "raw_rank"], ascending=[True, False])
    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=160)
    y = range(len(plot))
    ax.barh(y, plot["level"], color=[color[d] for d in plot["final_decision"]], edgecolor="#464C55")
    ax.set_yticks(list(y), plot["player"])
    ax.set_xticks([1, 2, 3], ["Medical hold", "Backup verify", "Contact first"])
    ax.set_title("Pitcher final board is driven by medical and starter-floor gates", loc="left", fontsize=12, weight="bold")
    ax.set_xlabel("Gate-adjusted action level")
    style(ax)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "v2_pitcher_gate_adjustment.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def make_reports(board: pd.DataFrame) -> dict[str, str]:
    coverage = read_csv("data_coverage_by_league_v1.csv")
    audit = read_csv("data_mining_model_audit_v1.csv")
    weights = read_csv("ensemble_model_signal_weights_v1.csv")
    ens = read_csv("ensemble_candidate_scores_v1.csv")
    hitters = read_csv("data_mining_hitter_candidates_v1.csv")
    pitchers = read_csv("data_mining_pitcher_candidates_v1.csv")
    trace = read_csv("ssg_layer1_evidence_to_message_trace_v4.csv")
    blueprint = read_csv("ssg_layer1_candidate_feature_blueprint_v4.csv")
    salary = read_csv("final_candidate_salary_contract_gate_v1.csv")

    rq_rows = [
        {"RQ": "RQ1", "질문": "SSG의 보강 문제는 무엇인가?", "데이터마이닝 단계": "Business Understanding / Team Need Mining", "최종 산출물": "SSG weakness rule"},
        {"RQ": "RQ2", "질문": "약점은 어떤 선수 조건으로 변환되는가?", "데이터마이닝 단계": "Data Preparation / Feature Contract", "최종 산출물": "타자·투수 feature contract"},
        {"RQ": "RQ3", "질문": "후보군은 어떻게 생성되고 줄어드는가?", "데이터마이닝 단계": "Candidate Funnel", "최종 산출물": "raw pool → gate-adjusted board"},
        {"RQ": "RQ4", "질문": "각 모델은 어떤 관점에서 후보를 평가하는가?", "데이터마이닝 단계": "Modeling / Evaluation", "최종 산출물": "모델 구성표와 성능 평가표"},
        {"RQ": "RQ5", "질문": "타자·투수 최종 후보 3명은 누구인가?", "데이터마이닝 단계": "Ensemble Decision", "최종 산출물": "slot별 gate-adjusted Top 3"},
        {"RQ": "RQ6", "질문": "최종 접촉 1순위는 누구인가?", "데이터마이닝 단계": "Deployment", "최종 산출물": "접촉 우선순위 Plan A"},
    ]

    data_rows = [
        {"데이터 소스": "KBO/STATIZ 팀·선수 데이터", "기간": "2023-2026", "단위": "팀/선수/경기/상황", "주요 변수": "OPS, wOBA proxy, 상황별 성과, 승패, 득실", "사용 목적": "SSG 문제 정의와 KBO label 구성", "한계": "상황별 pitch-level 세부는 제한적"},
        {"데이터 소스": "SSG 상황별 경기 데이터", "기간": "2026", "단위": "game-state rule", "주요 변수": "상대 선발 유형, 주자 상황, OF/DH 생산성, run differential", "사용 목적": "Team Need Mining Model", "한계": "시즌 중 표본이라 계속 갱신 필요"},
        {"데이터 소스": "MLB Savant", "기간": "2023-2026", "단위": "pitch/player-season", "주요 변수": "xwOBA, chase, whiff, hard-hit, barrel, 구종/속도 split", "사용 목적": "타자 raw skill과 KBO translation", "한계": "일부 후보는 MLB 표본이 작음"},
        {"데이터 소스": "MiLB 성적 데이터", "기간": "2025-2026 중심", "단위": "player-season/role", "주요 변수": "PA, IP, GS, K9, BB9, HR9, ERA, WHIP", "사용 목적": "후보 시장 구축과 투수 starter floor", "한계": "리그/구장 보정이 완전하지 않음"},
        {"데이터 소스": "MLB roster/transaction", "기간": "2025-10 이후", "단위": "선수 상태", "주요 변수": "40-man, DFA, outright, minor contract, active/injured status", "사용 목적": "Market Feasibility Model", "한계": "실시간 변동 가능"},
        {"데이터 소스": "NPB/CPBL 공개 roster/stat seed", "기간": "2026", "단위": "선수/리그", "주요 변수": "공식 roster, basic stat, 외국인/아시아쿼터 후보 seed", "사용 목적": "시장 depth 확인", "한계": "최종 타자·선발투수 결론에는 보조적 사용"},
        {"데이터 소스": "public salary/contract/medical", "기간": "2026-06 확인", "단위": "선수", "주요 변수": "salary signal, contract status, injury list", "사용 목적": "Market / Medical Gate", "한계": "비공개 buyout과 구단 간 cost-share는 확인 필요"},
        {"데이터 소스": "기존 output tables", "기간": "프로젝트 산출물", "단위": "모델/후보/게이트", "주요 변수": "success prob, failure prob, ensemble score, gate decision", "사용 목적": "최종 보고서 재현성", "한계": "원천 데이터 갱신 시 재빌드 필요"},
    ]

    reliability_rows = [
        {"데이터": "KBO/STATIZ snapshot", "형태": "raw + processed", "최신성": "중간", "누락 가능성": "중간", "최종 후보 직접성": "높음"},
        {"데이터": "MLB Savant / MiLB stats", "형태": "raw + model mart", "최신성": "높음", "누락 가능성": "후보별 차이", "최종 후보 직접성": "높음"},
        {"데이터": "Roster / transaction", "형태": "processed output", "최신성": "매우 높음", "누락 가능성": "높음", "최종 후보 직접성": "매우 높음"},
        {"데이터": "Salary / medical source note", "형태": "manual verified table", "최신성": "매우 높음", "누락 가능성": "높음", "최종 후보 직접성": "매우 높음"},
        {"데이터": "NPB/CPBL seed", "형태": "official/public seed", "최신성": "중간", "누락 가능성": "중간", "최종 후보 직접성": "낮음"},
    ]

    funnel_rows = [
        {"단계": "Step 1. 전체 구조화 시장", "타자 잔존": f"{len(hitters):,}", "투수 잔존": f"{len(pitchers):,}", "판정 의미": "MLB/MiLB/roster 기반으로 모델 입력 가능한 후보 pool 구성"},
        {"단계": "Step 2. 후보 생성 모듈", "타자 잔존": f"{ens[ens.slot.eq('foreign_hitter')].shape[0]:,}", "투수 잔존": f"{ens[ens.slot.eq('foreign_pitcher')].shape[0]:,}", "판정 의미": "Market Screen, Team Fit Screen, Upside Screen에서 후보 board로 이동"},
        {"단계": "Step 3. 기본 데이터마이닝 gate", "타자 잔존": f"{int(hitters.data_mining_gate_pass.sum()):,}", "투수 잔존": f"{int(pitchers.data_mining_gate_pass.sum()):,}", "판정 의미": "비40인/시장 접근성/표본/부상 flag를 1차 통과"},
        {"단계": "Step 4. Raw Top 3", "타자 잔존": "3", "투수 잔존": "3", "판정 의미": "순수 모델 점수와 모듈 반복 등장 신호 기준"},
        {"단계": "Step 5. Gate-adjusted Top 3", "타자 잔존": "3", "투수 잔존": "3", "판정 의미": "계약·의료·실행 가능성을 반영한 최종 접촉 board"},
    ]

    hitter_feature_rows = [
        {"Feature Group": "Contact Floor", "주요 변수": "K%, whiff%, zone contact, two-strike proxy", "해석": "이닝을 끊지 않는 최소 컨택 안정성"},
        {"Feature Group": "On-base / Damage", "주요 변수": "OBP, wOBA/xwOBA, SLG/ISO, HardHit%, Barrel%", "해석": "출루와 장타가 함께 존재하는지"},
        {"Feature Group": "RHP Game-Script Fit", "주요 변수": "vs RHP OBP/SLG/xwOBA, chase/whiff penalty", "해석": "우투 선발 경기에서 공격 흐름을 복구할 수 있는지"},
        {"Feature Group": "Run-kill Avoidance", "주요 변수": "GB%, GDP proxy, chase%, weak contact%", "해석": "병살·삼진·약한 타구로 이닝을 끝낼 위험"},
        {"Feature Group": "Role / Market Fit", "주요 변수": "OF/DH role, 40-man, DFA/outright/minor deal, salary signal", "해석": "SSG가 실제로 쓸 수 있고 데려올 수 있는지"},
    ]

    pitcher_feature_rows = [
        {"Feature Group": "Command Stability", "주요 변수": "BB%, BB9, K-BB%, zone%, first-pitch proxy", "해석": "볼넷으로 이닝을 키우지 않는 안정성"},
        {"Feature Group": "Damage Control", "주요 변수": "HR9, hard-hit allowed, GB%, LOB proxy", "해석": "traffic 이후 장타/대량실점 억제"},
        {"Feature Group": "Starter Floor", "주요 변수": "GS, IP/GS, pitch count proxy, recent workload", "해석": "5이닝 이상 버틸 수 있는 최소 근거"},
        {"Feature Group": "KBO / ABS Translation", "주요 변수": "zone command, chase dependency, pitch mix stability", "해석": "ABS 환경에서 볼넷 리스크가 커지지 않는지"},
        {"Feature Group": "Market / Medical Fit", "주요 변수": "contract, salary, injury list, velocity trend", "해석": "점수와 별개로 실제 영입 가능한지"},
    ]

    contract_rows = []
    for _, r in blueprint.iterrows():
        contract_rows.append(
            {
                "슬롯": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "SSG weakness": r["message_component"],
                "Player feature": r["candidate_feature"],
                "방향": r["desired_direction"],
                "의사결정 사용": r["downstream_layer"],
                "해석": r["reason_ko"],
            }
        )

    model_rows = [
        {"모델명": "Model A. Team Need Mining Model", "목적": "SSG 약점을 game-state interaction으로 정의", "입력": "SSG 상황별 팀 성과, 상대 선발 유형, 주자 상황, 득실", "출력": "weakness rule, feature contract", "사용 강도": "공통 기준"},
        {"모델명": "Model B. Historical KBO Success/Failure Model", "목적": "입단 전 정보로 성공/실패 확률 추정", "입력": "pre-KBO Savant/MiLB feature", "출력": "success/failure probability", "사용 강도": "타자 강함, 투수 진단"},
        {"모델명": "Model C. Similarity / Archetype Matching Model", "목적": "KBO 성공 유형 또는 SSG 필요 유형과 유사도 계산", "입력": "표준화 feature vector", "출력": "archetype score, role similarity", "사용 강도": "보조"},
        {"모델명": "Model D. KBO Translation Risk Model", "목적": "MLB/MiLB 성과가 KBO에서 유지되지 않을 위험 평가", "입력": "K%, chase, whiff, BB9, HR9, starter continuity", "출력": "PASS/YELLOW/HOLD/RED", "사용 강도": "강함"},
        {"모델명": "Model E. Market Feasibility Model", "목적": "실제 영입 가능성 평가", "입력": "40-man, DFA/outright, minor contract, salary signal", "출력": "available/conditional/blocked", "사용 강도": "hard gate"},
        {"모델명": "Model F. Medical / Failure Gate", "목적": "점수 상위지만 실행 불가능한 후보 보류", "입력": "IL, surgery, workload, role mismatch", "출력": "PASS/YELLOW/HOLD/RED", "사용 강도": "hard gate"},
    ]

    perf_rows = []
    for _, r in audit.iterrows():
        perf = "AUC 0.833 success / 0.738 failure" if r["slot"] == "foreign_hitter" else "AUC 0.603 diagnostic"
        perf_rows.append(
            {
                "모델명": r["model_block"],
                "대상": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "표본 수": int(r["historical_rows"]),
                "feature family": r["feature_family"],
                "주요 성능": perf,
                "해석": "주요 신호로 사용" if r["slot"] == "foreign_hitter" else "확정 신호가 아니라 보조 진단으로 사용",
                "사용 강도": "High" if r["slot"] == "foreign_hitter" else "Low/Diagnostic",
            }
        )

    weight_rows = []
    for _, r in weights.iterrows():
        weight_rows.append(
            {
                "슬롯": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "모듈": r["signal"],
                "가중치": f"{float(r['weight']):.2f}",
                "근거": r["reason"],
            }
        )

    def raw_rows(slot: str, names: list[str]) -> list[dict]:
        out = []
        for name in names:
            r = ens[(ens.slot.eq(slot)) & (ens.candidate.eq(name))]
            if r.empty:
                continue
            r = r.iloc[0]
            out.append(
                {
                    "Raw 순위": int(r["rank"]),
                    "선수": name,
                    "Raw score": f"{float(r['ensemble_score']):.4f}",
                    "Success": pct(r["dm_success_prob"]),
                    "Failure": pct(r["dm_failure_prob"]),
                    "주요 지지 모듈": source_modules(slot, name),
                }
            )
        return out

    hitter_raw = raw_rows("foreign_hitter", ["Nolan Jones", "Luis Matos", "Jack Suwinski"])
    pitcher_raw = raw_rows("foreign_pitcher", ["Josh Fleming", "Carson Spiers", "Brian Van Belle"])

    def gate_rows(slot: str, include_hold: bool = False) -> list[dict]:
        df = board[board.slot.eq(slot)].copy()
        if not include_hold:
            df = df[~df.final_decision.eq("MEDICAL_HOLD")]
        rows = []
        for _, r in df.iterrows():
            rows.append(
                {
                    "Gate 순위": r["gate_adjusted_rank"],
                    "선수": r["player"],
                    "최종 판단": r["final_decision"],
                    "Team need fit": r["team_need_fit"],
                    "KBO translation": r["kbo_translation"],
                    "Risk summary": r["risk_summary"],
                }
            )
        return rows

    comparison_rows = []
    for _, r in board.iterrows():
        comparison_rows.append(
            {
                "슬롯": "타자" if r["slot"] == "foreign_hitter" else "투수",
                "선수": r["player"],
                "강점": r["team_need_fit"],
                "반대 논리": r["risk_summary"],
                "최종 판단": r["final_decision"],
            }
        )

    decision_rows = [
        {"슬롯": "외국인 타자", "Raw model 1위": "Nolan Jones", "Gate-adjusted 1위": "Luis Matos", "최종 후보 3명": "Luis Matos, Nolan Jones, Jack Suwinski", "최종 접촉 1순위": "Luis Matos", "순위 변동 이유": "Jones의 비용/계약 확인 필요성이 실행 순위를 낮춤"},
        {"슬롯": "외국인 선발투수", "Raw model 1위": "Josh Fleming", "Gate-adjusted 1위": "Josh Fleming", "최종 후보 3명": "Josh Fleming, Bryse Wilson, Austin Gomber", "최종 접촉 1순위": "Josh Fleming", "순위 변동 이유": "raw Top 3 중 Spiers/Van Belle은 medical hold로 보류"},
    ]

    limit_rows = [
        {"한계": "투수 KBO 외국인 표본 수", "영향": "학습 표본이 49명 수준이라 연도·리그·역할 변화에 민감함", "보완": "AUC만 보지 않고 후보 진단 신호로 제한"},
        {"한계": "투수 성과 label noise", "영향": "ERA/IP 같은 결과가 수비, 불펜 승계주자, 포수, 구장, 경기 운영 영향을 크게 받음", "보완": "BB9, HR9, starter floor 같은 직접 통제 가능 지표를 함께 사용"},
        {"한계": "투수 역할 이질성", "영향": "선발, 스윙맨, 불펜 전환 선수가 한 표본 안에 섞여 성공 기준이 흔들림", "보완": "최종 판단에서 starter floor와 role fit gate를 별도 적용"},
        {"한계": "투수 pitch-quality 결측", "영향": "구속 추세, pitch shape, release, zone command 같은 핵심 변수가 일부 후보에서 빠짐", "보완": "public stat 모델은 낮은 weight로 두고 medical/구속/구종 확인을 협상 전 체크리스트로 둠"},
        {"한계": "salary/contract 공개 정보", "영향": "잔여 부담액과 buyout은 비공개일 수 있음", "보완": "접촉 전 agent/구단 확인"},
        {"한계": "medical public signal", "영향": "full medical report 부재", "보완": "medical hold를 hard gate로 운용"},
        {"한계": "2026 시즌 중 데이터", "영향": "SSG weakness rule이 갱신될 수 있음", "보완": "주 단위 재빌드"},
        {"한계": "NPB/CPBL 보조 데이터", "영향": "최종 타자·선발투수 후보에는 직접성이 낮음", "보완": "아시아쿼터 별도 모델로 분리"},
    ]

    profile_text = {
        "Luis Matos": """### Luis Matos

**후보 요약.** 우타 외야수, MIL 조직, 비40인 접근성 후보이며 최종 판정은 `CONTACT_1ST`다.

**데이터상 강점.** K% 16.6% 수준의 contact floor, success probability 92.4%, failure probability 8.2%로 historical success model에서 가장 안정적이다. SSG가 필요로 하는 RHP game-script unlocker와 OF/DH rotation stabilizer 조건에도 맞는다.

**모델이 지지한 이유.** Historical Success Model, Market Screen, Contact Floor Screen에서 동시에 살아남았다. Jones보다 raw power는 낮지만, 접촉 안정성과 비용 신호가 좋다.

**리스크.** BB/장타 총량은 model lead급 후보보다 낮다. 중심타선 전체를 혼자 해결하는 선수로 정의하면 과대평가가 된다. 시장 권리와 실제 assignment 조건 확인이 필요하다.

**SSG 내 역할.** RHP game-script unlocker, run-kill avoidance hitter, OF/DH rotation stabilizer.

**한 줄 결론.** Matos는 SSG의 공격 흐름 단절을 줄일 수 있지만, 장타 총량 기대치를 과도하게 잡으면 안 된다.""",
        "Nolan Jones": """### Nolan Jones

**후보 요약.** 좌타 코너 외야수, CLE 조직, raw model 기준 타자 1위이며 최종 판정은 `MODEL_LEAD_CONDITIONAL`이다.

**데이터상 강점.** hard-hit, barrel, 출루와 장타의 결합이 강하다. success probability 90.2%, failure probability 9.2%로 Historical Success Model이 높게 평가했다.

**모델이 지지한 이유.** Historical Success Model, Team Fit Screen, Market Screen, Cross-model Stability가 동시에 지지한다. SSG가 원하는 좌타 코너 OF 파워 보완에 가장 직접적이다.

**리스크.** 2026 현금 신호가 $2.00M로 확인되어 정규 외국인 계약 또는 injury replacement 비용 구조에서 부담이 될 수 있다. K% 28.0% 수준의 swing-and-miss 리스크도 관리해야 한다.

**SSG 내 역할.** middle-order bridge, RHP damage hitter, corner OF/DH power source.

**한 줄 결론.** Jones는 능력 기준 1위지만, 비용 조건이 해결되지 않으면 실행 우선순위는 Matos보다 낮다.""",
        "Jack Suwinski": """### Jack Suwinski

**후보 요약.** 좌타 외야수, LAD 조직, upside 후보이며 최종 판정은 `UPSIDE_HOLD`다.

**데이터상 강점.** BB% 13.5%, barrel 11.8%는 KBO에서 장점으로 번역될 수 있다. 볼넷과 장타가 동시에 있는 유형이어서 SSG의 외야 공격 ceiling을 끌어올릴 수 있다.

**모델이 지지한 이유.** Upside Screen과 Team Fit Screen에서 남았다. 단순 OPS보다 plate discipline + barrel 조합이 강점이다.

**리스크.** success probability 36.3%, failure probability 68.4%로 실패 경고가 크다. K% 31.5%는 SSG의 run-kill avoidance 요구와 충돌할 수 있다.

**SSG 내 역할.** upside power bat, lower-middle-order bridge, selective platoon OF.

**한 줄 결론.** Suwinski는 장타 upside를 제공하지만, 삼진 리스크가 해소되지 않으면 SSG의 숨은 약점을 오히려 키울 수 있다.""",
        "Josh Fleming": """### Josh Fleming

**후보 요약.** 좌완 투수, TOR 조직, 선발/스윙맨 역할 후보이며 최종 판정은 `CONTACT_1ST`다.

**데이터상 강점.** raw ensemble 1위, 낮은 HR9, 관리 가능한 BB9, 좌완성, minor contract 접근성이 결합된다. SSG가 필요로 하는 traffic-command starter 조건에 가장 직접적으로 맞는다.

**모델이 지지한 이유.** Team Need Mining Model, Market Screen, Cross-model Stability, Risk Gate를 함께 통과했다. 투수 모델의 예측확률보다 역할 fit과 실행 가능성이 더 큰 근거다.

**리스크.** K/9 upside는 제한적이어서 KBO에서 압도형 1선발을 기대하면 위험하다. 최근 availability와 실제 선발 빌드업 상태 확인이 필요하다.

**SSG 내 역할.** traffic-command starter, swingman / spot starter, HR/BB damage controller.

**한 줄 결론.** Fleming은 SSG 선발 운영을 안정화할 수 있지만, 에이스형 구위가 아니라 traffic 관리형 투수로 정의해야 한다.""",
        "Bryse Wilson": """### Bryse Wilson

**후보 요약.** 우완 투수, PHI 조직, 선발 이닝 표본이 있는 비교 검증군이며 최종 판정은 `BACKUP_VERIFY`다.

**데이터상 강점.** 2025-2026 MiLB 103이닝, 19선발, K9 8.65, BB9 2.79, HR9 0.96으로 starter floor와 damage control의 기본 조건을 갖춘다.

**모델이 지지한 이유.** Starter Floor Screen, KBO Translation Model, Market Screen에서 살아남았다. raw score는 낮지만 medical gate가 깨끗한 active backup이다.

**리스크.** success probability와 failure probability의 간격이 작다. 단독 Plan A로 보기에는 모델 확신이 낮고, 최근 구위/구종 품질 확인이 필요하다.

**SSG 내 역할.** five-inning floor starter, backup rotation candidate.

**한 줄 결론.** Wilson은 Fleming 이후 비교 검증군으로 적합하지만, 모델 margin이 낮아 단독 결론으로 밀기 어렵다.""",
        "Austin Gomber": """### Austin Gomber

**후보 요약.** 좌완 투수, ATL 조직, 이닝 축적형 후보이며 최종 판정은 `BACKUP_VERIFY`다.

**데이터상 강점.** 172이닝, 37선발 표본은 선발 지속성 측면에서 강하다. 좌완 선발이라는 점도 SSG rotation diversity에 기여할 수 있다.

**모델이 지지한 이유.** Starter Floor Screen과 KBO Translation Model에서 보조 후보로 남았다. 이닝 기반 안정성은 Bryse Wilson보다 긴 표본에서 나온다.

**리스크.** HR9 1.46은 KBO 번역에서 중요한 경고다. 홈런 억제와 최근 구속이 확인되지 않으면 문학 구장과 KBO 장타 환경에서 위험이 커질 수 있다.

**SSG 내 역할.** left-handed starter depth, Plan C starter.

**한 줄 결론.** Gomber는 좌완 이닝 후보지만, 장타 억제 확인 없이는 최종 1순위가 될 수 없다.""",
        "Carson Spiers": """### Carson Spiers

**후보 요약.** 우완 투수, CIN 조직, raw ranking에서는 상위권에 오른 starter floor 후보지만 최종 판정은 `MEDICAL_HOLD`다.

**데이터상 강점.** raw ensemble 2위로 평가될 만큼 선발 역할과 historical diagnostic signal은 존재한다.

**모델이 지지한 이유.** Starter Floor Screen과 Historical Diagnostic Model에서 후보로 남았다. 즉 순수 투수 역할 관점에서는 검토 가치가 있었다.

**리스크.** elbow surgery recovery로 2026년 대부분의 가동성이 불확실하다는 medical signal이 존재한다. 따라서 점수가 높아도 active contact board에 둘 수 없다.

**SSG 내 역할.** medical이 해소될 경우에만 five-inning floor starter 후보로 재검토한다.

**한 줄 결론.** Spiers는 raw score가 높아도 medical hard gate를 넘지 못하면 최종 접촉 대상이 될 수 없다는 반례다.""",
        "Brian Van Belle": """### Brian Van Belle

**후보 요약.** 우완 투수, TB 조직, command floor와 이닝 지속성이 강점인 raw Top 3 후보지만 최종 판정은 `MEDICAL_HOLD`다.

**데이터상 강점.** 낮은 BB9와 선발 이닝 표본은 SSG가 찾는 traffic-command starter 조건과 맞는다.

**모델이 지지한 이유.** Command Stability Screen과 Starter Floor Screen에서 높은 평가를 받았다. 투수 후보군에서 볼넷 억제와 역할 지속성은 분명한 장점이다.

**리스크.** full-season injured list 신호가 있어 2026년 즉시 전력 가능성이 낮다. public medical signal이 해소되지 않는 한 active board에 남길 수 없다.

**SSG 내 역할.** medical clearance 이후에만 depth starter로 재검토한다.

**한 줄 결론.** Van Belle은 좋은 command profile을 갖고 있지만, 현재 정보에서는 실제 등판 가능성이 모델 점수보다 우선한다.""",
    }

    source_rows = []
    for _, r in salary.iterrows():
        source_rows.append(
            {
                "선수": r["candidate"],
                "확인 항목": r["source_note"],
                "출처": r["source_url"],
            }
        )

    final_report = f"""# SSG 랜더스 외국인 선수 영입 전략

## 데이터 마이닝 기반 외국인 타자·선발투수 후보 선정 보고서

## 초록(Abstract)

### 국문

본 보고서는 SSG 랜더스의 외국인 타자 및 외국인 선발투수 영입 문제를 일반적인 데이터마이닝 절차에 맞춰 재구성했다. 분석은 SSG의 보강 문제가 단순한 장타 부족인지, 특정 경기 상황에서의 흐름 단절인지 검증하는 것에서 시작했다. KBO/STATIZ, SSG 상황별 경기 데이터, MLB Savant, MiLB 성적, roster/transaction, public salary/contract, medical status, 기존 output table을 통합해 후보 funnel을 만들고, Team Need Mining Model, Historical KBO Success/Failure Model, Similarity / Archetype Matching Model, KBO Translation Risk Model, Market Feasibility Model, Medical / Failure Gate를 결합했다. 최종 후보는 타자 Luis Matos, Nolan Jones, Jack Suwinski, 투수 Josh Fleming, Bryse Wilson, Austin Gomber다. 최종 접촉 1순위는 타자 Luis Matos, 투수 Josh Fleming이다.

### English

This report reframes SSG Landers' foreign hitter and starting pitcher acquisition problem as a structured data-mining task. The analysis starts by identifying whether SSG's roster need is a generic power shortage or a game-state interaction problem. Using KBO/STATIZ data, SSG situational tables, MLB Savant, MiLB statistics, roster and transaction data, salary/contract signals, medical status, and model outputs, the report builds a candidate funnel and evaluates players through team-need mining, historical KBO success/failure modeling, archetype matching, KBO translation risk, market feasibility, and medical/failure gates. The final hitter board is Luis Matos, Nolan Jones, and Jack Suwinski; the final pitcher board is Josh Fleming, Bryse Wilson, and Austin Gomber. The recommended first contacts are Luis Matos and Josh Fleming.

## Key Takeaways

- SSG의 보강 문제는 단순 장타 부족이 아니라 RHP game-script, 1루 주자 이후 전환, run-kill, extra-out 이후 복구 실패가 결합된 game-state interaction 문제다.
- 후보 선정은 전체 시장에서 시작해 후보 생성 모듈, 데이터마이닝 gate, raw ranking, gate-adjusted ranking으로 좁히는 funnel로 설계했다.
- 타자 최종 후보 3명은 Luis Matos, Nolan Jones, Jack Suwinski다.
- 투수 최종 후보 3명은 Josh Fleming, Bryse Wilson, Austin Gomber다. Carson Spiers와 Brian Van Belle은 raw 상위였지만 medical hold로 보류한다.
- 타자 raw 1위는 Nolan Jones지만, gate-adjusted 최종 접촉 1순위는 Luis Matos다. 투수 최종 접촉 1순위는 Josh Fleming이다.

# 1. 서론

## 1.1 문제 정의

SSG의 외국인 선수 영입 문제는 가장 좋은 누적 성적을 가진 선수를 찾는 문제가 아니다. SSG는 현재 팀의 경기 구조상 반복적으로 발생하는 약점을 완화하고, KBO 환경에서 성과가 번역될 가능성이 있으며, 실제 시장에서 접근 가능한 외국인 타자와 선발투수를 찾아야 한다. 따라서 최종 산출물은 “좋은 선수 순위”가 아니라 “실행 가능한 접촉 우선순위”다.

## 1.2 데이터마이닝 접근의 필요성

단순 OPS, HR, ERA, K/9 순위는 후보의 표면 능력만 보여준다. SSG의 실제 의사결정에는 세 가지 추가 질문이 필요하다. 첫째, 선수가 SSG의 특정 약점을 해결하는가. 둘째, MLB/MiLB 성과가 KBO에서 유지될 수 있는가. 셋째, 계약·의료·시장 접근성까지 고려해 실제 접촉 가능한가. 데이터마이닝 절차는 이 세 질문을 후보 funnel과 gate-adjusted ranking으로 분리한다.

## 1.3 분석 질문

{md_table(rq_rows, ["RQ", "질문", "데이터마이닝 단계", "최종 산출물"])}

## 1.4 최종 의사결정 구조

최종 의사결정은 `Raw Model Ranking`과 `Gate-adjusted Ranking`을 분리한다. Raw ranking은 선수의 데이터상 매력도를 의미하고, gate-adjusted ranking은 계약, 비용, 의료, 시장 접근성, KBO행 가능성을 반영한 실행 순위다.

# 2. 데이터 이해

## 2.1 데이터 소스

{md_table(data_rows, ["데이터 소스", "기간", "단위", "주요 변수", "사용 목적", "한계"])}

## 2.2 분석 단위

타자는 선수-시즌/최근 PA 단위를 기본으로 하고, 역할은 OF/DH 가능성, 좌우타, contact floor, on-base/damage profile로 정의한다. 투수는 선수-시즌/최근 IP/GS 단위를 기본으로 하고, 역할은 선발 지속성, command stability, traffic damage control, KBO/ABS translation으로 정의한다.

## 2.3 주요 변수

타자는 K%, whiff%, wOBA/xwOBA, hard-hit%, barrel%, chase%, OF/DH role, market status를 중심으로 본다. 투수는 IP, GS, K9, BB9, HR9, ERA, WHIP, starter role, injury status, contract status를 중심으로 본다.

## 2.4 데이터 한계와 신뢰도

{md_table(reliability_rows, ["데이터", "형태", "최신성", "누락 가능성", "최종 후보 직접성"])}

## 2.5 leakage 방지 원칙

과거 KBO 외국인 선수의 KBO 입단 후 성적은 label 또는 사후 검증에만 사용한다. 후보 평가 feature에는 KBO 입단 후 성과를 넣지 않는다. 모델은 “KBO에서 이미 성공한 결과”를 맞히는 것이 아니라, “입단 전 정보로 성공 가능성을 추정하는 것”이다.

# 3. 후보군 생성과 변수 설계

## 3.1 전체 후보 시장 정의

후보 시장은 MLB 40인 로스터 경계선, DFA/outright/minor league contract 선수, AAA regular role 선수, 최근 트랜잭션 후보, KBO행 가능성이 있는 나이·계약 상태의 선수로 구성했다. NPB/CPBL 후보는 시장 depth 확인과 아시아쿼터 확장 가능성 검토에 사용했다.

## 3.2 후보 funnel

{md_table(funnel_rows, ["단계", "타자 잔존", "투수 잔존", "판정 의미"])}

## 3.3 타자 feature engineering

{md_table(hitter_feature_rows, ["Feature Group", "주요 변수", "해석"])}

## 3.4 투수 feature engineering

{md_table(pitcher_feature_rows, ["Feature Group", "주요 변수", "해석"])}

## 3.5 SSG 약점의 feature contract 변환

![SSG weakness mining](assets/v2_hidden_weakness_rules.png)

{md_table(contract_rows, ["슬롯", "SSG weakness", "Player feature", "방향", "의사결정 사용", "해석"])}

# 4. 모델링

## 4.1 모델 구성

{md_table(model_rows, ["모델명", "목적", "입력", "출력", "사용 강도"])}

## 4.2 Model A. Team Need Mining Model

이 모델은 선수를 직접 뽑는 모델이 아니라, 후보에게 요구되는 조건을 정의하는 모델이다. SSG의 약점은 OF 홈런 부족보다 RHP game-script lock, run-kill avoidance, extra-out resilience에서 더 구체적으로 드러난다.

## 4.3 Model B. Historical KBO Success/Failure Model

이 모델은 과거 KBO 외국인 선수의 입단 전 데이터를 바탕으로 성공/실패 가능성을 추정한다. 타자 모델은 success/failure probability를 주요 신호로 사용하고, 투수 모델은 diagnostic signal로 제한한다.

## 4.4 Model C. Similarity / Archetype Matching Model

이 모델은 “성적이 좋은 선수”가 아니라 “KBO에서 성공한 유형 또는 SSG가 원하는 역할과 닮은 선수”를 찾는다. 표준화된 feature vector를 기반으로 role similarity와 archetype score를 계산하는 방식이다.

## 4.5 Model D. KBO Translation Risk Model

타자는 과도한 K%, 높은 chase%, 낮은 contact, 변화구/저속 구종 약점, 높은 run-kill risk를 경고한다. 투수는 높은 BB9, HR9, 낮은 GB%, 선발 지속성 부족, ABS 환경에서의 볼넷 증가 가능성을 경고한다.

## 4.6 Model E/F. Market Feasibility와 Medical / Failure Gate

Market Feasibility Model은 40-man, DFA/outright, minor contract, salary signal, option status를 평가한다. Medical / Failure Gate는 점수는 높지만 최종 후보에서 보류해야 하는 선수를 식별한다. 이 gate는 점수 모델이 아니라 hard gate다.

# 5. 앙상블 설계

## 5.1 타자 앙상블

타자는 SSG가 단순 거포보다 이닝을 다시 여는 OF/DH 자원이 필요하다는 전제에서 설계했다. 따라서 Historical Success Model, SSG Fit, KBO Translation, Contact / Run-kill Avoidance, Market Feasibility, Cross-model Stability를 함께 본다.

## 5.2 투수 앙상블

투수는 historical classifier의 안정성이 낮기 때문에 해당 신호를 낮게 반영하고, command stability, starter floor, damage control, market feasibility, medical gate를 더 중요하게 본다.

## 5.3 모델 weight

{md_table(weight_rows, ["슬롯", "모듈", "가중치", "근거"])}

## 5.4 모델 성능 평가

{md_table(perf_rows, ["모델명", "대상", "표본 수", "feature family", "주요 성능", "해석", "사용 강도"])}

## 5.5 Raw Ranking과 Gate-adjusted Ranking

Raw ranking은 순수 모델 점수와 cross-model consistency를 반영한다. Gate-adjusted ranking은 계약, 비용, 의료, 시장 접근성, KBO행 가능성을 반영한다. raw 1위가 최종 1순위가 아닐 수 있으며, 이는 모델 실패가 아니라 영입 실행 가능성 평가가 추가된 결과다.

# 6. 결과

## 6.1 SSG 보강 문제의 데이터마이닝 결과

SSG의 타자 보강 문제는 장타 총량이 아니라 RHP game-script에서 OF/DH가 공격 흐름을 다시 열지 못하는 구조다. 투수 보강 문제는 구위 총량보다 traffic 이후 볼넷과 장타를 억제하고 5이닝 이상을 버티는 선발 안정성이다.

## 6.2 타자 후보 Raw Top 3

{md_table(hitter_raw, ["Raw 순위", "선수", "Raw score", "Success", "Failure", "주요 지지 모듈"])}

## 6.3 타자 후보 Gate-adjusted Top 3

![Hitter gate adjustment](assets/v2_hitter_success_probability.png)

{md_table(gate_rows("foreign_hitter"), ["Gate 순위", "선수", "최종 판단", "Team need fit", "KBO translation", "Risk summary"])}

## 6.4 타자 최종 1인

타자 부문에서 raw model은 Nolan Jones를 가장 높게 평가했다. 그러나 계약 비용, 시장 접근성, KBO행 가능성을 반영한 gate-adjusted ranking에서는 Luis Matos가 최종 접촉 1순위로 올라온다. 이는 raw model의 실패가 아니라, 선수 능력 평가와 영입 실행 가능성 평가를 분리했기 때문에 발생한 합리적 순위 변화다.

{profile_text["Luis Matos"]}

{profile_text["Nolan Jones"]}

{profile_text["Jack Suwinski"]}

## 6.5 투수 후보 Raw Top 3

{md_table(pitcher_raw, ["Raw 순위", "선수", "Raw score", "Success", "Failure", "주요 지지 모듈"])}

## 6.6 투수 후보 Gate-adjusted Top 3

![Pitcher gate adjustment](assets/v2_pitcher_gate_adjustment.png)

{md_table(gate_rows("foreign_pitcher"), ["Gate 순위", "선수", "최종 판단", "Team need fit", "KBO translation", "Risk summary"])}

## 6.7 투수 최종 1인

투수 부문은 타자보다 historical classifier의 예측 안정성이 낮기 때문에 raw score만으로 최종 결론을 내리기 어렵다. 따라서 command, starter floor, medical gate, contract feasibility를 함께 반영했다. 이 과정을 통과한 최종 접촉 1순위는 Josh Fleming이다.

{profile_text["Josh Fleming"]}

{profile_text["Bryse Wilson"]}

{profile_text["Austin Gomber"]}

## 6.8 raw 상위였지만 보류된 투수

{profile_text["Carson Spiers"]}

{profile_text["Brian Van Belle"]}

## 6.9 후보별 차별점 비교

{md_table(comparison_rows, ["슬롯", "선수", "강점", "반대 논리", "최종 판단"])}

## 6.10 모델별 후보 지지/경고 요약

{md_table([
    {"모델": "Team Need Mining Model", "지지 후보": "Matos, Jones, Fleming", "경고 후보": "Suwinski", "이유": "run-kill avoidance와 traffic-command 조건 충족 여부"},
    {"모델": "Historical Success/Failure Model", "지지 후보": "Matos, Jones", "경고 후보": "Suwinski", "이유": "타자 success/failure probability 차이"},
    {"모델": "KBO Translation Risk Model", "지지 후보": "Matos, Wilson", "경고 후보": "Gomber, Suwinski", "이유": "HR9/K% translation risk"},
    {"모델": "Market Feasibility Model", "지지 후보": "Matos, Fleming", "경고 후보": "Jones", "이유": "salary signal과 접근성 차이"},
    {"모델": "Medical / Failure Gate", "지지 후보": "Fleming, Wilson, Gomber", "경고 후보": "Spiers, Van Belle", "이유": "medical hold 여부"},
], ["모델", "지지 후보", "경고 후보", "이유"])}

# 7. 논의

## 7.1 왜 이 후보들이 SSG에 맞는가

타자는 SSG의 RHP game-script와 run-kill avoidance 문제를 해결할 수 있어야 한다. Matos는 contact floor와 비용 접근성, Jones는 raw model strength, Suwinski는 upside를 제공한다. 투수는 traffic-command와 starter floor를 충족해야 한다. Fleming은 역할 fit과 시장 접근성, Wilson과 Gomber는 선발 표본 기반의 비교 검증군이다.

## 7.2 왜 단순 성적 순위와 다른가

단순 성적 순위는 KBO 번역 위험, 계약 접근성, 의료 상태를 반영하지 않는다. 본 보고서는 raw score와 gate-adjusted score를 분리했기 때문에, raw 능력은 높지만 비용 또는 의료 gate에서 내려가는 선수를 설명할 수 있다.

## 7.3 raw score와 final decision의 차이

Nolan Jones는 타자 raw 1위지만 비용 확인 전까지 Matos보다 실행 순위가 낮다. Carson Spiers와 Brian Van Belle은 투수 raw 상위지만 medical hold로 보류된다. 이 차이는 모델 실패가 아니라 deployment 단계의 의사결정이다.

## 7.4 실제 영입 협상에서 확인할 조건

{md_table([
    {"조건": "잔여 보장액과 buyout", "대상": "Jones, Suwinski", "의사결정 영향": "정규 외국인 계약 가능성 또는 injury replacement cap 충족 여부"},
    {"조건": "현재 assignment 권리", "대상": "Matos, Fleming", "의사결정 영향": "즉시 접촉 가능성"},
    {"조건": "최근 medical report", "대상": "Spiers, Van Belle", "의사결정 영향": "active board 복귀 여부"},
    {"조건": "최근 구속/구종 품질", "대상": "Fleming, Wilson, Gomber", "의사결정 영향": "KBO starter floor 확인"},
], ["조건", "대상", "의사결정 영향"])}

## 7.5 Plan A / Plan B / Plan C

{md_table([
    {"슬롯": "타자", "Plan A": "Luis Matos", "Plan B": "Nolan Jones", "Plan C": "Jack Suwinski", "조건": "Jones 비용 조건이 해결되면 Plan A 재검토"},
    {"슬롯": "투수", "Plan A": "Josh Fleming", "Plan B": "Bryse Wilson", "Plan C": "Austin Gomber", "조건": "Fleming 선발 빌드업이 부족하면 Wilson/Gomber 비교"},
], ["슬롯", "Plan A", "Plan B", "Plan C", "조건"])}

# 8. 한계

{md_table(limit_rows, ["한계", "영향", "보완"])}

## 8.1 투수 classifier를 diagnostic signal로만 쓰는 이유

투수 historical classifier의 안정성이 낮은 가장 큰 이유는 표본 수와 label noise다. 현재 투수 학습 표본은 49명 수준이며, KBO 입단 후 투수 성과는 타자보다 주변 환경의 영향을 더 크게 받는다. 예를 들어 ERA와 이닝은 투수 본인의 구위뿐 아니라 수비력, 포수 리드, 불펜 승계주자 처리, 구장, 등판 간격, 시즌 중 역할 변경의 영향을 받는다. 따라서 같은 입단 전 BB9/HR9를 가진 투수라도 KBO에서 받은 역할과 팀 환경에 따라 label이 달라질 수 있다.

두 번째 이유는 역할 이질성이다. 외국인 투수 표본 안에는 확정 선발, 스윙맨, 대체 선발, 불펜 전환 후보가 섞여 있다. 이들은 모두 “투수”로 묶이지만 성공 기준은 다르다. 선발투수에게 중요한 starter floor와 third-time-through-order risk는 불펜 후보에게는 같은 의미가 아니다. 이 때문에 투수 classifier는 최종 추천 모델이 아니라 후보의 위험 신호를 읽는 진단 모델로 제한한다.

세 번째 이유는 pitch-quality 결측이다. KBO 번역에서 중요한 구속 추세, pitch shape, release consistency, zone command, ABS 환경에서의 called-strike dependency는 공개 집계 성적만으로 완전히 설명되지 않는다. 그래서 투수 최종 판단은 model probability보다 BB9, HR9, 최근 선발 이닝, medical gate, 계약 접근성, 최근 구속/구종 확인을 함께 보는 gate-adjusted 방식으로 처리한다.

# 9. 결론

## 9.1 분석 질문별 요약 답변

{md_table([
    {"RQ": "RQ1", "요약 답변": "SSG의 약점은 단순 장타 부족이 아니라 game-state interaction 문제다."},
    {"RQ": "RQ2", "요약 답변": "타자는 이닝 전환형 OF/DH, 투수는 traffic-command starter가 필요하다."},
    {"RQ": "RQ3", "요약 답변": "후보는 전체 시장 → 후보 생성 모듈 → 데이터마이닝 gate → raw Top 3 → gate-adjusted Top 3로 축소했다."},
    {"RQ": "RQ4", "요약 답변": "각 모델은 팀 필요, historical success, archetype similarity, KBO translation, market, medical gate를 분담한다."},
    {"RQ": "RQ5", "요약 답변": "타자 Top 3는 Matos/Jones/Suwinski, 투수 Top 3는 Fleming/Wilson/Gomber다."},
    {"RQ": "RQ6", "요약 답변": "최종 접촉 1순위는 Luis Matos와 Josh Fleming이다."},
], ["RQ", "요약 답변"])}

## 9.2 최종 의사결정표

{md_table(decision_rows, ["슬롯", "Raw model 1위", "Gate-adjusted 1위", "최종 후보 3명", "최종 접촉 1순위", "순위 변동 이유"])}

## 9.3 핵심 한 줄

본 보고서의 결론은 Luis Matos와 Josh Fleming이 단순히 가장 좋은 성적의 선수가 아니라, SSG의 약점 구조, KBO 번역 가능성, 시장 접근성, 비용·의료 gate를 함께 통과한 가장 실행 가능한 접촉 우선순위라는 점이다.

# Appendix

## A. 후보 funnel 상세

{md_table(funnel_rows, ["단계", "타자 잔존", "투수 잔존", "판정 의미"])}

## B. 변수 정의

{md_table(hitter_feature_rows + pitcher_feature_rows, ["Feature Group", "주요 변수", "해석"])}

## C. 모델 weight

{md_table(weight_rows, ["슬롯", "모듈", "가중치", "근거"])}

## D. gate 기준

{md_table([
    {"Gate": "PASS", "정의": "시장·의료·역할 리스크가 관리 가능한 상태", "처리": "final board 유지"},
    {"Gate": "YELLOW", "정의": "추가 확인 필요하지만 접촉 가능", "처리": "conditional ranking"},
    {"Gate": "HOLD", "정의": "현재 정보로는 active contact 부적합", "처리": "watch 또는 medical hold"},
    {"Gate": "RED", "정의": "계약·의료·역할 리스크가 hard block", "처리": "최종 board 제외"},
], ["Gate", "정의", "처리"])}

## E. Source Notes

{md_table(source_rows, ["선수", "확인 항목", "출처"])}

## F. 재현성 체크리스트

```bash
python3 scripts/build_crispdm_leaf_report_v2.py
```

생성 산출물은 `reports/leaf_node/final_report.md`, `reports/leaf_node/executive_summary.md`, `reports/leaf_node/method_appendix.md`, `reports/leaf_node/index.html`, `outputs/tables/final_candidate_board.csv`다.
"""

    executive = f"""# SSG 랜더스 외국인 선수 영입 전략 Executive Summary

## 결론

최종 접촉 1순위는 외국인 타자 **Luis Matos**, 외국인 선발투수 **Josh Fleming**이다. 타자 raw model은 Nolan Jones를 가장 높게 평가했지만, 계약 비용과 실행 가능성을 반영한 gate-adjusted ranking에서는 Matos가 1순위로 올라온다. 투수는 raw Top 3 중 Carson Spiers와 Brian Van Belle이 medical hold로 내려가면서 Fleming, Bryse Wilson, Austin Gomber가 active board로 남는다.

## 핵심 논리

- SSG의 문제는 장타 총량 부족이 아니라 RHP game-script, run-kill, extra-out 이후 복구 실패로 나타나는 game-state interaction 문제다.
- 타자는 이닝을 다시 여는 OF/DH 자원, 투수는 traffic 상황에서 BB/HR damage를 억제하고 5이닝 이상 버티는 선발 자원이 필요하다.
- 최종 순위는 raw score가 아니라 Team Need Fit, KBO Translation, Market Feasibility, Medical / Failure Gate를 통과한 실행 순위다.

## 최종 후보

{md_table(decision_rows, ["슬롯", "Raw model 1위", "Gate-adjusted 1위", "최종 후보 3명", "최종 접촉 1순위", "순위 변동 이유"])}

## 주요 리스크

{md_table([
    {"대상": "Luis Matos", "리스크": "장타 총량은 Jones보다 낮음", "확인": "실제 assignment 권리와 최근 role"},
    {"대상": "Nolan Jones", "리스크": "2026 현금 신호가 큼", "확인": "잔여 부담액, buyout, cost-share"},
    {"대상": "Jack Suwinski", "리스크": "K%와 failure probability가 높음", "확인": "KBO contact translation"},
    {"대상": "Josh Fleming", "리스크": "K/9 upside 제한", "확인": "최근 구속과 선발 빌드업"},
    {"대상": "Bryse Wilson", "리스크": "모델 margin 낮음", "확인": "구종 품질과 starter floor"},
    {"대상": "Austin Gomber", "리스크": "HR9 경고", "확인": "장타 억제 가능성"},
], ["대상", "리스크", "확인"])}
"""

    method = f"""# Method Appendix

## 데이터마이닝 절차

본 프로젝트는 Business Understanding, Data Understanding, Data Preparation, Modeling, Evaluation, Ensemble Decision, Deployment 순서로 구성했다. 최종 의사결정은 raw ranking과 gate-adjusted ranking을 분리한다.

## Candidate Funnel

{md_table(funnel_rows, ["단계", "타자 잔존", "투수 잔존", "판정 의미"])}

## Feature Engineering

### Hitter Feature Groups

{md_table(hitter_feature_rows, ["Feature Group", "주요 변수", "해석"])}

### Pitcher Feature Groups

{md_table(pitcher_feature_rows, ["Feature Group", "주요 변수", "해석"])}

## 모델 구성

{md_table(model_rows, ["모델명", "목적", "입력", "출력", "사용 강도"])}

## 모델 성능과 사용 강도

{md_table(perf_rows, ["모델명", "대상", "표본 수", "feature family", "주요 성능", "해석", "사용 강도"])}

## Weight 근거

{md_table(weight_rows, ["슬롯", "모듈", "가중치", "근거"])}

## Gate 기준

{md_table([
    {"Gate": "PASS", "정의": "시장·의료·역할 리스크가 관리 가능한 상태", "처리": "final board 유지"},
    {"Gate": "YELLOW", "정의": "추가 확인 필요하지만 접촉 가능", "처리": "conditional ranking"},
    {"Gate": "HOLD", "정의": "현재 정보로는 active contact 부적합", "처리": "watch 또는 medical hold"},
    {"Gate": "RED", "정의": "계약·의료·역할 리스크가 hard block", "처리": "최종 board 제외"},
], ["Gate", "정의", "처리"])}

## Leakage 방지

과거 KBO 외국인 선수의 KBO 입단 후 성적은 label 또는 사후 검증에만 사용한다. 후보 평가 feature에는 KBO 입단 후 성과를 넣지 않는다. 모델은 입단 전 정보로 성공 가능성을 추정한다.

## 한계

{md_table(limit_rows, ["한계", "영향", "보완"])}
"""

    return {
        "final_report.md": final_report,
        "executive_summary.md": executive,
        "method_appendix.md": method,
    }


def markdown_to_html(markdown_text: str) -> str:
    def inline(text: str) -> str:
        escaped = html.escape(text)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        return escaped

    def parse_table(block: list[str]) -> str:
        rows = []
        for line in block:
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
        headers = rows[0]
        body = rows[2:] if len(rows) >= 2 else []
        parts = ["<table><thead><tr>"]
        parts.extend(f"<th>{inline(cell)}</th>" for cell in headers)
        parts.append("</tr></thead><tbody>")
        for row in body:
            parts.append("<tr>")
            parts.extend(f"<td>{inline(cell)}</td>" for cell in row)
            parts.append("</tr>")
        parts.append("</tbody></table>")
        return "\n".join(parts)

    lines: list[str] = []
    raw = markdown_text.splitlines()
    in_code = False
    code_buf: list[str] = []
    i = 0
    while i < len(raw):
        line = raw[i]
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
        if line.startswith("|") and i + 1 < len(raw) and raw[i + 1].startswith("|"):
            block = []
            while i < len(raw) and raw[i].startswith("|"):
                block.append(raw[i])
                i += 1
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
            items = []
            while i < len(raw) and raw[i].startswith("- "):
                items.append(f"<li>{inline(raw[i][2:])}</li>")
                i += 1
            lines.append("<ul>" + "\n".join(items) + "</ul>")
            continue
        elif line.strip() == "":
            pass
        else:
            lines.append(f"<p>{inline(line)}</p>")
        i += 1
    return "\n".join(lines)


def build_html(markdown_text: str) -> str:
    body = markdown_to_html(markdown_text)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>SSG 랜더스 외국인 선수 영입 전략</title>
  <style>
    :root {{ --ink:#20242d; --muted:#687084; --line:#dfe3ec; --panel:#fff; --wash:#f6f7fa; --accent:#b5121b; }}
    body {{ margin:0; background:var(--wash); color:var(--ink); font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR","Segoe UI",sans-serif; line-height:1.68; }}
    main {{ width:min(1120px, calc(100vw - 40px)); margin:44px auto 72px; background:var(--panel); border:1px solid var(--line); box-shadow:0 18px 48px rgba(28,34,45,.08); padding:56px 64px; }}
    h1 {{ font-size:clamp(30px,4vw,48px); line-height:1.12; margin:0 0 28px; padding-bottom:20px; border-bottom:4px solid var(--accent); letter-spacing:0; }}
    h2 {{ font-size:26px; margin:44px 0 16px; padding-top:18px; border-top:1px solid var(--line); }}
    h3 {{ font-size:20px; margin:30px 0 12px; }}
    p, li {{ font-size:16px; }}
    strong {{ color:var(--accent); }}
    img {{ max-width:100%; display:block; margin:22px 0 26px; border:1px solid var(--line); background:#fff; }}
    table {{ width:100%; border-collapse:collapse; margin:18px 0 28px; font-size:14px; }}
    th {{ background:#15171d; color:#fff; text-align:left; font-weight:700; }}
    td, th {{ border:1px solid var(--line); padding:9px 10px; vertical-align:top; }}
    tr:nth-child(even) td {{ background:#fafbfe; }}
    code, pre {{ font-family:"SF Mono",Menlo,Consolas,monospace; background:#f1f3f7; border-radius:6px; }}
    code {{ padding:2px 5px; }}
    pre {{ padding:14px; overflow-x:auto; }}
    @media (max-width:760px) {{ main {{ width:auto; margin:0; padding:28px 18px; border:0; box-shadow:none; }} table {{ display:block; overflow-x:auto; white-space:nowrap; }} }}
  </style>
</head>
<body><main>{body}</main></body></html>
"""


def assert_clean(paths: list[Path]) -> None:
    pattern = re.compile("|".join(BANNED_PATTERNS), flags=re.IGNORECASE)
    bad: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                bad.append(f"{path}:{idx}:{line[:160]}")
    if bad:
        raise RuntimeError("Forbidden wording detected:\n" + "\n".join(bad[:40]))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    board = build_final_board()
    build_charts(board)
    reports = make_reports(board)
    written: list[Path] = []
    for name, content in reports.items():
        path = OUT_DIR / name
        path.write_text(content, encoding="utf-8")
        written.append(path)
    html_path = OUT_DIR / "index.html"
    html_path.write_text(build_html(reports["final_report.md"]), encoding="utf-8")
    written.append(html_path)
    written.append(TABLE_DIR / "final_candidate_board.csv")
    assert_clean(written)
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
