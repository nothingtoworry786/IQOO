"""Admin / demo endpoints — for hackathon judges only."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin / Demo"])


class SimulateRequest(BaseModel):
    competitor_id: str = Field(..., description="ID of the competitor to simulate time passage for")
    days: int = Field(..., ge=1, le=90, description="Number of days to fast-forward (1-90)")
    user_id: str = Field("system", max_length=128)


class SimulateResponse(BaseModel):
    competitor_id: str
    days_simulated: int
    signals_generated: int
    dna_updated: bool
    prediction_fired: bool
    war_room_activated: bool
    activity_entries: int
    message: str


@router.post(
    "/simulate-time-passage",
    response_model=SimulateResponse,
    summary="Fast-forward N days of autonomous monitoring (demo only)",
    description=(
        "Simulates N days of autonomous operation in seconds. "
        "Runs signal hunting, DNA forging, prediction, and War Room activation "
        "across N iterations with day-varying AI prompts. "
        "Use this on stage to show agents that 'ran while you weren't looking'."
    ),
)
async def simulate_time_passage(data: SimulateRequest) -> SimulateResponse:
    """
    Demo endpoint: fast-forward N days of autonomous monitoring for one competitor.

    Each 'day' runs:
      - SignalHunterAgent (with day-N context so AI varies the signals)
      - DNAForgeAgent (once enough signals accumulate)
      - PredictionEngine (when high-intent signals + DNA align)
      - StrategyAgent / War Room (if prediction crosses threshold)
    """
    from app.agents.signal_hunter import hunt_signals
    from app.agents.dna_forge import forge_dna_profile
    from app.agents.prediction_engine import run_prediction, generate_battle_plan
    from app.agents.autonomy_orchestrator import _all_signals, _recent_signals, _dna_patterns, _signal_count
    from app.models.competitor import Competitor
    from app.services.database import async_session_factory
    from app.models.agent_log import AgentLog
    import uuid
    from sqlalchemy import select

    # Validate competitor exists
    async with async_session_factory() as session:
        result = await session.execute(
            select(Competitor).where(Competitor.id == data.competitor_id)
        )
        competitor = result.scalar_one_or_none()
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")
        comp_name = competitor.name
        industry = competitor.industry or "Technology"

    user_id = data.user_id
    total_signals = 0
    dna_updated = False
    prediction_fired = False
    war_room_activated = False

    logger.info(
        "simulate-time-passage: %d days for '%s' (user=%s)",
        data.days, comp_name, user_id,
    )

    async with async_session_factory() as session:
        session.add(AgentLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            competitor_id=data.competitor_id,
            agent_name="AutonomyOrchestrator",
            action=f"⏩ Time simulation started — fast-forwarding {data.days} days for {comp_name}",
            reasoning=f"Demo simulation: compressing {data.days} days of autonomous monitoring into seconds.",
        ))
        await session.commit()

    # ── Simulate each day ─────────────────────────────────────────────────────
    for day in range(1, data.days + 1):
        try:
            new_sigs = await hunt_signals(
                user_id=user_id,
                competitor_id=data.competitor_id,
                competitor_name=comp_name,
                industry=industry,
                context_hint=f"Day {day} of monitoring. Focus on signals that would emerge {day} days into tracking.",
                days_simulated=day,
            )
            total_signals += len(new_sigs)

            # Update DNA every 5 days or when we cross the 10-signal threshold
            total = await _signal_count(data.competitor_id)
            if day % 5 == 0 or (total >= 10 and not dna_updated):
                signals = await _all_signals(data.competitor_id)
                result = await forge_dna_profile(
                    user_id=user_id,
                    competitor_id=data.competitor_id,
                    competitor_name=comp_name,
                    signals=signals,
                )
                if result:
                    dna_updated = True

        except Exception as exc:
            logger.warning("Simulation day %d failed: %s", day, exc)

    # ── Final: run prediction with all accumulated signals ────────────────────
    try:
        recent = await _recent_signals(data.competitor_id, days=data.days + 1)
        high_intent = [s for s in recent if (s["impact_score"] + s["urgency_score"]) / 2 >= 6.0]
        dna = await _dna_patterns(data.competitor_id)

        if high_intent and dna:
            prediction = await run_prediction(
                user_id=user_id,
                competitor_id=data.competitor_id,
                competitor_name=comp_name,
                high_intent_signals=high_intent,
                dna_patterns=dna,
            )
            if prediction:
                prediction_fired = True
                if prediction.get("is_war_room_trigger"):
                    all_sigs = await _all_signals(data.competitor_id)
                    plan = await generate_battle_plan(
                        user_id=user_id,
                        competitor_id=data.competitor_id,
                        competitor_name=comp_name,
                        prediction=prediction,
                        signals=all_sigs,
                    )
                    if plan:
                        war_room_activated = True
    except Exception as exc:
        logger.warning("Post-simulation prediction failed: %s", exc)

    # Count new activity log entries
    from app.models.agent_log import AgentLog as AL
    from sqlalchemy import func
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(AL)
            .where(AL.competitor_id == data.competitor_id)
        )
        activity_count = result.scalar() or 0

    async with async_session_factory() as session:
        session.add(AgentLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            competitor_id=data.competitor_id,
            agent_name="AutonomyOrchestrator",
            action=f"⏩ Time simulation complete — {data.days} days compressed into seconds",
            reasoning=f"Generated {total_signals} signals, DNA updated: {dna_updated}, "
                      f"prediction fired: {prediction_fired}, War Room: {war_room_activated}.",
        ))
        await session.commit()

    return SimulateResponse(
        competitor_id=data.competitor_id,
        days_simulated=data.days,
        signals_generated=total_signals,
        dna_updated=dna_updated,
        prediction_fired=prediction_fired,
        war_room_activated=war_room_activated,
        activity_entries=activity_count,
        message=(
            f"Simulated {data.days} days of autonomous monitoring for {comp_name}. "
            f"{total_signals} signals generated, "
            f"{'DNA profile built, ' if dna_updated else ''}"
            f"{'prediction fired' + (', War Room activated' if war_room_activated else '') if prediction_fired else 'no prediction yet'}."
        ),
    )
