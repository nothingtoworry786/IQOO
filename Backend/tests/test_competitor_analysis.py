"""Tests for the competitor analysis service layer.

Tests cover:
- _build_prompt: system prompt construction
- _parse_response: JSON parsing and fallback logic
- analyze_competitor: end-to-end orchestration (with mocked provider)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.providers.base import AIProviderError
from app.schemas.requests import AnalyzeRequest
from app.services.competitor_analysis import (
    _build_prompt,
    _parse_response,
    analyze_competitor,
)


class TestBuildPrompt:
    """Tests for the _build_prompt helper."""

    def test_build_prompt_includes_competitor(self, sample_request: AnalyzeRequest) -> None:
        """The prompt should contain the competitor name."""
        prompt = _build_prompt(sample_request)
        assert sample_request.competitor_name in prompt

    def test_build_prompt_includes_city(self, sample_request: AnalyzeRequest) -> None:
        """The prompt should contain the target city."""
        prompt = _build_prompt(sample_request)
        assert sample_request.city in prompt

    def test_build_prompt_includes_signals(self, sample_request: AnalyzeRequest) -> None:
        """The prompt should contain all signal values."""
        prompt = _build_prompt(sample_request)
        assert str(sample_request.jobs_added) in prompt
        assert str(sample_request.ad_spend_change) in prompt
        assert str(sample_request.sentiment_change) in prompt

    def test_build_prompt_includes_system_instructions(self, sample_request: AnalyzeRequest) -> None:
        """The prompt should start with the system prompt."""
        prompt = _build_prompt(sample_request)
        assert prompt.startswith("You are MarketWatch")

    def test_build_prompt_is_string(self, sample_request: AnalyzeRequest) -> None:
        """The result should be a non-empty string."""
        prompt = _build_prompt(sample_request)
        assert isinstance(prompt, str)
        assert len(prompt) > 50


class TestParseResponse:
    """Tests for the _parse_response helper."""

    def test_parse_valid_json(self, valid_json_response: str) -> None:
        """A valid JSON string should parse correctly."""
        result = _parse_response(valid_json_response)
        assert result.summary == (
            "Blinkit is expanding rapidly in Pune with significant hiring "
            "and ad spend increases."
        )
        assert result.prediction == "Blinkit will capture 5-8% market share in Pune within 2 months."
        assert result.confidence == 75
        assert len(result.actions) == 3

    def test_parse_fenced_json(self, fenced_json_response: str) -> None:
        """A markdown-fenced JSON block should be stripped and parsed."""
        result = _parse_response(fenced_json_response)
        assert "Blinkit is scaling fast in Pune." in result.summary
        assert result.confidence == 82
        assert len(result.actions) == 3

    def test_parse_malformed_json_raises(self, malformed_json_response: str) -> None:
        """Non-JSON input should raise AIProviderError."""
        with pytest.raises(AIProviderError):
            _parse_response(malformed_json_response)

    def test_parse_empty_string_raises(self) -> None:
        """Empty string input should raise AIProviderError."""
        with pytest.raises(AIProviderError):
            _parse_response("")

    def test_parse_fallback_fields(self) -> None:
        """Missing fields should fall back to defaults."""
        result = _parse_response('{"summary": "Only summary"}')
        assert result.summary == "Only summary"
        assert result.prediction != ""  # should have default fallback
        assert result.confidence == 50  # default confidence
        assert len(result.actions) == 3  # fallback actions

    def test_parse_fallback_actions(self) -> None:
        """Fewer than 3 actions should use fallback defaults."""
        result = _parse_response(
            '{"summary": "s", "prediction": "p", "confidence": 60, "actions": ["Only one"]}'
        )
        assert len(result.actions) == 3
        # The implementation replaces ALL actions with defaults when fewer than 3
        assert result.actions[0] == "Monitor competitor activity closely."

    def test_parse_clamps_confidence(self) -> None:
        """Confidence values outside 0-100 should be clamped."""
        result = _parse_response(
            '{"summary": "s", "prediction": "p", "confidence": 999, "actions": ["a", "b", "c"]}'
        )
        assert result.confidence == 100

        result = _parse_response(
            '{"summary": "s", "prediction": "p", "confidence": -50, "actions": ["a", "b", "c"]}'
        )
        assert result.confidence == 0


class TestAnalyzeCompetitor:
    """Tests for the analyze_competitor async orchestration."""

    @patch("app.services.competitor_analysis.get_ai_provider")
    @pytest.mark.asyncio
    async def test_successful_analysis(
        self,
        mock_get_provider,
        sample_request: AnalyzeRequest,
        valid_json_response: str,
    ) -> None:
        """A successful provider call should return a parsed AnalyzeResponse."""
        mock_provider = AsyncMock()
        mock_provider.generate.return_value = valid_json_response
        mock_get_provider.return_value = mock_provider

        result = await analyze_competitor(sample_request)

        assert isinstance(result.summary, str)
        assert isinstance(result.prediction, str)
        assert 0 <= result.confidence <= 100
        assert len(result.actions) == 3
        mock_provider.generate.assert_awaited_once()

    @patch("app.services.competitor_analysis.get_ai_provider")
    @pytest.mark.asyncio
    async def test_provider_error_propagates(
        self,
        mock_get_provider,
        sample_request: AnalyzeRequest,
    ) -> None:
        """When the provider raises, the error should propagate."""
        mock_provider = AsyncMock()
        mock_provider.generate.side_effect = AIProviderError("API unavailable")
        mock_get_provider.return_value = mock_provider

        with pytest.raises(AIProviderError, match="API unavailable"):
            await analyze_competitor(sample_request)

    @patch("app.services.competitor_analysis.get_ai_provider")
    @pytest.mark.asyncio
    async def test_invalid_json_from_provider(
        self,
        mock_get_provider,
        sample_request: AnalyzeRequest,
        malformed_json_response: str,
    ) -> None:
        """If the provider returns non-JSON, AIProviderError should be raised."""
        mock_provider = AsyncMock()
        mock_provider.generate.return_value = malformed_json_response
        mock_get_provider.return_value = mock_provider

        with pytest.raises(AIProviderError, match="invalid JSON"):
            await analyze_competitor(sample_request)
