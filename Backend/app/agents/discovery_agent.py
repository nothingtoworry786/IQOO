"""DiscoveryAgent — autonomous two-pass competitor discovery powered by AI."""

from __future__ import annotations

import json
import logging
import re
import uuid

from app.core.ai_provider import get_ai_provider
from app.providers.base import AIProviderError
from app.services.claude import _filter_real_competitors
from app.services.database import async_session_factory

logger = logging.getLogger(__name__)


async def _ask_ai_for_competitors(
    company_name: str,
    industry: str,
    main_product: str,
    geographic_focus: str,
    exclude: list[str],
) -> list[dict]:
    """Call the AI provider to discover competitor companies."""
    exclude_str = ", ".join(exclude) if exclude else "none"

    prompt = f"""You are a competitive intelligence expert with deep knowledge of global markets.

Target company: {company_name}
Industry: {industry}
Main product/service: {main_product or industry}
Geographic focus: {geographic_focus}
Already known (EXCLUDE these): {exclude_str}

Identify 5 real, specific companies that directly compete with {company_name} in {industry}.
Do NOT include companies from the excluded list.
Companies must be real and verifiable — no made-up names.
NEVER use placeholder names like "Rival Alpha", "Competitor A", "Brand X", "Player 1", etc.

Return ONLY a valid JSON array, nothing else:
[
  {{
    "name": "RealCompanyName",
    "industry": "{industry}",
    "website": "https://realcompany.com",
    "market_scope": "National",
    "reason": "One sentence explaining the direct competitive overlap with {company_name}."
  }}
]

market_scope: "Local" | "Regional" | "National" | "Global" """

    try:
        provider = get_ai_provider()
        raw = await provider.generate(prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```\w*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        result: list[dict] = json.loads(cleaned.strip())
        real = [r for r in result if isinstance(r, dict) and r.get("name")]
        return _filter_real_competitors(real)
    except (AIProviderError, json.JSONDecodeError, Exception) as exc:
        logger.warning("DiscoveryAgent AI call failed: %s", exc)
        return []


async def autonomous_discovery(
    user_id: str,
    company_name: str,
    industry: str,
    main_product: str = "",
    geographic_focus: str = "National",
) -> list[dict]:
    """
    Two-pass autonomous competitor discovery:
      Pass 1 — AI identifies an initial set of 5 competitors.
      Pass 2 — AI finds 5 MORE not already known.

    Each newly discovered competitor is:
      - Inserted into the competitors table (is_active=True)
      - Immediately queued for signal hunting
      - Logged with reasoning to agent_logs

    Returns the list of newly inserted competitor dicts.
    """
    from app.models.competitor import Competitor
    from app.models.agent_log import AgentLog
    from app.agents.signal_hunter import hunt_signals
    from sqlalchemy import select

    logger.info("DiscoveryAgent: starting for '%s' (user=%s)", company_name, user_id)

    # ── Pass 1: Initial discovery ─────────────────────────────────────────────
    pass1 = await _ask_ai_for_competitors(
        company_name=company_name,
        industry=industry,
        main_product=main_product,
        geographic_focus=geographic_focus,
        exclude=[],
    )
    pass1_names = [c["name"] for c in pass1]

    async with async_session_factory() as session:
        session.add(AgentLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            competitor_id=None,
            agent_name="DiscoveryAgent",
            action=f"Pass 1 complete — found {len(pass1)} initial competitors for {company_name}",
            reasoning=f"AI identified: {', '.join(pass1_names) or 'none'}",
        ))
        await session.commit()

    # ── Pass 2: Second-pass to find additional competitors ────────────────────
    pass2 = await _ask_ai_for_competitors(
        company_name=company_name,
        industry=industry,
        main_product=main_product,
        geographic_focus=geographic_focus,
        exclude=pass1_names,
    )

    async with async_session_factory() as session:
        session.add(AgentLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            competitor_id=None,
            agent_name="DiscoveryAgent",
            action=f"Pass 2 complete — found {len(pass2)} additional competitors not in first pass",
            reasoning=f"Second-pass AI found: {', '.join(c['name'] for c in pass2) or 'none additional'}",
        ))
        await session.commit()

    all_discovered = pass1 + pass2

    # ── Deduplicate against existing DB + between the two passes ─────────────
    inserted: list[dict] = []
    seen_names: set[str] = set()

    async with async_session_factory() as session:
        existing = await session.execute(select(Competitor.name))
        for (existing_name,) in existing.fetchall():
            seen_names.add(existing_name.lower())

        for comp_data in all_discovered:
            name = str(comp_data.get("name", "")).strip()
            if not name or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())

            comp_id = f"auto-{str(uuid.uuid4())[:8]}"
            competitor = Competitor(
                id=comp_id,
                name=name,
                industry=comp_data.get("industry", industry),
                website=comp_data.get("website"),
                market_scope=comp_data.get("market_scope", "National"),
                is_active=True,
            )
            session.add(competitor)
            await session.flush()

            session.add(AgentLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                competitor_id=comp_id,
                agent_name="DiscoveryAgent",
                action=f"Added '{name}' to monitored competitors",
                reasoning=comp_data.get(
                    "reason",
                    f"Identified as a direct competitor to {company_name} in {industry}.",
                ),
            ))

            inserted.append({
                "id": comp_id,
                "name": name,
                "industry": comp_data.get("industry", industry),
                "website": comp_data.get("website", ""),
                "reason": comp_data.get("reason", ""),
            })

        await session.commit()

    logger.info("DiscoveryAgent: inserted %d new competitors", len(inserted))

    # ── Immediately hunt signals for each new competitor ─────────────────────
    for comp in inserted:
        try:
            await hunt_signals(
                user_id=user_id,
                competitor_id=comp["id"],
                competitor_name=comp["name"],
                industry=comp["industry"],
            )
        except Exception as exc:
            logger.warning("Initial signal hunt failed for '%s': %s", comp["name"], exc)

    return inserted
