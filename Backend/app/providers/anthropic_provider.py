"""Anthropic (Claude) AI provider implementation."""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.providers.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """AI provider that uses the Anthropic Claude API."""

    BASE_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self) -> None:
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.ANTHROPIC_MODEL

    async def generate(self, prompt: str, system: str | None = None) -> str:
        """Send a prompt to the Anthropic API and return the generated response.

        Args:
            prompt: The input prompt to send.
            system: Optional system message.

        Returns:
            The generated text content.

        Raises:
            AIProviderError: On API or network failure.
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        payload: dict = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            content = data["content"][0]["text"]
            logger.info(
                "Anthropic API call successful (model=%s, tokens=%s)",
                self.model,
                data.get("usage", {}).get("output_tokens", "unknown"),
            )
            return content.strip()

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Anthropic API HTTP error: %s - %s",
                exc.response.status_code,
                exc.response.text,
            )
            raise AIProviderError(
                f"Anthropic API returned status {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.RequestError as exc:
            logger.error("Anthropic API request failed: %s", exc)
            raise AIProviderError(f"Anthropic API request failed: {exc}") from exc
        except (KeyError, IndexError) as exc:
            logger.error("Anthropic API unexpected response format: %s", exc)
            raise AIProviderError(f"Unexpected response format from Anthropic API: {exc}") from exc
