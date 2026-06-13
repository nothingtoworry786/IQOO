"""Sales AI agent — analyses competitor sales and go-to-market strategy."""

from __future__ import annotations

from app.agents.base import BaseAgent


class SalesAgent(BaseAgent):
    """AI agent specialised in competitive sales intelligence.

    Analyses pricing changes, discounting patterns, expansion cities, and sales hiring.
    """

    def __init__(self) -> None:
        super().__init__(
            name="SalesAI",
            description="Analyses competitor pricing, expansion, discounts, and sales strategies.",
        )

    @property
    def system_prompt(self) -> str:
        return """You are SalesAI, an elite competitive sales intelligence analyst.

Analyse the provided competitor context and return a structured JSON response with:

- **summary** (string): A 2-3 sentence overview of the competitor's sales strategy.
- **threat_level** (string): One of "low", "medium", "high", "critical".
- **pricing_changes** (string): Any pricing or discount changes detected.
- **expansion_cities** (list of strings): Cities the competitor is expanding into.
- **sales_hiring** (string): Sales team growth signals.
- **recommended_response** (string): What your company should do in response.
- **confidence** (float): 0.0 to 1.0 confidence in this analysis.

Return valid JSON only, with no additional text."""
