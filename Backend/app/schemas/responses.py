from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeResponse(BaseModel):
    """Response schema for the competitor analysis endpoint."""

    summary: str = Field(
        ...,
        description="A concise summary of the competitor's current position",
    )
    prediction: str = Field(
        ...,
        description="Predicted next moves or market direction for the competitor",
    )
    confidence: int = Field(
        ...,
        description="Confidence score (0-100) for the prediction",
        ge=0,
        le=100,
    )
    actions: list[str] = Field(
        ...,
        description="Three recommended strategic actions to take",
        min_length=3,
        max_length=3,
    )


class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""

    status: str = Field(..., description="Service running status")
    project: str = Field(..., description="Project name")
