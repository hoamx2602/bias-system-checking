"""OpenAI Responses Batch API request builder."""

from __future__ import annotations

from typing import Any

from .base import ProviderAdapter


class OpenAIAdapter(ProviderAdapter):
    provider = "openai"

    @property
    def artifact_format(self) -> str:
        return "jsonl"

    def build_generation_record(
        self,
        control_card: dict[str, Any],
        prompt: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "custom_id": self.safe_request_id(control_card["family_id"]),
            "method": "POST",
            "url": "/v1/responses",
            "body": {
                "model": self.model,
                "input": [{
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}],
                }],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "generated_bias_family",
                        "strict": True,
                        "schema": output_schema,
                    }
                },
                "store": False,
            },
        }
