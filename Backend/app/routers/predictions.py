"""Prediction management API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/predictions", tags=["Predictions"])


@router.get("/", response_model=list[PredictionResponse])
async def list_predictions(
    competitor_id: str | None = None,
    limit: int = 50,
) -> list[PredictionResponse]:
    """List predictions, optionally filtered by competitor."""
    async with get_db() as db:
        query = select(Prediction).order_by(Prediction.created_at.desc()).limit(limit)
        if competitor_id:
            query = query.where(Prediction.competitor_id == competitor_id)
        result = await db.execute(query)
        predictions = result.scalars().all()
        return [PredictionResponse.model_validate(p) for p in predictions]


@router.post("/", response_model=PredictionResponse)
async def create_prediction(data: PredictionCreate) -> PredictionResponse:
    """Create a new prediction for a competitor."""
    async with get_db() as db:
        prediction = Prediction(**data.model_dump())
        db.add(prediction)
        await db.flush()
        await db.refresh(prediction)
        return PredictionResponse.model_validate(prediction)


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(prediction_id: str) -> PredictionResponse:
    """Get a prediction by ID."""
    async with get_db() as db:
        result = await db.execute(
            select(Prediction).where(Prediction.id == prediction_id)
        )
        prediction = result.scalar_one_or_none()
        if not prediction:
            raise HTTPException(status_code=404, detail="Prediction not found")
        return PredictionResponse.model_validate(prediction)
