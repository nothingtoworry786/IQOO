"""Competitive DNA analysis API endpoints — patterns, correlation, and behavioral analysis.

IMPORTANT: specific literal-segment routes (/similar/*, /analyze/*) MUST be declared
before the parameterized /{pattern_id} route, otherwise FastAPI matches the literal
segments as pattern IDs and those routes become unreachable.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.models.competitive_dna import CompetitiveDNA
from app.models.competitor import Competitor
from app.schemas.competitive_dna import (
    CompetitiveDNACreate,
    CompetitiveDNAUpdate,
    CompetitiveDNAResponse,
    DNAAnalysisResult,
    DNASimilarityResult,
)
from app.services.competitive_dna import (
    list_patterns,
    get_pattern,
    create_pattern,
    update_pattern,
    delete_pattern,
    find_similar_patterns,
    analyze_competitor_dna,
)
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dna", tags=["DNA"])


# ── List (no path param) ──────────────────────────────────────────────────────

@router.get("/", response_model=list[CompetitiveDNAResponse])
async def list_dna_patterns(
    competitor_id: str | None = None,
    pattern_type: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> list[CompetitiveDNAResponse]:
    """List all competitive DNA patterns with optional filtering."""
    return await list_patterns(
        competitor_id=competitor_id,
        pattern_type=pattern_type,
        limit=limit,
    )


# ── Analysis endpoints — MUST come before /{pattern_id} ──────────────────────

@router.get("/similar/{signal_type}", response_model=list[DNASimilarityResult])
async def find_similar_dna_patterns(
    signal_type: str,
    impact_score: float = Query(5.0, ge=0.0, le=10.0),
    top_k: int = Query(5, ge=1, le=20),
) -> list[DNASimilarityResult]:
    """Find DNA patterns similar to a given signal type and impact."""
    results = await find_similar_patterns(
        signal_type=signal_type,
        impact_score=impact_score,
        top_k=top_k,
    )
    return [DNASimilarityResult(**r) for r in results]


@router.get("/analyze/by-name/{competitor_name}", response_model=DNAAnalysisResult)
async def analyze_competitor_dna_by_name(
    competitor_name: str,
) -> DNAAnalysisResult:
    """Run full DNA analysis on a competitor by name."""
    async with get_db() as db:
        result = await db.execute(
            select(Competitor).where(Competitor.name == competitor_name)
        )
        competitor = result.scalar_one_or_none()
        if not competitor:
            raise HTTPException(status_code=404, detail=f"Competitor '{competitor_name}' not found")

    result = await analyze_competitor_dna(competitor.id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis failed")
    return result


@router.get("/analyze/{competitor_id}", response_model=DNAAnalysisResult)
async def analyze_competitor_dna_patterns(
    competitor_id: str,
) -> DNAAnalysisResult:
    """Run full DNA analysis on a competitor — correlate signals with patterns."""
    result = await analyze_competitor_dna(competitor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return result


# ── CRUD — /{pattern_id} AFTER all literal-segment routes ────────────────────

@router.get("/{pattern_id}", response_model=CompetitiveDNAResponse)
async def get_dna_pattern(pattern_id: str) -> CompetitiveDNAResponse:
    """Get a specific DNA pattern by ID."""
    pattern = await get_pattern(pattern_id)
    if not pattern:
        raise HTTPException(status_code=404, detail="DNA pattern not found")
    return pattern


@router.post("/", response_model=CompetitiveDNAResponse, status_code=status.HTTP_201_CREATED)
async def create_dna_pattern(data: CompetitiveDNACreate) -> CompetitiveDNAResponse:
    """Create a new DNA pattern."""
    async with get_db() as db:
        result = await db.execute(select(Competitor).where(Competitor.id == data.competitor_id))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Competitor not found")

    return await create_pattern(data.model_dump())


@router.put("/{pattern_id}", response_model=CompetitiveDNAResponse)
async def update_dna_pattern(
    pattern_id: str,
    data: CompetitiveDNAUpdate,
) -> CompetitiveDNAResponse:
    """Update an existing DNA pattern."""
    pattern = await update_pattern(pattern_id, data.model_dump(exclude_unset=True))
    if not pattern:
        raise HTTPException(status_code=404, detail="DNA pattern not found")
    return pattern


@router.delete("/{pattern_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dna_pattern(pattern_id: str) -> None:
    """Delete a DNA pattern."""
    deleted = await delete_pattern(pattern_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="DNA pattern not found")
