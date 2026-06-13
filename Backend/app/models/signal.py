"""Signal model — an intelligence signal detected for a competitor.

Signal categories:
- Hiring (workforce expansion, new roles, team growth)
- Funding (funding rounds, investments, valuations)
- Marketing (ad spend, campaigns, brand activity)
- Product (product launches, feature updates, platform changes)
- Expansion (geographic expansion, new markets, office openings)
- Leadership (executive hires, departures, organizational changes)
- Sentiment (brand sentiment changes, customer feedback, reviews)
"""

from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid


class SignalCategory(str, enum.Enum):
    """Signal categories for competitive intelligence."""

    HIRING = "Hiring"
    FUNDING = "Funding"
    MARKETING = "Marketing"
    PRODUCT = "Product"
    EXPANSION = "Expansion"
    LEADERSHIP = "Leadership"
    SENTIMENT = "Sentiment"


class Signal(Base, TimestampMixin):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    competitor_id: Mapped[str] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    signal_type: Mapped[SignalCategory] = mapped_column(
        SAEnum(SignalCategory, name="signal_category", create_constraint=True),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(256), nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    competitor = relationship("Competitor", back_populates="signals")

    def __repr__(self) -> str:
        return f"<Signal {self.signal_type.value} (score={self.impact_score})>"
