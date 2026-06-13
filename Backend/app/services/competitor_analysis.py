from __future__ import annotations

import json
import logging
import re

from app.core.ai_provider import get_ai_provider
from app.schemas.requests import AnalyzeRequest
from app.schemas.responses import AnalyzeResponse
from app.providers.base import AIProviderError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are MarketWatch, an elite competitive intelligence analyst.

Analyze competitor signals.

Return:
- summary
- prediction
- confidence
- 3 recommended actions

Return valid JSON only. Use this exact structure:
{{
  "summary": "string",
  "prediction": "string",
  "confidence": 74,
  "actions": ["string", "string", "string"]
}}"""


def _build_prompt(request: AnalyzeRequest) -> str:
    """Build the analysis prompt from the incoming request data."""
    return f"""{SYSTEM_PROMPT}

Competitor: {request.competitor_name}
City: {request.city}

Recent Signals:
- Jobs added: {request.jobs_added}
- Ad spend change: {request.ad_spend_change}%
- Sentiment change: {request.sentiment_change}%

Generate a comprehensive competitive intelligence analysis based on these signals."""



def _parse_response(raw: str) -> AnalyzeResponse:
    """Parse the JSON response from the AI provider into a structured response.

    Handles markdown-fenced JSON blocks and plain JSON strings.
    """
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        # Remove opening fence (possibly with language hint)
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        # Remove closing fence
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI provider response as JSON: %s", exc)
        raise AIProviderError(
            f"AI provider returned invalid JSON. Raw response: {raw[:500]}"
        ) from exc

    summary = data.get("summary", "")
    prediction = data.get("prediction", "")
    confidence = data.get("confidence", 50)
    actions = data.get("actions", [])

    # Validate and clamp confidence
    confidence = max(0, min(100, int(confidence))) if confidence is not None else 50

    # Ensure exactly 3 actions
    if not actions or len(actions) < 3:
        actions = [
            "Monitor competitor activity closely.",
            "Review and adjust marketing strategy.",
            "Strengthen local presence in the target city.",
        ]

    return AnalyzeResponse(
        summary=summary or "No summary provided.",
        prediction=prediction or "No prediction provided.",
        confidence=confidence,
        actions=actions[:3],
    )


async def analyze_competitor(request: AnalyzeRequest) -> AnalyzeResponse:
    """Orchestrate the competitor analysis workflow.

    Steps:
        1. Build the prompt from the request.
        2. Get the active AI provider.
        3. Call the provider to generate analysis.
        4. Parse the raw response into a structured output.

    Args:
        request: The validated analysis request.

    Returns:
        A structured analysis response.

    Raises:
        AIProviderError: If the AI provider fails or returns invalid data.
    """
    logger.info(
        "Starting analysis for competitor '%s' in '%s'",
        request.competitor_name,
        request.city,
    )

    prompt = _build_prompt(request)
    provider = get_ai_provider()

    logger.debug("Sending prompt to %s", type(provider).__name__)
    raw_response = await provider.generate(prompt)

    logger.debug("Raw response received (%d chars)", len(raw_response))
    result = _parse_response(raw_response)

    logger.info(
        "Analysis complete for '%s' (confidence=%d)",
        request.competitor_name,
        result.confidence,
    )

    return result
