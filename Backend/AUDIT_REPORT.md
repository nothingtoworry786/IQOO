# MarketWatch Backend Audit Report
**Date:** 2026-06-14  
**Auditor:** Claude Code  
**Scope:** All files in `/app/agents`, `/app/services`, `/app/routes`, `/app/routers`, `/app/core`, `/app/workers`

---

## Phase 1 — Audit Findings

| # | File | Line(s) | What it is | Why it's a problem | Fix |
|---|------|---------|-----------|-------------------|-----|
| 1 | `app/agents/market_discovery_agent.py` | 122 | `discover_competitors(company_name, industry, key_features, geo)` — 4 positional args to an 8-parameter function | Raises `TypeError` at runtime, crashing every Supabase v2 discovery job silently | Fixed: updated to keyword-arg call with all 8 params |
| 2 | `app/agents/market_discovery_agent.py` | import block | `recheck_competitors` not imported or called in the Supabase path | Wrong-industry companies from pass1 passed through unchecked (old SQLite path had recheck, Supabase path didn't) | Fixed: imported and added recheck call after pass1 |
| 3 | `app/agents/prediction_engine.py` | 72–76, 192–196 | `json.loads()` on raw Gemma4 output without stripping `<think>` blocks | On Ollama/Gemma4, `<think>...</think>` blocks appear before JSON — direct `json.loads()` throws `JSONDecodeError`, prediction and war-room never fire | Fixed: added `re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)` before parse in both functions |
| 4 | `app/core/config.py` | class body + `__init__` | `RAPIDAPI_KEY` missing from `Settings` | `.env` has `RAPIDAPI_KEY` but `settings.RAPIDAPI_KEY` would raise `AttributeError`; any future LinkedIn collector would silently break | Fixed: added `RAPIDAPI_KEY: str = ""` to class and `__init__` |
| 5 | `main.py` | lifespan | No startup log showing which external APIs are configured | Cannot tell from logs whether signal collection is active or disabled | Fixed: added structured log block listing SerpAPI/RapidAPI/httpx status |

### Not Flagged (Correct Behavior)
| Item | Reason |
|------|--------|
| `enrich_company_profile()` fallback dict | Graceful error handling — only returned when Claude call fails, never unconditionally |
| `generate_dna_profile()` fallback dict | Same — real AI call attempted first; fallback clearly labelled in `known_weakness` field |
| `validate_competitor()` fallback dict | Same |
| `recheck_competitors()` returning unfiltered list on failure | Acceptable: better to return unfiltered competitors than lose all of them |
| `signal_hunter.py` returning `[]` when `SERPAPI_KEY` missing | Correct graceful degradation per spec |
| `search_tool.py` returning `[]` when `SERPAPI_KEY` missing | Same |
| `OLLAMA_HOST` defaulting to `localhost:11434` | Expected dev default, overridden in `.env` |

### YouTube / Reddit
**None found.** No `youtube`, `YOUTUBE_API_KEY`, `collect_youtube_signals`, `reddit`, or `collect_reddit_signals` references exist anywhere in the codebase. `requirements.txt` has no `google-api-python-client` or PRAW. Nothing to remove.

---

## Phase 2 — Changes Made

### 1. `app/agents/market_discovery_agent.py`
- Added `recheck_competitors` to imports from `app.services.claude`
- Added `target_customers = enriched.get(...)` and `scraped_desc = description[:400]` variable extractions
- Replaced broken `discover_competitors(company_name, industry, key_features, geo)` with full 8-keyword-arg call
- Added `recheck_competitors()` call immediately after pass1 discovery

### 2. `app/agents/prediction_engine.py`
- `run_prediction()`: replaced raw `.strip()` with `re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()` before JSON parse
- `generate_battle_plan()`: same fix applied

### 3. `app/core/config.py`
- Added `RAPIDAPI_KEY: str = ""` class-level default
- Added `self.RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")` in `__init__`

### 4. `main.py`
- Added startup log block in `lifespan()` after `setup_scheduler()`:
  - SerpAPI: configured/missing
  - RapidAPI: configured/missing (optional)
  - httpx scraping: always active

---

## Phase 3 — Data Flow Verification

| Flow | Status | Notes |
|------|--------|-------|
| `POST /api/v1/competitors/discover` → enrich → discover → recheck → validate → DB | ✅ Real data flow | Uses `competitor_analysis.py` + `claude.py` — all real Claude calls, real SQLite writes |
| `POST /api/onboarding/discover` → Supabase path | ✅ Fixed | Was broken (TypeError in `discover_competitors` call) — now fixed with 8-param call + recheck |
| `GET /api/market-map` | ✅ Real data flow | Reads from Supabase `competitors`, `competitor_profiles`, `dna_profiles` tables |
| `GET /api/signals/` | ✅ Real data flow | Reads from Supabase `signals` table, filtered by real `user_id` |
| Signal `source` field | ✅ No YouTube/Reddit | Sources are SerpAPI URLs or "Google Search" only |
| `POST /api/v1/admin/simulate-time-passage` → predictions | ✅ Fixed | `<think>` blocks now stripped before JSON parse in prediction engine |
| War Room activation | ✅ Fixed | `generate_battle_plan()` now strips `<think>` blocks |
| `GET /api/v1/agents/activity` | ✅ Real data flow | Reads `agent_logs` table via SQLAlchemy — logs written by real agent runs |
| `GET /api/dna/` | ✅ Real data flow | Reads from Supabase `dna_profiles` — populated by `forge_dna_profile()` after signal collection |
| ChromaDB `add_signals()` | ✅ Real data flow | Called from `_hunt_and_save_signals()` after Supabase insert; upserts real signal documents |
| `find_similar_patterns()` / `query_similar()` | ✅ Real data flow | Queries real ChromaDB collections populated during discovery |

---

## Phase 4 — ChromaDB

- `chromadb_service.py:add_signals()` is called from `market_discovery_agent.py:_hunt_and_save_signals()` after each signal is saved to Supabase. Collections are populated with real signal data.
- `chromadb_service.py:query_similar()` queries real embedded data — no hardcoded return.
- ChromaDB `PersistentClient` initialized lazily on first use; path comes from `settings.CHROMADB_PATH` (env var, defaults to `./chromadb_data`).

---

## Phase 5 — Environment-Dependent Behavior

| API | Config check | Behavior when key missing | Behavior when key present |
|-----|-------------|--------------------------|--------------------------|
| SerpAPI | `settings.SERPAPI_KEY` | Returns `[]` — signal collection disabled | Real httpx calls to `serpapi.com/search` |
| RapidAPI (LinkedIn) | `settings.RAPIDAPI_KEY` | N/A — no LinkedIn collector implemented yet | N/A |
| Anthropic/Groq/OpenRouter | Provider-specific key check | Falls back to `AI_PROVIDER=none` at startup | Real API calls |
| Ollama | No key needed | Connects to `OLLAMA_HOST` | Real local model calls |
| httpx scraping | No key needed | Always active | Scrapes website content for enrichment |
| ChromaDB | No cloud key needed (local) | Uses local `./chromadb_data` directory | Persistent local vector store |

Startup log now emits one line per API clearly showing configured vs. missing.

---

## Summary

| Metric | Value |
|--------|-------|
| Dummy data blocks removed | 0 (none existed — previous session cleaned them) |
| YouTube collector removed | N/A (none existed) |
| Reddit collector removed | N/A (none existed) |
| Critical bugs fixed | 2 (TypeError in discover_competitors call; missing `<think>` stripping in prediction engine) |
| Missing features added | 1 (recheck_competitors in Supabase discovery path) |
| Config additions | 1 (RAPIDAPI_KEY) |
| Startup log improvements | 1 (API status block in lifespan) |
| Stub functions marked 501 | 0 (all stub agents make real AI calls via BaseAgent.analyze()) |
| Hardcoded credentials moved | 0 (all keys already loaded from env vars) |

## Active Signal Sources (Post-Audit)
- SerpAPI: News / Hiring / Funding / Product launches ✅ (graceful `[]` when key missing)
- RapidAPI (LinkedIn): key tracked in config, no collector implemented yet
- Web scraping (httpx + BeautifulSoup): ✅ always active — no key required

## Remaining Known Gaps
- No LinkedIn signal collector (`RAPIDAPI_KEY` is now tracked in config but no `collect_linkedin_signals()` function exists — returns nothing for LinkedIn)
- Autonomous orchestrator (`autonomy_orchestrator.py`) reads competitors from SQLite (old v1 stack). If a user's competitors were added exclusively via the Supabase v2 path, the autonomous cycle finds 0 competitors. These are two separate DB stacks with no sync layer — acceptable for current dual-stack state but worth noting.

## Verified Live Data Flows
1. `POST /api/v1/competitors/discover` ✅
2. `POST /api/onboarding/discover` ✅ (fixed)
3. `GET /api/market-map` ✅
4. `GET /api/signals/` ✅
5. `POST /api/v1/admin/simulate-time-passage` → predictions ✅ (fixed)
6. War Room battle plan generation ✅ (fixed)
7. `GET /api/war-room/status` (via `GET /api/v1/warroom/reports`) ✅
8. `GET /api/v1/agents/activity` ✅
