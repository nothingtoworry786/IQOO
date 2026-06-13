"""Competitor schemas — no user_id, added market_scope."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CompetitorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    industry: str = Field(..., min_length=1, max_length=128)
    website: str | None = Field(None, max_length=512)
    market_scope: str | None = Field(None, max_length=64)


class CompetitorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=256)
    industry: str | None = Field(None, min_length=1, max_length=128)
    website: str | None = Field(None, max_length=512)
    market_scope: str | None = Field(None, max_length=64)


class CompetitorResponse(BaseModel):
    id: str
    name: str
    industry: str
    website: str | None = None
    market_scope: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CompetitorWithSignals(CompetitorResponse):
    signals: list = []
    predictions: list = []
    momentum_score: float = 0.0
