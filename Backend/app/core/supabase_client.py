"""Supabase client + async DB helper layer.

All supabase-py calls are synchronous; they are wrapped in asyncio.to_thread()
so FastAPI's async handlers never block the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_client = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_supabase():
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in .env to use Supabase features."
            )
        from supabase import create_client
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialised (%s...)", settings.SUPABASE_URL[:40])
    return _client


# ── Core helpers ─────────────────────────────────────────────────────────────

async def db_insert(table: str, data: dict[str, Any]) -> dict[str, Any]:
    client = get_supabase()
    result = await asyncio.to_thread(
        lambda: client.table(table).insert(data).execute()
    )
    return result.data[0] if result.data else {}


async def db_select(
    table: str,
    filters: dict[str, Any] | None = None,
    limit: int | None = None,
    order_by: str | None = None,
    order_desc: bool = False,
    select_cols: str = "*",
) -> list[dict[str, Any]]:
    client = get_supabase()

    def _run():
        q = client.table(table).select(select_cols)
        if filters:
            for key, val in filters.items():
                q = q.eq(key, val)
        if order_by:
            q = q.order(order_by, desc=order_desc)
        if limit:
            q = q.limit(limit)
        return q.execute()

    result = await asyncio.to_thread(_run)
    return result.data or []


async def db_select_one(
    table: str,
    filters: dict[str, Any],
    select_cols: str = "*",
) -> dict[str, Any] | None:
    rows = await db_select(table, filters, limit=1, select_cols=select_cols)
    return rows[0] if rows else None


async def db_update(
    table: str,
    filters: dict[str, Any],
    data: dict[str, Any],
) -> dict[str, Any]:
    client = get_supabase()

    def _run():
        q = client.table(table).update(data)
        for key, val in filters.items():
            q = q.eq(key, val)
        return q.execute()

    result = await asyncio.to_thread(_run)
    return result.data[0] if result.data else {}


async def db_upsert(
    table: str,
    data: dict[str, Any],
    on_conflict: str,
    ignore_duplicates: bool = False,
) -> dict[str, Any]:
    client = get_supabase()
    result = await asyncio.to_thread(
        lambda: client.table(table)
        .upsert(data, on_conflict=on_conflict, ignore_duplicates=ignore_duplicates)
        .execute()
    )
    return result.data[0] if result.data else {}


async def db_insert_if_new(
    table: str,
    data: dict[str, Any],
    fetch_filters: dict[str, Any],
) -> tuple[dict[str, Any], bool]:
    """Insert row; on unique-constraint violation, fetch+return the existing row.

    Returns (row, created) where created=True means a new row was inserted.
    """
    try:
        row = await db_insert(table, data)
        if row:
            return row, True
    except Exception:
        pass
    existing = await db_select_one(table, fetch_filters)
    return (existing or {}, False)


async def db_delete(table: str, filters: dict[str, Any]) -> None:
    client = get_supabase()

    def _run():
        q = client.table(table).delete()
        for key, val in filters.items():
            q = q.eq(key, val)
        return q.execute()

    await asyncio.to_thread(_run)


async def db_count(table: str, filters: dict[str, Any] | None = None) -> int:
    client = get_supabase()

    def _run():
        q = client.table(table).select("id", count="exact")
        if filters:
            for key, val in filters.items():
                q = q.eq(key, val)
        return q.execute()

    result = await asyncio.to_thread(_run)
    return result.count or 0
