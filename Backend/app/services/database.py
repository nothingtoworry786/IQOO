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
        # Migrate: add new columns to existing tables (SQLite ALTER TABLE is limited)
        _new_cols = [
            ("competitors", "is_active", "BOOLEAN DEFAULT 1"),
            ("predictions", "is_war_room_trigger", "BOOLEAN DEFAULT 0"),
        ]
        for table, col, definition in _new_cols:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {definition}"))
                logger.info("Migration: added %s.%s", table, col)
            except Exception:
                pass  # column already exists
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
