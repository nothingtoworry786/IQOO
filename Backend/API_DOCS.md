# MarketWatch / CompetitorGPT — API Documentation

**Base URL:** `http://localhost:8000`
**Interactive Docs:** [`/docs`](http://localhost:8000/docs) (Swagger) · [`/redoc`](http://localhost:8000/redoc) (ReDoc)

---

## Table of Contents

| Group | Prefix | Backend |
|-------|--------|---------|
| [Health](#health) | `/` | — |
| [**Discovery Pipeline**](#discovery-pipeline-v2) | `/api/onboarding` | Supabase + Claude + SerpAPI |
| [**Market Map**](#market-map-v2) | `/api/market-map` | Supabase + ChromaDB |
| [**Competitors v2**](#competitors-v2) | `/api/competitors` | Supabase |
| [**Signals v2**](#signals-v2) | `/api/signals` | Supabase |
| [**DNA Profiles v2**](#dna-profiles-v2) | `/api/dna` | Supabase + Claude |
| [Analysis (legacy)](#analysis-legacy) | `/api/v1` | SQLite |
| [Competitors (legacy)](#competitors-legacy) | `/api/v1/competitors` | SQLite |
| [Signals (legacy)](#signals-legacy) | `/api/v1/signals` | SQLite |
| [Predictions](#predictions) | `/api/v1/predictions` | SQLite |
| [War Room](#war-room) | `/api/v1/warroom` | SQLite |
| [Alerts](#alerts) | `/api/v1/alerts` | SQLite |
| [AI Agents](#ai-agents) | `/api/v1/agents` | SQLite |
| [Competitive DNA (legacy)](#competitive-dna-legacy) | `/api/v1/dna` | SQLite |
| [Graph](#graph) | `/api/v1/graph` | SQLite |
| [Onboarding (legacy)](#onboarding-legacy) | `/api/v1/onboarding` | SQLite |
| [Admin / Demo](#admin--demo) | `/api/v1/admin` | SQLite |

---

## Health

### `GET /`
Returns server status.

**Response**
```json
{ "status": "running", "project": "MarketWatch" }
```

---

## Discovery Pipeline (v2)

> **Supabase-backed.** Requires `SUPABASE_URL`, `SUPABASE_KEY`, and `ANTHROPIC_API_KEY` in `.env`.

The intake form kicks off a 7-step background pipeline. The endpoint returns a `job_id` immediately; the frontend polls status until `progress` reaches 100.

**Pipeline steps:**
1. Scrape + enrich company profile (httpx + BeautifulSoup4)
2. Pass 1 — Claude direct competitor discovery (5 companies)
3. Pass 2 — SerpAPI search discovery (5 more companies)
4. Pass 3 — Validate & enrich all unique competitors (Claude)
5. Save competitors + profiles to Supabase
6. Collect live signals for every competitor (SerpAPI × 4 query types)
7. Finalize — generate summary, mark job complete

---

### `POST /api/onboarding/discover`
Start the discovery pipeline. Returns a `job_id` immediately.

**Request Body**
```json
{
  "user_id": "user_abc",
  "company_name": "IQOO",
  "website": "https://iqoo.com",
  "description": "Quick-commerce grocery delivery in India, 10-minute delivery"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | Unique user identifier |
| `company_name` | string | Yes | Your company name |
| `website` | string | No | Company website (used for scraping) |
| `description` | string | No | What your company does |

**Response · `200 OK`**
```json
{
  "job_id": "3f2a1b4c-...",
  "status": "pending",
  "message": "Discovery pipeline started. Poll /status/{job_id} for progress."
}
```

**Errors**
| Code | Reason |
|------|--------|
| 500 | Failed to create discovery job (check Supabase connection) |

---

### `GET /api/onboarding/discover/status/{job_id}`
Poll job progress. Call every 2–3 seconds until `status` is `completed` or `failed`.

**Path Parameter** — `job_id`: UUID returned by `POST /discover`

**Response — while running**
```json
{
  "id": "3f2a1b4c-...",
  "user_id": "user_abc",
  "status": "running",
  "stage": "Validating 8 companies found...",
  "progress": 55,
  "result": null,
  "error": null,
  "created_at": "2026-06-14T10:00:00Z",
  "updated_at": "2026-06-14T10:00:45Z"
}
```

**Response — on completion**
```json
{
  "id": "3f2a1b4c-...",
  "status": "completed",
  "stage": "Discovery complete",
  "progress": 100,
  "result": {
    "company": {
      "industry": "Quick Commerce",
      "sub_category": "10-minute Grocery Delivery",
      "key_features": ["10-min delivery", "dark stores", "live tracking"],
      "geographic_focus": "India",
      "target_customers": "Urban households",
      "business_model": "Marketplace"
    },
    "competitors_found": 8,
    "competitors": [
      {
        "id": "uuid-...",
        "name": "Blinkit",
        "website": "https://blinkit.com",
        "color_accent": "#FF6B35",
        "threat_level": "HIGH",
        "signals_found": 4
      }
    ],
    "discovery_summary": "IQOO faces strong competition from Blinkit and Zepto...",
    "total_signals_collected": 27,
    "processing_time_seconds": 48.3
  }
}
```

**Response — on failure**
```json
{
  "status": "failed",
  "stage": "...",
  "progress": 32,
  "error": "Claude API timeout after 3 retries"
}
```

**`status` values**

| Value | Meaning |
|-------|---------|
| `pending` | Job queued, pipeline not yet started |
| `running` | Pipeline active — check `stage` and `progress` |
| `completed` | Full results in `result` field |
| `failed` | See `error` field for reason; partial data may be saved |

**`progress` checkpoints**

| Range | Stage |
|-------|-------|
| 5–12 | Scraping + enriching company profile |
| 15–28 | Claude direct competitor discovery |
| 32–48 | SerpAPI web search |
| 52–70 | Validating & enriching competitors |
| 75–82 | Saving to database |
| 85–94 | Collecting live signals |
| 100 | Complete |

**Errors**
| Code | Reason |
|------|--------|
| 404 | Job not found |

---

## Market Map (v2)

### `GET /api/market-map`
Full competitive landscape for a user — competitors grouped by threat, discovery source, signal activity, and DNA behavioral profiles.

**Query Parameters**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | User whose market map to return |

**Response**
```json
{
  "your_company": {
    "user_id": "user_abc",
    "company_name": "IQOO",
    "industry": "Quick Commerce",
    "sub_category": "10-minute Grocery Delivery",
    "geographic_focus": "India",
    "key_features": ["10-min delivery", "dark stores"],
    "target_customers": "Urban households"
  },
  "market_size": 8,
  "competitors": [
    {
      "id": "uuid-...",
      "name": "Blinkit",
      "website": "https://blinkit.com",
      "color_accent": "#FF6B35",
      "industry": "Quick Commerce",
      "threat_level": "HIGH",
      "threat_reason": "Dominant market leader with 22% share and Zomato backing",
      "competitive_edge": "Scale, dark store density, and brand recognition",
      "description": "Blinkit is India's leading quick-commerce platform...",
      "discovery_pass": 1,
      "signals_24h": 2,
      "dna": {
        "launch_style": "aggressive",
        "expansion_speed": "rapid",
        "price_aggression": 0.7,
        "behavioral_summary": "Blinkit moves fast with funding-fueled expansion..."
      }
    }
  ],
  "competitors_by_threat": {
    "HIGH": [...],
    "MEDIUM": [...],
    "LOW": [...]
  },
  "competitors_by_discovery": {
    "direct_known": [...],
    "search_discovered": [...]
  },
  "most_active_competitor": {
    "name": "Zepto",
    "signal_count_24h": 3
  },
  "total_signals_24h": 11
}
```

**Notes**
- `discovery_pass: 1` = found by Claude directly; `2` = found via SerpAPI web search
- `dna` is `null` if fewer than 5 signals have been collected for that competitor
- `signals_24h` counts signals detected in the last 24 hours

---

## Competitors (v2)

### `GET /api/competitors/`
List active competitors for a user.

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `user_id` | string | required | User ID |
| `active_only` | bool | `true` | Filter to active competitors only |

**Response**
```json
{
  "competitors": [
    {
      "id": "uuid-...",
      "user_id": "user_abc",
      "name": "Blinkit",
      "normalized_name": "blinkit",
      "website": "https://blinkit.com",
      "industry": "Quick Commerce",
      "color_accent": "#FF6B35",
      "is_active": true,
      "created_at": "2026-06-14T10:00:00Z"
    }
  ],
  "total": 8
}
```

---

### `GET /api/competitors/{competitor_id}`
Get a single competitor.

**Response** — Competitor object (same shape as above)

**Errors**
| Code | Reason |
|------|--------|
| 404 | Competitor not found |

---

### `POST /api/competitors/`
Manually add a competitor.

**Request Body**
```json
{
  "user_id": "user_abc",
  "name": "Dunzo",
  "website": "https://dunzo.com",
  "industry": "Quick Commerce",
  "color_accent": "#00FF88"
}
```

**Response** — Created competitor object · `200 OK`

---

### `PUT /api/competitors/{competitor_id}`
Update competitor fields (all optional).

**Request Body**
```json
{
  "name": "Dunzo Daily",
  "website": "https://dunzodaily.com",
  "is_active": false,
  "color_accent": "#FFD700"
}
```

**Response** — Updated competitor object

**Errors**
| Code | Reason |
|------|--------|
| 404 | Competitor not found |

---

### `DELETE /api/competitors/{competitor_id}`
Soft-delete a competitor (sets `is_active = false`).

**Response**
```json
{ "id": "uuid-...", "is_active": false }
```

**Errors**
| Code | Reason |
|------|--------|
| 404 | Competitor not found |

---

## Signals (v2)

### `GET /api/signals/`
List signals with filtering.

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `user_id` | string | required | User ID |
| `competitor_id` | string | — | Filter to one competitor |
| `limit` | int | `50` | Max results (1–200) |
| `offset` | int | `0` | Pagination offset |
| `signal_type` | string | — | Filter by type (e.g. `Hiring`, `Funding`, `Product`, `Marketing`) |

**Response**
```json
{
  "signals": [
    {
      "id": "uuid-...",
      "user_id": "user_abc",
      "competitor_id": "uuid-...",
      "type": "Hiring",
      "title": "Blinkit hiring 20+ roles in Pune",
      "description": "...",
      "source": "https://linkedin.com/...",
      "intent_score": 82,
      "meaning": "Active hiring indicates expansion or product acceleration for Blinkit",
      "raw_data": { "link": "...", "snippet": "..." },
      "is_war_room_trigger": true,
      "detected_at": "2026-06-14T10:15:00Z"
    }
  ],
  "limit": 50,
  "offset": 0
}
```

**`type` values** — `Hiring` · `Marketing` · `Funding` · `Product` · `Expansion` · `Leadership`

---

### `GET /api/signals/high-intent`
Signals above an intent score threshold, sorted highest first.

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `user_id` | string | required | User ID |
| `threshold` | int | `70` | Minimum `intent_score` (0–100) |
| `limit` | int | `20` | Max results (1–100) |

**Response**
```json
{
  "signals": [...],
  "threshold": 70
}
```

---

### `GET /api/signals/war-room-triggers`
Signals flagged as War Room triggers (`is_war_room_trigger = true`), newest first.

**Query Parameters**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | User ID |
| `limit` | int | No | Max results (default 20) |

**Response**
```json
{ "signals": [...] }
```

---

### `GET /api/signals/{signal_id}`
Get one signal by ID.

**Response** — Signal object

**Errors**
| Code | Reason |
|------|--------|
| 404 | Signal not found |

---

## DNA Profiles (v2)

Behavioral profiles built from accumulated signals by `DNAForgeAgent` (Claude). Auto-generated when a competitor reaches 5+ signals.

### `GET /api/dna/`
List all DNA profiles for a user's competitors.

**Query Parameters**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | User ID |

**Response**
```json
{
  "profiles": [
    {
      "id": "uuid-...",
      "competitor_id": "uuid-...",
      "competitor_name": "Blinkit",
      "price_aggression": 0.72,
      "launch_style": "aggressive",
      "expansion_speed": "rapid",
      "expansion_trigger": "funding",
      "signal_to_launch_days": 28,
      "known_weakness": "Customer retention after discount campaigns",
      "patterns": [
        "Blinkit typically launches in a city within 30 days of a hiring spike",
        "Ad spend surges 2 weeks before city launch",
        "Zepto-entry markets trigger defensive pricing from Blinkit"
      ],
      "raw_signals_count": 9,
      "behavioral_summary": "Blinkit operates with funding-fueled aggression, moving into new markets rapidly after capital events.",
      "updated_at": "2026-06-14T10:30:00Z"
    }
  ],
  "total": 5
}
```

---

### `GET /api/dna/{competitor_id}`
Get the DNA profile for one competitor.

**Response** — DNA profile object (same shape as above)

**Errors**
| Code | Reason |
|------|--------|
| 404 | No DNA profile — collect at least 5 signals first |

---

### `POST /api/dna/{competitor_id}/rebuild`
Force-rebuild the DNA profile using the latest 50 signals from Supabase.

**Query Parameters**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `user_id` | string | Yes | User ID (for agent log) |

**Response**
```json
{
  "status": "rebuilt",
  "profile": { ... }
}
```

**Errors**
| Code | Reason |
|------|--------|
| 422 | Fewer than 3 signals — cannot build profile |
| 500 | Claude generation failed |

---

## Analysis (legacy)

### `POST /api/v1/analyze`
Run AI-powered competitor signal analysis (SQLite-backed).

**Request Body**
```json
{
  "competitor_name": "Blinkit",
  "city": "Pune",
  "jobs_added": 23,
  "ad_spend_change": 40,
  "sentiment_change": 5
}
```

**Response**
```json
{
  "summary": "...",
  "prediction": "...",
  "confidence": 78,
  "recommended_actions": ["..."]
}
```

**Errors**
| Code | Reason |
|------|--------|
| 502 | AI provider error |
| 500 | Unexpected error |

---

## Competitors (legacy)

> Prefix: `/api/v1/competitors` · SQLite-backed

### `POST /api/v1/competitors/discover`
Discover competitors and seed the SQLite database.

**Request Body**
```json
{ "company_name": "Dunzo", "website_url": "https://dunzo.com" }
```

**Response**
```json
{
  "status": "success",
  "competitors_found": 3,
  "signals_seeded": 12,
  "competitors": [...],
  "message": "..."
}
```

### `GET /api/v1/competitors/`
List all competitors. **Query param:** `limit` (default 50)

### `POST /api/v1/competitors/`
Create competitor. **Body:** `{ name, industry, website, market_scope }`

### `GET /api/v1/competitors/{competitor_id}`
Get competitor with signals and momentum score.

### `PUT /api/v1/competitors/{competitor_id}`
Update competitor metadata.

### `DELETE /api/v1/competitors/{competitor_id}`
Hard-delete competitor and all cascaded data.

### `GET /api/v1/competitors/{competitor_id}/momentum`
**Response:** `{ competitor_name, momentum_score, signal_count, prediction_count, recent_signals, latest_prediction }`

### `GET /api/v1/competitors/{competitor_id}/signals`
**Query params:** `signal_type` · `sort_by` (newest|impact|urgency) · `limit`

---

## Signals (legacy)

> Prefix: `/api/v1/signals` · SQLite-backed

### `GET /api/v1/signals/`
**Query params:** `signal_type` · `competitor_id` · `search` · `sort_by` · `limit`

### `POST /api/v1/signals/`
**Body:** `{ competitor_id, signal_type, title, description, source, impact_score, urgency_score }`
**Errors:** `404` — competitor not found

### `GET /api/v1/signals/{signal_id}`
**Errors:** `404` — signal not found

---

## Predictions

> Prefix: `/api/v1/predictions` · SQLite-backed

### `GET /api/v1/predictions/`
**Query params:** `competitor_id` · `limit`

### `POST /api/v1/predictions/`
**Body:** `{ competitor_id, prediction, confidence, threat_level, ai_reasoning }`

### `GET /api/v1/predictions/{prediction_id}`
**Errors:** `404` — prediction not found

---

## War Room

> Prefix: `/api/v1/warroom` · SQLite-backed

### `POST /api/v1/warroom/analyze`
Full War Room analysis via 4 AI agents (Marketing, Product, Sales, Strategy).

**Query Parameters**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `competitor_name` | string | Yes | Competitor to analyse |
| `city` | string | Yes | Target city |
| `jobs_added` | int | No | New hires count |
| `ad_spend_change` | int | No | Ad spend change % |
| `sentiment_change` | int | No | Sentiment shift |
| `include_agents` | bool | No | Include per-agent breakdown |

### `POST /api/v1/warroom/reports`
Save a War Room report. **Body:** `WarRoomReportCreate` schema

### `GET /api/v1/warroom/reports`
**Query param:** `competitor_id` (optional filter)

### `GET /api/v1/warroom/reports/{report_id}`
**Errors:** `404` — report not found

---

## Alerts

> Prefix: `/api/v1/alerts` · SQLite-backed

### `GET /api/v1/alerts/`
**Query param:** `competitor_id`

### `POST /api/v1/alerts/`
**Body:** `{ competitor_id, alert_type, threshold, enabled }`

### `PUT /api/v1/alerts/{alert_id}`
Update threshold / enabled status. **Errors:** `404`

### `DELETE /api/v1/alerts/{alert_id}`
**Response:** `204 No Content` · **Errors:** `404`

---

## AI Agents

> Prefix: `/api/v1/agents` · SQLite-backed

### `GET /api/v1/agents/`
List available agents.

**Response**
```json
[
  { "name": "marketing", "description": "...", "status": "ready" },
  { "name": "product",   "description": "...", "status": "ready" },
  { "name": "sales",     "description": "...", "status": "ready" },
  { "name": "strategy",  "description": "...", "status": "ready" }
]
```

### `POST /api/v1/agents/{agent_name}/analyze`
Run one agent. **Path:** `agent_name` = `marketing` | `product` | `sales` | `strategy`
**Query param:** `context` (string) — competitor/market context
**Errors:** `404` — unknown agent

### `POST /api/v1/agents/chat`
Chat with competitive intelligence AI.

**Request Body**
```json
{
  "message": "What is Zepto's latest funding activity?",
  "competitor_id": "comp-zepto"
}
```

`competitor_id` is optional. Falls back to curated mock responses when no AI provider is configured.
Keywords triggering specific mocks: `funding` · `hiring` · `pricing` · `expansion`

**Response**
```json
{ "reply": "...", "model_used": "ClaudeProvider" }
```

### `GET /api/v1/agents/activity`
Live agent activity feed from `agent_logs` table (most recent first).

**Query Parameters**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | `30` | Max entries (1–100) |
| `offset` | int | `0` | Pagination offset |
| `user_id` | string | `"system"` | Filter by user |

**Response**
```json
{
  "activity": [
    {
      "id": "uuid-...",
      "agent_name": "DiscoveryAgent",
      "action": "Added competitor: Blinkit",
      "reasoning": "Direct competitor in quick-commerce India with 22% market share",
      "competitor_name": "Blinkit",
      "created_at": "2026-06-14T10:05:00Z"
    }
  ]
}
```

### `GET /api/v1/agents/status`
Autonomy system status — live metrics from the autonomous monitoring loop.

**Response**
```json
{
  "total_competitors": 8,
  "active_competitors": 8,
  "total_signals": 43,
  "total_predictions": 6,
  "total_war_rooms": 2,
  "last_cycle_run": "2026-06-14T08:00:00Z",
  "next_cycle_run": "2026-06-14T12:00:00Z",
  "scheduler_running": true
}
```

---

## Competitive DNA (legacy)

> Prefix: `/api/v1/dna` · SQLite-backed (pattern-based, not Claude-generated profiles)

### `GET /api/v1/dna/`
**Query params:** `competitor_id` · `pattern_type` · `limit`

### `GET /api/v1/dna/{pattern_id}`
**Errors:** `404`

### `POST /api/v1/dna/`
**Body:** `{ competitor_id, pattern_type, description, confidence_score }`
**Errors:** `404` — competitor not found

### `PUT /api/v1/dna/{pattern_id}`
All fields optional. **Errors:** `404`

### `DELETE /api/v1/dna/{pattern_id}`
`204 No Content` · **Errors:** `404`

### `GET /api/v1/dna/similar/{signal_type}`
Vector similarity search.
**Query params:** `impact_score` (default 5.0) · `top_k` (default 5)

### `GET /api/v1/dna/analyze/{competitor_id}`
Full DNA analysis by ID. **Errors:** `404`

### `GET /api/v1/dna/analyze/by-name/{competitor_name}`
Full DNA analysis by name. **Errors:** `404`

---

## Graph

> Prefix: `/api/v1/graph` · SQLite-backed

### `GET /api/v1/graph/competitive/{company_name}`
Full competitive relationship graph.

**Response**
```json
{
  "company": "Blinkit",
  "nodes": [
    { "id": "comp-blinkit", "name": "Blinkit", "type": "Company", "industry": "Quick Commerce" }
  ],
  "relationships": [
    { "source": "comp-blinkit", "target": "comp-zepto", "type": "COMPETES_WITH", "intensity": 0.95 }
  ]
}
```

### `GET /api/v1/graph/nodes`
All competitor nodes.

### `GET /api/v1/graph/relationships`
All competitive relationships with resolved names.

### `GET /api/v1/graph/dna/{competitor_name}`
DNA behavioral profile for a company.

**Response**
```json
{
  "company": "Blinkit",
  "patterns": [{ "pattern": "...", "pattern_type": "hiring_spike", "confidence": 0.85 }],
  "behavioral_signature": "...",
  "momentum_score": 72.5,
  "signal_count": 3
}
```
**Errors:** `404`

---

## Onboarding (legacy)

> Prefix: `/api/v1/onboarding` · SQLite-backed

### `POST /api/v1/onboarding/setup`
Synchronous onboarding — seeds competitors, discovers more, hunts signals, builds DNA. Returns when all phases complete (~15–30s).

**Request Body**
```json
{
  "company_name": "IQOO",
  "industry": "Quick Commerce",
  "main_product": "10-minute grocery delivery",
  "geographic_focus": "India",
  "website_url": "https://iqoo.com",
  "user_id": "user_abc"
}
```

**Response**
```json
{
  "status": "active",
  "user_id": "user_abc",
  "competitors_seeded": 6,
  "competitors_discovered": 4,
  "signals_collected": 32,
  "dna_profiles_created": 5,
  "message": "Autonomy activated. Monitoring 10 competitors with 32 signals..."
}
```

> **Prefer** `POST /api/onboarding/discover` (v2) for the async fire-and-poll experience with progress tracking.

---

## Admin / Demo

> Prefix: `/api/v1/admin` · For hackathon demos and judges only

### `POST /api/v1/admin/simulate-time-passage`
Fast-forward N days of autonomous monitoring for one competitor in seconds.

Each simulated "day" runs: SignalHunterAgent → DNAForgeAgent (every 5 days) → PredictionEngine → War Room activation (if threshold met).

**Request Body**
```json
{
  "competitor_id": "comp-blinkit",
  "days": 30,
  "user_id": "system"
}
```

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `competitor_id` | string | required | Must exist in DB |
| `days` | int | 1–90 | Days to fast-forward |
| `user_id` | string | optional | Default: `"system"` |

**Response**
```json
{
  "competitor_id": "comp-blinkit",
  "days_simulated": 30,
  "signals_generated": 87,
  "dna_updated": true,
  "prediction_fired": true,
  "war_room_activated": true,
  "activity_entries": 94,
  "message": "Simulated 30 days of autonomous monitoring for Blinkit. 87 signals generated, DNA profile built, prediction fired, War Room activated."
}
```

**Errors**
| Code | Reason |
|------|--------|
| 404 | Competitor not found |

---

## Data Models Reference

### Signal `type` values
`Hiring` · `Marketing` · `Funding` · `Product` · `Expansion` · `Leadership`

### Threat levels
`LOW` · `MEDIUM` · `HIGH`

### DNA `launch_style`
`gradual` · `aggressive` · `stealth`

### DNA `expansion_speed`
`slow` · `moderate` · `rapid`

### DNA `expansion_trigger`
`funding` · `hiring` · `partnerships` · `organic`

### `intent_score` (0–100)
| Range | Meaning |
|-------|---------|
| 0–30 | Low signal, noise or irrelevant |
| 31–60 | Worth monitoring |
| 61–74 | High-priority signal |
| 75–100 | War Room trigger — immediate action recommended |

---

## Quick-Reference curl Examples

```bash
# Start discovery
curl -X POST http://localhost:8000/api/onboarding/discover \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","company_name":"IQOO","website":"https://iqoo.com","description":"Quick commerce in India"}'

# Poll status
curl http://localhost:8000/api/onboarding/discover/status/<job_id>

# Market map
curl "http://localhost:8000/api/market-map?user_id=u1"

# High-intent signals
curl "http://localhost:8000/api/signals/high-intent?user_id=u1&threshold=75"

# War Room trigger signals
curl "http://localhost:8000/api/signals/war-room-triggers?user_id=u1"

# DNA profile
curl "http://localhost:8000/api/dna/<competitor_id>"

# Rebuild DNA
curl -X POST "http://localhost:8000/api/dna/<competitor_id>/rebuild?user_id=u1"

# Simulate 30 days (demo)
curl -X POST http://localhost:8000/api/v1/admin/simulate-time-passage \
  -H "Content-Type: application/json" \
  -d '{"competitor_id":"comp-blinkit","days":30}'
```
