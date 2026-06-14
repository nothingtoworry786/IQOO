#!/usr/bin/env python3
"""
reset_db.py — Wipe ALL data from both database stacks (schema preserved).

Uses DATABASE_URL directly via SQLAlchemy — works for both SQLite and
Supabase PostgreSQL without needing separate SUPABASE_URL / SUPABASE_KEY.

Run from the Backend directory:
    python reset_db.py
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("reset")

# Union of all tables across both stacks — order matters (children first for FKs)
ALL_TABLES = [
    "agent_logs",
    "warroom_reports",
    "predictions",
    "competitive_dna",
    "dna_profiles",
    "signals",
    "discovery_jobs",
    "alerts",
    "competitor_profiles",
    "competitor_markets",
    "competitor_relationships",
    "markets",
    "competitors",
    "company_profiles",
    "users",
]


async def reset_via_sqlalchemy() -> int:
    """Delete all rows using the DATABASE_URL connection (SQLite or PostgreSQL)."""
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./marketwatch.db")

    # Auto-fix bare postgresql:// → postgresql+asyncpg://
    if db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    is_pg = "postgresql" in db_url
    log.info("  Database: %s", "PostgreSQL (Supabase)" if is_pg else "SQLite")

    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
    except ImportError:
        log.error("  sqlalchemy not installed — run: pip install sqlalchemy aiosqlite")
        return 0

    connect_args = {"statement_cache_size": 0} if is_pg else {}
    engine = create_async_engine(
        db_url,
        echo=False,
        pool_pre_ping=True,
        connect_args=connect_args,
    )

    total = 0

    if not is_pg:
        # SQLite: single transaction with FK checks off
        async with engine.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys = OFF"))
            for tbl in ALL_TABLES:
                try:
                    r = await conn.execute(text(f'DELETE FROM "{tbl}"'))
                    log.info("  %-32s %d rows deleted", tbl, r.rowcount)
                    total += r.rowcount
                except Exception as exc:
                    log.warning("  %-32s SKIP — %s", tbl, str(exc)[:80])
            await conn.execute(text("PRAGMA foreign_keys = ON"))
    else:
        # PostgreSQL: each table gets its own transaction so one missing table
        # doesn't put the connection into a failed state for everything else.
        for tbl in ALL_TABLES:
            try:
                async with engine.begin() as conn:
                    await conn.execute(text(f'TRUNCATE TABLE "{tbl}" CASCADE'))
                log.info("  %-32s TRUNCATED", tbl)
            except Exception as exc:
                err = str(exc)
                if "UndefinedTable" in err or "does not exist" in err.lower():
                    log.debug("  %-32s not in schema — skipped", tbl)
                else:
                    log.warning("  %-32s SKIP — %s", tbl, err[:120])

    await engine.dispose()
    return total


async def main() -> None:
    log.info("═══ MarketWatch Full Database Reset ═══\n")
    total = await reset_via_sqlalchemy()
    if total:
        log.info("\n  Total rows deleted: %d", total)
    log.info("\n═══ Reset complete — database is empty ═══")


if __name__ == "__main__":
    asyncio.run(main())
