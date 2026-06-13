"""Onboarding API — triggers the full autonomous pipeline the moment setup completes."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onboarding", tags=["Onboarding"])


class OnboardingRequest(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=256)
    industry: str = Field(..., min_length=1, max_length=128)
    main_product: str = Field("", max_length=256)
    geographic_focus: str = Field("National", max_length=64)
    website_url: str = Field("", max_length=512)
    user_id: str = Field("system", max_length=128)


class OnboardingResponse(BaseModel):
    status: str
    user_id: str
    competitors_seeded: int
    competitors_discovered: int
    signals_collected: int
    dna_profiles_created: int
    message: str


@router.post("/setup", response_model=OnboardingResponse, summary="Complete onboarding and activate autonomy")
async def onboarding_setup(data: OnboardingRequest) -> OnboardingResponse:
    """
    Complete the onboarding flow and immediately activate autonomous monitoring:

    1. Seed initial competitors from templates (discover_company_and_competitors)
    2. Run DiscoveryAgent — AI finds 5-10 MORE competitors via two-pass discovery
    3. Hunt signals for ALL competitors in parallel
    4. Forge DNA profiles for competitors with >= 5 signals
    5. Log every decision to agent_logs

    By the time this returns (~15-30s), the dashboard is already populated.
    """
    from app.services.competitor_analysis import discover_company_and_competitors
    from app.agents.discovery_agent import autonomous_discovery
    from app.agents.signal_hunter import hunt_signals
    from app.agents.dna_forge import forge_dna_profile
    from app.agents.autonomy_orchestrator import _all_signals, _active_competitors

    user_id = data.user_id

    # ── Phase 1: Seed initial competitors from static templates ──────────────
    logger.info("Onboarding Phase 1: seeding templates for '%s'", data.company_name)
    try:
        seed_result = await discover_company_and_competitors(
            company_name=data.company_name,
            website_url=data.website_url or f"https://{data.company_name.lower().replace(' ', '')}.com",
        )
        seeded_count = seed_result.get("competitors_found", 0)
    except Exception as exc:
        logger.warning("Template seeding failed: %s", exc)
        seeded_count = 0

    # ── Phase 2: AI discovers additional competitors (two passes) ─────────────
    logger.info("Onboarding Phase 2: autonomous discovery for '%s'", data.company_name)
    try:
        new_competitors = await autonomous_discovery(
            user_id=user_id,
            company_name=data.company_name,
            industry=data.industry,
            main_product=data.main_product,
            geographic_focus=data.geographic_focus,
        )
        discovered_count = len(new_competitors)
    except Exception as exc:
        logger.warning("Autonomous discovery failed: %s", exc)
        new_competitors = []
        discovered_count = 0

    # ── Phase 3: Hunt signals for ALL active competitors in parallel ──────────
    logger.info("Onboarding Phase 3: parallel signal hunting")
    all_active = await _active_competitors()
    hunt_tasks = [
        hunt_signals(
            user_id=user_id,
            competitor_id=c["id"],
            competitor_name=c["name"],
            industry=c["industry"],
        )
        for c in all_active
    ]
    hunt_results = await asyncio.gather(*hunt_tasks, return_exceptions=True)
    total_signals = sum(
        len(r) for r in hunt_results if isinstance(r, list)
    )

    # ── Phase 4: Forge DNA for competitors that now have >= 5 signals ─────────
    logger.info("Onboarding Phase 4: DNA profiling")
    dna_count = 0
    dna_tasks = []
    for comp in all_active:
        signals = await _all_signals(comp["id"])
        if len(signals) >= 5:
            dna_tasks.append(
                forge_dna_profile(
                    user_id=user_id,
                    competitor_id=comp["id"],
                    competitor_name=comp["name"],
                    signals=signals,
                )
            )
    if dna_tasks:
        dna_results = await asyncio.gather(*dna_tasks, return_exceptions=True)
        dna_count = sum(1 for r in dna_results if isinstance(r, dict))

    total_competitors = seeded_count + discovered_count
    return OnboardingResponse(
        status="active",
        user_id=user_id,
        competitors_seeded=seeded_count,
        competitors_discovered=discovered_count,
        signals_collected=total_signals,
        dna_profiles_created=dna_count,
        message=(
            f"Autonomy activated. Monitoring {total_competitors} competitors with "
            f"{total_signals} signals collected and {dna_count} DNA profiles built. "
            f"Agents will continue running every 4 hours automatically."
        ),
    )
