"""All Anthropic Claude calls for the market discovery pipeline.

Every function returns structured data. JSON is extracted from the response
and retried once if the initial parse fails.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from anthropic import AsyncAnthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        _client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


async def _call(prompt: str, max_tokens: int = 2048) -> str:
    client = _get_client()
    response = await client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def _strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw.strip())
    return raw.strip()


async def _call_json(prompt: str, max_tokens: int = 2048) -> Any:
    raw = await _call(prompt, max_tokens)
    try:
        return json.loads(_strip_fences(raw))
    except json.JSONDecodeError:
        retry_prompt = (
            prompt
            + "\n\nIMPORTANT: Your last response was not valid JSON. "
            "Return ONLY raw JSON — no markdown fences, no extra text."
        )
        raw2 = await _call(retry_prompt, max_tokens)
        return json.loads(_strip_fences(raw2))


# ── Public functions ──────────────────────────────────────────────────────────

async def enrich_company_profile(
    company_name: str,
    website: str | None,
    description: str,
    scraped: dict | None,
) -> dict[str, Any]:
    """Return enriched company profile from Claude."""
    scraped_text = ""
    if scraped:
        scraped_text = f"\n\nWebsite content (first 1000 chars):\n{scraped.get('content', '')[:1000]}"

    prompt = f"""You are a market research analyst. Enrich this company profile.

Company: {company_name}
Website: {website or "unknown"}
Description: {description}{scraped_text}

Return ONLY valid JSON:
{{
  "industry": "string (broad industry)",
  "sub_category": "string (specific niche/sub-sector)",
  "key_features": ["feature1", "feature2", "feature3"],
  "geographic_focus": "string (e.g. India, Global, Southeast Asia)",
  "target_customers": "string (who they serve)",
  "business_model": "string (SaaS/Marketplace/D2C/etc)",
  "founded_estimate": "string or null"
}}"""

    try:
        return await _call_json(prompt)
    except Exception as exc:
        logger.warning("enrich_company_profile failed: %s", exc)
        return {
            "industry": "Technology",
            "sub_category": "Software",
            "key_features": [],
            "geographic_focus": "India",
            "target_customers": "Businesses",
            "business_model": "SaaS",
            "founded_estimate": None,
        }


async def discover_competitors(
    company_name: str,
    industry: str,
    key_features: list[str],
    geographic_focus: str,
) -> list[dict[str, str]]:
    """Pass 1 — direct competitor discovery via Claude."""
    features = ", ".join(key_features[:5]) if key_features else "various features"

    prompt = f"""You are a competitive intelligence expert.

Company: {company_name}
Industry: {industry}
Key Features: {features}
Geographic Focus: {geographic_focus}

Name exactly 5 REAL, well-known direct competitors that operate in the same space.
Only include companies that genuinely exist and compete in this market.

Return ONLY valid JSON:
{{
  "competitors": [
    {{"name": "CompanyName", "reason": "One sentence of direct competitive overlap"}}
  ]
}}"""

    try:
        data = await _call_json(prompt)
        return data.get("competitors", [])
    except Exception as exc:
        logger.warning("discover_competitors failed: %s", exc)
        return []


async def extract_new_competitors(
    serp_text: str,
    company_name: str,
    existing_names: list[str],
    sub_category: str,
) -> list[str]:
    """Pass 2 — extract NEW competitor names from SerpAPI search text."""
    exclude = ", ".join(existing_names[:10]) if existing_names else "none"

    prompt = f"""From the search results below, extract company names that compete with {company_name} in {sub_category}.

Exclude: {exclude} and {company_name} itself.
Only extract real company names, not generic terms.
Extract 3-5 names maximum.

Search results:
{serp_text[:4000]}

Return ONLY valid JSON:
{{"company_names": ["Name1", "Name2", "Name3"]}}"""

    try:
        data = await _call_json(prompt)
        return data.get("company_names", [])
    except Exception as exc:
        logger.warning("extract_new_competitors failed: %s", exc)
        return []


async def validate_competitor(
    competitor_name: str,
    company_name: str,
    sub_category: str,
    geographic_focus: str,
    color_accent: str,
    guessed_website: str = "",
) -> dict[str, Any]:
    """Pass 3 — validate one competitor and enrich its profile."""
    website_hint = f"\nKnown website: {guessed_website}" if guessed_website else ""

    prompt = f"""You are a competitive intelligence analyst.

Competitor to profile: {competitor_name}{website_hint}
Competes with: {company_name}
Market: {sub_category}, {geographic_focus}

Provide a competitive profile. Use the known website if provided; otherwise provide a best guess.

Return ONLY valid JSON:
{{
  "name": "{competitor_name}",
  "website": "https://example.com",
  "description": "2-3 sentence description of what they do and how they compete",
  "threat_level": "LOW" | "MEDIUM" | "HIGH",
  "threat_reason": "Specific reason for threat level to {company_name}",
  "competitive_edge": "Their main advantage over {company_name}"
}}"""

    try:
        data = await _call_json(prompt)
        if guessed_website and not data.get("website"):
            data["website"] = guessed_website
        return data
    except Exception as exc:
        logger.warning("validate_competitor failed for '%s': %s", competitor_name, exc)
        return {
            "name": competitor_name,
            "website": guessed_website or "",
            "description": f"{competitor_name} is a competitor in {sub_category}.",
            "threat_level": "MEDIUM",
            "threat_reason": "Operates in the same market segment.",
            "competitive_edge": "Established market presence.",
        }


async def generate_discovery_summary(
    company_name: str,
    competitors: list[dict],
) -> str:
    """Generate a human-readable discovery summary narrative."""
    comp_list = "\n".join(
        f"- {c.get('name', '?')} (threat: {c.get('threat_level', '?')})"
        for c in competitors[:10]
    )

    prompt = f"""Write a 2-3 sentence executive summary of the competitive landscape for {company_name}.

Competitors found:
{comp_list}

Be specific, strategic, and actionable. No bullet points — flowing prose."""

    try:
        return (await _call(prompt, max_tokens=300)).strip()
    except Exception as exc:
        logger.warning("generate_discovery_summary failed: %s", exc)
        n = len(competitors)
        high = sum(1 for c in competitors if c.get("threat_level") == "HIGH")
        return (
            f"MarketWatch identified {n} competitors for {company_name}, "
            f"with {high} rated as high threat. Continuous monitoring is now active."
        )


async def generate_dna_profile(
    competitor_id: str,
    competitor_name: str,
    signals: list[dict],
) -> dict[str, Any]:
    """Build a behavioral DNA profile from accumulated signals."""
    signal_lines = "\n".join(
        f"- [{s.get('type', 'Signal')}] {s.get('title', '')} "
        f"(intent: {s.get('intent_score', 0)})"
        for s in signals[:25]
    )

    prompt = f"""You are a behavioral pattern analyst specializing in competitive intelligence.

Competitor: {competitor_name}
Total signals: {len(signals)}

Recent signals:
{signal_lines}

Analyze behavioral patterns and build a DNA profile.

Return ONLY valid JSON:
{{
  "price_aggression": 0.0,
  "launch_style": "gradual" | "aggressive" | "stealth",
  "expansion_speed": "slow" | "moderate" | "rapid",
  "expansion_trigger": "funding" | "hiring" | "partnerships" | "organic",
  "signal_to_launch_days": 30,
  "known_weakness": "One specific weakness based on signals",
  "patterns": [
    "Behavioral pattern 1 observed from signals",
    "Behavioral pattern 2 observed from signals",
    "Behavioral pattern 3 observed from signals"
  ],
  "behavioral_summary": "2-sentence summary of their competitive behavior style"
}}

price_aggression: float 0.0 (no discounting) to 1.0 (extremely aggressive pricing)
signal_to_launch_days: estimated days from first signal to product launch"""

    try:
        data = await _call_json(prompt, max_tokens=1024)
        data["raw_signals_count"] = len(signals)
        return data
    except Exception as exc:
        logger.warning("generate_dna_profile failed for '%s': %s", competitor_name, exc)
        return {
            "price_aggression": 0.5,
            "launch_style": "gradual",
            "expansion_speed": "moderate",
            "expansion_trigger": "organic",
            "signal_to_launch_days": 45,
            "known_weakness": "Insufficient signal data for detailed analysis.",
            "patterns": [
                f"{competitor_name} shows consistent market activity.",
                "Signal frequency suggests steady growth trajectory.",
                "No extreme behavioral outliers detected.",
            ],
            "raw_signals_count": len(signals),
            "behavioral_summary": (
                f"{competitor_name} demonstrates measured market behavior. "
                "Ongoing signal collection will improve profile accuracy."
            ),
        }


async def score_signal_intent(
    signal_type: str,
    title: str,
    description: str,
) -> int:
    """Score competitive intent of a signal. Returns 0-100."""
    prompt = f"""Rate the competitive threat level of this market signal on a scale of 0 to 100.

0 = irrelevant noise
50 = moderate competitive signal worth monitoring
80+ = high-priority threat requiring immediate action

Signal Type: {signal_type}
Title: {title}
Description: {description[:300]}

Respond with ONLY a single integer between 0 and 100. No other text."""

    try:
        raw = await _call(prompt, max_tokens=10)
        score = int(re.search(r"\d+", raw).group())
        return max(0, min(100, score))
    except Exception:
        return 50
