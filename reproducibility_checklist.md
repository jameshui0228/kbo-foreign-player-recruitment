# Reproducibility Checklist

Updated: 2026-06-12 KST

## Current Reproducible Commands

```bash
python3 src/features/build_savant_pitcher_features.py
python3 src/features/build_external_message_tables.py
python3 src/features/build_three_slot_message_framework.py
python3 src/features/mine_slot_message_evidence.py
```

## Required Before Final

- Record Python version and package versions.
- Ensure API keys are never written to repository files.
- Regenerate all outputs from raw data.
- Store exact candidate-screen generation commands.
- Store final shortlist CSV.
- Check final report links point to stable local files.

## Verified

- Message mining evidence tables were generated on 2026-06-12.
- Three-slot message framework table was generated on 2026-06-12.
- Secrets were previously checked by string search and not found in project files.
