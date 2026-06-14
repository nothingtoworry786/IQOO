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
from app.core.config import settings
from app.services.search_tool import research

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
    company: str | None = Field(None, description="Company whose knowledge shard to query")


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


def _chat_provider():
    """Chatbot LLM — Groq (same provider as the rest of the pipeline)."""
    from app.core.ai_provider import get_ai_provider
    return get_ai_provider()


@router.post("/chat", response_model=ChatResponse, summary="Chatbot — RAG over company + competitor knowledge, answered by Groq")
async def chat_with_ai(data: ChatRequest) -> ChatResponse:
    """
    RAG chatbot pipeline:
      1. Ensure the RAG knowledge base (company context + competitors + signals
         + predictions) is populated.
      2. Retrieve the most relevant context for the user's question from RAG.
      3. (Optional) add fresh web results via SerpAPI — no LLM needed.
      4. Answer with the Groq model.
    """
    from app.services import rag

    # ── Step 1: Ensure the company's knowledge shard is populated ─────────────
    await rag.ensure_knowledge_base(data.company)

    # ── Step 2: Hybrid (dense+sparse) retrieval from the company's shard ──────
    rag_docs = await rag.query_knowledge(data.message, company=data.company, n_results=6)
    if rag_docs:
        kb_context = "\n".join(f"- {d}" for d in rag_docs)
    else:
        # Fallback: pull straight from the DB if the KB is empty
        kb_context = await _load_db_context(data.competitor_id)

    # ── Step 3: Optional fresh web search (SerpAPI only — no LLM) ──────────────
    search_text = ""
    source_count = 0
    try:
        search_text, source_urls = await research(question=data.message)
        source_count = len(source_urls)
    except Exception as exc:
        logger.debug("Chat web search skipped: %s", exc)

    # ── Step 4: Answer with the Groq model ────────────────────────────────────
    web_block = f"\n\n--- LIVE WEB SEARCH ---\n{search_text}" if search_text.strip() else ""
    prompt = (
        "You are MarketWatch AI, a competitive-intelligence assistant for the user's company. "
        "Answer the user's question using the KNOWLEDGE BASE below — it contains our company "
        "profile, tracked competitors, intelligence signals, and predictions. "
        "Be concise and specific, cite competitor names and signals where relevant, and finish "
        "with one actionable suggestion. If the knowledge base doesn't cover the answer, say so plainly.\n\n"
        f"--- KNOWLEDGE BASE (retrieved context) ---\n{kb_context}{web_block}\n\n"
        f"--- USER QUESTION ---\n{data.message}\n\n"
        "Answer:"
    )

    provider = _chat_provider()
    try:
        reply = (await provider.generate(prompt)).strip()
        grounding = f"{len(rag_docs)} knowledge entries"
        if source_count:
            grounding += f" + {source_count} live sources"
        reply += f"\n\n_{settings.GROQ_MODEL} · grounded on {grounding}._"
        return ChatResponse(
            reply=reply,
            model_used=settings.GROQ_MODEL,
            sources_used=source_count,
        )
    except Exception as exc:
        logger.warning("Chat generation failed: %s", exc)
        return ChatResponse(
            reply=(
                "I couldn't reach the AI model right now. "
                f"Here is the relevant context I found:\n\n{kb_context}"
            ),
            model_used="rag-only",
            sources_used=source_count,
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
    from sqlalchemy import select, desc

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
