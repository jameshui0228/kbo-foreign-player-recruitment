# SSG Recruitment Decision Support

**A collaborative SDA project connecting multi-source data, model validation, and practical recruitment constraints.**

Completed in June 2026. Recommendations and market information are historical, not current recruitment advice.

[Case study & my contribution](https://github.com/jameshui0228/data-analysis-portfolio/blob/main/projects/kbo-foreign-player-recruitment.md) · [Report (Korean)](reports/ssg_overleaf_report_final.pdf) · [Presentation (Korean)](reports/presentation/SSG_final_presentation_2026-06-24.pdf) · [한국어](README.ko.md)

## At a Glance

| Area | Outcome |
|---|---|
| Candidate universe | 736 hitters and 1,009 pitchers; distinct from the model training sample |
| Decision output | Three contact priorities per role, with separate availability, contract, and risk checks |
| Deliverables | 23-page report, presentation, code, result CSVs, source and validation records |
| Key validation finding | Hitter success AUC: 1.000 in-sample versus 0.650 under player-held-out validation |
| Interpretation | Model outputs support candidate comparison; they are not absolute success probabilities |

![Training fit versus player-held-out validation](docs/portfolio/validation.svg)

**Suggested reading:** [Case study](https://github.com/jameshui0228/data-analysis-portfolio/blob/main/projects/kbo-foreign-player-recruitment.md) > [results](docs/portfolio/results.md) > [validation notes (Korean)](docs/final_report_last_validation_v1.md) > [offline demo](docs/portfolio/README.md).

## Run the Public Demo

No API keys, raw data, or third-party packages are required. The script validates stored result tables; it does not retrain models or recompute AUC from predictions.

```bash
git clone https://github.com/jameshui0228/kbo-foreign-player-recruitment.git
cd kbo-foreign-player-recruitment
python3 scripts/portfolio_demo.py
```

## Analytical Question

Which foreign hitter and starting pitcher could address SSG's roster needs while remaining realistic targets?

The analysis combined KBO/STATIZ, MLB/MiLB, NPB/CPBL, roster and transaction records, and public contract, salary, and medical-risk signals from 2023 onward. It considered:

- Team needs rather than aggregate performance alone.
- How performance might translate between leagues and into the KBO environment.
- Whether roster status and contract conditions made an approach feasible.
- Whether a candidate's weaknesses could be managed within the team's context.

The final model used structured numerical data and roster, transaction, contract, and medical-risk signals. Article and interview text was not used directly as model features; news sources supported contextual checks.

## Final Contact Priorities

| Role | First | Second | Third |
|---|---|---|---|
| Hitter | Will Brennan | Dominic Fletcher | Dylan Carlson |
| Starting pitcher | Josh Fleming | Keegan Thompson | Kolby Allard |

These are project recommendations as of June 2026, not evidence of adoption or recruitment by SSG.

[Final handover (Korean)](docs/final_project_handoff_2026_06_25.md) · [Candidate table](outputs/tables/final_candidate_board_execution_v4.csv) · [English result summary](docs/portfolio/results.md)

## Methods & Evidence

Original technical documents are primarily in Korean.

| Topic | Record |
|---|---|
| Integrated recommendation model | [Structured-data model](docs/unified_recommendation_model_structured_only_v2.md) |
| Availability and execution constraints | [Feasibility assessment](docs/realism_first_candidate_board_v3.md), [final candidate review](docs/candidate_board_execution_v4.md) |
| Cross-league performance translation | [Translation coefficients](docs/evidence_based_kbo_translation_coefficients_v2.md) |
| Model reliability | [Calibration audit](docs/model_probability_calibration_audit_v1.md), [final validation](docs/final_report_last_validation_v1.md) |
| Sources and assumptions | [Source log](docs/source_log.md), [data dictionary](docs/data_dictionary.md), [assumptions](docs/assumptions.md) |
| Experiment history | [Experiment log](docs/experiment_log.md), [six-stage progress](docs/six_layer_progress_board.md) |
| Final report source | [LaTeX source](reports/overleaf_ssg_recruitment/main.tex) |
| Presentation assets | [Graphs](outputs/ppt_graphs/), [tables](outputs/ppt_tables_png/), [presentation files](reports/presentation/) |

Earlier candidate reviews are retained as historical records. The [final handover](docs/final_project_handoff_2026_06_25.md) is the reference for the completed recommendation.

## Collaborator Setup

```bash
git clone https://github.com/jameshui0228/kbo-foreign-player-recruitment.git
cd kbo-foreign-player-recruitment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Keep personal STATIZ and Naver credentials in the local `.env` only. Do not commit credentials or source data. Full analysis may require separately obtained data and access permissions.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and [COLLABORATION.md](COLLABORATION.md) before changing the project.

## Repository Map

| Location | Contents |
|---|---|
| `src/`, `scripts/`, `notebooks/` | Analysis code, utility scripts, explanatory notebooks |
| `outputs/` | Tracked result tables, charts, and presentation assets |
| `reports/` | Final report, presentation, and report source |
| `docs/` | Methods, source records, assumptions, validation, handover |
| `data/` | Data organization and schemas; raw and processed datasets are not committed |

The [original Korean guide](README.ko.md) preserves the detailed artifact inventory and historical directory map.

## Reproducibility & Data Boundaries

- Raw, intermediate, and processed source data stay out of Git.
- Record source, access date, collection method, and usage constraints in the [source log](docs/source_log.md).
- Post-entry KBO performance is used as an outcome label in historical transfer evaluation, not as a pre-entry ranking feature.
- Keep skill, team fit, performance translation, availability, and risk distinct in recommendations.
- Do not interpret in-sample fit, stored-output verification, or contact priority as evidence of real-world success.
