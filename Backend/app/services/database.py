"""Database service — manages SQLAlchemy async engine and session lifecycle."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.models.base import Base

# All models must be imported here so their tables are registered with
# Base.metadata before create_all() runs. Adding a new model? Add it here too.
import app.models.competitor       # noqa: F401, E402
import app.models.signal           # noqa: F401, E402
import app.models.prediction       # noqa: F401, E402
import app.models.warroom          # noqa: F401, E402
import app.models.alert            # noqa: F401, E402
import app.models.competitive_dna  # noqa: F401, E402
import app.models.market           # noqa: F401, E402
import app.models.agent_log        # noqa: F401, E402

logger = logging.getLogger(__name__)

_is_postgres = "postgresql" in settings.DATABASE_URL

# Disable prepared statement caching for Supabase PgBouncer (transaction mode)
_connect_args = {}
if _is_postgres:
    _connect_args = {"statement_cache_size": 0}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "DEBUG",
    pool_pre_ping=True,
    pool_size=5 if _is_postgres else 1,
    max_overflow=10 if _is_postgres else 0,
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        if _is_postgres:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")
        await conn.run_sync(Base.metadata.create_all)
        # ── Remove pre-seeded demo data (IDs starting with 'comp-') ───────────
        await conn.execute(text("DELETE FROM competitors WHERE id LIKE 'comp-%'"))

        if _is_postgres:
            # ── Column migrations (PG 9.6+ IF NOT EXISTS) ──────────────────────
            _pg_cols = [
                "ALTER TABLE competitors  ADD COLUMN IF NOT EXISTS is_active           BOOLEAN NOT NULL DEFAULT TRUE",
                "ALTER TABLE predictions  ADD COLUMN IF NOT EXISTS is_war_room_trigger  BOOLEAN NOT NULL DEFAULT FALSE",
            ]
            for stmt in _pg_cols:
                try:
                    await conn.execute(text(stmt))
                except Exception as exc:
                    logger.warning("PG column migration skipped: %s", exc)

        else:
            # SQLite: no IF NOT EXISTS support — swallow duplicate-column errors
            _sqlite_cols = [
                ("competitors", "is_active", "BOOLEAN DEFAULT 1"),
                ("predictions", "is_war_room_trigger", "BOOLEAN DEFAULT 0"),
            ]
            for table, col, definition in _sqlite_cols:
                try:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {definition}"))
                    logger.info("Migration: added %s.%s", table, col)
                except Exception:
                    pass  # column already exists — expected on second run
    logger.info("Database tables initialised")


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database engine disposed")


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
