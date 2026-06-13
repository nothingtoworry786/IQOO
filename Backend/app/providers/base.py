from __future__ import annotations

from abc import ABC, abstractmethod


class AIProviderError(Exception):
    """Raised when an AI provider fails to generate a response."""


class AIProvider(ABC):
    """Abstract base class for all AI providers."""

    @abstractmethod
    async def generate(self, prompt: str, system: str | None = None) -> str:
        """Send a prompt to the AI model and return the generated response.

        Args:
            prompt: The input prompt to send to the AI model.
            system: Optional system message (used by some providers like Anthropic).

        Returns:
            The generated text response from the AI model.

        Raises:
            AIProviderError: If the API call fails or returns an invalid response.
        """
        ...
