# MarketWatch — Complete Project Description

---

## What We're Building

A **multi-agent AI market intelligence platform** that gives every startup and SMB an always-on strategic intelligence team. The user enters their company and competitors — the system takes over from there, continuously monitoring the market and telling them not just what happened, but what's about to happen and exactly what to do about it.

---

## The Core Differentiator

> **Every other team will build a market monitor. We're building a market strategist.**

Every existing tool — Crayon, Klue, Similarweb — and every other team in this hackathon will build the same thing: agents that collect data and display a feed. That is **reactive intelligence**.

MarketWatch operates on three levels no other tool reaches:

```
Level 1 — REACTIVE     "Blinkit launched a new ad campaign yesterday."
                        (Every other team stops here)

Level 2 — PREDICTIVE   "Based on their hiring pattern + ad spend, Blinkit
                        is likely entering Pune in 3-4 weeks. Confidence: 78%"
                        (We go here)

Level 3 — PRESCRIPTIVE "Here's the counter-campaign you should run this week,
                        the sales email targeting their churning clients, and
                        the product feature to fast-track."
                        (And here)
```

The gap between Level 1 and Level 3 is what separates a dashboard from a strategist.

---

## Who It's For

Startups and SMBs that operate in fast-moving markets but don't have dedicated market research, competitive intelligence, or strategy teams. A 10-person startup competing against a funded competitor gets the same intelligence firepower as an enterprise with a full analyst team.

---

## The 4 Agents

All 4 agents from the problem statement — but each is significantly more capable than a basic monitor.

### Marketing AI
**Monitors:** Google Trends, Meta Ad Library, competitor social media, regional ad campaigns, viral content

**Does more than monitor:**
- Scores every signal by urgency and business impact
- Detects shifts in competitor messaging strategy over time
- Identifies gaps in competitor campaigns that are exploitable
- Flags trending keywords competitors are not targeting yet

**Example output:**
```
Blinkit increased Google Ads spend by 40% in Pune this week.
Historical match: They did this before Hyderabad and Chennai launches.
Predicted move: Pune launch in 3-5 weeks (confidence: 74%)
Your window: 3 weeks to establish brand presence before they arrive.
```

---

### Product AI
**Monitors:** App Store reviews, Play Store reviews, Reddit, G2, Trustpilot, product forums, feature request boards

**Does more than monitor:**
- Sentiment trend tracking (not just current rating, but direction)
- Extracts specific pain points users have with competitor products
- Identifies feature gaps the market is asking for that nobody has built yet
- Tracks product update frequency and release patterns

**Example output:**
```
Swiggy Instamart: App rating dropped from 3.8 → 2.3 in Bangalore over 6 weeks.
Top complaint (847 mentions): "Delivery time estimates are always wrong"
Opportunity: ~40,000 active frustrated users in your core market.
Suggested action: Targeted campaign on delivery accuracy is ready.
```

---

### Sales AI
**Monitors:** LinkedIn job postings, Crunchbase funding news, company hiring patterns, B2B signal platforms, executive movement

**Does more than monitor:**
- Reads hiring patterns as expansion/contraction signals
- Detects when a competitor's key talent is leaving (decline signal)
- Identifies companies that just got funded and are now buying (lead signal)
- Tracks competitor sales team size changes as market aggression indicator

**Example output:**
```
Blinkit: 23 ops + logistics hires in Pune in the past 2 weeks.
Pattern match: Same pre-launch hiring signature seen before Hyderabad (2024).
Lead opportunity: 3 Pune-based restaurant chains currently on Swiggy only —
                  approaching them now before Blinkit arrives is high priority.
```

---

### Strategy AI
**The synthesis layer.** Reads all three agents' outputs, cross-references the Competitive DNA store, and produces:
- Weekly strategic brief with threats, opportunities, and recommended actions
- Real-time war room briefs when critical threats are detected
- Scenario planning ("If competitor raises a round, here's your playbook")
- Drafted counter-moves (ad copy, sales emails, product priorities)

**Does more than summarize:**
- Ranks every recommendation by impact vs. effort
- Assigns confidence scores to every prediction
- Cross-references patterns across all competitors simultaneously
- Flags contradictions between agent findings before they reach you

---

## The Architecture Layers

### Layer 1 — Perception
Raw data ingestion running continuously every 6 hours:
- SerpAPI for search trends and ad monitoring
- Reddit API for community signals
- NewsAPI + RSS feeds for industry news
- LinkedIn scraping for hiring signals
- App Store / Play Store for review monitoring
- Meta Ad Library for competitor ad tracking
- Crunchbase for funding signals

### Layer 2 — Signal Extraction
Agents process raw data into scored, classified signals:

```
Every signal gets:
  - Type: Threat / Opportunity / Neutral
  - Urgency: Immediate / This Week / This Month
  - Impact: High / Medium / Low
  - Confidence: % with source citations
  - Business implication: one-line "why this matters"
```

### Layer 3 — Competitive DNA Store
The most important architectural innovation. A **living knowledge graph** for each competitor stored in a vector database, continuously updated by all 3 monitoring agents.

Not just events — **patterns**:
```
Blinkit DNA Profile:
  Expansion pattern:  Ops hiring → 5-6 weeks → city launch (seen 4x)
  Pricing pattern:    Discount spike → 2-3 weeks → fundraise announcement (seen 2x)
  Product pattern:    App update every 3 weeks, major feature every quarter
  Current signals:    Pune ops hiring (matches expansion pattern)
  Predicted move:     Pune launch in 3-5 weeks (confidence: 74%)
  Momentum score:     8.4/10 ↑ (+1.2 this week) — Accelerating
```

This is what makes the system learn over time. Week 1 it monitors. Week 4 it predicts. Week 12 it knows your competitors better than they know themselves.

### Layer 4 — Prediction Engine
Pattern matching between current signals and historical Competitive DNA:

- Compares current signal signatures against all past patterns in the DNA store
- Generates probability-weighted predictions for competitor moves
- Assigns confidence scores based on how closely the current pattern matches historical ones
- Decays confidence when data is sparse (honest about uncertainty)

### Layer 5 — Action Generation
Strategy AI doesn't just brief — it drafts the response:

```
Threat detected: Competitor entering your market in 3-5 weeks
Drafted actions ready:
  → Google Ad copy targeting their weakness [deploy in 1 click]
  → Twitter post capitalizing on their low app rating [review + post]
  → Sales email for 3 high-priority leads before competitor arrives [send]
  → Product brief: which feature to fast-track this sprint [export]
```

---

## War Room Mode

When a critical threat is detected (impact: HIGH, urgency: IMMEDIATE), the system auto-triggers a War Room:

```
🚨 CRITICAL THREAT
"Swiggy announced free delivery for 6 months in your core market"

[WAR ROOM ACTIVATED — EST. 90 SECONDS]
Marketing AI  → analyzing their ad reach, spend, messaging angle
Product AI    → analyzing user reaction and sentiment shift
Sales AI      → identifying churn risk in your B2B clients
Strategy AI   → synthesizing response brief

[BRIEF READY]
Option A: Match the offer (cost analysis attached)
Option B: Counter on speed, not price (recommended — here's the campaign)
Option C: Double down on B2B segment they're ignoring (lowest risk)
```

This is a live demo moment that no other team will have.

---

## Competitor Momentum Score

A single number per competitor updated weekly. Judges understand it instantly, no explanation needed:

```
Competitor        Score      Change      Status
─────────────────────────────────────────────────
Blinkit           8.4/10     ↑ +1.2      Accelerating
Swiggy Instamart  5.1/10     → +0.1      Stable
Zepto (you)       6.8/10     ↑ +0.9      Growing
```

Composite of: hiring velocity + ad spend change + product update frequency + funding recency + sentiment trend.

---

## Blind Spot Transparency

No intelligence tool does this honestly. MarketWatch explicitly surfaces what it **couldn't find**:

```
⚠️ Data gaps this week:
  Blinkit's Hyderabad ops: LinkedIn blocked 3 fetches
  Swiggy's ad spend: Meta Ad Library data delayed 48hrs
  Reddit: No mentions of competitor in last 7 days

Confidence in Hyderabad analysis: LOW — treat as directional only
```

This builds trust. Judges will notice that this system is honest, which makes every high-confidence prediction land harder.

---

## Alerts — Where Users Actually Are

Three alert channels, configured by the user:

**In-app:** Real-time banner on dashboard, push notification on mobile

**WhatsApp:** (SMBs live here)
```
🔴 MarketWatch Alert
Blinkit posted 18 ops jobs in Pune overnight.
Expansion signal detected. Confidence: 74%
Reply BRIEF for full analysis.
```

**Slack:** Drops alert in team channel with a thread containing the full brief

This is critical because SMBs don't check dashboards every hour. The intelligence has to reach them where they already are.

---

## Alert Customization

Users define their own thresholds:
```
Alert me when:
  ☑ Competitor app rating drops below 3.0
  ☑ Competitor posts more than 10 jobs in a week
  ☑ My sector gets a funding announcement > $5M
  ☑ Any competitor runs ads in a new city
  ☐ Competitor mentioned in news
```

---

## Geography

**Generic by default, city-wise when needed.**

At onboarding:
```
Company: Zepto
Competitors: Blinkit, Swiggy Instamart
Market scope: Bangalore, Pune, Mumbai   ← optional
Industry: Quick Commerce
```

A hyperlocal business tracks city by city. A SaaS company tracks nationally. A D2C brand tracks by region. The system adapts to how the user defines their market.

---

## OfficeKit Integration

Since this is iQOO's platform, the weekly Strategy AI brief exports directly in formats openable in OfficeKit:

- **PDF** — Formatted competitive intelligence brief with charts and citations
- **PPTX** — 5-slide auto-generated competitive deck (ready to present)
- **XLSX** — Raw signal data with agent breakdown per competitor

The weekly brief is auto-generated every Monday and pushed to the user's OfficeKit folder.

---

## "Why It Matters" Layer

Every single signal has a one-line business implication — no raw data without meaning:

```
Signal: Competitor's app rating dropped to 2.3
Why it matters → ~40,000 frustrated users actively looking for alternatives.
                  This is your acquisition window.

Signal: Competitor hired 3 senior engineers from Google
Why it matters → Likely building a major technical feature in 2-3 months.
                  Watch their product roadmap closely.

Signal: Competitor's CEO posted about "new markets" on LinkedIn
Why it matters → Expansion announcement likely within 2 weeks.
                  Prepare your positioning in adjacent cities.
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Agents | Claude API with tool use |
| Backend | Python + FastAPI |
| Agent Scheduler | APScheduler (every 6 hours) |
| Competitive DNA Store | PostgreSQL + Pinecone (vector DB) |
| Real-time Alerts | WebSockets + Redis pub/sub |
| WhatsApp Alerts | Twilio WhatsApp API |
| Slack Alerts | Slack Webhooks |
| Data Sources | SerpAPI, Reddit API, NewsAPI, Meta Ad Library, RSS |
| Frontend | Next.js + Tailwind (mobile-first) |
| Report Export | ReportLab (PDF), python-pptx (PPTX) |
| Hosting | Railway / Render |

---

## Demo Flow for Judges

```
1. Sign up → enter "Zepto vs Blinkit, Swiggy — Bangalore, Pune"
2. Dashboard loads — Momentum Scores visible immediately
3. Live agent run — show agents working with status indicators
4. Marketing agent surfaces real Blinkit ad campaign
5. Sales agent shows Pune hiring spike → prediction fires (74%)
6. Product agent shows Swiggy's low app rating → opportunity flagged
7. Trigger War Room manually — agents collaborate in real-time
8. Strategy AI generates brief in 90 seconds
9. Show WhatsApp alert arriving on phone
10. Export weekly brief → opens in OfficeKit
11. Pull up on mobile — full mobile-first experience
```

---

## One-Line Pitch

> "Every other tool tells you what happened. MarketWatch tells you what's coming and hands you the counter-move — giving every startup the strategic intelligence firepower of a Fortune 500 research team."
