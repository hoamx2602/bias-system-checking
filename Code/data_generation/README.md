# Synthetic HR and Procurement Bias Data Setup

This directory contains the versioned inputs for the generation pipeline: coverage
configuration, JSON schemas, and prompt templates. Runtime outputs are written to
`data_generation/runs/` and are ignored by Git.

Version 2 is the active contract. It adds behavioural severity anchors, explicit
legitimate-justification tests for HR and Procurement, exact fact/evidence checks, blind
judge packets, a two-phase arbiter, and measured acceptance gates. Version 1 files remain
available only for reproducibility.

The implementation plan is in
[`docs/data_generation_implementation_plan.md`](../../docs/data_generation_implementation_plan.md).

## 1. Environment setup

Automated Windows setup from the repository root:

```powershell
.\scripts\setup_data_generation_windows.ps1
```

Manual setup from `Code/`:

```powershell
python -m venv .venv-generation
.\.venv-generation\Scripts\Activate.ps1
python -m pip install -r requirements-generation.txt
Copy-Item .env.example .env
```

Do not overwrite an existing `.env`; instead copy only the generation variables from
`.env.example`. API keys are not required for `plan`, `dry-run`, or `validate`.

## 2. Check coverage and allocation

```powershell
python run_data_generation.py plan --families 100 --seed 42
```

This previews distribution by domain, provider, split, and coverage cell. The split is
deterministic at `family_id` level, so all six variants remain together.

## 3. Offline dry-run

```powershell
python run_data_generation.py dry-run --families 12 --run-id local-smoke-001
```

The command creates:

- `manifest.json` with hashes and counts.
- `control_cards.jsonl`.
- `bronze.jsonl` containing deterministic fixture families.
- `validation.jsonl`.
- Provider-native generation request artifacts under `requests/`.

No external API call is made.

## 4. Provider environment check

After adding keys to `.env`:

```powershell
python run_data_generation.py check-env
```

The command reports only whether a key exists. It never prints secret values.

## 5. Validate retrieved/generated data

```powershell
python run_data_generation.py validate `
  --input data_generation/runs/<run-id>/bronze.jsonl `
  --report data_generation/runs/<run-id>/validation-recheck.jsonl
```

For raw `generation_v2` provider output, validate against the matching control cards:

```powershell
python run_data_generation.py validate-v2 `
  --input data_generation/runs/<run-id>/raw-generation-v2.jsonl `
  --control-cards data_generation/runs/<run-id>/control_cards.jsonl `
  --report data_generation/runs/<run-id>/prejudge-validation.jsonl
```

## 6. Quality release gates

The thresholds in `configs/quality_thresholds.yaml` are enforced as pipeline stop rules:

- At least 90% of a 100-family calibration pilot must pass automated pre-judge checks.
- After at most one targeted repair, at least 85% must receive an `accept` verdict for
  release to Silver.
- A smaller pilot or a result below either threshold fails closed. Inspect failures by
  domain, stage, provider, coverage cell, and reason code before generating at scale.

```powershell
python run_data_generation.py quality-report `
  --stage prejudge `
  --input data_generation/runs/<run-id>/prejudge-validation.jsonl

python run_data_generation.py quality-report `
  --stage silver `
  --input data_generation/runs/<run-id>/family-judge-results.jsonl
```

The 85% value is an acceptance criterion, not a promise made before provider calibration.
Do not start the 1,000-family run unless the measured 100-family pilot passes.

## 7. Tests

```powershell
python -m pytest tests/data_generation -q
```

## Live API boundary

The current setup deliberately stops at provider-native batch artifacts. Submission,
polling, downloading, and normalization will be enabled only after small provider smoke
tests confirm account access, exact model IDs, retention settings, and cost limits.

Never upload files from `dataset/` that contain real or sensitive data. The pilot must use
synthetic control cards only.
