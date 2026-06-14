"""
MarketWatch API — Competitive Intelligence Analysis Engine.

Powered by:
- FastAPI (backend framework)
- Supabase PostgreSQL (or SQLite for dev)
- pgvector for competitive DNA similarity search
- Groq | OpenRouter | Anthropic/Claude (AI providers)

Database tables: competitors, signals, predictions, warroom_reports,
competitive_dna, alerts, markets, competitor_markets, competitor_relationships.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers.analysis import router as analysis_router
from app.routers.competitors import router as competitors_router
from app.routers.signals import router as signals_router
from app.routers.predictions import router as predictions_router
from app.routers.warroom import router as warroom_router
from app.routers.alerts import router as alerts_router
from app.routers.agents import router as agents_router
from app.routers.dna import router as dna_router
from app.routers.graph import router as graph_router
from app.routers.onboarding import router as onboarding_router
from app.routers.admin import router as admin_router
from app.schemas.responses import HealthResponse

# ── New Supabase-backed routes ────────────────────────────────────────────────
from app.routes.onboarding import router as v2_onboarding_router
from app.routes.market_map import router as market_map_router
from app.routes.competitors import router as v2_competitors_router
from app.routes.signals import router as v2_signals_router
from app.routes.dna import router as v2_dna_router
from app.services.database import init_db, close_db
from app.workers.background_jobs import setup_scheduler, stop_scheduler

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MarketWatch starting (provider=%s)", settings.AI_PROVIDER)
    await init_db()
    setup_scheduler()          # start autonomous agent loop

    # ── API connectivity status ───────────────────────────────────────────────
    if settings.SERPAPI_KEY:
        logger.info("SerpAPI configured — News, Trends, Play Store signals active")
    else:
        logger.warning("SerpAPI key missing — signal collection disabled (set SERPAPI_KEY)")
    if settings.RAPIDAPI_KEY:
        logger.info("RapidAPI configured — LinkedIn signals active (optional)")
    else:
        logger.info("RapidAPI key missing — LinkedIn signals disabled (optional, set RAPIDAPI_KEY to enable)")
    logger.info("Web scraping (httpx + BeautifulSoup) always active — no key required")

    yield
    stop_scheduler()
    await close_db()
    logger.info("MarketWatch shut down")


app = FastAPI(
    title="MarketWatch API",
    description="Competitive intelligence analysis engine powered by AI.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(analysis_router)
app.include_router(competitors_router)
app.include_router(signals_router)
app.include_router(predictions_router)
app.include_router(warroom_router)
app.include_router(alerts_router)
app.include_router(agents_router)
app.include_router(dna_router)
app.include_router(graph_router)
app.include_router(onboarding_router)
app.include_router(admin_router)

# ── Supabase-backed v2 routes ─────────────────────────────────────────────────
app.include_router(v2_onboarding_router)
app.include_router(market_map_router)
app.include_router(v2_competitors_router)
app.include_router(v2_signals_router)
app.include_router(v2_dna_router)


@app.get("/", response_model=HealthResponse, summary="Health check", tags=["Health"])
async def health() -> HealthResponse:
    return HealthResponse(status="running", project="MarketWatch")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT,
                reload=True, log_level=settings.LOG_LEVEL.lower())
