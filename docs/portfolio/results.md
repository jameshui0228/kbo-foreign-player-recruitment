# Public Result Summary

[Demo guide](README.md) | [한국어](results.ko.md)

Snapshot: final June 2026 artifacts. This is not a current recommendation or a new model-training result.

## Final Contact Priorities

| Role | Rank | Candidate |
|---|---:|---|
| Hitter | 1 | Will Brennan |
| Hitter | 2 | Dominic Fletcher |
| Hitter | 3 | Dylan Carlson |
| Pitcher | 1 | Josh Fleming |
| Pitcher | 2 | Keegan Thompson |
| Pitcher | 3 | Kolby Allard |

## Training Fit vs. Player-Held-Out Validation

| Target | Training Rows | Unique Players | Training AUC | Player-Held-Out AUC |
|---|---:|---:|---:|---:|
| success | 22 | 17 | 1.000 | 0.650 |
| failure | 22 | 17 | 0.991 | 0.500 |

Training fit is not generalization. Model outputs support candidate comparison; they are not absolute success probabilities.

![AUC by evaluation setting](validation.svg)

## Source Tables & Methods

- [Final candidate table](../../outputs/tables/final_candidate_board_execution_v4.csv)
- [Validation audit table](../../outputs/tables/model_probability_calibration_audit_v1.csv)
- [Final validation interpretation (Korean)](../final_report_last_validation_v1.md)
- [Demo instructions](README.md)

This document and chart are generated from public CSVs with `python3 scripts/portfolio_demo.py --write`.
