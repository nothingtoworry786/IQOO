"""Prediction schemas for request/response serialization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PredictionCreate(BaseModel):
    competitor_id: str
    prediction: str
    confidence: int = Field(default=50, ge=0, le=100)
    threat_level: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    ai_reasoning: str | None = None


class PredictionResponse(BaseModel):
    id: str
    competitor_id: str
    prediction: str
    confidence: int
    threat_level: str
    ai_reasoning: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
