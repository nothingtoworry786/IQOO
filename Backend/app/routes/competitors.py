"""Competitor CRUD routes (Supabase-backed)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.supabase_client import db_insert, db_select, db_select_one, db_update, db_delete

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/competitors", tags=["Competitors v2"])


class CompetitorCreate(BaseModel):
    user_id: str
    name: str
    website: str = ""
    industry: str = ""
    color_accent: str = "#6C63FF"


class CompetitorUpdate(BaseModel):
    name: str | None = None
    website: str | None = None
    is_active: bool | None = None
    color_accent: str | None = None


@router.get("/", summary="List competitors for a user")
async def list_competitors(
    user_id: str = Query(...),
    active_only: bool = Query(True),
) -> dict:
    filters: dict = {"user_id": user_id}
    if active_only:
        filters["is_active"] = True
    rows = await db_select("competitors", filters, order_by="name")
    return {"competitors": rows, "total": len(rows)}


@router.get("/{competitor_id}", summary="Get one competitor")
async def get_competitor(competitor_id: str) -> dict:
    row = await db_select_one("competitors", {"id": competitor_id})
    if not row:
        raise HTTPException(status_code=404, detail="Competitor not found.")
    return row


@router.post("/", summary="Manually add a competitor")
async def create_competitor(data: CompetitorCreate) -> dict:
    import re

    def norm(name: str) -> str:
        result = name.lower().strip()
        for s in (" inc", " ltd", " llc", " corp", " co"):
            if result.endswith(s):
                result = result[: -len(s)].strip()
        return re.sub(r"[^\w\s]", "", result).strip()

    row = await db_insert(
        "competitors",
        {
            "user_id": data.user_id,
            "name": data.name,
            "normalized_name": norm(data.name),
            "website": data.website,
            "industry": data.industry,
            "color_accent": data.color_accent,
            "is_active": True,
        },
    )
    return row


@router.put("/{competitor_id}", summary="Update competitor fields")
async def update_competitor(competitor_id: str, data: CompetitorUpdate) -> dict:
    existing = await db_select_one("competitors", {"id": competitor_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    patch = {k: v for k, v in data.model_dump().items() if v is not None}
    if not patch:
        return existing

    updated = await db_update("competitors", {"id": competitor_id}, patch)
    return updated


@router.delete("/{competitor_id}", summary="Deactivate a competitor")
async def deactivate_competitor(competitor_id: str) -> dict:
    existing = await db_select_one("competitors", {"id": competitor_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Competitor not found.")
    await db_update("competitors", {"id": competitor_id}, {"is_active": False})
    return {"id": competitor_id, "is_active": False}
