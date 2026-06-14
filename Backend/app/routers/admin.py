"""Admin / demo endpoints — for hackathon judges only."""

from __future__ import annotations

import asyncio
import logging
import os

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin / Demo"])


class ResetResponse(BaseModel):
    sqlite_rows_deleted: int
    supabase_tables_cleared: list[str]
    supabase_tables_failed: list[str]
    message: str


@router.post(
    "/reset-all",
    response_model=ResetResponse,
    summary="Delete ALL data from SQLite and Supabase (irreversible)",
)
async def reset_all_data() -> ResetResponse:
    """Wipe every row from every table in both databases. Schema is preserved."""
    # ── SQLite ────────────────────────────────────────────────────────────────
    sqlite_tables = [
        "agent_logs", "warroom_reports", "predictions", "competitive_dna",
        "signals", "alerts", "competitor_markets", "competitor_relationships",
        "markets", "competitors", "users",
    ]
    sqlite_total = 0

    db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./marketwatch.db")
    if "postgresql" not in db_url:
        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text

            engine = create_async_engine(db_url, echo=False)
            async with engine.begin() as conn:
                await conn.execute(text("PRAGMA foreign_keys = OFF"))
                for tbl in sqlite_tables:
                    try:
                        r = await conn.execute(text(f'DELETE FROM "{tbl}"'))
                        sqlite_total += r.rowcount
                    except Exception:
                        pass
                await conn.execute(text("PRAGMA foreign_keys = ON"))
            await engine.dispose()
        except Exception as exc:
            logger.warning("SQLite reset failed: %s", exc)

    # ── Supabase ──────────────────────────────────────────────────────────────
    supabase_tables = [
        "agent_logs", "dna_profiles", "signals", "discovery_jobs",
        "competitor_profiles", "competitors", "company_profiles",
    ]
    cleared: list[str] = []
    failed: list[str] = []

    supa_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    supa_key = os.getenv("SUPABASE_KEY", "")

    if supa_url and supa_key:
        headers = {
            "apikey": supa_key,
            "Authorization": f"Bearer {supa_key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            for tbl in supabase_tables:
                try:
                    resp = await client.delete(
                        f"{supa_url}/rest/v1/{tbl}",
                        headers=headers,
                        params={"id": "neq.00000000-0000-0000-0000-000000000000"},
                    )
                    if resp.status_code in (200, 204):
                        cleared.append(tbl)
                    else:
                        logger.warning("Supabase %s reset HTTP %d: %s", tbl, resp.status_code, resp.text[:200])
                        failed.append(tbl)
                except Exception as exc:
                    logger.warning("Supabase %s reset error: %s", tbl, exc)
                    failed.append(tbl)
    else:
        logger.warning("Supabase credentials not set — skipped")

    return ResetResponse(
        sqlite_rows_deleted=sqlite_total,
        supabase_tables_cleared=cleared,
        supabase_tables_failed=failed,
        message=(
            f"SQLite: {sqlite_total} rows deleted. "
            f"Supabase: {len(cleared)}/{len(supabase_tables)} tables cleared."
            + (f" Failed: {failed}" if failed else "")
        ),
    )


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
                competitor_name=comp_name,
                industry=industry,
                context_hint=f"Day {day} of monitoring. Focus on signals that would emerge {day} days into tracking.",
                days_simulated=day,
            )
            total_signals += len(new_sigs)

            # Persist signals to SQLite so DNA / prediction logic can read them
            if new_sigs:
                from app.models.signal import Signal as _Signal, SignalCategory as _SC
                from app.services.database import async_session_factory as _asf
                async with _asf() as _session:
                    for s in new_sigs:
                        raw_type = s.get("type", "Hiring")
                        try:
                            sig_type = _SC(raw_type)
                        except ValueError:
                            sig_type = _SC.HIRING
                        intent = float(s.get("intent_score", 50))
                        impact = round(min(10.0, intent / 10.0), 1)
                        _session.add(_Signal(
                            competitor_id=data.competitor_id,
                            signal_type=sig_type,
                            title=s.get("title", "")[:512],
                            description=s.get("description", ""),
                            source=s.get("source", ""),
                            impact_score=impact,
                            urgency_score=round(impact * 0.85, 1),
                        ))
                    await _session.commit()

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
    from sqlalchemy import func
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count()).select_from(AgentLog)
            .where(AgentLog.competitor_id == data.competitor_id)
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
