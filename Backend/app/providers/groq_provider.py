from __future__ import annotations

import asyncio
import logging

import httpx

from app.core.config import settings
from app.providers.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


class GroqRateLimitError(AIProviderError):
    """Raised when Groq's quota is exhausted. Carries the server's Retry-After
    so callers can open a circuit breaker for exactly that long instead of
    retrying Groq on every request."""

    def __init__(self, message: str, retry_after: float) -> None:
        super().__init__(message)
        self.retry_after = retry_after

# Shared across all GroqProvider instances. Cap concurrency at 2 so that, with
# max_tokens=2048, two in-flight requests (~2×2.8K tokens reserved) stay under
# the 8B model's 6K tokens-per-minute free-tier ceiling and avoid 429s.
_SEMAPHORE = asyncio.Semaphore(2)
_MAX_RETRIES = 4
_BASE_BACKOFF = 2.0   # seconds; doubles each retry
# Never block a request longer than this on a 429. If Groq's Retry-After exceeds
# it, the per-minute/daily quota is exhausted — fail fast so callers fall back
# instead of freezing the request for minutes.
_MAX_BACKOFF = 30.0   # seconds


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
            "max_tokens": 2048,
        }

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            # Only the network call holds a semaphore slot — the backoff sleep
            # happens outside so a rate-limited call doesn't block other slots.
            async with _SEMAPHORE:
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.post(self.BASE_URL, headers=headers, json=payload)
                except httpx.RequestError as exc:
                    logger.error("Groq API request failed: %s", exc)
                    raise AIProviderError(f"Groq API request failed: {exc}") from exc

            if response.status_code == 429:
                # Respect Retry-After if present, otherwise exponential backoff.
                requested = float(response.headers.get("retry-after", _BASE_BACKOFF * (2 ** attempt)))

                # A long Retry-After means the per-minute/daily quota is exhausted.
                # Don't freeze the request for minutes — fail fast and let the
                # caller's fallback handle it.
                if requested > _MAX_BACKOFF:
                    logger.error(
                        "Groq quota exhausted — Retry-After %.0fs exceeds cap %.0fs. "
                        "Failing fast so the pipeline can fall back.",
                        requested, _MAX_BACKOFF,
                    )
                    raise GroqRateLimitError(
                        f"Groq rate limit: quota exhausted (retry in {requested:.0f}s). "
                        "Free-tier limit hit — try again later or upgrade the Groq plan.",
                        retry_after=requested,
                    )

                wait = min(requested, _MAX_BACKOFF)
                logger.warning(
                    "Groq rate limit hit (attempt %d/%d), waiting %.1fs",
                    attempt + 1, _MAX_RETRIES, wait,
                )
                await asyncio.sleep(wait)
                last_exc = AIProviderError(f"Groq API returned status 429: {response.text}")
                continue

            try:
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
            except (KeyError, IndexError) as exc:
                logger.error("Groq API unexpected response format: %s", exc)
                raise AIProviderError(f"Unexpected response format from Groq API: {exc}") from exc

        raise last_exc or AIProviderError("Groq API rate limit exceeded after all retries")

