# IncuBrix Option 2 — Social Media Content Engine

A reproducible Python content-engine prototype for the IncuBrix 2027 Growth Engineer assessment (Option 2: Social Media Marketing & Content Engine).

The engine takes one long-form text input and produces platform-adapted candidate assets for LinkedIn, Instagram, and YouTube Shorts, then applies validation, quality scoring, duplicate prevention, scheduling, UTM generation, and assessment-ready CSV export.

## 1. What this repository demonstrates

- One long-form input -> 20+ accepted social assets in deterministic mock mode
- Platform adaptation for LinkedIn, Instagram, and YouTube Shorts
- Four approved content pillars
- Hooks, captions, CTAs, hashtags/metadata, and UTM generation
- Brand/hype checks and unsupported-claim flagging
- 0–100 quality scoring with an acceptance threshold
- Exact, normalized, and TF-IDF/cosine semantic duplicate detection
- Refresh mode that blocks same-input repeats and allows genuinely new source material to generate fresh angles
- Scheduler-ready `calendar.csv` using the official workbook column schema
- Run evidence, QA summaries, rejected-asset logs, and duplicate reports
- Deterministic mock mode so reviewers can rerun the pipeline without paid APIs
- Readable failure behavior for missing/empty inputs
- Pytest suite that does not require live API calls

## 2. Architecture

```text
long-form input
    -> generation provider
    -> UTM builder
    -> brand / claim validation
    -> quality scoring
    -> exact + semantic dedupe
    -> acceptance threshold
    -> scheduler
    -> official CSV export + QA/debug evidence
```

Core modules:

```text
src/
  main.py            CLI orchestration
  config_loader.py   YAML / env / CLI configuration
  generator.py       deterministic mock provider + live-provider abstraction
  validators.py      brand, claim, completeness, platform checks
  scoring.py         transparent 0–100 quality score
  dedupe.py          exact + TF-IDF/cosine duplicate detection
  utm.py             campaign tracking URLs
  scheduler.py       platform cadence/date assignment
  exporter.py        official workbook-schema CSV output
  logger.py          run logs and JSON summaries
  models.py          dataclasses and official schema
```

## 3. Repository structure

```text
config/
  brand_rules.yaml
  engine.yaml
  platform_rules.yaml
examples/
  sample_input.txt
  new_input.txt
run-evidence/
src/
tests/
.env.example
.gitignore
README.md
requirements.txt
```

## 4. Python version

Recommended: Python 3.11+.

## 5. Setup

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

No API key is required for the default mock/demo mode.

## 6. Environment configuration

Copy `.env.example` to `.env` only if you need environment overrides.

```text
CONTENT_ENGINE_PROVIDER=mock
CONTENT_ENGINE_BASE_URL=https://example.com
CONTENT_ENGINE_CAMPAIGN=creator_os_launch
CONTENT_ENGINE_SEED=42
```

`https://example.com` is intentionally a placeholder. Replace it with the approved IncuBrix destination URL before any real launch. Do not invent a production URL.

Never commit `.env`.

## 7. One clear reviewer run command

```bash
python -m src.main --input examples/sample_input.txt
```

Expected behavior in mock mode:
- generates candidate assets
- validates and scores them
- removes duplicates
- accepts at least 20 when the repository is in its tested default configuration
- writes a new timestamped folder under `run-evidence/`
- writes `calendar.csv` to the project root for convenient review

## 8. Mock/demo mode

The default mode is deterministic mock mode:

```bash
python -m src.main --input examples/sample_input.txt --seed 42
```

Mock content is explicitly labelled in the `tools_used`/notes metadata and must not be represented as live LLM output.

## 9. Official CSV schema

`accepted_assets.csv` and `calendar.csv` use exactly these columns:

```text
asset_id
platform
format
content_pillar
hook
caption
cta
utm_link
final_file_url
source_file_url
source_input
tools_used
rights_checked
ai_label_needed
scheduled_date
test_published_url
impressions_or_views
engagement_rate
clicks
status
notes
duplicate_check
completeness_check
```

Workbook-facing platform values are normalized to `LinkedIn`, `Instagram`, and `YouTube Shorts`.

Workbook-facing format values use the assessment categories such as `text post`, `carousel`, `graphic`, and `short video`.

`rights_checked` and `ai_label_needed` export as `Yes`/`No`. Media-requiring concepts are conservatively marked `rights_checked=No` until a human verifies the final footage/images; the reason is preserved in `notes`.

No performance metrics, customer claims, final-file URLs, or publishing URLs are fabricated.

## 10. Quality scoring

The 100-point score covers:
- hook quality
- platform fit
- usefulness
- specificity
- brand voice
- CTA fit
- claim safety
- originality
- completeness

Default acceptance threshold: `75`.

Rejected items are written to `rejected_assets.csv` with their reasons.

## 11. Brand and claim safety

`config/brand_rules.yaml` contains:
- approved tone rules
- banned hype phrases
- unsupported-claim patterns
- observed IncuBrix capabilities from firsthand product testing

The engine does not treat sample Dashboard metrics as real IncuBrix performance.

The previously observed Home quick-start error is a launch risk, not a benefit claim.

## 12. Duplicate prevention

Three layers are used:
1. normalized exact hash
2. within-run semantic similarity using TF-IDF + cosine similarity
3. refresh comparison against prior accepted assets

Default within-run semantic threshold: `0.82`.

For refresh comparison, a stricter cross-run threshold is used so that the exact same source is blocked while genuinely new source material may reuse a topic without being rejected only because the editorial template is similar.

`duplicate_report.csv` records:
- duplicate asset ID
- matched asset ID
- similarity score
- detection method
- action taken

## 13. Refresh behavior

Same-input repeat:

```bash
python -m src.main --input examples/sample_input.txt --refresh
```

A deterministic repeat should activate duplicate prevention.

New-source refresh:

```bash
python -m src.main --input examples/new_input.txt --refresh
```

The deterministic mock provider grounds each candidate in the supplied source text, allowing new source material to produce fresh accepted assets while still being compared with prior runs.

## 14. Scheduling

Default cadence:
- LinkedIn: 3/week
- Instagram: 3/week
- YouTube Shorts: 2/week

The scheduler expands the horizon when accepted output exceeds four-week capacity so a `Ready` asset is not silently left without a scheduled date.

## 15. Experiment metadata

The engine supports internal experiment tags:
- `EXP_HOOK` — pain-led vs outcome-led
- `EXP_FORMAT` — demo-led vs educational
- `EXP_CTA` — generic vs outcome-specific

These appear in QA/debug output or notes rather than altering the official workbook schema.

## 16. Run evidence

Each normal run creates:

```text
run-evidence/run_YYYYMMDD_HHMMSS/
  run_summary.json
  qa_summary.json
  accepted_assets.csv
  rejected_assets.csv
  duplicate_report.csv
  qa_debug.csv
  calendar.csv
  run.log
```

The run summary records input size, candidate/accepted/rejected counts, duplicates removed, runtime, mode/provider, and cost status.

In mock mode direct generation cost is `not_applicable`. The engine never invents live API cost.

## 17. Four assessment run scenarios

### Run 1 — normal

```bash
python -m src.main --input examples/sample_input.txt
```

Capture the terminal summary and the newly created run-evidence folder.

### Run 2 — same-input repeat / duplicate prevention

```bash
python -m src.main --input examples/sample_input.txt --refresh
```

Expected: duplicate prevention activates strongly because the deterministic source and templates are the same.

### Run 3 — new-input refresh

```bash
python -m src.main --input examples/new_input.txt --refresh
```

Expected: new source-grounded assets are compared with prior accepted assets; fresh items can pass while close duplicates are rejected.

### Run 4 — failure and recovery

Failure:

```bash
python -m src.main --input examples/does_not_exist.txt
```

Expected: a readable input error and non-zero exit code.

Recovery:

```bash
python -m src.main --input examples/sample_input.txt
```

Expected: successful normal run.

## 18. Tests

```bash
pytest -q
```

The test suite covers configuration, UTM generation, exact and semantic dedupe, banned phrases, required hook/CTA checks, quality-score bounds, official export normalization, empty input failure, and deterministic mock-mode execution.

## 19. Privacy and secrets

- `.env` is gitignored.
- `.env.example` contains placeholders only.
- No secrets are required in mock mode.
- Do not commit API keys, access tokens, passwords, private customer data, or private social data.

## 20. Cost note

Mock mode has no direct model API cost and records `not_applicable`.

If a live provider is implemented later, actual cost must be calculated from provider usage rather than guessed.

## 21. Known limitations

1. Live OpenAI/Anthropic/Google generation is intentionally **not implemented in this repository version**; the current `LiveGenerationProvider` falls back to deterministic mock generation and logs that limitation.
2. Mock content validates the engineering pipeline; it is not evidence of real LLM output quality.
3. Final visual/video files still require human production and rights review. The engine creates scripts/concepts/copy and intentionally does not fabricate `final_file_url` or `source_file_url`.
4. Analytics values remain blank until real publishing/test data exists.
5. The base URL remains a placeholder until IncuBrix provides or approves the real destination URL.
6. Platform publishing APIs are outside this prototype; the export is scheduler/workbook-ready rather than an auto-publisher.

These limitations are explicit so a reviewer can distinguish verified pipeline behavior from future/live integrations.
