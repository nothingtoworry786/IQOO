"""Integration tests for the FastAPI endpoints.

Uses the TestClient (via httpx.AsyncClient with ASGITransport) against the
test app without requiring real API keys or network access.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.providers.base import AIProviderError

from app.schemas.requests import AnalyzeRequest


class TestHealthEndpoint:
    """Tests for the GET / health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_returns_status(self, client: AsyncClient) -> None:
        """The health endpoint should return a 200 with status and project."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["project"] == "MarketWatch"

    @pytest.mark.asyncio
    async def test_health_is_get(self, client: AsyncClient) -> None:
        """The health endpoint should only respond to GET."""
        response = await client.post("/")
        assert response.status_code in (405,)


class TestAnalyzeEndpoint:
    """Tests for the POST /api/v1/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_success(
        self, client: AsyncClient, valid_json_response: str
    ) -> None:
        """A valid request should return 200 with an AnalyzeResponse."""
        with patch(
            "app.services.competitor_analysis.get_ai_provider"
        ) as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = valid_json_response
            mock_get_provider.return_value = mock_provider

            payload = {
                "competitor_name": "Blinkit",
                "jobs_added": 23,
                "ad_spend_change": 40,
                "sentiment_change": -18,
                "city": "Pune",
            }

            response = await client.post("/api/v1/analyze", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert "summary" in data
            assert "prediction" in data
            assert "confidence" in data
            assert "actions" in data
            assert isinstance(data["confidence"], int)
            assert len(data["actions"]) == 3

    @pytest.mark.asyncio
    async def test_analyze_validation_error(self, client: AsyncClient) -> None:
        """Invalid request data should return 422."""
        payload = {
            "competitor_name": "",  # empty, violates min_length
            "jobs_added": -5,  # negative, violates ge=0
            "ad_spend_change": 40,
            "sentiment_change": -18,
            "city": "Pune",
        }

        response = await client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_missing_field(self, client: AsyncClient) -> None:
        """A request missing a required field should return 422."""
        payload = {
            "competitor_name": "Blinkit",
            "jobs_added": 10,
            # missing ad_spend_change
            "sentiment_change": -5,
            "city": "Delhi",
        }

        response = await client.post("/api/v1/analyze", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_provider_error(self, client: AsyncClient) -> None:
        """When the AI provider fails, the endpoint should return 502."""
        with patch(
            "app.services.competitor_analysis.get_ai_provider"
        ) as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.side_effect = AIProviderError("Provider down")
            mock_get_provider.return_value = mock_provider

            payload = {
                "competitor_name": "Zepto",
                "jobs_added": 5,
                "ad_spend_change": 10,
                "sentiment_change": 0,
                "city": "Mumbai",
            }

            response = await client.post("/api/v1/analyze", json=payload)
            assert response.status_code == 502
            assert "AI provider error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_analyze_invalid_json_from_provider(
        self, client: AsyncClient, malformed_json_response: str
    ) -> None:
        """Malformed JSON from the provider should return 502."""
        with patch(
            "app.services.competitor_analysis.get_ai_provider"
        ) as mock_get_provider:
            mock_provider = AsyncMock()
            mock_provider.generate.return_value = malformed_json_response
            mock_get_provider.return_value = mock_provider

            payload = {
                "competitor_name": "Swiggy",
                "jobs_added": 15,
                "ad_spend_change": -10,
                "sentiment_change": 5,
                "city": "Bangalore",
            }

            response = await client.post("/api/v1/analyze", json=payload)
            assert response.status_code == 502

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    async def test_analyze_unexpected_error(
        self, client: AsyncClient, sample_request: AnalyzeRequest
    ) -> None:
        """An unexpected exception should return 500."""
        with patch(
            "app.routers.analysis.analyze_competitor"
        ) as mock_analyze:
            mock_analyze.side_effect = RuntimeError("Unexpected crash")

            payload = sample_request.model_dump()

            response = await client.post("/api/v1/analyze", json=payload)
            assert response.status_code == 500
