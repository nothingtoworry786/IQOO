import { useState, useEffect, useCallback } from "react";
import {
  Text,
  View,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Pressable,
  RefreshControl,
} from "react-native";
import { BrainCircuit, AlertTriangle, TrendingUp } from "lucide-react-native";
import { api, type Prediction } from "../../services/apiClient";
import { usePersona } from "../../store/personaStore";

// ─────────────────────────────────────────────────────────────────────────────
// Threat level styling
// ─────────────────────────────────────────────────────────────────────────────

const THREAT_STYLES: Record<string, { bg: string; text: string; border: string; label: string }> = {
  low: { bg: "#052E16", text: "#4ADE80", border: "#166534", label: "LOW THREAT" },
  medium: { bg: "#2D1B09", text: "#FBBF24", border: "#92400E", label: "MEDIUM THREAT" },
  high: { bg: "#3B1200", text: "#FB923C", border: "#7C2D12", label: "HIGH THREAT" },
  critical: { bg: "#450A0A", text: "#F87171", border: "#7F1D1D", label: "CRITICAL" },
};

// ─────────────────────────────────────────────────────────────────────────────
// Prediction Card Component
// ─────────────────────────────────────────────────────────────────────────────

function PredictionCard({ prediction }: { prediction: Prediction }) {
  const threat = THREAT_STYLES[prediction.threat_level] ?? THREAT_STYLES.medium;
  const confidenceColor =
    prediction.confidence >= 75
      ? "#4ADE80"
      : prediction.confidence >= 50
      ? "#FBBF24"
      : "#FB923C";

  return (
    <View style={[pred.container, { borderLeftColor: threat.text }]}>
      {/* Threat badge + confidence */}
      <View style={pred.headerRow}>
        <View style={[pred.badge, { backgroundColor: threat.bg, borderColor: threat.border }]}>
          <Text style={[pred.badgeText, { color: threat.text }]}>{threat.label}</Text>
        </View>
        <View style={pred.confidenceRow}>
          <Text style={pred.confidenceLabel}>Confidence</Text>
          <Text style={[pred.confidenceValue, { color: confidenceColor }]}>
            {prediction.confidence}%
          </Text>
        </View>
      </View>

      {/* Confidence bar */}
      <View style={pred.barTrack}>
        <View
          style={[
            pred.barFill,
            {
              width: `${prediction.confidence}%` as any,
              backgroundColor: confidenceColor,
            },
          ]}
        />
      </View>

      {/* Prediction text */}
      <Text style={pred.predictionText}>{prediction.prediction}</Text>

      {/* AI Reasoning */}
      {prediction.ai_reasoning && (
        <View style={pred.reasoningBox}>
          <Text style={pred.reasoningLabel}>🤖 AI REASONING</Text>
          <Text style={pred.reasoningText}>{prediction.ai_reasoning}</Text>
        </View>
      )}

      {/* Competitor ID tag */}
      <Text style={pred.metaText}>
        Competitor: {prediction.competitor_id} ·{" "}
        {new Date(prediction.created_at).toLocaleDateString()}
      </Text>
    </View>
  );
}

const pred = StyleSheet.create({
  container: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#334155",
    borderLeftWidth: 4,
    padding: 16,
    marginBottom: 14,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  badge: {
    borderRadius: 99,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1,
  },
  confidenceRow: {
    alignItems: "flex-end",
  },
  confidenceLabel: {
    fontSize: 10,
    color: "#64748B",
    letterSpacing: 0.5,
    textTransform: "uppercase",
  },
  confidenceValue: {
    fontSize: 18,
    fontWeight: "800",
    marginTop: 2,
  },
  barTrack: {
    height: 3,
    backgroundColor: "#334155",
    borderRadius: 99,
    overflow: "hidden",
    marginBottom: 14,
  },
  barFill: {
    height: "100%",
    borderRadius: 99,
  },
  predictionText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#F1F5F9",
    lineHeight: 23,
    marginBottom: 12,
  },
  reasoningBox: {
    backgroundColor: "#0F172A",
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#1E293B",
  },
  reasoningLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 1.2,
    marginBottom: 6,
  },
  reasoningText: {
    fontSize: 13,
    color: "#94A3B8",
    lineHeight: 20,
    fontStyle: "italic",
  },
  metaText: {
    fontSize: 11,
    color: "#475569",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Predictions Screen
// ─────────────────────────────────────────────────────────────────────────────

type SortMode = "confidence" | "threat" | "newest";

export default function PredictionsScreen() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sortMode, setSortMode] = useState<SortMode>("confidence");

  const { state: personaState } = usePersona();

  const fetchPredictions = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const data = await api.predictions.list({ limit: 100 });
      setPredictions(data);
    } catch (err: any) {
      setError(err?.message ?? "Failed to load predictions.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  // Sort predictions based on sort mode and persona
  const sortedPredictions = [...predictions].sort((a, b) => {
    if (sortMode === "confidence") return b.confidence - a.confidence;
    if (sortMode === "newest")
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    if (sortMode === "threat") {
      const order: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 };
      return (order[b.threat_level] ?? 0) - (order[a.threat_level] ?? 0);
    }
    return 0;
  });

  // For Founder persona, boost high/critical threat predictions
  const displayPredictions =
    personaState.persona === "Founder"
      ? [
          ...sortedPredictions.filter((p) =>
            ["high", "critical"].includes(p.threat_level)
          ),
          ...sortedPredictions.filter(
            (p) => !["high", "critical"].includes(p.threat_level)
          ),
        ]
      : sortedPredictions;

  const highCount = predictions.filter((p) =>
    ["high", "critical"].includes(p.threat_level)
  ).length;
  const avgConfidence =
    predictions.length > 0
      ? Math.round(
          predictions.reduce((sum, p) => sum + p.confidence, 0) / predictions.length
        )
      : 0;

  return (
    <View style={screen.container}>
      {/* ── Header ───────────────────────────────────────────────── */}
      <View style={screen.header}>
        <View style={screen.titleRow}>
          <BrainCircuit size={20} color="#22D3EE" />
          <View>
            <Text style={screen.title}>Predictions</Text>
            <Text style={screen.subtitle}>
              {personaState.persona} lens · {displayPredictions.length} forecasts
            </Text>
          </View>
        </View>

        {/* Stats strip */}
        {predictions.length > 0 && (
          <View style={screen.statsRow}>
            <View style={screen.statBox}>
              <Text style={screen.statValue}>{highCount}</Text>
              <Text style={screen.statLabel}>HIGH/CRITICAL</Text>
            </View>
            <View style={[screen.statBox, { borderColor: "#334155" }]}>
              <Text style={[screen.statValue, { color: "#4ADE80" }]}>
                {avgConfidence}%
              </Text>
              <Text style={screen.statLabel}>AVG CONFIDENCE</Text>
            </View>
            <View style={screen.statBox}>
              <Text style={screen.statValue}>{predictions.length}</Text>
              <Text style={screen.statLabel}>TOTAL</Text>
            </View>
          </View>
        )}

        {/* Sort toggle */}
        <View style={screen.sortRow}>
          {(["confidence", "threat", "newest"] as SortMode[]).map((s) => (
            <Pressable
              key={s}
              onPress={() => setSortMode(s)}
              style={[screen.sortPill, sortMode === s && screen.sortPillActive]}
            >
              <Text
                style={[
                  screen.sortPillText,
                  sortMode === s && screen.sortPillTextActive,
                ]}
              >
                {s}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* ── Content ─────────────────────────────────────────────── */}
      {loading ? (
        <View style={screen.centered}>
          <ActivityIndicator size="large" color="#22D3EE" />
          <Text style={screen.loadingText}>Loading predictions…</Text>
        </View>
      ) : error ? (
        <View style={screen.centered}>
          <AlertTriangle size={32} color="#F87171" />
          <Text style={screen.errorText}>{error}</Text>
          <Pressable style={screen.retryBtn} onPress={() => fetchPredictions()}>
            <Text style={screen.retryBtnText}>Retry</Text>
          </Pressable>
        </View>
      ) : displayPredictions.length === 0 ? (
        <View style={screen.centered}>
          <TrendingUp size={32} color="#334155" />
          <Text style={screen.emptyText}>
            No predictions yet.{"\n"}Initialise your War Room from the Dashboard.
          </Text>
        </View>
      ) : (
        <FlatList
          data={displayPredictions}
          renderItem={({ item }) => <PredictionCard prediction={item} />}
          keyExtractor={(item) => item.id}
          contentContainerStyle={screen.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchPredictions(true)}
              tintColor="#22D3EE"
            />
          }
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

const screen = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  header: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#1E293B",
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: "#F1F5F9",
    letterSpacing: -0.3,
  },
  subtitle: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  statsRow: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 12,
  },
  statBox: {
    flex: 1,
    backgroundColor: "#1E293B",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
    padding: 10,
    alignItems: "center",
  },
  statValue: {
    fontSize: 20,
    fontWeight: "800",
    color: "#F87171",
  },
  statLabel: {
    fontSize: 9,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 0.8,
    marginTop: 2,
    textTransform: "uppercase",
  },
  sortRow: {
    flexDirection: "row",
    gap: 6,
  },
  sortPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 99,
    borderWidth: 1,
    borderColor: "#334155",
    backgroundColor: "#1E293B",
  },
  sortPillActive: {
    backgroundColor: "#164E63",
    borderColor: "#22D3EE",
  },
  sortPillText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#64748B",
    textTransform: "capitalize",
  },
  sortPillTextActive: {
    color: "#22D3EE",
  },
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    padding: 24,
  },
  loadingText: {
    fontSize: 14,
    color: "#64748B",
  },
  errorText: {
    fontSize: 14,
    color: "#F87171",
    textAlign: "center",
    lineHeight: 22,
  },
  emptyText: {
    fontSize: 14,
    color: "#475569",
    textAlign: "center",
    lineHeight: 22,
  },
  retryBtn: {
    paddingHorizontal: 24,
    paddingVertical: 10,
    backgroundColor: "#1E293B",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
  },
  retryBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#22D3EE",
  },
  list: {
    padding: 16,
    paddingBottom: 32,
  },
});
