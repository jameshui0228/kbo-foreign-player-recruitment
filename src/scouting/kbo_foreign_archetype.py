"""
KBO 외국인 선수 성공/실패 유형 마이닝 - 2단계
================================================
입력: data/processed/kbo/kbo_foreign_player_season_labels_v0_1.csv  (128개 Statiz 매칭)
출력: outputs/tables/kbo_foreign_archetype_*.csv

실행:
    python src/scouting/kbo_foreign_archetype.py

데이터 한계 (assumptions.md #15 참조):
- pre_arrival_primary_league / age_at_arrival 미입력 → 2단계는 KBO 진입 후 성적으로만 유형 정의
- 사전 특성 기반 예측 모델은 3단계 후보 풀 구축 후 Statcast/FanGraphs 연계 시 가능
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# ── 경로 설정 ────────────────────────────────────────────────────────────────

def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / ".env").exists() or (parent / "README.md").exists():
            return parent
    return Path.cwd()

PROJECT_ROOT = _find_project_root()

def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip()
    env.update(os.environ)
    return env

ENV = _load_env()

def _resolve(key: str, fallback: Path) -> Path:
    raw = ENV.get(key, "")
    if not raw:
        return fallback
    for k, v in ENV.items():
        raw = raw.replace(f"${{{k}}}", v)
    return Path(raw)

RAW_DATA_ROOT = _resolve(
    "RAW_DATA_ROOT",
    PROJECT_ROOT / "data",
)

LABEL_PATH = RAW_DATA_ROOT / "processed" / "kbo" / "kbo_foreign_player_season_labels_v0_1.csv"
OUT = PROJECT_ROOT / "outputs" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

# ── 상수 ─────────────────────────────────────────────────────────────────────

# KBO 진입 후 성적 기준 (아키타입 임계값, assumptions.md #15)
HITTER_THRESHOLDS = {
    "dominant":  {"war": 4.0, "wrc_plus": 130},   # 지배형
    "solid":     {"war": 2.0, "wrc_plus": 108},   # 안정 기여형
    "marginal":  {"war": 0.5, "wrc_plus":  90},   # 한계형
}
STARTER_THRESHOLDS = {
    "ace":       {"war": 4.0, "era": 3.5},         # 에이스 번역
    "solid":     {"war": 1.5, "era": 4.5},         # 중간 선발형
    "risky":     {"war": 0.5, "era": 5.0},         # 위험 임계
}

# 재계약/교체 기준선 (리그 2023-2025 관측치 기반)
REPLACEMENT_ERA_SOFT  = 5.0
REPLACEMENT_ERA_HARD  = 6.0
REPLACEMENT_WRC_SOFT  = 100
REPLACEMENT_WAR_SOFT  = 0.5

# SSG에서 연결되는 feature contract (1단계 결과)
SSG_FEATURE_CONTRACT = {
    "1루_주자_진루":  "gap_power_pull_avoidance",
    "초반이닝_공략":  "early_inning_support",
    "우언더_취약":   "abs_zone_discipline",
    "2아웃_약점":    "two_out_contact",
}

# ── 데이터 로드 ───────────────────────────────────────────────────────────────

def load_labels() -> pd.DataFrame:
    if not LABEL_PATH.exists():
        sys.exit(f"[ERROR] 라벨 파일 없음: {LABEL_PATH}\n.env의 RAW_DATA_ROOT를 확인하세요.")
    df = pd.read_csv(LABEL_PATH, low_memory=False)
    # 수치 컬럼 변환
    for c in ["first_kbo_war", "first_kbo_wrc_plus", "first_kbo_era", "first_kbo_k_bb_pct",
              "success", "strong_success", "failure",
              "in_season_replaced", "renewed_next_year", "injury_exit_flag", "performance_exit_flag"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    return df

# ── 1. 전체 베이스레이트 ──────────────────────────────────────────────────────

def compute_base_rates(df: pd.DataFrame) -> pd.DataFrame:
    labeled = df[df["label_available"] == True]
    rows = []
    for role in ["hitter", "starter", "all"]:
        sub = labeled if role == "all" else labeled[labeled["role_group"] == role]
        n = len(sub)
        if n == 0:
            continue
        rows.append({
            "role":              role,
            "total_labeled":     n,
            "success_n":         int(sub["success"].sum()),
            "failure_n":         int(sub["failure"].sum()),
            "replacement_n":     int(sub["in_season_replaced"].sum()),
            "strong_success_n":  int(sub["strong_success"].sum()),
            "success_rate":      round(sub["success"].mean(), 3),
            "failure_rate":      round(sub["failure"].mean(), 3),
            "replacement_rate":  round(sub["in_season_replaced"].mean(), 3),
        })
    return pd.DataFrame(rows)


# ── 2. 연도별 교체율 트렌드 ──────────────────────────────────────────────────

def compute_replacement_trend(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for season, g in df.groupby("season"):
        n = len(g)
        repl = int(g["in_season_replaced"].sum())
        succ = int(g["success"].sum()) if "success" in g.columns else None
        rows.append({
            "season":        season,
            "total":         n,
            "replaced_n":    repl,
            "replacement_rate": round(repl / n, 3) if n else None,
            "success_n":     succ,
            "success_rate":  round(succ / n, 3) if (succ is not None and n) else None,
        })
    return pd.DataFrame(rows).sort_values("season")


# ── 3. 팀별 성공률 ───────────────────────────────────────────────────────────

def compute_team_rates(df: pd.DataFrame) -> pd.DataFrame:
    labeled = df[df["label_available"] == True]
    rows = []
    for team, g in labeled.groupby("kbo_team"):
        n = len(g)
        rows.append({
            "team":           team,
            "total":          n,
            "success_n":      int(g["success"].sum()),
            "failure_n":      int(g["failure"].sum()),
            "replacement_n":  int(g["in_season_replaced"].sum()),
            "success_rate":   round(g["success"].mean(), 3),
            "failure_rate":   round(g["failure"].mean(), 3),
            "replacement_rate": round(g["in_season_replaced"].mean(), 3),
        })
    return pd.DataFrame(rows).sort_values("success_rate", ascending=False)


# ── 4. KBO 진입 후 성적 기반 아키타입 분류 ─────────────────────────────────

def _classify_hitter(row: pd.Series) -> str:
    war = row["first_kbo_war"]
    wrc = row["first_kbo_wrc_plus"]
    if pd.isna(war) or pd.isna(wrc):
        return "unknown"
    if row["in_season_replaced"] == 1 and war < REPLACEMENT_WAR_SOFT:
        return "C_replaced_poor"
    if war >= HITTER_THRESHOLDS["dominant"]["war"] and wrc >= HITTER_THRESHOLDS["dominant"]["wrc_plus"]:
        return "A_dominant"
    if war >= HITTER_THRESHOLDS["solid"]["war"] and wrc >= HITTER_THRESHOLDS["solid"]["wrc_plus"]:
        return "B_solid"
    if war >= HITTER_THRESHOLDS["marginal"]["war"] and wrc >= HITTER_THRESHOLDS["marginal"]["wrc_plus"]:
        return "C_marginal"
    return "D_failure"

def _classify_starter(row: pd.Series) -> str:
    war = row["first_kbo_war"]
    era = row["first_kbo_era"]
    if pd.isna(war) or pd.isna(era):
        return "unknown"
    if row["in_season_replaced"] == 1 and era >= REPLACEMENT_ERA_HARD:
        return "D_replaced_blowup"
    if row["in_season_replaced"] == 1 and era >= REPLACEMENT_ERA_SOFT:
        return "C_replaced_marginal"
    if war >= STARTER_THRESHOLDS["ace"]["war"] and era <= STARTER_THRESHOLDS["ace"]["era"]:
        return "A_ace_translation"
    if war >= STARTER_THRESHOLDS["solid"]["war"] and era <= STARTER_THRESHOLDS["solid"]["era"]:
        return "B_solid_contributor"
    if era >= REPLACEMENT_ERA_HARD:
        return "D_era_blowup"
    if era >= REPLACEMENT_ERA_SOFT or war < STARTER_THRESHOLDS["risky"]["war"]:
        return "C_risky"
    return "B_solid_contributor"

def build_archetypes(df: pd.DataFrame) -> pd.DataFrame:
    matched = df[df["statiz_matched"] == True].copy()

    matched["archetype"] = "unknown"
    h_mask = matched["role_group"] == "hitter"
    s_mask = matched["role_group"] == "starter"
    matched.loc[h_mask, "archetype"] = matched.loc[h_mask].apply(_classify_hitter, axis=1)
    matched.loc[s_mask, "archetype"] = matched.loc[s_mask].apply(_classify_starter, axis=1)

    keep = [
        "player_name_ko", "season", "kbo_team", "role_group", "archetype",
        "first_kbo_war", "first_kbo_wrc_plus", "first_kbo_era", "first_kbo_k_bb_pct",
        "success", "strong_success", "failure",
        "in_season_replaced", "renewed_next_year",
        "injury_exit_flag", "performance_exit_flag",
    ]
    return matched[[c for c in keep if c in matched.columns]]


# ── 5. 아키타입별 집계 프로파일 ─────────────────────────────────────────────

def build_archetype_profile(archetypes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (role, arch), g in archetypes.groupby(["role_group", "archetype"]):
        n = len(g)
        war_vals = g["first_kbo_war"].dropna()
        wrc_vals = g["first_kbo_wrc_plus"].dropna()
        era_vals = g["first_kbo_era"].dropna()
        rows.append({
            "role_group":       role,
            "archetype":        arch,
            "n":                n,
            "success_rate":     round(g["success"].mean(), 3),
            "failure_rate":     round(g["failure"].mean(), 3),
            "replacement_rate": round(g["in_season_replaced"].mean(), 3),
            "avg_war":          round(war_vals.mean(), 2) if len(war_vals) else None,
            "median_war":       round(war_vals.median(), 2) if len(war_vals) else None,
            "avg_wrc_plus":     round(wrc_vals.mean(), 1) if len(wrc_vals) else None,
            "avg_era":          round(era_vals.mean(), 2) if len(era_vals) else None,
            "median_era":       round(era_vals.median(), 2) if len(era_vals) else None,
        })
    return (
        pd.DataFrame(rows)
        .sort_values(["role_group", "success_rate"], ascending=[True, False])
        .reset_index(drop=True)
    )


# ── 6. 규칙 기반 lift 분석 ───────────────────────────────────────────────────
#
# 표본이 작으므로 lift를 "후보 점수"가 아닌 "스카우팅 질문 생성기"로 사용한다.
# support_rows < 5이면 연구 참고용(research_only)으로만 사용한다.

RULES = {
    # 타자 규칙
    "hitter_wrc_ge120_success":    {"role": "hitter", "target": "success",          "cond": lambda r: r["first_kbo_wrc_plus"] >= 120},
    "hitter_wrc_lt90_failure":     {"role": "hitter", "target": "failure",           "cond": lambda r: r["first_kbo_wrc_plus"] <   90},
    "hitter_war_ge4_strong":       {"role": "hitter", "target": "strong_success",    "cond": lambda r: r["first_kbo_war"]      >= 4.0},
    "hitter_war_lt1_replaced":     {"role": "hitter", "target": "in_season_replaced","cond": lambda r: r["first_kbo_war"]      <  1.0},
    # 선발 규칙
    "starter_era_le350_success":   {"role": "starter","target": "success",           "cond": lambda r: r["first_kbo_era"]      <= 3.5},
    "starter_era_ge500_replaced":  {"role": "starter","target": "in_season_replaced","cond": lambda r: r["first_kbo_era"]      >= 5.0},
    "starter_era_ge600_replaced":  {"role": "starter","target": "in_season_replaced","cond": lambda r: r["first_kbo_era"]      >= 6.0},
    "starter_war_ge4_strong":      {"role": "starter","target": "strong_success",    "cond": lambda r: r["first_kbo_war"]      >= 4.0},
    "starter_war_lt1_failure":     {"role": "starter","target": "failure",           "cond": lambda r: r["first_kbo_war"]      <  1.0},
}

def build_rule_lifts(archetypes: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for rule_name, spec in RULES.items():
        role     = spec["role"]
        target   = spec["target"]
        cond_fn  = spec["cond"]

        sub = archetypes[archetypes["role_group"] == role].copy()
        sub = sub[sub[target].notna() & sub["first_kbo_war"].notna()]
        if len(sub) == 0:
            continue

        base_rate = sub[target].mean()
        try:
            inside = sub[sub.apply(cond_fn, axis=1)]
        except Exception:
            continue

        n_inside = len(inside)
        if n_inside == 0:
            continue

        inside_rate = inside[target].mean()
        rate_delta  = inside_rate - base_rate
        lift        = (inside_rate / base_rate) if base_rate > 0 else np.nan

        # 간단한 permutation p-value (1000회 셔플)
        rng = np.random.default_rng(seed=42)
        shuffled_rates = []
        for _ in range(1000):
            perm = sub[target].values.copy()
            rng.shuffle(perm)
            shuffled_rates.append(perm[:n_inside].mean())
        p_val = np.mean(np.array(shuffled_rates) >= inside_rate) if rate_delta > 0 \
               else np.mean(np.array(shuffled_rates) <= inside_rate)

        rule_gate = "usable" if (n_inside >= 5 and p_val <= 0.20) else "research_only"

        rows.append({
            "rule_name":              rule_name,
            "role_group":             role,
            "target":                 target,
            "support_rows":           n_inside,
            "base_rate":              round(base_rate, 3),
            "inside_rate":            round(inside_rate, 3),
            "rate_delta_vs_base":     round(rate_delta, 3),
            "lift_vs_base":           round(lift, 2) if not np.isnan(lift) else None,
            "permutation_p_value":    round(p_val, 3),
            "rule_gate":              rule_gate,
            "abs_rate_delta":         round(abs(rate_delta), 3),
        })

    return (
        pd.DataFrame(rows)
        .sort_values(["rule_gate", "abs_rate_delta"], ascending=[True, False])
        .reset_index(drop=True)
    )


# ── 7. SSG 역대 외인 카드 ───────────────────────────────────────────────────

def build_ssg_history(df: pd.DataFrame, archetypes: pd.DataFrame) -> pd.DataFrame:
    ssg_raw = df[df["kbo_team"].isin(["SSG", "SK"])].copy()
    arch_map = archetypes.set_index(["player_name_ko", "season"])["archetype"].to_dict()
    ssg_raw["archetype"] = ssg_raw.apply(
        lambda r: arch_map.get((r["player_name_ko"], r["season"]), "no_statiz"), axis=1
    )
    keep = [
        "season", "player_name_ko", "role_group", "archetype",
        "first_kbo_war", "first_kbo_wrc_plus", "first_kbo_era",
        "success", "failure", "in_season_replaced", "renewed_next_year",
    ]
    return ssg_raw[[c for c in keep if c in ssg_raw.columns]].sort_values("season")


# ── 8. 교체 촉발 임계값 분석 ─────────────────────────────────────────────────

def build_replacement_triggers(archetypes: pd.DataFrame) -> pd.DataFrame:
    """교체 선수 vs 유지 선수의 성적 분포를 비교해 실질적인 교체 촉발 임계값을 추정."""
    rows = []
    for role in ["hitter", "starter"]:
        sub = archetypes[archetypes["role_group"] == role].copy()
        repl  = sub[sub["in_season_replaced"] == 1]
        kept  = sub[sub["in_season_replaced"] == 0]

        if role == "hitter":
            for stat, col in [("WAR", "first_kbo_war"), ("wRC+", "first_kbo_wrc_plus")]:
                r_vals = repl[col].dropna()
                k_vals = kept[col].dropna()
                rows.append({
                    "role": role, "stat": stat,
                    "replaced_median": round(r_vals.median(), 2) if len(r_vals) else None,
                    "replaced_q25":    round(r_vals.quantile(0.25), 2) if len(r_vals) else None,
                    "kept_median":     round(k_vals.median(), 2) if len(k_vals) else None,
                    "kept_q25":        round(k_vals.quantile(0.25), 2) if len(k_vals) else None,
                    "replaced_n":      len(r_vals), "kept_n": len(k_vals),
                })
        else:
            for stat, col in [("WAR", "first_kbo_war"), ("ERA", "first_kbo_era")]:
                r_vals = repl[col].dropna()
                k_vals = kept[col].dropna()
                asc = stat == "ERA"
                rows.append({
                    "role": role, "stat": stat,
                    "replaced_median": round(r_vals.median(), 2) if len(r_vals) else None,
                    "replaced_q75":    round(r_vals.quantile(0.75), 2) if len(r_vals) else None,
                    "kept_median":     round(k_vals.median(), 2) if len(k_vals) else None,
                    "kept_q75":        round(k_vals.quantile(0.75), 2) if len(k_vals) else None,
                    "replaced_n":      len(r_vals), "kept_n": len(k_vals),
                })
    return pd.DataFrame(rows)


# ── 9. SSG fit 연결 메시지 ──────────────────────────────────────────────────

SSG_FIT_MESSAGES = [
    {
        "ssg_weakness":      "1루 주자만 OPS 리그 10위",
        "archetype_signal":  "A_dominant 타자: wRC+ ≥ 130, 갭 파워",
        "candidate_variable": "gap_power_pull_avoidance + runner_advancement_proxy",
        "scouting_question": "반대 방향 타구 비율이 높고, 1루 상황에서 주자 진루 능력이 검증됐는가?",
    },
    {
        "ssg_weakness":      "초반 1~3이닝 OPS 리그 8위",
        "archetype_signal":  "A_ace 선발: ERA ≤ 3.5, WAR ≥ 4.0으로 초반 이닝 안정",
        "candidate_variable": "early_inning_support (kbo_translation_index)",
        "scouting_question": "1~3이닝 ERA가 시즌 ERA와 유사한가? 선발 초반 폭발 이력이 없는가?",
    },
    {
        "ssg_weakness":      "우언더/사이드암 상대 OPS 리그 6위",
        "archetype_signal":  "B_solid 이상 + 낮은 chase% on outside low",
        "candidate_variable": "abs_zone_discipline_score",
        "scouting_question": "KBO 사이드암/언더 유형의 낮고 바깥 공에 chase% / zone_contact% 수치가 어떤가?",
    },
    {
        "ssg_weakness":      "2아웃 상황 OPS 리그 8위",
        "archetype_signal":  "A_dominant 또는 B_solid: 2사 컨택 능력",
        "candidate_variable": "two_out_contact_proxy (zone_contact_pct, whiff_pct)",
        "scouting_question": "2스트라이크 이후 whiff%가 리그 평균 이하인가?",
    },
    {
        "ssg_weakness":      "홈-원정 격차 (원정 OPS 7위)",
        "archetype_signal":  "B_solid 이상 + 원정 적응 이력",
        "candidate_variable": "road_durability_proxy",
        "scouting_question": "원정 성적이 홈보다 크게 떨어지지 않는가? 장거리 이동 후 피로 회복 이력?",
    },
]

def build_ssg_fit_messages() -> pd.DataFrame:
    return pd.DataFrame(SSG_FIT_MESSAGES)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("[kbo_foreign_archetype] 데이터 로드 중...")
    df = load_labels()
    print(f"  전체 레코드: {len(df)}개 | Statiz 매칭: {(df['statiz_matched'] == True).sum()}개")

    # ── 분석 실행 ────────────────────────────────────────────────────────────
    print("\n[1/7] 전체 베이스레이트...")
    base = compute_base_rates(df)
    base.to_csv(OUT / "kbo_foreign_base_rates.csv", index=False, encoding="utf-8-sig")
    print(base.to_string(index=False))

    print("\n[2/7] 연도별 교체율 트렌드...")
    trend = compute_replacement_trend(df)
    trend.to_csv(OUT / "kbo_foreign_replacement_trend.csv", index=False, encoding="utf-8-sig")
    print(trend.to_string(index=False))

    print("\n[3/7] 팀별 성공률...")
    team_rates = compute_team_rates(df)
    team_rates.to_csv(OUT / "kbo_foreign_team_rates.csv", index=False, encoding="utf-8-sig")
    print(team_rates.to_string(index=False))

    print("\n[4/7] KBO 진입 후 성적 기반 아키타입 분류...")
    archetypes = build_archetypes(df)
    archetypes.to_csv(OUT / "kbo_foreign_archetypes.csv", index=False, encoding="utf-8-sig")
    print(f"  분류 완료: {len(archetypes)}개")
    print(archetypes.groupby(["role_group", "archetype"]).size().reset_index(name="n").to_string(index=False))

    print("\n[5/7] 아키타입별 집계 프로파일...")
    profiles = build_archetype_profile(archetypes)
    profiles.to_csv(OUT / "kbo_foreign_archetype_profiles.csv", index=False, encoding="utf-8-sig")
    print(profiles.to_string(index=False))

    print("\n[6/7] 규칙 기반 lift 분석...")
    lifts = build_rule_lifts(archetypes)
    lifts.to_csv(OUT / "kbo_foreign_rule_lifts.csv", index=False, encoding="utf-8-sig")
    print(lifts[["rule_name","support_rows","base_rate","inside_rate","rate_delta_vs_base","lift_vs_base","permutation_p_value","rule_gate"]].to_string(index=False))

    print("\n[7/7] 교체 촉발 임계값 분석...")
    triggers = build_replacement_triggers(archetypes)
    triggers.to_csv(OUT / "kbo_foreign_replacement_triggers.csv", index=False, encoding="utf-8-sig")
    print(triggers.to_string(index=False))

    # SSG 역대 카드 & fit 메시지
    ssg_hist = build_ssg_history(df, archetypes)
    ssg_hist.to_csv(OUT / "ssg_foreign_history_archetypes.csv", index=False, encoding="utf-8-sig")

    fit_msgs = build_ssg_fit_messages()
    fit_msgs.to_csv(OUT / "ssg_fit_messages_from_archetypes.csv", index=False, encoding="utf-8-sig")

    _print_summary(base, trend, lifts, ssg_hist)

    print("\n[완료] 출력 파일:")
    files = [
        "kbo_foreign_base_rates.csv",
        "kbo_foreign_replacement_trend.csv",
        "kbo_foreign_team_rates.csv",
        "kbo_foreign_archetypes.csv",
        "kbo_foreign_archetype_profiles.csv",
        "kbo_foreign_rule_lifts.csv",
        "kbo_foreign_replacement_triggers.csv",
        "ssg_foreign_history_archetypes.csv",
        "ssg_fit_messages_from_archetypes.csv",
    ]
    for f in files:
        print(f"  outputs/tables/{f}")


def _print_summary(
    base: pd.DataFrame,
    trend: pd.DataFrame,
    lifts: pd.DataFrame,
    ssg_hist: pd.DataFrame,
) -> None:
    print("\n" + "=" * 65)
    print("KBO 외인 성공/실패 유형 마이닝 요약")
    print("=" * 65)

    print("\n[리그 전체 베이스레이트]")
    for _, r in base.iterrows():
        print(f"  {r['role']:<10} 성공 {r['success_rate']:.1%}  실패 {r['failure_rate']:.1%}  "
              f"교체 {r['replacement_rate']:.1%}  (n={r['total_labeled']})")

    print("\n[교체율 트렌드]")
    recent = trend[trend["season"] >= 2022]
    for _, r in recent.iterrows():
        bar = "#" * int(r["replacement_rate"] * 30)
        print(f"  {r['season']}  {bar}  {r['replacement_rate']:.0%}  (교체 {r['replaced_n']}/{r['total']})")

    usable = lifts[lifts["rule_gate"] == "usable"]
    if not usable.empty:
        print("\n[주요 검증된 규칙 (usable gate)]")
        for _, r in usable.iterrows():
            direction = "상승" if r["rate_delta_vs_base"] > 0 else "하락"
            print(f"  [{r['role_group']}] {r['rule_name']}")
            print(f"    {r['target']} 비율: 전체 {r['base_rate']:.1%} → 규칙 내 {r['inside_rate']:.1%}  "
                  f"(delta {r['rate_delta_vs_base']:+.1%}, lift {r['lift_vs_base']:.2f}, p={r['permutation_p_value']:.3f})")

    print("\n[SSG 역대 외인 최근 5년]")
    recent_ssg = ssg_hist[ssg_hist["season"] >= 2021]
    for _, r in recent_ssg.iterrows():
        war_s = f"WAR {r['first_kbo_war']:.2f}" if pd.notna(r.get("first_kbo_war")) else "WAR N/A"
        wrc_s = f"wRC+ {r['first_kbo_wrc_plus']:.0f}" if pd.notna(r.get("first_kbo_wrc_plus")) else ""
        era_s = f"ERA {r['first_kbo_era']:.2f}" if pd.notna(r.get("first_kbo_era")) else ""
        stat_s = wrc_s or era_s or ""
        repl_s = " [교체]" if r.get("in_season_replaced") == 1 else ""
        print(f"  {r['season']}  {r['player_name_ko']:<14} [{r['archetype']}]  "
              f"{war_s}  {stat_s}{repl_s}")

    print("\n[SSG Fit - 스카우팅 질문 (1단계 약점 연결)]")
    for msg in SSG_FIT_MESSAGES:
        print(f"  약점: {msg['ssg_weakness']}")
        print(f"  질문: {msg['scouting_question']}")
        print()

    print("=" * 65)


if __name__ == "__main__":
    main()
