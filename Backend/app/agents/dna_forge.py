"""DNAForgeAgent — builds behavioral DNA profiles from accumulated signals.

Calls Claude to extract patterns. Saves result to dna_profiles (Supabase)
when called from the new pipeline. Returns raw dict always so callers
can choose where to persist.

Legacy signature (user_id, competitor_id, ...) kept for backward-compat.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.claude import generate_dna_profile as _claude_dna

logger = logging.getLogger(__name__)


async def forge_dna_profile(
    competitor_id: str,
    competitor_name: str,
    signals: list[dict[str, Any]],
    user_id: str | None = None,  # kept for backward-compat; unused here
) -> dict[str, Any]:
    """Build a behavioral DNA profile from signals via Claude.

    Returns the profile dict. Saving to DB is the caller's responsibility.
    Returns {} on any error so the pipeline never crashes.
    """
    if not signals:
        logger.debug("DNAForge: no signals for '%s', skipping", competitor_name)
        return {}

    try:
        profile = await _claude_dna(competitor_id, competitor_name, signals)
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
