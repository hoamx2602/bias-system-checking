import json
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_DIR = Path(__file__).resolve().parents[2] / "data_generation" / "schemas"


def test_all_json_schemas_are_valid_draft_2020_12():
    schema_paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
    assert schema_paths
    for path in schema_paths:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
