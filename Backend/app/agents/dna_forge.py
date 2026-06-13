"""DNAForgeAgent — builds behavioral DNA profiles from accumulated signals.

Accepts both signal formats:
  • New (Supabase):  {"type": str, "title": str, "intent_score": int, ...}
  • Old (SQLite ORM): {"signal_type": str, "title": str, "impact_score": float, "urgency_score": float, ...}

Normalizes to the Claude-expected format before calling the API.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.claude import generate_dna_profile as _claude_dna

logger = logging.getLogger(__name__)


def _normalize(s: dict[str, Any]) -> dict[str, Any]:
    """Normalize old (ORM) or new (Supabase) signal dict to Claude's expected format."""
    sig_type = s.get("type") or s.get("signal_type", "Signal")
    title = s.get("title", "")
    description = s.get("description", "")

    # intent_score: prefer explicit value, otherwise derive from impact+urgency (ORM path)
    if "intent_score" in s:
        intent = int(s["intent_score"])
    else:
        impact = float(s.get("impact_score", 5.0))
        urgency = float(s.get("urgency_score", 5.0))
        intent = int((impact + urgency) / 2.0 * 10)  # scale 0-10 → 0-100

    return {
        "type": str(sig_type),
        "title": title,
        "description": description,
        "intent_score": max(0, min(100, intent)),
    }


async def forge_dna_profile(
    competitor_id: str,
    competitor_name: str,
    signals: list[dict[str, Any]],
    user_id: str | None = None,  # kept for backward-compat
) -> dict[str, Any]:
    """Build a behavioral DNA profile from signals via Claude.

    Returns the profile dict. Saving to DB is the caller's responsibility.
    Returns {} on any error so the pipeline never crashes.
    """
    if not signals:
        logger.debug("DNAForge: no signals for '%s', skipping", competitor_name)
        return {}

    normalized = [_normalize(s) for s in signals]

    try:
        profile = await _claude_dna(competitor_id, competitor_name, normalized)
        logger.info(
            "DNAForge: built profile for '%s' (%d signals, launch_style=%s)",
            competitor_name,
            len(signals),
            profile.get("launch_style", "?"),
        )
        return profile
    except Exception as exc:
        logger.error("DNAForge failed for '%s': %s", competitor_name, exc)
        return {}
