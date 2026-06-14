#!/usr/bin/env python3
"""Build the presentation and scoring bridge for SSG Layer 1.

Run 017 does not introduce a new hidden-weakness message. It converts the
validated Run 016 message into audience-facing language, objection handling,
candidate feature contracts, and freeze criteria so later layers can score
players against the same SSG-specific need.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs/tables"


def read_table(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT_DIR / name)


def pct(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:.3f}"


def signed(value: float) -> str:
    if pd.isna(value):
        return "NA"
    return f"{value:+.2f}"


def row_by(df: pd.DataFrame, column: str, value: str) -> pd.Series:
    hit = df[df[column].eq(value)]
    if hit.empty:
        raise ValueError(f"missing {column}={value}")
    return hit.iloc[0]


def maybe_card(cards: pd.DataFrame, card_id: str) -> str:
    hit = cards[cards["card_id"].eq(card_id)]
    if hit.empty:
        return "not_available"
    row = hit.iloc[0]
    return f"{row['claim']} ({row['observed']}; {row['comparison']})"


def build_plain_story(final_msg: pd.Series, decisions: pd.DataFrame, controls: pd.DataFrame) -> pd.DataFrame:
    r1 = row_by(decisions, "rule_id", "R1_rhp_low_of_conversion_run_trade")
    r2 = row_by(decisions, "rule_id", "R2_rhp_ofdh_run_kill")
    r3 = row_by(decisions, "rule_id", "R3_extra_out_high_of_void")
    nc_hr = row_by(controls, "rule_id", "NC1_of_hr_zero")
    nc_rbi = row_by(controls, "rule_id", "NC5_of_rbi_low_only")

    rows = [
        {
            "story_level": "one_sentence",
            "audience": "general_public",
            "headline_ko": "SSG의 문제는 외야 홈런 부족이 아니라 경기 복구 루트의 잠김이다.",
            "plain_ko": "상대 우투 선발에게 외야와 지명타자 쪽에서 출루와 타점 전환이 막히고, 병살/도루자 같은 공격 단절이나 비자책 실점이 겹치면 SSG는 따라갈 길이 급격히 사라진다.",
            "proof_point": f"핵심 룰 3개가 승률 {pct(r1['win_pct'])}/{pct(r2['win_pct'])}/{pct(r3['win_pct'])}, 평균 득실 {signed(r1['avg_run_diff'])}/{signed(r2['avg_run_diff'])}/{signed(r3['avg_run_diff'])}로 나타났다.",
            "what_it_does_not_mean": f"외야 홈런 0개 경기만 보면 승률 {pct(nc_hr['win_pct'])}, 평균 득실 {signed(nc_hr['avg_run_diff'])}라서 단순 장타 부족 설명보다 훨씬 약하다.",
        },
        {
            "story_level": "thirty_second",
            "audience": "presentation_opening",
            "headline_ko": "SSG는 큰 한 방보다 '막힌 이닝을 다시 여는 선수'가 더 절실하다.",
            "plain_ko": "홈런을 더 치는 선수를 찾는 것이 아니라, 우투수 상대로 1루 주자를 득점권으로 보내고, 2스트라이크 이후에도 이닝을 죽이지 않고, 수비 실수 뒤에도 무너짐을 끊는 유형을 찾아야 한다.",
            "proof_point": f"RHP+낮은 외야 전환+상대 6득점 이상 조합은 {int(r1['games'])}경기에서 승률 {pct(r1['win_pct'])}, 평균 득실 {signed(r1['avg_run_diff'])}였다.",
            "what_it_does_not_mean": f"외야 RBI < 3만 보면 승률 {pct(nc_rbi['win_pct'])}, 평균 득실 {signed(nc_rbi['avg_run_diff'])}라서 '그냥 외야 타점 부족'도 충분한 설명이 아니다.",
        },
        {
            "story_level": "professor_version",
            "audience": "methodology_defense",
            "headline_ko": "단일 리더보드가 아니라 상호작용 룰이 메시지를 만든다.",
            "plain_ko": "Run 014-016은 포지션, 상대 선발 손, 공격 단절 이벤트, 비자책 실점, 선발 길이, 상대 수준을 결합한 게임 단위 상호작용을 만들고, 시간분할/상대제거/부트스트랩/퍼뮤테이션/음성대조군으로 걸러냈다.",
            "proof_point": "Run 016에서 4개 룰 중 3개는 promote_core, 1개는 support_only로 분리했다.",
            "what_it_does_not_mean": "상관관계를 곧바로 원인이라고 주장하지 않는다. 현재는 후보 feature contract로 쓰는 descriptive mining 결과다.",
        },
        {
            "story_level": "scouting_translation",
            "audience": "scout_or_front_office",
            "headline_ko": "스카우팅 언어로는 'RHP game-script unlocker'와 'traffic-command stabilizer'다.",
            "plain_ko": "외인 타자는 우투수 상대 출루+장타, 2스트라이크 생존, 병살/도루자 리스크 억제가 핵심이고, 외인 투수는 볼넷 변동성, 선발 길이, 실책 뒤 추가실점 억제가 핵심이다.",
            "proof_point": f"최종 메시지: {final_msg['final_layer1_message']}",
            "what_it_does_not_mean": "타자만 보거나 투수만 보는 메시지가 아니다. 한쪽이 막히면 다른 쪽 부담이 폭발하는 구조를 본다.",
        },
        {
            "story_level": "candidate_contract",
            "audience": "modeling_team",
            "headline_ko": "후보 점수화는 장점 나열이 아니라 SSG의 잠긴 경기 상태를 풀 수 있는지로 한다.",
            "plain_ko": "각 후보는 RHP 대응, 이닝 지속, run-kill 회피, 교통정리 커맨드, 선발 길이, extra-out resilience 중 어떤 SSG 문제를 직접 줄이는지로 평가한다.",
            "proof_point": f"투수 계약: {final_msg['foreign_pitcher_contract']} / 타자 계약: {final_msg['foreign_hitter_contract']}",
            "what_it_does_not_mean": "WAR나 OPS 상위권을 그대로 데려오는 일반 랭킹 모델이 아니다.",
        },
    ]
    return pd.DataFrame(rows)


def build_objections(decisions: pd.DataFrame, controls: pd.DataFrame, bootstrap: pd.DataFrame) -> pd.DataFrame:
    r1 = row_by(decisions, "rule_id", "R1_rhp_low_of_conversion_run_trade")
    r2 = row_by(decisions, "rule_id", "R2_rhp_ofdh_run_kill")
    r3 = row_by(decisions, "rule_id", "R3_extra_out_high_of_void")
    r4 = row_by(decisions, "rule_id", "R4_top_opponent_short_start_of_void")
    nc_hr = row_by(controls, "rule_id", "NC1_of_hr_zero")
    nc_rbi = row_by(controls, "rule_id", "NC5_of_rbi_low_only")
    boot_r1 = row_by(bootstrap, "rule_id", "R1_rhp_low_of_conversion_run_trade")
    boot_r2 = row_by(bootstrap, "rule_id", "R2_rhp_ofdh_run_kill")
    boot_r3 = row_by(bootstrap, "rule_id", "R3_extra_out_high_of_void")

    rows = [
        {
            "objection_id": "OBJ1_power_gap",
            "objection_ko": "그냥 외야 장타가 부족하다는 말 아닌가?",
            "answer_ko": "아니다. 외야 홈런 0개 경기만으로는 신호가 약하고, 우투 선발+낮은 외야 전환+상대 득점 폭증 같은 상호작용을 붙일 때만 급격히 나빠진다.",
            "controlling_evidence": f"OF HR zero: win {pct(nc_hr['win_pct'])}, RD {signed(nc_hr['avg_run_diff'])}; R1: {int(r1['games'])}G win {pct(r1['win_pct'])}, RD {signed(r1['avg_run_diff'])}.",
            "residual_risk": "외야 장타 자체가 불필요하다는 뜻은 아니다. 장타보다 먼저 볼 것은 우투수 상대 이닝 지속성과 전환 능력이다.",
            "presentation_line": "우리 메시지는 '파워 부족'이 아니라 '상대 우투수 경기 흐름에서 이닝이 잠기는 문제'다.",
        },
        {
            "objection_id": "OBJ2_only_of_rbi",
            "objection_ko": "외야 타점 낮은 경기만 골라서 본 거 아닌가?",
            "answer_ko": "외야 RBI < 3만 보면 패턴이 충분히 날카롭지 않다. RHP, run-kill, extra-out 변수를 붙여야 메시지가 선명해진다.",
            "controlling_evidence": f"OF RBI < 3 only: win {pct(nc_rbi['win_pct'])}, RD {signed(nc_rbi['avg_run_diff'])}; R2: {int(r2['games'])}G win {pct(r2['win_pct'])}, RD {signed(r2['avg_run_diff'])}.",
            "residual_risk": "타점은 결과지표라 선수 책임과 팀 상황이 섞인다. 그래서 후보 단계에서는 OBP, chase, whiff, GB/GDP, split 안정성을 proxy로 쓴다.",
            "presentation_line": "결과 타점이 아니라, 타점이 사라지는 경기 조건을 찾은 것이다.",
        },
        {
            "objection_id": "OBJ3_pitching_only",
            "objection_ko": "그냥 투수가 많이 맞아서 진 경기 아닌가?",
            "answer_ko": "투수 문제도 포함된다. 다만 핵심은 투수와 타자가 따로 약한 것이 아니라, 실점이 커진 날 외야/DH 전환이 막히면 복구 루트가 사라지는 결합 구조다.",
            "controlling_evidence": f"R3 extra-out high OF void: {int(r3['games'])}G win {pct(r3['win_pct'])}, RD {signed(r3['avg_run_diff'])}, decision {r3['decision']}.",
            "residual_risk": "수비 전체 가치를 직접 측정한 것은 아직 아니다. 비자책/실책 후 실점 proxy를 더 붙이면 강해진다.",
            "presentation_line": "외인투수는 에이스 이름값보다 traffic command와 extra-out resilience가 SSG fit의 언어다.",
        },
        {
            "objection_id": "OBJ4_small_sample",
            "objection_ko": "표본이 작은 룰을 과대해석하는 것 아닌가?",
            "answer_ko": "그래서 6경기짜리 강팀+짧은 선발 룰은 support_only로 내렸다. core는 20/9/8경기 룰이고, 부트스트랩과 퍼뮤테이션에서도 방향이 유지됐다.",
            "controlling_evidence": f"R4 support only: {int(r4['games'])}G; R1 permutation p(win) {boot_r1['perm_p_win_pct_as_low_or_lower']:.3f}, R2 {boot_r2['perm_p_win_pct_as_low_or_lower']:.3f}, R3 {boot_r3['perm_p_win_pct_as_low_or_lower']:.3f}.",
            "residual_risk": "2026-06-11 이후 데이터 refresh 전까지는 near-freeze이지 final-freeze는 아니다.",
            "presentation_line": "작은 표본은 버리고, 반복성과 robustness가 있는 상호작용만 후보 평가에 남겼다.",
        },
        {
            "objection_id": "OBJ5_candidate_use",
            "objection_ko": "그래서 실제 후보 선정에는 어떻게 쓰나?",
            "answer_ko": "각 메시지를 후보 feature로 바꾼다. 타자는 우투수 상대 OBP+damage, 2K 생존, GDP/CS 위험, 투수는 BB 변동성, 5이닝 바닥, 실책 후 추가실점 억제 proxy로 들어간다.",
            "controlling_evidence": "Run 017 candidate feature blueprint table links each feature family to R1/R2/R3 and downstream Layers 2-5.",
            "residual_risk": "후보 이름은 아직 잠금 상태다. 시장성, KBO 번역, 실패 리스크 모델이 붙기 전에는 research lead로만 본다.",
            "presentation_line": "메시지는 발표용 슬로건이 아니라 최종 ranking feature의 설계도다.",
        },
    ]
    return pd.DataFrame(rows)


def build_feature_blueprint() -> pd.DataFrame:
    rows = [
        {
            "slot": "foreign_hitter",
            "message_component": "RHP game-script unlocker",
            "candidate_feature": "vs_rhp_on_base_damage",
            "desired_direction": "high",
            "measurement_proxy": "MLB/MiLB vs RHP OBP, xwOBA, hard-hit/barrel without extreme chase or whiff penalty",
            "source_family": "Savant + MiLB splits + KBO translation",
            "evidence_rule_id": "R1_rhp_low_of_conversion_run_trade",
            "downstream_layer": "L2 archetype + L4 translation + L6 fit",
            "hard_gate_or_weight": "core_weight",
            "reason_ko": "SSG의 문제는 단순 홈런이 아니라 우투 선발 경기에서 외야/DH가 이닝을 다시 여는 능력이다.",
        },
        {
            "slot": "foreign_hitter",
            "message_component": "run-kill avoidance",
            "candidate_feature": "low_gdp_cs_run_kill_risk",
            "desired_direction": "low",
            "measurement_proxy": "GB%, sprint/attempt context, GDP rate where available, two-strike contact, chase%, whiff%",
            "source_family": "Savant batted-ball + MiLB play proxy + scouting notes",
            "evidence_rule_id": "R2_rhp_ofdh_run_kill",
            "downstream_layer": "L5 failure risk + L6 fit",
            "hard_gate_or_weight": "core_weight",
            "reason_ko": "병살/도루자 같은 이닝 단절이 붙는 순간 SSG의 복구 루트가 사라진다.",
        },
        {
            "slot": "foreign_hitter",
            "message_component": "two-strike survival",
            "candidate_feature": "two_strike_contact_floor",
            "desired_direction": "high",
            "measurement_proxy": "two-strike contact where available, K%, zone-contact%, chase-contact%, AAA K-BB trend",
            "source_family": "Savant plate discipline + MiLB trend",
            "evidence_rule_id": "R2_rhp_ofdh_run_kill",
            "downstream_layer": "L4 translation + L5 failure risk",
            "hard_gate_or_weight": "supporting_weight",
            "reason_ko": "SSG가 필요한 외야수는 장타만 있는 타자가 아니라 이닝을 끊지 않는 타자다.",
        },
        {
            "slot": "foreign_hitter",
            "message_component": "role stability",
            "candidate_feature": "corner_of_or_dh_role_continuity",
            "desired_direction": "high",
            "measurement_proxy": "recent OF/DH innings or games, handedness split stability, AAA regular role",
            "source_family": "MLB roster status + MiLB role context + news/manual check",
            "evidence_rule_id": "R1_rhp_low_of_conversion_run_trade",
            "downstream_layer": "L3 market + L6 fit",
            "hard_gate_or_weight": "feasibility_gate",
            "reason_ko": "타자 메시지는 외야/DH 슬롯에서 바로 쓸 수 있어야 의미가 있다.",
        },
        {
            "slot": "foreign_pitcher",
            "message_component": "traffic-command stabilizer",
            "candidate_feature": "low_free_pass_volatility",
            "desired_direction": "low",
            "measurement_proxy": "BB%, BB% year-to-year variance, zone%, first-pitch strike proxy, K-BB%",
            "source_family": "Savant + MiLB role context + KBO translation",
            "evidence_rule_id": "R3_extra_out_high_of_void",
            "downstream_layer": "L4 translation + L5 failure risk + L6 fit",
            "hard_gate_or_weight": "core_weight",
            "reason_ko": "SSG는 수비 실수나 추가 출루가 생긴 뒤 추가실점으로 번지는 경기를 줄여야 한다.",
        },
        {
            "slot": "foreign_pitcher",
            "message_component": "starter length floor",
            "candidate_feature": "five_inning_floor",
            "desired_direction": "high",
            "measurement_proxy": "recent GS, IP/GS, pitch count durability, AAA starter load, times-through-order penalty",
            "source_family": "MLB/MiLB game logs + role context",
            "evidence_rule_id": "R4_top_opponent_short_start_of_void",
            "downstream_layer": "L3 market + L5 risk + L6 fit",
            "hard_gate_or_weight": "supporting_weight",
            "reason_ko": "짧은 선발은 support-only 메시지지만, 강팀전에서 약점이 커지는 구조라 후보 리스크 가중치로 남긴다.",
        },
        {
            "slot": "foreign_pitcher",
            "message_component": "extra-out resilience",
            "candidate_feature": "damage_control_after_traffic",
            "desired_direction": "high",
            "measurement_proxy": "LOB%, HR/BB suppression with runners, GB% with traffic, hard-hit allowed with men on where available",
            "source_family": "Savant split proxy + game logs + scouting notes",
            "evidence_rule_id": "R3_extra_out_high_of_void",
            "downstream_layer": "L5 failure risk + L6 fit",
            "hard_gate_or_weight": "core_weight",
            "reason_ko": "비자책/실책성 상황 이후 한 이닝이 무너지는 흐름을 끊는 투수가 필요하다.",
        },
        {
            "slot": "foreign_pitcher",
            "message_component": "ABS adaptation",
            "candidate_feature": "zone_command_not_called_strike_dependency",
            "desired_direction": "high",
            "measurement_proxy": "zone%, chase%, edge-location tendency, BB% stability, pitch-shape command review",
            "source_family": "Savant pitch-level + KBO ABS literature/context",
            "evidence_rule_id": "R3_extra_out_high_of_void",
            "downstream_layer": "L4 translation + L5 failure risk",
            "hard_gate_or_weight": "supporting_weight",
            "reason_ko": "KBO ABS 환경에서는 커맨드 불안이 볼넷과 긴 이닝으로 바로 번질 수 있다.",
        },
        {
            "slot": "asian_quota",
            "message_component": "shock absorber",
            "candidate_feature": "multi_inning_or_spot_start_flex",
            "desired_direction": "high",
            "measurement_proxy": "multi-inning appearances, spot starts, IP/game, quick recovery usage",
            "source_family": "NPB/CPBL/ABL roster + game logs + manual availability",
            "evidence_rule_id": "R4_top_opponent_short_start_of_void",
            "downstream_layer": "L3 market + L5 risk + L6 fit",
            "hard_gate_or_weight": "role_gate",
            "reason_ko": "아쿼는 정규 외인 에이스 대체가 아니라 짧은 선발/불펜 과부하 충격을 흡수하는 옵션으로 해석한다.",
        },
        {
            "slot": "asian_quota",
            "message_component": "contract-realistic optionality",
            "candidate_feature": "market_access_and_role_acceptance",
            "desired_direction": "high",
            "measurement_proxy": "nationality eligibility, current league status, contract feasibility, role acceptance evidence",
            "source_family": "official rosters + transactions + news/manual check",
            "evidence_rule_id": "Layer1_supporting_need",
            "downstream_layer": "L3 market + L5 risk",
            "hard_gate_or_weight": "hard_gate",
            "reason_ko": "아쿼는 시장성이 핵심이다. SSG fit이 좋아도 실제 영입 가능성이 없으면 제외한다.",
        },
    ]
    return pd.DataFrame(rows)


def build_evidence_trace(
    decisions: pd.DataFrame,
    controls: pd.DataFrame,
    bootstrap: pd.DataFrame,
    news_hit: pd.DataFrame,
    news_pitch: pd.DataFrame,
    cards: pd.DataFrame,
) -> pd.DataFrame:
    r1 = row_by(decisions, "rule_id", "R1_rhp_low_of_conversion_run_trade")
    r2 = row_by(decisions, "rule_id", "R2_rhp_ofdh_run_kill")
    r3 = row_by(decisions, "rule_id", "R3_extra_out_high_of_void")
    r4 = row_by(decisions, "rule_id", "R4_top_opponent_short_start_of_void")
    nc_hr = row_by(controls, "rule_id", "NC1_of_hr_zero")
    nc_rbi = row_by(controls, "rule_id", "NC5_of_rbi_low_only")
    b1 = row_by(bootstrap, "rule_id", "R1_rhp_low_of_conversion_run_trade")
    b2 = row_by(bootstrap, "rule_id", "R2_rhp_ofdh_run_kill")
    b3 = row_by(bootstrap, "rule_id", "R3_extra_out_high_of_void")

    def tag_count(df: pd.DataFrame, tag: str, count_col: str) -> str:
        hit = df[df["tag"].eq(tag)]
        if hit.empty:
            return "not_available"
        return str(int(hit.iloc[0][count_col]))

    rows = [
        {
            "message_component": "not_generic_power_gap",
            "evidence_type": "negative_control",
            "source_output": "outputs/tables/ssg_hidden_weakness_negative_controls_v3.csv",
            "evidence_summary": f"OF HR zero control win {pct(nc_hr['win_pct'])}, RD {signed(nc_hr['avg_run_diff'])}; OF RBI < 3 control win {pct(nc_rbi['win_pct'])}, RD {signed(nc_rbi['avg_run_diff'])}.",
            "decision_use": "Use to reject the easy 'just add power' narrative.",
            "confidence": "high_for_descriptive_control",
        },
        {
            "message_component": "rhp_game_script_lock",
            "evidence_type": "promoted_core_rule",
            "source_output": "outputs/tables/ssg_hidden_weakness_robustness_decisions_v3.csv",
            "evidence_summary": f"R1 {int(r1['games'])}G, win {pct(r1['win_pct'])}, RD {signed(r1['avg_run_diff'])}, permutation p(win) {b1['perm_p_win_pct_as_low_or_lower']:.3f}.",
            "decision_use": "Foreign hitter must be evaluated on RHP-resistant OBP plus damage, not only raw HR.",
            "confidence": "high_with_refresh_needed",
        },
        {
            "message_component": "run_kill_avoidance",
            "evidence_type": "promoted_core_rule",
            "source_output": "outputs/tables/ssg_hidden_weakness_robustness_decisions_v3.csv",
            "evidence_summary": f"R2 {int(r2['games'])}G, win {pct(r2['win_pct'])}, RD {signed(r2['avg_run_diff'])}, permutation p(win) {b2['perm_p_win_pct_as_low_or_lower']:.3f}.",
            "decision_use": "Penalize hitter candidates with high chase/whiff/GDP-style run-kill profiles.",
            "confidence": "medium_high_sample_limited",
        },
        {
            "message_component": "extra_out_resilience",
            "evidence_type": "promoted_core_rule",
            "source_output": "outputs/tables/ssg_hidden_weakness_robustness_decisions_v3.csv",
            "evidence_summary": f"R3 {int(r3['games'])}G, win {pct(r3['win_pct'])}, RD {signed(r3['avg_run_diff'])}, permutation p(win) {b3['perm_p_win_pct_as_low_or_lower']:.3f}.",
            "decision_use": "Foreign pitcher scoring needs traffic command and error-aftershock damage control.",
            "confidence": "medium_high_proxy_needed",
        },
        {
            "message_component": "starter_length_support",
            "evidence_type": "support_rule",
            "source_output": "outputs/tables/ssg_hidden_weakness_robustness_decisions_v3.csv",
            "evidence_summary": f"R4 {int(r4['games'])}G, win {pct(r4['win_pct'])}, RD {signed(r4['avg_run_diff'])}, decision {r4['decision']}.",
            "decision_use": "Keep starter length as a risk/support feature, not the central thesis.",
            "confidence": "support_only",
        },
        {
            "message_component": "external_text_corroboration_hitter",
            "evidence_type": "news_metadata_context",
            "source_output": "outputs/tables/ssg_news_need_tag_summary.csv",
            "evidence_summary": f"News tags include outfield={tag_count(news_hit, 'outfield', 'article_count')}, run_creation={tag_count(news_hit, 'run_creation', 'article_count')}, onbase_discipline={tag_count(news_hit, 'onbase_discipline', 'article_count')}, foreign_hitter={tag_count(news_hit, 'foreign_hitter', 'article_count')}.",
            "decision_use": "Use articles as context, not proof; quant tables control the message.",
            "confidence": "corroboration_only",
        },
        {
            "message_component": "external_text_corroboration_pitcher",
            "evidence_type": "news_metadata_context",
            "source_output": "outputs/tables/ssg_pitching_news_tag_summary.csv",
            "evidence_summary": f"Pitching news tags include starter_rotation={tag_count(news_pitch, 'starter_rotation', 'articles')}, run_prevention={tag_count(news_pitch, 'run_prevention', 'articles')}, bullpen_load={tag_count(news_pitch, 'bullpen_load', 'articles')}, foreign_pitcher={tag_count(news_pitch, 'foreign_pitcher', 'articles')}.",
            "decision_use": "Use articles to frame why pitcher stability is a live organizational need.",
            "confidence": "corroboration_only",
        },
        {
            "message_component": "older_split_support",
            "evidence_type": "prior_evidence_card",
            "source_output": "outputs/tables/message_mining_evidence_cards_v1.csv",
            "evidence_summary": maybe_card(cards, "hit_001_runway_gap"),
            "decision_use": "Keep as supporting background; Run 014-016 game interaction evidence is stronger.",
            "confidence": "supporting",
        },
        {
            "message_component": "role_location_support",
            "evidence_type": "prior_evidence_card",
            "source_output": "outputs/tables/message_mining_evidence_cards_v1.csv",
            "evidence_summary": maybe_card(cards, "hit_002_role_location"),
            "decision_use": "Supports why OF/DH role matters, but not enough alone for final message.",
            "confidence": "supporting",
        },
    ]
    return pd.DataFrame(rows)


def build_freeze_checklist() -> pd.DataFrame:
    rows = [
        {
            "check_id": "F1_refresh_current_statiz",
            "check_name": "Refresh post-2026-06-11 STATIZ/current-game data",
            "status": "pending",
            "why_it_matters": "The current Layer 1 snapshot ends at 2026-06-11, so final freeze needs the newest games.",
            "pass_condition": "Core R1/R2/R3 directions remain materially worse than negative controls after refresh.",
        },
        {
            "check_id": "F2_play_by_play_state",
            "check_name": "Attach inning/score/base-out game-state proxies",
            "status": "pending",
            "why_it_matters": "The message is about game-script lock, so finer game state would reduce interpretation risk.",
            "pass_condition": "RHP/run-kill/extra-out signals remain visible when score and base-out state are controlled or stratified.",
        },
        {
            "check_id": "F3_defense_proxy",
            "check_name": "Strengthen defense and extra-out measurement",
            "status": "partial",
            "why_it_matters": "Unearned runs are useful but too coarse to represent all defensive friction.",
            "pass_condition": "Errors, failed plays, or defense-independent proxy confirms that extra-out damage is not a scorer artifact.",
        },
        {
            "check_id": "F4_baserunning_proxy",
            "check_name": "Strengthen baserunning/run-kill measurement",
            "status": "partial",
            "why_it_matters": "GDP/CS events are attached, but full baserunning value is still missing.",
            "pass_condition": "Candidate-side run-kill proxy includes GDP tendency, speed/attempt context, and two-strike contact floor.",
        },
        {
            "check_id": "F5_opponent_quality_sensitivity",
            "check_name": "Keep opponent-quality rule support-only unless sample grows",
            "status": "ready",
            "why_it_matters": "Top-opponent short-start rule is sharp but only six games.",
            "pass_condition": "Use it as a risk modifier unless refreshed sample reaches the core threshold with robustness support.",
        },
        {
            "check_id": "F6_candidate_feature_join",
            "check_name": "Join Layer 1 feature contract into Layers 2-5",
            "status": "pending",
            "why_it_matters": "A message is only useful if candidate scoring can observe it with available player features.",
            "pass_condition": "Every L1 candidate feature has a usable proxy in market, translation, or risk tables.",
        },
        {
            "check_id": "F7_manual_baseball_review",
            "check_name": "Manual baseball review of promoted rules",
            "status": "pending",
            "why_it_matters": "Descriptive mining can find real patterns that still need baseball interpretation before presentation.",
            "pass_condition": "A human review marks each promoted rule as baseball-plausible and not merely a schedule artifact.",
        },
        {
            "check_id": "F8_news_refresh",
            "check_name": "Refresh text/news corroboration",
            "status": "optional",
            "why_it_matters": "News should shape wording and context, but not control the quantitative message.",
            "pass_condition": "No newer injury/foreign-player/role news materially changes the recruitment constraint.",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    final_message = read_table("ssg_hidden_weakness_final_message_v3.csv").iloc[0]
    decisions = read_table("ssg_hidden_weakness_robustness_decisions_v3.csv")
    controls = read_table("ssg_hidden_weakness_negative_controls_v3.csv")
    bootstrap = read_table("ssg_hidden_weakness_bootstrap_permutation_v3.csv")
    news_hit = read_table("ssg_news_need_tag_summary.csv")
    news_pitch = read_table("ssg_pitching_news_tag_summary.csv")
    cards = read_table("message_mining_evidence_cards_v1.csv")

    outputs = {
        "ssg_layer1_plain_language_story_v4.csv": build_plain_story(final_message, decisions, controls),
        "ssg_layer1_objection_response_v4.csv": build_objections(decisions, controls, bootstrap),
        "ssg_layer1_candidate_feature_blueprint_v4.csv": build_feature_blueprint(),
        "ssg_layer1_evidence_to_message_trace_v4.csv": build_evidence_trace(
            decisions, controls, bootstrap, news_hit, news_pitch, cards
        ),
        "ssg_layer1_freeze_checklist_v4.csv": build_freeze_checklist(),
    }

    for name, df in outputs.items():
        df.to_csv(OUT_DIR / name, index=False)
        print(f"wrote {OUT_DIR / name} rows={len(df)}")


if __name__ == "__main__":
    main()
