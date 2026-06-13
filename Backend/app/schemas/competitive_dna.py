"""Competitive DNA schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CompetitiveDNACreate(BaseModel):
    competitor_id: str
    pattern_type: str = Field(..., max_length=64)
    description: str
    embedding: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class CompetitiveDNAResponse(BaseModel):
    id: str
    competitor_id: str
    pattern_type: str
    description: str
    embedding: str | None = None
    confidence_score: float
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class DNASimilarityResult(BaseModel):
    competitor_name: str
    pattern_type: str
    description: str
    confidence_score: float
    similarity_score: float
