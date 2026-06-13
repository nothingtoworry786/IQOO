# CompetitorGPT / MarketWatch — Backend

Competitive intelligence engine: **FastAPI + Supabase + Anthropic Claude + SerpAPI + ChromaDB**.

Submit a company intake form → autonomous 7-step pipeline discovers competitors, collects live signals, builds behavioral DNA profiles, and triggers War Room alerts for high-threat events.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt
# or with uv: uv sync

# 2. Copy env template
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY

# 3. Run Supabase schema (copy SQL below into Supabase SQL Editor)

# 4. Start server
uvicorn main:app --reload --port 8000
# Docs at http://localhost:8000/docs
```

---

## Supabase SQL Schema

Paste into **Supabase Dashboard → SQL Editor → New Query**:

```sql
-- Company profiles (one per user)
CREATE TABLE IF NOT EXISTS company_profiles (
  user_id          TEXT PRIMARY KEY,
  company_name     TEXT NOT NULL,
  website          TEXT,
  description      TEXT,
  industry         TEXT,
  sub_category     TEXT,
  key_features     JSONB DEFAULT '[]',
  geographic_focus TEXT,
  target_customers TEXT,
  business_model   TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Async pipeline jobs
CREATE TABLE IF NOT EXISTS discovery_jobs (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'pending',  -- pending|running|completed|failed
  stage      TEXT,
  progress   INTEGER DEFAULT 0,               -- 0-100
  result     JSONB,
  error      TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Competitors
CREATE TABLE IF NOT EXISTS competitors (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         TEXT NOT NULL,
  name            TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  website         TEXT,
  industry        TEXT,
  color_accent    TEXT DEFAULT '#6C63FF',
  is_active       BOOLEAN DEFAULT TRUE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS competitors_user_norm
  ON competitors (user_id, normalized_name);

-- Competitor profiles (1:1)
CREATE TABLE IF NOT EXISTS competitor_profiles (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_id    UUID REFERENCES competitors(id) ON DELETE CASCADE,
  description      TEXT,
  threat_level     TEXT DEFAULT 'MEDIUM',
  threat_reason    TEXT,
  competitive_edge TEXT,
  discovery_pass   INTEGER DEFAULT 1,
  updated_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (competitor_id)
);

-- Signals
CREATE TABLE IF NOT EXISTS signals (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             TEXT NOT NULL,
  competitor_id       UUID REFERENCES competitors(id) ON DELETE CASCADE,
  type                TEXT,
  title               TEXT,
  description         TEXT,
  source              TEXT,
  intent_score        INTEGER DEFAULT 0,
  meaning             TEXT,
  raw_data            JSONB,
  is_war_room_trigger BOOLEAN DEFAULT FALSE,
  detected_at         TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS signals_competitor_idx ON signals (competitor_id);
CREATE INDEX IF NOT EXISTS signals_user_date_idx  ON signals (user_id, detected_at DESC);

-- DNA profiles (1:1)
CREATE TABLE IF NOT EXISTS dna_profiles (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_id         UUID REFERENCES competitors(id) ON DELETE CASCADE,
  user_id               TEXT,
  price_aggression      FLOAT,
  launch_style          TEXT,
  expansion_speed       TEXT,
  expansion_trigger     TEXT,
  signal_to_launch_days INTEGER,
  known_weakness        TEXT,
  patterns              JSONB DEFAULT '[]',
  raw_signals_count     INTEGER DEFAULT 0,
  behavioral_summary    TEXT,
  updated_at            TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (competitor_id)
);

-- Agent activity log
CREATE TABLE IF NOT EXISTS agent_logs (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       TEXT DEFAULT 'system',
  competitor_id UUID REFERENCES competitors(id) ON DELETE SET NULL,
  agent_name    TEXT NOT NULL,
  action        TEXT NOT NULL,
  reasoning     TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS agent_logs_user_idx ON agent_logs (user_id, created_at DESC);
```

---

## API Reference

### Discovery Pipeline (fire-and-poll)

**Start discovery:**
```
POST /api/onboarding/discover
{
  "user_id": "user_abc",
  "company_name": "IQOO",
  "website": "https://iqoo.com",
  "description": "Quick-commerce platform in India"
}
→ { "job_id": "uuid-...", "status": "pending" }
```

**Poll status (every 2-3s):**
```
GET /api/onboarding/discover/status/{job_id}
→ { "status": "running", "stage": "Validating 8 companies...", "progress": 55 }
→ { "status": "completed", "progress": 100, "result": { "competitors": [...] } }
```

### Market Map
```
GET /api/market-map?user_id=user_abc
```
Returns: competitors by threat level, by discovery method, 24h signal counts, DNA profiles.

### Competitors
```
GET    /api/competitors?user_id=user_abc
GET    /api/competitors/{id}
POST   /api/competitors
PUT    /api/competitors/{id}
DELETE /api/competitors/{id}
```

### Signals
```
GET /api/signals?user_id=user_abc&competitor_id=&limit=50
GET /api/signals/high-intent?user_id=user_abc&threshold=70
GET /api/signals/war-room-triggers?user_id=user_abc
GET /api/signals/{id}
```

### DNA Profiles
```
GET  /api/dna?user_id=user_abc
GET  /api/dna/{competitor_id}
POST /api/dna/{competitor_id}/rebuild?user_id=user_abc
```

---

## Architecture

```
POST /api/onboarding/discover
  └─ asyncio.create_task(run_discovery_pipeline)
       Step 1  scrape_and_analyze(website)          ← httpx + BS4
       Step 2  claude.enrich_company_profile()       ← Anthropic
       Step 3  claude.discover_competitors()         ← Pass 1 (5 names)
       Step 4  SerpAPI searches + claude.extract_new_competitors()  ← Pass 2
       Step 5  claude.validate_competitor() × N     ← Pass 3
       Step 6  INSERT into competitors + competitor_profiles
       Step 7  hunt_signals() × N (parallel)        ← SerpAPI × 4 query types
               └─ INSERT into signals
               └─ chromadb.add_signals()
               └─ forge_dna_profile() if signals ≥ 5
       Step 8  UPDATE discovery_jobs SET status='completed', result={...}
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_KEY` | Yes | Anon or service role key |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `SERPAPI_KEY` | No | SerpAPI key (signals gracefully empty without it) |
| `CHROMADB_PATH` | No | Local ChromaDB directory (default: `./chromadb_data`) |
| `ANTHROPIC_MODEL` | No | Default: `claude-sonnet-4-6` |
