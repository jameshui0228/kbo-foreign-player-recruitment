#!/usr/bin/env python3
"""Build the final ensemble-style data-mining report.

This script treats the existing team analyses as base learners and produces a
single stacked evidence model. It intentionally uses structured numeric/model
outputs only; article, interview, and text-derived features are not model inputs.
"""

from __future__ import annotations

import html
from pathlib import Path
import re
import textwrap

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = PROJECT_ROOT / "outputs" / "tables"
REPORT_DIR = PROJECT_ROOT / "outputs" / "reports"
ASSET_DIR = REPORT_DIR / "ensemble_final_report_v1_assets"
DOC_DIR = PROJECT_ROOT / "docs"

TEAM_MATRIX = TABLE_DIR / "team_opinion_candidate_matrix_v1.csv"
DM_TOP3 = TABLE_DIR / "data_mining_recommendations_top3_v1.csv"
MODEL_AUDIT = TABLE_DIR / "data_mining_model_audit_v1.csv"

REPORT_HTML = REPORT_DIR / "ensemble_final_report_v1.html"
SCORE_CSV = TABLE_DIR / "ensemble_candidate_scores_v1.csv"
WEIGHT_CSV = TABLE_DIR / "ensemble_model_signal_weights_v1.csv"
SOURCE_NOTES = DOC_DIR / "ensemble_final_report_source_notes_v1.md"


FONT_FAMILY = ["Apple SD Gothic Neo", "AppleGothic", "Helvetica Neue", "Arial", "sans-serif"]
MONO_FONT_FAMILY = ["SF Mono", "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"]

TOKENS = {
    "surface": "#FCFCFD",
    "panel": "#FFFFFF",
    "ink": "#1F2430",
    "muted": "#6F768A",
    "grid": "#E6E8F0",
    "axis": "#D7DBE7",
}

COLOR_FAMILIES = {
    "blue": {
        "xlight": "#EAF1FE",
        "light": "#CEDFFE",
        "base": "#A3BEFA",
        "mid": "#5477C4",
        "dark": "#2E4780",
    },
    "gold": {
        "xlight": "#FFF4C2",
        "light": "#FFEA8F",
        "base": "#FFE15B",
        "mid": "#B8A037",
        "dark": "#736422",
    },
    "orange": {
        "xlight": "#FFEDDE",
        "light": "#FFBDA1",
        "base": "#F0986E",
        "mid": "#CC6F47",
        "dark": "#804126",
    },
    "olive": {
        "xlight": "#D8ECBD",
        "light": "#BEEB96",
        "base": "#A3D576",
        "mid": "#71B436",
        "dark": "#386411",
    },
    "pink": {
        "xlight": "#FCDAD6",
        "light": "#F5BACC",
        "base": "#F390CA",
        "mid": "#BD569B",
        "dark": "#8A3A6F",
    },
}


def add_chart_header(fig, ax, title: str, subtitle: str, *, title_width: int = 78, subtitle_width: int = 110) -> None:
    title = textwrap.fill(str(title).strip(), width=title_width, break_long_words=False)
    subtitle = textwrap.fill(str(subtitle).strip(), width=subtitle_width, break_long_words=False)
    ax.set_title("")
    title_lines = title.count("\n") + 1
    subtitle_lines = subtitle.count("\n") + 1
    fig.subplots_adjust(top=max(0.68, 0.88 - 0.04 * (title_lines - 1) - 0.03 * (subtitle_lines - 1)))
    left = ax.get_position().x0
    fig.text(left, 0.97, title, ha="left", va="top", fontsize=15, fontweight="bold", color=TOKENS["ink"])
    fig.text(left, 0.91, subtitle, ha="left", va="top", fontsize=10.5, color=TOKENS["muted"])


def set_chart_style() -> None:
    plt.rcParams.update(
        {
            "font.family": FONT_FAMILY,
            "axes.facecolor": TOKENS["panel"],
            "figure.facecolor": TOKENS["surface"],
            "axes.edgecolor": TOKENS["axis"],
            "axes.labelcolor": TOKENS["ink"],
            "xtick.color": TOKENS["muted"],
            "ytick.color": TOKENS["muted"],
            "grid.color": TOKENS["grid"],
            "grid.linestyle": "-",
            "grid.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def parse_rank(value: object) -> float | None:
    text = str(value).strip()
    if text.isdigit():
        return float(text)
    match = re.search(r"(\d+)", text)
    if match:
        return float(match.group(1))
    if "prior top" in text:
        return 3.0
    return None


def rank_signal(rank: float | None, max_rank: int) -> float:
    if rank is None:
        return 0.0
    rank = max(1.0, min(float(max_rank), rank))
    return (max_rank - rank + 1) / max_rank


def build_signal_weights() -> pd.DataFrame:
    rows = [
        {
            "slot": "foreign_hitter",
            "signal": "historical_success_failure_classifier",
            "weight": 0.40,
            "reason": "타자 AUC가 성공 0.833, 실패 0.738로 promoted gate를 통과했기 때문에 가장 큰 base learner로 사용",
        },
        {
            "slot": "foreign_hitter",
            "signal": "ssg_fit_translation_pipeline",
            "weight": 0.25,
            "reason": "SSG 2026 상황별 약점, KBO 번역, 영입 등급을 동시에 반영하는 구조적 base learner",
        },
        {
            "slot": "foreign_hitter",
            "signal": "kbo_adaptation_filter",
            "weight": 0.15,
            "reason": "변화구/저속 구종 대응과 좌타/스위치 적합성을 통해 KBO 적응 실패를 줄이는 filter",
        },
        {
            "slot": "foreign_hitter",
            "signal": "market_inefficiency_feature_model",
            "weight": 0.15,
            "reason": "AAA 장점과 MLB 결함의 translation gap, quality contact를 통해 시장 비효율을 탐색",
        },
        {
            "slot": "foreign_hitter",
            "signal": "cross_model_consensus",
            "weight": 0.05,
            "reason": "서로 다른 가정의 base learner에서 반복 등장한 후보에 작은 안정성 보너스",
        },
        {
            "slot": "foreign_pitcher",
            "signal": "historical_success_failure_classifier",
            "weight": 0.05,
            "reason": "투수 AUC 0.603으로 watch 등급이므로 확정 추천이 아닌 약한 diagnostic signal로만 사용",
        },
        {
            "slot": "foreign_pitcher",
            "signal": "ssg_fit_translation_pipeline",
            "weight": 0.25,
            "reason": "선발 이닝, KBO ERA 번역, 영입 등급을 반영하는 구조적 base learner",
        },
        {
            "slot": "foreign_pitcher",
            "signal": "kbo_adaptation_filter",
            "weight": 0.25,
            "reason": "BB/9, HR/9, third-time wOBA로 KBO 선발 지속성과 ABS 적응 위험을 줄이는 filter",
        },
        {
            "slot": "foreign_pitcher",
            "signal": "market_inefficiency_feature_model",
            "weight": 0.20,
            "reason": "선발 지속성, GB, HR 억제, command feature로 MLB fringe 선발 시장을 탐색",
        },
        {
            "slot": "foreign_pitcher",
            "signal": "cross_model_consensus",
            "weight": 0.25,
            "reason": "투수 supervised model이 약하기 때문에 여러 독립 분석에서 반복 등장하는지를 더 크게 반영",
        },
    ]
    return pd.DataFrame(rows)


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    team = pd.read_csv(TEAM_MATRIX)
    dm = pd.read_csv(DM_TOP3)
    audit = pd.read_csv(MODEL_AUDIT)
    return team, dm, audit


def build_candidate_scores() -> pd.DataFrame:
    team, dm, _ = load_inputs()
    weights = build_signal_weights()
    records: list[dict[str, object]] = []

    slot_map = {"hitter": "foreign_hitter", "pitcher": "foreign_pitcher"}
    candidates: set[tuple[str, str]] = set()
    for _, row in team.iterrows():
        candidates.add((slot_map[row["slot"]], row["candidate"]))
    for _, row in dm.iterrows():
        candidates.add((row["slot"], row["player_name"]))

    for slot, candidate in sorted(candidates):
        short_slot = "hitter" if slot == "foreign_hitter" else "pitcher"
        slot_weights = weights[weights["slot"].eq(slot)].set_index("signal")["weight"].to_dict()
        rows = team[(team["slot"].eq(short_slot)) & (team["candidate"].eq(candidate))]
        dm_rows = dm[(dm["slot"].eq(slot)) & (dm["player_name"].eq(candidate))]

        dm_signal = 0.0
        dm_success_prob = None
        dm_failure_prob = None
        dm_margin = None
        if not dm_rows.empty:
            dm_row = dm_rows.iloc[0]
            dm_success_prob = float(dm_row["dm_success_prob"])
            dm_failure_prob = float(dm_row["dm_failure_prob"])
            dm_margin = float(dm_row["dm_margin"])
            dm_signal = max(0.0, min(1.0, dm_margin))

        source_signals = {
            "sewon": 0.0,
            "jimini": 0.0,
            "kyuho": 0.0,
        }
        source_presence = []
        for source in ["sewon", "jimini", "kyuho"]:
            src_rows = rows[rows["source"].eq(source)]
            if src_rows.empty:
                continue
            rank = parse_rank(src_rows.iloc[0]["rank_or_group"])
            max_rank = 6 if short_slot == "hitter" and source == "sewon" else 5
            signal = rank_signal(rank, max_rank)
            source_signals[source] = signal
            source_presence.append(source)

        if not rows[rows["source"].eq("codex")].empty:
            source_presence.append("codex_structured")

        if not dm_rows.empty:
            source_presence.append("historical_dm")

        consensus_signal = min(1.0, len(set(source_presence)) / 4)
        if slot == "foreign_hitter":
            score = (
                slot_weights["historical_success_failure_classifier"] * dm_signal
                + slot_weights["ssg_fit_translation_pipeline"] * source_signals["sewon"]
                + slot_weights["kbo_adaptation_filter"] * source_signals["jimini"]
                + slot_weights["market_inefficiency_feature_model"] * source_signals["kyuho"]
                + slot_weights["cross_model_consensus"] * consensus_signal
            )
        else:
            score = (
                slot_weights["historical_success_failure_classifier"] * dm_signal
                + slot_weights["ssg_fit_translation_pipeline"] * source_signals["sewon"]
                + slot_weights["kbo_adaptation_filter"] * source_signals["jimini"]
                + slot_weights["market_inefficiency_feature_model"] * source_signals["kyuho"]
                + slot_weights["cross_model_consensus"] * consensus_signal
            )

        tier = "core"
        if slot == "foreign_pitcher":
            tier = "diagnostic_core" if score >= 0.30 else "watch"
        elif score < 0.30:
            tier = "watch"
        elif dm_signal == 0 and consensus_signal >= 0.5:
            tier = "scouting_consensus"
        elif dm_signal > 0 and consensus_signal < 0.5:
            tier = "model_discovery"

        records.append(
            {
                "slot": slot,
                "candidate": candidate,
                "ensemble_score": round(score, 4),
                "dm_success_prob": dm_success_prob,
                "dm_failure_prob": dm_failure_prob,
                "dm_margin": dm_margin,
                "dm_signal": round(dm_signal, 4),
                "sewon_signal": round(source_signals["sewon"], 4),
                "jimini_signal": round(source_signals["jimini"], 4),
                "kyuho_signal": round(source_signals["kyuho"], 4),
                "consensus_signal": round(consensus_signal, 4),
                "source_presence": "; ".join(source_presence) if source_presence else "-",
                "ensemble_tier": tier,
            }
        )

    scores = pd.DataFrame(records)
    scores = scores.sort_values(["slot", "ensemble_score"], ascending=[True, False]).reset_index(drop=True)
    scores["rank"] = scores.groupby("slot").cumcount() + 1
    return scores


def save_charts(scores: pd.DataFrame, weights: pd.DataFrame) -> dict[str, Path]:
    set_chart_style()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    # Chart 1: model signal weights by slot.
    weight_plot = weights.copy()
    label_map = {
        "historical_success_failure_classifier": "과거 성공/실패 학습",
        "ssg_fit_translation_pipeline": "SSG fit/번역",
        "kbo_adaptation_filter": "KBO 적응 filter",
        "market_inefficiency_feature_model": "시장 비효율",
        "cross_model_consensus": "반복 등장 consensus",
    }
    weight_plot["signal_label"] = weight_plot["signal"].map(label_map)
    weight_plot["slot_label"] = weight_plot["slot"].map({"foreign_hitter": "타자", "foreign_pitcher": "투수"})

    pivot = (
        weight_plot.pivot_table(index="signal_label", columns="slot_label", values="weight", aggfunc="sum")
        .loc[list(label_map.values())]
        .fillna(0)
    )
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
    y_positions = list(range(len(pivot.index)))
    bar_h = 0.34
    hitter_vals = pivot.get("타자", pd.Series([0] * len(pivot), index=pivot.index)).values
    pitcher_vals = pivot.get("투수", pd.Series([0] * len(pivot), index=pivot.index)).values
    ax.barh(
        [y + bar_h / 2 for y in y_positions],
        hitter_vals,
        height=bar_h,
        color=COLOR_FAMILIES["blue"]["base"],
        edgecolor=TOKENS["ink"],
        linewidth=0.6,
        label="타자",
    )
    ax.barh(
        [y - bar_h / 2 for y in y_positions],
        pitcher_vals,
        height=bar_h,
        color=COLOR_FAMILIES["orange"]["base"],
        edgecolor=TOKENS["ink"],
        linewidth=0.6,
        label="투수",
    )
    for y, value in zip([y + bar_h / 2 for y in y_positions], hitter_vals):
        ax.text(value + 0.008, y, f"{value:.0%}", va="center", ha="left", fontsize=9, color=TOKENS["ink"])
    for y, value in zip([y - bar_h / 2 for y in y_positions], pitcher_vals):
        ax.text(value + 0.008, y, f"{value:.0%}", va="center", ha="left", fontsize=9, color=TOKENS["ink"])
    ax.set_yticks(y_positions)
    ax.set_yticklabels(pivot.index)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xlim(0, 0.46)
    ax.set_xlabel("앙상블 내 반영 비중")
    ax.set_ylabel("")
    ax.legend(title="", loc="lower right", frameon=False)
    ax.grid(axis="x", color=TOKENS["grid"])
    ax.grid(axis="y", visible=False)
    add_chart_header(
        fig,
        ax,
        "타자는 학습 모델, 투수는 consensus와 적응 filter 비중이 더 크다",
        "타자 classifier는 promoted gate를 통과했지만 투수 classifier는 watch 등급이라 슬롯별 가중 구조를 다르게 설계했다.",
    )
    path = ASSET_DIR / "ensemble_signal_weights.png"
    fig.savefig(path, bbox_inches="tight", facecolor=TOKENS["surface"])
    plt.close(fig)
    paths["weights"] = path

    # Chart 2: top hitter scores.
    top_hitters = scores[scores["slot"].eq("foreign_hitter")].head(8).copy()
    hitter_plot = top_hitters.sort_values("ensemble_score", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=160)
    bars = ax.barh(
        hitter_plot["candidate"],
        hitter_plot["ensemble_score"],
        color=COLOR_FAMILIES["blue"]["base"],
        edgecolor=TOKENS["ink"],
        linewidth=0.6,
    )
    ax.set_xlabel("앙상블 점수")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xlim(0, max(0.58, float(hitter_plot["ensemble_score"].max()) + 0.08))
    ax.grid(axis="x", color=TOKENS["grid"])
    ax.grid(axis="y", visible=False)
    for bar in bars:
        value = bar.get_width()
        ax.text(value + 0.008, bar.get_y() + bar.get_height() / 2, f"{value:.1%}", va="center", ha="left", fontsize=9, color=TOKENS["ink"])
    add_chart_header(
        fig,
        ax,
        "Nolan Jones가 모델 확률과 팀원 consensus를 동시에 통과했다",
        "상위 타자 후보 8명. 점수는 과거 성공/실패 학습, SSG fit, KBO 적응 filter, 시장 비효율, 반복 등장 신호를 합성했다.",
    )
    path = ASSET_DIR / "hitter_ensemble_ranking.png"
    fig.savefig(path, bbox_inches="tight", facecolor=TOKENS["surface"])
    plt.close(fig)
    paths["hitters"] = path

    # Chart 3: pitcher scores.
    top_pitchers = scores[scores["slot"].eq("foreign_pitcher")].head(8).copy()
    pitcher_plot = top_pitchers.sort_values("ensemble_score", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.8), dpi=160)
    bars = ax.barh(
        pitcher_plot["candidate"],
        pitcher_plot["ensemble_score"],
        color=COLOR_FAMILIES["orange"]["base"],
        edgecolor=TOKENS["ink"],
        linewidth=0.6,
    )
    ax.set_xlabel("앙상블 점수")
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0))
    ax.set_xlim(0, max(0.58, float(pitcher_plot["ensemble_score"].max()) + 0.08))
    ax.grid(axis="x", color=TOKENS["grid"])
    ax.grid(axis="y", visible=False)
    for bar in bars:
        value = bar.get_width()
        ax.text(value + 0.008, bar.get_y() + bar.get_height() / 2, f"{value:.1%}", va="center", ha="left", fontsize=9, color=TOKENS["ink"])
    add_chart_header(
        fig,
        ax,
        "투수는 Josh Fleming만 consensus가 강하고 나머지는 검증 후보로 남는다",
        "상위 투수 후보 8명. 투수 supervised model은 watch 등급이라 consensus, command, starter translation signal을 더 크게 반영했다.",
    )
    path = ASSET_DIR / "pitcher_ensemble_ranking.png"
    fig.savefig(path, bbox_inches="tight", facecolor=TOKENS["surface"])
    plt.close(fig)
    paths["pitchers"] = path

    # Chart 4: model validation audit.
    audit_rows = [
        {"slot": "타자 성공", "auc": 0.833, "status": "promoted"},
        {"slot": "타자 실패", "auc": 0.738, "status": "promoted"},
        {"slot": "투수 성공", "auc": 0.603, "status": "watch"},
    ]
    audit_plot = pd.DataFrame(audit_rows)
    fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=160)
    bar_colors = [
        COLOR_FAMILIES["olive"]["base"] if status == "promoted" else COLOR_FAMILIES["gold"]["base"]
        for status in audit_plot["status"]
    ]
    bars = ax.barh(
        audit_plot["slot"],
        audit_plot["auc"],
        color=bar_colors,
        edgecolor=TOKENS["ink"],
        linewidth=0.6,
    )
    ax.axvline(0.5, color=TOKENS["muted"], linestyle="--", linewidth=1)
    ax.set_xlim(0.45, 0.90)
    ax.set_xlabel("AUC")
    ax.set_ylabel("")
    ax.grid(axis="x", color=TOKENS["grid"])
    ax.grid(axis="y", visible=False)
    for bar in bars:
        value = bar.get_width()
        ax.text(value + 0.008, bar.get_y() + bar.get_height() / 2, f"{value:.3f}", va="center", ha="left", fontsize=9, color=TOKENS["ink"])
    add_chart_header(
        fig,
        ax,
        "타자는 추천 가능, 투수는 진단용이라는 결론이 모델 검증에서 나온다",
        "과거 KBO 외국인 label 기반 검증. AUC 0.5는 무작위 기준선이며, 투수 성공 모델은 watch 등급으로 처리했다.",
    )
    path = ASSET_DIR / "model_validation_auc.png"
    fig.savefig(path, bbox_inches="tight", facecolor=TOKENS["surface"])
    plt.close(fig)
    paths["auc"] = path

    return paths


def fmt_pct(value: object, digits: int = 1) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{float(value) * 100:.{digits}f}%"


def html_table(df: pd.DataFrame, columns: list[str], headers: list[str]) -> str:
    body = []
    body.append("<table>")
    body.append("<thead><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in headers) + "</tr></thead>")
    body.append("<tbody>")
    for _, row in df.iterrows():
        cells = []
        for col in columns:
            value = row[col]
            if isinstance(value, float):
                if col.endswith("score") or col.endswith("signal") or col in {"dm_success_prob", "dm_failure_prob", "dm_margin"}:
                    text = fmt_pct(value)
                else:
                    text = f"{value:.3f}"
            else:
                text = str(value)
            cells.append(f"<td>{html.escape(text)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    body.append("</tbody></table>")
    return "\n".join(body)


def render_report(scores: pd.DataFrame, weights: pd.DataFrame, chart_paths: dict[str, Path]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)

    hitter_top = scores[scores["slot"].eq("foreign_hitter")].head(6).copy()
    pitcher_top = scores[scores["slot"].eq("foreign_pitcher")].head(6).copy()

    css = """
    :root {
      --bg: #FCFCFD;
      --panel: #FFFFFF;
      --ink: #1F2430;
      --muted: #6F768A;
      --grid: #E6E8F0;
      --axis: #D7DBE7;
      --blue: #5477C4;
      --orange: #CC6F47;
      --olive: #71B436;
      --gold: #B8A037;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, Aptos, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.62;
    }
    main {
      max-width: 1080px;
      margin: 0 auto;
      padding: 54px 28px 80px;
    }
    h1 {
      font-size: 34px;
      line-height: 1.18;
      margin: 0 0 18px;
      letter-spacing: 0;
    }
    h2 {
      font-size: 23px;
      margin: 42px 0 14px;
      padding-top: 4px;
      border-top: 1px solid var(--grid);
      letter-spacing: 0;
    }
    h3 {
      font-size: 18px;
      margin: 28px 0 10px;
    }
    p { margin: 10px 0 16px; }
    .summary {
      background: #FFFFFF;
      border: 1px solid var(--grid);
      border-left: 6px solid var(--blue);
      padding: 18px 20px;
      margin: 24px 0 30px;
      border-radius: 6px;
    }
    .summary p { margin: 0 0 10px; }
    .summary p:last-child { margin-bottom: 0; }
    .kpi-row {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin: 22px 0 28px;
    }
    .kpi {
      background: var(--panel);
      border: 1px solid var(--grid);
      border-radius: 6px;
      padding: 15px 16px;
    }
    .kpi .value {
      font-family: "SF Mono", Menlo, Consolas, monospace;
      font-size: 22px;
      font-weight: 700;
      color: var(--ink);
    }
    .kpi .label {
      font-size: 13px;
      color: var(--muted);
      margin-top: 4px;
    }
    figure {
      margin: 24px 0 30px;
      padding: 0;
      background: var(--panel);
      border: 1px solid var(--grid);
      border-radius: 6px;
      overflow: hidden;
    }
    figure img {
      display: block;
      width: 100%;
      height: auto;
    }
    figcaption {
      font-size: 13px;
      color: var(--muted);
      border-top: 1px solid var(--grid);
      padding: 10px 14px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 16px 0 26px;
      background: var(--panel);
      border: 1px solid var(--grid);
      border-radius: 6px;
      overflow: hidden;
      font-size: 14px;
    }
    th, td {
      border-bottom: 1px solid var(--grid);
      padding: 10px 11px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #F4F5F7;
      font-weight: 700;
      color: var(--ink);
    }
    td:nth-child(3), td:nth-child(4), td:nth-child(5) {
      font-family: "SF Mono", Menlo, Consolas, monospace;
      white-space: nowrap;
    }
    .note {
      color: var(--muted);
      font-size: 14px;
    }
    .callout {
      background: #FFF9D8;
      border: 1px solid #FFEA8F;
      padding: 14px 16px;
      border-radius: 6px;
      margin: 18px 0 22px;
    }
    ul { padding-left: 21px; }
    li { margin: 6px 0; }
    code {
      font-family: "SF Mono", Menlo, Consolas, monospace;
      font-size: 0.92em;
      background: #F4F5F7;
      padding: 1px 5px;
      border-radius: 4px;
    }
    @media (max-width: 760px) {
      main { padding: 34px 18px 60px; }
      h1 { font-size: 27px; }
      .kpi-row { grid-template-columns: 1fr; }
      table { font-size: 13px; }
      th, td { padding: 8px; }
    }
    """

    hitter_table = html_table(
        hitter_top,
        ["rank", "candidate", "ensemble_score", "dm_success_prob", "dm_failure_prob", "source_presence", "ensemble_tier"],
        ["순위", "선수", "앙상블 점수", "성공확률", "실패확률", "근거 출처", "판정"],
    )
    pitcher_table = html_table(
        pitcher_top,
        ["rank", "candidate", "ensemble_score", "dm_success_prob", "dm_failure_prob", "source_presence", "ensemble_tier"],
        ["순위", "선수", "앙상블 점수", "성공확률", "실패위험", "근거 출처", "판정"],
    )

    weights_for_table = weights.copy()
    weights_for_table["weight"] = weights_for_table["weight"].map(lambda v: f"{v:.0%}")
    weight_table = html_table(
        weights_for_table,
        ["slot", "signal", "weight", "reason"],
        ["슬롯", "base learner", "비중", "근거"],
    )

    rel = {k: v.relative_to(REPORT_DIR) for k, v in chart_paths.items()}

    html_doc = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SSG 외국인 선수 영입 앙상블 데이터 마이닝 최종 보고서</title>
  <style>{css}</style>
</head>
<body>
<main>
  <h1>SSG 외국인 선수 영입 앙상블 데이터 마이닝 최종 보고서</h1>

  <section class="summary">
    <p><strong>기술 요약.</strong> 네 명의 분석을 따로 병렬 비교하지 않고, 하나의 stacked-style 앙상블 모델로 재구성했다. base learner는 과거 KBO 외국인 성공/실패 학습 모델, SSG fit/번역 파이프라인, KBO 적응 filter, 시장 비효율 feature model, 반복 등장 consensus signal이다.</p>
    <p><strong>최종 결론.</strong> 타자는 Nolan Jones가 앙상블 1순위이고, Luis Matos는 순수 성공/실패 classifier가 새로 끌어올린 model-discovery 후보로 남는다. 투수는 Josh Fleming만 consensus가 강하며, 나머지는 확정 추천이 아니라 검증 board로 두는 것이 타당하다.</p>
    <p><strong>가장 중요한 해석.</strong> 이 모델은 “가중치 점수표”가 아니라 서로 다른 데이터 마이닝 관점을 base learner로 둔 앙상블이다. 특히 투수는 모델 검증력이 낮아 추천 강도를 의도적으로 낮췄다.</p>
  </section>

  <div class="kpi-row">
    <div class="kpi"><div class="value">0.833</div><div class="label">타자 성공 classifier AUC</div></div>
    <div class="kpi"><div class="value">0.738</div><div class="label">타자 실패 classifier AUC</div></div>
    <div class="kpi"><div class="value">0.603</div><div class="label">투수 성공 classifier AUC, watch only</div></div>
  </div>

  <h2>1. 결론은 “팀원별 후보 모음”이 아니라 하나의 앙상블 모델이다</h2>
  <p><strong>이번 최종 모델은 네 명의 산출물을 하나의 evidence stack으로 묶는다.</strong> Codex의 과거 KBO 성공/실패 classifier는 historical label을 직접 학습한 가장 강한 타자 base learner다. sewon의 6단계 파이프라인은 SSG 약점, KBO 번역, 영입 현실성을 연결한다. jimini의 filter는 KBO 변화구, 저속 구종, ABS 환경에서 무너질 후보를 제거한다. kyuho의 feature model은 MLB fringe 시장에서 KBO로 번역될 수 있는 숨은 장점을 찾는다.</p>
  <p>따라서 발표에서는 “각자 후보가 다르다”가 아니라 <strong>서로 다른 base learner가 같은 후보를 얼마나 지지하는가</strong>를 보여주면 된다. 이 구조가 데이터 마이닝 느낌을 가장 잘 살린다.</p>

  <figure>
    <img src="{html.escape(str(rel['weights']))}" alt="앙상블 base learner 가중 구조" />
    <figcaption>슬롯별 base learner 비중. 타자는 classifier 검증력이 있어 historical model 비중이 크고, 투수는 classifier가 약해 consensus와 command/translation filter 비중이 커진다.</figcaption>
  </figure>

  <h2>2. 모델 설계: base learner와 역할</h2>
  <p><strong>앙상블은 단순 평균이 아니다.</strong> 각 base learner의 신뢰도와 역할이 다르기 때문에 슬롯별로 다른 weight를 부여했다. 타자는 과거 KBO 성공/실패 classifier가 검증을 통과했으므로 40%를 반영했고, 투수는 classifier AUC가 0.603에 그쳐 5% diagnostic signal로만 반영했다.</p>
  {weight_table}

  <h2>3. 타자: Nolan Jones는 모델 확률과 팀원 consensus가 동시에 붙는다</h2>
  <p><strong>타자 앙상블의 핵심은 Nolan Jones와 Luis Matos의 역할 차이다.</strong> Nolan Jones는 과거 성공/실패 classifier에서 높은 성공확률을 받고 sewon, jimini에서도 반복 등장한다. 즉 모델 확률과 팀원 독립 분석이 동시에 지지한다. Luis Matos는 팀원 교집합은 약하지만 classifier가 가장 강하게 끌어올린 hidden/model-discovery 후보다.</p>
  <p>Dylan Carlson은 순수 classifier에서는 Top 3지만, 다른 base learner의 지지가 약하다. 그래서 최종 발표에서는 “모델 후보 유지”로 남기되, Nolan Jones나 Luis Matos와 같은 강도로 말하지 않는 편이 낫다. Jack Suwinski와 Michael Toglia는 pure classifier 후보는 아니지만 sewon과 kyuho가 동시에 잡은 power-upside board다.</p>

  <figure>
    <img src="{html.escape(str(rel['hitters']))}" alt="외국인 타자 앙상블 랭킹" />
    <figcaption>타자 상위 후보. Nolan Jones는 classifier와 consensus가 결합되어 1위가 되었고, Luis Matos는 classifier가 새로 발굴한 후보로 유지된다.</figcaption>
  </figure>
  {hitter_table}

  <h2>4. 투수: Josh Fleming은 합의 후보지만 아직 확정 추천은 아니다</h2>
  <p><strong>투수는 타자와 같은 방식으로 확정 추천하면 안 된다.</strong> 과거 KBO 투수 성공 classifier의 AUC는 0.603으로 watch 등급이다. 따라서 투수 모델은 “누가 확실히 성공한다”가 아니라 “어떤 후보를 먼저 검증할지”를 정하는 장치다.</p>
  <p>이 조건에서 Josh Fleming이 가장 앞서는 이유는 명확하다. jimini와 kyuho가 동시에 지지했고, 기존 Codex 통합모델에서도 반복 등장했다. 반면 Bryse Wilson과 Austin Gomber는 pure diagnostic model에서는 잡히지만 팀원 consensus가 약하다. Carson Spiers와 Brian Van Belle은 sewon의 번역/이닝형 후보로 가치가 있지만, medical, 계약 접근성, 역할 지속성 확인이 필요하다.</p>

  <figure>
    <img src="{html.escape(str(rel['pitchers']))}" alt="외국인 투수 앙상블 랭킹" />
    <figcaption>투수 상위 후보. Josh Fleming은 반복 등장 consensus가 강하지만, 투수 classifier 검증력이 낮아 최종 추천이 아니라 1차 검증 후보로 제시한다.</figcaption>
  </figure>
  {pitcher_table}

  <h2>5. 왜 타자와 투수를 다르게 말해야 하는가</h2>
  <p><strong>모델 검증 결과가 결론의 말투를 결정한다.</strong> 타자 성공/실패 classifier는 각각 AUC 0.833, 0.738로 후보 추천에 쓸 수 있는 수준이다. 반면 투수 성공 classifier는 AUC 0.603이라서 확정 추천으로 쓰기 어렵다. 이 차이를 숨기면 발표가 약해진다. 오히려 이 차이를 명확히 말해야 모델이 정직해 보인다.</p>

  <figure>
    <img src="{html.escape(str(rel['auc']))}" alt="모델 검증 AUC 비교" />
    <figcaption>검증 성능 비교. 타자는 promoted, 투수는 watch 등급으로 처리했기 때문에 최종 추천 강도도 달라진다.</figcaption>
  </figure>

  <h2>6. 발표용 핵심 인사이트</h2>
  <ul>
    <li><strong>SSG의 타자 보강은 장타 총량이 아니라 game-state conversion 문제다.</strong> 1루 주자 상황, 2사, 초반 이닝에서 공격 흐름을 살릴 수 있는 선구/갭파워/구종 대응형 외야 자원이 필요하다.</li>
    <li><strong>외국인 타자 모델은 후보를 실제로 바꿨다.</strong> 기존 수동 fit 점수에서는 덜 보였던 Luis Matos가 classifier에서 강하게 올라왔고, Nolan Jones는 classifier와 consensus를 동시에 통과했다.</li>
    <li><strong>투수는 “정답 후보”보다 “검증 우선순위”가 결론이다.</strong> Josh Fleming이 가장 강한 1차 검증 후보지만, 투수 전체는 계약, medical, 선발 지속성, BB/9/HR/9 추가 확인이 필요하다.</li>
    <li><strong>Dylan Carlson, Bryse Wilson, Austin Gomber는 모델-only 또는 diagnostic 후보로 분리해야 한다.</strong> 이들을 무리하게 최종 추천처럼 말하지 않는 것이 보고서의 신뢰도를 높인다.</li>
    <li><strong>Jack Suwinski와 Michael Toglia는 최종 모델의 반박 후보군이다.</strong> classifier top은 아니지만 시장 비효율과 power-upside base learner가 지지하기 때문에 스카우팅 검증군에 남길 가치가 있다.</li>
  </ul>

  <h2>7. 최종 후보 board</h2>
  <div class="callout">
    <strong>최종 타자 board:</strong> Nolan Jones를 ensemble 1순위, Luis Matos를 model-discovery 1순위, Jack Suwinski/Michael Toglia를 upside 반박 후보로 둔다. Dylan Carlson은 classifier Top 3지만 다른 base learner 지지가 약해 보류성 후보로 설명한다.
  </div>
  <div class="callout">
    <strong>최종 투수 board:</strong> Josh Fleming을 consensus 검증 1순위로 두고, Carson Spiers, Brian Van Belle, Bryse Wilson, Austin Gomber를 추가 검증군으로 둔다. 투수는 확정 추천이 아니라 검증 우선순위라는 표현을 유지한다.
  </div>

  <h2>8. 한계와 다음 검증</h2>
  <p><strong>이 보고서는 현재 확보된 구조화 숫자 데이터로 만든 앙상블이다.</strong> 기사, 인터뷰, 평판 텍스트는 input에서 제외했다. 남은 핵심 리스크는 실제 연봉, buyout, opt-out, 한국행 의사, medical, 40인/계약 변동이다. 특히 투수는 이 추가 정보가 들어오기 전까지 “추천”보다 “검증 board”로 두는 편이 맞다.</p>
  <ul>
    <li>타자 추가 검증: 2026 최신 Savant 표본, 좌/우 split, breaking/off-speed 대응, KBO 외야 수비/주루 역할.</li>
    <li>투수 추가 검증: 최근 4주 구속 변화, starter pitch count, BB/9와 HR/9의 park-adjusted 안정성, medical flag.</li>
    <li>계약 검증: 실제 연봉, 잔여 보장액, 방출 가능성, KBO 외국인 선수 계약 상한/세금/이적료 리스크.</li>
  </ul>

  <p class="note">Source artifacts: ensemble scores, model weights, data-mining Top 3, team candidate matrix, and branch reports under the local project repository. This report uses numeric/model outputs only and excludes article/interview/text variables from model input.</p>
</main>
</body>
</html>
"""
    REPORT_HTML.write_text(html_doc, encoding="utf-8")

    source_notes = f"""# Ensemble Final Report Source Notes v1

Generated: 2026-06-23

## Delivery surface

- HTML report: `{REPORT_HTML.relative_to(PROJECT_ROOT)}`
- Chart assets: `{ASSET_DIR.relative_to(PROJECT_ROOT)}`

## Source tables

- `outputs/tables/team_opinion_candidate_matrix_v1.csv`
- `outputs/tables/data_mining_recommendations_top3_v1.csv`
- `outputs/tables/data_mining_model_audit_v1.csv`

## Chart map

1. `ensemble_signal_weights.png`
   - Question: how does the ensemble combine base learners differently by slot?
   - Form: grouped horizontal bar.
   - Claim: hitter relies more on promoted classifier; pitcher relies more on consensus/filter signals.
2. `hitter_ensemble_ranking.png`
   - Question: which hitter candidates survive the ensemble?
   - Form: ranked horizontal bar.
   - Claim: Nolan Jones combines classifier and consensus; Luis Matos is model-discovery.
3. `pitcher_ensemble_ranking.png`
   - Question: which pitcher candidates should be verified first?
   - Form: ranked horizontal bar.
   - Claim: Josh Fleming is the strongest consensus verification candidate.
4. `model_validation_auc.png`
   - Question: why are hitter and pitcher recommendation strengths different?
   - Form: benchmark bar with 0.5 random baseline.
   - Claim: hitter models are promoted; pitcher model remains watch-grade.

## Omitted or bounded evidence

- Articles, interviews, and text-derived variables were excluded from model input by user instruction.
- Pitcher final recommendation is intentionally downgraded to diagnostic board because the pitcher classifier AUC is 0.603.
- Salary and buyout variables are named as next hard gates, not fully embedded in the current ensemble score.
"""
    SOURCE_NOTES.write_text(source_notes, encoding="utf-8")


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    DOC_DIR.mkdir(parents=True, exist_ok=True)

    weights = build_signal_weights()
    scores = build_candidate_scores()
    weights.to_csv(WEIGHT_CSV, index=False, encoding="utf-8-sig")
    scores.to_csv(SCORE_CSV, index=False, encoding="utf-8-sig")
    chart_paths = save_charts(scores, weights)
    render_report(scores, weights, chart_paths)

    print(f"wrote {REPORT_HTML}")
    print(f"wrote {SCORE_CSV}")
    print(f"wrote {WEIGHT_CSV}")
    print(f"wrote {SOURCE_NOTES}")
    for path in chart_paths.values():
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
