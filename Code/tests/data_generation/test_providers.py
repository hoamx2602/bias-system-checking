import json

from src.data_generation.coverage import build_assignments, load_coverage_cells
from src.data_generation.dry_run import control_card_from_assignment
from src.data_generation.providers import get_adapter
from src.data_generation.providers.base import ProviderAdapter


SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["family_id"],
    "properties": {"family_id": {"type": "string"}},
}
PROMPT = "Generate from {{CONTROL_CARD_JSON}}"


def _card():
    assignment = build_assignments(load_coverage_cells(), 1)[0]
    return control_card_from_assignment(assignment)


def test_openai_batch_record_uses_responses_and_json_schema():
    record = get_adapter("openai", "test-openai-model").build_artifact([_card()], PROMPT, SCHEMA).records[0]
    assert record["url"] == "/v1/responses"
    assert record["body"]["text"]["format"]["type"] == "json_schema"
    assert len(record["custom_id"]) <= 64


def test_gemini_batch_record_has_key_and_request():
    record = get_adapter("gemini", "test-gemini-model").build_artifact([_card()], PROMPT, SCHEMA).records[0]
    assert record["key"]
    assert record["request"]["generation_config"]["response_mime_type"] == "application/json"
    assert record["request"]["generation_config"]["response_schema"] == SCHEMA


def test_anthropic_batch_record_uses_message_batch_shape():
    record = get_adapter("anthropic", "test-claude-model").build_artifact([_card()], PROMPT, SCHEMA).records[0]
    assert record["params"]["model"] == "test-claude-model"
    assert record["params"]["messages"][0]["role"] == "user"
    assert json.dumps(SCHEMA, sort_keys=True) in record["params"]["messages"][0]["content"]
    assert len(record["custom_id"]) <= 64


def test_long_request_ids_remain_bounded_and_distinct():
    first = ProviderAdapter.safe_request_id("family-" + "a" * 100 + "-1")
    second = ProviderAdapter.safe_request_id("family-" + "a" * 100 + "-2")
    assert len(first) <= 64
    assert len(second) <= 64
    assert first != second
