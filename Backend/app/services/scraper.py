"""Website scraper using httpx + BeautifulSoup4."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


async def scrape_and_analyze(url: str, char_limit: int = 2000) -> dict[str, Any] | None:
    """Fetch a URL and extract clean text content.

    Returns None on any error so callers can proceed without scraped data.
    """
    if not url or not url.startswith("http"):
        return None

    try:
        async with httpx.AsyncClient(
            timeout=12.0,
            follow_redirects=True,
            headers=_HEADERS,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            ct = response.headers.get("content-type", "")
            if "text/html" not in ct and "text/plain" not in ct:
                return None

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove noise tags
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
                tag.decompose()

            title = (soup.title.string or "").strip() if soup.title else ""

            meta_desc = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_desc = (meta_tag.get("content") or "").strip()[:500]

            # Clean body text
            text = " ".join(soup.get_text(separator=" ").split())[:char_limit]

            return {
                "url": url,
                "title": title,
                "meta_description": meta_desc,
                "content": text,
            }

    except httpx.HTTPStatusError as exc:
        logger.debug("Scraper HTTP error %s for %s", exc.response.status_code, url)
    except httpx.RequestError as exc:
        logger.debug("Scraper request error for %s: %s", url, exc)
    except Exception as exc:
        logger.warning("Scraper unexpected error for %s: %s", url, exc)

    return None
