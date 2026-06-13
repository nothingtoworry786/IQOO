/**
 * apiClient.ts
 *
 * Centralised HTTP client for the MarketWatch FastAPI backend.
 *
 * Handles:
 *  - Android emulator vs iOS/web localhost URL differences
 *  - Consistent error normalisation
 *  - Typed request/response interfaces matching backend Pydantic schemas
 */

import { Platform } from "react-native";

// ─────────────────────────────────────────────────────────────────────────────
// Base URL resolution
// ─────────────────────────────────────────────────────────────────────────────

/**
 * On Android emulators, localhost inside the emulator refers to the AVD itself,
 * not the host machine. 10.0.2.2 reaches the host's loopback.
 * On iOS simulator and web, localhost resolves correctly.
 */
function resolveBaseUrl(): string {
  if (Platform.OS === "android") {
    return "http://10.0.2.2:8000/api/v1";
  }
  return "http://localhost:8000/api/v1";
}

const BASE_URL = resolveBaseUrl();

// ─────────────────────────────────────────────────────────────────────────────
// Shared types — mirror backend Pydantic schemas
// ─────────────────────────────────────────────────────────────────────────────

export type SignalCategory =
  | "Hiring"
  | "Funding"
  | "Marketing"
  | "Product"
  | "Expansion"
  | "Leadership"
  | "Sentiment";

export type ThreatLevel = "low" | "medium" | "high" | "critical";

export interface Competitor {
  id: string;
  name: string;
  industry: string;
  website: string | null;
  market_scope: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface Signal {
  id: string;
  competitor_id: string;
  signal_type: SignalCategory;
  source: string;
  title: string;
  description: string | null;
  impact_score: number;
  urgency_score: number;
  created_at: string;
  updated_at: string | null;
}

export interface Prediction {
  id: string;
  competitor_id: string;
  prediction: string;
  confidence: number;
  threat_level: ThreatLevel;
  ai_reasoning: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface WarRoomReport {
  id: string;
  competitor_id: string;
  threat_summary: string;
  recommended_actions: string | null;
  impact_score: number;
  created_at: string;
  updated_at: string | null;
}

export interface DiscoverRequest {
  company_name: string;
  website_url: string;
}

export interface DiscoverResponse {
  status: string;
  company_name: string;
  website_url: string;
  competitors_found: number;
  signals_seeded: number;
  competitors: Array<{
    id: string;
    name: string;
    industry: string;
    website: string;
    threat_level: ThreatLevel;
  }>;
  message: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Core fetch wrapper
// ─────────────────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15_000); // 15s timeout

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...options.headers,
      },
      signal: controller.signal,
      ...options,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let detail: unknown;
      try {
        detail = await response.json();
      } catch {
        detail = await response.text();
      }
      throw new ApiError(
        response.status,
        `HTTP ${response.status}: ${response.statusText}`,
        detail
      );
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as unknown as T;
    }

    return (await response.json()) as T;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiError(408, "Request timeout — is the backend running?");
    }
    throw new ApiError(0, `Network error: ${(err as Error).message}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// API resource methods
// ─────────────────────────────────────────────────────────────────────────────

export const api = {
  // ── Competitors ───────────────────────────────────────────────────────────

  competitors: {
    /** Discover competitors and seed intelligence data for a company. */
    discover: (data: DiscoverRequest): Promise<DiscoverResponse> =>
      request<DiscoverResponse>("/competitors/discover", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    /** List all tracked competitors. */
    list: (limit = 50): Promise<Competitor[]> =>
      request<Competitor[]>(`/competitors/?limit=${limit}`),

    /** Get a single competitor with signals, predictions, and momentum. */
    get: (id: string): Promise<Competitor> =>
      request<Competitor>(`/competitors/${id}`),

    /** Get momentum score for a competitor. */
    momentum: (id: string): Promise<Record<string, unknown>> =>
      request<Record<string, unknown>>(`/competitors/${id}/momentum`),
  },

  // ── Signals ───────────────────────────────────────────────────────────────

  signals: {
    /** List signals with optional filtering and sorting. */
    list: (params?: {
      signal_type?: SignalCategory;
      competitor_id?: string;
      search?: string;
      sort_by?: "newest" | "impact" | "urgency";
      limit?: number;
    }): Promise<Signal[]> => {
      const qs = new URLSearchParams();
      if (params?.signal_type) qs.set("signal_type", params.signal_type);
      if (params?.competitor_id) qs.set("competitor_id", params.competitor_id);
      if (params?.search) qs.set("search", params.search);
      if (params?.sort_by) qs.set("sort_by", params.sort_by);
      if (params?.limit !== undefined) qs.set("limit", String(params.limit));
      const query = qs.toString();
      return request<Signal[]>(`/signals/${query ? `?${query}` : ""}`);
    },

    /** Get a single signal by ID. */
    get: (id: string): Promise<Signal> => request<Signal>(`/signals/${id}`),
  },

  // ── Predictions ───────────────────────────────────────────────────────────

  predictions: {
    /** List predictions, optionally filtered by competitor. */
    list: (params?: {
      competitor_id?: string;
      limit?: number;
    }): Promise<Prediction[]> => {
      const qs = new URLSearchParams();
      if (params?.competitor_id) qs.set("competitor_id", params.competitor_id);
      if (params?.limit !== undefined) qs.set("limit", String(params.limit));
      const query = qs.toString();
      return request<Prediction[]>(`/predictions/${query ? `?${query}` : ""}`);
    },

    /** Get a single prediction by ID. */
    get: (id: string): Promise<Prediction> =>
      request<Prediction>(`/predictions/${id}`),
  },

  // ── War Room ──────────────────────────────────────────────────────────────

  warroom: {
    /** List War Room reports, optionally filtered by competitor. */
    list: (params?: {
      competitor_id?: string;
    }): Promise<WarRoomReport[]> => {
      const qs = new URLSearchParams();
      if (params?.competitor_id) qs.set("competitor_id", params.competitor_id);
      const query = qs.toString();
      return request<WarRoomReport[]>(
        `/warroom/reports${query ? `?${query}` : ""}`
      );
    },

    /** Get a single War Room report by ID. */
    get: (id: string): Promise<WarRoomReport> =>
      request<WarRoomReport>(`/warroom/reports/${id}`),
  },

  // ── Chat ───────────────────────────────────────────────────────────────────

  chat: {
    /** Send a message to the AI competitive intelligence assistant. */
    send: (message: string, competitorId?: string): Promise<{ reply: string; model_used: string }> =>
      request<{ reply: string; model_used: string }>("/agents/chat", {
        method: "POST",
        body: JSON.stringify({ message, competitor_id: competitorId ?? null }),
      }),
  },
};
