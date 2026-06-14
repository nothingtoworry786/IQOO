"""AI agent execution, activity, and chat API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.agents.marketing import MarketingAgent
from app.agents.product import ProductAgent
from app.agents.sales import SalesAgent
from app.agents.strategy import StrategyAgent
from app.core.ai_provider import get_ai_provider
from app.providers.base import AIProviderError
from app.services.search_tool import research, format_search_results

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents", tags=["AI Agents"])

# Agent registry — maps agent names to instances
_agents: dict[str, Any] = {
    "marketing": MarketingAgent(),
    "product": ProductAgent(),
    "sales": SalesAgent(),
    "strategy": StrategyAgent(),
}


@router.get("/", response_model=list[dict])
async def list_agents() -> list[dict]:
    """List all available AI agents and their descriptions."""
    return [
        {
            "name": name,
            "description": agent.description,
            "status": "ready",
        }
        for name, agent in _agents.items()
    ]


@router.post("/{agent_name}/analyze", response_model=dict)
async def run_agent(agent_name: str, context: str) -> dict:
    """Run a specific AI agent against a given context string.

    Args:
        agent_name: One of 'marketing', 'product', 'sales', 'strategy'.
        context: The market / competitor context to analyse.

    Returns:
        The agent's structured analysis result.
    """
    agent = _agents.get(agent_name.lower())
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent '{agent_name}'. Available: {', '.join(_agents.keys())}",
        )
    result = await agent.analyze(context)
    return result.to_dict()


# ---------------------------------------------------------------------------
# Research Agent Chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    competitor_id: str | None = Field(None)


class ChatResponse(BaseModel):
    reply: str
    model_used: str = "unknown"
    sources_used: int = 0


async def _load_db_context(competitor_id: str | None) -> str:
    """Pull tracked competitors + recent signals from DB for AI context."""
    try:
        from app.models.competitor import Competitor
        from app.models.signal import Signal
        from app.models.prediction import Prediction
        from app.services.database import async_session_factory
        from sqlalchemy import select, desc

        async with async_session_factory() as session:
            # Competitors
            comp_rows = (await session.execute(select(Competitor).limit(10))).scalars().all()
            if not comp_rows:
                return "No competitors are currently tracked in the database."

            comp_names = [c.name for c in comp_rows]
            lines = [f"TRACKED COMPETITORS: {', '.join(comp_names)}\n"]

            # Recent signals
            sig_q = select(Signal).order_by(desc(Signal.created_at)).limit(20)
            if competitor_id:
                sig_q = sig_q.where(Signal.competitor_id == competitor_id)
            signals = (await session.execute(sig_q)).scalars().all()

            if signals:
                lines.append("RECENT INTELLIGENCE SIGNALS:")
                for s in signals[:10]:
                    comp = next((c for c in comp_rows if c.id == s.competitor_id), None)
                    comp_name = comp.name if comp else "Unknown"
                    lines.append(
                        f"  [{s.signal_type.value}] {comp_name}: {s.title} "
                        f"(impact {s.impact_score:.1f}/10)"
                    )

            # Latest predictions
            pred_rows = (
                await session.execute(
                    select(Prediction).order_by(desc(Prediction.created_at)).limit(5)
                )
            ).scalars().all()
            if pred_rows:
                lines.append("\nLATEST PREDICTIONS:")
                for p in pred_rows:
                    comp = next((c for c in comp_rows if c.id == p.competitor_id), None)
                    comp_name = comp.name if comp else "Unknown"
                    lines.append(f"  {comp_name} [{p.threat_level}]: {p.prediction}")

        return "\n".join(lines)

    except Exception as exc:
        logger.warning("_load_db_context failed: %s", exc)
        return "Database context unavailable."


async def _build_search_queries(question: str, db_context: str, provider: Any) -> list[str]:
    """Ask the AI to generate 1-2 targeted search queries for the question."""
    prompt = (
        f"You are a search query generator for a competitive intelligence tool.\n\n"
        f"User question: {question}\n\n"
        f"Tracked competitors context:\n{db_context[:500]}\n\n"
        f"Generate 1-2 precise Google search queries that would find current, relevant information "
        f"to answer this question. Focus on recent news, data, or events.\n\n"
        f"Return ONLY a JSON object like: {{\"queries\": [\"query 1\", \"query 2\"]}}"
    )
    try:
        import json
        import re
        raw = await provider.generate(prompt)
        # Strip thinking blocks
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Extract JSON
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            queries = data.get("queries", [])
            return [q for q in queries if isinstance(q, str) and q.strip()][:2]
    except Exception as exc:
        logger.debug("_build_search_queries failed: %s", exc)
    # Fallback: use the question directly
    return [question]


@router.post("/chat", response_model=ChatResponse, summary="Research agent — answers questions with live web search + DB context")
async def chat_with_ai(data: ChatRequest) -> ChatResponse:
    """
    Research agent pipeline:
      1. Load tracked competitor context from DB
      2. Generate targeted search queries from the user's question
      3. Execute web searches via SerpAPI
      4. Synthesize a final answer using AI + DB context + search results
    """
    try:
        provider = get_ai_provider()
    except Exception:
        provider = None

    # ── Step 1: DB context ────────────────────────────────────────────────────
    db_context = await _load_db_context(data.competitor_id)

    # ── Step 2 + 3: Search ────────────────────────────────────────────────────
    search_text = "No web search results — SERPAPI_KEY not configured."
    source_count = 0
    source_urls: list[str] = []

    if provider:
        try:
            queries = await _build_search_queries(data.message, db_context, provider)
            logger.info("Research agent queries: %s", queries)
            search_text, source_urls = await research(
                question=queries[0] if queries else data.message,
                extra_queries=queries[1:],
            )
            source_count = len(source_urls)
            logger.info("Research agent: %d sources retrieved", source_count)
        except Exception as exc:
            logger.warning("Search step failed: %s", exc)
            search_text = "Web search unavailable."

    # ── Step 4: Synthesize ────────────────────────────────────────────────────
    if provider:
        try:
            final_prompt = (
                "You are MarketWatch AI, an expert competitive intelligence analyst. "
                "Answer the user's question using BOTH the internal database context "
                "AND the fresh web search results provided below. "
                "Be concise (3-5 paragraphs), cite specific facts, and end with 1-2 actionable recommendations.\n\n"
                f"--- INTERNAL DATABASE CONTEXT ---\n{db_context}\n\n"
                f"--- LIVE WEB SEARCH RESULTS ---\n{search_text}\n\n"
                f"--- USER QUESTION ---\n{data.message}\n\n"
                "Provide a strategic, data-driven answer:"
            )
            raw = await provider.generate(final_prompt)
            reply = raw.strip()
            model_name = provider.__class__.__name__.replace("Provider", "")
            if source_count > 0:
                reply += f"\n\n_Researched {source_count} live sources._"
            return ChatResponse(reply=reply, model_used=model_name, sources_used=source_count)
        except Exception as exc:
            logger.warning("AI synthesis failed: %s", exc)

    # ── Fallback: DB context only ─────────────────────────────────────────────
    return ChatResponse(
        reply=(
            f"Here is the current intelligence from your tracked competitors:\n\n{db_context}\n\n"
            f"(AI provider unavailable — showing raw database context.)"
        ),
        model_used="db-only",
        sources_used=0,
    )


@router.get("/activity", response_model=dict, summary="Live agent activity feed")
async def get_agent_activity(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Query("system"),
) -> dict:
    """
    Return the agent decision log — every run/skip decision made by autonomous agents,
    most recent first. Powers the live Activity Feed on the frontend.
    """
    from app.models.agent_log import AgentLog
    from app.models.competitor import Competitor
    from app.services.database import async_session_factory
    from sqlalchemy import select, desc, outerjoin

    async with async_session_factory() as session:
        result = await session.execute(
            select(AgentLog, Competitor.name)
            .outerjoin(Competitor, AgentLog.competitor_id == Competitor.id)
            .where(AgentLog.user_id == user_id)
            .order_by(desc(AgentLog.created_at))
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()

    return {
        "activity": [
            {
                "id": log.id,
                "agent_name": log.agent_name,
                "action": log.action,
                "reasoning": log.reasoning,
                "competitor_name": comp_name,
                "created_at": log.created_at.isoformat(),
            }
            for log, comp_name in rows
        ]
    }


@router.get("/status", response_model=dict, summary="Autonomy system status")
async def get_autonomy_status_endpoint() -> dict:
    """Return current state of the autonomous agent system."""
    from app.agents.autonomy_orchestrator import get_autonomy_status
    return await get_autonomy_status()
