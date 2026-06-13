"""Alert schemas with competitor_id."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    competitor_id: str
    alert_type: str = Field(..., max_length=64)
    threshold: float = Field(default=0.0)
    enabled: bool = True


class AlertUpdate(BaseModel):
    alert_type: str | None = Field(None, max_length=64)
    threshold: float | None = None
    enabled: bool | None = None


class AlertResponse(BaseModel):
    id: str
    competitor_id: str
    alert_type: str
    threshold: float
    enabled: bool
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
