"""
competitor_analysis.py — Company discovery + competitor seeding service.

Two responsibilities:
  1. analyze_competitor()  — existing AI-powered signal analysis (unchanged).
  2. discover_company_and_competitors() — MVP ingestion pipeline:
       • Resolves 3 real competitors for the supplied company/website.
       • Seeds the SQLite DB with richly structured mock Signals,
         Predictions, and WarRoom reports so the app populates instantly.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime

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
# MVP Discovery + Seeding Pipeline
# ---------------------------------------------------------------------------

# Static competitor map keyed by industry keyword found in the website/name.
# Each entry defines 3 competitors with fully pre-baked mock signal payloads.
_COMPETITOR_TEMPLATES: dict[str, list[dict]] = {
    "grocery|blinkit|zepto|swiggy|instamart|bigbasket|dunzo": [
        {
            "id": "disc-blinkit",
            "name": "Blinkit",
            "industry": "Quick Commerce",
            "website": "https://blinkit.com",
            "market_scope": "National",
            "signals": [
                {
                    "signal_type": "Hiring",
                    "source": "LinkedIn Jobs",
                    "title": "Blinkit hiring surge — 23 ops roles in Pune",
                    "description": (
                        "Blinkit posted 23 new operations, logistics, and tech roles "
                        "in Pune within 48 hours, signalling imminent market launch."
                    ),
                    "impact_score": 8.5,
                    "urgency_score": 7.5,
                    "tags": ["hiring", "expansion"],
                },
                {
                    "signal_type": "Marketing",
                    "source": "SensorTower",
                    "title": "Blinkit ad spend up 40% MoM in Pune",
                    "description": (
                        "Blinkit increased digital ad spend 40% month-over-month in "
                        "Pune. Focus on social media and hyperlocal search ads."
                    ),
                    "impact_score": 7.2,
                    "urgency_score": 6.5,
                    "tags": ["ad campaign", "copy change"],
                },
                {
                    "signal_type": "Expansion",
                    "source": "Press Release",
                    "title": "Blinkit expanding to 5 new cities Q3",
                    "description": (
                        "Official press release confirms Jaipur, Lucknow, Chandigarh, "
                        "Bhopal, and Indore launches with hiring already underway."
                    ),
                    "impact_score": 9.0,
                    "urgency_score": 8.5,
                    "tags": ["product expansion", "expansion"],
                },
                {
                    "signal_type": "Product",
                    "source": "App Store",
                    "title": "Blinkit redesigns checkout — 3-tap ordering",
                    "description": (
                        "Blinkit shipped a redesigned checkout flow reducing steps from "
                        "7 to 3. Beta reviews cite 30% faster ordering experience."
                    ),
                    "impact_score": 6.8,
                    "urgency_score": 5.0,
                    "tags": ["feature positioning", "product expansion"],
                },
                {
                    "signal_type": "Funding",
                    "source": "TechCrunch",
                    "title": "Zomato injects ₹300 Cr into Blinkit ops",
                    "description": (
                        "Parent Zomato announced ₹300 Cr internal funding to Blinkit "
                        "earmarked for dark store expansion and last-mile logistics tech."
                    ),
                    "impact_score": 9.2,
                    "urgency_score": 8.0,
                    "tags": ["funding"],
                },
            ],
            "prediction": {
                "prediction": (
                    "Blinkit will launch in 5 new cities within 60 days. "
                    "Expect 25-35% increase in competitive pressure in Tier-2 markets."
                ),
                "confidence": 82,
                "threat_level": "high",
                "ai_reasoning": (
                    "Hiring spike + ad spend surge + city expansion press release = "
                    "textbook pre-launch pattern matched at 85% historical confidence."
                ),
            },
            "warroom": {
                "threat_summary": (
                    "🔴 CRITICAL: Blinkit is executing a coordinated expansion playbook. "
                    "23 new hires + 40% ad spend + city expansion announcement in the "
                    "same 48-hour window is a high-confidence launch signal."
                ),
                "recommended_actions": (
                    "1. Increase local marketing budget by 20% in Pune immediately.\n"
                    "2. Accelerate your own Tier-2 city hiring pipeline.\n"
                    "3. Launch a loyalty/subscription program before Blinkit arrives.\n"
                    "4. Negotiate exclusive SKU agreements with top local vendors."
                ),
                "impact_score": 8.5,
            },
        },
        {
            "id": "disc-zepto",
            "name": "Zepto",
            "industry": "Quick Commerce",
            "website": "https://zepto.com",
            "market_scope": "National",
            "signals": [
                {
                    "signal_type": "Funding",
                    "source": "TechCrunch",
                    "title": "Zepto raises $340M Series E at $3.5B valuation",
                    "description": (
                        "Nexus Venture Partners led a $340M Series E. Funds earmarked "
                        "for expanding dark store network from 350 to 700 locations."
                    ),
                    "impact_score": 9.0,
                    "urgency_score": 8.0,
                    "tags": ["funding"],
                },
                {
                    "signal_type": "Product",
                    "source": "Twitter/X",
                    "title": "Zepto Pass subscription launches at ₹99/month",
                    "description": (
                        "Zepto Pass offers free delivery + 5% cashback on all orders. "
                        "Early adopter numbers exceeded 100k users in 72 hours."
                    ),
                    "impact_score": 7.8,
                    "urgency_score": 7.0,
                    "tags": ["feature positioning", "pricing"],
                },
                {
                    "signal_type": "Marketing",
                    "source": "App Annie",
                    "title": "Zepto student discount campaign — 20% off first 5 orders",
                    "description": (
                        "Targeted campaign via college WhatsApp groups in Mumbai. "
                        "Download rank jumped from #14 to #3 in student demographics."
                    ),
                    "impact_score": 6.8,
                    "urgency_score": 5.5,
                    "tags": ["ad campaign", "copy change"],
                },
                {
                    "signal_type": "Hiring",
                    "source": "LinkedIn Jobs",
                    "title": "Zepto opens 45 roles across tech, product, ops",
                    "description": (
                        "Major push in ML engineering and supply-chain product management "
                        "signals heavy investment in demand forecasting and routing."
                    ),
                    "impact_score": 7.0,
                    "urgency_score": 6.0,
                    "tags": ["hiring"],
                },
                {
                    "signal_type": "Expansion",
                    "source": "Company Blog",
                    "title": "Zepto pilots B2B grocery vertical for restaurants",
                    "description": (
                        "Zepto quietly launched a B2B bulk-ordering pilot in Bangalore "
                        "targeting restaurants and small food businesses."
                    ),
                    "impact_score": 7.5,
                    "urgency_score": 6.8,
                    "tags": ["product expansion"],
                },
            ],
            "prediction": {
                "prediction": (
                    "Zepto will use Series E capital to enter 8-10 new cities "
                    "and push Zepto Pass to 1M subscribers within 90 days."
                ),
                "confidence": 85,
                "threat_level": "high",
                "ai_reasoning": (
                    "Funding rounds historically precede aggressive expansion at Zepto. "
                    "Zepto Pass shows customer retention is now the strategic priority."
                ),
            },
            "warroom": {
                "threat_summary": (
                    "🟠 HIGH: Zepto's $340M raise is a 6-month competitive threat timer. "
                    "Zepto Pass and the student campaign indicate they are targeting "
                    "your highest-LTV customer segments with precision."
                ),
                "recommended_actions": (
                    "1. Counter Zepto Pass with your own loyalty program at ₹79/month.\n"
                    "2. Engage college campus brand ambassadors before Zepto does.\n"
                    "3. Monitor Zepto's B2B pilot — pivot your B2B offering if it gains traction.\n"
                    "4. Prepare a 'lock-in' retention offer for your top 20% customers."
                ),
                "impact_score": 7.8,
            },
        },
        {
            "id": "disc-swiggy",
            "name": "Swiggy Instamart",
            "industry": "Quick Commerce",
            "website": "https://swiggy.com",
            "market_scope": "National",
            "signals": [
                {
                    "signal_type": "Leadership",
                    "source": "LinkedIn",
                    "title": "Swiggy hires Amazon VP to lead Instamart platform",
                    "description": (
                        "New VP of Engineering from Amazon brings supply-chain ML expertise. "
                        "Signals major Instamart platform rebuild is underway."
                    ),
                    "impact_score": 7.5,
                    "urgency_score": 6.0,
                    "tags": ["hiring"],
                },
                {
                    "signal_type": "Marketing",
                    "source": "SensorTower",
                    "title": "Swiggy Instamart ad spend +25% in Bangalore",
                    "description": (
                        "Digital and OOH advertising spend increased 25% in Bangalore. "
                        "New creatives focus on 'guaranteed 10-minute delivery' messaging."
                    ),
                    "impact_score": 6.5,
                    "urgency_score": 5.8,
                    "tags": ["ad campaign", "copy change", "feature positioning"],
                },
                {
                    "signal_type": "Marketing",
                    "source": "App Analysis",
                    "title": "Swiggy cuts delivery fees in Tier-2 to match Blinkit",
                    "description": (
                        "Delivery fee reduced from ₹25 to ₹9 in Jaipur, Lucknow, Indore. "
                        "Defensive pricing move to hold market share against Blinkit."
                    ),
                    "impact_score": 6.0,
                    "urgency_score": 4.5,
                    "tags": ["pricing"],
                },
                {
                    "signal_type": "Product",
                    "source": "Swiggy Blog",
                    "title": "Swiggy Instamart introduces AI-powered substitutions",
                    "description": (
                        "New feature suggests similar in-stock items when ordered items "
                        "are unavailable, reducing cancellations by an estimated 18%."
                    ),
                    "impact_score": 6.2,
                    "urgency_score": 4.8,
                    "tags": ["feature positioning", "product expansion"],
                },
                {
                    "signal_type": "Expansion",
                    "source": "Press",
                    "title": "Swiggy opens 50 new dark stores in Metro suburbs",
                    "description": (
                        "50 new dark stores opened across Delhi-NCR, Mumbai, and Bangalore "
                        "suburbs to cover underserved pin codes."
                    ),
                    "impact_score": 7.8,
                    "urgency_score": 7.0,
                    "tags": ["expansion", "product expansion"],
                },
            ],
            "prediction": {
                "prediction": (
                    "Swiggy will focus on deepening Instamart in existing metros "
                    "rather than new city launches for the next 6 months."
                ),
                "confidence": 70,
                "threat_level": "medium",
                "ai_reasoning": (
                    "Amazon VP hire signals platform investment, not expansion. "
                    "Fee cuts in Tier-2 are defensive, not offensive. "
                    "Expect strong metro competition but limited new market entry."
                ),
            },
            "warroom": {
                "threat_summary": (
                    "🟡 MEDIUM: Swiggy is playing defence in existing markets while "
                    "hardening its platform. The Amazon VP hire is a 6-month forward "
                    "threat — expect a materially improved product experience by Q4."
                ),
                "recommended_actions": (
                    "1. Compete on delivery speed in metros — sub-10-minute SLA.\n"
                    "2. Match or beat Swiggy's Tier-2 delivery fee reduction.\n"
                    "3. Track Instamart's AI substitution rollout and clone the feature.\n"
                    "4. Intensify dark store coverage in their suburban gaps."
                ),
                "impact_score": 6.5,
            },
        },
    ],
    # Default fallback for any company not matched by keyword
    "default": [
        {
            "id": "disc-rival-alpha",
            "name": "Rival Alpha",
            "industry": "Technology",
            "website": "https://rival-alpha.com",
            "market_scope": "National",
            "signals": [
                {
                    "signal_type": "Hiring",
                    "source": "LinkedIn",
                    "title": "Rival Alpha hiring 30 engineers across ML and product",
                    "description": "Major engineering headcount push signals product acceleration.",
                    "impact_score": 7.5,
                    "urgency_score": 6.5,
                    "tags": ["hiring"],
                },
                {
                    "signal_type": "Marketing",
                    "source": "SimilarWeb",
                    "title": "Rival Alpha ad spend up 35% on Google Ads",
                    "description": "Aggressive paid search investment targeting your core keywords.",
                    "impact_score": 7.0,
                    "urgency_score": 6.0,
                    "tags": ["ad campaign", "copy change"],
                },
                {
                    "signal_type": "Product",
                    "source": "ProductHunt",
                    "title": "Rival Alpha launches v2.0 with AI-native features",
                    "description": "Version 2.0 ships with GPT-powered features your roadmap doesn't cover yet.",
                    "impact_score": 8.0,
                    "urgency_score": 7.5,
                    "tags": ["feature positioning", "product expansion"],
                },
                {
                    "signal_type": "Funding",
                    "source": "Crunchbase",
                    "title": "Rival Alpha closes $50M Series B",
                    "description": "Sequoia-led round with 24-month runway. Expect aggressive hiring and marketing.",
                    "impact_score": 8.5,
                    "urgency_score": 7.0,
                    "tags": ["funding"],
                },
                {
                    "signal_type": "Expansion",
                    "source": "Press",
                    "title": "Rival Alpha expands to Southeast Asian markets",
                    "description": "Singapore and Indonesia launches indicate global growth phase.",
                    "impact_score": 7.8,
                    "urgency_score": 6.8,
                    "tags": ["product expansion", "expansion"],
                },
            ],
            "prediction": {
                "prediction": "Rival Alpha will grow 3x in 12 months using Series B capital for market expansion.",
                "confidence": 78,
                "threat_level": "high",
                "ai_reasoning": "Funding + hiring + product launch = classic growth acceleration pattern.",
            },
            "warroom": {
                "threat_summary": "🔴 HIGH: Rival Alpha is in a funded acceleration phase. Their AI-native v2.0 directly challenges your core offering.",
                "recommended_actions": (
                    "1. Ship your own AI feature set within 60 days.\n"
                    "2. Lock in enterprise contracts before Rival Alpha enters your accounts.\n"
                    "3. Defend your top keyword positions with increased SEM budget.\n"
                    "4. Brief your sales team on competitive objection handling for Rival Alpha."
                ),
                "impact_score": 8.0,
            },
        },
        {
            "id": "disc-rival-beta",
            "name": "Rival Beta",
            "industry": "Technology",
            "website": "https://rival-beta.com",
            "market_scope": "National",
            "signals": [
                {
                    "signal_type": "Marketing",
                    "source": "SpyFu",
                    "title": "Rival Beta launches aggressive comparison ad campaign",
                    "description": "New ads directly compare against your product on pricing.",
                    "impact_score": 7.2,
                    "urgency_score": 6.8,
                    "tags": ["ad campaign", "copy change", "pricing"],
                },
                {
                    "signal_type": "Product",
                    "source": "G2 Reviews",
                    "title": "Rival Beta ships integrations with Salesforce and HubSpot",
                    "description": "Native CRM integrations dramatically expand their enterprise appeal.",
                    "impact_score": 7.5,
                    "urgency_score": 6.5,
                    "tags": ["feature positioning"],
                },
                {
                    "signal_type": "Hiring",
                    "source": "LinkedIn",
                    "title": "Rival Beta adds enterprise sales team of 15 AEs",
                    "description": "Going upmarket — 15 enterprise AE hires indicates ICP shift.",
                    "impact_score": 7.0,
                    "urgency_score": 5.5,
                    "tags": ["hiring"],
                },
                {
                    "signal_type": "Expansion",
                    "source": "Blog",
                    "title": "Rival Beta opens London and Dubai offices",
                    "description": "International expansion with 2 new regional offices this quarter.",
                    "impact_score": 7.3,
                    "urgency_score": 6.0,
                    "tags": ["expansion"],
                },
                {
                    "signal_type": "Sentiment",
                    "source": "Twitter/X",
                    "title": "Rival Beta NPS drops 12 points after price hike",
                    "description": "Customer backlash on social media following 20% annual plan increase.",
                    "impact_score": 5.5,
                    "urgency_score": 4.0,
                    "tags": ["pricing"],
                },
            ],
            "prediction": {
                "prediction": "Rival Beta's price hike creates a 90-day churn window — target their dissatisfied customers.",
                "confidence": 76,
                "threat_level": "medium",
                "ai_reasoning": "NPS drop + price hike = competitor vulnerability. Their enterprise pivot creates a gap in your shared SMB customer base.",
            },
            "warroom": {
                "threat_summary": "🟠 MEDIUM: Rival Beta is going upmarket while leaving SMB customers exposed. Their price hike is your acquisition opportunity.",
                "recommended_actions": (
                    "1. Launch a targeted campaign: 'Switch from Rival Beta — no price surprises'.\n"
                    "2. Contact Rival Beta's unhappy customers directly via G2 reviews.\n"
                    "3. Ship your Salesforce integration to neutralize their enterprise edge.\n"
                    "4. Monitor their enterprise move — if it succeeds, you may need to follow."
                ),
                "impact_score": 6.8,
            },
        },
        {
            "id": "disc-rival-gamma",
            "name": "Rival Gamma",
            "industry": "Technology",
            "website": "https://rival-gamma.com",
            "market_scope": "Regional",
            "signals": [
                {
                    "signal_type": "Marketing",
                    "source": "Facebook Ads Library",
                    "title": "Rival Gamma running 40+ active ad creatives",
                    "description": "High creative volume indicates aggressive A/B testing and budget allocation.",
                    "impact_score": 6.5,
                    "urgency_score": 5.8,
                    "tags": ["ad campaign", "copy change"],
                },
                {
                    "signal_type": "Product",
                    "source": "AppFollow",
                    "title": "Rival Gamma mobile app redesign ships — 4.8 stars",
                    "description": "Complete UX overhaul received 95% positive reviews. App store ranking improved 20 positions.",
                    "impact_score": 7.0,
                    "urgency_score": 6.2,
                    "tags": ["feature positioning"],
                },
                {
                    "signal_type": "Funding",
                    "source": "Crunchbase",
                    "title": "Rival Gamma raises $12M Seed from Y Combinator",
                    "description": "YC backing brings network effects, mentorship, and deal flow.",
                    "impact_score": 8.0,
                    "urgency_score": 7.2,
                    "tags": ["funding"],
                },
                {
                    "signal_type": "Hiring",
                    "source": "LinkedIn",
                    "title": "Rival Gamma hires ex-Google VP Product",
                    "description": "High-profile product leadership hire signals maturity and product-led growth focus.",
                    "impact_score": 7.8,
                    "urgency_score": 6.5,
                    "tags": ["hiring"],
                },
                {
                    "signal_type": "Expansion",
                    "source": "Website Changelog",
                    "title": "Rival Gamma adds Spanish and German language support",
                    "description": "Localisation push signals European market entry within 6 months.",
                    "impact_score": 6.8,
                    "urgency_score": 5.5,
                    "tags": ["product expansion"],
                },
            ],
            "prediction": {
                "prediction": "Rival Gamma will become a Tier-1 competitor within 18 months backed by YC network and ex-Google product leadership.",
                "confidence": 71,
                "threat_level": "medium",
                "ai_reasoning": "YC + ex-Google VP = credibility multiplier. Mobile app quality jump shows execution discipline.",
            },
            "warroom": {
                "threat_summary": "🟡 MEDIUM: Rival Gamma is an emerging threat — YC-backed with strong product DNA. Currently regional but well-positioned to scale nationally.",
                "recommended_actions": (
                    "1. Benchmark your mobile UX against Rival Gamma's new 4.8-star design.\n"
                    "2. Track their international expansion — prepare localisation strategy.\n"
                    "3. Consider acqui-hire or partnership conversations before they scale.\n"
                    "4. Monitor YC batch demo day for their growth trajectory data."
                ),
                "impact_score": 6.2,
            },
        },
    ],
}


def _resolve_competitor_template(company_name: str, website_url: str) -> list[dict]:
    """
    Resolve the best-match competitor template based on company name / website.
    Falls back to the generic 'default' template.
    """
    search_text = f"{company_name} {website_url}".lower()
    for pattern, templates in _COMPETITOR_TEMPLATES.items():
        if pattern == "default":
            continue
        keywords = pattern.split("|")
        if any(kw in search_text for kw in keywords):
            logger.info("Matched industry template: '%s'", pattern)
            return templates
    logger.info("No industry match found — using default template")
    return _COMPETITOR_TEMPLATES["default"]


async def discover_company_and_competitors(
    company_name: str,
    website_url: str,
) -> dict:
    """
    MVP ingestion pipeline:
      1. Resolves 3 contextually appropriate competitor templates.
      2. Upserts Competitor rows into the database.
      3. Seeds 5 Signals, 1 Prediction, and 1 WarRoom report per competitor.
      4. Returns a summary payload for the API response.

    Args:
        company_name: The name of the user's company.
        website_url:  The user's company website (used for keyword matching).

    Returns:
        dict with 'competitors_found', 'signals_seeded', 'status'.
    """
    from app.models.competitor import Competitor
    from app.models.signal import Signal, SignalCategory
    from app.models.prediction import Prediction
    from app.models.warroom import WarRoomReport
    from app.services.database import async_session_factory
    from sqlalchemy import select

    logger.info(
        "discover_company_and_competitors called for '%s' (%s)",
        company_name,
        website_url,
    )

    templates = _resolve_competitor_template(company_name, website_url)
    seeded_competitors = []
    total_signals = 0

    async with async_session_factory() as session:
        try:
            for tmpl in templates:
                comp_id = tmpl["id"]

                # ── Upsert competitor ────────────────────────────────────────
                existing = await session.execute(
                    select(Competitor).where(Competitor.id == comp_id)
                )
                competitor = existing.scalar_one_or_none()
                if not competitor:
                    competitor = Competitor(
                        id=comp_id,
                        name=tmpl["name"],
                        industry=tmpl["industry"],
                        website=tmpl["website"],
                        market_scope=tmpl["market_scope"],
                    )
                    session.add(competitor)
                    await session.flush()

                # ── Seed signals (skip if already present) ───────────────────
                existing_signals = await session.execute(
                    select(Signal).where(Signal.competitor_id == comp_id)
                )
                if not existing_signals.scalars().first():
                    for sig in tmpl["signals"]:
                        signal = Signal(
                            id=str(uuid.uuid4()),
                            competitor_id=comp_id,
                            signal_type=SignalCategory(sig["signal_type"]),
                            source=sig["source"],
                            title=sig["title"],
                            description=sig["description"],
                            impact_score=sig["impact_score"],
                            urgency_score=sig["urgency_score"],
                        )
                        session.add(signal)
                        total_signals += 1
                    await session.flush()

                # ── Seed prediction ──────────────────────────────────────────
                existing_pred = await session.execute(
                    select(Prediction).where(Prediction.competitor_id == comp_id)
                )
                if not existing_pred.scalars().first():
                    pred_data = tmpl["prediction"]
                    prediction = Prediction(
                        id=str(uuid.uuid4()),
                        competitor_id=comp_id,
                        prediction=pred_data["prediction"],
                        confidence=pred_data["confidence"],
                        threat_level=pred_data["threat_level"],
                        ai_reasoning=pred_data["ai_reasoning"],
                    )
                    session.add(prediction)
                    await session.flush()

                # ── Seed war room report ─────────────────────────────────────
                existing_report = await session.execute(
                    select(WarRoomReport).where(WarRoomReport.competitor_id == comp_id)
                )
                if not existing_report.scalars().first():
                    wr_data = tmpl["warroom"]
                    report = WarRoomReport(
                        id=str(uuid.uuid4()),
                        competitor_id=comp_id,
                        threat_summary=wr_data["threat_summary"],
                        recommended_actions=wr_data["recommended_actions"],
                        impact_score=wr_data["impact_score"],
                    )
                    session.add(report)
                    await session.flush()

                seeded_competitors.append(
                    {
                        "id": comp_id,
                        "name": tmpl["name"],
                        "industry": tmpl["industry"],
                        "website": tmpl["website"],
                        "threat_level": tmpl["prediction"]["threat_level"],
                    }
                )

            await session.commit()

        except Exception as exc:
            await session.rollback()
            logger.error("Discovery seeding failed: %s", exc)
            raise

    logger.info(
        "Discovery complete — %d competitors, %d signals seeded",
        len(seeded_competitors),
        total_signals,
    )

    return {
        "status": "ok",
        "company_name": company_name,
        "website_url": website_url,
        "competitors_found": len(seeded_competitors),
        "signals_seeded": total_signals,
        "competitors": seeded_competitors,
        "message": (
            f"War Room initialised with {len(seeded_competitors)} competitors "
            f"and {total_signals} intelligence signals."
        ),
    }
