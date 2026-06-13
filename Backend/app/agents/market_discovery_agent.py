"""MarketDiscoveryAgent — full 7-step competitive intelligence pipeline.

Runs as an asyncio background task (asyncio.create_task).
Updates discovery_jobs table with progress so the frontend can poll.

Steps:
  1  Scrape & enrich company profile
  2  Pass 1 — Claude direct competitor discovery (5 companies)
  3  Pass 2 — SerpAPI search-based discovery (5 more)
  4  Pass 3 — Validate & enrich all unique competitors
  5  Save validated competitors to Supabase
  6  Collect live signals for every saved competitor
  7  Finalize — summary + mark job complete
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

from app.core.supabase_client import (
    db_insert,
    db_insert_if_new,
    db_select,
    db_update,
    db_upsert,
)
from app.services.claude import (
    discover_competitors,
    enrich_company_profile,
    extract_new_competitors,
    generate_discovery_summary,
    validate_competitor,
)
from app.services.scraper import scrape_and_analyze
from app.agents.signal_hunter import serp_search, hunt_signals
from app.agents.dna_forge import forge_dna_profile

logger = logging.getLogger(__name__)

COLOR_PALETTE = [
    "#FF6B35", "#6C63FF", "#00D4FF", "#00FF88",
    "#FF3366", "#FFD700", "#9B59B6", "#1ABC9C",
    "#E67E22", "#3498DB",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_name(name: str) -> str:
    result = name.lower().strip()
    for suffix in (" inc.", " inc", " pvt ltd", " pvt. ltd.", " ltd.", " ltd",
                   " llc", " corp.", " corp", " corporation", " co.", " co"):
        if result.endswith(suffix):
            result = result[: -len(suffix)].strip()
    result = re.sub(r"[^\w\s]", "", result)
    return result.strip()


async def _update_job(job_id: str, **kwargs) -> None:
    try:
        await db_update("discovery_jobs", {"id": job_id}, {**kwargs, "updated_at": _now()})
    except Exception as exc:
        logger.warning("_update_job failed for %s: %s", job_id, exc)


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def run_discovery_pipeline(
    job_id: str,
    user_id: str,
    company_name: str,
    website: str | None,
    description: str,
) -> None:
    """Full 7-step discovery pipeline. Never raises — all errors go to the job row."""
    start = time.time()

    try:
        await _update_job(job_id, status="running", stage="Analyzing your company...", progress=5)

        # ── STEP 1 — Enrich company profile ──────────────────────────────────
        scraped = None
        if website:
            scraped = await scrape_and_analyze(website)

        enriched = await enrich_company_profile(company_name, website, description, scraped)

        await db_upsert(
            "company_profiles",
            {
                "user_id": user_id,
                "company_name": company_name,
                "website": website or "",
                "description": description,
                "industry": enriched.get("industry", ""),
                "sub_category": enriched.get("sub_category", ""),
                "key_features": enriched.get("key_features", []),
                "geographic_focus": enriched.get("geographic_focus", ""),
                "target_customers": enriched.get("target_customers", ""),
                "business_model": enriched.get("business_model", ""),
            },
            on_conflict="user_id",
        )

        industry = enriched.get("industry", "Technology")
        sub_category = enriched.get("sub_category", industry)
        geo = enriched.get("geographic_focus", "")
        key_features = enriched.get("key_features", [])

        await _update_job(job_id, stage="Analyzing your company...", progress=12)

        # ── STEP 2 — Pass 1: Claude direct discovery ──────────────────────────
        await _update_job(job_id, stage="Finding direct competitors...", progress=15)

        pass1 = await discover_competitors(company_name, industry, key_features, geo)
        pass1_names = [c["name"] for c in pass1 if c.get("name")]

        await _update_job(job_id, stage="Finding direct competitors...", progress=28)

        # ── STEP 3 — Pass 2: SerpAPI search discovery ─────────────────────────
        await _update_job(job_id, stage="Searching the web for hidden competitors...", progress=32)

        search_queries = [
            f"{name} alternatives {sub_category}" for name in pass1_names[:3]
        ] + [
            f"best {sub_category} companies {geo} 2025",
            f"top {sub_category} startups {geo}",
        ]

        serp_batches = await asyncio.gather(
            *[serp_search(q, num=5) for q in search_queries],
            return_exceptions=True,
        )

        serp_text_parts: list[str] = []
        for batch in serp_batches:
            if isinstance(batch, list):
                for r in batch:
                    serp_text_parts.append(f"{r.get('title', '')} {r.get('snippet', '')} ")

        serp_text = " ".join(serp_text_parts)[:8000]

        pass2_names: list[str] = []
        if serp_text.strip():
            try:
                pass2_names = await extract_new_competitors(
                    serp_text, company_name, pass1_names, sub_category
                )
            except Exception as exc:
                logger.warning("extract_new_competitors failed: %s", exc)

        await _update_job(job_id, stage="Searching the web for hidden competitors...", progress=48)

        # ── STEP 4 — Pass 3: Deduplicate + validate ───────────────────────────
        seen_norm: set[str] = set()
        unique: list[tuple[str, int]] = []  # (name, discovery_pass)

        for name in pass1_names:
            norm = _normalize_name(name)
            if norm and norm not in seen_norm:
                seen_norm.add(norm)
                unique.append((name, 1))

        for name in pass2_names:
            norm = _normalize_name(name)
            if norm and norm not in seen_norm:
                seen_norm.add(norm)
                unique.append((name, 2))

        n_total = len(unique)
        await _update_job(
            job_id,
            stage=f"Validating {n_total} companies found...",
            progress=52,
        )

        validated: list[dict] = []
        color_idx = 0

        for i, (name, disc_pass) in enumerate(unique):
            color = COLOR_PALETTE[color_idx % len(COLOR_PALETTE)]
            color_idx += 1
            try:
                # Try to resolve website via SerpAPI
                website_results = await serp_search(f"{name} official website", num=1)
                guessed_site = (
                    website_results[0].get("link", "") if website_results else ""
                )
                comp_data = await validate_competitor(
                    name, company_name, sub_category, geo, color, guessed_site
                )
            except Exception as exc:
                logger.warning("Validation failed for '%s': %s", name, exc)
                comp_data = {
                    "name": name,
                    "website": "",
                    "description": f"{name} is a competitor in {sub_category}.",
                    "threat_level": "MEDIUM",
                    "threat_reason": "Operates in the same market.",
                    "competitive_edge": "Established presence.",
                }

            comp_data["color_accent"] = color
            comp_data["discovery_pass"] = disc_pass
            validated.append(comp_data)

            progress = 52 + int((i + 1) / n_total * 18)
            await _update_job(
                job_id, stage=f"Validating {n_total} companies found...", progress=progress
            )

        await _update_job(job_id, stage=f"Validating {n_total} companies found...", progress=72)

        # ── STEP 5 — Save to Supabase ─────────────────────────────────────────
        await _update_job(job_id, stage="Saving discovered competitors...", progress=75)

        saved: list[dict] = []

        for comp_data in validated:
            raw_name = comp_data.get("name", "").strip()
            if not raw_name:
                continue
            norm_name = _normalize_name(raw_name)
            try:
                comp_row, created = await db_insert_if_new(
                    "competitors",
                    {
                        "user_id": user_id,
                        "name": raw_name,
                        "normalized_name": norm_name,
                        "website": comp_data.get("website") or "",
                        "industry": industry,
                        "color_accent": comp_data["color_accent"],
                        "is_active": True,
                    },
                    fetch_filters={"user_id": user_id, "normalized_name": norm_name},
                )

                if not comp_row or not comp_row.get("id"):
                    continue

                comp_id = comp_row["id"]

                # Upsert profile
                try:
                    await db_upsert(
                        "competitor_profiles",
                        {
                            "competitor_id": comp_id,
                            "description": comp_data.get("description", ""),
                            "threat_level": comp_data.get("threat_level", "MEDIUM"),
                            "threat_reason": comp_data.get("threat_reason", ""),
                            "competitive_edge": comp_data.get("competitive_edge", ""),
                            "discovery_pass": comp_data.get("discovery_pass", 1),
                        },
                        on_conflict="competitor_id",
                    )
                except Exception as exc:
                    logger.warning("competitor_profiles upsert failed for %s: %s", raw_name, exc)

                # Agent log
                try:
                    await db_insert(
                        "agent_logs",
                        {
                            "user_id": user_id,
                            "competitor_id": comp_id,
                            "agent_name": "DiscoveryAgent",
                            "action": f"{'Added' if created else 'Re-validated'} competitor: {raw_name}",
                            "reasoning": (
                                comp_data.get("threat_reason", "")
                                if comp_data.get("discovery_pass") == 1
                                else f"Found via web search — {comp_data.get('competitive_edge', '')}"
                            ),
                        },
                    )
                except Exception:
                    pass

                saved.append({**comp_row, **comp_data})

            except Exception as exc:
                logger.warning("Save failed for '%s': %s", raw_name, exc)

        await _update_job(job_id, stage="Saving discovered competitors...", progress=82)

        # ── STEP 6 — Collect live signals ─────────────────────────────────────
        await _update_job(
            job_id, stage="Collecting live signals from all sources...", progress=85
        )

        signal_tasks = [
            _hunt_and_save_signals(user_id, comp, industry)
            for comp in saved
        ]
        signal_counts = await asyncio.gather(*signal_tasks, return_exceptions=True)

        total_signals = 0
        for i, count in enumerate(signal_counts):
            n = count if isinstance(count, int) else 0
            total_signals += n
            if i < len(saved):
                saved[i]["signals_found"] = n

        await _update_job(
            job_id, stage="Collecting live signals from all sources...", progress=94
        )

        # ── STEP 7 — Finalize ─────────────────────────────────────────────────
        summary = await generate_discovery_summary(company_name, saved)

        elapsed = round(time.time() - start, 1)
        await _update_job(
            job_id,
            status="completed",
            stage="Discovery complete",
            progress=100,
            result={
                "company": enriched,
                "competitors_found": len(saved),
                "competitors": [
                    {
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "website": c.get("website"),
                        "color_accent": c.get("color_accent"),
                        "threat_level": c.get("threat_level"),
                        "signals_found": c.get("signals_found", 0),
                    }
                    for c in saved
                ],
                "discovery_summary": summary,
                "total_signals_collected": total_signals,
                "processing_time_seconds": elapsed,
            },
        )

        logger.info(
            "Discovery complete — user=%s, %.1fs, %d competitors, %d signals",
            user_id, elapsed, len(saved), total_signals,
        )

    except Exception as exc:
        logger.error("Discovery pipeline crashed for job=%s: %s", job_id, exc, exc_info=True)
        try:
            await db_update(
                "discovery_jobs",
                {"id": job_id},
                {
                    "status": "failed",
                    "error": str(exc)[:1000],
                    "updated_at": _now(),
                },
            )
        except Exception:
            pass


async def _hunt_and_save_signals(
    user_id: str,
    competitor: dict[str, Any],
    industry: str,
) -> int:
    """Hunt signals for one competitor, save to Supabase + ChromaDB. Returns count."""
    comp_id = competitor.get("id", "")
    comp_name = competitor.get("name", "")

    try:
        signals = await hunt_signals(
            competitor_name=comp_name,
            website=competitor.get("website"),
            industry=industry,
        )

        saved_count = 0
        saved_signals: list[dict] = []
        for s in signals:
            try:
                row = await db_insert(
                    "signals",
                    {
                        "user_id": user_id,
                        "competitor_id": comp_id,
                        "type": s.get("type", ""),
                        "title": s.get("title", ""),
                        "description": s.get("description", ""),
                        "source": s.get("source", ""),
                        "intent_score": s.get("intent_score", 0),
                        "meaning": s.get("meaning", ""),
                        "raw_data": s.get("raw_data", {}),
                        "is_war_room_trigger": s.get("is_war_room_trigger", False),
                    },
                )
                saved_signals.append({**s, "id": row.get("id", str(saved_count))})
                saved_count += 1
            except Exception as exc:
                logger.debug("Signal insert failed for %s: %s", comp_name, exc)

        # Vector store
        if saved_signals:
            try:
                from app.services.chromadb_service import add_signals
                await add_signals(comp_id, saved_signals)
            except Exception as exc:
                logger.debug("ChromaDB store failed for %s: %s", comp_name, exc)

        # DNA if enough signals
        if saved_count >= 5:
            try:
                profile = await forge_dna_profile(comp_id, comp_name, saved_signals)
                if profile:
                    await db_upsert(
                        "dna_profiles",
                        {
                            "competitor_id": comp_id,
                            "user_id": user_id,
                            **profile,
                        },
                        on_conflict="competitor_id",
                    )
                    await db_insert(
                        "agent_logs",
                        {
                            "user_id": user_id,
                            "competitor_id": comp_id,
                            "agent_name": "DNAForgeAgent",
                            "action": f"Built DNA profile for {comp_name}",
                            "reasoning": profile.get("behavioral_summary", ""),
                        },
                    )
            except Exception as exc:
                logger.warning("DNA build failed for %s: %s", comp_name, exc)

        return saved_count

    except Exception as exc:
        logger.error("_hunt_and_save_signals failed for '%s': %s", comp_name, exc)
        return 0
