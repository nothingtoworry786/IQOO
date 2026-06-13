"""SignalHunterAgent — collects competitive signals via SerpAPI.

Multi-source search: hiring, news, funding, product launches.
Gracefully returns [] when SERPAPI_KEY is not configured.

Backward-compatible signature accepts legacy kwargs (user_id, competitor_id, etc.)
for the old SQLite-based callers in app/routers/*.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.services.claude import score_signal_intent

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


async def _serp_search(query: str, num: int = 10) -> list[dict[str, Any]]:
    """Call SerpAPI and return organic results. Returns [] if no key or any error."""
    if not settings.SERPAPI_KEY:
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                SERPAPI_BASE,
                params={
                    "q": query,
                    "api_key": settings.SERPAPI_KEY,
                    "engine": "google",
                    "num": num,
                },
            )
            resp.raise_for_status()
            return resp.json().get("organic_results", [])
    except Exception as exc:
        logger.debug("SerpAPI search failed for '%s': %s", query, exc)
        return []


async def _make_signal(
    signal_type: str,
    title: str,
    snippet: str,
    link: str,
    meaning: str,
) -> dict[str, Any]:
    intent = await score_signal_intent(signal_type, title, snippet)
    return {
        "type": signal_type,
        "title": title[:200],
        "description": snippet[:600],
        "source": link or "Google Search",
        "intent_score": intent,
        "meaning": meaning,
        "raw_data": {"link": link, "snippet": snippet},
        "is_war_room_trigger": intent >= 75,
    }


async def _hiring(name: str) -> list[dict]:
    results = await _serp_search(f"{name} hiring jobs 2025 2026", num=5)
    signals = []
    for r in results[:3]:
        title = r.get("title", "")
        if not title:
            continue
        signals.append(await _make_signal(
            "Hiring", title, r.get("snippet", ""), r.get("link", ""),
            f"Active hiring indicates expansion or product acceleration for {name}",
        ))
    return signals


async def _news(name: str) -> list[dict]:
    results = await _serp_search(f'"{name}" news announcement 2025 2026', num=5)
    signals = []
    for r in results[:3]:
        title = r.get("title", "")
        if not title:
            continue
        signals.append(await _make_signal(
            "Marketing", title, r.get("snippet", ""), r.get("link", ""),
            f"Recent public announcement from {name}",
        ))
    return signals


async def _funding(name: str) -> list[dict]:
    results = await _serp_search(f"{name} funding raised investment 2025 2026", num=5)
    signals = []
    for r in results[:2]:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        kws = ("fund", "rais", "invest", "series", "round", "valuation")
        if not title or not any(k in (title + snippet).lower() for k in kws):
            continue
        signals.append(await _make_signal(
            "Funding", title, snippet, r.get("link", ""),
            f"Funding activity gives {name} runway to expand aggressively",
        ))
    return signals


async def _product(name: str) -> list[dict]:
    results = await _serp_search(f"{name} new feature launch product update 2025", num=5)
    signals = []
    for r in results[:2]:
        title = r.get("title", "")
        if not title:
            continue
        signals.append(await _make_signal(
            "Product", title, r.get("snippet", ""), r.get("link", ""),
            f"Product update/launch from {name}",
        ))
    return signals


async def hunt_signals(
    competitor_name: str = "",
    website: str | None = None,
    industry: str = "",
    # ── Legacy params for backward-compat with app/routers/* ─────────────────
    user_id: str | None = None,
    competitor_id: str | None = None,
    context_hint: str | None = None,
    days_simulated: int | None = None,
) -> list[dict[str, Any]]:
    """Collect signals from multiple SerpAPI searches.

    Returns a list of raw signal dicts (not saved to DB — the caller saves them).
    When SERPAPI_KEY is not set, returns an empty list silently.
    """
    name = competitor_name.strip()
    if not name:
        return []

    results = await asyncio.gather(
        _hiring(name),
        _news(name),
        _funding(name),
        _product(name),
        return_exceptions=True,
    )

    signals: list[dict] = []
    for r in results:
        if isinstance(r, list):
            signals.extend(r)

    logger.info(
        "SignalHunter: %d signals collected for '%s' (serpapi_key=%s)",
        len(signals),
        name,
        "set" if settings.SERPAPI_KEY else "missing",
    )
    return signals
