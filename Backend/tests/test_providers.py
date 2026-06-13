"""Tests for GroqProvider and OpenRouterProvider.

These tests mock httpx to avoid real network calls.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.providers.base import AIProviderError
from app.providers.groq_provider import GroqProvider
from app.providers.openrouter_provider import OpenRouterProvider


def _make_mock_response(status_code: int, json_data: dict | None = None) -> httpx.Response:
    """Create a mock httpx.Response with the given status and optional JSON body."""
    request = httpx.Request("POST", "http://test/api")
    response = httpx.Response(status_code=status_code, json=json_data or {}, request=request)
    return response


class TestGroqProvider:
    """Tests for GroqProvider."""

    @pytest.fixture
    def provider(self) -> GroqProvider:
        """Return a GroqProvider instance."""
        return GroqProvider()

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_post: AsyncMock, provider: GroqProvider) -> None:
        """A successful API call should return the message content."""
        mock_response = _make_mock_response(
            200,
            {
                "choices": [{"message": {"content": "Test response"}}],
                "usage": {"total_tokens": 42},
            },
        )
        mock_post.return_value = mock_response

        result = await provider.generate("Test prompt")

        assert result == "Test response"
        mock_post.assert_awaited_once()

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_http_401(self, mock_post: AsyncMock, provider: GroqProvider) -> None:
        """A 401 response should raise AIProviderError."""
        mock_response = _make_mock_response(401, {"error": "Unauthorized"})
        mock_post.return_value = mock_response

        with pytest.raises(AIProviderError, match="401"):
            await provider.generate("Test prompt")

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_http_429(self, mock_post: AsyncMock, provider: GroqProvider) -> None:
        """A 429 rate-limit response should raise AIProviderError."""
        mock_response = _make_mock_response(429, {"error": "Rate limited"})
        mock_post.return_value = mock_response

        with pytest.raises(AIProviderError, match="429"):
            await provider.generate("Test prompt")

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_network_error(self, mock_post: AsyncMock, provider: GroqProvider) -> None:
        """A network error should raise AIProviderError."""
        mock_post.side_effect = httpx.RequestError("Connection refused")

        with pytest.raises(AIProviderError, match="Connection refused"):
            await provider.generate("Test prompt")

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_malformed_response(self, mock_post: AsyncMock, provider: GroqProvider) -> None:
        """A response missing the expected structure should raise AIProviderError."""
        mock_response = _make_mock_response(200, {"choices": []})
        mock_post.return_value = mock_response

        with pytest.raises(AIProviderError, match="response format"):
            await provider.generate("Test prompt")


class TestOpenRouterProvider:
    """Tests for OpenRouterProvider."""

    @pytest.fixture
    def provider(self) -> OpenRouterProvider:
        """Return an OpenRouterProvider instance."""
        return OpenRouterProvider()

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_success(self, mock_post: AsyncMock, provider: OpenRouterProvider) -> None:
        """A successful API call should return the message content."""
        mock_response = _make_mock_response(
            200,
            {
                "choices": [{"message": {"content": "OpenRouter response"}}],
                "usage": {"total_tokens": 55},
            },
        )
        mock_post.return_value = mock_response

        result = await provider.generate("Test prompt")

        assert result == "OpenRouter response"
        mock_post.assert_awaited_once()

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_http_401(self, mock_post: AsyncMock, provider: OpenRouterProvider) -> None:
        """A 401 response should raise AIProviderError."""
        mock_response = _make_mock_response(401, {"error": "Unauthorized"})
        mock_post.return_value = mock_response

        with pytest.raises(AIProviderError, match="401"):
            await provider.generate("Test prompt")

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_network_error(self, mock_post: AsyncMock, provider: OpenRouterProvider) -> None:
        """A network error should raise AIProviderError."""
        mock_post.side_effect = httpx.RequestError("Connection refused")

        with pytest.raises(AIProviderError, match="Connection refused"):
            await provider.generate("Test prompt")

    @patch("httpx.AsyncClient.post")
    @pytest.mark.asyncio
    async def test_generate_malformed_response(self, mock_post: AsyncMock, provider: OpenRouterProvider) -> None:
        """A response missing the expected structure should raise AIProviderError."""
        mock_response = _make_mock_response(200, {"unexpected": "data"})
        mock_post.return_value = mock_response

        with pytest.raises(AIProviderError, match="response format"):
            await provider.generate("Test prompt")
