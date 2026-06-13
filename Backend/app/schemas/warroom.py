"""War Room report schemas for request/response serialization."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WarRoomReportCreate(BaseModel):
    competitor_id: str
    threat_summary: str
    recommended_actions: str | None = None
    impact_score: float = Field(default=0.0, ge=-10, le=10)


class WarRoomReportResponse(BaseModel):
    id: str
    competitor_id: str
    threat_summary: str
    recommended_actions: str | None = None
    impact_score: float
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
