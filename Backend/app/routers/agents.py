"""AI agent execution, activity, and chat API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agents.marketing import MarketingAgent
from app.agents.product import ProductAgent
from app.agents.sales import SalesAgent
from app.agents.strategy import StrategyAgent
from app.core.ai_provider import get_ai_provider
from app.providers.base import AIProviderError

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
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent '{agent_name}'. Available: {', '.join(_agents.keys())}",
        )
    result = await agent.analyze(context)
    return result.to_dict()


# ---------------------------------------------------------------------------
# Chat with AI Competitor Intelligence
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="The user's question about competitors")
    competitor_id: str | None = Field(None, description="Optional competitor ID to scope the question")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="AI-generated response")
    model_used: str = Field("mock", description="Which AI model was used")


@router.post("/chat", response_model=ChatResponse, summary="Chat with AI competitive intelligence")
async def chat_with_ai(data: ChatRequest) -> ChatResponse:
    """
    Ask a question about your competitors and get an AI-powered answer.
    Scopes the response to your tracked competitors when competitor_id is provided.
    """
    # Try to use the AI provider if configured
    try:
        provider = get_ai_provider()
    except (ValueError, Exception):
        provider = None

    if provider:
        try:
            system_prompt = (
                "You are MarketWatch AI, a competitive intelligence assistant. "
                "Answer questions about competitors, market trends, and strategic threats. "
                "Keep responses concise (2-4 paragraphs), data-driven, and actionable.\n\n"
                f"{'The user is asking about a specific competitor.' if data.competitor_id else 'The user is asking a general question about their competitive landscape.'}"
            )
            user_prompt = f"Question: {data.message}\n\nProvide a concise, strategic answer with actionable insights."
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            raw = await provider.generate(full_prompt)
            return ChatResponse(reply=raw.strip(), model_used=provider.__class__.__name__)
        except (AIProviderError, Exception) as exc:
            logger.warning("AI provider failed, falling back to mock: %s", exc)
            # Fall through to mock response
            pass

    # Fallback mock responses when no AI provider is configured
    mock_responses: dict[str, str] = {
        "funding": (
            "🔍 **Recent Funding Activity**\n\n"
            "Based on market intelligence gathered from your tracked competitors:\n\n"
            "• **Zepto** raised $340M Series E at $3.5B valuation — funds earmarked for dark store expansion from 350 to 700 locations.\n"
            "• **Blinkit** received ₹300 Cr internal funding from Zomato for last-mile logistics tech.\n\n"
            "📈 **Recommendation:** Monitor Zepto's expansion closely. Their funding round historically precedes aggressive hiring and market entry into new cities."
        ),
        "hiring": (
            "👥 **Hiring Intelligence**\n\n"
            "Recent hiring signals from your competitive landscape:\n\n"
            "• **Blinkit** posted 23 new operations and tech roles in Pune — strong signal of imminent market launch.\n"
            "• **Zepto** opened 45 roles across ML engineering and supply-chain product management.\n"
            "• **Swiggy** hired a VP of Engineering from Amazon to lead the Instamart platform rebuild.\n\n"
            "⚡ **Action:** Accelerate your own hiring in Pune if you're not already staffed there."
        ),
        "pricing": (
            "💰 **Pricing Intelligence**\n\n"
            "Recent pricing changes detected:\n\n"
            "• **Swiggy Instamart** reduced delivery fees from ₹25 to ₹9 in Tier-2 cities — defensive pricing against Blinkit.\n"
            "• **Zepto** launched Zepto Pass at ₹99/month with free delivery + 5% cashback — aggressive retention play.\n"
            "• **Zomato** launched Foodie Membership at INR 199/year with unlimited free delivery.\n\n"
            "📊 **Impact:** Pricing pressure is increasing across the board. Consider reviewing your own pricing strategy for Tier-2 markets."
        ),
        "expansion": (
            "🚀 **Expansion Intelligence**\n\n"
            "Key expansion signals from competitors:\n\n"
            "• **Blinkit** confirmed expansion to 5 new cities: Jaipur, Lucknow, Chandigarh, Bhopal, Indore. Hiring already underway.\n"
            "• **Zepto** piloting B2B grocery vertical in Bangalore targeting restaurants.\n"
            "• **Flipkart** launched 'Flipkart Minutes' quick-commerce in 5 major metros.\n\n"
            "🎯 **Strategic Response:** Prioritize locking in exclusive partnerships with top local vendors in these cities before competitors establish dominance."
        ),
        "default": (
            "🤖 **MarketWatch AI Insight**\n\n"
            "Here's a strategic summary of your competitive landscape:\n\n"
            "**Quick Commerce India** is experiencing aggressive expansion with Blinkit, Zepto, and Swiggy Instamart all scaling operations. "
            "Blinkit's hiring surge and ad spend increase (+40% MoM in Pune) indicate imminent market launches. "
            "Zepto's $340M Series E and Zepto Pass subscription signal a retention-focused growth strategy. "
            "Swiggy is playing defence with fee cuts while rebuilding the Instamart platform under new Amazon engineering leadership.\n\n"
            "⚡ **Top priority:** Focus on Tier-2 city expansion and customer retention programs to counter the incoming competitive wave."
        ),
    }

    msg_lower = data.message.lower()
    for keyword, response in mock_responses.items():
        if keyword in msg_lower and keyword != "default":
            return ChatResponse(reply=response, model_used="mock")

    return ChatResponse(reply=mock_responses["default"], model_used="mock")


@router.get("/activity", response_model=list[dict])
async def get_agent_activity() -> list[dict]:
    """Return activity summary from all 4 agents (mock data for now)."""
    return [
        {
            "agent": "MarketingAI",
            "status": "idle",
            "last_run": "2025-06-12T14:30:00Z",
            "total_analyses": 42,
            "avg_confidence": 0.76,
        },
        {
            "agent": "ProductAI",
            "status": "idle",
            "last_run": "2025-06-12T14:28:00Z",
            "total_analyses": 38,
            "avg_confidence": 0.81,
        },
        {
            "agent": "SalesAI",
            "status": "idle",
            "last_run": "2025-06-12T14:25:00Z",
            "total_analyses": 35,
            "avg_confidence": 0.73,
        },
        {
            "agent": "StrategyAI",
            "status": "idle",
            "last_run": "2025-06-12T14:35:00Z",
            "total_analyses": 40,
            "avg_confidence": 0.79,
        },
    ]
