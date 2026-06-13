"""War Room report generation — orchestrates AI agents to produce strategic reports."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.agents.base import AgentResult
from app.agents.marketing import MarketingAgent
from app.agents.product import ProductAgent
from app.agents.sales import SalesAgent
from app.agents.strategy import StrategyAgent
from app.schemas.requests import AnalyzeRequest

logger = logging.getLogger(__name__)


async def generate_war_room_report(
    request: AnalyzeRequest,
    include_agent_details: bool = False,
) -> dict[str, Any]:
    """Generate a comprehensive War Room report by running all 4 AI agents.

    Args:
        request: The validated analysis request with competitor signals.
        include_agent_details: If True, include individual agent outputs in the response.

    Returns:
        A dictionary with the strategic analysis, agent results, and metadata.
    """
    context = _build_agent_context(request)

    # Run all 4 agents in parallel
    import asyncio

    marketing_agent = MarketingAgent()
    product_agent = ProductAgent()
    sales_agent = SalesAgent()
    strategy_agent = StrategyAgent()

    marketing_task = marketing_agent.analyze(context)
    product_task = product_agent.analyze(context)
    sales_task = sales_agent.analyze(context)
    strategy_task = strategy_agent.analyze(context)

    marketing_result, product_result, sales_result, strategy_result = await asyncio.gather(
        marketing_task, product_task, sales_task, strategy_task,
    )

    # Build the consolidated report
    report = {
        "competitor_name": request.competitor_name,
        "city": request.city,
        "signals": {
            "jobs_added": request.jobs_added,
            "ad_spend_change": request.ad_spend_change,
            "sentiment_change": request.sentiment_change,
        },
        "strategic_analysis": strategy_result.data,
        "threat_level": strategy_result.data.get("threat_level", "medium"),
        "momentum_score": strategy_result.data.get("momentum_score", 50),
        "prediction": strategy_result.data.get("prediction", "No prediction available."),
        "summary": strategy_result.summary,
        "confidence": strategy_result.confidence,
        "time_horizon": strategy_result.data.get("time_horizon", "short_term"),
        "strategic_actions": strategy_result.data.get("strategic_actions", []),
    }

    if include_agent_details:
        report["agent_details"] = {
            "marketing": marketing_result.to_dict(),
            "product": product_result.to_dict(),
            "sales": sales_result.to_dict(),
            "strategy": strategy_result.to_dict(),
        }

    return report


def _build_agent_context(request: AnalyzeRequest) -> str:
    """Build the context string that agents will analyse."""
    return f"""Competitor: {request.competitor_name}
City: {request.city}
Industry: Quick Commerce

Signals Detected:
- Jobs Added: {request.jobs_added} (recent hiring activity)
- Ad Spend Change: {request.ad_spend_change}% (marketing investment change)
- Sentiment Change: {request.sentiment_change}% (brand/consumer sentiment shift)

Recent Context:
{request.competitor_name} has been active in the {request.city} market.
The {request.jobs_added} new job postings suggest {'aggressive' if request.jobs_added > 15 else 'moderate'} expansion.
The {'+' if request.ad_spend_change >= 0 else ''}{request.ad_spend_change}% ad spend change indicates {'increased' if request.ad_spend_change > 0 else 'decreased'} marketing investment.
The {'+' if request.sentiment_change >= 0 else ''}{request.sentiment_change}% sentiment shift suggests {'improving' if request.sentiment_change > 0 else 'declining'} brand perception.

Provide a comprehensive competitive intelligence analysis."""
