"""Prediction model — an AI-generated prediction about a competitor."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid


class Prediction(Base, TimestampMixin):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    competitor_id: Mapped[str] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    prediction: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    threat_level: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)

    competitor = relationship("Competitor", back_populates="predictions")

    def __repr__(self) -> str:
        return f"<Prediction (confidence={self.confidence}, threat={self.threat_level})>"
