"""Competitive DNA service — pattern matching, signal correlation, and behavioral analysis.

Uses the competitive_dna table with text-based pattern matching (SQLite dev)
and supports pgvector semantic search (PostgreSQL production).
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from sqlalchemy import select, text

from app.models.competitive_dna import CompetitiveDNA
from app.models.competitor import Competitor
from app.models.signal import Signal, SignalCategory
from app.services.database import get_db
from app.schemas.competitive_dna import (
    CompetitiveDNAResponse,
    DNASimilarityResult,
    DNASignalCorrelation,
    DNAAnalysisResult,
)

logger = logging.getLogger(__name__)

# ── Pattern type mappings from signal categories ──

SIGNAL_TO_PATTERN_MAP: dict[str, list[str]] = {
    "Hiring": ["hiring_spike", "team_growth", "talent_acquisition"],
    "Funding": ["funding_round", "investment_pattern", "valuation_shift"],
    "Marketing": ["ad_spend_increase", "discount_campaign", "brand_push"],
    "Product": ["product_launch", "feature_release", "platform_update"],
    "Expansion": ["city_expansion", "market_entry", "geo_diversification"],
    "Leadership": ["executive_hire", "org_restructure", "leadership_change"],
    "Sentiment": ["sentiment_shift", "reputation_change", "customer_signal"],
}


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


async def list_patterns(
    competitor_id: str | None = None,
    pattern_type: str | None = None,
    limit: int = 50,
) -> list[CompetitiveDNAResponse]:
    """List DNA patterns with optional filtering."""
    async with get_db() as db:
        query = select(CompetitiveDNA).order_by(CompetitiveDNA.confidence_score.desc())
        if competitor_id:
            query = query.where(CompetitiveDNA.competitor_id == competitor_id)
        if pattern_type:
            query = query.where(CompetitiveDNA.pattern_type == pattern_type)
        query = query.limit(limit)
        result = await db.execute(query)
        return [CompetitiveDNAResponse.model_validate(p) for p in result.scalars().all()]


async def get_pattern(pattern_id: str) -> CompetitiveDNAResponse | None:
    """Get a single DNA pattern by ID."""
    async with get_db() as db:
        result = await db.execute(select(CompetitiveDNA).where(CompetitiveDNA.id == pattern_id))
        pattern = result.scalar_one_or_none()
        if pattern:
            return CompetitiveDNAResponse.model_validate(pattern)
        return None


async def create_pattern(data: dict) -> CompetitiveDNAResponse:
    """Create a new DNA pattern."""
    async with get_db() as db:
        pattern = CompetitiveDNA(**data)
        db.add(pattern)
        await db.flush()
        await db.refresh(pattern)
        return CompetitiveDNAResponse.model_validate(pattern)


async def update_pattern(pattern_id: str, data: dict) -> CompetitiveDNAResponse | None:
    """Update an existing DNA pattern."""
    async with get_db() as db:
        result = await db.execute(select(CompetitiveDNA).where(CompetitiveDNA.id == pattern_id))
        pattern = result.scalar_one_or_none()
        if not pattern:
            return None
        for field, value in data.items():
            if value is not None:
                setattr(pattern, field, value)
        await db.flush()
        await db.refresh(pattern)
        return CompetitiveDNAResponse.model_validate(pattern)


async def delete_pattern(pattern_id: str) -> bool:
    """Delete a DNA pattern by ID."""
    async with get_db() as db:
        result = await db.execute(select(CompetitiveDNA).where(CompetitiveDNA.id == pattern_id))
        pattern = result.scalar_one_or_none()
        if not pattern:
            return False
        await db.delete(pattern)
        return True


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
            .where(
                CompetitiveDNA.pattern_type.in_(
                    SIGNAL_TO_PATTERN_MAP.get(signal_type, [signal_type.lower()])
                )
            )
            .order_by(CompetitiveDNA.confidence_score.desc())
            .limit(top_k)
        )
        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "pattern_id": row.CompetitiveDNA.id,
                "competitor_name": row.competitor_name,
                "competitor_id": row.CompetitiveDNA.competitor_id,
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
                "competitor_id": row.competitor_id,
                "pattern_type": row.pattern_type,
                "description": row.description,
                "confidence_score": row.confidence_score,
            }
            for row in rows
        ]


# ── DNA Analysis Engine ──


async def analyze_competitor_dna(competitor_id: str) -> DNAAnalysisResult | None:
    """Run full DNA analysis on a competitor — correlate signals with patterns."""
    async with get_db() as db:
        # Get competitor
        comp_result = await db.execute(select(Competitor).where(Competitor.id == competitor_id))
        competitor = comp_result.scalar_one_or_none()
        if not competitor:
            return None

        # Get competitor signals
        signals_result = await db.execute(
            select(Signal)
            .where(Signal.competitor_id == competitor_id)
            .order_by(Signal.created_at.desc())
        )
        signals = signals_result.scalars().all()

        # Get competitor DNA patterns
        patterns_result = await db.execute(
            select(CompetitiveDNA)
            .where(CompetitiveDNA.competitor_id == competitor_id)
            .order_by(CompetitiveDNA.confidence_score.desc())
        )
        patterns = patterns_result.scalars().all()

        # Correlate signals with DNA patterns
        correlations: list[DNASignalCorrelation] = []
        for signal in signals:
            matching_patterns = SIGNAL_TO_PATTERN_MAP.get(signal.signal_type.value, [])
            for pattern in patterns:
                if pattern.pattern_type in matching_patterns:
                    # Calculate correlation based on impact alignment
                    impact_alignment = 1.0 - abs(signal.impact_score / 10 - pattern.confidence_score)
                    correlation_score = min(1.0, (impact_alignment * 0.6) + (pattern.confidence_score * 0.4))
                    correlations.append(DNASignalCorrelation(
                        signal_id=signal.id,
                        signal_title=signal.title,
                        signal_type=signal.signal_type.value,
                        impact_score=signal.impact_score,
                        urgency_score=signal.urgency_score,
                        matched_pattern_id=pattern.id,
                        matched_pattern_type=pattern.pattern_type,
                        match_reason=f"Signal type '{signal.signal_type.value}' matches pattern '{pattern.pattern_type}'",
                        correlation_score=round(correlation_score, 3),
                    ))

        # Generate behavioral signature
        pattern_count = len(patterns)
        signal_count = len(signals)
        pattern_coverage = min(1.0, (pattern_count / max(signal_count, 1)) * 2) if signal_count > 0 else 0

        # Calculate momentum
        total_impact = sum(s.impact_score for s in signals) if signals else 0
        momentum = min(100, (total_impact / max(len(signals), 1)) * 5) if signals else 0

        # Determine dominant behaviors
        dominant_behaviors = _get_dominant_behaviors(patterns, correlations)

        # Generate recommendations
        recommendations = _generate_recommendations(patterns, dominant_behaviors, competitor.name)

        return DNAAnalysisResult(
            competitor_id=competitor.id,
            competitor_name=competitor.name,
            industry=competitor.industry or "Unknown",
            patterns=[CompetitiveDNAResponse.model_validate(p) for p in patterns],
            signal_correlations=correlations,
            behavioral_signature=_build_signature(competitor.name, patterns, dominant_behaviors),
            momentum_score=round(momentum, 1),
            pattern_coverage=round(pattern_coverage, 3),
            dominant_behaviors=dominant_behaviors,
            recommendations=recommendations,
        )


def _build_signature(name: str, patterns: list[CompetitiveDNA], dominant: list[dict]) -> str:
    """Generate a human-readable behavioral signature for a competitor."""
    if not patterns:
        return f"No behavioral patterns detected for {name} yet."

    top_patterns = sorted(patterns, key=lambda p: p.confidence_score, reverse=True)[:3]
    pattern_desc = "; ".join(
        f"{p.pattern_type} (confidence: {p.confidence_score:.0%})" for p in top_patterns
    )
    return (
        f"{name} exhibits {len(patterns)} behavioral patterns. "
        f"Dominant patterns: {pattern_desc}. "
        f"{'Aggressive expansion strategy detected.' if any('expansion' in d.get('pattern','') for d in dominant) else ''}"
        f"{'Strong hiring and talent acquisition focus.' if any('hiring' in d.get('pattern','') for d in dominant) else ''}"
    )


def _get_dominant_behaviors(
    patterns: list[CompetitiveDNA],
    correlations: list[DNASignalCorrelation],
) -> list[dict]:
    """Extract dominant behavioral patterns from DNA data."""
    pattern_counts: dict[str, int] = Counter()
    pattern_confidence: dict[str, float] = {}

    for p in patterns:
        pattern_counts[p.pattern_type] += 1
        pattern_confidence[p.pattern_type] = p.confidence_score

    for c in correlations:
        if c.matched_pattern_type:
            pattern_counts[c.matched_pattern_type] += 1

    if not pattern_counts:
        return []

    sorted_patterns = sorted(
        pattern_counts.items(),
        key=lambda x: (x[1], pattern_confidence.get(x[0], 0)),
        reverse=True,
    )

    return [
        {
            "pattern": pt,
            "frequency": count,
            "confidence": round(pattern_confidence.get(pt, 0), 3),
            "intensity": _get_intensity_label(pattern_confidence.get(pt, 0)),
        }
        for pt, count in sorted_patterns[:5]
    ]


def _get_intensity_label(confidence: float) -> str:
    if confidence >= 0.8:
        return "Very High"
    if confidence >= 0.6:
        return "High"
    if confidence >= 0.4:
        return "Medium"
    return "Low"


def _generate_recommendations(
    patterns: list[CompetitiveDNA],
    dominant: list[dict],
    competitor_name: str,
) -> list[str]:
    """Generate strategic recommendations based on detected DNA patterns."""
    recs = []
    pattern_types = {d["pattern"] for d in dominant}

    if "hiring_spike" in pattern_types or "team_growth" in pattern_types:
        recs.append(f"Monitor {competitor_name}'s hiring in key roles — hiring spikes often precede market expansion.")
    if "funding_round" in pattern_types:
        recs.append(f"{competitor_name} has raised significant capital. Expect aggressive moves in the next 6 months.")
    if "ad_spend_increase" in pattern_types or "discount_campaign" in pattern_types:
        recs.append(f"Marketing intensity is high for {competitor_name}. Consider defensive brand investments.")
    if "city_expansion" in pattern_types or "market_entry" in pattern_types:
        recs.append(f"{competitor_name} is expanding geographically. Prioritize retention in existing strongholds.")
    if "product_launch" in pattern_types or "feature_release" in pattern_types:
        recs.append(f"Product innovation cycle is active for {competitor_name}. Accelerate your own roadmap.")
    if not recs:
        recs.append(f"Continue monitoring {competitor_name}'s signals for emerging behavioral patterns.")
        recs.append("Consider adding more signals to improve DNA pattern detection accuracy.")
        recs.append("Set up alerts for signal volume changes to detect new patterns early.")

    return recs


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
