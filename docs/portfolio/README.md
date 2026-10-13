# Offline Result Verification

[Repository](../../README.md) · [한국어](README.ko.md)

Read the repository's **final candidate CSV and validation CSV** without raw data or credentials. The demo uses Python 3.10 or later and only the standard library. It makes no network requests.

## Run

From the repository root:

```bash
python3 scripts/portfolio_demo.py
python3 scripts/portfolio_demo.py --check
python3 -m unittest discover -s tests -v
```

The first command prints three contact priorities for each role and the audit table. The second checks that the generated document and chart match the tracked CSVs. The third runs the public demo's tests.

[Result summary](results.md) · [Validation chart](validation.svg)

## What Is Verified

- Required columns, unique candidate ranks, and valid AUC ranges.
- Clear separation of stored training-fit and player-held-out evaluation results.
- Reproducible Markdown and SVG output from the public tables via `--write`.

**The demo does not collect source data, retrain models, or recompute AUC from predictions.** See the [final validation notes (Korean)](../final_report_last_validation_v1.md) for the original analysis.

Candidate and market information reflects June 2026. A successful demo run does not verify current availability or future predictive performance.
