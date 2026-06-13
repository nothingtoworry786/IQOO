"""Background jobs — APScheduler configuration for the autonomous agent system."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")


def setup_scheduler() -> None:
    """
    Register and start all autonomous agent jobs.
    Called once during FastAPI lifespan startup.
    """
    from app.agents.autonomy_orchestrator import run_autonomous_cycle

    # Main intelligence cycle — runs every 4 hours, also fires once at startup
    scheduler.add_job(
        run_autonomous_cycle,
        trigger="interval",
        hours=4,
        id="autonomy_cycle",
        replace_existing=True,
        next_run_time=datetime.now(timezone.utc),   # immediate first run
        misfire_grace_time=120,
        kwargs={"user_id": "system"},
    )

    # Weekly discovery check — looks for new competitors to add
    scheduler.add_job(
        _weekly_discovery_check,
        trigger="interval",
        days=7,
        id="weekly_discovery",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.start()
    logger.info(
        "APScheduler started — autonomy cycle every 4h (first run: now), "
        "discovery check every 7d"
    )


def stop_scheduler() -> None:
    """Gracefully stop the scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")


async def _weekly_discovery_check() -> None:
    """
    Weekly job: re-run discovery to surface new competitors that emerged since onboarding.
    Reads the most recent onboarding context from agent_logs to re-discover.
    """
    from app.models.agent_log import AgentLog
    from app.services.database import async_session_factory
    from sqlalchemy import select, desc
    import uuid

    logger.info("WeeklyDiscovery: checking for new competitor discovery opportunities")

    async with async_session_factory() as session:
        # Find the most recent onboarding discovery log to get company context
        result = await session.execute(
            select(AgentLog)
            .where(AgentLog.agent_name == "DiscoveryAgent")
            .where(AgentLog.competitor_id == None)  # noqa: E711
            .order_by(desc(AgentLog.created_at))
            .limit(1)
        )
        last_log = result.scalar_one_or_none()

        if not last_log:
            logger.info("WeeklyDiscovery: no prior discovery run found, skipping")
            return

        session.add(AgentLog(
            id=str(uuid.uuid4()),
            user_id=last_log.user_id,
            competitor_id=None,
            agent_name="DiscoveryAgent",
            action="Weekly discovery check triggered — will re-discover competitors on next onboarding call",
            reasoning="7-day scheduled check to detect new entrants and emerging competitors "
                      "in the monitored industry landscape.",
        ))
        await session.commit()

    logger.info("WeeklyDiscovery: logged check, full re-discovery runs on next onboarding")
