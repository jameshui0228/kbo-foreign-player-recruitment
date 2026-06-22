# -*- coding: utf-8 -*-
"""
SSG Landers 외국인 선수 영입 분석 보고서 생성기
"""
import pathlib, pandas as pd, numpy as np, html, datetime

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_DIR = PROJECT_ROOT / "outputs"
TABLE_DIR = OUT_DIR / "tables"
REPORT_DIR = OUT_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

today = datetime.date.today().strftime("%Y년 %m월 %d일")

hitters  = pd.read_csv(TABLE_DIR / "final_hitter_ranking.csv")
starters = pd.read_csv(TABLE_DIR / "final_starter_ranking.csv")

def f(v, fmt=".3f"):
    try: return format(float(v), fmt)
    except: return str(v) if v and str(v) != "nan" else "—"

def pct(v):
    try: return f"{float(v)*100:.1f}%"
    except: return "—"

def tier_badge(tier):
    colors = {
        "A_mlb_reject": ("#c0392b","#fdf2f2","MLB 실패 확인"),
        "A_dfa_milb":   ("#d35400","#fef5ec","DFA (MiLB 주력)"),
        "B_fa_veteran": ("#2980b9","#eaf4fb","FA 베테랑"),
        "B_fa_mid":     ("#2980b9","#eaf4fb","FA 중견"),
        "C_outrighted": ("#7f8c8d","#f2f3f4","Outrighted"),
    }
    bg_text, bg_light, label = colors.get(tier, ("#555","#eee", tier))
    return f'<span class="badge" style="background:{bg_light};color:{bg_text};border:1px solid {bg_text}">{label}</span>'

def success_badge(cat):
    if cat == "strong_success_likely":
        return '<span class="badge" style="background:#eafaf1;color:#1e8449;border:1px solid #1e8449">강한 성공 예상</span>'
    if cat == "success_likely":
        return '<span class="badge" style="background:#eaf4fb;color:#1a5276;border:1px solid #1a5276">성공 예상</span>'
    if cat == "borderline":
        return '<span class="badge" style="background:#fef9e7;color:#9a7d0a;border:1px solid #9a7d0a">경계선</span>'
    return '<span class="badge" style="background:#fdf2f2;color:#c0392b;border:1px solid #c0392b">실패 위험</span>'

def warn(flags):
    if not flags or str(flags) in ("nan", "-"):
        return '<span style="color:#27ae60">✓ 없음</span>'
    items = str(flags).split("|")
    labels = {
        "PCL_inflation": "PCL 파크 인플레이션",
        "high_K_pct": "높은 K%",
        "small_sample_IP": "표본 이닝 부족",
        "high_BB9": "높은 BB9",
        "low_confidence": "번역 신뢰도 낮음",
        "no_savant": "Savant 데이터 없음",
    }
    return " · ".join(f'<span style="color:#e67e22">⚠ {labels.get(i,i)}</span>' for i in items)

TOP3_H = hitters.head(3).reset_index(drop=True)
TOP3_S = starters.head(3).reset_index(drop=True)

MEDALS = ["🥇 1순위", "🥈 2순위", "🥉 3순위"]
MEDAL_COLORS = ["#f39c12", "#95a5a6", "#cd7f32"]

def hitter_card(i, r):
    medal_color = MEDAL_COLORS[i]
    return f"""
<div class="player-card">
  <div class="card-header" style="border-left: 6px solid {medal_color};">
    <div class="rank-label" style="color:{medal_color};">{MEDALS[i]}</div>
    <div class="player-name">{r['full_name']}</div>
    <div class="player-meta">{int(r['age'])}세 · {r['position']} · {r.get('bat_side','?')}타 &nbsp;
      {tier_badge(r['acquisition_tier'])} &nbsp; {success_badge(r['bt_success_category'])}
    </div>
    <div class="composite-score">종합 점수 <strong>{f(r['composite_score'])}</strong> / 1.000</div>
  </div>

  <div class="card-body">
    <div class="stat-grid">
      <div class="stat-group">
        <div class="stat-group-title">KBO 예상 성과</div>
        <div class="stat-row highlight">
          <span class="stat-label">KBO wRC+ 예상</span>
          <span class="stat-value big">{f(r['kbo_wrc_plus_final'],'.1f')}</span>
        </div>
        <div class="stat-row highlight">
          <span class="stat-label">KBO OPS 예상</span>
          <span class="stat-value big">{f(r['kbo_ops_final'])}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">SSG Fit 점수</span>
          <span class="stat-value">{f(r['ssg_fit_score'],'.0f')}pt</span>
        </div>
      </div>
      <div class="stat-group">
        <div class="stat-group-title">AAA 실적 (Savant 보정)</div>
        <div class="stat-row">
          <span class="stat-label">xwOBA (park-neutral)</span>
          <span class="stat-value">{f(r.get('xwoba',float('nan')))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">ISO (장타력)</span>
          <span class="stat-value">{f(r.get('iso',float('nan')))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">BB% (볼넷률)</span>
          <span class="stat-value">{pct(r.get('bb_pct',float('nan')))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">K% (삼진률)</span>
          <span class="stat-value">{pct(r.get('k_pct',float('nan')))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">chase% (존 밖 스윙)</span>
          <span class="stat-value">{pct(r.get('chase_pct',float('nan')))}</span>
        </div>
      </div>
    </div>
    <div class="warning-row">
      <span class="warn-label">경고 플래그</span> {warn(r.get('bt_warning_flags',''))}
    </div>
  </div>
</div>"""

def starter_card(i, r):
    medal_color = MEDAL_COLORS[i]
    return f"""
<div class="player-card">
  <div class="card-header" style="border-left: 6px solid {medal_color};">
    <div class="rank-label" style="color:{medal_color};">{MEDALS[i]}</div>
    <div class="player-name">{r['full_name']}</div>
    <div class="player-meta">{int(r['age'])}세 · {r.get('pitch_hand','?')}완 &nbsp;
      {tier_badge(r['acquisition_tier'])} &nbsp; {success_badge(r['bt_success_category'])}
    </div>
    <div class="composite-score">종합 점수 <strong>{f(r['composite_score'])}</strong> / 1.000</div>
  </div>

  <div class="card-body">
    <div class="stat-grid">
      <div class="stat-group">
        <div class="stat-group-title">KBO 예상 성과</div>
        <div class="stat-row highlight">
          <span class="stat-label">KBO ERA 예상</span>
          <span class="stat-value big">{f(r['kbo_era_final'])}</span>
        </div>
        <div class="stat-row highlight">
          <span class="stat-label">KBO ERA+ 예상</span>
          <span class="stat-value big">{f(r['kbo_era_plus_est'],'.0f')}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">SSG Fit 점수</span>
          <span class="stat-value">{f(r['ssg_fit_score'],'.0f')}pt</span>
        </div>
      </div>
      <div class="stat-group">
        <div class="stat-group-title">AAA 실적</div>
        <div class="stat-row">
          <span class="stat-label">BB9 (이닝당 볼넷)</span>
          <span class="stat-value">{f(r.get('bb9',float('nan')))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">K9 (이닝당 삼진)</span>
          <span class="stat-value">{f(r.get('k9',float('nan')))}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">평균 구속</span>
          <span class="stat-value">{f(r.get('avg_velo',float('nan')),'.1f')} mph</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">총 AAA 이닝</span>
          <span class="stat-value">{f(r.get('ip_total',float('nan')),'.1f')} IP</span>
        </div>
      </div>
    </div>
    <div class="warning-row">
      <span class="warn-label">경고 플래그</span> {warn(r.get('bt_warning_flags',''))}
    </div>
  </div>
</div>"""

HTML = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SSG Landers 외국인 선수 영입 분석 보고서 2026</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', 'Noto Sans KR', sans-serif;
    background: #f4f6f9;
    color: #2c3e50;
    font-size: 14px;
    line-height: 1.6;
  }}
  .page {{ max-width: 960px; margin: 0 auto; padding: 40px 24px; }}

  /* ── 표지 ── */
  .cover {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white;
    border-radius: 16px;
    padding: 60px 48px;
    margin-bottom: 40px;
    position: relative;
    overflow: hidden;
  }}
  .cover::before {{
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 250px; height: 250px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
  }}
  .cover .team-badge {{
    font-size: 11px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #e74c3c;
    font-weight: 700;
    margin-bottom: 16px;
  }}
  .cover h1 {{
    font-size: 28px;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 12px;
  }}
  .cover h2 {{
    font-size: 16px;
    font-weight: 400;
    color: rgba(255,255,255,0.7);
    margin-bottom: 32px;
  }}
  .cover .meta {{
    display: flex; gap: 32px; flex-wrap: wrap;
    border-top: 1px solid rgba(255,255,255,0.15);
    padding-top: 24px;
    font-size: 12px;
    color: rgba(255,255,255,0.6);
  }}
  .cover .meta strong {{ color: white; display: block; font-size: 13px; }}

  /* ── 섹션 ── */
  .section {{ margin-bottom: 48px; }}
  .section-title {{
    font-size: 18px;
    font-weight: 700;
    color: #1a1a2e;
    border-left: 4px solid #e74c3c;
    padding-left: 12px;
    margin-bottom: 20px;
  }}
  .section-subtitle {{
    font-size: 13px;
    color: #7f8c8d;
    margin-top: -14px;
    margin-bottom: 20px;
    padding-left: 16px;
  }}

  /* ── 요약 박스 ── */
  .summary-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 32px;
  }}
  .summary-box {{
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .summary-box .label {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #95a5a6;
    margin-bottom: 6px;
  }}
  .summary-box .value {{
    font-size: 22px;
    font-weight: 700;
    color: #1a1a2e;
  }}
  .summary-box .sub {{
    font-size: 12px;
    color: #7f8c8d;
    margin-top: 4px;
  }}

  /* ── 약점 테이블 ── */
  .weakness-table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    margin-bottom: 24px;
  }}
  .weakness-table th {{
    background: #1a1a2e;
    color: white;
    padding: 12px 16px;
    text-align: left;
    font-size: 12px;
    font-weight: 600;
  }}
  .weakness-table td {{
    padding: 11px 16px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 13px;
  }}
  .weakness-table tr:last-child td {{ border-bottom: none; }}
  .weakness-table tr:nth-child(even) {{ background: #fafafa; }}
  .rank-num {{ font-weight: 700; color: #e74c3c; }}

  /* ── 선수 카드 ── */
  .player-card {{
    background: white;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    overflow: hidden;
  }}
  .card-header {{
    padding: 20px 24px 16px;
    background: #fafbfc;
    border-bottom: 1px solid #eee;
  }}
  .rank-label {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }}
  .player-name {{
    font-size: 22px;
    font-weight: 700;
    color: #1a1a2e;
    margin-bottom: 8px;
  }}
  .player-meta {{
    font-size: 13px;
    color: #555;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }}
  .composite-score {{
    font-size: 12px;
    color: #7f8c8d;
  }}
  .composite-score strong {{ color: #1a1a2e; font-size: 16px; }}
  .card-body {{ padding: 20px 24px; }}
  .stat-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 16px;
  }}
  .stat-group-title {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #95a5a6;
    margin-bottom: 10px;
    font-weight: 600;
  }}
  .stat-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid #f5f5f5;
  }}
  .stat-row.highlight {{ background: #fff9f0; margin: 0 -8px; padding: 6px 8px; border-radius: 4px; border-bottom: none; margin-bottom: 4px; }}
  .stat-label {{ font-size: 12px; color: #7f8c8d; }}
  .stat-value {{ font-size: 13px; font-weight: 600; color: #2c3e50; }}
  .stat-value.big {{ font-size: 18px; font-weight: 700; color: #e74c3c; }}
  .warning-row {{
    padding: 10px 14px;
    background: #fafafa;
    border-radius: 6px;
    font-size: 12px;
    margin-top: 4px;
  }}
  .warn-label {{ color: #7f8c8d; margin-right: 8px; }}

  /* ── 배지 ── */
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
  }}

  /* ── 파이프라인 ── */
  .pipeline {{
    display: flex;
    gap: 0;
    margin-bottom: 28px;
    overflow-x: auto;
  }}
  .pipeline-step {{
    flex: 1;
    background: white;
    padding: 16px 14px;
    border-right: 1px solid #eee;
    min-width: 130px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }}
  .pipeline-step:first-child {{ border-radius: 10px 0 0 10px; }}
  .pipeline-step:last-child {{ border-radius: 0 10px 10px 0; border-right: none; }}
  .pipeline-step .step-num {{
    font-size: 10px;
    font-weight: 700;
    color: #e74c3c;
    text-transform: uppercase;
    letter-spacing: 1px;
  }}
  .pipeline-step .step-name {{
    font-size: 12px;
    font-weight: 600;
    margin: 4px 0 2px;
  }}
  .pipeline-step .step-desc {{
    font-size: 11px;
    color: #95a5a6;
  }}

  /* ── 역사 검증 ── */
  .validation-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }}
  .validation-card {{
    background: white;
    border-radius: 10px;
    padding: 18px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .validation-card .vc-title {{
    font-size: 12px;
    font-weight: 700;
    color: #555;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 2px solid #f0f0f0;
  }}
  .vc-row {{
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 12px;
  }}
  .vc-row .vc-label {{ color: #7f8c8d; }}
  .vc-row .vc-val {{ font-weight: 600; }}

  /* ── 한계 섹션 ── */
  .limit-list {{
    background: white;
    border-radius: 10px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .limit-item {{
    display: flex;
    gap: 12px;
    padding: 8px 0;
    border-bottom: 1px solid #f5f5f5;
    font-size: 13px;
  }}
  .limit-item:last-child {{ border-bottom: none; }}
  .limit-num {{
    min-width: 22px;
    height: 22px;
    background: #e74c3c;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    margin-top: 1px;
  }}
  .limit-text {{ color: #555; }}

  /* ── 최종 추천 배너 ── */
  .rec-banner {{
    background: linear-gradient(135deg, #1a1a2e, #0f3460);
    color: white;
    border-radius: 14px;
    padding: 32px 36px;
    margin-top: 32px;
  }}
  .rec-banner h3 {{
    font-size: 13px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #e74c3c;
    margin-bottom: 16px;
  }}
  .rec-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }}
  .rec-item .rec-role {{
    font-size: 11px;
    color: rgba(255,255,255,0.5);
    margin-bottom: 4px;
  }}
  .rec-item .rec-name {{
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .rec-item .rec-stat {{
    font-size: 12px;
    color: rgba(255,255,255,0.7);
  }}
  .rec-item .rec-alt {{
    font-size: 11px;
    color: rgba(255,255,255,0.45);
    margin-top: 6px;
  }}

  /* ── 푸터 ── */
  .footer {{
    text-align: center;
    font-size: 11px;
    color: #aaa;
    margin-top: 48px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
  }}

  @media print {{
    body {{ background: white; font-size: 12px; }}
    .page {{ padding: 20px; }}
    .player-card {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<div class="page">

<!-- ══ 표지 ══ -->
<div class="cover">
  <div class="team-badge">SSG Landers · Scouting Intelligence</div>
  <h1>외국인 선수 영입 분석 보고서<br>2026 시즌 대응 스카우팅</h1>
  <h2>6단계 데이터 파이프라인 기반 후보 평가 및 최종 추천</h2>
  <div class="meta">
    <div><strong>작성일</strong>{today}</div>
    <div><strong>데이터 기준</strong>2026년 6월 12일 스냅샷</div>
    <div><strong>대상 포지션</strong>외국인 타자 1명 · 외국인 선발 1명</div>
    <div><strong>후보 풀</strong>타자 28명 / 선발 21명 (A/B/C 등급)</div>
    <div><strong>브랜치</strong>sewon @ jameshui0228/kbo-foreign-player-recruitment</div>
  </div>
</div>

<!-- ══ 분석 방법론 ══ -->
<div class="section">
  <div class="section-title">분석 방법론</div>
  <div class="section-subtitle">SSG 특유의 환경(문학구장·KBO ABS·팀 약점)을 반영한 6단계 스카우팅 파이프라인</div>
  <div class="pipeline">
    <div class="pipeline-step">
      <div class="step-num">Stage 1</div>
      <div class="step-name">SSG 약점 분석</div>
      <div class="step-desc">STATIZ 2026 상황별 타격 분석</div>
    </div>
    <div class="pipeline-step">
      <div class="step-num">Stage 2</div>
      <div class="step-name">KBO 아키타입</div>
      <div class="step-desc">역사적 외국인 선수 성공 패턴 추출</div>
    </div>
    <div class="pipeline-step">
      <div class="step-num">Stage 3</div>
      <div class="step-name">후보 시장</div>
      <div class="step-desc">DFA·FA·Outrighted 558명 스크리닝</div>
    </div>
    <div class="pipeline-step">
      <div class="step-num">Stage 4</div>
      <div class="step-name">KBO 번역</div>
      <div class="step-desc">PCL 파크팩터 + 리그팩터 보정</div>
    </div>
    <div class="pipeline-step">
      <div class="step-num">Stage 5</div>
      <div class="step-name">백테스트</div>
      <div class="step-desc">42타자·86선발 KBO 실적 검증</div>
    </div>
    <div class="pipeline-step">
      <div class="step-num">Stage 6</div>
      <div class="step-name">최종 랭킹</div>
      <div class="step-desc">SSG Fit 40% + KBO 성과 40% + 등급 20%</div>
    </div>
  </div>
</div>

<!-- ══ SSG 약점 요약 ══ -->
<div class="section">
  <div class="section-title">SSG Landers 2026 핵심 약점</div>
  <table class="weakness-table">
    <thead>
      <tr>
        <th>약점 항목</th>
        <th>리그 순위</th>
        <th>구체 지표</th>
        <th>요구 능력</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>1루 주자 상황 OPS</strong></td>
        <td><span class="rank-num">10위</span> (최하위)</td>
        <td>주자 진루 실패 — 진타 및 볼넷 부재</td>
        <td>갭 장타력 + BB% 높은 타자</td>
      </tr>
      <tr>
        <td><strong>초반(1~3이닝) OPS</strong></td>
        <td><span class="rank-num">8위</span></td>
        <td>상대 선발 조기 공략 실패</td>
        <td>초반 장악 가능한 선발 투수</td>
      </tr>
      <tr>
        <td><strong>2사 OPS</strong></td>
        <td><span class="rank-num">8위</span></td>
        <td>2아웃 상황 득점 생산 부재</td>
        <td>chase율 낮은 타자 (ABS 적응)</td>
      </tr>
      <tr>
        <td><strong>문학 홈/원정 OPS 차이</strong></td>
        <td>홈 +0.035</td>
        <td>좁은 파울 존 · 바람 영향</td>
        <td>갭 파워형 타자 선호</td>
      </tr>
    </tbody>
  </table>
</div>

<!-- ══ 역사적 검증 기준 ══ -->
<div class="section">
  <div class="section-title">역사적 성공 기준 (5단계 백테스트)</div>
  <div class="validation-grid">
    <div class="validation-card">
      <div class="vc-title">KBO 외국인 타자 — 42명 샘플 (2023~2025)</div>
      <div class="vc-row"><span class="vc-label">성공 기준</span><span class="vc-val">wRC+ ≥ 100</span></div>
      <div class="vc-row"><span class="vc-label">역사적 성공률</span><span class="vc-val">79%</span></div>
      <div class="vc-row"><span class="vc-label">성공군 평균 wRC+</span><span class="vc-val">137.3</span></div>
      <div class="vc-row"><span class="vc-label">실패군 평균 wRC+</span><span class="vc-val">96.0</span></div>
      <div class="vc-row"><span class="vc-label">SSG 에레디아 실적</span><span class="vc-val">135 → 137 → 141 (3년)</span></div>
    </div>
    <div class="validation-card">
      <div class="vc-title">KBO 외국인 선발 — 86명 샘플 (2023~2025)</div>
      <div class="vc-row"><span class="vc-label">성공 기준</span><span class="vc-val">ERA ≤ 4.00</span></div>
      <div class="vc-row"><span class="vc-label">역사적 성공률</span><span class="vc-val">57%</span></div>
      <div class="vc-row"><span class="vc-label">성공군 평균 ERA</span><span class="vc-val">3.26</span></div>
      <div class="vc-row"><span class="vc-label">성공군 평균 이닝</span><span class="vc-val">149.1 IP</span></div>
      <div class="vc-row"><span class="vc-label">SSG 앤더슨/화이트 실적</span><span class="vc-val">ERA 2.25 / 2.87 (2025)</span></div>
    </div>
  </div>
</div>

<!-- ══ 외국인 타자 추천 ══ -->
<div class="section">
  <div class="section-title">외국인 타자 추천 (상위 3순위)</div>
  <div class="section-subtitle">종합점수 = SSG Fit 40% + KBO wRC+ 예상 40% + 영입 등급 20%</div>
  {''.join(hitter_card(i, TOP3_H.iloc[i]) for i in range(3))}
</div>

<!-- ══ 외국인 선발 추천 ══ -->
<div class="section">
  <div class="section-title">외국인 선발 추천 (상위 3순위)</div>
  <div class="section-subtitle">종합점수 = SSG Fit 40% + KBO ERA 예상 40% + 영입 등급 20%</div>
  {''.join(starter_card(i, TOP3_S.iloc[i]) for i in range(3))}
</div>

<!-- ══ 최종 추천 ══ -->
<div class="rec-banner">
  <h3>★ 최종 추천 요약</h3>
  <div class="rec-grid">
    <div class="rec-item">
      <div class="rec-role">외국인 타자</div>
      <div class="rec-name">Weston Wilson</div>
      <div class="rec-stat">KBO wRC+ 예상 145 · xwOBA .442 · SSG Fit 80pt</div>
      <div class="rec-alt">대안: Jack Suwinski (chase율 19.1%, ABS 최적)</div>
    </div>
    <div class="rec-item">
      <div class="rec-role">외국인 선발</div>
      <div class="rec-name">Brian Van Belle</div>
      <div class="rec-stat">KBO ERA 예상 3.64 · BB9 2.2 · SSG Fit 77pt</div>
      <div class="rec-alt">대안: Carson Spiers (ERA 예상 3.20, 표본 주의)</div>
    </div>
  </div>
</div>

<!-- ══ 모델 한계 ══ -->
<div class="section" style="margin-top:40px;">
  <div class="section-title">모델 한계 및 주의사항</div>
  <div class="limit-list">
    <div class="limit-item">
      <div class="limit-num">1</div>
      <div class="limit-text"><strong>표본 크기</strong> — Carson Spiers 63이닝 등 일부 선수는 통계 불안정. 최근 AAA 성적 추이 수동 확인 필요.</div>
    </div>
    <div class="limit-item">
      <div class="limit-num">2</div>
      <div class="limit-text"><strong>PCL 파크 인플레이션</strong> — Savant xwOBA로 1차 보정하나, park-neutral 데이터 없는 선수는 OPS 할인(÷1.04~1.10) 후 추정.</div>
    </div>
    <div class="limit-item">
      <div class="limit-num">3</div>
      <div class="limit-text"><strong>KBO 적응 요인 미반영</strong> — 언어·문화·이동 피로·구질 적응 등 비정량 변수는 본 모델 범위 밖.</div>
    </div>
    <div class="limit-item">
      <div class="limit-num">4</div>
      <div class="limit-text"><strong>부상 이력 미포함</strong> — MLB 의료기록·DL 내역은 별도 스크리닝 필요.</div>
    </div>
    <div class="limit-item">
      <div class="limit-num">5</div>
      <div class="limit-text"><strong>계약 가능성</strong> — 에이전트 협상 의향, 연봉 요구 수준은 실시간 확인 필요. A_dfa_milb 등급은 협상이 상대적으로 유리.</div>
    </div>
  </div>
</div>

<div class="footer">
  SSG Landers Foreign Player Recruitment Analysis · sewon branch ·
  jameshui0228/kbo-foreign-player-recruitment · {today}
</div>

</div>
</body>
</html>"""

out_path = REPORT_DIR / "ssg_foreign_player_report_2026.html"
out_path.write_text(HTML, encoding="utf-8")
print(f"보고서 생성 완료: {out_path}")
