import json
from pathlib import Path

from src.data_generation.cli import main


def test_plan_command(capsys):
    result = main(["plan", "--families", "12", "--seed", "9"])
    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["families"] == 12
    assert payload["dialogue_variants"] == 72


def test_dry_run_creates_a_valid_manifest(tmp_path: Path):
    result = main([
        "dry-run",
        "--families", "3",
        "--seed", "11",
        "--run-id", "test-run",
        "--output-dir", str(tmp_path),
    ])
    assert result == 0
    manifest = json.loads((tmp_path / "test-run" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["family_count"] == 3
    assert manifest["variant_count"] == 18
    assert manifest["invalid_family_count"] == 0
    assert manifest["live_api_calls"] is False
    assert len(manifest["artifacts"]["provider_requests"]) == 3
