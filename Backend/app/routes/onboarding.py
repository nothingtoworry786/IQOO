"""Onboarding routes — fire-and-poll discovery pipeline."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.supabase_client import db_insert, db_select_one
from app.agents.market_discovery_agent import run_discovery_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding v2"])

# Keeps strong references to running background tasks so they aren't garbage-collected.
_bg_tasks: set[asyncio.Task] = set()


class DiscoverRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    company_name: str = Field(..., min_length=1, max_length=256)
    website: str | None = Field(None, max_length=512)
    description: str = Field("", max_length=2000)


class DiscoverResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post(
    "/discover",
    response_model=DiscoverResponse,
    summary="Start market discovery (returns job_id immediately)",
)
async def start_discovery(data: DiscoverRequest) -> DiscoverResponse:
    """
    Kick off the full 7-step competitive intelligence pipeline in the background.
    Returns a job_id immediately — poll GET /api/onboarding/discover/status/{job_id}
    to track progress (0-100%) and retrieve results when status='completed'.
    """
    job = await db_insert(
        "discovery_jobs",
        {
            "user_id": data.user_id,
            "status": "pending",
            "stage": "Initializing...",
            "progress": 0,
        },
    )

    job_id = job.get("id")
    if not job_id:
        raise HTTPException(status_code=500, detail="Failed to create discovery job.")

    # Keep a strong reference to prevent GC before the task finishes.
    # The callback removes the reference on completion and logs any crash.
    task = asyncio.create_task(
        run_discovery_pipeline(
            job_id=job_id,
            user_id=data.user_id,
            company_name=data.company_name,
            website=data.website,
            description=data.description,
        )
    )
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
    task.add_done_callback(
        lambda t: logger.error("Discovery pipeline unhandled crash: %s", t.exception())
        if not t.cancelled() and t.exception()
        else None
    )

    logger.info("Discovery job %s started for user=%s (%s)", job_id, data.user_id, data.company_name)

    return DiscoverResponse(
        job_id=job_id,
        status="pending",
        message="Discovery pipeline started. Poll /status/{job_id} for progress.",
    )


@router.get(
    "/discover/status/{job_id}",
    summary="Poll discovery job status",
)
async def get_discovery_status(job_id: str) -> dict:
    """
    Returns current job status. Frontend should poll every 2-3 seconds.

    status values: pending | running | completed | failed
    progress: 0-100 (int)
    stage: human-readable current step description
    result: populated when status=completed (full competitor + signal data)
    error: populated when status=failed
    """
    job = await db_select_one("discovery_jobs", {"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job
