"""Alert management API endpoints — using competitor_id."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertResponse, AlertUpdate
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])


@router.get("/", response_model=list[AlertResponse])
async def list_alerts(competitor_id: str | None = None) -> list[AlertResponse]:
    async with get_db() as db:
        query = select(Alert).order_by(Alert.created_at.desc())
        if competitor_id:
            query = query.where(Alert.competitor_id == competitor_id)
        result = await db.execute(query)
        return [AlertResponse.model_validate(a) for a in result.scalars().all()]


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(data: AlertCreate) -> AlertResponse:
    async with get_db() as db:
        alert = Alert(**data.model_dump())
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return AlertResponse.model_validate(alert)


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(alert_id: str, data: AlertUpdate) -> AlertResponse:
    async with get_db() as db:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(alert, field, value)
        await db.flush()
        await db.refresh(alert)
        return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(alert_id: str) -> None:
    async with get_db() as db:
        result = await db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        await db.delete(alert)
