from __future__ import annotations

from ..config import Settings
from .base import Provider, ProviderError
from .offline import OfflineProvider


def build_provider(settings: Settings) -> Provider:
    if settings.provider == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            settings.anthropic_model, settings.company_name, settings.max_history_messages
        )
    if settings.provider == "openai":
        if not settings.openai_model:
            raise RuntimeError("Set OPENAI_MODEL to the model id you want to use.")
        from .openai_provider import OpenAIProvider

        return OpenAIProvider(
            settings.openai_model, settings.company_name, settings.max_history_messages
        )
    if settings.provider == "offline":
        return OfflineProvider()
    raise RuntimeError(f"Unknown LLM_PROVIDER: {settings.provider!r}")


__all__ = ["Provider", "ProviderError", "build_provider"]
