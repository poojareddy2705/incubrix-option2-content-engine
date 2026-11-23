# Engine repair / verification notes

This repository was completed after an interrupted Antigravity implementation.

Verified locally on 2026-11-22:

- `pytest -q` -> 12 passed
- default mock dry run -> 29 accepted, 0 rejected, 0 duplicates
- same-input refresh -> duplicate prevention activates on all deterministic repeats
- new-input refresh -> 24 accepted, 1 quality rejection, 4 duplicates removed in the verification sequence
- missing-input failure -> readable error, exit code 1
- official export -> exactly 23 required workbook columns
- export platforms -> LinkedIn, Instagram, YouTube Shorts
- export formats -> text post, carousel, graphic, short video
- rights / AI label export -> Yes/No values
- all Ready assets in verified normal run received scheduled dates

Important: these are local engineering verification results for deterministic mock mode, not public campaign performance or live AI-generation results.
