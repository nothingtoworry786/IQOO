"""Signal schemas with value field."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SignalCreate(BaseModel):
    competitor_id: str
    signal_type: str = Field(..., max_length=64)
    source: str = Field(..., max_length=256)
    value: str | None = None
    impact_score: float = Field(default=0.0, ge=-10, le=10)
    urgency_score: float = Field(default=0.0, ge=0, le=10)


class SignalResponse(BaseModel):
    id: str
    competitor_id: str
    signal_type: str
    source: str
    value: str | None = None
    impact_score: float
    urgency_score: float
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
