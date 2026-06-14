"""Background retry queue for competitor-discovery jobs.

When a discovery request fails (e.g. the AI provider is rate-limited / down) or
returns no competitors, the job is added to this in-memory queue. A single
background worker drains the queue and retries each job with exponential
backoff until it succeeds or hits MAX_ATTEMPTS. Once it succeeds, the
competitors are seeded into the DB and appear in the app on the next refresh.
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
BASE_RETRY_DELAY = 60.0  # seconds; doubles each attempt (60s, 120s, 240s, …)

_queue: asyncio.Queue | None = None
_worker_task: asyncio.Task | None = None
# Companies currently in-flight (queued or mid-retry) — dedupes user resubmits.
_pending: set[str] = set()


def _key(company_name: str, website_url: str) -> str:
    return f"{company_name.lower().strip()}|{website_url.lower().strip()}"


def is_pending(company_name: str, website_url: str) -> bool:
    return _key(company_name, website_url) in _pending


async def enqueue_discovery(company_name: str, website_url: str, attempt: int = 1) -> bool:
    """Add a discovery job to the retry queue. Returns False if it can't be queued."""
    if _queue is None:
        logger.warning("Discovery queue not started — cannot enqueue '%s'", company_name)
        return False

    k = _key(company_name, website_url)
    if attempt == 1 and k in _pending:
        logger.info("Discovery for '%s' already queued — skipping duplicate", company_name)
        return False

    _pending.add(k)
    await _queue.put(
        {"company_name": company_name, "website_url": website_url, "attempt": attempt}
    )
    logger.info(
        "Queued discovery for '%s' (attempt %d/%d), queue size=%d",
        company_name, attempt, MAX_ATTEMPTS, _queue.qsize(),
    )
    return True


async def _process(job: dict) -> None:
    from app.services.competitor_analysis import discover_company_and_competitors

    company_name = job["company_name"]
    website_url = job["website_url"]
    attempt = job["attempt"]
    k = _key(company_name, website_url)

    try:
        result = await discover_company_and_competitors(
            company_name=company_name,
            website_url=website_url,
        )
        found = result.get("competitors_found", 0)
        if found > 0:
            logger.info(
                "Queued discovery SUCCEEDED for '%s' — %d competitors, %d signals seeded",
                company_name, found, result.get("signals_seeded", 0),
            )
            _pending.discard(k)
            return
        logger.warning(
            "Queued discovery for '%s' returned 0 competitors (attempt %d)",
            company_name, attempt,
        )
    except Exception as exc:
        logger.warning(
            "Queued discovery for '%s' failed (attempt %d): %s",
            company_name, attempt, exc,
        )

    # ── Retry with exponential backoff, or give up ───────────────────────────
    if attempt >= MAX_ATTEMPTS:
        logger.error(
            "Discovery for '%s' gave up after %d attempts — removing from queue",
            company_name, MAX_ATTEMPTS,
        )
        _pending.discard(k)
        return

    delay = BASE_RETRY_DELAY * (2 ** (attempt - 1))
    logger.info(
        "Re-queuing discovery for '%s' in %.0fs (next attempt %d/%d)",
        company_name, delay, attempt + 1, MAX_ATTEMPTS,
    )

    async def _requeue() -> None:
        try:
            await asyncio.sleep(delay)
            await enqueue_discovery(company_name, website_url, attempt + 1)
        except asyncio.CancelledError:
            pass

    asyncio.create_task(_requeue())


async def _worker_loop() -> None:
    assert _queue is not None
    logger.info("Discovery retry worker started")
    while True:
        job = await _queue.get()
        try:
            await _process(job)
        except Exception as exc:  # never let the worker die
            logger.exception("Discovery worker error: %s", exc)
        finally:
            _queue.task_done()


def start_discovery_worker() -> None:
    """Start the background worker. Safe to call once during app startup."""
    global _queue, _worker_task
    if _worker_task is not None and not _worker_task.done():
        return
    _queue = asyncio.Queue()
    _worker_task = asyncio.create_task(_worker_loop())


async def stop_discovery_worker() -> None:
    """Cancel the background worker on app shutdown."""
    global _worker_task
    if _worker_task is not None:
        _worker_task.cancel()
        try:
            await _worker_task
        except asyncio.CancelledError:
            pass
        _worker_task = None
        logger.info("Discovery retry worker stopped")
