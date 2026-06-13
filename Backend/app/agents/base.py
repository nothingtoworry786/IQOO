"""Base class for all MarketWatch AI agents."""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from app.core.ai_provider import get_ai_provider
from app.providers.base import AIProviderError

logger = logging.getLogger(__name__)


class AgentResult:
    """Structured result from an AI agent."""

    def __init__(
        self,
        agent_name: str,
        summary: str,
        data: dict[str, Any] | None = None,
        confidence: float = 0.7,
    ) -> None:
        self.agent_name = agent_name
        self.summary = summary
        self.data = data or {}
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "summary": self.summary,
            "data": self.data,
            "confidence": self.confidence,
        }


class BaseAgent(ABC):
    """Abstract base class for all MarketWatch AI agents."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt that defines the agent's persona and behaviour."""
        ...

    async def analyze(
        self,
        context: str,
        structured_output: bool = True,
    ) -> AgentResult:
        """Run the agent against the given context and return structured results.

        Args:
            context: The market / competitor context to analyse.
            structured_output: Whether to expect JSON output from the LLM.

        Returns:
            An AgentResult with the analysis.
        """
        prompt = self._build_prompt(context)
        provider = get_ai_provider()

        try:
            raw = await provider.generate(prompt)
        except AIProviderError as exc:
            logger.error("%s agent failed: %s", self.name, exc)
            return AgentResult(
                agent_name=self.name,
                summary=f"Analysis failed: {exc}",
                confidence=0.0,
            )

        if structured_output:
            return self._parse_json(raw)
        return AgentResult(agent_name=self.name, summary=raw.strip(), confidence=0.5)

    def _build_prompt(self, context: str) -> str:
        """Build the full prompt from system prompt + context."""
        return f"{self.system_prompt}\n\nContext:\n{context}"

    def _parse_json(self, raw: str) -> AgentResult:
        """Parse a JSON response from the LLM into an AgentResult."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```\w*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning("%s agent returned non-JSON, falling back to raw text", self.name)
            return AgentResult(
                agent_name=self.name,
                summary=raw[:500],
                confidence=0.3,
            )

        return AgentResult(
            agent_name=self.name,
            summary=data.get("summary", "No summary provided."),
            data=data,
            confidence=float(data.get("confidence", 0.5)),
        )
