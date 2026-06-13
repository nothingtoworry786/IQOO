"""Strategy AI agent — synthesises all signals into strategic recommendations."""

from __future__ import annotations

from app.agents.base import BaseAgent


class StrategyAgent(BaseAgent):
    """AI agent specialised in strategic competitive intelligence.

    Synthesises marketing, product, and sales signals into an overall strategic assessment.
    """

    def __init__(self) -> None:
        super().__init__(
            name="StrategyAI",
            description="Synthesises all competitive signals into strategic recommendations for leadership.",
        )

    @property
    def system_prompt(self) -> str:
        return """You are StrategyAI, an elite strategic competitive intelligence analyst reporting to the CEO.

Analyse the provided competitor context and agent insights, then return a structured JSON response with:

- **summary** (string): A 2-3 sentence executive summary of the competitive situation.
- **threat_level** (string): One of "low", "medium", "high", "critical".
- **momentum_score** (integer): Competitor momentum score from 0-100.
- **prediction** (string): The most likely next move from the competitor.
- **strategic_actions** (list of 3 strings): Recommended strategic actions ranked by priority.
- **time_horizon** (string): "immediate", "short_term", "medium_term", or "long_term".
- **confidence** (float): 0.0 to 1.0 confidence in this strategic assessment.

Return valid JSON only, with no additional text."""
