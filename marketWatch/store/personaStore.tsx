/**
 * personaStore.ts
 *
 * Lightweight Zustand-style persona state using React Context + useReducer
 * (no extra dependency needed beyond React).
 *
 * Manages:
 *  - Active persona: "Founder" | "Marketing"
 *  - On-device signal filtering logic per persona
 *  - Local Gemma insight generation (simulated for MVP)
 */

import React, {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import type { Signal, WarRoomReport } from "../services/apiClient";
import { getItem, setItem } from "../services/storage";

const PERSONA_STORAGE_KEY = "persona_preference";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

export type Persona = "Founder" | "Marketing";

/**
 * Signal tags that each persona cares about.
 * These are matched case-insensitively against signal_type, title, and description.
 */
const PERSONA_TAGS: Record<Persona, string[]> = {
  Founder: ["pricing", "funding", "product expansion", "expansion", "hiring"],
  Marketing: ["copy change", "ad campaign", "feature positioning", "marketing", "sentiment"],
};

/**
 * Signal categories that map to founder vs marketing concerns.
 */
const PERSONA_SIGNAL_TYPES: Record<Persona, string[]> = {
  Founder: ["Funding", "Expansion", "Hiring", "Product"],
  Marketing: ["Marketing", "Sentiment", "Product"],
};

export interface PersonaState {
  persona: Persona;
}

type PersonaAction = { type: "SET_PERSONA"; persona: Persona };

// ─────────────────────────────────────────────────────────────────────────────
// Reducer
// ─────────────────────────────────────────────────────────────────────────────

function personaReducer(state: PersonaState, action: PersonaAction): PersonaState {
  switch (action.type) {
    case "SET_PERSONA":
      return { ...state, persona: action.persona };
    default:
      return state;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────

interface PersonaContextValue {
  state: PersonaState;
  setPersona: (persona: Persona) => void;
  /** Returns signals sorted and highlighted by persona relevance. */
  filterSignals: (signals: Signal[]) => Array<Signal & { highlighted: boolean }>;
  /** Generates a simulated on-device Gemma summary for the war room. */
  generateLocalInsight: (reports: WarRoomReport[], signals: Signal[]) => string;
}

const PersonaContext = createContext<PersonaContextValue | undefined>(undefined);

// ─────────────────────────────────────────────────────────────────────────────
// Provider
// ─────────────────────────────────────────────────────────────────────────────

export function PersonaProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(personaReducer, { persona: "Founder" });

  // Restore persisted persona on mount
  useEffect(() => {
    getItem<Persona>(PERSONA_STORAGE_KEY).then((saved) => {
      if (saved === "Founder" || saved === "Marketing") {
        dispatch({ type: "SET_PERSONA", persona: saved });
      }
    });
  }, []);

  const setPersona = useCallback((persona: Persona) => {
    dispatch({ type: "SET_PERSONA", persona });
    setItem(PERSONA_STORAGE_KEY, persona);
  }, []);

  /**
   * Filters and sorts signals based on the active persona.
   * Signals matching persona-relevant tags are floated to the top
   * and marked with `highlighted: true` for visual callout in the UI.
   */
  const filterSignals = useCallback(
    (signals: Signal[]): Array<Signal & { highlighted: boolean }> => {
      const tags = PERSONA_TAGS[state.persona];
      const relevantTypes = PERSONA_SIGNAL_TYPES[state.persona];

      const scored = signals.map((signal) => {
        const searchText = [
          signal.signal_type,
          signal.title,
          signal.description ?? "",
        ]
          .join(" ")
          .toLowerCase();

        const tagMatch = tags.some((tag) => searchText.includes(tag.toLowerCase()));
        const typeMatch = relevantTypes.some(
          (t) => t.toLowerCase() === signal.signal_type.toLowerCase()
        );
        const highlighted = tagMatch || typeMatch;

        // Persona-relevance boost: highlighted signals float to the top
        const personaScore = highlighted
          ? signal.impact_score + signal.urgency_score + 10
          : signal.impact_score + signal.urgency_score;

        return { ...signal, highlighted, personaScore };
      });

      // Sort: highlighted first, then by combined impact+urgency score
      return scored
        .sort((a, b) => b.personaScore - a.personaScore)
        .map(({ personaScore: _, ...rest }) => rest);
    },
    [state.persona]
  );

  /**
   * Simulates on-device Gemma local model inference.
   *
   * In a production build, this would invoke a locally bundled ONNX/GGUF
   * model via react-native-executorch or similar.
   *
   * For the MVP, this generates deterministic, persona-contextual summaries
   * from the actual data payloads, clearly labelled as a local simulation.
   */
  const generateLocalInsight = useCallback(
    (reports: WarRoomReport[], signals: Signal[]): string => {
      const persona = state.persona;
      const topReport = reports.sort((a, b) => b.impact_score - a.impact_score)[0];
      const relevantTypes = PERSONA_SIGNAL_TYPES[persona];

      const relevantSignals = signals
        .filter((s) => relevantTypes.includes(s.signal_type))
        .sort((a, b) => b.impact_score - a.impact_score)
        .slice(0, 3);

      if (persona === "Founder") {
        const fundingSignals = signals.filter((s) => s.signal_type === "Funding");
        const expansionSignals = signals.filter((s) => s.signal_type === "Expansion");
        const hiringSignals = signals.filter((s) => s.signal_type === "Hiring");

        const hasFunding = fundingSignals.length > 0;
        const hasExpansion = expansionSignals.length > 0;
        const hasHiring = hiringSignals.length > 0;

        const highestImpact = relevantSignals[0];

        let insight =
          "📊 FOUNDER LENS — Strategic Intelligence Summary\n\n";

        if (hasFunding) {
          insight += `⚠️ Capital Activity: ${fundingSignals.length} competitor(s) have received new funding. `;
          insight += "This accelerates their runway and expansion velocity significantly.\n\n";
        }

        if (hasExpansion) {
          insight += `🗺️ Market Expansion: ${expansionSignals.length} active expansion signal(s) detected. `;
          insight += "Competitors are moving into new geographies — evaluate if your market position is defensible.\n\n";
        }

        if (hasHiring) {
          insight += `👥 Workforce Signals: ${hiringSignals.length} hiring surge(s) across competitors. `;
          insight += "Correlates with product launch cycles 60-90 days out — prepare counter-strategy now.\n\n";
        }

        if (topReport) {
          insight += `🔴 Highest Threat: ${topReport.threat_summary.split("\n")[0]}\n\n`;
        }

        if (highestImpact) {
          insight += `🎯 CEO Action Required: "${highestImpact.title}" — Impact: ${highestImpact.impact_score}/10. `;
          insight += "Schedule strategy review this week.";
        }

        return insight;
      } else {
        // Marketing persona
        const marketingSignals = signals.filter((s) => s.signal_type === "Marketing");
        const productSignals = signals.filter((s) => s.signal_type === "Product");
        const sentimentSignals = signals.filter((s) => s.signal_type === "Sentiment");

        let insight =
          "🎯 MARKETING LENS — GTM Intelligence Summary\n\n";

        if (marketingSignals.length > 0) {
          const topMkt = marketingSignals.sort(
            (a, b) => b.impact_score - a.impact_score
          )[0];
          insight += `📣 Ad & Campaign Activity: ${marketingSignals.length} active competitor campaign(s). `;
          insight += `Most urgent: "${topMkt.title}" (${topMkt.source}). `;
          insight += "Review your current messaging — are you being out-positioned?\n\n";
        }

        if (productSignals.length > 0) {
          insight += `🚀 Feature Positioning: ${productSignals.length} competitor product move(s) detected. `;
          insight += "Audit your website copy and feature comparison pages for accuracy.\n\n";
        }

        if (sentimentSignals.length > 0) {
          insight += `💬 Sentiment Shift: ${sentimentSignals.length} competitor brand sentiment change(s). `;
          insight += "Opportunity to capture dissatisfied competitor customers — launch a direct comparison campaign.\n\n";
        }

        const highestMktImpact = relevantSignals[0];
        if (highestMktImpact) {
          insight += `🎯 CMO Action Required: "${highestMktImpact.title}" — `;
          insight += `Urgency: ${highestMktImpact.urgency_score}/10. `;
          insight += "Draft a counter-messaging brief by EOD.";
        }

        if (relevantSignals.length === 0) {
          insight += "✅ No urgent marketing-level competitive moves detected this cycle. ";
          insight += "Good time to invest in brand-building campaigns.";
        }

        return insight;
      }
    },
    [state.persona]
  );

  return (
    <PersonaContext.Provider
      value={{ state, setPersona, filterSignals, generateLocalInsight }}
    >
      {children}
    </PersonaContext.Provider>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook
// ─────────────────────────────────────────────────────────────────────────────

export function usePersona(): PersonaContextValue {
  const ctx = useContext(PersonaContext);
  if (!ctx) {
    throw new Error("usePersona must be used inside <PersonaProvider>");
  }
  return ctx;
}
