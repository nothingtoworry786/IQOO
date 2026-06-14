"""Ollama provider — routes AI calls to a local Ollama instance.

Ollama exposes an OpenAI-compatible endpoint at /v1/chat/completions.
No API key is required; pass any non-empty string as the bearer token.
"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.providers.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)

_SEMAPHORE = asyncio.Semaphore(5)
_MAX_RETRIES = 3
_BASE_BACKOFF = 2.0


class OllamaProvider(AIProvider):
    """AI provider that uses a local Ollama instance."""

    def __init__(self) -> None:
        self.host = settings.OLLAMA_HOST.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.url = f"{self.host}/v1/chat/completions"

    async def generate(self, prompt: str, system: str | None = None) -> str:
        headers = {
            "Authorization": "Bearer ollama",
            "Content-Type": "application/json",
        }
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "stream": False,
        }

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            async with _SEMAPHORE:
                try:
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(self.url, headers=headers, json=payload)

                    if response.status_code == 503:
                        wait = _BASE_BACKOFF * (2 ** attempt)
                        logger.warning("Ollama unavailable (attempt %d/%d), waiting %.1fs", attempt + 1, _MAX_RETRIES, wait)
                        await asyncio.sleep(wait)
                        last_exc = AIProviderError(f"Ollama returned 503")
                        continue

                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    tokens = data.get("usage", {}).get("total_tokens", "?")
                    logger.info("Ollama call successful (model=%s, tokens=%s)", self.model, tokens)
                    return content.strip()

                except httpx.HTTPStatusError as exc:
                    logger.error("Ollama HTTP error: %s - %s", exc.response.status_code, exc.response.text)
                    raise AIProviderError(f"Ollama returned status {exc.response.status_code}: {exc.response.text}") from exc
                except httpx.RequestError as exc:
                    logger.error("Ollama request failed: %s", exc)
                    raise AIProviderError(f"Cannot reach Ollama at {self.host} — is it running? ({exc})") from exc
                except (KeyError, IndexError) as exc:
                    logger.error("Ollama unexpected response: %s", exc)
                    raise AIProviderError(f"Unexpected response from Ollama: {exc}") from exc

        raise last_exc or AIProviderError("Ollama unavailable after all retries")
