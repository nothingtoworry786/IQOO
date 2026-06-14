"""General-purpose web search tool for AI agents.

Wraps SerpAPI to provide structured search results that agents can
include in their reasoning context. Gracefully returns empty results
when SERPAPI_KEY is not configured.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SERPAPI_BASE = "https://serpapi.com/search"


async def web_search(query: str, num: int = 6) -> list[dict[str, Any]]:
    """Run a Google search via SerpAPI and return structured results.

    Returns a list of dicts with keys: title, snippet, link, source.
    Returns [] silently when SERPAPI_KEY is missing or the request fails.
    """
    if not settings.SERPAPI_KEY:
        logger.debug("web_search: SERPAPI_KEY not set — returning empty results")
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
                    "hl": "en",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for r in data.get("organic_results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "link": r.get("link", ""),
                "source": r.get("source", r.get("displayed_link", "")),
            })

        logger.info("web_search('%s'): %d results", query[:60], len(results))
        return results

    except Exception as exc:
        logger.warning("web_search failed for '%s': %s", query[:60], exc)
        return []


def format_search_results(results: list[dict[str, Any]], max_chars: int = 3000) -> str:
    """Format search results into a compact text block for AI context."""
    if not results:
        return "No web search results available."

    lines = ["=== WEB SEARCH RESULTS ==="]
    total = 0
    for i, r in enumerate(results, 1):
        block = (
            f"\n[{i}] {r['title']}\n"
            f"Source: {r['source'] or r['link']}\n"
            f"{r['snippet']}\n"
        )
        if total + len(block) > max_chars:
            break
        lines.append(block)
        total += len(block)

    lines.append("=== END RESULTS ===")
    return "\n".join(lines)


async def research(
    question: str,
    extra_queries: list[str] | None = None,
    num_per_query: int = 5,
) -> tuple[str, list[str]]:
    """Run one or more searches related to a question and return formatted context.

    Args:
        question:      Primary question to search for.
        extra_queries: Additional targeted queries (e.g. competitor-specific).
        num_per_query: Results per query.

    Returns:
        (formatted_text, source_urls)
    """
    all_results: list[dict] = []
    seen_links: set[str] = set()

    queries = [question] + (extra_queries or [])
    for q in queries[:3]:  # cap at 3 queries to stay within SerpAPI quota
        for r in await web_search(q, num=num_per_query):
            link = r.get("link", "")
            if link and link not in seen_links:
                seen_links.add(link)
                all_results.append(r)

    source_urls = [r["link"] for r in all_results if r.get("link")]
    formatted = format_search_results(all_results)
    return formatted, source_urls
