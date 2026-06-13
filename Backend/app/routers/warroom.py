"""War Room report API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.models.competitor import Competitor
from app.models.warroom import WarRoomReport
from app.schemas.warroom import WarRoomReportCreate, WarRoomReportResponse
from app.services.database import get_db
from app.services.warroom import generate_war_room_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/warroom", tags=["War Room"])


@router.post("/analyze", response_model=dict)
async def analyze_competitor_warroom(
    competitor_name: str,
    city: str,
    jobs_added: int = 0,
    ad_spend_change: int = 0,
    sentiment_change: int = 0,
    include_agents: bool = False,
) -> dict:
    """Run a full War Room analysis on a competitor.

    This runs all 4 AI agents (Marketing, Product, Sales, Strategy)
    and returns a consolidated strategic report.
    """
    from app.schemas.requests import AnalyzeRequest

    request = AnalyzeRequest(
        competitor_name=competitor_name,
        city=city,
        jobs_added=jobs_added,
        ad_spend_change=ad_spend_change,
        sentiment_change=sentiment_change,
    )
    return await generate_war_room_report(request, include_agent_details=include_agents)


@router.post("/reports", response_model=WarRoomReportResponse, status_code=201)
async def create_warroom_report(data: WarRoomReportCreate) -> WarRoomReportResponse:
    """Create a new War Room report."""
    async with get_db() as db:
        report = WarRoomReport(**data.model_dump())
        db.add(report)
        await db.flush()
        await db.refresh(report)
        return WarRoomReportResponse.model_validate(report)


@router.get("/reports", response_model=list[WarRoomReportResponse])
async def list_warroom_reports(competitor_id: str | None = None) -> list[WarRoomReportResponse]:
    """List War Room reports, optionally filtered by competitor."""
    async with get_db() as db:
        query = select(WarRoomReport).order_by(WarRoomReport.created_at.desc())
        if competitor_id:
            query = query.where(WarRoomReport.competitor_id == competitor_id)
        result = await db.execute(query)
        reports = result.scalars().all()
        return [WarRoomReportResponse.model_validate(r) for r in reports]


@router.get("/reports/{report_id}", response_model=WarRoomReportResponse)
async def get_warroom_report(report_id: str) -> WarRoomReportResponse:
    """Get a War Room report by ID."""
    async with get_db() as db:
        result = await db.execute(
            select(WarRoomReport).where(WarRoomReport.id == report_id)
        )
        report = result.scalar_one_or_none()
        if not report:
            raise HTTPException(status_code=404, detail="War Room report not found")
        return WarRoomReportResponse.model_validate(report)
