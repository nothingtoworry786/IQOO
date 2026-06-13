"""Shared fixtures and configuration for the test suite."""

from __future__ import annotations

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.routers.analysis import router as analysis_router
from app.schemas.requests import AnalyzeRequest
from app.schemas.responses import AnalyzeResponse, HealthResponse


@pytest.fixture
def app() -> FastAPI:
    """Create a fresh FastAPI app with the analysis router for testing."""
    application = FastAPI(title="MarketWatch Test")
    application.include_router(analysis_router)

    @application.get("/")
    async def health() -> HealthResponse:
        return HealthResponse(status="running", project="MarketWatch")

    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient wired to the test app via ASGI."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_request() -> AnalyzeRequest:
    """Return a standard AnalyzeRequest for use across tests."""
    return AnalyzeRequest(
        competitor_name="Blinkit",
        jobs_added=23,
        ad_spend_change=40,
        sentiment_change=-18,
        city="Pune",
    )


@pytest.fixture
def sample_response() -> AnalyzeResponse:
    """Return a standard AnalyzeResponse for use across tests."""
    return AnalyzeResponse(
        summary="Blinkit is aggressively expanding in Pune with 23 new jobs and 40% more ad spend.",
        prediction="Blinkit will likely capture 5-8% more market share in Pune within the next quarter.",
        confidence=74,
        actions=[
            "Increase local marketing spend in Pune by 20%.",
            "Accelerate hiring for delivery partner roles.",
            "Launch a customer loyalty program in Pune.",
        ],
    )


@pytest.fixture
def valid_json_response() -> str:
    """Return a valid JSON string that matches the expected LLM response format."""
    return """{
  "summary": "Blinkit is expanding rapidly in Pune with significant hiring and ad spend increases.",
  "prediction": "Blinkit will capture 5-8% market share in Pune within 2 months.",
  "confidence": 75,
  "actions": [
    "Increase local marketing budget by 20%",
    "Hire more delivery partners in Pune",
    "Launch targeted customer promotions"
  ]
}"""


@pytest.fixture
def fenced_json_response() -> str:
    """Return a markdown-fenced JSON block as some LLMs output."""
    return """```json
{
  "summary": "Blinkit is scaling fast in Pune.",
  "prediction": "They will dominate quick-commerce in Pune.",
  "confidence": 82,
  "actions": [
    "Match their delivery times",
    "Improve app UX",
    "Offer first-order discounts"
  ]
}
```"""


@pytest.fixture
def malformed_json_response() -> str:
    """Return a non-JSON string to test error handling."""
    return "I think Blinkit is doing well in Pune. They are hiring a lot."
