from __future__ import annotations

import math
import textwrap
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "ppt_tables_png_ssg_style"
ZIP_OUT = ROOT / "outputs" / "ppt_tables_png_ssg_style.zip"

FONT_PATHS = [
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf"),
]
FONT_PATH = next((p for p in FONT_PATHS if p.exists()), FONT_PATHS[-1])

W, H = 1920, 1080
MARGIN_X = 110
TITLE_Y = 72
SUBTITLE_Y = 188
TABLE_Y = 300
SOURCE_Y = 1020

BG = (247, 248, 246)
SSG_RED = (140, 14, 26)
SSG_RED_BRIGHT = (201, 21, 43)
SSG_BLUE = (36, 92, 115)
DARK = (38, 35, 33)
MID = (128, 128, 123)
GRID = (218, 219, 214)
HEADER_BG = (236, 237, 234)
ROW_ALT = (255, 255, 255)
SOFT_RED = (253, 246, 247)
SOFT_BLUE = (242, 246, 247)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    index = 6 if bold else 0
    return ImageFont.truetype(str(FONT_PATH), size=size, index=index)


F_TITLE = font(58, bold=True)
F_SUB = font(28)
F_HEADER = font(25, bold=True)
F_CELL = font(23)
F_SMALL = font(19)
F_SOURCE = font(17)
F_BIG = font(38, bold=True)


def fmt_pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


def fmt_signed(x: float, digits: int = 1) -> str:
    return f"{x:+.{digits}f}"


def wrap_text(text: object, width: int) -> str:
    raw = "" if pd.isna(text) else str(text)
    if len(raw) <= width:
        return raw
    chunks = []
    for line in raw.split("\n"):
        chunks.extend(textwrap.wrap(line, width=width, break_long_words=False, replace_whitespace=False) or [""])
    return "\n".join(chunks)


def text_height(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, spacing: int = 6) -> int:
    if not text:
        return 0
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing)
    return bbox[3] - bbox[1]


def draw_title(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.text((MARGIN_X, TITLE_Y), title, fill=DARK, font=F_TITLE)
    draw.rectangle((MARGIN_X, TITLE_Y + 82, MARGIN_X + 235, TITLE_Y + 90), fill=SSG_RED_BRIGHT)
    if subtitle:
        draw.text((MARGIN_X, SUBTITLE_Y), subtitle, fill=MID, font=F_SUB)


def draw_source(draw: ImageDraw.ImageDraw, source: str) -> None:
    draw.text((MARGIN_X, SOURCE_Y), f"Source: {source}", fill=(125, 125, 120), font=F_SOURCE)


def render_table(
    filename: str,
    title: str,
    subtitle: str,
    rows: list[list[object]],
    columns: list[str],
    widths: list[float],
    source: str = "project output tables, KBO/STATIZ 2023-2026, MLB/MiLB 2023-2026",
    highlight_cols: set[int] | None = None,
    footer: str | None = None,
    accent: tuple[int, int, int] | None = None,
) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_title(draw, title, subtitle)
    accent = accent or SSG_RED

    left = MARGIN_X
    right = W - MARGIN_X
    table_w = right - left
    col_px = [int(table_w * x) for x in widths]
    col_px[-1] = table_w - sum(col_px[:-1])
    x_positions = [left]
    for w in col_px[:-1]:
        x_positions.append(x_positions[-1] + w)

    wrapped_rows: list[list[str]] = []
    wrap_widths = [max(7, int(w / 17)) for w in col_px]
    for row in rows:
        wrapped_rows.append([wrap_text(cell, wrap_widths[i]) for i, cell in enumerate(row)])

    header_h = 76
    row_heights = []
    for row in wrapped_rows:
        row_h = max(text_height(draw, cell, F_CELL) for cell in row) + 40
        row_heights.append(max(80, row_h))
    total_h = header_h + sum(row_heights)
    max_h = SOURCE_Y - TABLE_Y - (84 if footer else 24)
    scale = min(1.0, max_h / total_h)
    cell_font = F_CELL if scale >= 0.92 else font(max(18, int(24 * scale)))
    header_font = F_HEADER if scale >= 0.92 else font(max(19, int(26 * scale)))
    if scale < 1.0:
        header_h = int(header_h * scale)
        row_heights = [int(h * scale) for h in row_heights]

    y = TABLE_Y
    draw.rectangle((left, y, right, y + header_h), fill=HEADER_BG)
    for i, col in enumerate(columns):
        x = x_positions[i]
        bbox = draw.textbbox((0, 0), col, font=header_font)
        tx = x + (col_px[i] - (bbox[2] - bbox[0])) / 2
        ty = y + (header_h - (bbox[3] - bbox[1])) / 2 - 3
        draw.text((tx, ty), col, fill=DARK, font=header_font)
    y += header_h
    draw.line((left, y, right, y), fill=GRID, width=2)

    highlight_cols = highlight_cols or set()
    for r_idx, row in enumerate(wrapped_rows):
        rh = row_heights[r_idx]
        bg = ROW_ALT
        draw.rectangle((left, y, right, y + rh), fill=bg)
        for i, cell in enumerate(row):
            x = x_positions[i]
            col_bg = None
            if i in highlight_cols:
                col_bg = SOFT_RED if accent == SSG_RED else SOFT_BLUE
            if col_bg:
                draw.rectangle((x, y, x + col_px[i], y + rh), fill=col_bg)
            lines = cell.split("\n")
            is_long_text = any(len(line) > 18 for line in lines)
            if is_long_text:
                tx = x + 22
                anchor = "la"
            else:
                tx = x + col_px[i] / 2
                anchor = "ma"
            th = text_height(draw, cell, cell_font, spacing=5)
            ty = y + (rh - th) / 2
            draw.multiline_text((tx, ty), cell, fill=DARK, font=cell_font, spacing=5, align="center" if not is_long_text else "left", anchor=anchor)
            if i > 0:
                draw.line((x, y, x, y + rh), fill=GRID, width=1)
        draw.line((left, y + rh, right, y + rh), fill=GRID, width=1)
        y += rh

    draw.line((left, TABLE_Y, left, y), fill=GRID, width=1)
    draw.line((right, TABLE_Y, right, y), fill=GRID, width=1)
    draw.line((left, y, right, y), fill=GRID, width=1)

    if footer:
        fy = min(y + 70, SOURCE_Y - 82)
        draw.rounded_rectangle((left + 170, fy, right - 170, fy + 74), radius=10, outline=accent, width=2, fill=BG)
        footer_font = font(28, bold=True)
        bbox = draw.textbbox((0, 0), footer, font=footer_font)
        draw.text(((W - (bbox[2] - bbox[0])) / 2, fy + 20), footer, fill=accent, font=footer_font)

    draw_source(draw, source)
    path = OUT_DIR / filename
    img.save(path, quality=95)
    return path


def table_hidden_weakness() -> Path:
    df = pd.read_csv(ROOT / "outputs/tables/ssg_hidden_weakness_robustness_decisions_v3.csv")
    label = {
        "R1_rhp_low_of_conversion_run_trade": "우투 선발 상대 OF/DH 저전환",
        "R2_rhp_ofdh_run_kill": "run-kill 타석 집중",
        "R3_extra_out_high_of_void": "추가 아웃 이후 외야 공백",
        "R4_top_opponent_short_start_of_void": "강팀/짧은 선발 경기 보조 신호",
    }
    rows = []
    for _, r in df.iterrows():
        rows.append([
            label.get(r["rule_id"], r["rule_id"]),
            f"{int(r['games'])}G",
            fmt_pct(r["win_pct"]),
            f"{r['avg_run_diff']:.2f}",
            "핵심" if r["decision"] == "promote_core" else "보조",
            "공격 흐름 또는 경기 회복 경로가 사라지는 상황",
        ])
    return render_table(
        "01_ssg_hidden_weakness_objective_metrics.png",
        "SSG 약점을 객관 지표로 본 표",
        "약점은 단순 장타 부족이 아니라 특정 경기 상태에서 승률과 득실이 동시에 무너지는 구조입니다.",
        rows,
        ["약점 신호", "경기", "승률", "평균 득실", "판정", "발표 해석"],
        [0.26, 0.08, 0.10, 0.12, 0.10, 0.34],
        highlight_cols={2, 3},
        footer="한 줄: SSG는 특정 조건에서 공격 회복 경로가 사라질 때 경기 전체가 무너진다.",
    )


def table_outfield_gap() -> Path:
    df = pd.read_csv(ROOT / "outputs/tables/ssg_outfield_gap_summary.csv")
    rows = []
    for _, r in df.iterrows():
        rows.append([
            int(r["year"]),
            f"{int(r['of_hr'])}개 / {int(r['of_hr_rank'])}위",
            f"{r['of_ops']:.3f} / {int(r['of_ops_rank'])}위",
            f"{r['of_wrc_plus_pa_weighted']:.1f} / {int(r['of_wrc_plus_rank'])}위",
            f"{r['of_ops_vs_lg_avg']:+.3f}",
            "홈런은 많지만 안정적 생산성으로 완전히 번역되지 않음",
        ])
    return render_table(
        "02_outfield_power_vs_production_gap.png",
        "외야는 장타가 없던 팀이 아니다",
        "문제는 홈런 수 자체보다 장타가 안정적 득점 생산성으로 번역되는 정도입니다.",
        rows,
        ["연도", "외야 HR", "외야 OPS", "외야 wRC+", "OPS 리그 대비", "해석"],
        [0.09, 0.15, 0.15, 0.16, 0.14, 0.31],
        highlight_cols={1, 3},
        footer="한 줄: 그래서 단순 거포보다 contact-floor OF가 더 설득력 있는 보강 방향이다.",
    )


def table_pitching_impact() -> Path:
    df = pd.read_csv(ROOT / "outputs/tables/ssg_pitching_message_v0_2_game_impact.csv")
    names = {
        "starter_5ip_plus": "선발 5이닝 이상",
        "starter_short_lt5": "선발 5이닝 미만",
        "starter_er_4plus": "선발 4자책 이상",
        "starter_disaster": "선발 disaster start",
        "starter_quality_6ip_3er": "6이닝 3자책 이하",
    }
    order = ["starter_5ip_plus", "starter_short_lt5", "starter_er_4plus", "starter_disaster", "starter_quality_6ip_3er"]
    rows = []
    for sig in order:
        r = df[df["signal"].eq(sig)].iloc[0]
        rows.append([
            names[sig],
            f"{int(r['signal_games'])}G",
            fmt_pct(r["signal_win_rate"]),
            fmt_pct(r["non_signal_win_rate"]),
            f"{r['win_rate_delta_signal_minus_non']*100:+.1f}%p",
            f"{r['signal_avg_margin']:+.2f}",
            "선발 안정성이 승패와 직결",
        ])
    return render_table(
        "03_starting_pitcher_game_impact.png",
        "선발 안정성은 승패와 직접 연결된다",
        "SSG 투수 보강은 탈삼진 총량보다 5이닝 유지와 traffic 이후 피해 억제가 핵심입니다.",
        rows,
        ["상황", "경기", "해당 승률", "비해당 승률", "승률 차이", "평균 득실", "해석"],
        [0.21, 0.08, 0.13, 0.13, 0.13, 0.12, 0.20],
        highlight_cols={2, 4, 5},
        footer="한 줄: SSG에는 압도형보다 무너지지 않는 traffic-command starter가 필요하다.",
        accent=SSG_BLUE,
    )


def table_candidate_funnel() -> Path:
    rows = [
        ["1", "전체 구조화 시장", "736", "1,009", "MLB/MiLB/roster 기반 입력 후보 pool"],
        ["2", "후보 생성 모듈", "16", "18", "Market, Team Fit, Upside screen 통과"],
        ["3", "데이터마이닝 1차 검증", "6", "3", "접근성, 표본, 부상 flag 1차 통과"],
        ["4", "초기 모델 Top 3", "3", "3", "순수 모델 점수와 반복 등장 신호"],
        ["5", "실행 보정 Top 3", "3", "3", "계약, 의료, 시장 접근성까지 반영"],
    ]
    return render_table(
        "04_candidate_funnel.png",
        "후보 선정 과정",
        "전체 시장에서 바로 결론을 내리지 않고, 데이터마이닝과 현실성 검증으로 단계별 축소했습니다.",
        rows,
        ["Step", "단계", "타자", "투수", "의미"],
        [0.08, 0.26, 0.10, 0.10, 0.46],
        highlight_cols={2, 3},
        footer="한 줄: 모델은 후보를 찾고, 실행 검증은 실제 접촉 순위를 정한다.",
    )


def table_ensemble_models() -> Path:
    rows = [
        ["A", "Team Need Mining", "SSG 약점 정의", "팀 약점을 선수 조건으로 번역"],
        ["B", "KBO History", "성공/실패 패턴", "과거 KBO 외국인 유형과 닮았는지 평가"],
        ["C", "Archetype", "역할 유사도", "KBO 성공 유형 또는 SSG 필요 역할과 비교"],
        ["D", "Translation", "KBO 적응 위험", "미국 성적이 KBO에서도 유지될지 점검"],
        ["E", "Market", "시장 접근성", "40-man, DFA, 계약, 권리 상태 확인"],
        ["F", "Medical/Execution", "실행 불가능성 보류", "부상, 선발 빌드업, 즉시 전력 가능성 확인"],
    ]
    return render_table(
        "05_ensemble_model_roles.png",
        "여섯 모델이 각각 다른 질문을 담당했다",
        "한 점수표가 아니라 서로 다른 관점의 base learner를 앙상블했습니다.",
        rows,
        ["모델", "이름", "담당 질문", "발표 해석"],
        [0.09, 0.22, 0.24, 0.45],
        highlight_cols={0},
        footer="한 줄: 성적, 팀 필요, KBO 번역, 시장 접근성을 한 번에 본 통합 의사결정 모델이다.",
    )


def table_model_validation() -> Path:
    audit = pd.read_csv(ROOT / "outputs/tables/model_probability_calibration_audit_v1.csv")
    succ = audit[audit["target"].eq("success")].iloc[0]
    fail = audit[audit["target"].eq("failure")].iloc[0]
    rows = [
        ["직접 label leakage", "발견 없음", "success/failure/outcome/player id 계열 feature 제외"],
        ["후보 입력 누수", "발견 없음", "후보 입력은 recent Savant/MiLB 구조화 지표 중심"],
        ["타자 full-fit AUC", f"{succ['full_fit_auc']:.3f} / {fail['full_fit_auc']:.3f}", "높지만 절대 확률로 쓰면 과신 위험"],
        ["선수 단위 그룹 검증", f"success {succ['leave_one_player_group_auc']:.3f}, failure {fail['leave_one_player_group_auc']:.3f}", "반복 선수 효과를 줄이면 성능 하락"],
        ["최종 처리", "확률 표기 제거", "모델 지지/실패 경고/접촉 순위로만 사용"],
    ]
    return render_table(
        "06_leakage_overfit_validation.png",
        "누수와 과적합 가능성을 마지막에 검증했다",
        "성공확률처럼 과장하지 않고 후보 비교 신호로만 사용한 것이 핵심 방어 논리입니다.",
        rows,
        ["검증 항목", "결과", "발표 해석"],
        [0.24, 0.22, 0.54],
        highlight_cols={1},
        footer="한 줄: 이 모델은 성공확률 예언이 아니라, 후보 간 우선순위를 가르는 데이터마이닝 장치다.",
    )


def final_board() -> pd.DataFrame:
    return pd.read_csv(ROOT / "outputs/tables/final_candidate_board_execution_v4.csv")


def table_hitter_top3() -> Path:
    df = final_board()
    sub = df[(df["slot"].eq("foreign_hitter")) & (df["decision_rank"].astype(str).isin(["1", "2", "3"]))]
    rows = []
    for _, r in sub.iterrows():
        rows.append([
            r["decision_rank"],
            r["player"],
            r["decision"].replace("_", " "),
            r["model_support_tier"],
            r["failure_warning_tier"],
            r["market_reason"],
            r["risk_summary"],
        ])
    return render_table(
        "07_hitter_final_top3.png",
        "외국인 타자 최종 후보 3명",
        "현실성 제외 조건을 강화한 최종 접촉 보드입니다.",
        rows,
        ["순위", "선수", "최종 판단", "모델 지지", "실패 경고", "시장/역할 근거", "확인 리스크"],
        [0.06, 0.15, 0.14, 0.10, 0.10, 0.25, 0.20],
        highlight_cols={0, 3, 4},
        footer="한 줄: Brennan은 모델 지지와 시장 접근성이 동시에 맞물린 현실형 접촉 1순위다.",
    )


def table_hitter_hold() -> Path:
    df = final_board()
    names = ["Luis Matos", "Nolan Jones", "Jack Suwinski"]
    sub = df[df["player"].isin(names)]
    rows = []
    for _, r in sub.iterrows():
        rows.append([
            r["player"],
            r["decision"].replace("_", " "),
            r["model_support_tier"],
            r["failure_warning_tier"],
            r["market_reason"],
            r["risk_summary"],
        ])
    return render_table(
        "08_hitter_hold_watch_reasons.png",
        "좋아 보여도 최종 접촉 후보에서 내려간 타자들",
        "모델 신호가 좋아도 나이, 비용, 권리, 실패 경고가 맞지 않으면 보류했습니다.",
        rows,
        ["선수", "분류", "모델 지지", "실패 경고", "내려간 이유", "해석"],
        [0.15, 0.18, 0.10, 0.10, 0.27, 0.20],
        highlight_cols={1, 3},
        footer="한 줄: Matos는 좋은 후보지만, 지금 당장 KBO 대체 외국인으로는 현실성이 낮다.",
    )


def table_pitcher_top3() -> Path:
    df = final_board()
    sub = df[(df["slot"].eq("foreign_pitcher")) & (df["decision_rank"].astype(str).isin(["1", "2", "3"]))]
    rows = []
    for _, r in sub.iterrows():
        rows.append([
            r["decision_rank"],
            r["player"],
            r["decision"].replace("_", " "),
            f"{float(r['unified_fit_score']):.1f}",
            r["market_reason"],
            r["model_reason"],
            r["risk_summary"],
        ])
    return render_table(
        "09_pitcher_final_top3.png",
        "외국인 선발투수 최종 후보 3명",
        "투수는 classifier보다 command, starter floor, 실행 검증을 더 강하게 봤습니다.",
        rows,
        ["순위", "선수", "최종 판단", "통합 점수", "시장/역할 근거", "모델 근거", "확인 리스크"],
        [0.06, 0.15, 0.14, 0.10, 0.23, 0.18, 0.14],
        highlight_cols={0, 3},
        footer="한 줄: Fleming은 traffic-command starter 조건과 시장 접근성을 동시에 통과했다.",
        accent=SSG_BLUE,
    )


def table_pitcher_hold() -> Path:
    df = final_board()
    names = ["Bruce Zimmermann", "Bryse Wilson", "Randy Dobnak"]
    sub = df[df["player"].isin(names)]
    rows = []
    for _, r in sub.iterrows():
        rows.append([
            r["player"],
            r["decision"].replace("_", " "),
            r["market_reason"],
            r["model_reason"],
            r["risk_summary"],
        ])
    return render_table(
        "10_pitcher_hold_watch_reasons.png",
        "투수 대안과 보류 판단",
        "Plan B/C는 남기되, 계약 blocker와 HR 위험은 분리했습니다.",
        rows,
        ["선수", "분류", "시장 근거", "모델 근거", "보류/경고 이유"],
        [0.17, 0.20, 0.24, 0.20, 0.19],
        highlight_cols={1},
        footer="한 줄: 투수는 모델 점수보다 당장 던질 수 있는지와 경기 붕괴를 막는지가 더 중요하다.",
        accent=SSG_BLUE,
    )


def table_final_contact() -> Path:
    rows = [
        ["외국인 타자", "Will Brennan", "CONTACT 1ST", "DFA/outright 후 40-man 밖", "contact-floor OF, run-kill 완화", "medical history, KBO행 의사, 권리 조건"],
        ["외국인 선발", "Josh Fleming", "CONTACT 1ST", "minor contract 접근성", "BB/9 1.36, HR/9 0.51, 53.0 IP/10 GS", "최근 선발 빌드업, 구속, 구종 품질"],
    ]
    return render_table(
        "11_final_contact_1st_summary.png",
        "최종 접촉 1순위",
        "두 선수는 SSG 약점, KBO 번역 가능성, 시장 접근성, 비용·의료 검증을 함께 통과했습니다.",
        rows,
        ["슬롯", "선수", "판정", "시장 접근성", "SSG 적합성", "접촉 전 확인"],
        [0.14, 0.18, 0.15, 0.19, 0.20, 0.14],
        highlight_cols={1, 2},
        footer="한 줄: 가장 화려한 선수가 아니라 SSG가 실제로 데려와 약점을 줄일 수 있는 선수다.",
    )


def table_salary_contract_medical() -> Path:
    df = pd.read_csv(ROOT / "outputs/tables/final_candidate_salary_contract_gate_v1.csv")
    keep = ["Nolan Jones", "Luis Matos", "Jack Suwinski", "Josh Fleming", "Carson Spiers", "Brian Van Belle"]
    rows = []
    for _, r in df[df["candidate"].isin(keep)].iterrows():
        salary = r["structured_salary_signal_usd"]
        salary_text = "minor/unknown" if float(salary) == 0 else f"${float(salary)/1_000_000:.2f}M"
        rows.append([
            r["candidate"],
            salary_text,
            r["contract_access_status"],
            r["medical_availability_status"],
            r["economic_gate"],
            r["model_action"],
        ])
    return render_table(
        "12_salary_contract_medical_reality_check.png",
        "연봉·계약·의료 현실성 검증",
        "최종 추천은 능력뿐 아니라 계약 비용, 소속권, 의료 상태를 함께 통과해야 합니다.",
        rows,
        ["선수", "연봉 신호", "계약 접근성", "의료 상태", "경제성 판단", "모델 처리"],
        [0.13, 0.10, 0.24, 0.20, 0.18, 0.15],
        highlight_cols={1, 4},
        footer="한 줄: 현실성 검증은 모델 점수가 높은 후보를 무조건 추천하지 않기 위한 장치다.",
    )


def table_team_consensus() -> Path:
    df = final_board()
    rows = [
        ["Will Brennan", "최종 접촉 1순위", "모델 지지 강함 + 6/17 outright + OF role fit"],
        ["Luis Matos", "발견 단계 보류", "모델상 강하지만 age 24와 MLB reset value가 큼"],
        ["Nolan Jones", "비용/권리 보류", "power/OBP 신호는 강하지만 cash trade와 salary 확인 필요"],
        ["Jack Suwinski", "watchlist", "BB/barrel upside는 있지만 K%와 실패 경고가 큼"],
        ["Josh Fleming", "최종 접촉 1순위", "BB/9 1.36, HR/9 0.51, 선발/스윙맨 역할 적합"],
        ["Kolby Allard", "투수 3순위", "좌완, 낮은 HR/9, repeated minor deal"],
    ]
    return render_table(
        "13_candidate_reclassification_summary.png",
        "초기 후보와 최종 접촉 순위는 다르다",
        "팀원 후보와 모델 발견 후보를 버린 것이 아니라, 실행 가능성으로 재분류했습니다.",
        rows,
        ["선수", "최종 위치", "핵심 근거"],
        [0.20, 0.20, 0.60],
        highlight_cols={1},
        footer="한 줄: 좋은 신호가 있는 후보를 접촉/보류/관찰로 나눠야 실제 스카우팅 의사결정이 된다.",
    )


def make_contact_sheet(paths: list[Path]) -> Path:
    thumbs = []
    thumb_w = 430
    for i, path in enumerate(paths, 1):
        img = Image.open(path).convert("RGB")
        ratio = thumb_w / img.width
        thumb_h = int(img.height * ratio)
        t = img.resize((thumb_w, thumb_h))
        canvas = Image.new("RGB", (thumb_w, thumb_h + 34), WHITE)
        canvas.paste(t, (0, 0))
        d = ImageDraw.Draw(canvas)
        d.text((10, thumb_h + 7), f"{i:02d}. {path.name}", fill=DARK, font=font(16))
        thumbs.append(canvas)
    cols = 3
    gap = 18
    rows = math.ceil(len(thumbs) / cols)
    sheet_w = cols * thumb_w + (cols - 1) * gap
    sheet_h = rows * thumbs[0].height + (rows - 1) * gap
    sheet = Image.new("RGB", (sheet_w, sheet_h), WHITE)
    for idx, thumb in enumerate(thumbs):
        x = (idx % cols) * (thumb_w + gap)
        y = (idx // cols) * (thumb.height + gap)
        sheet.paste(thumb, (x, y))
    out = OUT_DIR / "00_contact_sheet_all_tables.png"
    sheet.save(out, quality=95)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.png"):
        old.unlink()
    paths = [
        table_hidden_weakness(),
        table_outfield_gap(),
        table_pitching_impact(),
        table_candidate_funnel(),
        table_ensemble_models(),
        table_model_validation(),
        table_hitter_top3(),
        table_hitter_hold(),
        table_pitcher_top3(),
        table_pitcher_hold(),
        table_final_contact(),
        table_salary_contract_medical(),
        table_team_consensus(),
    ]
    contact = make_contact_sheet(paths)
    if ZIP_OUT.exists():
        ZIP_OUT.unlink()
    with ZipFile(ZIP_OUT, "w", ZIP_DEFLATED) as zf:
        for path in [contact] + paths:
            zf.write(path, path.relative_to(OUT_DIR.parent))
    print(f"wrote {len(paths)} table PNGs")
    print(f"contact sheet: {contact}")
    print(f"zip: {ZIP_OUT}")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
