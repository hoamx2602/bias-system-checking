"""Provider-native request builders."""

from .anthropic import AnthropicAdapter
from .base import ProviderAdapter
from .gemini import GeminiAdapter
from .openai import OpenAIAdapter


def get_adapter(provider: str, model: str) -> ProviderAdapter:
    adapters = {
        "openai": OpenAIAdapter,
        "gemini": GeminiAdapter,
        "anthropic": AnthropicAdapter,
    }
    try:
        return adapters[provider](model=model)
    except KeyError as exc:
        raise ValueError(f"Unsupported provider: {provider}") from exc


__all__ = [
    "AnthropicAdapter",
    "GeminiAdapter",
    "OpenAIAdapter",
    "ProviderAdapter",
    "get_adapter",
]
