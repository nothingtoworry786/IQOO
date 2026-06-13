"""AgentLog model — records every autonomous decision made by an agent."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, gen_uuid


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    competitor_id: Mapped[str | None] = mapped_column(
        ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True
    )
    agent_name: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(512), nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_agent_logs_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AgentLog {self.agent_name}: {self.action[:60]}>"
