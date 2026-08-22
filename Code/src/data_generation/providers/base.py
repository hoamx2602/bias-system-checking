"""Common contract for provider-specific batch request builders."""

from __future__ import annotations

import json
import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NativeBatchArtifact:
    provider: str
    format: str
    records: list[dict[str, Any]]


class ProviderAdapter(ABC):
    provider: str

    def __init__(self, model: str):
        if not model:
            raise ValueError(f"A model ID is required for {self.provider}")
        self.model = model

    @staticmethod
    def safe_request_id(family_id: str, limit: int = 64) -> str:
        value = re.sub(r"[^A-Za-z0-9_-]", "-", family_id)
        if len(value) <= limit:
            return value
        suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
        return f"{value[:limit - len(suffix) - 1]}-{suffix}"

    @abstractmethod
    def build_generation_record(
        self,
        control_card: dict[str, Any],
        prompt: str,
        output_schema: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError

    def build_artifact(
        self,
        control_cards: list[dict[str, Any]],
        prompt_template: str,
        output_schema: dict[str, Any],
    ) -> NativeBatchArtifact:
        records = []
        for card in control_cards:
            prompt = prompt_template.replace(
                "{{CONTROL_CARD_JSON}}",
                json.dumps(card, ensure_ascii=False, sort_keys=True),
            )
            records.append(self.build_generation_record(card, prompt, output_schema))
        return NativeBatchArtifact(provider=self.provider, format=self.artifact_format, records=records)

    @property
    @abstractmethod
    def artifact_format(self) -> str:
        raise NotImplementedError


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)
