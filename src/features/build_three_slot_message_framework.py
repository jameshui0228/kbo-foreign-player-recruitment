#!/usr/bin/env python3
"""Build the three-slot recruitment message framework."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs/tables"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "slot": "foreign_hitter",
            "message_name": "The Runway Converter",
            "korean_tagline": "득점권 해결사가 아니라, 득점권을 만들어주는 타자",
            "core_claim": "SSG needs a hitter who converts runner-on-first traffic into scoring-position pressure.",
            "role": "OF/DH bridge bat",
            "ssg_problem": "RISP performance is elite, but runner-on-first offense is last-tier and concentrated in OF/DH usage.",
            "evidence_snapshot": "RISP OPS .831 rank 1; runner-on-first OPS .649 rank 10; high-leverage OF on-first OPS .383 with 0 RBI.",
            "screening_metrics": "on_1b OPS/OBP/xwOBA, GDP risk, RHP production, two-strike survival, gap/line-drive contact, chase/whiff discipline",
            "avoid": "generic slugger, RBI-only profile, 1B-only bat unless exceptional, hitter whose value appears only after RISP is already created",
        },
        {
            "slot": "foreign_pitcher",
            "message_name": "The ABS-Native Load-Bearing Starter",
            "korean_tagline": "강한 공보다, ABS가 스트라이크로 인정하는 공을 6이닝 반복하는 투수",
            "core_claim": "SSG needs a six-inning stabilizer whose command survives the stricter KBO ABS rule-book zone.",
            "role": "regular foreign starter",
            "ssg_problem": "Short starts compress games early, force the league's heaviest bullpen workload, and the import slot has amplified the problem.",
            "evidence_snapshot": "SSG starter ERA/WHIP/OPS/IPG rank 10; short starts 26/61; import-slot starters ERA 6.17 and OPSA .821.",
            "screening_metrics": "starter workload, zone rate, first-pitch non-ball rate, three-ball pitch rate, BB+HBP%, HR%, early-inning/RISP wOBA, hard-hit/barrel suppression",
            "avoid": "velocity-only starter, reputation command, reliever stretch-out without workload proof, edge nibbler dependent on human zone/framing",
        },
        {
            "slot": "asian_quota",
            "message_name": "The Option Layer",
            "korean_tagline": "아쿼는 1선발 복권이 아니라, 시즌 중 붕괴를 막는 옵션 보험",
            "core_claim": "The Asian quota should buy low-cost optionality and shock absorption, not pretend to solve the ace problem.",
            "role": "command swingman / long bridge",
            "ssg_problem": "SSG's rotation volatility turns depth pieces into emergency pillars; the quota should prevent the next overload rather than duplicate the foreign starter job.",
            "evidence_snapshot": "Asian quota is structurally a lower-cost fourth foreign lane; short starts force 5.36 bullpen IP; external option-trap message ranked 2nd.",
            "screening_metrics": "3-5 inning absorption, low BB+HBP%, low HR%, role flexibility, recent Asia/Australia workload, visa/availability, transition risk",
            "avoid": "fake ace, starter-only inflexibility, name value, hitter who duplicates the foreign hitter profile, cheapness as the only reason",
        },
    ]
    out = pd.DataFrame(rows)
    out.to_csv(OUTPUT_DIR / "three_slot_message_framework_v1.csv", index=False)
    print("wrote", OUTPUT_DIR / "three_slot_message_framework_v1.csv")
    print(out[["slot", "message_name", "korean_tagline"]].to_string(index=False))


if __name__ == "__main__":
    main()
