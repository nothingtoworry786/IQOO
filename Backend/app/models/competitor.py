"""Competitor model — simplified without user_id, added market_scope."""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid


class Competitor(Base, TimestampMixin):
    __tablename__ = "competitors"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    industry: Mapped[str] = mapped_column(String(128), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    market_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("1"))

    # Relationships
    signals = relationship("Signal", back_populates="competitor", lazy="selectin")
    predictions = relationship("Prediction", back_populates="competitor", lazy="selectin")
    warroom_reports = relationship("WarRoomReport", back_populates="competitor", lazy="selectin")
    dna_profiles = relationship("CompetitiveDNA", back_populates="competitor", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Competitor {self.name}>"
