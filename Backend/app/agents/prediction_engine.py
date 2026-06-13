"""PredictionEngine + StrategyAgent — fires predictions and battle plans autonomously."""

from __future__ import annotations

import json
import logging
import re
import uuid

from app.core.ai_provider import get_ai_provider
from app.providers.base import AIProviderError
from app.services.database import async_session_factory

logger = logging.getLogger(__name__)


async def run_prediction(
    user_id: str,
    competitor_id: str,
    competitor_name: str,
    high_intent_signals: list[dict],
    dna_patterns: list[dict],
) -> dict | None:
    """
    Analyze high-intent signals + DNA patterns and fire a prediction if warranted.
    Inserts the prediction into DB and returns it, or returns None if AI says skip.
    """
    from app.models.prediction import Prediction
    from app.models.agent_log import AgentLog

    signal_lines = "\n".join(
        f"- [{s.get('signal_type', '')}] {s.get('title', '')} "
        f"(impact {s.get('impact_score', 0):.1f}, urgency {s.get('urgency_score', 0):.1f})"
        for s in high_intent_signals
    )
    dna_lines = "\n".join(
        f"- {p.get('pattern_type', '')}: {str(p.get('description', ''))[:120]}"
        for p in dna_patterns
    ) if dna_patterns else "No DNA profile yet — predict from signals only."

    prompt = f"""You are a competitive prediction engine.

Competitor: {competitor_name}

High-intent signals detected in the last 7 days:
{signal_lines}

Known behavioral DNA patterns:
{dna_lines}

Based on the signals and DNA patterns, should a prediction be filed now?
Only predict when confidence is genuinely above 60%.

Return ONLY valid JSON, nothing else:
{{
  "should_predict": true,
  "prediction": "Specific, time-bound prediction about what this competitor will do in 30-90 days",
  "confidence": 78,
  "threat_level": "high",
  "ai_reasoning": "2-3 sentences explaining how the signals + DNA patterns justify this prediction",
  "is_war_room_trigger": false
}}

threat_level: "low" | "medium" | "high" | "critical"
confidence: integer 0-100
is_war_room_trigger: true ONLY when confidence >= 75 AND threat_level is "high" or "critical"
If should_predict is false, set prediction to "" but keep all other fields."""

    try:
        provider = get_ai_provider()
        raw = await provider.generate(prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```\w*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        data: dict = json.loads(cleaned.strip())

        if not data.get("should_predict") or not str(data.get("prediction", "")).strip():
            async with async_session_factory() as session:
                session.add(AgentLog(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    competitor_id=competitor_id,
                    agent_name="PredictionEngine",
                    action=f"Prediction skipped for {competitor_name} — signals not yet sufficient",
                    reasoning="AI determined the current signal set does not justify a high-confidence prediction at this time.",
                ))
                await session.commit()
            return None

        confidence = max(0, min(100, int(data.get("confidence", 50))))
        threat_level = str(data.get("threat_level", "medium"))
        is_trigger = bool(data.get("is_war_room_trigger", False))

        async with async_session_factory() as session:
            pred = Prediction(
                id=str(uuid.uuid4()),
                competitor_id=competitor_id,
                prediction=data.get("prediction", ""),
                confidence=confidence,
                threat_level=threat_level,
                ai_reasoning=data.get("ai_reasoning", ""),
                is_war_room_trigger=is_trigger,
            )
            session.add(pred)

            session.add(AgentLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                competitor_id=competitor_id,
                agent_name="PredictionEngine",
                action=f"Prediction filed for {competitor_name} — {data.get('prediction', '')[:120]}... "
                       f"(confidence: {confidence}%{', WAR ROOM TRIGGERED' if is_trigger else ''})",
                reasoning=data.get("ai_reasoning", ""),
            ))
            await session.commit()
            pred_id = pred.id

        logger.info(
            "PredictionEngine fired for '%s' (conf=%d, trigger=%s)",
            competitor_name, confidence, is_trigger,
        )
        return {
            "id": pred_id,
            "prediction": data.get("prediction", ""),
            "confidence": confidence,
            "threat_level": threat_level,
            "is_war_room_trigger": is_trigger,
            "ai_reasoning": data.get("ai_reasoning", ""),
        }

    except (AIProviderError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("PredictionEngine failed for '%s': %s", competitor_name, exc)
        async with async_session_factory() as session:
            session.add(AgentLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                competitor_id=competitor_id,
                agent_name="PredictionEngine",
                action=f"Prediction engine error for {competitor_name}",
                reasoning=str(exc)[:300],
            ))
            await session.commit()
        return None

    except Exception as exc:
        logger.error("PredictionEngine unexpected error for '%s': %s", competitor_name, exc)
        return None


async def generate_battle_plan(
    user_id: str,
    competitor_id: str,
    competitor_name: str,
    prediction: dict,
    signals: list[dict],
) -> dict | None:
    """
    StrategyAgent: generate a War Room battle plan for a triggered prediction.
    Inserts a WarRoomReport and logs the activation.
    """
    from app.models.warroom import WarRoomReport
    from app.models.agent_log import AgentLog

    signal_lines = "\n".join(
        f"- [{s.get('signal_type', '')}] {s.get('title', '')} (impact {s.get('impact_score', 0):.1f})"
        for s in signals[-10:]
    )

    prompt = f"""You are a strategic warfare analyst generating an executive battle plan.

Competitor: {competitor_name}
Triggered Prediction: {prediction.get('prediction', '')}
Threat Level: {prediction.get('threat_level', 'high')} | Confidence: {prediction.get('confidence', 0)}%

Supporting Intelligence:
{signal_lines}

Generate an actionable War Room battle plan. Return ONLY valid JSON:
{{
  "threat_summary": "2-3 sentence executive threat summary with specific details and timeline",
  "recommended_actions": "1. Action with metric/timeline\\n2. Action with metric/timeline\\n3. Action with metric/timeline\\n4. Action with metric/timeline",
  "impact_score": 8.5
}}

impact_score: float 0-10. Make actions specific and time-bound — no generic advice."""

    try:
        provider = get_ai_provider()
        raw = await provider.generate(prompt)
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```\w*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        data: dict = json.loads(cleaned.strip())

        async with async_session_factory() as session:
            report = WarRoomReport(
                id=str(uuid.uuid4()),
                competitor_id=competitor_id,
                threat_summary=data.get("threat_summary", ""),
                recommended_actions=data.get("recommended_actions", ""),
                impact_score=min(10.0, max(0.0, float(data.get("impact_score", 7.0)))),
            )
            session.add(report)

            session.add(AgentLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                competitor_id=competitor_id,
                agent_name="StrategyAgent",
                action=f"War Room activated for {competitor_name} — battle plan generated autonomously",
                reasoning=f"Triggered by {prediction.get('threat_level', 'high')}-threat prediction "
                          f"at {prediction.get('confidence', 0)}% confidence. "
                          f"Battle plan covers {len(signals)} intelligence signals.",
            ))
            await session.commit()

        logger.info("StrategyAgent: battle plan generated for '%s'", competitor_name)
        return data

    except (AIProviderError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("StrategyAgent failed for '%s': %s", competitor_name, exc)
        return None

    except Exception as exc:
        logger.error("StrategyAgent unexpected error for '%s': %s", competitor_name, exc)
        return None
