from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "SSG_발표_핵심_인사이트_치트시트.pdf"
FONT_PATH = Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf")


def register_fonts():
    pdfmetrics.registerFont(TTFont("KR", str(FONT_PATH)))
    pdfmetrics.registerFont(TTFont("KRB", str(FONT_PATH)))


def styles():
    base = getSampleStyleSheet()
    for style in base.byName.values():
        style.fontName = "KR"

    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="KRB",
            fontSize=24,
            leading=31,
            textColor=colors.HexColor("#242424"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName="KR",
            fontSize=10.5,
            leading=16,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="KRB",
            fontSize=17,
            leading=22,
            textColor=colors.HexColor("#9B0F1D"),
            spaceBefore=8,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="KRB",
            fontSize=12.5,
            leading=17,
            textColor=colors.HexColor("#1F5D72"),
            spaceBefore=6,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="KR",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#242424"),
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName="KR",
            fontSize=8.2,
            leading=11.5,
            textColor=colors.HexColor("#555555"),
            spaceAfter=2,
        ),
        "note": ParagraphStyle(
            "note",
            parent=base["BodyText"],
            fontName="KR",
            fontSize=8.8,
            leading=12.5,
            textColor=colors.HexColor("#555555"),
            backColor=colors.HexColor("#F6F4F0"),
            borderColor=colors.HexColor("#D8D5CF"),
            borderWidth=0.6,
            borderPadding=7,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "quote": ParagraphStyle(
            "quote",
            parent=base["BodyText"],
            fontName="KRB",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#9B0F1D"),
            backColor=colors.HexColor("#FFF7F7"),
            borderColor=colors.HexColor("#E6B5B8"),
            borderWidth=0.7,
            borderPadding=8,
            spaceBefore=5,
            spaceAfter=8,
        ),
        "center": ParagraphStyle(
            "center",
            parent=base["BodyText"],
            fontName="KR",
            fontSize=9.3,
            leading=13,
            alignment=TA_CENTER,
        ),
    }


def p(text, style):
    return Paragraph(text, style)


def bullets(items, st, bullet_color="#9B0F1D"):
    return ListFlowable(
        [
            ListItem(
                p(item, st["body"]),
                bulletColor=colors.HexColor(bullet_color),
                leftIndent=10,
            )
            for item in items
        ],
        bulletType="bullet",
        start="bulletchar",
        bulletFontName="KR",
        bulletFontSize=7,
        leftIndent=14,
        bulletOffsetY=1,
        spaceBefore=1,
        spaceAfter=4,
    )


def table(data, widths, header=True, font_size=8.5, leading=11.3):
    st = styles()
    rows = [[p(str(cell), ParagraphStyle("cell", parent=st["small"], fontSize=font_size, leading=leading)) for cell in row] for row in data]
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "KR"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6D3CD")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F0EEE9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#242424")),
            ("FONTNAME", (0, 0), (-1, 0), "KRB"),
        ]
    for r in range(1 if header else 0, len(data)):
        if r % 2 == 0:
            style.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#FBFAF7")))
    t.setStyle(TableStyle(style))
    return t


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("KR", 7.5)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(18 * mm, 10 * mm, "SSG 외국인 타자/선발투수 영입 제안 - 발표 핵심 인사이트 치트시트")
    canvas.drawRightString(192 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def make_doc():
    register_fonts()
    st = styles()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=17 * mm,
        rightMargin=17 * mm,
        topMargin=15 * mm,
        bottomMargin=17 * mm,
        title="SSG 발표 핵심 인사이트 치트시트",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=footer)])

    story = []
    story += [
        Spacer(1, 16 * mm),
        p("SSG 랜더스 외국인 타자 · 선발투수 영입 제안", st["title"]),
        p("발표자가 꼭 기억해야 할 핵심 인사이트, 근거, 예상 질문 답변", st["subtitle"]),
        p(
            "핵심 한 줄: 우리는 가장 유명하거나 점수가 높은 선수가 아니라, SSG의 실제 약점을 메우면서 지금 시장에서 접촉 가능한 선수를 찾았다.",
            st["quote"],
        ),
        p("최종 결론", st["h1"]),
        table(
            [
                ["슬롯", "최종 접촉 1순위", "왜 이 선수인가"],
                [
                    "외국인 타자",
                    "Will Brennan",
                    "DFA/outright 이후 40인 로스터 밖. contact-floor형 외야수로 SSG의 run-kill 및 이닝 단절 약점을 줄이는 유형.",
                ],
                [
                    "외국인 선발",
                    "Josh Fleming",
                    "40인 로스터 밖, AAA 선발 load 보유. BB/9 1.36, HR/9 0.51로 traffic-command starter 조건에 가장 근접.",
                ],
            ],
            [28 * mm, 35 * mm, 102 * mm],
        ),
        Spacer(1, 7),
        p("발표에서 계속 반복할 문장", st["h2"]),
        bullets(
            [
                "좋은 선수와 데려올 수 있는 좋은 선수는 다르다.",
                "타자는 이닝을 다시 여는 contact-floor OF, 투수는 주자 출루 이후 무너지지 않는 traffic-command starter가 필요하다.",
                "Raw Ranking은 야구적 적합성, Final Ranking은 접촉 가능성·비용·40인 여부·메디컬까지 반영한 실제 우선순위다.",
            ],
            st,
        ),
        PageBreak(),
    ]

    story += [
        p("1. 프로젝트 프레임", st["h1"]),
        p("왜 SSG인가", st["h2"]),
        bullets(
            [
                "SSG는 긴 연패, 하위권 순위, 외국인 타자/선발 슬롯 불안이 동시에 나타난 팀이다.",
                "따라서 목표는 단순한 후보 추천이 아니라, 즉시 접촉 가능한 대체 외국인 타자와 선발투수를 찾는 것이다.",
                "발표의 차별점은 선수 이름보다 의사결정 구조다. 팀 약점, KBO 적응, 시장 접근성, 의료/계약 리스크를 함께 본다.",
            ],
            st,
        ),
        p("Research Question", st["h2"]),
        table(
            [
                ["RQ", "질문", "발표 답변"],
                ["RQ1", "SSG의 숨은 약점은 무엇인가?", "타선은 이닝 단절과 run-kill, 선발은 traffic damage와 5이닝 안정성이 핵심이다."],
                ["RQ2", "어떤 외국인 선수가 맞는가?", "타자는 이닝 전환형 OF/DH, 투수는 traffic-command starter가 맞다."],
                ["RQ3", "누구를 먼저 접촉해야 하는가?", "타자 Will Brennan, 투수 Josh Fleming이 최종 접촉 1순위다."],
            ],
            [20 * mm, 60 * mm, 85 * mm],
        ),
        p("데이터 소스", st["h2"]),
        bullets(
            [
                "KBO/STATIZ 2023-2026 SSG 상황별 경기 데이터: 팀 약점과 game-state interaction 마이닝에 사용.",
                "MLB Savant 2023-2026: 타자 contact, chase, hard-hit, xwOBA 등 KBO 번역 가능 feature 구성.",
                "MiLB AAA/AA 성적: 투수 IP, GS, K/9, BB/9, HR/9, ERA, WHIP 등 선발 지속성과 damage-control 진단.",
                "Roster/Transaction 데이터: DFA, outright, selected contract, trade, minor contract, 40인 여부 확인.",
                "Public salary/contract/medical signal: 연봉 부담, 권리 상태, 부상/역할 가능성 gate 보정.",
                "중요: 최종 모델 입력에는 기사/인터뷰 같은 텍스트 변수를 넣지 않고, 숫자형 structured data와 구조화된 상태 변수만 사용했다.",
            ],
            st,
        ),
        p("<b>발표 문장</b><br/>저희는 감으로 후보를 뽑은 것이 아니라, SSG 경기 데이터와 미국 선수 데이터를 구조화해 팀 약점과 시장 접근성을 동시에 통과한 후보를 찾았습니다.", st["quote"]),
        PageBreak(),
    ]

    story += [
        p("2. SSG 약점 마이닝", st["h1"]),
        p("타선: 단순 장타 부족이 아니라 이닝 단절", st["h2"]),
        table(
            [
                ["마이닝 신호", "의미", "평균 득실"],
                ["RHP game-script lock", "우완 선발 상대에서 OF/DH가 흐름을 다시 열지 못하는 경기", "-5.10"],
                ["Run-kill avoidance", "병살, 도루자, 삼진 등으로 득점 흐름이 닫히는 경기", "-5.11"],
                ["Extra-out resilience", "실책/추가 출루 이후 복구하지 못하는 경기", "-4.50"],
                ["Starter length support", "선발이 짧게 내려간 날 타선이 반격을 만들지 못하는 경기", "-5.83"],
            ],
            [43 * mm, 92 * mm, 30 * mm],
        ),
        p(
            "해석: SSG는 홈런 하나가 부족한 팀이라기보다, 주자가 나간 뒤 다음 타자가 이닝을 이어가지 못하고 경기 흐름이 닫히는 구간에서 크게 무너진다.",
            st["note"],
        ),
        p("필요한 타자 유형", st["h2"]),
        bullets(
            [
                "이닝 전환형 OF/DH: 끊긴 흐름을 다시 여는 선수.",
                "vs RHP 출루와 장타: 우투수 상대 game-script를 풀어줄 능력.",
                "contact floor와 two-strike 생존력: 삼진으로 이닝을 쉽게 닫지 않는 능력.",
                "낮은 run-kill 위험: 병살, chase, weak contact 리스크를 줄이는 선수.",
            ],
            st,
        ),
        p("<b>발표 문장</b><br/>SSG의 문제는 단순히 타격이 약하다는 것이 아니라, 특정 흐름에서 이닝이 닫히는 구조적 약점입니다. 그래서 저희는 거포보다 이닝을 다시 여는 외야수를 찾았습니다.", st["quote"]),
        PageBreak(),
    ]

    story += [
        p("3. 선발 약점과 필요한 투수상", st["h1"]),
        p("선발: traffic 관리 실패", st["h2"]),
        bullets(
            [
                "핵심은 구위 자체보다 주자를 내보낸 이후 피해를 얼마나 억제하느냐다.",
                "볼넷 뒤 장타, 5이닝 미달, 선발 조기 강판이 팀 흐름을 크게 흔든다.",
                "ABS 환경에서는 존 주변 제구가 무너지지 않는 선발이 더 중요하다.",
            ],
            st,
        ),
        p("필요한 투수 유형: traffic-command starter", st["h2"]),
        table(
            [
                ["조건", "보는 지표", "해석"],
                ["Free-pass control", "BB/9, walk volatility", "볼넷으로 위기를 키우지 않는가"],
                ["Damage control", "HR/9, extra-base hit risk", "주자 출루 이후 장타 피해를 줄이는가"],
                ["Starter floor", "IP, GS, 5-inning floor", "5-6이닝을 반복적으로 맡길 수 있는가"],
                ["Role access", "SP/Swing, recent load", "현재 선발 빌드업이 되어 있는가"],
            ],
            [38 * mm, 52 * mm, 75 * mm],
        ),
        p("<b>발표 문장</b><br/>SSG에 필요한 선발은 삼진 쇼케이스형 에이스가 아니라, 주자가 나가도 5-6이닝을 버티는 traffic-command starter입니다.", st["quote"]),
        p("주의할 말", st["h2"]),
        bullets(
            [
                "'탈삼진은 많은데'라고 단정하지 말 것. 대본에서는 '주자를 내보낸 이후 피해 억제가 약하다'가 더 안전하다.",
                "투수 classifier는 신뢰도가 낮으므로, 투수는 예측확률보다 BB/9, HR/9, starter load, 계약/메디컬 gate 중심으로 설명한다.",
            ],
            st,
        ),
        PageBreak(),
    ]

    story += [
        p("4. 모델 구조", st["h1"]),
        p("6개 모델은 서로 다른 질문에 답한다", st["h2"]),
        table(
            [
                ["모델", "질문", "발표 설명"],
                ["A Team Need", "SSG 약점과 맞는가?", "SSG 약점을 feature contract로 바꾸고 후보 feature와 매칭."],
                ["B KBO History", "과거 KBO 성공/실패와 닮았는가?", "과거 외국인 선수의 pre-KBO 패턴과 유사도/경고 신호 확인."],
                ["C Archetype", "KBO 성공 유형인가?", "KBO에서 통했던 역할 유형과 후보 역할의 유사성 평가."],
                ["D Translation", "미국 성적이 KBO에서 유지될까?", "Savant/MiLB 지표가 KBO 환경에서 붕괴될 위험 진단."],
                ["E Market", "실제로 데려올 수 있나?", "40인 여부, DFA/outright, salary, 권리 상태, 최근 거래 확인."],
                ["F Medical", "몸 상태와 역할이 가능한가?", "부상 이력, 선발 빌드업, 역할 수용 가능성 점검."],
            ],
            [27 * mm, 55 * mm, 83 * mm],
            font_size=8.1,
            leading=10.8,
        ),
        p("Raw Ranking vs Final Ranking", st["h2"]),
        bullets(
            [
                "Raw Ranking: A-D 중심으로 야구적 적합성과 데이터마이닝 신호를 본 순위.",
                "Final Ranking: Raw Ranking에 E-F gate, 즉 시장 접근성·비용·40인 여부·메디컬을 반영한 최종 접촉 순위.",
                "따라서 Matos와 Jones가 내려가고 Brennan이 올라온 것은 모델이 흔들린 것이 아니라, 실행 가능성을 반영한 결과다.",
            ],
            st,
        ),
        p("모델 신뢰도", st["h2"]),
        table(
            [
                ["슬롯", "검증 결과", "의사결정 방식"],
                ["타자", "Success AUC 0.833, Failure AUC 0.738", "후보 간 우선순위 신호로 강하게 반영."],
                ["투수", "Diagnostic AUC 0.603, 표본 49건", "확정 추천이 아니라 진단 지표와 gate를 보수적으로 결합."],
            ],
            [28 * mm, 65 * mm, 72 * mm],
        ),
        p("<b>발표 문장</b><br/>저희는 모델을 절대 성공확률로 쓰지 않았습니다. 타자는 후보 간 분리 신호로 활용했고, 투수는 classifier 신뢰도가 낮아 진단 지표와 실행 gate를 더 강하게 반영했습니다.", st["quote"]),
        PageBreak(),
    ]

    story += [
        p("5. 후보 선정 과정", st["h1"]),
        p("Step별 의미", st["h2"]),
        table(
            [
                ["Step", "숫자", "무슨 단계인가", "발표 포인트"],
                ["1", "736 / 1,009", "타자 736명, 투수 1,009명 전체 구조화 시장", "처음부터 Top 후보만 본 게 아니라 넓은 시장에서 출발."],
                ["2", "16 / 18", "후보 생성 모듈. 하나라도 강한 신호가 있으면 살리는 OR-screen", "발견 단계라 넓게 잡음."],
                ["3", "6 / 3", "1차 검증 통과. 여러 조건을 동시에 통과해야 하는 AND-gate", "투수는 모델 신뢰도가 낮아 더 보수적으로 좁힘."],
                ["4", "Top 3", "Raw Ranking. 야구적/모델 적합성 기준 상위권", "좋은 선수 순위."],
                ["5", "Top 3", "Final Ranking. 시장, 비용, 40인, 메디컬 반영", "데려올 수 있는 좋은 선수 순위."],
            ],
            [15 * mm, 26 * mm, 70 * mm, 54 * mm],
            font_size=7.7,
            leading=10.3,
        ),
        p("Step 2와 Step 3의 차이", st["h2"]),
        bullets(
            [
                "Step 2는 '발견'이다. 한 모델에서라도 강한 신호가 있으면 후보로 남긴다.",
                "Step 3는 '검증'이다. SSG fit, KBO translation, 시장 접근성, 리스크가 함께 맞아야 남긴다.",
                "그래서 타자는 6명, 투수는 3명만 남는다. 특히 투수는 classifier 신뢰도가 낮아 더 엄격하게 처리했다.",
            ],
            st,
        ),
        p("<b>발표 문장</b><br/>Step 2는 넓게 찾는 단계이고, Step 3는 실제 후보로 세울 수 있는지를 검증하는 단계입니다. 그래서 Step 2의 16/18명은 후보군이고, Step 3의 6/3명은 검증을 통과한 핵심 후보입니다.", st["quote"]),
        PageBreak(),
    ]

    story += [
        p("6. 현실성 반영 Gate", st["h1"]),
        p("현실성은 감이 아니라 구조화된 실행 변수다", st["h2"]),
        table(
            [
                ["Gate", "무엇을 봤나", "왜 중요한가"],
                ["40인 로스터", "40-man 여부, selected contract", "구단 통제력이 강하면 KBO가 바로 데려오기 어렵다."],
                ["최근 트랜잭션", "DFA, outright, release, minor contract, trade", "DFA/outright는 접근성 상승, selected/trade 직후는 접근성 하락."],
                ["나이와 MLB 잔류 가치", "age, MLB reset value", "너무 어린 선수는 KBO행보다 MLB 재도전 가능성이 크다."],
                ["연봉·권리·비용", "salary signal, cash trade, rights", "대체 외국인은 비용과 권리 구조가 현실적이어야 한다."],
                ["메디컬·역할", "부상 이력, 선발 load, 역할 적합성", "몸 상태와 역할 수용 가능성이 안 맞으면 실행 불가능하다."],
            ],
            [34 * mm, 54 * mm, 77 * mm],
            font_size=8.1,
            leading=10.8,
        ),
        p("대표 보류 사례", st["h2"]),
        table(
            [
                ["선수", "초기 신호", "왜 Final에서 내려갔나"],
                ["Luis Matos", "low-K contact floor, 강한 발견 신호", "24세라 MLB 재도전 가치가 커서 HOLD."],
                ["Nolan Jones", "power/OBP, hard-hit 신호", "cash trade와 salary signal 때문에 COST HOLD."],
                ["Bryse Wilson", "투수 진단 모델상 backup 후보", "6/18 selected contract 이후 40인/MLB 장벽이 생겨 CONTRACT HOLD."],
                ["Jack Suwinski", "BB/barrel upside", "K%와 실패 경고가 SSG run-kill 회피 조건과 충돌."],
            ],
            [30 * mm, 58 * mm, 77 * mm],
            font_size=8.1,
            leading=10.8,
        ),
        p("<b>Selected contract 뜻</b><br/>마이너 계약 상태의 선수를 구단이 40인 로스터/MLB 쪽으로 올리는 절차다. 즉 '아직 우리 팀이 쓸 생각이 있다'는 신호이므로, KBO 구단 입장에서는 바로 빼오기 어렵다.", st["note"]),
        p("<b>발표 문장</b><br/>현실성은 느낌이 아니라 40인 여부, 최근 트랜잭션, 나이, 연봉/권리, 메디컬을 구조화한 gate입니다. 그래서 모델상 좋은 선수라도 지금 데려오기 어려우면 보류했습니다.", st["quote"]),
        PageBreak(),
    ]

    story += [
        p("7. 최종 후보와 말할 근거", st["h1"]),
        p("타자 최종 후보", st["h2"]),
        table(
            [
                ["순위", "선수", "핵심 근거", "확인 필요"],
                ["1", "Will Brennan", "DFA/outright, 40인 밖, contact-floor OF, SSG run-kill 완화 유형", "메디컬, KBO행 의사, 권리 조건"],
                ["2", "Dominic Fletcher", "non-40man/minor contract, 좌타 OF, 구조화 모델과 독립 후보 신호 교차", "장타 ceiling 낮음, 계약 조건"],
                ["3", "Dylan Carlson", "27세 switch-hitting OF, DFA/outright 이력, platoon/OF depth 안정화", "최근 소속권, opt-out/release 조건"],
            ],
            [15 * mm, 34 * mm, 82 * mm, 34 * mm],
            font_size=7.8,
            leading=10.4,
        ),
        p("투수 최종 후보", st["h2"]),
        table(
            [
                ["순위", "선수", "핵심 근거", "확인 필요"],
                ["1", "Josh Fleming", "LHP SP/Swing, non-40man, 53.0 IP/10 GS, BB/9 1.36, HR/9 0.51", "구속, 구종 품질, 최근 선발 빌드업, availability"],
                ["2", "Keegan Thompson", "recent DFA/outright, starter load, HR/9 0.56, 시장 접근성 강함", "K/9 5.29로 헛스윙 ceiling 낮음"],
                ["3", "Kolby Allard", "LHP, repeated DFA/outright/minor deal, HR/9 0.36, 선발 표본", "BB/9 3.20, 최근 소속권"],
            ],
            [15 * mm, 34 * mm, 82 * mm, 34 * mm],
            font_size=7.8,
            leading=10.4,
        ),
        p("최종 1순위 설명", st["h2"]),
        bullets(
            [
                "Will Brennan: SSG가 원하는 '이닝을 닫지 않는 외야수'에 가장 가까우며, 시장 접근성도 높다.",
                "Josh Fleming: 압도적 구위형은 아니지만, SSG가 필요한 볼넷 억제와 장타 피해 억제형 선발에 가장 가깝다.",
            ],
            st,
        ),
        p("<b>발표 문장</b><br/>Brennan은 SSG의 이닝 단절 문제를 줄일 타자이고, Fleming은 주자 출루 이후 무너지는 선발 문제를 줄일 투수입니다.", st["quote"]),
        PageBreak(),
    ]

    story += [
        p("8. 예상 질문 답변", st["h1"]),
        table(
            [
                ["질문", "짧은 답변"],
                [
                    "왜 Matos가 아니라 Brennan인가?",
                    "Matos는 contact floor가 좋아 Raw/discovery 단계에서는 강했지만 24세라 MLB 재도전 가치가 큽니다. Brennan은 28세, DFA/outright, 40인 밖이라 실제 접촉 가능성이 더 높습니다.",
                ],
                [
                    "Nolan Jones는 왜 보류인가?",
                    "power/OBP 신호는 강하지만 cash trade와 salary signal 때문에 비용/권리 조건이 풀리기 전까지는 COST HOLD가 맞습니다.",
                ],
                [
                    "Bryse Wilson의 selected contract HOLD는?",
                    "마이너 선수를 구단이 40인/MLB 쪽으로 올린 상태라 현재 구단 통제력이 강해졌다는 뜻입니다. 능력 부족이 아니라 계약 접근성 문제로 보류했습니다.",
                ],
                [
                    "투수 후보가 왜 3명밖에 안 남았나?",
                    "투수 성공/실패 classifier 신뢰도가 낮아 Step 3에서 더 보수적으로 gate를 걸었습니다. 그래서 확정 예측보다 BB/9, HR/9, starter floor, 계약/메디컬을 더 중시했습니다.",
                ],
                [
                    "모델이 과적합 아닌가?",
                    "그래서 확률을 절대값으로 말하지 않고, 후보 간 우선순위 신호로만 사용했습니다. 최종 검증에서도 과도한 성공확률 표현을 제거했습니다.",
                ],
                [
                    "기사나 인터뷰는 모델에 넣었나?",
                    "최종 모델 입력에는 넣지 않았습니다. 발표/맥락 설명에는 참고할 수 있지만, 모델은 숫자형 structured data와 구조화된 상태 변수 중심입니다.",
                ],
                [
                    "연봉 데이터는 반영했나?",
                    "정확한 계약 세부가 모두 공개된 것은 아니지만, salary signal, cash trade, 권리 상태, minor contract 여부를 market gate에 반영했습니다.",
                ],
            ],
            [50 * mm, 115 * mm],
            font_size=7.8,
            leading=10.6,
        ),
        p("교수님 질문을 받을 때의 태도", st["h2"]),
        bullets(
            [
                "과장하지 않는다. 특히 투수 모델은 diagnostic이라고 먼저 말한다.",
                "확률을 성공 보장처럼 말하지 않는다. '후보 간 분리 신호'라고 말한다.",
                "후보가 바뀐 이유를 숨기지 않는다. Raw와 Final을 나눠 설명하면 오히려 분석이 단단해 보인다.",
                "마지막에는 항상 SSG 약점으로 돌아온다. 후보 이름보다 '왜 SSG에 맞는가'가 핵심이다.",
            ],
            st,
        ),
        PageBreak(),
    ]

    story += [
        p("9. 발표자가 외울 최종 스크립트", st["h1"]),
        p("30초 요약", st["h2"]),
        p(
            "저희 분석의 결론은 단순합니다. SSG는 유명한 선수가 아니라, 팀 약점에 정확히 맞고 실제로 데려올 수 있는 선수가 필요합니다. "
            "타선은 장타 부족보다 이닝 단절과 run-kill이 문제였고, 선발은 구위보다 주자 출루 이후 피해 억제가 중요했습니다. "
            "그래서 타자는 contact-floor형 외야수 Will Brennan, 투수는 traffic-command starter Josh Fleming을 최종 접촉 1순위로 제안합니다.",
            st["quote"],
        ),
        p("슬라이드별 핵심 말", st["h2"]),
        table(
            [
                ["구간", "반드시 말할 문장"],
                ["왜 SSG인가", "지금 SSG는 즉시 전력 보강 압력이 크고, 외국인 슬롯 재검토 필요성이 분명한 팀입니다."],
                ["SSG 약점", "문제는 단순 장타 부족이 아니라 특정 경기 흐름에서 이닝이 닫히는 구조입니다."],
                ["선수상", "타자는 이닝 전환형 OF/DH, 투수는 traffic-command starter로 feature contract를 정의했습니다."],
                ["모델", "A-D는 야구적 적합성, E-F는 실제 영입 가능성을 검증하는 gate입니다."],
                ["Gate 결과", "좋은 선수와 데려올 수 있는 좋은 선수를 분리했기 때문에 Matos/Jones/Wilson은 보류됐습니다."],
                ["최종 후보", "Brennan과 Fleming은 SSG 약점, KBO 적응 가능성, 시장 접근성을 함께 통과한 현실형 접촉 1순위입니다."],
            ],
            [34 * mm, 131 * mm],
            font_size=8.2,
            leading=11,
        ),
        p("발표 전 마지막 체크", st["h2"]),
        bullets(
            [
                "최신 40인 로스터, DFA/outright, selected contract 여부는 발표 직전에 한 번 더 확인한다.",
                "Will Brennan과 Josh Fleming의 이름, 포지션, 핵심 수치만큼은 틀리지 않게 외운다.",
                "Matos/Jones/Wilson은 '탈락'이 아니라 '발견 신호는 있었지만 실행 gate에서 보류'라고 말한다.",
                "대본에서 '성공확률 90% 이상' 같은 표현은 쓰지 않는다.",
            ],
            st,
        ),
    ]

    doc.build(story)
    return OUT


if __name__ == "__main__":
    out = make_doc()
    print(out)
