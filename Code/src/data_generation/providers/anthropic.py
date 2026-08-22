"""Claude Message Batches request builder."""

from __future__ import annotations

import json
from typing import Any

from .base import ProviderAdapter


class AnthropicAdapter(ProviderAdapter):
    provider = "anthropic"

    @property
    def artifact_format(self) -> str:
        return "json"

    def build_generation_record(
        self,
        control_card: dict[str, Any],
        prompt: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        # JSON is enforced by the prompt and validated locally after retrieval. Keeping the
        # provider-neutral schema in the prompt avoids coupling this setup to a beta header.
        schema_instruction = (
            "\n\nReturn only JSON matching this JSON Schema:\n"
            + json.dumps(output_schema, ensure_ascii=False, sort_keys=True)
        )
        return {
            "custom_id": self.safe_request_id(control_card["family_id"]),
            "params": {
                "model": self.model,
                "max_tokens": 6000,
                "temperature": 0.7,
                "messages": [{
                    "role": "user",
                    "content": prompt + schema_instruction,
                }],
            },
        }
