"""Competitor management API endpoints — simplified."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.models.competitor import Competitor
from app.models.signal import Signal, SignalCategory
from app.models.prediction import Prediction
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorResponse,
    CompetitorUpdate,
    CompetitorWithSignals,
)
from app.schemas.signal import SignalResponse
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/competitors", tags=["Competitors"])


@router.get("/", response_model=list[CompetitorResponse])
async def list_competitors() -> list[CompetitorResponse]:
    async with get_db() as db:
        result = await db.execute(select(Competitor).order_by(Competitor.created_at.desc()))
        return [CompetitorResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
async def create_competitor(data: CompetitorCreate) -> CompetitorResponse:
    async with get_db() as db:
        competitor = Competitor(**data.model_dump())
        db.add(competitor)
        await db.flush()
        await db.refresh(competitor)
        return CompetitorResponse.model_validate(competitor)


@router.get("/{competitor_id}", response_model=CompetitorWithSignals)
async def get_competitor(competitor_id: str) -> CompetitorWithSignals:
    async with get_db() as db:
        result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = result.scalar_one_or_none()
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")

        return CompetitorWithSignals(
            id=competitor.id,
            name=competitor.name,
            industry=competitor.industry,
            website=competitor.website,
            market_scope=competitor.market_scope,
            created_at=competitor.created_at,
            updated_at=competitor.updated_at,
            signals=list(competitor.signals) if competitor.signals else [],
            predictions=list(competitor.predictions) if competitor.predictions else [],
            momentum_score=_calculate_momentum(competitor),
        )


@router.put("/{competitor_id}", response_model=CompetitorResponse)
async def update_competitor(competitor_id: str, data: CompetitorUpdate) -> CompetitorResponse:
    async with get_db() as db:
        result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = result.scalar_one_or_none()
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(competitor, field, value)
        await db.flush()
        await db.refresh(competitor)
        return CompetitorResponse.model_validate(competitor)


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_competitor(competitor_id: str) -> None:
    async with get_db() as db:
        result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = result.scalar_one_or_none()
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        await db.delete(competitor)


@router.get("/{competitor_id}/momentum", response_model=dict)
async def get_competitor_momentum(competitor_id: str) -> dict:
    async with get_db() as db:
        result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = result.scalar_one_or_none()
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")

        signals = list(competitor.signals) if competitor.signals else []
        predictions = list(competitor.predictions) if competitor.predictions else []
        momentum = _calculate_momentum(competitor)

        return {
            "competitor_name": competitor.name,
            "momentum_score": momentum,
            "signal_count": len(signals),
            "prediction_count": len(predictions),
            "recent_signals": [
                {"type": s.signal_type, "impact": s.impact_score, "urgency": s.urgency_score,
                 "source": s.source, "created_at": s.created_at.isoformat()}
                for s in signals[-5:]
            ],
            "latest_prediction": {
                "prediction": predictions[-1].prediction,
                "confidence": predictions[-1].confidence,
                "threat_level": predictions[-1].threat_level,
            } if predictions else None,
        }



@router.get("/{competitor_id}/signals", response_model=list[SignalResponse])
async def get_competitor_signals(
    competitor_id: str,
    signal_type: SignalCategory | None = None,
    sort_by: str | None = None,
    limit: int = 50,
) -> list[SignalResponse]:
    """Get signals for a specific competitor."""
    async with get_db() as db:
        # Verify competitor exists
        result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Competitor not found")

        query = select(Signal).where(Signal.competitor_id == competitor_id)
        if signal_type:
            query = query.where(Signal.signal_type == signal_type)
        if sort_by == "impact":
            query = query.order_by(Signal.impact_score.desc(), Signal.created_at.desc())
        elif sort_by == "urgency":
            query = query.order_by(Signal.urgency_score.desc(), Signal.created_at.desc())
        else:
            query = query.order_by(Signal.created_at.desc())
        query = query.limit(limit)

        result = await db.execute(query)
        return [SignalResponse.model_validate(s) for s in result.scalars().all()]


def _calculate_momentum(competitor: Competitor) -> float:
    signals = list(competitor.signals) if competitor.signals else []
    if not signals:
        return 0.0
    total_impact = sum(s.impact_score for s in signals)
    total_urgency = sum(s.urgency_score for s in signals)
    count = len(signals)
    score = ((total_impact / count) * 5) + ((total_urgency / count) * 5)
    return max(0.0, min(100.0, score))
