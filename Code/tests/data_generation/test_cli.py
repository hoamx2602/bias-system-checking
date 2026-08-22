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
    request_file = next((tmp_path / "test-run" / "requests").glob("openai*.jsonl"))
    request = json.loads(request_file.read_text(encoding="utf-8").splitlines()[0])
    schema = request["body"]["text"]["format"]["schema"]
    prompt = request["body"]["input"][0]["content"][0]["text"]
    assert "generation_status" in schema["required"]
    assert "# Severity anchors" in prompt


def test_quality_report_fails_below_silver_threshold(tmp_path: Path, capsys):
    path = tmp_path / "judge-results.jsonl"
    records = [
        {"verdict": "accept" if index < 84 else "repair"}
        for index in range(100)
    ]
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    result = main(["quality-report", "--stage", "silver", "--input", str(path)])
    assert result == 1
    assert json.loads(capsys.readouterr().out)["acceptance_rate"] == 0.84
