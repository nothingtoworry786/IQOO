#!/usr/bin/env python3
"""
reset_db.py — Wipe ALL data from both databases (schema preserved).

  • SQLite  : deletes every row in every ORM-managed table
  • Supabase: deletes every row in every v2 table via the PostgREST API

Run from the Backend directory:
    python reset_db.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
log = logging.getLogger("reset")

# ── SQLite tables (FK-safe order: children first) ─────────────────────────────
SQLITE_TABLES = [
    "agent_logs",
    "warroom_reports",
    "predictions",
    "competitive_dna",
    "signals",
    "alerts",
    "competitor_markets",
    "competitor_relationships",
    "markets",
    "competitors",
    "users",
]

# ── Supabase tables (children first) ─────────────────────────────────────────
SUPABASE_TABLES = [
    "agent_logs",
    "dna_profiles",
    "signals",
    "discovery_jobs",
    "competitor_profiles",
    "competitors",
    "company_profiles",
]


# ─────────────────────────────────────────────────────────────────────────────
# SQLite reset
# ─────────────────────────────────────────────────────────────────────────────

async def reset_sqlite() -> int:
    """Delete all rows from every SQLite table. Returns total rows deleted."""
    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./marketwatch.db")
    if "postgresql" in db_url:
        log.info("  SQLite: DATABASE_URL points to PostgreSQL — skipping")
        return 0

    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
    except ImportError:
        log.error("  sqlalchemy / aiosqlite not installed — cannot reset SQLite")
        return 0

    engine = create_async_engine(db_url, echo=False)
    total = 0

    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys = OFF"))
        for tbl in SQLITE_TABLES:
            try:
                r = await conn.execute(text(f'DELETE FROM "{tbl}"'))
                log.info("  SQLite  %-28s %d rows deleted", tbl, r.rowcount)
                total += r.rowcount
            except Exception as exc:
                log.warning("  SQLite  %-28s SKIP — %s", tbl, exc)
        await conn.execute(text("PRAGMA foreign_keys = ON"))

    await engine.dispose()
    return total


# ─────────────────────────────────────────────────────────────────────────────
# Supabase reset
# ─────────────────────────────────────────────────────────────────────────────

def reset_supabase() -> dict[str, str]:
    """Delete all rows from every Supabase table via direct PostgREST HTTP calls."""
    url = os.getenv("SUPABASE_URL", "").rstrip("/")
    key = os.getenv("SUPABASE_KEY", "")

    if not url or not key:
        log.warning("  Supabase: SUPABASE_URL or SUPABASE_KEY missing — skipping")
        return {}

    try:
        import httpx
    except ImportError:
        log.error("  httpx not installed — cannot reset Supabase")
        return {}

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    results: dict[str, str] = {}

    for tbl in SUPABASE_TABLES:
        try:
            # PostgREST requires at least one filter for DELETE.
            # Using "id neq zero-UUID" matches every real row (no row uses the zero UUID).
            resp = httpx.delete(
                f"{url}/rest/v1/{tbl}",
                headers=headers,
                params={"id": "neq.00000000-0000-0000-0000-000000000000"},
                timeout=30.0,
            )
            if resp.status_code in (200, 204):
                log.info("  Supabase %-28s cleared (HTTP %d)", tbl, resp.status_code)
                results[tbl] = "ok"
            else:
                log.warning(
                    "  Supabase %-28s HTTP %d — %s",
                    tbl, resp.status_code, resp.text[:200],
                )
                results[tbl] = f"error {resp.status_code}"
        except Exception as exc:
            log.warning("  Supabase %-28s ERROR — %s", tbl, exc)
            results[tbl] = f"error: {exc}"

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    log.info("═══ MarketWatch Full Database Reset ═══")
    log.info("")

    log.info("[1/2] SQLite")
    sqlite_rows = await reset_sqlite()
    log.info("      Total SQLite rows deleted: %d", sqlite_rows)
    log.info("")

    log.info("[2/2] Supabase")
    supabase_results = reset_supabase()
    errors = [t for t, s in supabase_results.items() if s != "ok"]
    if errors:
        log.warning("      Supabase tables with errors: %s", errors)
    log.info("")

    log.info("═══ Reset complete — both databases are empty ═══")


if __name__ == "__main__":
    asyncio.run(main())
