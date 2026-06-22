"""
후보 시장 구축 - 3단계
========================
입력:
  data/raw/mlb/milb_stats/milb_stats_research_plus_medical_20260614_002614.jsonl
  data/raw/mlb/transactions/mlb_transactions_raw_20251001_20260613.json
  data/raw/mlb/roster_status/mlb_roster_status_raw_20260612.json
  data/processed/mlb_milb/savant/savant_statcast_{year}.parquet  (2023-2025)

출력:
  outputs/tables/candidate_hitter_pool.csv
  outputs/tables/candidate_starter_pool.csv
  outputs/tables/candidate_availability_flags.csv
  outputs/tables/candidate_savant_aggregates.csv

실행:
  python src/scouting/candidate_market.py
  python src/scouting/candidate_market.py --no-savant   # Savant 집계 생략 (빠름)

Leakage 방지 원칙:
  KBO 입단 후 성적은 이 스크립트에서 절대 feature로 사용하지 않는다.
  2단계 threshold는 KBO 진입 후 성적 기반이지만, 여기서는 사전(pre-arrival) 성적에 적용한다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# ── 경로 설정 ────────────────────────────────────────────────────────────────

def _find_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / ".env").exists() or (p / "README.md").exists():
            return p
    return Path.cwd()

PROJECT_ROOT = _find_root()

def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    ef = PROJECT_ROOT / ".env"
    if ef.exists():
        for line in ef.read_text(encoding="utf-8").splitlines():
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

RAW_ROOT    = _resolve("RAW_DATA_ROOT", PROJECT_ROOT / "data")
MILB_JSONL  = RAW_ROOT / "raw" / "mlb" / "milb_stats" / "milb_stats_research_plus_medical_20260614_002614.jsonl"
TXNS_JSON   = RAW_ROOT / "raw" / "mlb" / "transactions" / "mlb_transactions_raw_20251001_20260613.json"
ROSTER_JSON = RAW_ROOT / "raw" / "mlb" / "roster_status" / "mlb_roster_status_raw_20260612.json"
SAVANT_DIR  = RAW_ROOT / "processed" / "mlb_milb" / "savant"
OUT         = PROJECT_ROOT / "outputs" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

# ── 상수 ─────────────────────────────────────────────────────────────────────

SPORT_AAA   = 11   # Triple-A
SPORT_AA    = 12   # Double-A
SPORT_MLB   = 1    # MLB (혹시 포함 시)
RECENT_SEASONS = [2023, 2024, 2025]

# PCL 고도/기후 타자 유리 구장 (OPS +0.050~+0.100 인플레이션 추정, assumption #20)
PCL_INFLATED_TEAMS = {
    "Albuquerque Isotopes",  # COL AAA, 해발 1585m
    "El Paso Chihuahuas",    # SD AAA
    "Salt Lake Bees",        # LAA AAA
    "Reno Aces",             # ARI AAA
    "Sugar Land Space Cowboys",  # HOU AAA
    "Las Vegas Aviators",    # OAK AAA
    "Round Rock Express",    # TEX AAA
}

# 2단계 검증 thresholds (KBO 진입 후 성적 기준에서 도출한 사전 필터)
# Assumption #16: AAA OPS ≥ 0.800 → KBO wRC+ 120+ 달성 가능성 높음 (proxy)
HITTER_FILTER = {
    "min_pa_aaa":   100,    # 충분한 AAA 표본
    "min_ops_aaa":  0.780,  # KBO B_solid 이상 proxy
    "max_k_pct":    0.310,  # 과도한 K% 제외 (KBO 적응 리스크)
    "min_bb_pct":   0.060,  # 최소 선구안
}
STARTER_FILTER = {
    "min_ip_aaa":   30.0,   # 충분한 이닝
    "max_era_aaa":  4.80,   # KBO ERA ≤ 4.5 proxy
    "min_k9":       5.5,    # 최소 탈삼진
    "max_bb9":      5.0,    # 최대 볼넷
    "min_gs_ratio": 0.30,   # 선발 역할 확인 (GS/GP ≥ 30%)
}

# 가용성 트랜잭션 타입 (assumptions #17)
AVAILABLE_TXNS = {"Designated for Assignment", "Released", "Declared Free Agency", "Outrighted"}

# Savant 집계용 컬럼 (메모리 절약)
SAVANT_BATTER_COLS = [
    "batter", "player_name", "game_year",
    "launch_speed", "estimated_woba_using_speedangle",
    "estimated_ba_using_speedangle", "estimated_slg_using_speedangle",
    "events", "description", "zone",
    "balls", "strikes", "type",
    "bat_speed", "attack_angle",
]
SAVANT_PITCHER_COLS = [
    "pitcher", "player_name", "game_year", "p_throws",
    "release_speed", "release_spin_rate", "pitch_name",
    "pfx_z", "pfx_x",
    "events", "description", "zone",
    "balls", "strikes", "type",
    "arm_angle",
]

# ── 1. 가용성 파악 ───────────────────────────────────────────────────────────

def load_available_player_ids() -> tuple[set[int], pd.DataFrame]:
    """DFA/Released/FA 선언된 선수 MLB ID 집합 + 상세 DataFrame."""
    txns_raw = json.loads(TXNS_JSON.read_text(encoding="utf-8"))
    txns = txns_raw.get("transactions", txns_raw) if isinstance(txns_raw, dict) else txns_raw

    rows = []
    for t in txns:
        ttype = t.get("typeDesc", "")
        if ttype not in AVAILABLE_TXNS:
            continue
        pid = t.get("person", {}).get("id")
        if not pid:
            continue
        rows.append({
            "mlb_id":     pid,
            "full_name":  t.get("person", {}).get("fullName", ""),
            "txn_type":   ttype,
            "txn_date":   t.get("date", ""),
            "from_team":  t.get("fromTeam", {}).get("name", ""),
            "to_team":    t.get("toTeam", {}).get("name", ""),
            "description": t.get("description", ""),
        })

    df = pd.DataFrame(rows).drop_duplicates(subset=["mlb_id", "txn_type"])
    available_ids = set(df["mlb_id"].tolist())
    return available_ids, df


def load_40man_ids() -> set[int]:
    """현재 40인 로스터에 있는 MLB ID 집합 (후보 제외 판단용).
    구조: rosters[str(team_id)]['40Man']['roster'] = [{'person': {'id': ...}, ...}]
    """
    raw = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
    ids: set[int] = set()
    rosters = raw.get("rosters", {})
    # rosters가 dict일 때 (team_id → 로스터 dict)
    if isinstance(rosters, dict):
        for team_val in rosters.values():
            man40 = team_val.get("40Man", {})
            if isinstance(man40, dict):
                roster_list = man40.get("roster", [])
            else:
                roster_list = man40 if isinstance(man40, list) else []
            for entry in roster_list:
                if isinstance(entry, dict):
                    pid = entry.get("person", {}).get("id")
                    if pid:
                        ids.add(pid)
    else:
        # 구형 구조: list of team rosters
        for team_roster in rosters:
            for entry in (team_roster.get("roster", []) if isinstance(team_roster, dict) else []):
                pid = entry.get("person", {}).get("id")
                if pid:
                    ids.add(pid)
    return ids


def _build_name_map(avail_df: pd.DataFrame) -> dict[int, str]:
    """MLB ID -> 선수 이름 딕셔너리 (트랜잭션 + roster people)."""
    name_map: dict[int, str] = {}
    for _, row in avail_df.iterrows():
        pid = row.get("mlb_id")
        name = row.get("full_name", "")
        if pid and name:
            name_map[int(pid)] = name
    try:
        raw = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        for pid_str, pinfo in raw.get("people", {}).items():
            pid = int(pid_str)
            if pid not in name_map and pinfo.get("fullName"):
                name_map[pid] = pinfo["fullName"]
    except Exception:
        pass
    return name_map


def _build_age_map() -> dict[int, int]:
    """MLB ID -> 현재 나이 딕셔너리 (roster people의 currentAge)."""
    age_map: dict[int, int] = {}
    try:
        raw = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        for pid_str, pinfo in raw.get("people", {}).items():
            age = pinfo.get("currentAge")
            if age is not None:
                age_map[int(pid_str)] = int(age)
    except Exception:
        pass
    return age_map


def _build_player_meta() -> dict[int, dict]:
    """MLB ID -> {position, bat_side, pitch_hand, birth_country} 딕셔너리."""
    meta: dict[int, dict] = {}
    try:
        raw = json.loads(ROSTER_JSON.read_text(encoding="utf-8"))
        for pid_str, pinfo in raw.get("people", {}).items():
            meta[int(pid_str)] = {
                "position":      pinfo.get("primaryPosition", {}).get("abbreviation", "?"),
                "bat_side":      pinfo.get("batSide", {}).get("code", "?"),
                "pitch_hand":    pinfo.get("pitchHand", {}).get("code", "?"),
                "birth_country": pinfo.get("birthCountry", "?"),
            }
    except Exception:
        pass
    return meta


# 포지션 코드 → KBO 외국인 타자 포지션 해당 여부
# KBO 외국인 타자는 일반적으로 코너 내야(1B/3B), 외야(LF/CF/RF), DH 포지션
KBO_ELIGIBLE_HITTER_POS = {"1B", "LF", "CF", "RF", "OF", "DH", "3B"}
# 내야 공격형 선수 중 3B는 KBO에서 외국인 배치가 드물지만 가능

# 한국 국적 선수는 KBO 외국인 자격 없음 (assumption #23)
KOREAN_BIRTH_COUNTRIES = {"Republic of Korea", "South Korea", "Korea"}


def _build_txn_type_map(avail_df: pd.DataFrame) -> dict[int, str]:
    """MLB ID -> 가장 강한 트랜잭션 타입 (DFA > Released > Outrighted > FA 순)."""
    priority = {
        "Designated for Assignment": 4,
        "Released": 3,
        "Outrighted": 2,
        "Declared Free Agency": 1,
    }
    best: dict[int, tuple[int, str]] = {}
    for _, row in avail_df.iterrows():
        pid = int(row["mlb_id"])
        ttype = row.get("txn_type", "")
        score = priority.get(ttype, 0)
        if pid not in best or score > best[pid][0]:
            best[pid] = (score, ttype)
    return {pid: v[1] for pid, v in best.items()}


def _classify_acquisition(
    mlb_id: int,
    available: bool,
    age: Optional[int],
    txn_type: Optional[str],
    savant_pitches: Optional[float],
    xwoba_or_era: Optional[float],
    role: str,
) -> str:
    """
    획득 가능성 등급 분류 (assumption #22):
      A: DFA/Released + 충분한 MLB 노출 → MLB에서 실패가 확인된 선수. SSG 영입 핵심 타깃.
      B: FA + 나이 26+ → 자유계약으로 계약 협의 가능, 현실적.
      C: Outrighted + 어느정도 나이 → 협상 가능하나 복잡.
      D: On40man or 어린 프로스펙트 → MLB 콜업 경쟁 중, 영입 불가 또는 비현실적.
    """
    is_dfa_released = txn_type in ("Designated for Assignment", "Released")
    is_fa = txn_type == "Declared Free Agency"
    is_outrighted = txn_type == "Outrighted"
    has_mlb_exposure = savant_pitches is not None and savant_pitches >= 500

    if not available:
        # 40인 로스터 + 아직 DFA 없음
        if age is not None and age <= 24:
            return "D_prospect"  # 어린 프로스펙트, 영입 불가
        return "D_on40man"       # 40인이지만 나이 있음, 트레이드 대상 아님

    if is_dfa_released and has_mlb_exposure:
        return "A_mlb_reject"    # 황금 타깃: MLB 실패 확인, 자유 계약
    if is_dfa_released:
        return "A_dfa_milb"      # DFA됐지만 MLB 경험 미미 (AAA가 ceiling)
    if is_fa and age is not None and age >= 28:
        return "B_fa_veteran"    # FA 베테랑, 협상 가능
    if is_fa and age is not None and age >= 25:
        return "B_fa_mid"        # FA 중간 나이
    if is_outrighted and age is not None and age >= 26:
        return "C_outrighted"    # Outrighted, 협상 가능
    if is_fa and age is not None and age <= 24:
        return "D_prospect"      # 어린 FA (드물지만 존재)
    return "B_fa_unknown"        # 나이 불명 FA


# ── 2. MiLB/MLB 성적 파싱 ───────────────────────────────────────────────────

def _safe_div(a: float, b: float, default: float = None) -> Optional[float]:
    return a / b if b and b != 0 else default

def parse_milb_stats() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    JSONL에서 타자/투수 AAA 성적(2023-2025)을 파싱해 선수별 최근 가중 성적 반환.
    같은 선수가 여러 시즌이면 PA/IP 가중 평균 적용.
    """
    hitter_rows: list[dict] = []
    pitcher_rows: list[dict] = []

    lines = MILB_JSONL.read_text(encoding="utf-8").strip().split("\n")
    for line in lines:
        d = json.loads(line)
        pid = d["player_id"]
        if d.get("status_code") != 200 or not d.get("payload"):
            continue
        group = d.get("stat_group", "")
        for stat_block in d["payload"].get("stats", []):
            for split in stat_block.get("splits", []):
                season = int(split.get("season", 0))
                if season not in RECENT_SEASONS:
                    continue
                sport_id = split.get("sport", {}).get("id")
                if sport_id not in (SPORT_AAA, SPORT_AA, SPORT_MLB):
                    continue
                stat = split.get("stat", {})
                team = split.get("team", {}).get("name", "")

                if group == "hitting":
                    pa = stat.get("plateAppearances", 0) or 0
                    if pa < 10:
                        continue
                    bb  = stat.get("baseOnBalls", 0) or 0
                    so  = stat.get("strikeOuts", 0) or 0
                    hr  = stat.get("homeRuns", 0) or 0
                    ab  = stat.get("atBats", 0) or 0
                    h   = stat.get("hits", 0) or 0
                    hitter_rows.append({
                        "mlb_id": pid,
                        "season": season,
                        "sport_id": sport_id,
                        "team": team,
                        "pa": pa, "ab": ab, "h": h,
                        "hr": hr, "bb": bb, "so": so,
                        "avg": stat.get("avg"), "obp": stat.get("obp"),
                        "slg": stat.get("slg"), "ops": stat.get("ops"),
                        "bb_pct": _safe_div(bb, pa),
                        "k_pct":  _safe_div(so, pa),
                        "iso":    _safe_div(stat.get("totalBases", h) - h, ab),
                        "sb":     stat.get("stolenBases", 0),
                    })
                elif group == "pitching":
                    ip_str = str(stat.get("inningsPitched", "0") or "0")
                    # "6.2" → 6 + 2/3 = 6.67 이닝
                    try:
                        parts = ip_str.split(".")
                        ip = int(parts[0]) + (int(parts[1]) / 3 if len(parts) > 1 else 0)
                    except Exception:
                        ip = 0.0
                    if ip < 5:
                        continue
                    gs  = stat.get("gamesStarted", 0) or 0
                    gp  = stat.get("gamesPlayed", 0) or 1
                    so  = stat.get("strikeOuts", 0) or 0
                    bb  = stat.get("baseOnBalls", 0) or 0
                    pitcher_rows.append({
                        "mlb_id": pid,
                        "season": season,
                        "sport_id": sport_id,
                        "team": team,
                        "ip": ip, "gs": gs, "gp": gp,
                        "era": stat.get("era"), "whip": stat.get("whip"),
                        "k9":  stat.get("strikeoutsPer9Inn"),
                        "bb9": stat.get("walksPer9Inn"),
                        "hr9": stat.get("homeRunsPer9"),
                        "k_bb_ratio": _safe_div(so, bb),
                        "gs_ratio": _safe_div(gs, gp),
                        "k_pct_proxy": _safe_div(so, so + bb + (stat.get("hits", 0) or 0)),
                    })

    hitters  = _aggregate_player_stats(pd.DataFrame(hitter_rows),  weight_col="pa",  group="hitter")
    starters = _aggregate_player_stats(pd.DataFrame(pitcher_rows), weight_col="ip",  group="starter")
    return hitters, starters


def _aggregate_player_stats(df: pd.DataFrame, weight_col: str, group: str) -> pd.DataFrame:
    """선수별 최근 시즌 가중 평균 (AAA 우선, 없으면 AA 포함)."""
    if df.empty:
        return pd.DataFrame()

    for c in ["avg", "obp", "slg", "ops", "era", "whip", "k9", "bb9", "hr9",
              "bb_pct", "k_pct", "iso", "k_bb_ratio", "gs_ratio", "k_pct_proxy"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # AAA 우선
    aaa = df[df["sport_id"] == SPORT_AAA]
    aa  = df[df["sport_id"] == SPORT_AA]

    def weighted_mean(sub: pd.DataFrame, col: str, w: str) -> Optional[float]:
        sub = sub.dropna(subset=[col, w])
        if sub.empty:
            return None
        weights = sub[w].clip(lower=0)
        total_w = weights.sum()
        return float((sub[col] * weights).sum() / total_w) if total_w > 0 else None

    rows = []
    all_ids = df["mlb_id"].unique()
    for pid in all_ids:
        p_aaa = aaa[aaa["mlb_id"] == pid]
        p_aa  = aa[aa["mlb_id"] == pid]
        # 최근 AAA 시즌 사용 (없으면 AA)
        p = p_aaa if len(p_aaa) > 0 else p_aa
        if p.empty:
            continue

        total_w = p[weight_col].sum()
        seasons_used = sorted(p["season"].unique().tolist())
        team_latest = p.sort_values("season").iloc[-1]["team"]
        level_latest = "AAA" if p.sort_values("season").iloc[-1]["sport_id"] == SPORT_AAA else "AA"

        row: dict = {
            "mlb_id": pid,
            "role": group,
            "level": level_latest,
            "team_latest": team_latest,
            "seasons_used": str(seasons_used),
            weight_col: total_w,
        }
        float_cols = [c for c in p.columns if p[c].dtype == float or p[c].dtype in (np.float64, np.float32)]
        for c in float_cols:
            row[c] = weighted_mean(p, c, weight_col)

        if group == "hitter":
            # 집계 HR/BB/K (합산)
            row["hr_total"] = int(p["hr"].sum())
            row["bb_total"] = int(p["bb"].sum())
            row["so_total"] = int(p["so"].sum())
        elif group == "starter":
            row["gs_total"] = int(p["gs"].sum())
            row["ip_total"] = round(p["ip"].sum(), 1)

        rows.append(row)

    result = pd.DataFrame(rows)
    # sport_id 컬럼 제거 (집계 후 불필요)
    if "sport_id" in result.columns:
        result = result.drop(columns=["sport_id"])
    return result


# ── 3. Savant 집계 ───────────────────────────────────────────────────────────

def load_savant_aggregates(seasons: list[int] = RECENT_SEASONS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Savant parquet에서 타자/투수 집계 지표 계산."""
    batter_chunks, pitcher_chunks = [], []

    for yr in seasons:
        p = SAVANT_DIR / f"savant_statcast_{yr}.parquet"
        if not p.exists():
            print(f"  [WARN] Savant {yr} 없음: {p}")
            continue
        print(f"  Savant {yr} 읽는 중...")

        b_cols = [c for c in SAVANT_BATTER_COLS if c in _get_parquet_cols(p)]
        s_cols = [c for c in SAVANT_PITCHER_COLS if c in _get_parquet_cols(p)]

        df = pd.read_parquet(p, columns=list(set(b_cols + s_cols)))
        df["game_year"] = yr

        # 타자 집계
        batters = df[df["type"].isin(["X", "S", "B"])].copy()
        if "batter" in batters.columns:
            batter_chunks.append(_agg_savant_batters(batters, yr))

        # 투수 집계
        pitchers = df.copy()
        if "pitcher" in pitchers.columns:
            pitcher_chunks.append(_agg_savant_pitchers(pitchers, yr))

    def _concat(chunks: list[pd.DataFrame]) -> pd.DataFrame:
        if not chunks:
            return pd.DataFrame()
        df = pd.concat([c for c in chunks if not c.empty], ignore_index=True)
        str_cols = [c for c in df.columns if df[c].dtype == object and c != "mlb_id"]
        num_agg = df.groupby("mlb_id").mean(numeric_only=True).reset_index()
        # 문자열 컬럼은 첫 번째 값으로 복원
        if str_cols:
            str_agg = df.groupby("mlb_id")[str_cols].first().reset_index()
            num_agg = num_agg.merge(str_agg, on="mlb_id", how="left")
        return num_agg

    return _concat(batter_chunks), _concat(pitcher_chunks)


def _get_parquet_cols(path: Path) -> list[str]:
    import pyarrow.parquet as pq
    return pq.read_schema(path).names


def _agg_savant_batters(df: pd.DataFrame, yr: int) -> pd.DataFrame:
    df = df.copy()
    df["launch_speed"] = pd.to_numeric(df.get("launch_speed"), errors="coerce")
    df["xwoba"]        = pd.to_numeric(df.get("estimated_woba_using_speedangle"), errors="coerce")
    df["xba"]          = pd.to_numeric(df.get("estimated_ba_using_speedangle"), errors="coerce")
    df["xslg"]         = pd.to_numeric(df.get("estimated_slg_using_speedangle"), errors="coerce")

    in_play = df[df["type"] == "X"]
    has_speed = in_play["launch_speed"].notna()

    rows = []
    for pid, g in df.groupby("batter"):
        ip_g = in_play[in_play["batter"] == pid]
        spd_g = ip_g[ip_g["launch_speed"].notna()]
        n_pitches = len(g)
        if n_pitches < 50:
            continue

        name = g["player_name"].iloc[0] if "player_name" in g.columns else ""
        swings = g[g["description"].isin(["swinging_strike", "hit_into_play", "foul",
                                            "swinging_strike_blocked", "foul_tip"])]
        misses = g[g["description"].isin(["swinging_strike", "swinging_strike_blocked", "foul_tip"])]
        in_zone = g[g["zone"].between(1, 9)] if "zone" in g.columns else pd.DataFrame()
        out_zone = g[~g["zone"].between(1, 9)] if "zone" in g.columns else pd.DataFrame()

        in_zone_swings   = in_zone[in_zone["description"].isin(["swinging_strike","hit_into_play","foul","swinging_strike_blocked","foul_tip"])] if not in_zone.empty else pd.DataFrame()
        out_zone_swings  = out_zone[out_zone["description"].isin(["swinging_strike","hit_into_play","foul","swinging_strike_blocked","foul_tip"])] if not out_zone.empty else pd.DataFrame()

        rows.append({
            "mlb_id":        pid,
            "player_name":   name,
            "n_pitches":     n_pitches,
            "avg_ev":        spd_g["launch_speed"].mean() if len(spd_g) else None,
            "hard_hit_pct":  (spd_g["launch_speed"] >= 95).mean() if len(spd_g) else None,
            "xwoba":         ip_g["xwoba"].mean() if len(ip_g) else None,
            "xba":           ip_g["xba"].mean() if len(ip_g) else None,
            "xslg":          ip_g["xslg"].mean() if len(ip_g) else None,
            "whiff_pct":     len(misses) / len(swings) if len(swings) else None,
            "zone_sw_pct":   len(in_zone_swings) / len(in_zone) if len(in_zone) else None,
            "chase_pct":     len(out_zone_swings) / len(out_zone) if len(out_zone) else None,
        })
    return pd.DataFrame(rows)


def _agg_savant_pitchers(df: pd.DataFrame, yr: int) -> pd.DataFrame:
    df = df.copy()
    df["release_speed"] = pd.to_numeric(df.get("release_speed"), errors="coerce")

    rows = []
    for pid, g in df.groupby("pitcher"):
        n_pitches = len(g)
        if n_pitches < 50:
            continue

        name = g["player_name"].iloc[0] if "player_name" in g.columns else ""
        throws = g["p_throws"].iloc[0] if "p_throws" in g.columns else ""
        arm_angle = g["arm_angle"].mean() if "arm_angle" in g.columns else None

        swings = g[g["description"].isin(["swinging_strike","hit_into_play","foul","swinging_strike_blocked","foul_tip"])]
        misses = g[g["description"].isin(["swinging_strike","swinging_strike_blocked","foul_tip"])]
        in_zone  = g[g["zone"].between(1, 9)] if "zone" in g.columns else pd.DataFrame()
        out_zone = g[~g["zone"].between(1, 9)] if "zone" in g.columns else pd.DataFrame()
        out_zone_swings = out_zone[out_zone["description"].isin(["swinging_strike","hit_into_play","foul","swinging_strike_blocked","foul_tip"])] if not out_zone.empty else pd.DataFrame()

        ff = g[g["pitch_name"].isin(["4-Seam Fastball","Fastball"])] if "pitch_name" in g.columns else pd.DataFrame()

        rows.append({
            "mlb_id":        pid,
            "player_name":   name,
            "p_throws":      throws,
            "n_pitches":     n_pitches,
            "avg_velo":      ff["release_speed"].mean() if len(ff) else g["release_speed"].mean(),
            "max_velo":      g["release_speed"].max(),
            "whiff_pct":     len(misses) / len(swings) if len(swings) else None,
            "zone_pct":      len(in_zone) / n_pitches if n_pitches else None,
            "chase_pct":     len(out_zone_swings) / len(out_zone) if len(out_zone) else None,
            "arm_angle":     arm_angle,
        })
    return pd.DataFrame(rows)


# ── 4. 필터링 ────────────────────────────────────────────────────────────────

def filter_hitters(hitters: pd.DataFrame, available_ids: set[int], on_40man: set[int]) -> pd.DataFrame:
    if hitters.empty:
        return pd.DataFrame()
    df = hitters.copy()
    df["available"] = df["mlb_id"].isin(available_ids)
    df["on_40man"]  = df["mlb_id"].isin(on_40man)
    df["acquirable"] = df["available"] | ~df["on_40man"]

    # 2단계 임계값 필터
    mask = (
        (df["pa"].fillna(0) >= HITTER_FILTER["min_pa_aaa"]) &
        (df["ops"].fillna(0) >= HITTER_FILTER["min_ops_aaa"]) &
        (df["k_pct"].fillna(1) <= HITTER_FILTER["max_k_pct"]) &
        (df["bb_pct"].fillna(0) >= HITTER_FILTER["min_bb_pct"])
    )
    return df[mask].sort_values("ops", ascending=False).reset_index(drop=True)


def filter_starters(starters: pd.DataFrame, available_ids: set[int], on_40man: set[int]) -> pd.DataFrame:
    if starters.empty:
        return pd.DataFrame()
    df = starters.copy()
    df["available"] = df["mlb_id"].isin(available_ids)
    df["on_40man"]  = df["mlb_id"].isin(on_40man)
    df["acquirable"] = df["available"] | ~df["on_40man"]

    mask = (
        (df["ip"].fillna(0) >= STARTER_FILTER["min_ip_aaa"]) &
        (df["era"].fillna(99) <= STARTER_FILTER["max_era_aaa"]) &
        (df["k9"].fillna(0) >= STARTER_FILTER["min_k9"]) &
        (df["bb9"].fillna(99) <= STARTER_FILTER["max_bb9"]) &
        (df["gs_ratio"].fillna(0) >= STARTER_FILTER["min_gs_ratio"])
    )
    return df[mask].sort_values("era", ascending=True).reset_index(drop=True)


# ── 5. SSG Fit 스코어 ────────────────────────────────────────────────────────
#
# 1단계 feature contract 기반 0~1 스코어
# Assumption #18: pre-arrival 프록시 점수이며, 실제 SSG fit은 4단계 번역 모델 이후 확정

def score_hitter_ssg_fit(df: pd.DataFrame) -> pd.DataFrame:
    """
    SSG 약점 보완 + KBO 수용가능 결함 기반 타자 fit 점수 (0-100):

    [SSG 약점 대응]
    S1. runner_advancement (25pt)
        - SSG 약점: "1루 주자만" OPS 리그 10위 → 주자 진루 실패
        - 필요 능력: 갭 장타 + 볼넷으로 진루 가능한 상대 수비 압박
        - Proxy: ISO(장타 능력) + BB%(볼카운트 관리) + hard_hit_pct(타구 질)

    S2. two_out_abs_discipline (25pt)
        - SSG 약점: 2사 OPS 리그 8위 + KBO ABS 환경 적응
        - 필요 능력: 존 안 공 선별 → 볼넷/2루타, 체이스 최소화
        - Proxy: chase_pct(낮을수록 good) + whiff_pct + BB%

    S3. early_inning_pressure (20pt)
        - SSG 약점: 초반(1-3이닝) OPS 리그 8위
        - 필요 능력: 상대 선발 이른 투구수 유도 + 초반 득점 생산
        - Proxy: xwOBA(타구 품질 → 이닝 초 타석에서 승부) + OPS

    [KBO 수용가능 결함 보너스]
    S4. kbo_masked_flaw_bonus (15pt)
        - MLB에서 실패한 이유가 KBO 환경에서는 드러나지 않는 경우 추가점
        - 케이스 A: 높은 K%(24-30%) + 높은 xwOBA(≥0.380) → KBO 투수 수준↓로 K% 감소 예상
        - 케이스 B: 파워는 있으나 avg 낮음(≤.240) → KBO DH 기용으로 수비 약점 무관
        - 케이스 C: PCL 인플레이션 이지만 xwOBA는 park-neutral → 실제 파워 진짜

    S5. acquisition_tier_bonus (15pt)
        - 영입 현실성 반영
        - A_mlb_reject: 15pt, A_dfa_milb: 12pt, B_fa: 10pt, C_outrighted: 7pt
    """
    df = df.copy()

    def runner_advancement(r: pd.Series) -> float:
        # SSG 1루 주자 진루 실패 보완: 장타 + 볼넷 + 타구 속도
        iso   = r.get("iso") or 0
        bb    = r.get("bb_pct") or 0
        hh    = r.get("hard_hit_pct") or None
        score = 0.0
        # ISO: 2루타/3루타 → 1루 주자 홈 또는 3루
        if iso >= 0.240: score += 12
        elif iso >= 0.200: score += 8
        elif iso >= 0.160: score += 5
        elif iso >= 0.130: score += 2
        # BB%: 볼넷으로 주자 1루 → 추가 선행주자 생성 압박
        if bb >= 0.130: score += 10
        elif bb >= 0.100: score += 7
        elif bb >= 0.080: score += 3
        # 타구 속도: 강한 타구 = 외야수 깊이 밀어 주자 진루
        if hh is not None:
            if hh >= 0.48: score += 3
            elif hh >= 0.42: score += 2
        return min(score, 25)

    def two_out_abs_discipline(r: pd.Series) -> float:
        # SSG 2사 OPS 8위 + KBO ABS 적응: 존 밖 공 안 휘두름
        bb    = r.get("bb_pct") or 0
        k     = r.get("k_pct") or 1
        chase = r.get("chase_pct")    # Savant: 존 밖 스윙률
        whiff = r.get("whiff_pct")    # Savant: 스윙 헛스윙률
        score = 0.0
        # 체이스율: ABS에서 볼 판정이 정확해질수록 존밖 낚시 효과↓ → 체이스 낮은 선수 유리
        if chase is not None:
            if chase <= 0.23: score += 12
            elif chase <= 0.27: score += 8
            elif chase <= 0.31: score += 4
        else:
            # Savant 없으면 BB%로 대체 (assumption #13)
            if bb >= 0.120: score += 8
            elif bb >= 0.090: score += 5
            elif bb >= 0.070: score += 2
        # 헛스윙률: 낮을수록 존 안 컨택 능력 우수
        if whiff is not None:
            if whiff <= 0.24: score += 8
            elif whiff <= 0.28: score += 5
            elif whiff <= 0.32: score += 2
        else:
            if k <= 0.22: score += 5
            elif k <= 0.26: score += 2
        # BB% 추가 (체이스/whiff 없을 때 의존도 높임)
        if chase is None and whiff is None:
            if bb >= 0.120: score += 5
            elif bb >= 0.090: score += 2
        return min(score, 25)

    def early_inning_pressure(r: pd.Series) -> float:
        # 초반 타석 득점 생산력: xwOBA(타구 품질 park-neutral) + OPS
        xwob = r.get("xwoba")
        ops  = r.get("ops") or 0
        score = 0.0
        # xwOBA 우선 (park-neutral, PCL 인플레이션 무시)
        if xwob is not None:
            if xwob >= 0.420: score += 20
            elif xwob >= 0.390: score += 15
            elif xwob >= 0.360: score += 10
            elif xwob >= 0.320: score += 5
        else:
            # Savant 없으면 OPS (PCL 선수는 discount 필요 → pcl_inflated 페널티)
            effective_ops = ops * (0.93 if r.get("pcl_inflated") else 1.0)
            if effective_ops >= 0.900: score += 14
            elif effective_ops >= 0.860: score += 9
            elif effective_ops >= 0.820: score += 4
        return min(score, 20)

    def kbo_masked_flaw_bonus(r: pd.Series) -> float:
        # MLB 실패 원인이 KBO 환경에서 안 드러나는 경우
        k    = r.get("k_pct") or 0
        xwob = r.get("xwoba")
        iso  = r.get("iso") or 0
        avg  = r.get("avg") or 0
        pcl  = r.get("pcl_inflated", False)
        score = 0.0
        # 케이스 A: K%높음(MLB 실패) + xwOBA양호 → KBO 투수 수준↓로 K% 자연 감소
        if 0.24 <= k <= 0.32 and xwob is not None and xwob >= 0.380:
            score += 10  # 핵심 "묻히는 결함" 패턴
        elif 0.24 <= k <= 0.32 and xwob is None and iso >= 0.210:
            score += 6
        # 케이스 B: avg 낮지만 ISO 높음 → KBO DH 기용으로 수비 약점 무관
        if avg <= 0.240 and iso >= 0.220:
            score += 3
        # 케이스 C: PCL 인플레이션이지만 xwOBA park-neutral → 실제 파워 존재
        if pcl and xwob is not None and xwob >= 0.390:
            score += 2  # PCL 경보를 덜어줌
        return min(score, 15)

    def acquisition_tier_bonus(r: pd.Series) -> float:
        tier = r.get("acquisition_tier", "")
        if tier.startswith("A_mlb"): return 15
        if tier.startswith("A_dfa"): return 12
        if tier.startswith("B_fa"):  return 10
        if tier.startswith("C_"):    return 7
        return 0

    df["fit_runner_advancement"]       = df.apply(runner_advancement, axis=1)
    df["fit_two_out_abs_discipline"]   = df.apply(two_out_abs_discipline, axis=1)
    df["fit_early_inning_pressure"]    = df.apply(early_inning_pressure, axis=1)
    df["fit_kbo_masked_flaw"]          = df.apply(kbo_masked_flaw_bonus, axis=1)
    df["fit_acquisition_tier"]         = df.apply(acquisition_tier_bonus, axis=1)
    df["ssg_fit_score"] = (
        df["fit_runner_advancement"] +
        df["fit_two_out_abs_discipline"] +
        df["fit_early_inning_pressure"] +
        df["fit_kbo_masked_flaw"] +
        df["fit_acquisition_tier"]
    )
    return df.sort_values("ssg_fit_score", ascending=False).reset_index(drop=True)


def score_starter_ssg_fit(df: pd.DataFrame) -> pd.DataFrame:
    """
    SSG 약점 보완 + KBO 수용가능 결함 기반 선발 fit 점수 (0-100):

    [SSG 약점 대응]
    P1. early_inning_support (30pt)
        - SSG 약점: 초반(1-3이닝) OPS 리그 8위 → 상대 선발이 SSG를 초반에 압박
        - 필요 능력: 선발 자신이 초반을 장악해 SSG 타선이 마운드 운영 주도권을 가져옴
        - 지표: ERA(초반 실점 proxy) + WHIP (선발이 초반 무너지면 SSG 역전 구도 불리)

    P2. inning_depth (25pt)
        - SSG 약점: 초반 불리한 상황에서 불펜 조기 소모 → 이닝 깊이 있는 선발이 해결
        - 필요 능력: 6이닝 이상 자력 완투 가능 → SSG 불펜 절약
        - 지표: IP/GS + GS비율

    P3. contact_management (25pt)
        - KBO 타선 특성: KBO 타자들은 직구 중심 + 패스트볼 타이밍이 MLB보다 느림
        - 필요 능력: 삼진보다 땅볼 + 낮은 볼넷 (KBO에서 BB는 실점 직결)
        - 지표: BB9(낮을수록) + K9 + K/BB

    [KBO 수용가능 결함 보너스]
    P4. kbo_masked_flaw_bonus (10pt)
        - 케이스 A: 낮은 구속(89-92mph) + 좋은 커맨드(BB9 ≤ 2.8)
          → MLB에서 구속 부족으로 실패, KBO에서는 평균 구속↓로 피해 작음
        - 케이스 B: 높은 BB9(3.5-4.5) + 높은 K9(≥8.5)
          → MLB에서 제구 불안으로 실패, KBO ABS에서 일부 볼 판정 유리해질 수 있음 (단, 리스크)
        - 케이스 C: WHIP 높지만 K9 높음(삼진=ABS 타자 상대 유리)
          → 맞힘 허용 많지만 삼진으로 지우는 스타일

    P5. acquisition_tier_bonus (10pt)
        - 영입 현실성 + MLB 실패 검증
    """
    df = df.copy()

    def early_inning_support(r: pd.Series) -> float:
        # SSG 초반 OPS 8위 → 선발이 초반 장악해야 SSG 공격진이 주도권 회복
        era  = r.get("era") or 99
        whip = r.get("whip") or 99
        score = 0.0
        if era <= 3.20: score += 30
        elif era <= 3.70: score += 22
        elif era <= 4.10: score += 13
        elif era <= 4.50: score += 6
        # WHIP 페널티: 주자 많이 내보내면 SSG 수비 부담
        score -= max(0, (whip - 1.25) * 18)
        return max(0, min(score, 30))

    def inning_depth(r: pd.Series) -> float:
        # SSG 불펜 보호: 선발이 6이닝 이상 → 이닝 부담 줄임
        ip   = r.get("ip_total") or 0
        gs   = r.get("gs_total") or 1
        gsr  = r.get("gs_ratio") or 0
        ipgs = ip / gs if gs else 0
        score = 0.0
        if ipgs >= 6.0: score += 20
        elif ipgs >= 5.5: score += 13
        elif ipgs >= 5.0: score += 6
        if gsr >= 0.80: score += 5
        elif gsr >= 0.65: score += 3
        elif gsr >= 0.50: score += 1
        return min(score, 25)

    def contact_management(r: pd.Series) -> float:
        # KBO 타자는 MLB보다 빠른 타이밍 약함 → 제구+변화구로 땅볼 유도
        bb9 = r.get("bb9") or 99
        k9  = r.get("k9") or 0
        kbb = r.get("k_bb_ratio") or 0
        whiff = r.get("whiff_pct")
        score = 0.0
        # BB9: 낮을수록 KBO에서 실점 억제 (볼넷 → 진루타 → 실점 패턴)
        if bb9 <= 2.3: score += 15
        elif bb9 <= 2.8: score += 11
        elif bb9 <= 3.3: score += 7
        elif bb9 <= 3.8: score += 3
        # K9: 삼진 = ABS 환경에서 타자 기술보다 투수 유리 (ABS볼→스윙유도)
        if k9 >= 9.0: score += 8
        elif k9 >= 7.5: score += 5
        elif k9 >= 6.5: score += 2
        # whiff%: 헛스윙 많을수록 KBO 타자에게 효과적
        if whiff is not None:
            if whiff >= 0.30: score += 4
            elif whiff >= 0.25: score += 2
        elif kbb >= 3.0: score += 2
        return min(score, 25)

    def kbo_masked_flaw_bonus(r: pd.Series) -> float:
        # MLB 실패 원인이 KBO 환경에서 완화되는 경우
        bb9   = r.get("bb9") or 99
        k9    = r.get("k9") or 0
        velo  = r.get("avg_velo")
        whiff = r.get("whiff_pct")
        score = 0.0
        # 케이스 A: 저구속(89-92) + 좋은 커맨드 → KBO 평균 구속↓ 환경에서 생존 가능
        if velo is not None and 88 <= velo <= 92 and bb9 <= 2.8:
            score += 8
        # 케이스 B: 볼넷 많지만 K9 높음 → KBO에서 ABS 볼 판정이 더 일관적이어서 일부 BB 감소 가능
        elif 3.5 <= bb9 <= 4.5 and k9 >= 8.5:
            score += 5
        # 케이스 C: whiff% 높음 → ABS 스트라이크존 일관성 → 스윙유도 투수 유리
        if whiff is not None and whiff >= 0.28:
            score += 3
        return min(score, 10)

    def acquisition_tier_bonus(r: pd.Series) -> float:
        tier = r.get("acquisition_tier", "")
        if tier.startswith("A_mlb"): return 10
        if tier.startswith("A_dfa"): return 8
        if tier.startswith("B_fa"):  return 6
        if tier.startswith("C_"):    return 4
        return 0

    df["fit_early_inning_support"]   = df.apply(early_inning_support, axis=1)
    df["fit_inning_depth"]           = df.apply(inning_depth, axis=1)
    df["fit_contact_management"]     = df.apply(contact_management, axis=1)
    df["fit_kbo_masked_flaw"]        = df.apply(kbo_masked_flaw_bonus, axis=1)
    df["fit_acquisition_tier"]       = df.apply(acquisition_tier_bonus, axis=1)
    df["ssg_fit_score"] = (
        df["fit_early_inning_support"] +
        df["fit_inning_depth"] +
        df["fit_contact_management"] +
        df["fit_kbo_masked_flaw"] +
        df["fit_acquisition_tier"]
    )
    return df.sort_values("ssg_fit_score", ascending=False).reset_index(drop=True)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main(use_savant: bool = True) -> None:
    print("[candidate_market] 시작\n")

    # ── 가용성 ──────────────────────────────────────────────────────────────
    print("[1/5] 가용 선수 파악 (트랜잭션 + 40인 로스터)...")
    available_ids, avail_df = load_available_player_ids()
    on_40man = load_40man_ids()
    avail_df.to_csv(OUT / "candidate_availability_flags.csv", index=False, encoding="utf-8-sig")
    print(f"  DFA/Released/FA 선수: {len(available_ids)}명")
    print(f"  현재 40인 로스터:      {len(on_40man)}명")
    print(f"  트랜잭션 타입별:")
    for ttype, cnt in avail_df["txn_type"].value_counts().items():
        print(f"    {ttype}: {cnt}명")

    # ── MiLB 성적 ───────────────────────────────────────────────────────────
    print("\n[2/5] MiLB/MLB AAA 성적 파싱 (2023-2025)...")
    hitters_raw, starters_raw = parse_milb_stats()
    print(f"  타자 레코드: {len(hitters_raw)}명  |  투수 레코드: {len(starters_raw)}명")

    # ── Savant 집계 ─────────────────────────────────────────────────────────
    savant_bat, savant_pit = pd.DataFrame(), pd.DataFrame()
    if use_savant:
        print("\n[3/5] Savant 집계 (2023-2025, 시간 소요)...")
        savant_bat, savant_pit = load_savant_aggregates()
        if not savant_bat.empty:
            savant_bat.to_csv(OUT / "candidate_savant_bat_aggregates.csv", index=False, encoding="utf-8-sig")
            print(f"  Savant 타자: {len(savant_bat)}명")
        if not savant_pit.empty:
            savant_pit.to_csv(OUT / "candidate_savant_pit_aggregates.csv", index=False, encoding="utf-8-sig")
            print(f"  Savant 투수: {len(savant_pit)}명")
    else:
        print("\n[3/5] Savant 집계 생략 (--no-savant)")

    # ── 나이·트랜잭션 타입 맵 빌드 ──────────────────────────────────────────
    age_map     = _build_age_map()
    txn_map     = _build_txn_type_map(avail_df)

    # ── 필터링 ──────────────────────────────────────────────────────────────
    print("\n[4/5] 2단계 threshold 필터링 + SSG fit 스코어...")
    hitter_pool = filter_hitters(hitters_raw, available_ids, on_40man)
    starter_pool = filter_starters(starters_raw, available_ids, on_40man)

    # Savant 컬럼 합치기 (실제 존재하는 컬럼만 선택)
    sav_n_bat = pd.DataFrame()
    sav_n_pit = pd.DataFrame()
    if not savant_bat.empty and not hitter_pool.empty:
        bat_want = ["mlb_id","n_pitches","avg_ev","hard_hit_pct","xwoba","xba","xslg",
                    "whiff_pct","zone_sw_pct","chase_pct"]
        bat_cols = [c for c in bat_want if c in savant_bat.columns]
        hitter_pool = hitter_pool.merge(savant_bat[bat_cols], on="mlb_id", how="left")
        sav_n_bat = savant_bat[["mlb_id","n_pitches"]].copy() if "n_pitches" in savant_bat.columns else sav_n_bat
    if not savant_pit.empty and not starter_pool.empty:
        pit_want = ["mlb_id","n_pitches","avg_velo","max_velo","whiff_pct","zone_pct",
                    "chase_pct","arm_angle","p_throws"]
        pit_cols = [c for c in pit_want if c in savant_pit.columns]
        starter_pool = starter_pool.merge(savant_pit[pit_cols], on="mlb_id", how="left")
        sav_n_pit = savant_pit[["mlb_id","n_pitches"]].copy() if "n_pitches" in savant_pit.columns else sav_n_pit

    # ── 이름 + 나이 + 포지션/국적 + 트랜잭션 타입 + acquisition_tier ─────────
    # NOTE: _enrich 먼저 실행해야 acquisition_tier가 채점 함수에서 사용 가능
    id_to_name = _build_name_map(avail_df)
    player_meta = _build_player_meta()

    def _enrich(df: pd.DataFrame, role: str, sav_n: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        df = df.copy()
        df.insert(1, "full_name", df["mlb_id"].map(id_to_name).fillna(""))
        df["age"]           = df["mlb_id"].map(age_map)
        df["position"]      = df["mlb_id"].map(lambda x: player_meta.get(int(x), {}).get("position", "?"))
        df["bat_side"]      = df["mlb_id"].map(lambda x: player_meta.get(int(x), {}).get("bat_side", "?"))
        df["pitch_hand"]    = df["mlb_id"].map(lambda x: player_meta.get(int(x), {}).get("pitch_hand", "?"))
        df["birth_country"] = df["mlb_id"].map(lambda x: player_meta.get(int(x), {}).get("birth_country", "?"))
        df["txn_type"]      = df["mlb_id"].map(txn_map).fillna("")
        df["pcl_inflated"]  = df["team_latest"].isin(PCL_INFLATED_TEAMS)
        # KBO 외국인 자격 불가 플래그
        df["kbo_ineligible"] = df["birth_country"].isin(KOREAN_BIRTH_COUNTRIES)

        # Savant 피치 수 (MLB 노출 지표)
        if not sav_n.empty:
            df = df.merge(sav_n.rename(columns={"n_pitches": "mlb_pitches"}), on="mlb_id", how="left")
        else:
            df["mlb_pitches"] = None

        # acquisition_tier
        xwoba_col = "xwoba" if role == "hitter" else None
        era_col   = "era"   if role == "starter" else None
        perf_col  = xwoba_col or era_col
        df["acquisition_tier"] = df.apply(
            lambda r: _classify_acquisition(
                mlb_id=r["mlb_id"],
                available=bool(r.get("available")),
                age=age_map.get(int(r["mlb_id"])),
                txn_type=txn_map.get(int(r["mlb_id"])),
                savant_pitches=r.get("mlb_pitches"),
                xwoba_or_era=r.get(perf_col) if perf_col else None,
                role=role,
            ),
            axis=1,
        )
        # KBO 외국인 자격 불가 선수는 D로 강제 재분류
        df.loc[df["kbo_ineligible"], "acquisition_tier"] = "D_kbo_ineligible"
        return df

    hitter_pool  = _enrich(hitter_pool,  "hitter",  sav_n_bat)
    starter_pool = _enrich(starter_pool, "starter", sav_n_pit)

    # 포지션 필터: 타자는 외야/코너 내야만 (포수·2루수 제외)
    if not hitter_pool.empty and "position" in hitter_pool.columns:
        non_eligible_pos = ~hitter_pool["position"].isin(KBO_ELIGIBLE_HITTER_POS)
        hitter_pool.loc[non_eligible_pos, "acquisition_tier"] = "D_wrong_position"

    # ── acquisition_tier 확정 후 채점 ─────────────────────────────────────────
    hitter_pool  = score_hitter_ssg_fit(hitter_pool)
    starter_pool = score_starter_ssg_fit(starter_pool)

    # D등급(프로스펙트/40인 잔류)은 전체 CSV에는 남기되 별도 플래그로 표시
    # 요약 출력은 A/B/C 등급만 표시
    hitter_pool.to_csv(OUT / "candidate_hitter_pool.csv", index=False, encoding="utf-8-sig")
    starter_pool.to_csv(OUT / "candidate_starter_pool.csv", index=False, encoding="utf-8-sig")

    n_h_realistic = (hitter_pool["acquisition_tier"].str.startswith(("A","B","C"))).sum()
    n_s_realistic = (starter_pool["acquisition_tier"].str.startswith(("A","B","C"))).sum()
    print(f"  타자 통과: {len(hitter_pool)}명 (현실적 영입 A/B/C: {n_h_realistic}명)")
    print(f"  투수 통과: {len(starter_pool)}명 (현실적 영입 A/B/C: {n_s_realistic}명)")

    # ── 요약 출력 ────────────────────────────────────────────────────────────
    print("\n[5/5] 상위 후보 요약...")
    _print_summary(hitter_pool, starter_pool)

    print("\n[완료] 출력 파일:")
    for f in ["candidate_availability_flags.csv", "candidate_hitter_pool.csv",
              "candidate_starter_pool.csv", "candidate_savant_bat_aggregates.csv",
              "candidate_savant_pit_aggregates.csv"]:
        fp = OUT / f
        if fp.exists():
            print(f"  outputs/tables/{f}")


def _print_summary(hitters: pd.DataFrame, starters: pd.DataFrame) -> None:
    print("\n" + "=" * 70)
    print("3단계 후보 시장 요약 (A/B/C 등급 = 현실적 영입 대상만)")
    print("=" * 70)
    print("등급: A_mlb_reject=MLB 실패 확인, A_dfa_milb=DFA(MLB경험없음),")
    print("      B_fa_veteran/mid=FA 베테랑, C_outrighted=Outrighted")
    print("      D=프로스펙트/40인 잔류 (제외)")

    h_display_cols = [
        "mlb_id","full_name","age","position","bat_side","level","team_latest",
        "pa","ops","xwoba","iso","bb_pct","k_pct","chase_pct","whiff_pct",
        "mlb_pitches","pcl_inflated","acquisition_tier",
        "fit_runner_advancement","fit_two_out_abs_discipline",
        "fit_early_inning_pressure","fit_kbo_masked_flaw","fit_acquisition_tier",
        "ssg_fit_score",
    ]
    s_display_cols = [
        "mlb_id","full_name","age","pitch_hand","level","team_latest",
        "ip_total","era","whip","k9","bb9","k_bb_ratio","avg_velo","arm_angle",
        "mlb_pitches","pcl_inflated","acquisition_tier",
        "fit_early_inning_support","fit_inning_depth",
        "fit_contact_management","fit_kbo_masked_flaw","fit_acquisition_tier",
        "ssg_fit_score",
    ]

    # A/B/C 등급만 필터
    def _abc(df: pd.DataFrame) -> pd.DataFrame:
        if "acquisition_tier" not in df.columns:
            return df
        return df[df["acquisition_tier"].str.startswith(("A", "B", "C"))].copy()

    h_real = _abc(hitters).sort_values("ssg_fit_score", ascending=False)
    s_real = _abc(starters).sort_values("ssg_fit_score", ascending=False)

    print(f"\n[타자 상위 20명 - 현실적 영입 대상 ({len(h_real)}명)]")
    h_cols = [c for c in h_display_cols if c in h_real.columns]
    print(h_real[h_cols].head(20).to_string(index=False))

    print(f"\n[선발 상위 20명 - 현실적 영입 대상 ({len(s_real)}명)]")
    s_cols = [c for c in s_display_cols if c in s_real.columns]
    print(s_real[s_cols].head(20).to_string(index=False))

    print("\n[등급별 분포 - 타자]")
    if "acquisition_tier" in hitters.columns:
        for tier, cnt in hitters["acquisition_tier"].value_counts().items():
            print(f"  {tier}: {cnt}명")
    print("\n[등급별 분포 - 선발]")
    if "acquisition_tier" in starters.columns:
        for tier, cnt in starters["acquisition_tier"].value_counts().items():
            print(f"  {tier}: {cnt}명")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="후보 시장 구축")
    parser.add_argument("--no-savant", action="store_true", help="Savant 집계 생략")
    args = parser.parse_args()
    main(use_savant=not args.no_savant)
