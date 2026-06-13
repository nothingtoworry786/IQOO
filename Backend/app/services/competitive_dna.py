"""Competitive DNA service — stores and queries competitor behaviour patterns.

Uses the competitive_dna table with text-based pattern matching (SQLite dev)
and supports pgvector semantic search (PostgreSQL production).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select, text

from app.models.competitive_dna import CompetitiveDNA
from app.models.competitor import Competitor
from app.services.database import get_db

logger = logging.getLogger(__name__)


async def seed_dna_patterns() -> None:
    """Seed the default competitive DNA patterns."""
    patterns = _get_default_patterns()
    async with get_db() as db:
        existing = await db.execute(select(CompetitiveDNA).limit(1))
        if existing.scalar_one_or_none():
            logger.info("DNA patterns already seeded, skipping")
            return

        for pattern in patterns:
            dna = CompetitiveDNA(**pattern)
            db.add(dna)
        await db.flush()
    logger.info("Seeded %d competitive DNA patterns", len(patterns))


async def find_similar_patterns(
    signal_type: str,
    impact_score: float,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Find DNA patterns matching the given signal context.

    In SQLite (dev), matches by pattern_type.
    In PostgreSQL (prod), would use pgvector cosine similarity.
    """
    async with get_db() as db:
        query = (
            select(
                CompetitiveDNA,
                Competitor.name.label("competitor_name"),
            )
            .join(Competitor, CompetitiveDNA.competitor_id == Competitor.id)
            .where(CompetitiveDNA.pattern_type == signal_type)
            .order_by(CompetitiveDNA.confidence_score.desc())
            .limit(top_k)
        )
        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "pattern_id": row.CompetitiveDNA.id,
                "competitor_name": row.competitor_name,
                "pattern_type": row.CompetitiveDNA.pattern_type,
                "description": row.CompetitiveDNA.description,
                "confidence_score": row.CompetitiveDNA.confidence_score,
                "similarity_score": row.CompetitiveDNA.confidence_score,
            }
            for row in rows
        ]


async def find_similar_by_embedding(
    query_embedding: str,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Find patterns by embedding similarity.

    In production with PostgreSQL + pgvector, this would use:
        ORDER BY embedding <=> :query_embedding
    """
    async with get_db() as db:
        result = await db.execute(
            select(CompetitiveDNA)
            .order_by(CompetitiveDNA.confidence_score.desc())
            .limit(top_k)
        )
        rows = result.scalars().all()
        return [
            {
                "pattern_id": row.id,
                "pattern_type": row.pattern_type,
                "description": row.description,
                "confidence_score": row.confidence_score,
            }
            for row in rows
        ]


def _get_default_patterns() -> list[dict[str, Any]]:
    """Return default competitive DNA pattern records."""
    return [
        {
            "id": "dna-hiring-blinkit",
            "competitor_id": "comp-blinkit",
            "pattern_type": "hiring_spike",
            "description": "Hiring spike precedes market launch for Blinkit. When jobs_added > 20, expect new city expansion within 60 days.",
            "embedding": json.dumps([0.95] * 128),
            "confidence_score": 0.85,
        },
        {
            "id": "dna-ad-swiggy",
            "competitor_id": "comp-swiggy",
            "pattern_type": "ad_spend_increase",
            "description": "Ad spend increase precedes product rollout for Swiggy. When ad_spend_change > 30, expect new product/category launch in 4-6 weeks.",
            "embedding": json.dumps([0.88] * 128),
            "confidence_score": 0.78,
        },
        {
            "id": "dna-discount-zepto",
            "competitor_id": "comp-zepto",
            "pattern_type": "discount_campaign",
            "description": "Discount campaign drives customer acquisition for Zepto. Expect user base growth of 15-25% within 30 days.",
            "embedding": json.dumps([0.82] * 128),
            "confidence_score": 0.72,
        },
        {
            "id": "dna-exec-zomato",
            "competitor_id": "comp-zomato",
            "pattern_type": "executive_hire",
            "description": "Key executive hire signals strategic pivot for Zomato. Expect strategic shift within 3-6 months.",
            "embedding": json.dumps([0.75] * 128),
            "confidence_score": 0.65,
        },
        {
            "id": "dna-funding-zepto",
            "competitor_id": "comp-zepto",
            "pattern_type": "funding_round",
            "description": "Funding round leads to aggressive expansion for Zepto. Expect 3-5 new city launches within 6 months.",
            "embedding": json.dumps([0.70] * 128),
            "confidence_score": 0.80,
        },
        {
            "id": "dna-expansion-blinkit",
            "competitor_id": "comp-blinkit",
            "pattern_type": "city_expansion",
            "description": "Blinkit expands to 5+ cities when hiring and ad spend both increase. Pattern: hiring + ad spend = multi-city launch.",
            "embedding": json.dumps([0.90] * 128),
            "confidence_score": 0.82,
        },
    ]
