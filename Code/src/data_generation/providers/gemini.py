"""Gemini Batch API JSONL request builder."""

from __future__ import annotations

from typing import Any

from .base import ProviderAdapter


class GeminiAdapter(ProviderAdapter):
    provider = "gemini"

    @property
    def artifact_format(self) -> str:
        return "jsonl"

    def build_generation_record(
        self,
        control_card: dict[str, Any],
        prompt: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        # The model is selected when the Gemini batch job is submitted, not per JSONL line.
        return {
            "key": self.safe_request_id(control_card["family_id"]),
            "request": {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}],
                }],
                "generation_config": {
                    "response_mime_type": "application/json",
                    "response_schema": output_schema,
                },
            },
        }
