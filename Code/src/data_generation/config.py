"""Configuration loading without exposing provider secrets."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


CODE_ROOT = Path(__file__).resolve().parents[2]
GENERATION_ROOT = CODE_ROOT / "data_generation"
DEFAULT_COVERAGE_PATH = GENERATION_ROOT / "configs" / "coverage.yaml"
DEFAULT_PROVIDER_PATH = GENERATION_ROOT / "configs" / "providers.example.yaml"
DEFAULT_QUALITY_PATH = GENERATION_ROOT / "configs" / "quality_thresholds.yaml"
DEFAULT_RUNS_DIR = GENERATION_ROOT / "runs"

load_dotenv(CODE_ROOT / ".env")


@dataclass(frozen=True)
class ProviderSettings:
    name: str
    enabled: bool
    api_key_env: str
    generator_model: str
    judge_model: str
    batch_endpoint: str

    @property
    def has_api_key(self) -> bool:
        return bool(os.environ.get(self.api_key_env, "").strip())


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a YAML object in {path}")
    return payload


def _resolve_model(provider: dict[str, Any], role: str) -> str:
    env_name = str(provider.get(f"{role}_model_env", "")).strip()
    default = str(provider.get(f"{role}_model_default", "")).strip()
    return os.environ.get(env_name, default).strip() if env_name else default


def load_provider_settings(path: str | Path = DEFAULT_PROVIDER_PATH) -> dict[str, ProviderSettings]:
    raw = load_yaml(path).get("providers", {})
    if not isinstance(raw, dict):
        raise ValueError("providers must be a YAML object")

    settings: dict[str, ProviderSettings] = {}
    for name, values in raw.items():
        if not isinstance(values, dict):
            raise ValueError(f"Provider {name} must be an object")
        settings[name] = ProviderSettings(
            name=name,
            enabled=bool(values.get("enabled", True)),
            api_key_env=str(values["api_key_env"]),
            generator_model=_resolve_model(values, "generator"),
            judge_model=_resolve_model(values, "judge"),
            batch_endpoint=str(values["batch_endpoint"]),
        )
    return settings
