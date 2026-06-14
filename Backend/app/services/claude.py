"""AI calls for the market discovery pipeline.

Routes through the configured AI provider (Groq, OpenRouter, Anthropic, Ollama)
via get_ai_provider(). Every function returns structured data. JSON is
extracted from the response and retried once if the initial parse fails.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.ai_provider import get_ai_provider

logger = logging.getLogger(__name__)


async def _call(prompt: str) -> str:
    provider = get_ai_provider()
    return await provider.generate(prompt)


def _strip_fences(raw: str) -> str:
    """Strip markdown fences AND <think>...</think> blocks (Gemma/DeepSeek thinking mode)."""
    raw = raw.strip()

    # Remove <think>...</think> blocks produced by reasoning models
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

    # Remove markdown code fences
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw.strip())

    return raw.strip()


def _extract_json(raw: str) -> Any:
    """Extract JSON from raw text — tries full parse first, then finds outermost {} or []."""
    cleaned = _strip_fences(raw)

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to pull the first { ... } block
    brace = cleaned.find("{")
    if brace != -1:
        depth = 0
        for i, ch in enumerate(cleaned[brace:], start=brace):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(cleaned[brace : i + 1])
                    except json.JSONDecodeError:
                        break

    # Try to pull the first [ ... ] block
    bracket = cleaned.find("[")
    if bracket != -1:
        depth = 0
        for i, ch in enumerate(cleaned[bracket:], start=bracket):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(cleaned[bracket : i + 1])
                    except json.JSONDecodeError:
                        break

    raise json.JSONDecodeError("No valid JSON found in response", cleaned, 0)


async def _call_json(prompt: str) -> Any:
    raw = await _call(prompt)
    try:
        return _extract_json(raw)
    except json.JSONDecodeError:
        retry_prompt = (
            prompt
            + "\n\nIMPORTANT: Your previous response was not valid JSON. "
            "Return ONLY raw JSON — no markdown fences, no <think> blocks, no extra text."
        )
        raw2 = await _call(retry_prompt)
        return _extract_json(raw2)


# ── Placeholder-name guard ────────────────────────────────────────────────────

_PLACEHOLDER_PATTERNS = re.compile(
    r"^(rival|competitor|company|brand|player|startup|firm|vendor)\s*"
    r"(alpha|beta|gamma|delta|a|b|c|d|x|y|z|\d+)$",
    re.IGNORECASE,
)

def _is_fake_name(name: str) -> bool:
    """Return True if the name looks like an AI-generated placeholder."""
    n = name.strip()
    if not n or len(n) < 2:
        return True
    if _PLACEHOLDER_PATTERNS.match(n):
        return True
    # Single generic word with no real-company feel
    generic = {"unknown", "n/a", "none", "tbd", "placeholder", "example", "test"}
    if n.lower() in generic:
        return True
    return False


def _filter_real_competitors(competitors: list[dict]) -> list[dict]:
    real = [c for c in competitors if not _is_fake_name(c.get("name", ""))]
    removed = len(competitors) - len(real)
    if removed:
        logger.warning(
            "Filtered %d placeholder/fake competitor names: %s",
            removed,
            [c.get("name") for c in competitors if _is_fake_name(c.get("name", ""))],
        )
    return real


# ── Public functions ──────────────────────────────────────────────────────────

async def enrich_company_profile(
    company_name: str,
    website: str | None,
    description: str,
    scraped: dict | None,
) -> dict[str, Any]:
    """Return enriched company profile from AI."""
    # Use up to 2000 chars of scraped content for better context
    scraped_text = ""
    if scraped:
        content = scraped.get("content", "")[:2000]
        title = scraped.get("title", "")
        meta = scraped.get("meta_description", "")
        scraped_text = f"\n\nWebsite title: {title}\nMeta description: {meta}\nPage content:\n{content}"

    prompt = f"""You are a market research analyst. Analyze this company and return a structured profile.

Company Name: {company_name}
Website: {website or "unknown"}
Description: {description}{scraped_text}

Based on the above information, identify:
- The EXACT industry this company operates in (e.g. "Ed-Tech", "Quick Commerce", "FinTech", "SaaS", etc.)
- The specific sub-category/niche
- Their key product features
- Their target customers
- Their geographic focus

Return ONLY valid JSON with no extra text:
{{
  "industry": "specific industry name",
  "sub_category": "specific niche within that industry",
  "key_features": ["feature1", "feature2", "feature3"],
  "geographic_focus": "e.g. India, Global, Southeast Asia",
  "target_customers": "who they serve (e.g. 'engineering students in India')",
  "business_model": "SaaS/Marketplace/D2C/B2C/etc",
  "founded_estimate": "year or null"
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
    website: str,
    industry: str,
    sub_category: str,
    key_features: list[str],
    geographic_focus: str,
    target_customers: str,
    description: str,
) -> list[dict[str, str]]:
    """Discover 5 real direct competitors using full company context."""
    features = ", ".join(key_features[:5]) if key_features else "not specified"

    prompt = f"""You are a competitive intelligence expert specializing in {industry}.

I need you to find the TOP 5 DIRECT competitors of "{company_name}".

COMPANY PROFILE:
- Name: {company_name}
- Website: {website}
- Industry: {industry}
- Specific Category: {sub_category}
- What they do: {description[:400]}
- Key features: {features}
- Target customers: {target_customers}
- Geographic focus: {geographic_focus}

STRICT RULES:
1. Competitors MUST be in the EXACT same category: {sub_category}
2. Competitors MUST target the SAME customers: {target_customers}
3. Competitors MUST operate in the SAME geography: {geographic_focus}
4. Only include REAL companies with verifiable websites — no made-up names
5. Do NOT include {company_name} itself
6. Do NOT include companies from unrelated industries
7. NEVER use placeholder names like "Rival Alpha", "Competitor A", "Brand X", "Player 1", etc.

Example: If the company is an ed-tech coding bootcamp, return OTHER ed-tech coding bootcamps — NOT grocery apps, food delivery, or unrelated software.

Return ONLY valid JSON with no extra text:
{{
  "competitors": [
    {{
      "name": "ExactCompanyName",
      "website": "https://their-website.com",
      "reason": "1-2 sentences: exactly how they directly compete with {company_name}"
    }}
  ]
}}"""

    try:
        data = await _call_json(prompt)
        competitors = data.get("competitors", [])
        competitors = _filter_real_competitors(competitors)
        logger.info("discover_competitors returned %d real results", len(competitors))
        return competitors
    except Exception as exc:
        logger.warning("discover_competitors failed: %s", exc)
        return []


async def recheck_competitors(
    competitors: list[dict],
    company_name: str,
    industry: str,
    sub_category: str,
    target_customers: str,
    description: str,
) -> list[dict]:
    """
    Validation layer — audits discovered competitors and rejects any that are
    not genuinely in the same industry/category as the target company.
    """
    if not competitors:
        return []

    comp_list = "\n".join(
        f"{i + 1}. {c.get('name', '?')} — {c.get('reason', c.get('description', 'no details'))}"
        for i, c in enumerate(competitors)
    )

    prompt = f"""You are a strict competitive intelligence auditor. Your job is to VERIFY or REJECT each proposed competitor.

COMPANY BEING RESEARCHED:
- Name: {company_name}
- What they do: {description[:300]}
- Exact industry category: {sub_category}
- Target customers: {target_customers}

PROPOSED COMPETITORS (verify each one):
{comp_list}

For EACH proposed competitor, decide:
- KEEP: it genuinely competes with {company_name} in {sub_category} for the same customers
- REJECT: it is from a different industry, targets different customers, or is clearly wrong

Be STRICT. If a company like "Swiggy" or "Zepto" (grocery delivery) appears when the company is an ed-tech firm, REJECT it.
If a company like "Coursera" appears when the company sells car insurance, REJECT it.

Return ONLY valid JSON:
{{
  "results": [
    {{
      "name": "CompanyName",
      "decision": "KEEP",
      "reason": "one sentence justification"
    }}
  ]
}}"""

    try:
        data = await _call_json(prompt)
        results = data.get("results", [])

        kept_names = {r["name"].lower() for r in results if r.get("decision") == "KEEP"}
        rejected = [r for r in results if r.get("decision") == "REJECT"]

        if rejected:
            logger.warning(
                "Recheck REJECTED %d competitors: %s",
                len(rejected),
                [r["name"] for r in rejected],
            )

        filtered = [c for c in competitors if c.get("name", "").lower() in kept_names]
        logger.info(
            "Recheck kept %d / %d competitors",
            len(filtered), len(competitors),
        )
        return filtered

    except Exception as exc:
        logger.warning("recheck_competitors failed: %s — returning unfiltered list", exc)
        return competitors


async def extract_new_competitors(
    serp_text: str,
    company_name: str,
    existing_names: list[str],
    sub_category: str,
) -> list[str]:
    """Extract NEW competitor names from SerpAPI search results."""
    exclude = ", ".join(existing_names[:10]) if existing_names else "none"

    prompt = f"""From the search results below, extract company names that are DIRECT competitors of {company_name} in {sub_category}.

Rules:
- Exclude: {exclude} and {company_name} itself
- Only real company names (not generic terms)
- Only companies in the SAME category as {company_name}: {sub_category}
- Extract 3-5 names maximum

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
    """Enrich and validate one competitor's full profile."""
    website_hint = f"\nKnown website: {guessed_website}" if guessed_website else ""

    prompt = f"""You are a competitive intelligence analyst.

Competitor to profile: {competitor_name}{website_hint}
This company competes with: {company_name}
Market category: {sub_category}, {geographic_focus}

Provide a structured competitive profile for {competitor_name}.

Return ONLY valid JSON:
{{
  "name": "{competitor_name}",
  "website": "https://their-actual-website.com",
  "description": "2-3 sentences: what they do and how they compete with {company_name}",
  "threat_level": "LOW",
  "threat_reason": "specific reason for threat level to {company_name}",
  "competitive_edge": "their main advantage over {company_name}"
}}

threat_level must be exactly one of: "LOW", "MEDIUM", "HIGH" """

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
            "description": f"{competitor_name} competes in the {sub_category} space.",
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
        return (await _call(prompt)).strip()
    except Exception as exc:
        logger.warning("generate_discovery_summary failed: %s", exc)
        n = len(competitors)
        high = sum(1 for c in competitors if str(c.get("threat_level", "")).upper() == "HIGH")
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
        f"- [{s.get('type', 'Signal')}] {s.get('title', '')} (intent: {s.get('intent_score', 0)})"
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
  "launch_style": "gradual",
  "expansion_speed": "moderate",
  "expansion_trigger": "organic",
  "signal_to_launch_days": 45,
  "known_weakness": "one specific weakness based on signals",
  "patterns": [
    "behavioral pattern 1 from signals",
    "behavioral pattern 2 from signals",
    "behavioral pattern 3 from signals"
  ],
  "behavioral_summary": "2-sentence summary of their competitive behavior"
}}

price_aggression: float 0.0 (no discounting) to 1.0 (extremely aggressive)
launch_style must be: "gradual", "aggressive", or "stealth"
expansion_speed must be: "slow", "moderate", or "rapid"
expansion_trigger must be: "funding", "hiring", "partnerships", or "organic" """

    try:
        data = await _call_json(prompt)
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
