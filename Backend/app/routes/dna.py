"""DNA profile routes (Supabase-backed)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase_client import db_select, db_select_one

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dna", tags=["DNA Profiles v2"])


@router.get("/", summary="List all DNA profiles for a user's competitors")
async def list_dna_profiles(user_id: str = Query(...)) -> dict:
    # Get competitor IDs for this user
    competitors = await db_select("competitors", {"user_id": user_id}, select_cols="id,name")
    if not competitors:
        return {"profiles": []}

    comp_ids = {c["id"]: c["name"] for c in competitors}

    profiles = []
    for comp_id, comp_name in comp_ids.items():
        row = await db_select_one("dna_profiles", {"competitor_id": comp_id})
        if row:
            profiles.append({**row, "competitor_name": comp_name})

    return {"profiles": profiles, "total": len(profiles)}


@router.get("/{competitor_id}", summary="Get DNA profile for one competitor")
async def get_dna_profile(competitor_id: str) -> dict:
    row = await db_select_one("dna_profiles", {"competitor_id": competitor_id})
    if not row:
        raise HTTPException(
            status_code=404,
            detail="DNA profile not found. Collect at least 5 signals to auto-generate one.",
        )
    return row


@router.post("/{competitor_id}/rebuild", summary="Trigger a fresh DNA rebuild")
async def rebuild_dna(competitor_id: str, user_id: str = Query(...)) -> dict:
    """Force-rebuild the DNA profile using the latest signals from Supabase."""
    from app.core.supabase_client import db_upsert, db_insert
    from app.agents.dna_forge import forge_dna_profile

    signals = await db_select(
        "signals",
        {"competitor_id": competitor_id},
        order_by="detected_at",
        order_desc=True,
        limit=50,
    )
    if len(signals) < 3:
        raise HTTPException(
            status_code=422,
            detail=f"Not enough signals ({len(signals)}). Need at least 3.",
        )

    comp = await db_select_one("competitors", {"id": competitor_id})
    comp_name = comp.get("name", competitor_id) if comp else competitor_id

    profile = await forge_dna_profile(competitor_id, comp_name, signals, user_id=user_id)
    if not profile:
        raise HTTPException(status_code=500, detail="DNA generation failed.")

    saved = await db_upsert(
        "dna_profiles",
        {"competitor_id": competitor_id, "user_id": user_id, **profile},
        on_conflict="competitor_id",
    )

    await db_insert(
        "agent_logs",
        {
            "user_id": user_id,
            "competitor_id": competitor_id,
            "agent_name": "DNAForgeAgent",
            "action": f"Manual DNA rebuild for {comp_name}",
            "reasoning": profile.get("behavioral_summary", ""),
        },
    )

    return {"status": "rebuilt", "profile": saved or profile}
