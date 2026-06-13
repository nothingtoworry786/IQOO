from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.providers.base import AIProvider, AIProviderError

logger = logging.getLogger(__name__)


class GroqProvider(AIProvider):
    """AI provider that uses the Groq API."""

    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self) -> None:
        self.api_key = settings.GROQ_API_KEY
        self.model = settings.GROQ_MODEL

    async def generate(self, prompt: str, system: str | None = None) -> str:
        """Send a prompt to the Groq API and return the generated response.

        Args:
            prompt: The input prompt to send.

        Returns:
            The generated text content.

        Raises:
            AIProviderError: On API or network failure.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1024,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                )
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

