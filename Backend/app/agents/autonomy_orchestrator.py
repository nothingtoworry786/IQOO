"""AutonomyOrchestrator — master agent loop, runs every 4 hours via APScheduler."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from app.services.database import async_session_factory

logger = logging.getLogger(__name__)

# In-process state (reset on restart — good enough for demo)
_last_cycle_run: datetime | None = None


# ── DB helpers ────────────────────────────────────────────────────────────────

async def _active_competitors() -> list[dict]:
    from app.models.competitor import Competitor
    from sqlalchemy import select

    async with async_session_factory() as session:
        rows = await session.execute(
            select(Competitor).where(Competitor.is_active == True)  # noqa: E712
        )
        return [
            {"id": c.id, "name": c.name, "industry": c.industry or "Technology"}
            for c in rows.scalars().all()
        ]


async def _signal_count(competitor_id: str) -> int:
    from app.models.signal import Signal
    from sqlalchemy import func, select

    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(Signal).where(Signal.competitor_id == competitor_id)
        )
        return result.scalar() or 0


async def _dna_pattern_count(competitor_id: str) -> int:
    from app.models.competitive_dna import CompetitiveDNA
    from sqlalchemy import func, select

    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(CompetitiveDNA)
            .where(CompetitiveDNA.competitor_id == competitor_id)
        )
        return result.scalar() or 0


async def _recent_signals(competitor_id: str, days: int = 7) -> list[dict]:
    from app.models.signal import Signal
    from sqlalchemy import select

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with async_session_factory() as session:
        rows = await session.execute(
            select(Signal)
            .where(Signal.competitor_id == competitor_id, Signal.created_at >= cutoff)
            .order_by(Signal.created_at.desc())
        )
        return [
            {
                "id": s.id,
                "signal_type": s.signal_type.value,
                "title": s.title,
                "impact_score": s.impact_score,
                "urgency_score": s.urgency_score,
            }
            for s in rows.scalars().all()
        ]


async def _all_signals(competitor_id: str) -> list[dict]:
    from app.models.signal import Signal
    from sqlalchemy import select

    async with async_session_factory() as session:
        rows = await session.execute(
            select(Signal)
            .where(Signal.competitor_id == competitor_id)
            .order_by(Signal.created_at.desc())
        )
        return [
            {
                "id": s.id,
                "signal_type": s.signal_type.value,
                "title": s.title,
                "description": s.description or "",
                "impact_score": s.impact_score,
                "urgency_score": s.urgency_score,
            }
            for s in rows.scalars().all()
        ]


async def _dna_patterns(competitor_id: str) -> list[dict]:
    from app.models.competitive_dna import CompetitiveDNA
    from sqlalchemy import select

    async with async_session_factory() as session:
        rows = await session.execute(
            select(CompetitiveDNA).where(CompetitiveDNA.competitor_id == competitor_id)
        )
        return [
            {
                "pattern_type": d.pattern_type,
                "description": d.description,
                "confidence_score": d.confidence_score,
            }
            for d in rows.scalars().all()
        ]


async def _log(
    user_id: str,
    competitor_id: str | None,
    agent_name: str,
    action: str,
    reasoning: str,
) -> None:
    from app.models.agent_log import AgentLog

    async with async_session_factory() as session:
        session.add(AgentLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            competitor_id=competitor_id,
            agent_name=agent_name,
            action=action,
            reasoning=reasoning,
        ))
        await session.commit()


# ── Per-competitor cycle ──────────────────────────────────────────────────────

async def run_competitor_cycle(
    user_id: str,
    competitor: dict,
    days_simulated: int = 0,
) -> None:
    """Full intelligence cycle for one competitor. All steps isolated by try/except."""
    from app.agents.signal_hunter import hunt_signals
    from app.agents.dna_forge import forge_dna_profile
    from app.agents.prediction_engine import run_prediction, generate_battle_plan

    comp_id = competitor["id"]
    comp_name = competitor["name"]
    industry = competitor.get("industry", "Technology")

    # ── STEP 1: Hunt new signals ──────────────────────────────────────────────
    try:
        await hunt_signals(
            user_id=user_id,
            competitor_id=comp_id,
            competitor_name=comp_name,
            industry=industry,
            days_simulated=days_simulated,
        )
    except Exception as exc:
        logger.error("Step 1 (hunt) failed for '%s': %s", comp_name, exc)

    # ── STEP 2: Decide whether to update DNA ─────────────────────────────────
    try:
        total = await _signal_count(comp_id)
        dna_count = await _dna_pattern_count(comp_id)

        # Update DNA when: first time, or every 5 new signals, or >= 10 total
        should_update = (dna_count == 0) or (total >= 10) or (total > 0 and total % 5 == 0)

        if should_update:
            signals = await _all_signals(comp_id)
            await forge_dna_profile(
                user_id=user_id,
                competitor_id=comp_id,
                competitor_name=comp_name,
                signals=signals,
            )
        else:
            await _log(
                user_id=user_id,
                competitor_id=comp_id,
                agent_name="DNAForgeAgent",
                action=f"DNA update skipped for {comp_name} — not enough new signals yet ({total}/10)",
                reasoning=f"{total} total signals, {dna_count} existing DNA patterns. "
                          f"Threshold: 10 signals or 5 new since last update.",
            )
    except Exception as exc:
        logger.error("Step 2 (DNA) failed for '%s': %s", comp_name, exc)

    # ── STEP 3: Decide whether to fire a prediction ───────────────────────────
    try:
        recent = await _recent_signals(comp_id, days=7)
        # "High intent" = average of impact + urgency scores >= 6.0
        high_intent = [s for s in recent if (s["impact_score"] + s["urgency_score"]) / 2 >= 6.0]
        dna = await _dna_patterns(comp_id)

        if len(high_intent) >= 2 and dna:
            prediction = await run_prediction(
                user_id=user_id,
                competitor_id=comp_id,
                competitor_name=comp_name,
                high_intent_signals=high_intent,
                dna_patterns=dna,
            )

            # ── STEP 4: War Room activation ───────────────────────────────────
            if prediction and prediction.get("is_war_room_trigger"):
                all_sigs = await _all_signals(comp_id)
                await generate_battle_plan(
                    user_id=user_id,
                    competitor_id=comp_id,
                    competitor_name=comp_name,
                    prediction=prediction,
                    signals=all_sigs,
                )
        else:
            await _log(
                user_id=user_id,
                competitor_id=comp_id,
                agent_name="PredictionEngine",
                action=f"Prediction skipped for {comp_name} — insufficient high-intent signals "
                       f"({len(high_intent)}/2 required) or no DNA profile yet ({len(dna)} patterns)",
                reasoning=f"Found {len(high_intent)} high-intent signals in last 7 days "
                          f"and {len(dna)} DNA patterns. Need ≥2 signals + ≥1 DNA pattern.",
            )
    except Exception as exc:
        logger.error("Step 3 (prediction) failed for '%s': %s", comp_name, exc)


# ── Master orchestration loop ─────────────────────────────────────────────────

async def run_autonomous_cycle(user_id: str = "system") -> dict:
    """
    Master loop called by APScheduler every 4 hours.
    Runs the full intelligence pipeline for every active competitor.
    One competitor's failure never blocks others.
    """
    global _last_cycle_run
    _last_cycle_run = datetime.now(timezone.utc)

    competitors = await _active_competitors()

    if not competitors:
        logger.info("AutonomyOrchestrator: no active competitors")
        return {"competitors_processed": 0}

    names_preview = ", ".join(c["name"] for c in competitors[:5])
    if len(competitors) > 5:
        names_preview += f" + {len(competitors) - 5} more"

    await _log(
        user_id=user_id,
        competitor_id=None,
        agent_name="AutonomyOrchestrator",
        action=f"Autonomous cycle started — monitoring {len(competitors)} competitors",
        reasoning=f"Scheduled 4-hour intelligence cycle. Competitors: {names_preview}.",
    )

    results = await asyncio.gather(
        *[run_competitor_cycle(user_id=user_id, competitor=c) for c in competitors],
        return_exceptions=True,
    )
    errors = sum(1 for r in results if isinstance(r, Exception))

    await _log(
        user_id=user_id,
        competitor_id=None,
        agent_name="AutonomyOrchestrator",
        action=f"Cycle complete — {len(competitors) - errors}/{len(competitors)} competitors processed",
        reasoning=f"{errors} errors isolated; they did not block the remaining competitors.",
    )

    logger.info(
        "AutonomyOrchestrator: cycle done — %d processed, %d errors",
        len(competitors) - errors, errors,
    )
    return {"competitors_processed": len(competitors), "errors": errors}


# ── Status query ──────────────────────────────────────────────────────────────

async def get_autonomy_status() -> dict:
    """Return live autonomy system metrics."""
    from app.models.competitor import Competitor
    from app.models.signal import Signal
    from app.models.prediction import Prediction
    from app.models.warroom import WarRoomReport
    from sqlalchemy import func, select

    async with async_session_factory() as session:
        comp_count = (await session.execute(
            select(func.count()).select_from(Competitor).where(Competitor.is_active == True)  # noqa: E712
        )).scalar() or 0

        signal_count = (await session.execute(
            select(func.count()).select_from(Signal)
        )).scalar() or 0

        pred_count = (await session.execute(
            select(func.count()).select_from(Prediction)
        )).scalar() or 0

        war_room_count = (await session.execute(
            select(func.count()).select_from(WarRoomReport)
        )).scalar() or 0

    next_run = (
        (_last_cycle_run + timedelta(hours=4)).isoformat()
        if _last_cycle_run else None
    )

    return {
        "is_autonomous": True,
        "last_cycle_run": _last_cycle_run.isoformat() if _last_cycle_run else None,
        "next_cycle_run": next_run,
        "competitors_monitored": comp_count,
        "total_signals_collected": signal_count,
        "active_predictions": pred_count,
        "active_war_rooms": war_room_count,
    }
