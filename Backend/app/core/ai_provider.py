"""AI provider factory — supports Groq, OpenRouter, Anthropic, and Ollama."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.providers.base import AIProvider
from app.providers.groq_provider import GroqProvider
from app.providers.openrouter_provider import OpenRouterProvider

logger = logging.getLogger(__name__)


def get_ai_provider() -> AIProvider:
    """Factory function that returns the active AI provider based on configuration.

    The provider is selected via the ``AI_PROVIDER`` environment variable.
    Supports: groq, openrouter, anthropic, ollama
    """
    provider_name = settings.AI_PROVIDER

    if provider_name == "groq":
        logger.info("Initialising Groq provider (model=%s)", settings.GROQ_MODEL)
        return GroqProvider()

    if provider_name == "openrouter":
        logger.info("Initialising OpenRouter provider (model=%s)", settings.OPENROUTER_MODEL)
        return OpenRouterProvider()

    if provider_name == "anthropic":
        logger.info("Initialising Anthropic provider (model=%s)", settings.ANTHROPIC_MODEL)
        try:
            from app.providers.anthropic_provider import AnthropicProvider
            return AnthropicProvider()
        except Exception as exc:
            logger.error("Failed to load Anthropic provider: %s", exc)
            raise ValueError(f"Anthropic provider not available: {exc}") from exc

    if provider_name == "ollama":
        logger.info("Initialising Ollama provider (host=%s, model=%s)", settings.OLLAMA_HOST, settings.OLLAMA_MODEL)
        from app.providers.ollama_provider import OllamaProvider
        return OllamaProvider()

    raise ValueError(f"Unknown AI provider: {provider_name}")
