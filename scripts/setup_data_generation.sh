#!/usr/bin/env bash
set -euo pipefail

script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_root/.." && pwd)"
code_root="$repo_root/Code"
venv_root="$code_root/.venv-generation"
python_command="${PYTHON_COMMAND:-python3}"

if [[ ! -x "$venv_root/bin/python" ]]; then
  "$python_command" -m venv "$venv_root"
fi

"$venv_root/bin/python" -m pip install --upgrade pip
"$venv_root/bin/python" -m pip install -r "$code_root/requirements-generation.txt"

if [[ ! -f "$code_root/.env" ]]; then
  cp "$code_root/.env.example" "$code_root/.env"
  echo "Created Code/.env from .env.example. Add provider API keys before live calls."
else
  echo "Preserved existing Code/.env. Copy missing generation variables from .env.example."
fi

cd "$code_root"
"$venv_root/bin/python" -m pytest tests/data_generation -q
"$venv_root/bin/python" run_data_generation.py plan --families 100 --seed 42
run_id="setup-smoke-$(date -u +%Y%m%d-%H%M%S)"
"$venv_root/bin/python" run_data_generation.py dry-run --families 12 --seed 42 --run-id "$run_id"

echo "Setup complete. Run Code/.venv-generation/bin/python Code/run_data_generation.py check-env"
