# Run 028 Naver News Ready State v0.1

Date: 2026-06-21 KST

Layer focus:

- 3. Candidate market construction
- 5. Failure risk model
- 6. SSG fit ranking preparation

Candidate policy: locked. This run does not create a final ranking, shortlist, recommendation label, candidate-name release, or score release.

## Purpose

Run 027 showed that Google Korean-locale RSS is not a reliable substitute for Naver/local Korean news. Run 028 prepares the collector so Naver credentials can be used without putting secrets in commands, source files, Git, or output tables.

## Change

`src/data/collect_candidate_news.py` now supports:

```bash
--env-file .env.naver
```

The file should be local and gitignored. `.env.*` is already ignored by `.gitignore`.

Expected local file shape:

```bash
<Naver client ID variable>=<your local value>
<Naver client secret variable>=<your local value>
```

Do not commit this file.

## Ready-To-Run Command

After the local env file exists, run:

```bash
python3 src/data/collect_candidate_news.py \
  --env-file .env.naver \
  --output-name candidate_news_naver_v0_4 \
  --table-suffix naver_v0_4 \
  --scope-label run028_naver_news_collection \
  --mlb-limit-per-slot 16 \
  --asian-limit 30 \
  --query-mode compact \
  --max-items-per-query 6 \
  --timeout-sec 6 \
  --sleep-sec 0.05 \
  --providers naver_news
```

Then combine with the existing English layer:

```bash
python3 src/features/build_candidate_news_signals.py \
  --raw-dirs data/raw/articles/candidate_news_expanded_v0_2 data/raw/articles/candidate_news_naver_v0_4 \
  --scope-file outputs/tables/candidate_news_scope_v0_2.csv \
  --output-suffix v0_4 \
  --missing-status not_in_run028_combined_scope
```

## Current Status

Naver collection has not been executed in this run because the shell environment still does not contain `NAVER_CLIENT_ID` or `NAVER_CLIENT_SECRET`, and no local `.env.naver` file is present.

## Six-Layer Progress After Run 028

Progress does not move until actual Naver rows are collected.

| no. | layer | progress | movement |
|---:|---|---:|---|
| 1 | SSG hidden weakness mining | 93% | unchanged |
| 2 | KBO foreign-player success/failure archetype mining | 73% | unchanged |
| 3 | Candidate market construction | 92% | unchanged |
| 4 | KBO translation model | 80% | unchanged |
| 5 | Failure risk model | 82% | unchanged |
| 6 | SSG fit ranking | 68% | unchanged |

Candidate release remains locked.
