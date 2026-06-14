from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import certifi
import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
BASE_URL = "https://statsapi.mlb.com/api/v1"
ROSTER_TYPES = ("40Man", "active", "fullRoster")


def get_json(session: requests.Session, url: str) -> dict:
    response = session.get(url, timeout=30, verify=certifi.where())
    response.raise_for_status()
    return response.json()


def chunked(values: list[int], size: int) -> list[list[int]]:
    return [values[i : i + size] for i in range(0, len(values), size)]


def collect_rosters(eval_date: str) -> tuple[pd.DataFrame, dict]:
    session = requests.Session()
    teams_url = f"{BASE_URL}/teams?sportId=1"
    teams_payload = get_json(session, teams_url)
    teams = teams_payload.get("teams", [])

    records: dict[tuple[int, int], dict] = {}
    raw_rosters: dict[str, object] = {"teams": teams_payload, "rosters": {}}

    for team in teams:
        team_id = team["id"]
        team_name = team["name"]
        raw_rosters["rosters"][str(team_id)] = {}
        for roster_type in ROSTER_TYPES:
            url = f"{BASE_URL}/teams/{team_id}/roster/{roster_type}"
            payload = get_json(session, url)
            raw_rosters["rosters"][str(team_id)][roster_type] = payload
            for entry in payload.get("roster", []):
                person = entry.get("person", {})
                person_id = person.get("id")
                if person_id is None:
                    continue
                key = (team_id, person_id)
                record = records.setdefault(
                    key,
                    {
                        "evaluation_date": eval_date,
                        "team_id": team_id,
                        "team_name": team_name,
                        "team_abbreviation": team.get("abbreviation"),
                        "player_id": person_id,
                        "player_name": person.get("fullName"),
                        "primary_position": None,
                        "primary_position_type": None,
                        "primary_position_abbrev": None,
                        "status_code": None,
                        "status_description": None,
                        "roster_note": None,
                        "is_40man": False,
                        "is_active": False,
                        "is_full_roster": False,
                    },
                )
                position = entry.get("position", {})
                status = entry.get("status", {})
                record["primary_position"] = record["primary_position"] or position.get("name")
                record["primary_position_type"] = record["primary_position_type"] or position.get("type")
                record["primary_position_abbrev"] = record["primary_position_abbrev"] or position.get("abbreviation")
                record["status_code"] = record["status_code"] or status.get("code")
                record["status_description"] = record["status_description"] or status.get("description")
                record["roster_note"] = record["roster_note"] or entry.get("note")
                if roster_type == "40Man":
                    record["is_40man"] = True
                elif roster_type == "active":
                    record["is_active"] = True
                elif roster_type == "fullRoster":
                    record["is_full_roster"] = True

    player_ids = sorted({person_id for _, person_id in records})
    people: dict[int, dict] = {}
    for ids in chunked(player_ids, 100):
        url = f"{BASE_URL}/people?personIds={','.join(map(str, ids))}"
        payload = get_json(session, url)
        for person in payload.get("people", []):
            people[person["id"]] = person
    raw_rosters["people"] = people

    today = datetime.strptime(eval_date, "%Y-%m-%d").date()
    for (_, person_id), record in records.items():
        person = people.get(person_id, {})
        birth_date = person.get("birthDate")
        age = None
        if birth_date:
            born = datetime.strptime(birth_date, "%Y-%m-%d").date()
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        record.update(
            {
                "birth_date": birth_date,
                "age": age,
                "bat_side": (person.get("batSide") or {}).get("description"),
                "pitch_hand": (person.get("pitchHand") or {}).get("description"),
                "mlb_debut_date": person.get("mlbDebutDate"),
                "birth_country": person.get("birthCountry"),
                "height": person.get("height"),
                "weight": person.get("weight"),
            }
        )

    df = pd.DataFrame(records.values()).sort_values(["team_name", "player_name"])
    return df, raw_rosters


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--date",
        default=datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat(),
        help="Evaluation date in YYYY-MM-DD.",
    )
    args = parser.parse_args()

    df, raw = collect_rosters(args.date)
    raw_dir = ROOT / "data/raw/mlb/roster_status"
    out_dir = ROOT / "outputs/tables"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    compact_date = args.date.replace("-", "")
    raw_path = raw_dir / f"mlb_roster_status_raw_{compact_date}.json"
    table_path = out_dir / f"mlb_roster_status_{compact_date}.csv"
    latest_path = out_dir / "mlb_roster_status_latest.csv"

    raw_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    df.to_csv(table_path, index=False)
    df.to_csv(latest_path, index=False)

    print(f"wrote {table_path} ({len(df)} rows)")
    print(f"wrote {raw_path}")


if __name__ == "__main__":
    main()
