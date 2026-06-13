"""Signal management API endpoints with filtering, sorting, and search."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select

from app.models.competitor import Competitor
from app.models.signal import Signal, SignalCategory
from app.schemas.signal import SignalCreate, SignalResponse
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/signals", tags=["Signals"])


@router.get("/", response_model=list[SignalResponse])
async def list_signals(
    signal_type: SignalCategory | None = None,
    competitor_id: str | None = None,
    search: str | None = Query(None, max_length=256),
    sort_by: str | None = Query(None, pattern=r"^(newest|impact|urgency)$"),
    limit: int = Query(50, ge=1, le=200),
) -> list[SignalResponse]:
    """List signals with optional filtering, sorting, and search."""
    async with get_db() as db:
        query = select(Signal)

        if competitor_id:
            query = query.where(Signal.competitor_id == competitor_id)
        if signal_type:
            query = query.where(Signal.signal_type == signal_type)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Signal.title.ilike(pattern),
                    Signal.description.ilike(pattern),
                    Signal.source.ilike(pattern),
                )
            )

        # Sorting
        if sort_by == "impact":
            query = query.order_by(Signal.impact_score.desc(), Signal.created_at.desc())
        elif sort_by == "urgency":
            query = query.order_by(Signal.urgency_score.desc(), Signal.created_at.desc())
        else:
            query = query.order_by(Signal.created_at.desc())

        query = query.limit(limit)
        result = await db.execute(query)
        return [SignalResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
async def create_signal(data: SignalCreate) -> SignalResponse:
    """Create a new intelligence signal."""
    async with get_db() as db:
        # Verify competitor exists
        result = await db.execute(
            select(Competitor).where(Competitor.id == data.competitor_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Competitor not found")

        signal = Signal(**data.model_dump())
        db.add(signal)
        await db.flush()
        await db.refresh(signal)
        return SignalResponse.model_validate(signal)


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str) -> SignalResponse:
    """Get a single signal by ID."""
    async with get_db() as db:
        result = await db.execute(select(Signal).where(Signal.id == signal_id))
        signal = result.scalar_one_or_none()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        return SignalResponse.model_validate(signal)


