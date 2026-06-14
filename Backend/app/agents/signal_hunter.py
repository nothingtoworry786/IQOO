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

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"

# Base competitive-intent weight per signal type (0-100).
_TYPE_WEIGHT = {
    "Funding": 80,
    "Expansion": 75,
    "Product": 66,
    "Leadership": 60,
    "Hiring": 55,
    "Marketing": 46,
    "Sentiment": 40,
}

# High-signal keywords that bump the intent score when present in title/snippet.
_HOT_KEYWORDS = (
    "launch", "raise", "raised", "million", "billion", "series a", "series b",
    "series c", "funding", "valuation", "ipo", "acquire", "acquisition",
    "merger", "partnership", "expand", "expansion", "record", "surge",
    "double", "triple", "new market", "rollout", "unveil", "breakthrough",
)


def _heuristic_intent(signal_type: str, title: str, snippet: str) -> int:
    """Fast, deterministic 0-100 competitive-intent score — no AI call.

    Avoids one AI request per signal (which both burns quota and, when the
    provider is throttled, collapses every score to a flat default).
    """
    score = _TYPE_WEIGHT.get(signal_type, 50)
    text = f"{title} {snippet}".lower()

    hits = sum(1 for kw in _HOT_KEYWORDS if kw in text)
    score += min(hits * 6, 18)            # up to +18 for strong keywords

    if "2026" in text:
        score += 6                        # very recent
    elif "2025" in text:
        score += 3

    if "%" in text or any(c.isdigit() for c in text):
        score += 3                        # concrete metrics → more actionable

    return max(0, min(100, score))


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
    intent = _heuristic_intent(signal_type, title, snippet)
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


# Public alias so other modules don't need to import a private function
serp_search = _serp_search


async def persist_signals(competitor_id: str, raw_signals: list[dict]) -> int:
    """Save hunted signal dicts to the signals table. Returns the number saved.

    Maps the raw signal dict (type/title/description/source/intent_score) onto
    the Signal ORM model, converting the 0-100 intent score to the 0-10
    impact/urgency scale the app expects.
    """
    if not raw_signals:
        return 0

    from app.models.signal import Signal, SignalCategory
    from app.services.database import async_session_factory

    saved = 0
    async with async_session_factory() as session:
        for s in raw_signals:
            try:
                sig_type = SignalCategory(s.get("type", "Marketing"))
            except ValueError:
                sig_type = SignalCategory.MARKETING

            intent = float(s.get("intent_score", 50) or 50)
            impact = round(min(10.0, max(0.0, intent / 10.0)), 1)
            urgency = round(min(10.0, impact * 0.9), 1)

            session.add(Signal(
                competitor_id=competitor_id,
                signal_type=sig_type,
                title=(s.get("title") or "Untitled signal")[:256],
                description=s.get("description") or "",
                source=(s.get("source") or "Google Search")[:256],
                impact_score=impact,
                urgency_score=urgency,
            ))
            saved += 1
        await session.commit()

    return saved


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

    # Persist to DB when a competitor_id is provided (the live SQLite callers in
    # discovery / onboarding). Callers without a competitor_id (e.g. the demo
    # simulator) save signals themselves, so we don't double-write.
    if competitor_id and signals:
        try:
            saved = await persist_signals(competitor_id, signals)
            logger.info("SignalHunter: persisted %d/%d signals for '%s'", saved, len(signals), name)
        except Exception as exc:
            logger.warning("SignalHunter: failed to persist signals for '%s': %s", name, exc)

    return signals
