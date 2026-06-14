"""
competitor_analysis.py — Company discovery + competitor seeding service.

Two responsibilities:
  1. analyze_competitor()  — AI-powered signal analysis.
  2. discover_company_and_competitors() — live discovery pipeline:
       • Scrapes the company website.
       • AI enriches the company profile (industry, features, geo).
       • AI discovers real competitors, then rechecks for relevance.
       • SerpAPI hunts live signals for each discovered competitor.
       • Predictions and War Room reports are generated from real signals.
"""

from __future__ import annotations

import json
import logging
import re
import uuid

from app.core.ai_provider import get_ai_provider
from app.schemas.requests import AnalyzeRequest
from app.schemas.responses import AnalyzeResponse
from app.providers.base import AIProviderError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Existing analysis helpers (unchanged)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are MarketWatch, an elite competitive intelligence analyst.

Analyze competitor signals.

Return:
- summary
- prediction
- confidence
- 3 recommended actions

Return valid JSON only. Use this exact structure:
{{
  "summary": "string",
  "prediction": "string",
  "confidence": 74,
  "actions": ["string", "string", "string"]
}}"""


def _build_prompt(request: AnalyzeRequest) -> str:
    """Build the analysis prompt from the incoming request data."""
    return f"""{SYSTEM_PROMPT}

Competitor: {request.competitor_name}
City: {request.city}

Recent Signals:
- Jobs added: {request.jobs_added}
- Ad spend change: {request.ad_spend_change}%
- Sentiment change: {request.sentiment_change}%

Generate a comprehensive competitive intelligence analysis based on these signals."""


def _parse_response(raw: str) -> AnalyzeResponse:
    """Parse the JSON response from the AI provider into a structured response."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```\w*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI provider response as JSON: %s", exc)
        raise AIProviderError(
            f"AI provider returned invalid JSON. Raw response: {raw[:500]}"
        ) from exc

    summary = data.get("summary", "")
    prediction = data.get("prediction", "")
    confidence = data.get("confidence", 50)
    actions = data.get("actions", [])

    confidence = max(0, min(100, int(confidence))) if confidence is not None else 50

    if not actions or len(actions) < 3:
        actions = [
            "Monitor competitor activity closely.",
            "Review and adjust marketing strategy.",
            "Strengthen local presence in the target city.",
        ]

    return AnalyzeResponse(
        summary=summary or "No summary provided.",
        prediction=prediction or "No prediction provided.",
        confidence=confidence,
        actions=actions[:3],
    )


async def analyze_competitor(request: AnalyzeRequest) -> AnalyzeResponse:
    """Orchestrate the competitor analysis workflow."""
    logger.info(
        "Starting analysis for competitor '%s' in '%s'",
        request.competitor_name,
        request.city,
    )

    prompt = _build_prompt(request)
    provider = get_ai_provider()

    logger.debug("Sending prompt to %s", type(provider).__name__)
    raw_response = await provider.generate(prompt)

    logger.debug("Raw response received (%d chars)", len(raw_response))
    result = _parse_response(raw_response)

    logger.info(
        "Analysis complete for '%s' (confidence=%d)",
        request.competitor_name,
        result.confidence,
    )

    return result


# ---------------------------------------------------------------------------
# Predictive-move synthesis (signal-driven, no AI call)
# ---------------------------------------------------------------------------

# Predicted strategic move keyed by the competitor's dominant signal type.
_MOVE_BY_TYPE = {
    "Funding": (
        "just strengthened its balance sheet — expect aggressive pricing, "
        "faster geographic expansion, and a hiring push within 30-60 days."
    ),
    "Hiring": (
        "is staffing up fast — anticipate a new product launch or city rollout "
        "within the next quarter."
    ),
    "Product": (
        "is shipping features rapidly — expect a feature-parity push that will "
        "pressure your roadmap; prepare a differentiation response."
    ),
    "Expansion": (
        "is moving into new markets — expect them to enter your core geography "
        "next, likely with localized pricing."
    ),
    "Marketing": (
        "is ramping brand spend — expect higher customer-acquisition competition "
        "and aggressive promotions aimed at your customers."
    ),
    "Leadership": (
        "made key leadership changes — expect a strategic pivot or a new business "
        "line within one to two quarters."
    ),
    "Sentiment": (
        "is seeing shifting brand sentiment — a reputation window may be opening "
        "that you can capture; monitor for churn."
    ),
}


def _synthesize_prediction(comp_name: str, industry: str, signals: list) -> tuple[str, int, str, str]:
    """Build a specific predictive move from the competitor's signal mix.

    Returns (prediction_text, confidence, threat_level, reasoning).
    """
    from collections import Counter

    type_counts = Counter(s.signal_type.value for s in signals)
    top_type, top_type_n = type_counts.most_common(1)[0]
    top = max(signals, key=lambda s: s.impact_score)

    avg_impact = sum(s.impact_score for s in signals) / len(signals)
    high_intent = sum(1 for s in signals if s.impact_score >= 7.0)

    confidence = int(min(92, max(55, avg_impact * 9 + high_intent * 2)))

    if avg_impact >= 7.5 or high_intent >= 3:
        threat = "high"
    elif avg_impact >= 5.0 or high_intent >= 1:
        threat = "medium"
    else:
        threat = "low"

    move = _MOVE_BY_TYPE.get(
        top_type,
        f"is showing active {top_type} signals suggesting strategic moves in {industry}.",
    )
    prediction = f"{comp_name} {move}"

    reasoning = (
        f"Dominant signal: {top_type} ({top_type_n} of {len(signals)} signals). "
        f"Strongest signal: '{top.title}' (impact {top.impact_score:.1f}/10). "
        f"{high_intent} high-intent signal(s) detected; avg impact {avg_impact:.1f}/10."
    )
    return prediction, confidence, threat, reasoning


# ---------------------------------------------------------------------------
# Live Discovery + Seeding Pipeline
# ---------------------------------------------------------------------------



async def discover_company_and_competitors(
    company_name: str,
    website_url: str,
) -> dict:
    """
    Live discovery pipeline:
      1. Scrapes the company website for context.
      2. AI enriches the company profile (industry, features, geo focus).
      3. AI discovers 3-5 real competitors.
      4. AI validates and enriches each competitor.
      5. SerpAPI signal hunter collects live signals for each competitor.
      6. Predictions and War Room reports are generated from real signal data.
    """
    from app.models.competitor import Competitor
    from app.models.signal import Signal
    from app.models.prediction import Prediction
    from app.models.warroom import WarRoomReport
    from app.services.database import async_session_factory
    from app.services.scraper import scrape_and_analyze
    from app.services.claude import (
        enrich_company_profile,
        discover_competitors,
        recheck_competitors,
        validate_competitor,
        generate_discovery_summary,
    )
    from app.agents.signal_hunter import hunt_signals
    from sqlalchemy import select, func

    logger.info("Discovery pipeline starting for '%s' (%s)", company_name, website_url)

    # ── Step 1: Scrape company website ────────────────────────────────────────
    scraped = await scrape_and_analyze(website_url)
    if scraped:
        logger.info("Scraped '%s': %d chars", website_url, len(scraped.get("content", "")))
    else:
        logger.warning("Could not scrape '%s' — proceeding without page content", website_url)

    description = (scraped or {}).get("meta_description", "")

    # ── Step 2: AI-enrich company profile ────────────────────────────────────
    profile = await enrich_company_profile(company_name, website_url, description, scraped)
    industry = profile.get("industry", "Technology")
    key_features = profile.get("key_features", [])
    geographic_focus = profile.get("geographic_focus", "National")
    sub_category = profile.get("sub_category", industry)
    target_customers = profile.get("target_customers", "businesses")
    logger.info("Profile: industry=%s, sub_category=%s, geo=%s, customers=%s",
                industry, sub_category, geographic_focus, target_customers)

    # Use scraped description for richer context downstream
    scraped_description = description or sub_category
    if scraped and scraped.get("content"):
        scraped_description = scraped["content"][:400]

    # ── Step 3: AI discovers competitors ─────────────────────────────────────
    raw_competitors = await discover_competitors(
        company_name=company_name,
        website=website_url,
        industry=industry,
        sub_category=sub_category,
        key_features=key_features,
        geographic_focus=geographic_focus,
        target_customers=target_customers,
        description=scraped_description,
    )
    if not raw_competitors:
        logger.warning("AI returned no competitors — aborting discovery")
        return {
            "status": "ok",
            "company_name": company_name,
            "website_url": website_url,
            "competitors_found": 0,
            "signals_seeded": 0,
            "competitors": [],
            "message": "No competitors found. Try a more specific company name or website.",
        }

    # ── Step 3.5: Recheck — reject competitors from wrong industries ─────────
    logger.info("Running recheck on %d raw competitors…", len(raw_competitors))
    raw_competitors = await recheck_competitors(
        competitors=raw_competitors,
        company_name=company_name,
        industry=industry,
        sub_category=sub_category,
        target_customers=target_customers,
        description=scraped_description,
    )
    if not raw_competitors:
        logger.warning("Recheck rejected ALL competitors — returning early")
        return {
            "status": "ok",
            "company_name": company_name,
            "website_url": website_url,
            "competitors_found": 0,
            "signals_seeded": 0,
            "competitors": [],
            "message": (
                f"No valid competitors found for {company_name} in {sub_category}. "
                "Try a more specific company name or website URL."
            ),
        }
    logger.info("%d competitors passed recheck", len(raw_competitors))

    # ── Step 4: Validate and enrich each competitor (up to 3) ────────────────
    validated: list[dict] = []
    for raw in raw_competitors[:3]:
        name = str(raw.get("name", "")).strip()
        if not name:
            continue
        try:
            enriched = await validate_competitor(
                competitor_name=name,
                company_name=company_name,
                sub_category=sub_category,
                geographic_focus=geographic_focus,
                color_accent="#22D3EE",
            )
            validated.append(enriched)
            logger.info("Validated competitor: %s (threat=%s)", name, enriched.get("threat_level"))
        except Exception as exc:
            logger.warning("validate_competitor failed for '%s': %s", name, exc)
            validated.append({
                "name": name,
                "website": raw.get("website", ""),
                "description": raw.get("reason", ""),
                "threat_level": "MEDIUM",
                "threat_reason": "Unable to fully validate.",
                "competitive_edge": "Unknown.",
            })

    # ── Step 5: Insert competitors into DB ───────────────────────────────────
    seeded_competitors: list[dict] = []
    async with async_session_factory() as session:
        existing_names_result = await session.execute(
            select(Competitor.name)
        )
        existing_names = {n.lower() for (n,) in existing_names_result.fetchall()}

        for comp_data in validated:
            name = comp_data.get("name", "").strip()
            if not name or name.lower() in existing_names:
                logger.info("Skipping duplicate competitor: %s", name)
                continue
            existing_names.add(name.lower())

            comp_id = f"disc-{uuid.uuid4().hex[:8]}"
            threat_level = str(comp_data.get("threat_level", "MEDIUM")).lower()

            competitor = Competitor(
                id=comp_id,
                name=name,
                industry=industry,
                website=comp_data.get("website", ""),
                market_scope=geographic_focus,
                is_active=True,
            )
            session.add(competitor)
            await session.flush()

            seeded_competitors.append({
                "id": comp_id,
                "name": name,
                "industry": industry,
                "website": comp_data.get("website", ""),
                "threat_level": threat_level,
                "description": comp_data.get("description", ""),
            })

        await session.commit()

    logger.info("Inserted %d competitors into DB", len(seeded_competitors))

    # ── Step 6: Hunt live signals via SerpAPI ────────────────────────────────
    total_signals = 0
    for comp in seeded_competitors:
        try:
            await hunt_signals(
                user_id="system",
                competitor_id=comp["id"],
                competitor_name=comp["name"],
                industry=industry,
            )
            async with async_session_factory() as session:
                result = await session.execute(
                    select(func.count(Signal.id)).where(Signal.competitor_id == comp["id"])
                )
                count = result.scalar() or 0
                total_signals += count
                logger.info("Hunted %d signals for '%s'", count, comp["name"])
        except Exception as exc:
            logger.warning("Signal hunt failed for '%s': %s", comp["name"], exc)

    # ── Step 7: Generate predictions + War Room reports from real signals ─────
    async with async_session_factory() as session:
        for comp in seeded_competitors:
            signals_result = await session.execute(
                select(Signal)
                .where(Signal.competitor_id == comp["id"])
                .order_by(Signal.impact_score.desc())
                .limit(10)
            )
            signals = signals_result.scalars().all()

            if not signals:
                continue

            top = signals[0]
            avg_impact = sum(s.impact_score for s in signals) / len(signals)

            prediction_text, confidence, threat, reasoning = _synthesize_prediction(
                comp["name"], industry, list(signals)
            )

            prediction = Prediction(
                id=str(uuid.uuid4()),
                competitor_id=comp["id"],
                prediction=prediction_text,
                confidence=confidence,
                threat_level=threat,
                ai_reasoning=reasoning,
            )
            session.add(prediction)

            icon = "🔴" if threat == "high" else ("🟠" if threat == "medium" else "🟡")
            report = WarRoomReport(
                id=str(uuid.uuid4()),
                competitor_id=comp["id"],
                threat_summary=(
                    f"{icon} {threat.upper()}: {comp['name']} detected with "
                    f"{len(signals)} active intelligence signals in {industry}. "
                    f"Top signal: {top.title}."
                ),
                recommended_actions=(
                    "1. Review the latest signals in the Competitors tab.\n"
                    "2. Set up alerts for high-impact signal types.\n"
                    "3. Brief your team on the competitive moves detected.\n"
                    "4. Monitor this competitor's next actions closely."
                ),
                impact_score=float(avg_impact),
            )
            session.add(report)

        await session.commit()

    # ── Step 8: Generate human-readable summary ───────────────────────────────
    try:
        message = await generate_discovery_summary(company_name, seeded_competitors)
    except Exception:
        n = len(seeded_competitors)
        message = (
            f"War Room initialised with {n} competitors "
            f"and {total_signals} live intelligence signals for {company_name}."
        )

    # ── Step 9: Index company + competitors into the RAG knowledge base ───────
    try:
        from app.services import rag
        await rag.index_company_context(company_name, profile)
        await rag.sync_from_db(company_name)
    except Exception as exc:
        logger.warning("RAG indexing skipped: %s", exc)

    logger.info(
        "Discovery complete — %d competitors, %d signals",
        len(seeded_competitors), total_signals,
    )

    return {
        "status": "ok",
        "company_name": company_name,
        "website_url": website_url,
        "competitors_found": len(seeded_competitors),
        "signals_seeded": total_signals,
        "competitors": seeded_competitors,
        "message": message,
    }
