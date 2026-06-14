# Contributing

## Before You Start

1. Pull the latest `main`.
2. Create a topic branch.
3. Check `docs/six_layer_progress_board.md` to understand the current layer status.
4. Do not commit raw data or secrets.

## Recommended Commands

```bash
git checkout main
git pull
git checkout -b analysis/layer2-foreign-archetypes
```

## Commit Style

Use short, concrete commit messages:

```text
Add layer 2 archetype validation table
Update SSG layer 1 progress board
Fix Naver news tag parser
```

## Validation

For script changes, run at least:

```bash
python3 -m py_compile src/path/to/script.py
python3 src/path/to/script.py
```

For modeling changes, record the row counts, metrics, and promotion/hold decision in:

- `docs/experiment_log.md`
- `experiments.csv`

## Pull Request Checklist

- [ ] No API keys, tokens, or secrets committed
- [ ] No `data/raw/`, `data/interim/`, or `data/processed/` files committed
- [ ] Relevant scripts were rerun or the reason is documented
- [ ] Row counts or model metrics are recorded
- [ ] Six-layer progress is updated if the work changes project status
- [ ] Candidate recommendation lock is respected

