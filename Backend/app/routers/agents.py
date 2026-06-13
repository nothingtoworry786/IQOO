"""AI agent execution and activity API endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter

from app.agents.marketing import MarketingAgent
from app.agents.product import ProductAgent
from app.agents.sales import SalesAgent
from app.agents.strategy import StrategyAgent

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
