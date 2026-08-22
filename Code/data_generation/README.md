# Synthetic HR and Procurement Bias Data Setup

This directory contains the versioned inputs for the generation pipeline: coverage
configuration, JSON schemas, and prompt templates. Runtime outputs are written to
`data_generation/runs/` and are ignored by Git.

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

## 6. Tests

```powershell
python -m pytest tests/data_generation -q
```

## Live API boundary

The current setup deliberately stops at provider-native batch artifacts. Submission,
polling, downloading, and normalization will be enabled only after small provider smoke
tests confirm account access, exact model IDs, retention settings, and cost limits.

Never upload files from `dataset/` that contain real or sensitive data. The pilot must use
synthetic control cards only.
