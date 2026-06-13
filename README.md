# IQOO — AI Market Research Agent

> Production-ready React Native (Expo) mobile app with on-device AI (Gemma 3), RAG (retrieval-augmented generation), and graph memory.

## Overview

IQOO is an AI-powered market research agent for startup founders, CTOs, and market heads. It runs Gemma 3 fully on-device when offline, and Claude (Anthropic) in the cloud when online.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | React Native / Expo SDK 51 (bare workflow) |
| Language | TypeScript (strict mode) |
| On-device AI | react-native-executorch + Gemma 3 2B GGUF |
| Cloud AI | Anthropic Claude API |
| Vector Store | SQLite-backed local embeddings |
| Graph Memory | expo-sqlite (nodes + edges) |
| State | Zustand |
| Navigation | Expo Router (file-based) |
| Styling | NativeWind (Tailwind for RN) |
| Storage | expo-sqlite + expo-secure-store |

---

## Quick Start

### 1. Install dependencies

```bash
npm install
```

### 2. Run Expo install for native modules

```bash
npx expo install expo-sqlite expo-secure-store expo-speech expo-file-system expo-sharing expo-crypto expo-av
npx expo install @react-native-community/netinfo react-native-svg react-native-gesture-handler react-native-reanimated react-native-screens react-native-safe-area-context
```

### 3. Configure environment

Create `.env.local`:

```env
EXPO_PUBLIC_API_URL=https://your-iqoo-backend.com
EXPO_PUBLIC_CLAUDE_MODEL=claude-sonnet-4-6
```

### 4. Add your Anthropic API Key

Open the app → Settings tab → paste your `sk-ant-...` key.

It is stored via `expo-secure-store` (encrypted on-device).

### 5. Run on iOS

```bash
npx expo run:ios
```

### 6. Run on Android

```bash
npx expo run:android
```

---

## Model Files (First Launch)

On first launch the app will prompt to download:

| Model | Size | URL |
|---|---|---|
| Gemma 3 2B (4-bit) | ~1.4 GB | HuggingFace GGUF |
| all-MiniLM-L6-v2 | ~90 MB | HuggingFace GGUF |

Files are cached in `expo-file-system` `documentDirectory`.

> **Note**: Models require ~4 GB free storage. The app warns if storage is insufficient.
> A "Skip — use cloud only" option is available for users without enough space.

---

## Connectivity Logic

```
IF offline:
  → Gemma 3 (on-device)
  → RAG from local SQLite vector store
  → Graph memory lookups
  → Offline badge shown in UI

IF online + API key set:
  → Claude API (streaming SSE)
  → Fresh data fetched via backend
  → Results embedded and stored locally
  → Entities extracted → graph updated
```

---

## Screens

| Screen | Route | Description |
|---|---|---|
| Agent Chat | `/(tabs)/` | Streaming chat with model badge, source citations, graph node chips |
| Research Workbench | `/(tabs)/research` | Quick-action buttons + custom research queries |
| Graph Explorer | `/(tabs)/graph` | SVG force-directed graph, node tap → detail sheet |
| Settings | `/(tabs)/settings` | API key, model selection, storage stats, JSON export |

---

## Architecture

```
app/
  (tabs)/
    index.tsx         ← Agent chat
    research.tsx      ← Research workbench
    graph.tsx         ← Graph memory explorer
    settings.tsx      ← Settings
  _layout.tsx

services/
  AIService.ts        ← Claude streaming / Gemma 3 fallback
  RAGService.ts       ← Vector store (embeddings + cosine similarity)
  GraphMemoryService.ts ← SQLite graph (nodes, edges, traversal)
  EntityExtractor.ts  ← NER → graph upsert
  ConnectivityService.ts ← NetInfo wrapper

store/
  chatStore.ts        ← Zustand: messages, streaming, model
  settingsStore.ts    ← Zustand: API key, model choice

hooks/
  useAgent.ts         ← Full query pipeline orchestration
  useGraphMemory.ts   ← Graph CRUD + state
  useVectorStore.ts   ← RAG operations

components/
  ChatBubble.tsx      ← Message + sources + graph node chips
  SourceBadge.tsx     ← Tap-to-expand source modal
  GraphNode.tsx       ← SVG node (react-native-svg)
  OfflineBanner.tsx   ← Animated amber offline banner
  TypingIndicator.tsx ← Animated bouncing dots
```

---

## Running Tests

```bash
npm test
```

The `__tests__/GraphMemoryService.test.ts` suite uses an in-memory mock of `expo-sqlite` (located at `__mocks__/expo-sqlite.ts`) and covers:

- Node creation and deduplication
- Edge weight incrementing (capped at 1.0)
- Neighbor traversal (depth 1 and 2)
- Node search
- clearAll
- JSON export

---

## Graph Memory Schema

**Nodes**
```sql
CREATE TABLE nodes (
  id TEXT PRIMARY KEY,
  type TEXT,        -- 'company' | 'topic' | 'trend' | 'person'
  name TEXT,
  metadata TEXT,    -- JSON blob
  created_at INTEGER,
  last_seen INTEGER
);
```

**Edges**
```sql
CREATE TABLE edges (
  id TEXT PRIMARY KEY,
  from_id TEXT,
  to_id TEXT,
  relation TEXT,    -- 'COMPETES_WITH' | 'MENTIONED_IN' | 'RELATED_TO' | 'FOUNDED_BY'
  weight REAL,      -- 0.0–1.0, increments per mention
  created_at INTEGER
);
```

---

## Production Notes

- All SQLite operations are wrapped in try/catch with typed errors
- AI calls have a 30s timeout with user-visible error state
- Graph and vector store initialize lazily on first use
- App works fully offline after model download
- API key stored via `expo-secure-store` (AES-256 on iOS Keychain / Android Keystore)
