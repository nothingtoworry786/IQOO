from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request schema for the competitor analysis endpoint."""

    competitor_name: str = Field(
        ...,
        description="Name of the competitor being analysed",
        min_length=1,
        max_length=256,
    )
    jobs_added: int = Field(
        ...,
        description="Number of jobs posted by the competitor recently",
        ge=0,
    )
    ad_spend_change: int = Field(
        ...,
        description="Percentage change in competitor ad spend",
    )
    sentiment_change: int = Field(
        ...,
        description="Percentage change in competitor sentiment score",
    )
    city: str = Field(
        ...,
        description="Target city for the analysis",
        min_length=1,
        max_length=128,
    )
