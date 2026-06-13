from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.providers.base import AIProviderError
from app.schemas.requests import AnalyzeRequest
from app.schemas.responses import AnalyzeResponse
from app.services.competitor_analysis import analyze_competitor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Analysis"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze competitor signals",
    description=(
        "Accepts competitor intelligence signals (jobs, ad spend, sentiment, city) "
        "and returns a structured analysis with summary, prediction, confidence, "
        "and recommended actions."
    ),
)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze competitor signals and return actionable intelligence.

    The request is forwarded to the configured AI provider (Groq or OpenRouter)
    which generates a structured competitive analysis.
    """
    logger.info(
        "POST /analyze - competitor=%s, city=%s",
        request.competitor_name,
        request.city,
    )

    try:
        result = await analyze_competitor(request)
        return result
    except AIProviderError as exc:
        logger.error("Analysis failed: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"AI provider error: {exc}",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during analysis")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during analysis.",
        ) from exc
