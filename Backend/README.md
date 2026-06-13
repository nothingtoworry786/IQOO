# MarketWatch — Competitive Intelligence Analysis Engine

> **Enterprise-grade competitive intelligence platform** powered by FastAPI, SQLAlchemy, Pinecone, Neo4j, and AI agents (Groq / OpenRouter / Claude).

Track competitors, analyse signals, predict moves, and get War Room recommendations — all through a single API.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MarketWatch API                       │
│                    FastAPI + Uvicorn                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │Users     │  │Competitors│  │Signals   │  │Predictns│  │
│  │ CRUD     │  │ +Momentum │  │ +Patterns│  │ AI-based│  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
│  │War Room  │  │Alerts    │  │AI Agents │  │Graph    │  │
│  │ Reports  │  │ Threshold│  │ M/P/S/S  │  │ Neo4j   │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                    Storage Layer                          │
│  ┌──────────────────┐  ┌──────────┐  ┌───────────────┐   │
│  │  PostgreSQL       │  │ Pinecone │  │  Neo4j        │   │
│  │  (SQLAlchemy)     │  │ Vectors  │  │  Graph        │   │
│  │  ┌──────────────┐ │  │ DNA      │  │  Relationships│   │
│  │  │ SQLite (mock) │ │  │ Patterns │  │  Dict (mock)  │   │
│  │  │ Postgres(real)│ │  │ Memory   │  │  Neo4j (real)  │   │
│  │  └──────────────┘ │  └──────────┘  └───────────────┘   │
│  └──────────────────┘                                      │
├─────────────────────────────────────────────────────────┤
│                    AI Provider Layer                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Groq    │  │  OpenRouter  │  │  Anthropic/Claude │    │
│  └──────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Storage Modes

All three databases support **mock** (in-memory or SQLite — no external services needed) and **real** (production connections) modes, toggled via `DATABASE_MODE=mock|real` in `.env`.

| Database | Mock Mode | Real Mode |
|---|---|---|
| PostgreSQL | SQLite via aiosqlite | asyncpg |
| Pinecone | In-memory dict with cosine similarity | Pinecone cloud index |
| Neo4j | In-memory dict-based graph | Neo4j Aura / local |

---

## Quick Start

```bash
# Clone and enter the backend directory
cd Backend

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (or use mock defaults)

# Install dependencies
uv sync --extra dev

# Start the server
uv run uvicorn main:app --reload

# Open the API docs
open http://localhost:8000/docs
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DATABASE_MODE` | `mock` | `mock` or `real` |
| `AI_PROVIDER` | `groq` | `groq`, `openrouter`, or `anthropic` |
| `DATABASE_URL` | `sqlite+aiosqlite:///...` | PostgreSQL connection string (real mode) |
| `GROQ_API_KEY` | — | Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | OpenRouter model name |
| `ANTHROPIC_API_KEY` | — | Anthropic/Claude API key |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Claude model name |
| `PINECONE_API_KEY` | — | Pinecone API key (real mode) |
| `PINECONE_INDEX_NAME` | `competitive-dna` | Pinecone index name |
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI (real mode) |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | — | Neo4j password |

---

## API Endpoints

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check (returns `{"status": "running", "project": "MarketWatch"}`) |

### Analysis

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/analyze` | Analyse competitor signals and get AI prediction |

### Users

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/users/` | List all users |
| `POST` | `/api/v1/users/` | Create a new user |
| `GET` | `/api/v1/users/{id}` | Get user by ID |
| `PUT` | `/api/v1/users/{id}` | Update a user |
| `DELETE` | `/api/v1/users/{id}` | Delete a user |

### Competitors

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/competitors/` | List competitors (filter by `user_id`) |
| `POST` | `/api/v1/competitors/` | Create a competitor (also creates graph node) |
| `GET` | `/api/v1/competitors/{id}` | Get competitor with signals & predictions |
| `PUT` | `/api/v1/competitors/{id}` | Update a competitor |
| `DELETE` | `/api/v1/competitors/{id}` | Delete a competitor |
| `GET` | `/api/v1/competitors/{id}/momentum` | Get momentum score & recent signals |

### Signals

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/signals/` | List signals (filter by `competitor_id`, `signal_type`) |
| `POST` | `/api/v1/signals/` | Create a signal (also stores in vector memory) |
| `GET` | `/api/v1/signals/{id}` | Get signal by ID |

### Predictions

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/predictions/` | List predictions (filter by `competitor_id`) |
| `POST` | `/api/v1/predictions/` | Create a prediction |
| `GET` | `/api/v1/predictions/{id}` | Get prediction by ID |

### War Room

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/warroom/analyze` | Run full AI-powered War Room analysis (all 4 agents) |
| `POST` | `/api/v1/warroom/reports` | Create a War Room report |
| `GET` | `/api/v1/warroom/reports` | List War Room reports |
| `GET` | `/api/v1/warroom/reports/{id}` | Get War Room report by ID |

### Alerts

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/alerts/` | List alerts (filter by `user_id`) |
| `POST` | `/api/v1/alerts/` | Create an alert |
| `PUT` | `/api/v1/alerts/{id}` | Update an alert |
| `DELETE` | `/api/v1/alerts/{id}` | Delete an alert |

### AI Agents

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/agents/` | List all 4 AI agents and their status |
| `POST` | `/api/v1/agents/{name}/analyze` | Run a specific agent against context |
| `GET` | `/api/v1/agents/activity` | Agent activity summary |

**Available agents:** `marketing`, `product`, `sales`, `strategy`

### Graph & DNA

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/graph/competitive/{company}` | Get full competitive relationship graph |
| `GET` | `/api/v1/graph/nodes` | List all graph nodes |
| `GET` | `/api/v1/graph/relationships` | List all graph relationships |
| `GET` | `/api/v1/graph/dna/{company}` | Get competitive DNA profile |

---

## AI Agents

Four specialised AI agents analyse competitor intelligence:

| Agent | Focus | Outputs |
|---|---|---|
| **MarketingAI** | Ad spend, campaigns, positioning, brand sentiment | Threat level, marketing moves, recommended response |
| **ProductAI** | Product launches, features, hiring patterns, roadmaps | Product changes, launch timeline, recommended response |
| **SalesAI** | Pricing, discounts, expansion cities, sales hiring | Pricing changes, expansion cities, recommended response |
| **StrategyAI** | Synthesises all signals into strategic assessment | Threat level, momentum score, prediction, strategic actions, time horizon |

Each agent runs against the same competitor context and produces structured JSON, which the **War Room** orchestrator combines into a consolidated strategic report.

---

## Mock Data

In `DATABASE_MODE=mock`, the server automatically seeds realistic demo data on startup:

- **1 user** — Acme Corp
- **3 competitors** — Blinkit, Zepto, Swiggy
- **6 signals** — hiring spikes, ad spend changes, funding rounds, executive hires
- **3 predictions** — AI-generated market predictions
- **2 War Room reports** — strategic assessments
- **3 alerts** — threshold-based monitoring configs
- **5 competitive DNA patterns** — stored in vector memory
- **21 graph nodes + 9 relationships** — connecting companies, cities, executives, investors, products, and campaigns

---

## Competitive DNA Memory

The Pinecone vector store maintains a living **Competitive DNA** profile for each competitor. Known behaviour patterns:

```
Blinkit:  "Hiring spike → market launch"           (confidence: 85%)
Swiggy:   "Ad spend increase → product rollout"    (confidence: 78%)
Zepto:    "Discount campaign → customer acquisition" (confidence: 72%)
Zomato:   "Executive hire → strategic shift"        (confidence: 65%)
Zepto:    "Funding round → aggressive expansion"    (confidence: 80%)
```

When new signals arrive, the system queries the vector store for matching historical patterns and returns confidence-scored predictions.

---

## Relationship Graph

The Neo4j graph store models competitive relationships:

**Node types:** `Company`, `Competitor`, `Market`, `City`, `Executive`, `Investor`, `FundingRound`, `Product`, `Campaign`

**Relationship types:** `COMPETES_WITH`, `OPERATES_IN`, `HIRED`, `FUNDED`, `LAUNCHED`, `RUNNING`

Example: `Company:Blinkit` → `COMPETES_WITH` → `Company:Zepto`  
Example: `Company:Blinkit` → `OPERATES_IN` → `City:Pune`  
Example: `Investor:SoftBank` → `FUNDED` → `Company:Blinkit`

---

## Testing

```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=app --cov-report=term-missing
```

**46 tests** across 4 test files covering:
- Pydantic schema validation
- AI provider HTTP error handling
- Competitor analysis prompt building & JSON parsing
- Full API endpoint integration tests

---

## Project Structure

```
Backend/
├── main.py                      # FastAPI app entry point + lifespan + seed data
├── pyproject.toml               # Dependencies and project metadata
├── .env.example                 # Environment variable template
├── app/
│   ├── core/
│   │   ├── config.py            # Environment config + validation
│   │   └── ai_provider.py       # AI provider factory
│   ├── providers/
│   │   ├── base.py              # Abstract AIProvider + AIProviderError
│   │   ├── groq_provider.py     # Groq API implementation
│   │   ├── openrouter_provider.py  # OpenRouter API implementation
│   │   └── anthropic_provider.py   # Anthropic/Claude API implementation
│   ├── models/
│   │   ├── base.py              # SQLAlchemy declarative base + mixins
│   │   ├── user.py              # User model
│   │   ├── competitor.py        # Competitor model
│   │   ├── signal.py            # Signal model
│   │   ├── prediction.py        # Prediction model
│   │   ├── warroom.py           # WarRoomReport model
│   │   └── alert.py             # Alert model
│   ├── schemas/
│   │   ├── requests.py          # Request schemas
│   │   ├── responses.py         # Response schemas
│   │   ├── user.py              # User schemas
│   │   ├── competitor.py        # Competitor schemas
│   │   ├── signal.py            # Signal schemas
│   │   ├── prediction.py        # Prediction schemas
│   │   ├── warroom.py           # WarRoom schemas
│   │   └── alert.py             # Alert schemas
│   ├── services/
│   │   ├── database.py          # SQLAlchemy async engine + session
│   │   ├── pinecone.py          # Pinecone vector store (mock/real)
│   │   ├── neo4j.py             # Neo4j graph store (mock/real)
│   │   ├── patterns.py          # Competitive DNA pattern matching
│   │   ├── warroom.py           # War Room report generation
│   │   └── competitor_analysis.py # Competitor analysis service
│   ├── agents/
│   │   ├── base.py              # Abstract BaseAgent
│   │   ├── marketing.py         # MarketingAI agent
│   │   ├── product.py           # ProductAI agent
│   │   ├── sales.py             # SalesAI agent
│   │   └── strategy.py          # StrategyAI agent
│   ├── routers/
│   │   ├── analysis.py          # POST /api/v1/analyze
│   │   ├── users.py             # User CRUD
│   │   ├── competitors.py       # Competitor CRUD + momentum
│   │   ├── signals.py           # Signal CRUD
│   │   ├── predictions.py       # Prediction CRUD
│   │   ├── warroom.py           # War Room endpoints
│   │   ├── alerts.py            # Alert CRUD
│   │   ├── agents.py            # AI agent execution
│   │   └── graph.py             # Graph + DNA endpoints
│   └── ...
├── tests/
│   ├── conftest.py              # Shared test fixtures
│   ├── test_schemas.py          # Schema validation tests
│   ├── test_competitor_analysis.py # Service layer tests
│   ├── test_providers.py        # Provider error handling tests
│   └── test_routes.py           # API integration tests
└── ...
```
