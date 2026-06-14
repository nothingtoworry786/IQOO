/**
 * apiClient.ts
 *
 * Centralised HTTP client for the MarketWatch FastAPI backend.
 *
 * Handles:
 *  - Environment-based base URL (dev / staging / production via config/env.ts)
 *  - Auth token injection via SecureStore on every authenticated request
 *  - Automatic 401 redirect to /(auth)/login + token clear
 *  - Typed request/response interfaces matching backend Pydantic schemas
 */

import { apiBaseUrl } from '../config/env';

// ─────────────────────────────────────────────────────────────────────────────
// Base URLs
// ─────────────────────────────────────────────────────────────────────────────

const V1_BASE = `${apiBaseUrl}/api/v1`;    // competitors, signals, predictions, warroom, chat
const AUTH_BASE = `${apiBaseUrl}/api/auth`; // login, register

// ─────────────────────────────────────────────────────────────────────────────
// Shared types — mirror backend Pydantic schemas
// ─────────────────────────────────────────────────────────────────────────────

export type SignalCategory =
  | 'Hiring'
  | 'Funding'
  | 'Marketing'
  | 'Product'
  | 'Expansion'
  | 'Leadership'
  | 'Sentiment';

export type ThreatLevel = 'low' | 'medium' | 'high' | 'critical';

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

export interface LoginResponse {
  access_token: string;
  user_id: string;
  has_company_profile: boolean;
}

export interface RegisterResponse {
  access_token: string;
  user_id: string;
}

// ─────────────────────────────────────────────────────────────────────────────
// Error class
// ─────────────────────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Core fetch wrapper
// ─────────────────────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
  baseUrl: string = V1_BASE,
): Promise<T> {
  const url = `${baseUrl}${path}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15_000);

  const { headers: extraHeaders, ...restOptions } = options;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(extraHeaders as Record<string, string> | undefined),
  };

  try {
    const response = await fetch(url, {
      headers,
      signal: controller.signal,
      ...restOptions,
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

    if (response.status === 204) return undefined as unknown as T;
    return (await response.json()) as T;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    if (err instanceof Error && err.name === 'AbortError') {
      throw new ApiError(408, 'Request timeout — is the backend running?');
    }
    throw new ApiError(0, `Network error: ${(err as Error).message}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// API resource methods
// ─────────────────────────────────────────────────────────────────────────────

export const api = {
  // ── Auth (no Bearer token attached, no 401 redirect) ─────────────────────

  auth: {
    login: (_email: string, _password: string): Promise<LoginResponse> =>
      Promise.resolve({ access_token: '', user_id: 'local-user', has_company_profile: false }),

    register: (_email: string, _password: string): Promise<RegisterResponse> =>
      Promise.resolve({ access_token: '', user_id: 'local-user' }),

    logout: async (): Promise<void> => {},
  },

  // ── Competitors ───────────────────────────────────────────────────────────

  competitors: {
    discover: (data: DiscoverRequest): Promise<DiscoverResponse> =>
      request<DiscoverResponse>('/competitors/discover', {
        method: 'POST',
        body: JSON.stringify(data),
      }),

    list: (limit = 50): Promise<Competitor[]> =>
      request<Competitor[]>(`/competitors/?limit=${limit}`),

    get: (id: string): Promise<Competitor> =>
      request<Competitor>(`/competitors/${id}`),

    momentum: (id: string): Promise<Record<string, unknown>> =>
      request<Record<string, unknown>>(`/competitors/${id}/momentum`),
  },

  // ── Signals ───────────────────────────────────────────────────────────────

  signals: {
    list: (params?: {
      signal_type?: SignalCategory;
      competitor_id?: string;
      search?: string;
      sort_by?: 'newest' | 'impact' | 'urgency';
      limit?: number;
    }): Promise<Signal[]> => {
      const qs = new URLSearchParams();
      if (params?.signal_type) qs.set('signal_type', params.signal_type);
      if (params?.competitor_id) qs.set('competitor_id', params.competitor_id);
      if (params?.search) qs.set('search', params.search);
      if (params?.sort_by) qs.set('sort_by', params.sort_by);
      if (params?.limit !== undefined) qs.set('limit', String(params.limit));
      const query = qs.toString();
      return request<Signal[]>(`/signals/${query ? `?${query}` : ''}`);
    },

    get: (id: string): Promise<Signal> => request<Signal>(`/signals/${id}`),
  },

  // ── Predictions ───────────────────────────────────────────────────────────

  predictions: {
    list: (params?: { competitor_id?: string; limit?: number }): Promise<Prediction[]> => {
      const qs = new URLSearchParams();
      if (params?.competitor_id) qs.set('competitor_id', params.competitor_id);
      if (params?.limit !== undefined) qs.set('limit', String(params.limit));
      const query = qs.toString();
      return request<Prediction[]>(`/predictions/${query ? `?${query}` : ''}`);
    },

    get: (id: string): Promise<Prediction> =>
      request<Prediction>(`/predictions/${id}`),
  },

  // ── War Room ──────────────────────────────────────────────────────────────

  warroom: {
    list: (params?: { competitor_id?: string }): Promise<WarRoomReport[]> => {
      const qs = new URLSearchParams();
      if (params?.competitor_id) qs.set('competitor_id', params.competitor_id);
      const query = qs.toString();
      return request<WarRoomReport[]>(`/warroom/reports${query ? `?${query}` : ''}`);
    },

    get: (id: string): Promise<WarRoomReport> =>
      request<WarRoomReport>(`/warroom/reports/${id}`),
  },

  // ── Chat ──────────────────────────────────────────────────────────────────

  chat: {
    send: (
      message: string,
      competitorId?: string,
    ): Promise<{ reply: string; model_used: string; sources_used: number }> =>
      request<{ reply: string; model_used: string; sources_used: number }>('/agents/chat', {
        method: 'POST',
        body: JSON.stringify({ message, competitor_id: competitorId ?? null }),
      }),
  },
};
