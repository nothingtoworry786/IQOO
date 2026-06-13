"""Signal schemas with title/description, categories, and search/filter support."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.signal import SignalCategory


class SignalCreate(BaseModel):
    competitor_id: str
    signal_type: SignalCategory
    source: str = Field(..., max_length=256)
    title: str = Field(..., max_length=256)
    description: str | None = None
    impact_score: float = Field(default=0.0, ge=0, le=10)
    urgency_score: float = Field(default=0.0, ge=0, le=10)


class SignalResponse(BaseModel):
    id: str
    competitor_id: str
    signal_type: SignalCategory
    source: str
    title: str
    description: str | None = None
    impact_score: float
    urgency_score: float
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

