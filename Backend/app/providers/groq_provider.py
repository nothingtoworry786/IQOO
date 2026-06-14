from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.providers.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)

# Shared across all GroqProvider instances — caps concurrent Groq calls to stay
# under the free-tier 30 RPM limit (5 slots × ~6s avg latency ≈ 50 RPM ceiling).
_SEMAPHORE = asyncio.Semaphore(5)
_MAX_RETRIES = 4
_BASE_BACKOFF = 2.0  # seconds; doubles each retry


class GroqProvider(AIProvider):
    """AI provider that uses the Groq API."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self) -> None:
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL

    async def generate(self, prompt: str, system: str | None = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 4096,
        }

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            async with _SEMAPHORE:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(self.BASE_URL, headers=headers, json=payload)

                    if response.status_code == 429:
                        # Respect Retry-After if present, otherwise exponential backoff
                        retry_after = float(response.headers.get("retry-after", _BASE_BACKOFF * (2 ** attempt)))
                        logger.warning(
                            "Groq rate limit hit (attempt %d/%d), waiting %.1fs",
                            attempt + 1, _MAX_RETRIES, retry_after,
                        )
                        await asyncio.sleep(retry_after)
                        last_exc = AIProviderError(f"Groq API returned status 429: {response.text}")
                        continue

                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info(
                        "Groq API call successful (model=%s, tokens=%s)",
                        self.model,
                        data.get("usage", {}).get("total_tokens", "unknown"),
                    )
                    return content.strip()

                except httpx.HTTPStatusError as exc:
                    logger.error("Groq API HTTP error: %s - %s", exc.response.status_code, exc.response.text)
                    raise AIProviderError(
                        f"Groq API returned status {exc.response.status_code}: {exc.response.text}"
                    ) from exc
                except httpx.RequestError as exc:
                    logger.error("Groq API request failed: %s", exc)
                    raise AIProviderError(f"Groq API request failed: {exc}") from exc
                except (KeyError, IndexError) as exc:
                    logger.error("Groq API unexpected response format: %s", exc)
                    raise AIProviderError(f"Unexpected response format from Groq API: {exc}") from exc

        raise last_exc or AIProviderError("Groq API rate limit exceeded after all retries")

