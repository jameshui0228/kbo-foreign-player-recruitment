from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "tables"
DOCS = ROOT / "docs"


SALARY_ROWS = [
    {
        "player_name": "Luis Matos",
        "fit_slot": "foreign_hitter",
        "salary_year": 2026,
        "public_salary_usd": 780000,
        "public_salary_type": "2026 MLB salary ranking / pre-arb estimate",
        "aav_usd": None,
        "guaranteed_contract_usd": None,
        "minor_salary_usd": None,
        "prior_or_career_salary_reference_usd": None,
        "salary_data_status": "public_2026_salary_estimate_available",
        "structured_source_name": "Spotrac 2026 MLB Payroll Rankings",
        "structured_source_url": "https://www.spotrac.com/mlb/rankings/player/_/year/2026",
        "model_use_status": "usable_as_numeric_cost_feature_medium_confidence",
        "notes": "Public ranking page lists Luis Matos, MIL, OF, at $780,000 for 2026.",
    },
    {
        "player_name": "Will Brennan",
        "fit_slot": "foreign_hitter",
        "salary_year": 2026,
        "public_salary_usd": 900000,
        "public_salary_type": "2026 signed free-agent contract value / MLB salary",
        "aav_usd": 900000,
        "guaranteed_contract_usd": None,
        "minor_salary_usd": 400000,
        "prior_or_career_salary_reference_usd": None,
        "salary_data_status": "public_2026_contract_available",
        "structured_source_name": "Spotrac 2026 Signed Free Agents",
        "structured_source_url": "https://www.spotrac.com/mlb/free-agents/signed/_/year/2026",
        "model_use_status": "usable_as_numeric_cost_feature_high_confidence",
        "notes": "Spotrac signed-free-agent table lists Will Brennan at 1 yr / $900,000. Separate public reporting says $400,000 minors guarantee; stored only as secondary structured field.",
    },
    {
        "player_name": "Dominic Fletcher",
        "fit_slot": "foreign_hitter",
        "salary_year": 2026,
        "public_salary_usd": None,
        "public_salary_type": "current 2026 salary undisclosed",
        "aav_usd": None,
        "guaranteed_contract_usd": None,
        "minor_salary_usd": None,
        "prior_or_career_salary_reference_usd": 760000,
        "salary_data_status": "current_salary_undisclosed_prior_reference_only",
        "structured_source_name": "Spotrac player contract page / prior salary reference",
        "structured_source_url": "https://www.spotrac.com/mlb/player/_/id/30473/dominic-fletcher",
        "model_use_status": "do_not_use_as_exact_2026_cost_use_as_manual_gap",
        "notes": "Current 2026 contract amount was not found as a public structured salary. Prior/average salary reference appears around $760,000, but this is not treated as exact current cost.",
    },
    {
        "player_name": "Josh Fleming",
        "fit_slot": "foreign_pitcher",
        "salary_year": 2026,
        "public_salary_usd": None,
        "public_salary_type": "minor-league deal terms undisclosed",
        "aav_usd": None,
        "guaranteed_contract_usd": None,
        "minor_salary_usd": None,
        "prior_or_career_salary_reference_usd": None,
        "payroll_allocation_reference_usd": 4545,
        "salary_data_status": "minor_contract_terms_undisclosed_payroll_allocation_only",
        "structured_source_name": "Spotrac Toronto Blue Jays 2026 payroll/tax table",
        "structured_source_url": "https://www.spotrac.com/mlb/toronto-blue-jays/payroll/_/year/2026",
        "model_use_status": "do_not_use_as_exact_annual_salary_use_as_manual_gap",
        "notes": "Spotrac payroll pages show a small current allocation, but minor-league contract annual terms are not public. Do not treat $4,545 as full annual salary.",
    },
    {
        "player_name": "Bruce Zimmermann",
        "fit_slot": "foreign_pitcher",
        "salary_year": 2026,
        "public_salary_usd": None,
        "public_salary_type": "minor-league/free-agent deal terms undisclosed",
        "aav_usd": None,
        "guaranteed_contract_usd": None,
        "minor_salary_usd": None,
        "prior_or_career_salary_reference_usd": 969380,
        "salary_data_status": "current_salary_undisclosed_prior_career_reference_only",
        "structured_source_name": "Spotrac player contract page / free-agent table",
        "structured_source_url": "https://www.spotrac.com/mlb/player/_/id/23353/bruce-zimmermann",
        "model_use_status": "do_not_use_as_exact_2026_cost_use_as_manual_gap",
        "notes": "Spotrac player page exposes career earnings, while current minor/free-agent terms are not usable as exact 2026 salary.",
    },
    {
        "player_name": "Yariel Rodríguez",
        "fit_slot": "foreign_pitcher",
        "salary_year": 2026,
        "public_salary_usd": 6400000,
        "public_salary_type": "AAV / luxury-tax salary from multiyear MLB contract",
        "aav_usd": 6400000,
        "guaranteed_contract_usd": 32000000,
        "minor_salary_usd": None,
        "prior_or_career_salary_reference_usd": None,
        "salary_data_status": "public_multiyear_contract_available",
        "structured_source_name": "Spotrac player page and Toronto Blue Jays payroll/tax table",
        "structured_source_url": "https://www.spotrac.com/mlb/player/_/id/87490/yariel-rodriguez",
        "model_use_status": "usable_as_numeric_cost_feature_high_confidence_but_contract_blocker",
        "notes": "Spotrac lists 5 yr / $32,000,000 and $6,400,000 AAV/luxury-tax salary. This is a major cost/access blocker relative to KBO replacement economics.",
    },
]


def markdown_table(df: pd.DataFrame) -> str:
    display = df.fillna("").astype(str)
    headers = list(display.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in display.iterrows():
        values = [str(row[col]).replace("\n", " ").replace("|", "/") for col in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)

    salary = pd.DataFrame(SALARY_ROWS)
    top3_path = OUT / "unified_foreign_recommendations_top3_structured_only_v2.csv"
    if top3_path.exists():
        top3 = pd.read_csv(top3_path)
        salary = top3[["slot_label", "recommendation_rank", "player_name"]].merge(
            salary,
            on="player_name",
            how="left",
        )

    salary.to_csv(OUT / "recommended_candidate_salary_audit_v1.csv", index=False)

    numeric_usable = salary["model_use_status"].fillna("").str.contains("usable_as_numeric").sum()
    exact_missing = len(salary) - numeric_usable
    doc = [
        "# Recommended Candidate Salary Audit v1",
        "",
        "Generated: 2026-06-22 KST",
        "",
        "## Summary",
        "",
        f"- Recommended candidates audited: {len(salary)}",
        f"- Public numeric salary/cost usable in model: {numeric_usable}",
        f"- Current exact salary still missing/undisclosed: {exact_missing}",
        "",
        "This table intentionally separates exact public salary data from minor-league or undisclosed contract situations. Unknown salary is not imputed as a fake value.",
        "",
        "## Audit Table",
        "",
        markdown_table(
            salary[
                [
                    "slot_label",
                    "recommendation_rank",
                    "player_name",
                    "public_salary_usd",
                    "public_salary_type",
                    "aav_usd",
                    "guaranteed_contract_usd",
                    "minor_salary_usd",
                    "salary_data_status",
                    "model_use_status",
                    "structured_source_name",
                ]
            ]
        ),
        "",
        "## Modeling Decision",
        "",
        "Salary should enter the final ranking only where a current public numeric value is available. For undisclosed minor-league contracts, the model should keep a manual cost gap instead of guessing.",
        "",
    ]
    (DOCS / "recommended_candidate_salary_audit_v1.md").write_text("\n".join(doc), encoding="utf-8")

    print("wrote outputs/tables/recommended_candidate_salary_audit_v1.csv")
    print("wrote docs/recommended_candidate_salary_audit_v1.md")
    print(salary[["slot_label", "recommendation_rank", "player_name", "public_salary_usd", "salary_data_status", "model_use_status"]].to_string(index=False))


if __name__ == "__main__":
    main()
