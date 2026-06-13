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
from app.schemas.responses import HealthResponse
from app.services.database import init_db, close_db
from app.services.competitive_dna import seed_dna_patterns

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MarketWatch starting (provider=%s)", settings.AI_PROVIDER)
    await init_db()
    await seed_mock_data()
    yield
    await close_db()
    logger.info("MarketWatch shut down")


app = FastAPI(
    title="MarketWatch API",
    description="Competitive intelligence analysis engine powered by AI.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
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


@app.get("/", response_model=HealthResponse, summary="Health check", tags=["Health"])
async def health() -> HealthResponse:
    return HealthResponse(status="running", project="MarketWatch")


async def seed_mock_data() -> None:
    from app.models.competitor import Competitor
    from app.models.signal import Signal
    from app.models.prediction import Prediction
    from app.models.warroom import WarRoomReport
    from app.models.alert import Alert
    from app.models.competitive_dna import CompetitiveDNA
    from app.models.market import Market, CompetitorMarket, CompetitorRelationship
    from app.services.database import async_session_factory
    from sqlalchemy import select, func

    async with async_session_factory() as session:
        try:
            result = await session.execute(select(func.count(Competitor.id)))
            count = result.scalar()
            if count and count > 0:
                logger.info("Database already seeded, skipping")
                await session.close()
                return

            # ── Batch 1: Competitors (no FK dependencies) ──
            session.add_all([
                Competitor(id="comp-blinkit", name="Blinkit", industry="Quick Commerce",
                           website="https://blinkit.com", market_scope="National"),
                Competitor(id="comp-zepto", name="Zepto", industry="Quick Commerce",
                           website="https://zepto.com", market_scope="National"),
                Competitor(id="comp-swiggy", name="Swiggy", industry="Food and Grocery Delivery",
                           website="https://swiggy.com", market_scope="National"),
                Competitor(id="comp-zomato", name="Zomato", industry="Food Delivery",
                           website="https://zomato.com", market_scope="National"),
                Competitor(id="comp-flipkart", name="Flipkart", industry="E-Commerce",
                           website="https://flipkart.com", market_scope="National"),
                Competitor(id="comp-bigbasket", name="BigBasket", industry="Online Grocery",
                           website="https://bigbasket.com", market_scope="National"),
            ])
            await session.flush()

            # ── Batch 2: Markets (no FK dependencies) ──
            session.add_all([
                Market(id="mkt-qc", name="Quick Commerce India", market_size=3500000000, growth_rate="35% YoY"),
                Market(id="mkt-og", name="Online Grocery India", market_size=7500000000, growth_rate="25% YoY"),
                Market(id="mkt-fd", name="Food Delivery India", market_size=6000000000, growth_rate="18% YoY"),
                Market(id="mkt-ec", name="E-Commerce India", market_size=70000000000, growth_rate="22% YoY"),
            ])
            await session.flush()

            # ── Batch 3: Join tables & relationships (FKs to competitors & markets) ──
            session.add_all([
                CompetitorMarket(competitor_id="comp-blinkit", market_id="mkt-qc", market_share=0.22, since_year=2019),
                CompetitorMarket(competitor_id="comp-zepto", market_id="mkt-qc", market_share=0.18, since_year=2021),
                CompetitorMarket(competitor_id="comp-swiggy", market_id="mkt-qc", market_share=0.15, since_year=2020),
                CompetitorMarket(competitor_id="comp-swiggy", market_id="mkt-fd", market_share=0.40, since_year=2014),
                CompetitorMarket(competitor_id="comp-zomato", market_id="mkt-fd", market_share=0.45, since_year=2008),
                CompetitorMarket(competitor_id="comp-flipkart", market_id="mkt-ec", market_share=0.35, since_year=2007),
                CompetitorMarket(competitor_id="comp-bigbasket", market_id="mkt-og", market_share=0.15, since_year=2011),
                CompetitorRelationship(source_competitor_id="comp-blinkit", target_competitor_id="comp-zepto",
                    relationship_type="COMPETES_WITH", intensity=0.95),
                CompetitorRelationship(source_competitor_id="comp-blinkit", target_competitor_id="comp-swiggy",
                    relationship_type="COMPETES_WITH", intensity=0.80),
                CompetitorRelationship(source_competitor_id="comp-zepto", target_competitor_id="comp-swiggy",
                    relationship_type="COMPETES_WITH", intensity=0.75),
                CompetitorRelationship(source_competitor_id="comp-swiggy", target_competitor_id="comp-zomato",
                    relationship_type="COMPETES_WITH", intensity=0.90),
                CompetitorRelationship(source_competitor_id="comp-flipkart", target_competitor_id="comp-blinkit",
                    relationship_type="COMPETES_WITH", intensity=0.60),
                CompetitorRelationship(source_competitor_id="comp-bigbasket", target_competitor_id="comp-blinkit",
                    relationship_type="COMPETES_WITH", intensity=0.70),
            ])
            await session.flush()

            # ── Batch 4: Signal, Prediction, WarRoomReport (FKs to competitors) ──
            from app.models.signal import SignalCategory as SC
            session.add_all([
                Signal(competitor_id="comp-blinkit", signal_type=SC.HIRING, source="LinkedIn Jobs",
                       impact_score=8.5, urgency_score=7.0,
                       title="Blinkit hiring surge in Pune",
                       description="Blinkit posted 23 new jobs in Pune across delivery, ops, and tech roles. Includes 10 delivery managers, 8 operations leads, and 5 software engineers."),
                Signal(competitor_id="comp-blinkit", signal_type=SC.MARKETING, source="SensorTower",
                       impact_score=7.2, urgency_score=6.5,
                       title="Blinkit ad spend up 40% MoM in Pune",
                       description="Blinkit ad spend increased 40% month-over-month in Pune market. Focus on social media and local search ads."),
                Signal(competitor_id="comp-blinkit", signal_type=SC.EXPANSION, source="Press Release",
                       impact_score=9.0, urgency_score=8.5,
                       title="Blinkit expanding to 5 new cities",
                       description="Blinkit announced expansion to 5 new cities: Jaipur, Lucknow, Chandigarh, Bhopal, Indore. Setup in progress with hiring already started."),
                Signal(competitor_id="comp-zepto", signal_type=SC.MARKETING, source="App Annie",
                       impact_score=6.8, urgency_score=5.5,
                       title="Zepto launches student discount campaign in Mumbai",
                       description="Zepto launched student discount campaign in Mumbai with 20% off first 5 orders targeting college students."),
                Signal(competitor_id="comp-zepto", signal_type=SC.FUNDING, source="TechCrunch",
                       impact_score=9.0, urgency_score=8.0,
                       title="Zepto raises $340M in Series E funding",
                       description="Zepto raised $340M in Series E funding led by Nexus Venture Partners at a $3.5B valuation. Funds earmarked for expansion."),
                Signal(competitor_id="comp-zepto", signal_type=SC.PRODUCT, source="Twitter/X",
                       impact_score=7.8, urgency_score=6.2,
                       title="Zepto launches Zepto Pass subscription",
                       description="Zepto launched Zepto Pass subscription with free delivery and discounts at INR 99/month. Aimed at increasing customer retention."),
                Signal(competitor_id="comp-zepto", signal_type=SC.HIRING, source="LinkedIn Jobs",
                       impact_score=7.0, urgency_score=6.0,
                       title="Zepto opens 45 new positions across teams",
                       description="Zepto posted 45 new job openings across tech, product, and operations teams. Major push in engineering and product management."),
                Signal(competitor_id="comp-swiggy", signal_type=SC.LEADERSHIP, source="LinkedIn",
                       impact_score=7.5, urgency_score=6.0,
                       title="Swiggy hires VP of Engineering from Amazon",
                       description="Swiggy hired new VP of Engineering from Amazon to lead Instamart platform team. Signals focus on scaling tech platform."),
                Signal(competitor_id="comp-swiggy", signal_type=SC.MARKETING, source="SensorTower",
                       impact_score=6.5, urgency_score=5.8,
                       title="Swiggy Instamart ad spend surges in Bangalore",
                       description="Swiggy Instamart ad spend increased 25% in Bangalore market. Focus on digital and OOH advertising."),
                Signal(competitor_id="comp-swiggy", signal_type=SC.MARKETING, source="App Analysis",
                       impact_score=6.0, urgency_score=4.5,
                       title="Swiggy reduces delivery fees in tier-2 cities",
                       description="Swiggy reduced delivery fees in tier-2 cities to compete with Zepto and Blinkit. Pricing pressure in smaller markets."),
                Signal(competitor_id="comp-zomato", signal_type=SC.PRODUCT, source="TechCrunch",
                       impact_score=8.0, urgency_score=7.5,
                       title="Zomato launches loyalty membership at INR 199/year",
                       description="Zomato launched Zomato Foodie Membership at INR 199/year with unlimited free delivery. Aggressive pricing to drive subscriber growth."),
                Signal(competitor_id="comp-flipkart", signal_type=SC.PRODUCT, source="Press Release",
                       impact_score=8.0, urgency_score=7.5,
                       title="Flipkart Minutes quick-commerce launches in 5 cities",
                       description="Flipkart launched Flipkart Minutes quick-commerce service in 5 cities: Bangalore, Mumbai, Delhi, Hyderabad, Chennai. 10-minute delivery promise."),
                Signal(competitor_id="comp-bigbasket", signal_type=SC.MARKETING, source="Email Marketing",
                       impact_score=6.5, urgency_score=5.0,
                       title="BigBasket Monthly Saver subscription launches",
                       description="BigBasket launched Monthly Saver subscription with 15% discount on all orders. Loyalty play to retain existing customers."),
                Prediction(competitor_id="comp-blinkit", confidence=78, threat_level="high",
                    prediction="Blinkit will expand to 5 new cities in Q3 2025 based on hiring and ad spend signals",
                    ai_reasoning="Hiring spike + ad spend increase = market launch within 60 days. Pattern matched at 85% confidence."),
                Prediction(competitor_id="comp-zepto", confidence=85, threat_level="medium",
                    prediction="Zepto will use Series E funding to enter 8-10 new cities and launch Zepto Pass nationally",
                    ai_reasoning="Funding round historically leads to aggressive expansion. Zepto Pass indicates retention focus."),
                Prediction(competitor_id="comp-swiggy", confidence=65, threat_level="low",
                    prediction="Swiggy will focus on Instamart vertical expansion in existing cities",
                    ai_reasoning="Executive hire from Amazon signals platform deepening. Pricing changes suggest defensive play."),
                Prediction(competitor_id="comp-zomato", confidence=80, threat_level="medium",
                    prediction="Zomato Foodie Membership will reach 2M subscribers within 6 months",
                    ai_reasoning="Aggressive pricing at INR 199/year with unlimited delivery creates strong value proposition."),
                Prediction(competitor_id="comp-flipkart", confidence=75, threat_level="high",
                    prediction="Flipkart Minutes will disrupt quick-commerce and reach 10 cities by end of 2025",
                    ai_reasoning="E-commerce giant entering quick-commerce with massive distribution advantage."),
                Prediction(competitor_id="comp-bigbasket", confidence=60, threat_level="low",
                    prediction="BigBasket will lose market share as Blinkit and Zepto expand aggressively",
                    ai_reasoning="Legacy online grocer facing pressure from faster, well-funded competitors."),
                WarRoomReport(competitor_id="comp-blinkit", impact_score=8.0,
                    threat_summary="Blinkit is in an aggressive expansion phase. Hiring spike (23 jobs) + 40% ad spend increase signals imminent market launch in Pune.",
                    recommended_actions="1. Increase local marketing budget by 20%\n2. Accelerate hiring in Pune\n3. Launch loyalty program\n4. Negotiate exclusive local retailer partnerships"),
                WarRoomReport(competitor_id="comp-zepto", impact_score=7.2,
                    threat_summary="Zepto's $340M raise signals major expansion. Discount campaigns and Zepto Pass are driving customer acquisition.",
                    recommended_actions="1. Review student segment pricing\n2. Counter Zepto Pass with loyalty program\n3. Monitor new city launches\n4. Prepare discount response playbook"),
                WarRoomReport(competitor_id="comp-flipkart", impact_score=8.5,
                    threat_summary="Flipkart entering quick-commerce with Flipkart Minutes is a game-changer with their distribution and brand trust.",
                    recommended_actions="1. Accelerate quick-commerce expansion\n2. Build exclusive merchant partnerships\n3. Focus on delivery speed\n4. Prepare for pricing pressure"),
            ])
            await session.flush()

            # ── Batch 5: Alerts (FKs to competitors) ──
            session.add_all([
                Alert(competitor_id="comp-blinkit", alert_type="hiring_spike", threshold=15.0, enabled=True),
                Alert(competitor_id="comp-blinkit", alert_type="ad_spend_surge", threshold=25.0, enabled=True),
                Alert(competitor_id="comp-zepto", alert_type="funding_round", threshold=0.0, enabled=True),
                Alert(competitor_id="comp-zepto", alert_type="city_expansion", threshold=0.0, enabled=True),
                Alert(competitor_id="comp-swiggy", alert_type="pricing_change", threshold=10.0, enabled=True),
            ])
            await session.flush()

            # ── Batch 6: Competitive DNA (FKs to competitors, no embeddings for dev) ──
            session.add_all([
                CompetitiveDNA(id="dna-hiring-blinkit", competitor_id="comp-blinkit", pattern_type="hiring_spike",
                    description="Hiring spike precedes market launch for Blinkit. When jobs_added > 20, expect new city expansion within 60 days.",
                    confidence_score=0.85),
                CompetitiveDNA(id="dna-ad-swiggy", competitor_id="comp-swiggy", pattern_type="ad_spend_increase",
                    description="Ad spend increase precedes product rollout for Swiggy. When ad_spend_change > 30, expect new launch in 4-6 weeks.",
                    confidence_score=0.78),
                CompetitiveDNA(id="dna-discount-zepto", competitor_id="comp-zepto", pattern_type="discount_campaign",
                    description="Discount campaign drives customer acquisition for Zepto. Expect user base growth of 15-25% in 30 days.",
                    confidence_score=0.72),
                CompetitiveDNA(id="dna-funding-zepto", competitor_id="comp-zepto", pattern_type="funding_round",
                    description="Funding round leads to aggressive expansion for Zepto. Expect 3-5 new city launches within 6 months.",
                    confidence_score=0.80),
                CompetitiveDNA(id="dna-expansion-blinkit", competitor_id="comp-blinkit", pattern_type="city_expansion",
                    description="Blinkit expands to 5+ cities when hiring and ad spend both increase simultaneously.",
                    confidence_score=0.82),
            ])

            await session.commit()
            logger.info("Seeded: 6 competitors, 4 markets, 7 market links, 6 relationships, 13 signals, 6 predictions, 3 reports, 5 alerts, 5 DNA patterns")

        except Exception as exc:
            await session.rollback()
            logger.warning("Mock data seeding skipped (%s)", exc)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT,
                reload=True, log_level=settings.LOG_LEVEL.lower())
