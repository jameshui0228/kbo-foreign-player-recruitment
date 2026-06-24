import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT_DIR = "/Users/jameshui/CODEX/포트폴리오/SDA 2기 프로젝트_야구/kbo-foreign-player-recruitment/outputs/canva_supplement_pages";
const PPTX_OUT = path.join(OUT_DIR, "SSG_model_funnel_supplement_pages.pptx");

const W = 1600;
const H = 900;
const C = {
  bg: "#F7F8F6",
  ink: "#262321",
  mid: "#66635F",
  light: "#ECEDEA",
  line: "#D9D9D2",
  red: "#8C0E1A",
  red2: "#C9152B",
  redSoft: "#F6E7EA",
  blue: "#245C73",
  blueSoft: "#E7EFF2",
  white: "#FFFFFF",
};

function addShape(slide, geometry, left, top, width, height, fill = C.white, line = C.line, radius = "rounded-lg") {
  const spec = {
    geometry,
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: line, width: line === "none" ? 0 : 1 },
  };
  if (geometry === "roundRect") spec.borderRadius = radius;
  return slide.shapes.add(spec);
}

function addText(slide, text, left, top, width, height, opts = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: opts.size ?? 20,
    bold: opts.bold ?? false,
    color: opts.color ?? C.ink,
    fontFace: "Apple SD Gothic Neo",
    fit: "shrink",
  };
  return shape;
}

function header(slide, title, subtitle) {
  slide.background.fill = C.bg;
  addText(slide, title, 72, 54, 1100, 64, { size: 44, bold: true, color: C.ink });
  addShape(slide, "rect", 72, 124, 150, 7, C.red2, "none", "none");
  addText(slide, subtitle, 72, 158, 1220, 42, { size: 22, color: C.mid });
}

function sectionLabel(slide, label, left, top, color = C.red) {
  addText(slide, label, left, top, 48, 44, { size: 34, bold: true, color });
}

function card(slide, { left, top, width, height, label, title, body, color = C.red, fill = C.white }) {
  addShape(slide, "roundRect", left, top, width, height, fill, C.line, "rounded-xl");
  sectionLabel(slide, label, left + 26, top + 28, color);
  addText(slide, title, left + 96, top + 30, width - 122, 38, { size: 25, bold: true });
  addText(slide, body, left + 34, top + 88, width - 68, height - 106, { size: 15.6, color: C.mid });
}

function callout(slide, text, left, top, width, height, color = C.red) {
  addShape(slide, "roundRect", left, top, width, height, C.white, color, "rounded-lg");
  addText(slide, text, left + 18, top + 17, width - 36, height - 22, { size: 21, bold: true, color });
}

function miniTable(slide, left, top, width, rowH, headers, rows, opts = {}) {
  const cols = opts.cols ?? headers.map(() => 1 / headers.length);
  const colW = cols.map((v) => v * width);
  addShape(slide, "roundRect", left, top, width, rowH * (rows.length + 1), C.white, C.line, "rounded-lg");
  addShape(slide, "rect", left, top, width, rowH, opts.headerFill ?? C.light, "none", "none");
  let x = left;
  headers.forEach((h, i) => {
    addText(slide, h, x + 8, top + 10, colW[i] - 16, rowH - 14, { size: opts.headerSize ?? 14.5, bold: true });
    x += colW[i];
  });
  rows.forEach((row, r) => {
    const y = top + rowH * (r + 1);
    addShape(slide, "rect", left, y, width, 1, C.line, "none", "none");
    let xx = left;
    row.forEach((cell, i) => {
      if (i > 0) addShape(slide, "rect", xx, y, 1, rowH, C.line, "none", "none");
      addText(slide, String(cell), xx + 8, y + 9, colW[i] - 16, rowH - 12, { size: opts.size ?? 13.4, color: i === 0 && opts.firstRed ? C.red : C.ink, bold: i === 0 && opts.firstRed });
      xx += colW[i];
    });
  });
}

function slideModelABC(p) {
  const slide = p.slides.add();
  header(slide, "모델 상세 1: A/B/C", "SSG 약점 정의 → 과거 KBO 성공/실패 학습 → 역할 유사도 매칭");
  const w = 462, h = 432, gap = 38, y = 250;
  card(slide, {
    left: 72, top: y, width: w, height: h, label: "A", title: "Team Need Mining",
    body: "질문: SSG는 어떤 경기 조건에서 평균 득실과 승률이 급격히 나빠지는가?\n\n입력: KBO/STATIZ 2023-2026 SSG 상황별 성과, 상대 선발 유형, 주자 상황, 득실, 선발 이닝, 불펜 부담.\n\n방법: 단순 순위표가 아니라 game-state interaction을 조합해 hidden weakness rule을 mining.\n\n발견: RHP game-script lock(-5.10), RHP OF/DH run-kill(-5.11), extra-out high OF void(-4.50), top-opponent short start(-5.83).\n\n출력: 타자=이닝 전환형 OF/DH, 투수=traffic-command starter feature contract.",
    color: C.red,
  });
  card(slide, {
    left: 72 + w + gap, top: y, width: w, height: h, label: "B", title: "KBO History Model",
    body: "질문: 후보는 과거 KBO 성공 외국인 선수와 닮았는가, 혹은 실패 패턴을 가졌는가?\n\n입력: 과거 KBO 외국인 선수의 pre-KBO Savant/MiLB feature. KBO 입단 후 성과는 label/사후 검증에만 사용.\n\n모델: 타자 Ridge Logistic Regression success/failure classifier. 투수 Sparse/L1 diagnostic classifier.\n\n성능: 타자 success AUC 0.833, failure AUC 0.738. 투수 AUC 0.603.\n\n사용: 타자는 high signal, 투수는 확정 추천이 아닌 diagnostic signal.",
    color: C.red,
    fill: C.light,
  });
  card(slide, {
    left: 72 + (w + gap) * 2, top: y, width: w, height: h, label: "C", title: "Archetype Matching",
    body: "질문: 이 선수는 어떤 유형이며, SSG 필요 역할과 얼마나 닮았는가?\n\n입력: 후보별 표준화 feature vector.\n\n타자 vector: contact floor, on-base/damage, RHP fit, run-kill avoidance, role/market fit.\n\n투수 vector: command stability, damage control, starter floor, KBO/ABS translation, market/medical fit.\n\n방법: role similarity, archetype score, KBO 성공 유형/SSG 필요 유형과의 distance 비교.\n\n유형: contact-floor OF/DH, RHP unlocker, traffic-command starter.",
    color: C.red,
  });
  callout(slide, "핵심: A는 필요 유형을 정의하고, B는 성공/실패 신호를 학습하며, C는 후보가 그 역할과 얼마나 닮았는지 비교한다.", 220, 742, 1160, 64);
}

function slideModelDEF(p) {
  const slide = p.slides.add();
  header(slide, "모델 상세 2: D/E/F", "미국 성적의 KBO 번역 가능성, 시장 접근성, 의료·실행 리스크를 gate로 검증");
  const w = 462, h = 432, gap = 38, y = 250;
  card(slide, {
    left: 72, top: y, width: w, height: h, label: "D", title: "KBO Translation Risk",
    body: "질문: 미국 성적이 KBO에서도 유지될 수 있는가?\n\n입력: MLB Savant 2023-2026, MiLB 성적, K%, chase, whiff, contact, ISO, xwOBA, BB9, HR9, starter continuity, third-time wOBA, GB%, zone command.\n\n방법: feature family ablation + risk flagging + threshold-based translation risk.\n\n타자 위험: 과도한 K%, 높은 chase%, 낮은 contact, 변화구/저속 구종 약점, run-kill risk.\n\n투수 위험: 높은 BB9/HR9, 낮은 GB%, 선발 지속성 부족, ABS 환경 볼넷 증가.",
    color: C.blue,
    fill: C.light,
  });
  card(slide, {
    left: 72 + w + gap, top: y, width: w, height: h, label: "E", title: "Market Feasibility",
    body: "질문: 아무리 좋은 선수여도 실제로 데려올 수 있는가?\n\n입력: roster/transaction, 40-man 포함 여부, DFA/outright, minor contract, salary signal, option status, 권리 상태.\n\n방법: 점수 모델이 아니라 hard gate + market access bucket.\n\n판정 예시: MLB active 40-man=접근성 낮음, DFA/outright 이후 40-man 밖=접근성 높음, minor/non-roster=검토 가능.\n\n출력: available, conditional, blocked, contract verification needed, manual contact priority.",
    color: C.blue,
  });
  card(slide, {
    left: 72 + (w + gap) * 2, top: y, width: w, height: h, label: "F", title: "Medical / Failure Gate",
    body: "질문: 건강, 역할, 비용, 계약 측면에서 현실적인가?\n\n입력: IL, surgery, workload, recent usage, velocity trend, role mismatch, medical public signal, salary/contract signal.\n\n방법: 최종 board에서 실행 불가능성을 걸러내는 hard gate/보류 gate.\n\n출력: PASS(final 유지), YELLOW(conditional), HOLD(watch/medical hold), RED(최종 제외).\n\n예시: 점수 높아도 너무 젊고 MLB 가치가 높으면 HOLD. 최근 부상 이력이 크면 WATCH/RED. 선발 workload 부족 시 감점.",
    color: C.blue,
    fill: C.light,
  });
  callout(slide, "핵심: D는 KBO에서 통할 위험, E는 실제 접촉 가능성, F는 점수 상위 후보를 무조건 추천하지 않기 위한 방어 장치다.", 208, 742, 1184, 64, C.blue);
}

function slideEnsemble(p) {
  const slide = p.slides.add();
  header(slide, "앙상블 의사결정 로직", "단순 평균 점수표가 아니라 score model과 hard gate를 결합한 structured-only fit model");
  addShape(slide, "roundRect", 72, 236, 536, 158, C.white, C.line, "rounded-xl");
  addText(slide, "Unified Fit Score", 104, 260, 320, 32, { size: 25, bold: true, color: C.red });
  addText(slide, "weighted feature-block score\n+ role/position adjustment\n+ sample adjustment\n+ age adjustment\n- categorical risk penalty", 104, 306, 460, 72, { size: 18, color: C.ink });
  addShape(slide, "roundRect", 636, 236, 420, 158, C.light, C.line, "rounded-xl");
  addText(slide, "타자 모델 사용 강도", 668, 260, 300, 30, { size: 23, bold: true, color: C.red });
  addText(slide, "Historical classifier를 가장 강한 base learner로 사용\nsuccess AUC 0.833 / failure AUC 0.738\nSavant feature가 비교적 안정적", 668, 306, 340, 74, { size: 17.2, color: C.ink });
  addShape(slide, "roundRect", 1084, 236, 444, 158, C.blueSoft, C.line, "rounded-xl");
  addText(slide, "투수 모델 사용 강도", 1116, 260, 300, 30, { size: 23, bold: true, color: C.blue });
  addText(slide, "Classifier AUC 0.603으로 diagnostic만 사용\ncommand, starter floor, damage control,\nmarket/medical gate를 더 강하게 반영", 1116, 306, 356, 74, { size: 17.2, color: C.ink });

  miniTable(slide, 72, 432, 686, 48,
    ["타자 모듈", "Weight", "근거"],
    [
      ["Historical success/failure", "0.40", "AUC promoted gate 통과"],
      ["SSG fit + translation", "0.25", "SSG 약점과 KBO 번역 동시 반영"],
      ["KBO adaptation filter", "0.15", "변화구·저속 구종·좌/스위치 적합성"],
      ["Market inefficiency", "0.15", "AAA 장점과 MLB 결함의 translation gap"],
      ["Cross-model consensus", "0.05", "반복 등장 후보 안정성 보너스"],
    ],
    { cols: [0.47, 0.13, 0.40], firstRed: true, size: 12.8, headerSize: 14.2 }
  );
  miniTable(slide, 842, 432, 686, 48,
    ["투수 모듈", "Weight", "근거"],
    [
      ["Historical classifier", "0.05", "AUC 0.603, weak diagnostic only"],
      ["SSG fit + translation", "0.25", "선발 이닝·KBO ERA 번역·영입 등급"],
      ["KBO adaptation filter", "0.25", "BB/9, HR/9, third-time risk"],
      ["Market inefficiency", "0.20", "fringe starter 시장 탐색"],
      ["Cross-model consensus", "0.25", "독립 분석 반복 등장 중요"],
    ],
    { cols: [0.47, 0.13, 0.40], firstRed: true, size: 12.8, headerSize: 14.2, headerFill: C.blueSoft }
  );
  callout(slide, "Leakage 방지: KBO 입단 후 성과는 label/사후 검증에만 사용했고, 후보 feature에는 입단 전·현재 구조화 데이터만 사용했다.", 176, 746, 1248, 62, C.red);
}

function slideFunnel(p) {
  const slide = p.slides.add();
  header(slide, "Candidate Funnel: 넓게 만들고, 좁게 검증했다", "Step 1~3은 후보를 줄이는 과정, Step 4~5는 후보를 정렬하는 과정");
  const steps = [
    ["Step 1", "736 / 1,009", "전체 구조화 시장", "MLB/MiLB/roster 기반으로 모델 입력 가능한 후보 pool 구성.\n추천이 아니라 분석 가능한 시장 구축."],
    ["Step 2", "16 / 18", "후보 생성 모듈", "Market, Team Fit, Upside, Translation screen 중 하나 이상에서 강한 신호.\nOR-screen: 넓게 건져 올림."],
    ["Step 3", "6 / 3", "1차 검증 통과", "표본, 포지션/역할, 40-man/계약, salary, medical, 데이터 결측을 동시에 확인.\nAND-gate: 검증된 후보만 남김."],
    ["Step 4", "Top 3", "Raw Ranking", "SSG Need Fit, KBO Translation, Archetype, Failure Resilience, Consensus 기반.\n데이터상 좋아 보이는 후보."],
    ["Step 5", "Top 3", "Final Ranking", "40-man, DFA/outright, 연봉, 계약, 의료, role acceptance, KBO행 가능성을 반영.\n실제 접촉 가능한 후보."],
  ];
  const x0 = 72, y = 250, w = 268, h = 376, gap = 24;
  steps.forEach((s, i) => {
    const left = x0 + i * (w + gap);
    const final = i === 4;
    addShape(slide, "roundRect", left, y, w, h, final ? C.redSoft : (i % 2 ? C.light : C.white), final ? C.red2 : C.line, "rounded-xl");
    addText(slide, s[0], left + 28, y + 26, 150, 28, { size: 17, bold: true, color: C.mid });
    addText(slide, s[1], left + 28, y + 80, 220, 42, { size: 30, bold: true, color: final ? C.red : C.ink });
    addText(slide, s[2], left + 28, y + 132, 220, 30, { size: 18.5, bold: true, color: C.mid });
    addText(slide, s[3], left + 24, y + 190, w - 48, 150, { size: 13.8, color: C.ink });
  });
  callout(slide, "발표 포인트: Step 1~3은 pool을 줄이는 mining process, Step 4~5는 raw score와 실행 가능성을 나눠 정렬하는 decision process다.", 140, 730, 1320, 64);
}

function slideStep2Step3(p) {
  const slide = p.slides.add();
  header(slide, "Step 2와 Step 3은 무엇이 다른가?", "Step 2는 가능성을 넓게 보는 OR-screen, Step 3은 발표 가능한 후보만 남기는 AND-gate");
  const top = 238, h = 378, w = 686;
  addShape(slide, "roundRect", 72, top, w, h, C.white, C.line, "rounded-xl");
  addText(slide, "Step 2 Candidate Generation", 110, top + 26, 470, 32, { size: 25, bold: true, color: C.red });
  addText(slide, "목적: 넓게 후보 발굴\n방식: OR-screen\n기준: 하나 이상의 모듈에서 강한 신호가 있으면 후보 board 포함\n결과: 타자 16명, 투수 18명\n해석: 찾아낸 후보", 110, top + 74, 590, 104, { size: 17.2, color: C.ink });
  addText(slide, "타자 예시: RHP 상대 출루/장타, contact floor, OF/DH 가능성, 낮은 run-kill risk, 시장 비효율\n\n투수 예시: starter floor, low BB9, low HR9, traffic command, multi-inning 가능성", 110, top + 206, 590, 118, { size: 16.3, color: C.mid });
  addShape(slide, "roundRect", 842, top, w, h, C.blueSoft, C.line, "rounded-xl");
  addText(slide, "Step 3 Basic Data-Mining Gate", 880, top + 26, 500, 32, { size: 25, bold: true, color: C.blue });
  addText(slide, "목적: 모델 비교 가능한 후보만 남김\n방식: AND-gate\n기준: 핵심 조건을 동시에 통과해야 함\n결과: 타자 6명, 투수 3명\n해석: 검증을 통과한 후보", 880, top + 74, 590, 104, { size: 17.2, color: C.ink });
  addText(slide, "검증 항목: 표본 신뢰도, 포지션/역할 적합성, 시장 접근성, 40-man/계약 상태, salary/contract signal, medical risk, 데이터 결측, 신원 매칭", 880, top + 206, 590, 118, { size: 16.3, color: C.mid });
  addShape(slide, "roundRect", 72, 650, 1456, 112, C.white, C.line, "rounded-xl");
  addText(slide, "왜 타자는 6명, 투수는 3명인가?", 104, 674, 420, 30, { size: 23, bold: true, color: C.red });
  addText(slide, "타자: historical KBO hitter classifier가 success AUC 0.833 / failure AUC 0.738로 의미 있는 신호를 보였고, Savant 기반 OF/DH feature가 비교적 안정적이었다.", 104, 714, 640, 38, { size: 15.4, color: C.ink });
  addText(slide, "투수: classifier AUC 0.603으로 diagnostic 수준이고, 수비·포수·구장·역할 이질성 영향이 커서 starter floor, BB9, HR9, workload, market/medical gate를 더 보수적으로 적용했다.", 790, 714, 686, 46, { size: 15.4, color: C.ink });
}

function slideRawFinal(p) {
  const slide = p.slides.add();
  header(slide, "Raw Ranking과 Final Ranking은 왜 다른가?", "Raw는 데이터상 우수 후보, Final은 실제 영입 가능한 후보");
  addShape(slide, "roundRect", 78, 232, 410, 152, C.white, C.line, "rounded-xl");
  addText(slide, "Raw Ranking", 112, 256, 280, 34, { size: 28, bold: true, color: C.red });
  addText(slide, "순수 모델 점수와 cross-model consistency 기반\nSSG Need, KBO Translation, Archetype, Failure Risk 반영\n= 데이터상 좋아 보이는 후보", 112, 306, 330, 60, { size: 15.7, color: C.ink });
  addText(slide, "→", 518, 282, 70, 52, { size: 42, bold: true, color: C.mid });
  addShape(slide, "roundRect", 596, 232, 410, 152, C.light, C.line, "rounded-xl");
  addText(slide, "Execution Gate", 630, 256, 300, 34, { size: 28, bold: true, color: C.ink });
  addText(slide, "40-man, DFA/outright, minor contract,\nsalary/contract, medical, role acceptance,\nKBO행 가능성, 즉시 전력 가능성", 630, 306, 330, 60, { size: 15.7, color: C.ink });
  addText(slide, "→", 1036, 282, 70, 52, { size: 42, bold: true, color: C.mid });
  addShape(slide, "roundRect", 1114, 232, 410, 152, C.redSoft, C.red2, "rounded-xl");
  addText(slide, "Final Ranking", 1148, 256, 300, 34, { size: 28, bold: true, color: C.red });
  addText(slide, "모델 점수에 프런트 현실성 검증을 더한 최종 접촉 순위\n= 실제로 데려올 수 있는 후보", 1148, 306, 330, 60, { size: 15.7, color: C.ink });

  addShape(slide, "roundRect", 78, 428, 654, 202, C.white, C.line, "rounded-xl");
  addText(slide, "Unified Fit Score", 110, 452, 280, 28, { size: 23, bold: true, color: C.red });
  addText(slide, "weighted feature-block score + role/position adjustment + sample adjustment + age adjustment - categorical risk penalty", 110, 494, 568, 42, { size: 17, color: C.ink });
  addText(slide, "외인타자: Need 0.34 · Translation 0.24 · Market 0.15 · Tool 0.08 · Surplus 0.09 · Failure 0.10\n외인투수: Need 0.32 · Translation 0.22 · Market 0.17 · Tool 0.09 · Surplus 0.10 · Failure 0.10", 110, 558, 568, 48, { size: 14.8, color: C.mid });

  addShape(slide, "roundRect", 788, 428, 736, 202, C.blueSoft, C.line, "rounded-xl");
  addText(slide, "왜 순위가 바뀌나?", 820, 452, 320, 28, { size: 23, bold: true, color: C.blue });
  addText(slide, "Raw 점수가 높아도 40-man blocked면 HOLD\n너무 젊고 MLB 가치가 높으면 HOLD\nmedical risk가 크면 WATCH 또는 RED\nRaw 점수가 중간이어도 DFA/outright + SSG fit 강하면 CONTACT 상승\n투수는 raw score보다 starter floor, command, BB/HR 억제, workload를 더 강하게 본다.", 820, 494, 646, 100, { size: 16, color: C.ink });

  addShape(slide, "roundRect", 78, 670, 1446, 104, C.white, C.red2, "rounded-lg");
  addText(slide, "방어 문장", 110, 696, 150, 26, { size: 22, bold: true, color: C.red });
  addText(slide, "Raw 1위가 Final 1위가 아닐 수 있는 이유는 모델이 틀려서가 아니라, 실제 영입에서는 계약·연봉·의료·로스터 접근성이 hard gate로 작동하기 때문이다. 후보 feature에는 KBO 입단 후 성과를 넣지 않아 leakage를 방지했다.", 268, 694, 1180, 44, { size: 17.4, color: C.ink });
}

async function writeBlob(file, blob) {
  await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  slideModelABC(presentation);
  slideModelDEF(presentation);
  slideEnsemble(presentation);
  slideFunnel(presentation);
  slideStep2Step3(presentation);
  slideRawFinal(presentation);

  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `supplement_slide_${String(index + 1).padStart(2, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await writeBlob(path.join(OUT_DIR, `${stem}.png`), png);
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(OUT_DIR, `${stem}.layout.json`), await layout.text());
  }
  const montage = await presentation.export({ format: "png", montage: true, scale: 1 });
  await writeBlob(path.join(OUT_DIR, "supplement_contact_sheet.png"), montage);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(PPTX_OUT);
  console.log(PPTX_OUT);
  console.log(path.join(OUT_DIR, "supplement_contact_sheet.png"));
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});
