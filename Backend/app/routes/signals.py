"""Signal routes (Supabase-backed)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase_client import db_select, db_select_one, get_supabase
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signals", tags=["Signals v2"])


@router.get("/", summary="List signals for a user/competitor")
async def list_signals(
    user_id: str = Query(...),
    competitor_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    signal_type: str | None = Query(None),
) -> dict:
    client = get_supabase()

    def _run():
        q = (
            client.table("signals")
            .select("*")
            .eq("user_id", user_id)
            .order("detected_at", desc=True)
        )
        if competitor_id:
            q = q.eq("competitor_id", competitor_id)
        if signal_type:
            q = q.eq("type", signal_type)
        return q.range(offset, offset + limit - 1).execute()

    result = await asyncio.to_thread(_run)
    return {"signals": result.data or [], "limit": limit, "offset": offset}


@router.get("/high-intent", summary="Signals with intent_score >= threshold")
async def high_intent_signals(
    user_id: str = Query(...),
    threshold: int = Query(70, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    client = get_supabase()

    def _run():
        return (
            client.table("signals")
            .select("*")
            .eq("user_id", user_id)
            .gte("intent_score", threshold)
            .order("intent_score", desc=True)
            .limit(limit)
            .execute()
        )

    result = await asyncio.to_thread(_run)
    return {"signals": result.data or [], "threshold": threshold}


@router.get("/war-room-triggers", summary="Signals flagged as war-room triggers")
async def war_room_trigger_signals(
    user_id: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    client = get_supabase()

    def _run():
        return (
            client.table("signals")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_war_room_trigger", True)
            .order("detected_at", desc=True)
            .limit(limit)
            .execute()
        )

    result = await asyncio.to_thread(_run)
    return {"signals": result.data or []}


@router.get("/{signal_id}", summary="Get one signal")
async def get_signal(signal_id: str) -> dict:
    row = await db_select_one("signals", {"id": signal_id})
    if not row:
        raise HTTPException(status_code=404, detail="Signal not found.")
    return row
