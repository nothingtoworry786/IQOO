"""Competitive DNA schemas — patterns, analysis results, and behavioral signatures."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CompetitiveDNACreate(BaseModel):
    competitor_id: str
    pattern_type: str = Field(..., max_length=64)
    description: str
    embedding: str | None = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class CompetitiveDNAUpdate(BaseModel):
    pattern_type: str | None = Field(None, max_length=64)
    description: str | None = None
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)


class CompetitiveDNAResponse(BaseModel):
    id: str
    competitor_id: str
    pattern_type: str
    description: str
    embedding: str | None = None
    confidence_score: float
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class DNASimilarityResult(BaseModel):
    competitor_name: str
    competitor_id: str
    pattern_type: str
    description: str
    confidence_score: float
    similarity_score: float


class DNASignalCorrelation(BaseModel):
    """Correlation between a signal and a DNA pattern."""

    signal_id: str
    signal_title: str
    signal_type: str
    impact_score: float
    urgency_score: float
    matched_pattern_id: str
    matched_pattern_type: str
    match_reason: str
    correlation_score: float


class DNAAnalysisResult(BaseModel):
    """Full DNA analysis result for a competitor."""

    competitor_id: str
    competitor_name: str
    industry: str
    patterns: list[CompetitiveDNAResponse]
    signal_correlations: list[DNASignalCorrelation] = []
    behavioral_signature: str
    momentum_score: float
    pattern_coverage: float
    dominant_behaviors: list[dict] = []
    recommendations: list[str] = []
