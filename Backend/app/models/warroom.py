"""WarRoomReport model — strategic intelligence report for a competitor."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid


class WarRoomReport(Base, TimestampMixin):
    __tablename__ = "warroom_reports"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    competitor_id: Mapped[str] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    threat_summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    competitor = relationship("Competitor", back_populates="warroom_reports")

    def __repr__(self) -> str:
        return f"<WarRoomReport (impact={self.impact_score})>"
