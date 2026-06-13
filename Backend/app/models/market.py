"""Market and competitor relationship models — replaces Neo4j graph storage."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, gen_uuid


class Market(Base, TimestampMixin):
    __tablename__ = "markets"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    market_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    growth_rate: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Market {self.name}>"


class CompetitorMarket(Base, TimestampMixin):
    """Links competitors to markets they operate in — replaces OPERATES_IN Neo4j relationship."""

    __tablename__ = "competitor_markets"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    competitor_id: Mapped[str] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    market_id: Mapped[str] = mapped_column(
        ForeignKey("markets.id", ondelete="CASCADE"), nullable=False
    )
    market_share: Mapped[float | None] = mapped_column(Float, nullable=True)
    since_year: Mapped[int | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<CompetitorMarket {self.competitor_id} in {self.market_id}>"


class CompetitorRelationship(Base, TimestampMixin):
    """Stores competitive relationships — replaces COMPETES_WITH Neo4j relationship."""

    __tablename__ = "competitor_relationships"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    source_competitor_id: Mapped[str] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    target_competitor_id: Mapped[str] = mapped_column(
        ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False)
    intensity: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CompetitorRelationship {self.relationship_type}>"
