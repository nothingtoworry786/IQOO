"""Tests for Pydantic request/response schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.requests import AnalyzeRequest
from app.schemas.responses import AnalyzeResponse, HealthResponse


class TestAnalyzeRequest:
    """Validate the AnalyzeRequest schema."""

    def test_valid_request(self) -> None:
        """A fully populated request should pass validation."""
        req = AnalyzeRequest(
            competitor_name="Zepto",
            jobs_added=10,
            ad_spend_change=25,
            sentiment_change=-5,
            city="Mumbai",
        )
        assert req.competitor_name == "Zepto"
        assert req.jobs_added == 10
        assert req.ad_spend_change == 25
        assert req.sentiment_change == -5
        assert req.city == "Mumbai"

    def test_minimal_valid_request(self) -> None:
        """Boundary values should still pass."""
        req = AnalyzeRequest(
            competitor_name="X",
            jobs_added=0,
            ad_spend_change=-100,
            sentiment_change=100,
            city="NY",
        )
        assert req.competitor_name == "X"
        assert req.jobs_added == 0
        assert req.ad_spend_change == -100
        assert req.sentiment_change == 100
        assert req.city == "NY"

    def test_empty_competitor_name_raises(self) -> None:
        """Empty competitor_name should fail min_length validation."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(
                competitor_name="",
                jobs_added=5,
                ad_spend_change=10,
                sentiment_change=0,
                city="Delhi",
            )

    def test_empty_city_raises(self) -> None:
        """Empty city should fail min_length validation."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(
                competitor_name="Swiggy",
                jobs_added=5,
                ad_spend_change=10,
                sentiment_change=0,
                city="",
            )

    def test_negative_jobs_added_raises(self) -> None:
        """Negative jobs_added should fail ge=0 validation."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(
                competitor_name="Zepto",
                jobs_added=-1,
                ad_spend_change=10,
                sentiment_change=0,
                city="Bangalore",
            )

    def test_missing_field_raises(self) -> None:
        """Omitting a required field should fail."""
        with pytest.raises(ValidationError):
            AnalyzeRequest(
                competitor_name="Test",
                jobs_added=5,
                ad_spend_change=10,
                # missing sentiment_change
                city="TestCity",
            )  # type: ignore[call-arg]


class TestAnalyzeResponse:
    """Validate the AnalyzeResponse schema."""

    def test_valid_response(self) -> None:
        """A fully populated response should pass."""
        resp = AnalyzeResponse(
            summary="Test summary",
            prediction="Test prediction",
            confidence=50,
            actions=["Action A", "Action B", "Action C"],
        )
        assert resp.summary == "Test summary"
        assert resp.confidence == 50
        assert len(resp.actions) == 3

    def test_confidence_at_boundaries(self) -> None:
        """Confidence values at the edges should be accepted."""
        AnalyzeResponse(
            summary="s",
            prediction="p",
            confidence=0,
            actions=["a", "b", "c"],
        )
        AnalyzeResponse(
            summary="s",
            prediction="p",
            confidence=100,
            actions=["a", "b", "c"],
        )

    def test_confidence_below_zero_raises(self) -> None:
        """Confidence below 0 should fail ge=0 validation."""
        with pytest.raises(ValidationError):
            AnalyzeResponse(
                summary="s",
                prediction="p",
                confidence=-1,
                actions=["a", "b", "c"],
            )

    def test_confidence_above_100_raises(self) -> None:
        """Confidence above 100 should fail le=100 validation."""
        with pytest.raises(ValidationError):
            AnalyzeResponse(
                summary="s",
                prediction="p",
                confidence=101,
                actions=["a", "b", "c"],
            )

    def test_less_than_three_actions_raises(self) -> None:
        """Fewer than 3 actions should fail min_length validation."""
        with pytest.raises(ValidationError):
            AnalyzeResponse(
                summary="s",
                prediction="p",
                confidence=50,
                actions=["Only one action"],
            )

    def test_more_than_three_actions_raises(self) -> None:
        """More than 3 actions should fail max_length validation."""
        with pytest.raises(ValidationError):
            AnalyzeResponse(
                summary="s",
                prediction="p",
                confidence=50,
                actions=["a", "b", "c", "d"],
            )


class TestHealthResponse:
    """Validate the HealthResponse schema."""

    def test_valid_health(self) -> None:
        """A valid health response should be accepted."""
        h = HealthResponse(status="running", project="MarketWatch")
        assert h.status == "running"
        assert h.project == "MarketWatch"

    def test_missing_field_raises(self) -> None:
        """Omitting a field should fail."""
        with pytest.raises(ValidationError):
            HealthResponse(status="running")  # type: ignore[call-arg]
