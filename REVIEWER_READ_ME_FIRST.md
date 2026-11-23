# IncuBrix Option 2 — Content Engine

Candidate: C. Pooja Reddy

## Reviewer quick start

```powershell
python -m pip install -r requirements.txt
python -m src.main --input examples/sample_input.txt
python -m src.main --input examples/sample_input.txt --refresh
python -m src.main --input examples/new_input.txt --refresh
python -m pytest -q
```

## Important disclosure

This assessment engine runs in deterministic **mock mode** so the workflow is reproducible.
It demonstrates:
- one long-form input -> many structured social assets
- brand/completeness validation
- duplicate prevention
- accepted/rejected routing
- scheduler-ready calendar export
- logging
- failure and recovery evidence

It is **not presented as live AI generation**.

## Expected proof

- `src/` — engine implementation
- `config/` — brand/platform rules
- `examples/` — sample and refresh inputs
- `tests/` — automated tests
- `run-evidence/` — normal, dedupe, refresh and failure/recovery evidence
- `docs/` — architecture, commands, mock disclosure, reviewer guide, test summary
