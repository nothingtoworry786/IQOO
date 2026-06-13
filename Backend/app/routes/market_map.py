"""Market map endpoint — aggregated competitive landscape view."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase_client import db_select, db_select_one, get_supabase
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Market Map"])


@router.get("/market-map", summary="Full competitive market map for a user")
async def get_market_map(user_id: str = Query(..., description="User ID")) -> dict:
    """
    Returns the full competitive landscape for a user:
    - Their company profile
    - All active competitors with profiles + DNA
    - Threat distribution (HIGH/MEDIUM/LOW)
    - Discovery source breakdown
    - Most active competitor (signals in last 24h)
    - Total market size estimate
    """
    # Company profile
    company = await db_select_one("company_profiles", {"user_id": user_id})

    # Competitors with nested profile + DNA
    client = get_supabase()

    def _fetch_competitors():
        return (
            client.table("competitors")
            .select("*, competitor_profiles(*), dna_profiles(*)")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .execute()
        )

    result = await asyncio.to_thread(_fetch_competitors)
    competitors = result.data or []

    if not competitors:
        return {
            "your_company": company,
            "market_size": 0,
            "competitors": [],
            "competitors_by_threat": {"HIGH": [], "MEDIUM": [], "LOW": []},
            "competitors_by_discovery": {"direct_known": [], "search_discovered": []},
            "most_active_competitor": None,
            "total_signals_24h": 0,
        }

    # Signals in last 24h per competitor
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    def _fetch_recent_signals():
        return (
            client.table("signals")
            .select("competitor_id")
            .eq("user_id", user_id)
            .gte("detected_at", cutoff)
            .execute()
        )

    sig_result = await asyncio.to_thread(_fetch_recent_signals)
    sig_counts: Counter = Counter(
        row["competitor_id"] for row in (sig_result.data or [])
    )
    total_signals_24h = sum(sig_counts.values())

    # Flatten nested data and annotate
    by_threat: dict[str, list] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    by_discovery: dict[str, list] = {"direct_known": [], "search_discovered": []}
    most_active = None
    most_active_count = 0

    enriched: list[dict] = []
    for comp in competitors:
        profile = (comp.get("competitor_profiles") or [{}])
        profile = profile[0] if profile else {}
        dna = (comp.get("dna_profiles") or [{}])
        dna = dna[0] if dna else {}

        threat = (profile.get("threat_level") or "MEDIUM").upper()
        disc_pass = profile.get("discovery_pass", 1)
        signal_count_24h = sig_counts.get(comp["id"], 0)

        flat = {
            "id": comp["id"],
            "name": comp["name"],
            "website": comp.get("website", ""),
            "color_accent": comp.get("color_accent", "#6C63FF"),
            "industry": comp.get("industry", ""),
            "threat_level": threat,
            "threat_reason": profile.get("threat_reason", ""),
            "competitive_edge": profile.get("competitive_edge", ""),
            "description": profile.get("description", ""),
            "discovery_pass": disc_pass,
            "signals_24h": signal_count_24h,
            "dna": {
                "launch_style": dna.get("launch_style"),
                "expansion_speed": dna.get("expansion_speed"),
                "price_aggression": dna.get("price_aggression"),
                "behavioral_summary": dna.get("behavioral_summary"),
            } if dna else None,
        }

        enriched.append(flat)
        by_threat.get(threat, by_threat["MEDIUM"]).append(flat)

        if disc_pass == 1:
            by_discovery["direct_known"].append(flat)
        else:
            by_discovery["search_discovered"].append(flat)

        if signal_count_24h > most_active_count:
            most_active_count = signal_count_24h
            most_active = {"name": comp["name"], "signal_count_24h": signal_count_24h}

    return {
        "your_company": company,
        "market_size": len(enriched),
        "competitors": enriched,
        "competitors_by_threat": by_threat,
        "competitors_by_discovery": by_discovery,
        "most_active_competitor": most_active,
        "total_signals_24h": total_signals_24h,
    }
