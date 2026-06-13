"""Competitive graph / relationship endpoints — using PostgreSQL tables."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select, or_

from app.models.competitor import Competitor
from app.models.market import CompetitorRelationship, CompetitorMarket, Market
from app.models.competitive_dna import CompetitiveDNA
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["Graph"])


@router.get("/competitive/{company_name}", response_model=dict)
async def get_competitive_graph(company_name: str) -> dict:
    """Get the competitive relationship graph for a company from PostgreSQL."""
    async with get_db() as db:
        comp_result = await db.execute(
            select(Competitor).where(Competitor.name == company_name)
        )
        competitor = comp_result.scalar_one_or_none()
        if not competitor:
            return {"nodes": [], "relationships": [], "company": company_name}

        nodes = [{"id": competitor.id, "name": competitor.name, "type": "Company",
                   "industry": competitor.industry, "market_scope": competitor.market_scope}]

        rels_result = await db.execute(
            select(CompetitorRelationship).where(
                or_(
                    CompetitorRelationship.source_competitor_id == competitor.id,
                    CompetitorRelationship.target_competitor_id == competitor.id,
                )
            )
        )
        relationships_data = rels_result.scalars().all()

        related_ids = set()
        for rel in relationships_data:
            if rel.source_competitor_id != competitor.id:
                related_ids.add(rel.source_competitor_id)
            if rel.target_competitor_id != competitor.id:
                related_ids.add(rel.target_competitor_id)

        if related_ids:
            related_result = await db.execute(
                select(Competitor).where(Competitor.id.in_(related_ids))
            )
            for c in related_result.scalars().all():
                nodes.append({"id": c.id, "name": c.name, "type": "Company", "industry": c.industry})

        return {
            "nodes": nodes,
            "relationships": [
                {"source": r.source_competitor_id, "target": r.target_competitor_id,
                 "type": r.relationship_type, "intensity": r.intensity}
                for r in relationships_data
            ],
            "company": company_name,
        }


@router.get("/nodes", response_model=list[dict])
async def list_graph_nodes() -> list[dict]:
    async with get_db() as db:
        result = await db.execute(select(Competitor).order_by(Competitor.name))
        return [
            {"name": c.name, "type": "Company", "industry": c.industry, "id": c.id}
            for c in result.scalars().all()
        ]


@router.get("/relationships", response_model=list[dict])
async def list_graph_relationships() -> list[dict]:
    async with get_db() as db:
        result = await db.execute(
            select(CompetitorRelationship).order_by(CompetitorRelationship.relationship_type)
        )
        rels = result.scalars().all()
        output = []
        for r in rels:
            src = await db.execute(select(Competitor).where(Competitor.id == r.source_competitor_id))
            tgt = await db.execute(select(Competitor).where(Competitor.id == r.target_competitor_id))
            src_name = src.scalar_one_or_none()
            tgt_name = tgt.scalar_one_or_none()
            output.append({
                "source": src_name.name if src_name else r.source_competitor_id,
                "target": tgt_name.name if tgt_name else r.target_competitor_id,
                "type": r.relationship_type,
                "intensity": r.intensity,
            })
        return output


@router.get("/dna/{competitor_name}", response_model=dict)
async def get_competitive_dna(competitor_name: str) -> dict:
    """Get the competitive DNA profile for a company from PostgreSQL."""
    async with get_db() as db:
        comp_result = await db.execute(select(Competitor).where(Competitor.name == competitor_name))
        competitor = comp_result.scalar_one_or_none()
        if not competitor:
            raise HTTPException(status_code=404, detail=f"No DNA profile found for '{competitor_name}'")

        dna_result = await db.execute(
            select(CompetitiveDNA).where(CompetitiveDNA.competitor_id == competitor.id)
            .order_by(CompetitiveDNA.confidence_score.desc())
        )
        patterns = dna_result.scalars().all()

        signals = list(competitor.signals) if competitor.signals else []
        total_impact = sum(s.impact_score for s in signals) if signals else 0
        momentum = min(100, (total_impact / max(len(signals), 1)) * 5) if signals else 0

        return {
            "company": competitor_name,
            "industry": competitor.industry,
            "patterns": [
                {"pattern": p.description, "pattern_type": p.pattern_type,
                 "confidence": p.confidence_score}
                for p in patterns
            ],
            "behavioral_signature": f"Analyzing {len(patterns)} known patterns for {competitor_name}",
            "momentum_score": round(momentum, 1),
            "signal_count": len(signals),
        }
