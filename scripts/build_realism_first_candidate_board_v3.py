from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables" / "final_candidate_board_execution_v4.csv"
LEGACY_OUT = ROOT / "outputs" / "tables" / "final_candidate_board_realism_v3.csv"
DOC = ROOT / "docs" / "candidate_board_execution_v4.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def by_name(rows: list[dict[str, str]], name_key: str = "player_name") -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        name = (row.get(name_key) or "").strip().lower()
        if name and name not in out:
            out[name] = row
        if "," in name:
            last, first = [part.strip() for part in name.split(",", 1)]
            flipped = f"{first} {last}".strip()
            if flipped and flipped not in out:
                out[flipped] = row
    return out


def latest_transactions(rows: list[dict[str, str]]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in rows:
        name = (row.get("player_name") or "").strip().lower()
        desc = row.get("description") or ""
        date = row.get("effective_date") or ""
        if name:
            out.setdefault(name, []).append(f"{date}: {desc}")
    return out


def pct(x: str) -> str:
    if not x:
        return ""
    return f"{float(x) * 100:.1f}%"


def support_tier(x: str) -> str:
    if not x:
        return ""
    value = float(x)
    if value >= 0.85:
        return "강함"
    if value >= 0.70:
        return "중상"
    if value >= 0.55:
        return "중"
    return "약함"


def warning_tier(x: str) -> str:
    if not x:
        return ""
    value = float(x)
    if value <= 0.20:
        return "낮음"
    if value <= 0.45:
        return "보통"
    return "높음"


def margin_direction(x: str) -> str:
    if not x:
        return ""
    value = float(x)
    if value >= 0.30:
        return "긍정"
    if value >= 0:
        return "보통"
    return "경고"


def one(rows_by_name: dict[str, dict[str, str]], name: str) -> dict[str, str]:
    return rows_by_name.get(name.lower(), {})


def main() -> None:
    hitter_dm = by_name(read_csv(ROOT / "outputs" / "tables" / "data_mining_hitter_candidates_v1.csv"))
    pitcher_dm = by_name(read_csv(ROOT / "outputs" / "tables" / "data_mining_pitcher_candidates_v1.csv"))
    unified = by_name(read_csv(ROOT / "outputs" / "tables" / "unified_foreign_recommendation_pool_structured_only_v2.csv"))
    market = by_name(read_csv(ROOT / "outputs" / "tables" / "ssg_market_realism_layer_v0_2.csv"))
    tx = latest_transactions(read_csv(ROOT / "outputs" / "tables" / "mlb_transactions_latest.csv"))

    rows: list[dict[str, str]] = []

    hitter_board = [
        (
            "Will Brennan",
            1,
            "CONTACT_1ST",
            "DFA/outright 후 40-man 밖, age 28, OF, 시장 접근성 최상위",
            "SSG가 찾는 contact-floor OF. 접촉형 프로필과 6/17 outright 신호가 결합됨.",
            "medical history watch는 확인 필요하지만, Matos보다 KBO행 현실성이 높음.",
        ),
        (
            "Dominic Fletcher",
            2,
            "CONTACT_2ND",
            "age 28, non-40man, minor-league contract, OF",
            "독립 후보 신호와 구조화 모델이 교차하는 현실형 외야수.",
            "장타 ceiling은 낮아 중심타선 해결사보다 run-kill avoidance/OF 안정화 역할.",
        ),
        (
            "Dylan Carlson",
            3,
            "CONTACT_3RD",
            "age 27, DFA/outright 이력, non-40man signal, switch-hitting OF",
            "Matos보다 나이/커리어 단계가 KBO 전환에 가깝고, 모델 Top 3도 통과.",
            "최근 소속권과 opt-out/release 조건 확인 필요.",
        ),
        (
            "Luis Matos",
            "HOLD",
            "DISCOVERY_HOLD",
            "초기 discovery 모델 리드였지만 age 24, 현 소속권과 MLB 재도전 가치가 큼",
            "데이터마이닝 발견 후보로 보존.",
            "현실성 반영 게이트에서는 active Top 3가 아니라 hold.",
        ),
        (
            "Nolan Jones",
            "HOLD",
            "POWER_DISCOVERY_COST_HOLD",
            "power/OBP discovery 신호가 강하지만 6/11 cash trade와 2.0M salary signal",
            "비용/권리 조건이 풀리면 재상승 가능.",
            "대체 외국인 월봉 구조에는 과하게 비쌀 위험.",
        ),
        (
            "Jack Suwinski",
            "WATCH",
            "UPSIDE_WATCHLIST",
            "BB/barrel upside와 반복 후보 신호",
            "좌타 장타 watchlist.",
            "실패 경고 신호와 K%가 SSG run-kill avoidance 조건과 충돌.",
        ),
    ]

    pitcher_board = [
        (
            "Josh Fleming",
            1,
            "CONTACT_1ST",
            "age 30, non-40man, minor contract, current AAA starter load",
            "53.0 IP/10 GS, BB/9 1.36, HR/9 0.51로 SSG traffic-command 조건에 가장 근접.",
            "에이스형 구위가 아니라 안정화형 선발/스윙맨으로 정의해야 함.",
        ),
        (
            "Keegan Thompson",
            2,
            "CONTACT_2ND",
            "age 31, recent DFA/outright high-access, current AAA starter load",
            "시장 접근성 신호가 강함. HR/9 0.56으로 damage-control 측면이 좋음.",
            "K/9 5.29라 swing-and-miss ceiling은 낮음.",
        ),
        (
            "Kolby Allard",
            3,
            "CONTACT_3RD",
            "age 28, left-handed, repeated DFA/outright/minor deal, non-40man",
            "좌완, HR/9 0.36, 선발 표본 존재. Fleming 실패 시 같은 좌완 계열 대안.",
            "BB/9 3.20과 최근 소속권 확인 필요.",
        ),
        (
            "Bruce Zimmermann",
            "WATCH",
            "K_UPSIDE_WATCH",
            "age 31, non-40man LHP, 67.2 IP/13 GS",
            "K/9 9.98, BB/9 2.26으로 선발 표본은 좋음.",
            "HR/9 1.86이 KBO 장타 억제 조건과 충돌해 active Top 3 밖.",
        ),
        (
            "Bryse Wilson",
            "HOLD",
            "CONTRACT_BLOCKER_HOLD",
            "6/18 Phillies selected contract, current 40-man/MLB access blocker",
            "선발 경력은 있지만 당장 빼오기 어렵다.",
            "현실성 gate에서 hold.",
        ),
        (
            "Randy Dobnak",
            "HOLD",
            "RECENT_CASH_TRADE_HOLD",
            "6/17 cash trade to Kansas City, 40-man signal",
            "반복 후보 신호로 유지.",
            "새 구단이 방금 현금으로 데려온 직후라 release 가능성이 낮음.",
        ),
    ]

    def add(slot: str, item: tuple[str, object, str, str, str, str]) -> None:
        name, rank, decision, market_reason, model_reason, risk = item
        dm = one(hitter_dm if slot == "foreign_hitter" else pitcher_dm, name)
        uni = one(unified, name)
        mkt = one(market, name)
        rows.append(
            {
                "slot": slot,
                "player": name,
                "decision_rank": str(rank),
                "decision": decision,
                "age": dm.get("age") or uni.get("age") or mkt.get("age"),
                "position_or_role": dm.get("primary_position") or uni.get("primary_position") or mkt.get("position_or_role"),
                "hand_or_bat": dm.get("bat_side") or dm.get("pitch_hand") or uni.get("bat_side") or uni.get("pitch_hand"),
                "is_40man": mkt.get("current_is_40man") or dm.get("is_40man"),
                "model_support_tier": support_tier(dm.get("dm_success_prob", "")),
                "failure_warning_tier": warning_tier(dm.get("dm_failure_prob", "")),
                "model_margin_direction": margin_direction(dm.get("dm_margin", "")),
                "unified_fit_score": uni.get("unified_fit_score", ""),
                "market_feasibility_score": mkt.get("market_realism_score", ""),
                "market_status": mkt.get("market_realism_status", ""),
                "contract_bucket": mkt.get("contract_control_bucket", ""),
                "latest_transactions": " | ".join(tx.get(name.lower(), [])[-4:]),
                "market_reason": market_reason,
                "model_reason": model_reason,
                "risk_summary": risk,
            }
        )

    for item in hitter_board:
        add("foreign_hitter", item)
    for item in pitcher_board:
        add("foreign_pitcher", item)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with LEGACY_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text(
        "\n".join(
            [
                "# Candidate Board Execution v4",
                "",
                "## 핵심 수정",
                "",
                "기존 보드는 data-mining score가 높은 젊은 MLB-depth 후보를 너무 적극적으로 올렸다. v4에서는 실제 KBO 영입 가능성을 후보 축소 단계에 포함한다.",
                "",
                "## 현실성 반영 게이트",
                "",
                "- 40-man 또는 방금 claimed/selected/traded된 선수는 active Top 3에서 제외한다.",
                "- age 25 이하의 MLB 재도전 가치가 큰 선수는 discovery 단계에서 좋아 보여도 hold로 둔다.",
                "- 외국인 타자는 OF/DH 역할을 우선하고, 1B/3B 전용 후보는 role hold로 둔다.",
                "- 실패 경고 신호가 높거나 K%/run-kill risk가 큰 후보는 watchlist로 둔다.",
                "- 최종 active board는 모델 지지 신호, 시장 접근성, 역할 적합성을 함께 통과한 후보 안에서 고른다.",
                "",
                "## 재구성 결론",
                "",
                "- 외국인 타자 현실형 Top 3: Will Brennan, Dominic Fletcher, Dylan Carlson",
                "- Luis Matos: 초기 discovery 리드였지만 age 24와 MLB 재도전 가치 때문에 접촉 보류",
                "- Nolan Jones: power/OBP discovery 신호는 강하지만 cash trade와 salary signal 때문에 cost/rights hold",
                "- 외국인 투수 현실형 Top 3: Josh Fleming, Keegan Thompson, Kolby Allard",
                "- Bryse Wilson: 6/18 selected contract 이후 contract blocker hold",
                "",
                "## 발표용 한 줄",
                "",
                "최종 모델은 '가장 점수가 높은 선수'가 아니라 'KBO로 실제 데려올 수 있는 선수 중 SSG 약점에 가장 잘 맞는 선수'를 고르는 현실성 반영 통합 모델로 수정했다.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Wrote {OUT}")
    print(f"Wrote {LEGACY_OUT}")
    print(f"Wrote {DOC}")


if __name__ == "__main__":
    main()
