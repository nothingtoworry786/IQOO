"""Competitive DNA model — stores competitor behaviour patterns with vector embeddings.

Uses pgvector for semantic similarity search (PostgreSQL) or text-based matching (SQLite).
"""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid


class CompetitiveDNA(Base, TimestampMixin):
    __tablename__ = "competitive_dna"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    competitor_id: Mapped[str] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    pattern_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    competitor = relationship("Competitor", back_populates="dna_profiles")

    def __repr__(self) -> str:
        return f"<CompetitiveDNA {self.pattern_type} ({self.confidence_score})>"
