"""Signal management API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.models.signal import Signal
from app.schemas.signal import SignalCreate, SignalResponse
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/signals", tags=["Signals"])


@router.get("/", response_model=list[SignalResponse])
async def list_signals(
    competitor_id: str | None = None,
    signal_type: str | None = None,
    limit: int = 50,
) -> list[SignalResponse]:
    async with get_db() as db:
        query = select(Signal).order_by(Signal.created_at.desc()).limit(limit)
        if competitor_id:
            query = query.where(Signal.competitor_id == competitor_id)
        if signal_type:
            query = query.where(Signal.signal_type == signal_type)
        result = await db.execute(query)
        return [SignalResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
async def create_signal(data: SignalCreate) -> SignalResponse:
    async with get_db() as db:
        signal = Signal(**data.model_dump())
        db.add(signal)
        await db.flush()
        await db.refresh(signal)
        return SignalResponse.model_validate(signal)


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str) -> SignalResponse:
    async with get_db() as db:
        result = await db.execute(select(Signal).where(Signal.id == signal_id))
        signal = result.scalar_one_or_none()
        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")
        return SignalResponse.model_validate(signal)
