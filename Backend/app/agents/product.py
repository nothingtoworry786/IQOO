"""Product AI agent — analyses competitor product strategy."""

from __future__ import annotations

from app.agents.base import BaseAgent


class ProductAgent(BaseAgent):
    """AI agent specialised in competitive product intelligence.

    Analyses product launches, feature changes, hiring for R&D, and product roadmaps.
    """

    def __init__(self) -> None:
        super().__init__(
            name="ProductAI",
            description="Analyses competitor product launches, features, hiring patterns, and roadmaps.",
        )

    @property
    def system_prompt(self) -> str:
        return """You are ProductAI, an elite competitive product intelligence analyst.

Analyse the provided competitor context and return a structured JSON response with:

- **summary** (string): A 2-3 sentence overview of the competitor's product direction.
- **threat_level** (string): One of "low", "medium", "high", "critical".
- **product_changes** (list of strings): Product or feature changes detected.
- **hiring_signals** (list of strings): Hiring patterns that indicate product direction (e.g., hiring engineers for mobile).
- **launch_timeline** (string): Estimated timeline for any upcoming product launches.
- **recommended_response** (string): What your company should do in response.
- **confidence** (float): 0.0 to 1.0 confidence in this analysis.

Return valid JSON only, with no additional text."""
