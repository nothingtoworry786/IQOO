import { useState, useEffect, useCallback } from "react";
import {
  Text,
  View,
  FlatList,
  StyleSheet,
  Pressable,
  ActivityIndicator,
  TextInput,
  RefreshControl,
} from "react-native";
import { RadioTower, Search, AlertTriangle, TrendingUp, Filter } from "lucide-react-native";
import { api, type Signal, type SignalCategory } from "../../services/apiClient";
import { usePersona } from "../../store/personaStore";

// ─────────────────────────────────────────────────────────────────────────────
// Type badge colours matching the backend SignalCategory enum
// ─────────────────────────────────────────────────────────────────────────────

const CATEGORY_COLORS: Record<SignalCategory, { bg: string; text: string; border: string }> = {
  Hiring: { bg: "#1E3A2F", text: "#4ADE80", border: "#166534" },
  Funding: { bg: "#1A2E4A", text: "#60A5FA", border: "#1E40AF" },
  Marketing: { bg: "#2D1B4E", text: "#C084FC", border: "#6B21A8" },
  Product: { bg: "#1E293B", text: "#22D3EE", border: "#0E7490" },
  Expansion: { bg: "#3B1F12", text: "#FB923C", border: "#7C2D12" },
  Leadership: { bg: "#1F1635", text: "#A78BFA", border: "#4C1D95" },
  Sentiment: { bg: "#1C2A1C", text: "#86EFAC", border: "#14532D" },
};

const IMPACT_BAR_COLORS = ["#4ADE80", "#4ADE80", "#FBBF24", "#FBBF24", "#FB923C", "#FB923C", "#FB923C", "#F87171", "#F87171", "#F87171"];

// ─────────────────────────────────────────────────────────────────────────────
// Signal Card Component
// ─────────────────────────────────────────────────────────────────────────────

interface SignalWithHighlight extends Signal {
  highlighted: boolean;
}

function SignalCard({ signal }: { signal: SignalWithHighlight }) {
  const colors = CATEGORY_COLORS[signal.signal_type] ?? CATEGORY_COLORS.Product;
  const impactBarColor = IMPACT_BAR_COLORS[Math.floor(signal.impact_score)] ?? "#4ADE80";
  const impactPercent = (signal.impact_score / 10) * 100;
  const urgencyPercent = (signal.urgency_score / 10) * 100;

  return (
    <View
      style={[
        card.container,
        signal.highlighted && card.containerHighlighted,
      ]}
    >
      {/* Highlighted persona lens indicator */}
      {signal.highlighted && (
        <View style={card.highlightBanner}>
          <Text style={card.highlightText}>✦ PERSONA MATCH</Text>
        </View>
      )}

      {/* Header row */}
      <View style={card.headerRow}>
        <View style={[card.badge, { backgroundColor: colors.bg, borderColor: colors.border }]}>
          <Text style={[card.badgeText, { color: colors.text }]}>
            {signal.signal_type.toUpperCase()}
          </Text>
        </View>
        <Text style={card.source}>{signal.source}</Text>
      </View>

      {/* Title */}
      <Text style={card.title}>{signal.title}</Text>

      {/* Description */}
      {signal.description && (
        <Text style={card.description} numberOfLines={3}>
          {signal.description}
        </Text>
      )}

      {/* Score bars */}
      <View style={card.scoresRow}>
        <View style={card.scoreBlock}>
          <View style={card.scoreLabelRow}>
            <Text style={card.scoreLabel}>Impact</Text>
            <Text style={[card.scoreValue, { color: impactBarColor }]}>
              {signal.impact_score.toFixed(1)}
            </Text>
          </View>
          <View style={card.barTrack}>
            <View
              style={[
                card.barFill,
                { width: `${impactPercent}%` as any, backgroundColor: impactBarColor },
              ]}
            />
          </View>
        </View>

        <View style={[card.scoreBlock, { marginLeft: 12 }]}>
          <View style={card.scoreLabelRow}>
            <Text style={card.scoreLabel}>Urgency</Text>
            <Text style={[card.scoreValue, { color: "#22D3EE" }]}>
              {signal.urgency_score.toFixed(1)}
            </Text>
          </View>
          <View style={card.barTrack}>
            <View
              style={[
                card.barFill,
                { width: `${urgencyPercent}%` as any, backgroundColor: "#22D3EE" },
              ]}
            />
          </View>
        </View>
      </View>
    </View>
  );
}

const card = StyleSheet.create({
  container: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#334155",
    padding: 14,
    marginBottom: 12,
  },
  containerHighlighted: {
    borderColor: "#22D3EE",
    borderWidth: 1.5,
    backgroundColor: "#0F2942",
  },
  highlightBanner: {
    backgroundColor: "#164E63",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    alignSelf: "flex-start",
    marginBottom: 10,
  },
  highlightText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#22D3EE",
    letterSpacing: 1.2,
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
    paddingVertical: 3,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 0.8,
  },
  source: {
    fontSize: 12,
    color: "#475569",
    fontStyle: "italic",
  },
  title: {
    fontSize: 15,
    fontWeight: "700",
    color: "#F1F5F9",
    lineHeight: 22,
    marginBottom: 8,
  },
  description: {
    fontSize: 13,
    color: "#94A3B8",
    lineHeight: 20,
    marginBottom: 14,
  },
  scoresRow: {
    flexDirection: "row",
  },
  scoreBlock: {
    flex: 1,
  },
  scoreLabelRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 5,
  },
  scoreLabel: {
    fontSize: 11,
    color: "#64748B",
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  scoreValue: {
    fontSize: 11,
    fontWeight: "700",
  },
  barTrack: {
    height: 4,
    backgroundColor: "#334155",
    borderRadius: 99,
    overflow: "hidden",
  },
  barFill: {
    height: "100%",
    borderRadius: 99,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Signals Screen
// ─────────────────────────────────────────────────────────────────────────────

const FILTER_OPTIONS: Array<{ label: string; value: SignalCategory | "all" }> = [
  { label: "All", value: "all" },
  { label: "Hiring", value: "Hiring" },
  { label: "Funding", value: "Funding" },
  { label: "Marketing", value: "Marketing" },
  { label: "Product", value: "Product" },
  { label: "Expansion", value: "Expansion" },
];

export default function SignalsScreen() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState<SignalCategory | "all">("all");
  const [sortBy, setSortBy] = useState<"newest" | "impact" | "urgency">("impact");

  const { filterSignals, state: personaState } = usePersona();

  const fetchSignals = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      try {
        const data = await api.signals.list({
          signal_type: activeFilter === "all" ? undefined : activeFilter,
          search: search.trim() || undefined,
          sort_by: sortBy,
          limit: 100,
        });
        setSignals(data);
      } catch (err: any) {
        setError(err?.message ?? "Failed to load signals.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [activeFilter, search, sortBy]
  );

  useEffect(() => {
    const debounce = setTimeout(() => fetchSignals(), 300);
    return () => clearTimeout(debounce);
  }, [fetchSignals]);

  // Apply persona filtering on fetched signals
  const filteredSignals = filterSignals(signals) as Array<Signal & { highlighted: boolean }>;

  const renderItem = useCallback(
    ({ item }: { item: Signal & { highlighted: boolean } }) => (
      <SignalCard signal={item} />
    ),
    []
  );

  return (
    <View style={screen.container}>
      {/* ── Header ─────────────────────────────────────────────────── */}
      <View style={screen.header}>
        <View style={screen.titleRow}>
          <RadioTower size={20} color="#22D3EE" />
          <View>
            <Text style={screen.title}>Signals</Text>
            <Text style={screen.subtitle}>
              {personaState.persona} lens · {filteredSignals.length} signals
            </Text>
          </View>
        </View>

        {/* Sort toggle */}
        <View style={screen.sortRow}>
          {(["impact", "urgency", "newest"] as const).map((s) => (
            <Pressable
              key={s}
              onPress={() => setSortBy(s)}
              style={[screen.sortPill, sortBy === s && screen.sortPillActive]}
            >
              <Text
                style={[
                  screen.sortPillText,
                  sortBy === s && screen.sortPillTextActive,
                ]}
              >
                {s}
              </Text>
            </Pressable>
          ))}
        </View>
      </View>

      {/* ── Search ──────────────────────────────────────────────────── */}
      <View style={screen.searchRow}>
        <Search size={16} color="#475569" style={{ marginRight: 8 }} />
        <TextInput
          style={screen.searchInput}
          placeholder="Search signals…"
          placeholderTextColor="#475569"
          value={search}
          onChangeText={setSearch}
          autoCapitalize="none"
          autoCorrect={false}
          returnKeyType="search"
          accessibilityLabel="Search signals"
        />
      </View>

      {/* ── Category Filter ─────────────────────────────────────────── */}
      <View style={screen.filterRow}>
        {FILTER_OPTIONS.map((opt) => (
          <Pressable
            key={opt.value}
            onPress={() => setActiveFilter(opt.value)}
            style={[
              screen.filterChip,
              activeFilter === opt.value && screen.filterChipActive,
            ]}
          >
            <Text
              style={[
                screen.filterChipText,
                activeFilter === opt.value && screen.filterChipTextActive,
              ]}
            >
              {opt.label}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* ── Content ────────────────────────────────────────────────── */}
      {loading ? (
        <View style={screen.centered}>
          <ActivityIndicator size="large" color="#22D3EE" />
          <Text style={screen.loadingText}>Loading signals…</Text>
        </View>
      ) : error ? (
        <View style={screen.centered}>
          <AlertTriangle size={32} color="#F87171" />
          <Text style={screen.errorText}>{error}</Text>
          <Pressable style={screen.retryBtn} onPress={() => fetchSignals()}>
            <Text style={screen.retryBtnText}>Retry</Text>
          </Pressable>
        </View>
      ) : filteredSignals.length === 0 ? (
        <View style={screen.centered}>
          <TrendingUp size={32} color="#334155" />
          <Text style={screen.emptyText}>No signals found.{"\n"}Initialise your War Room from the Dashboard.</Text>
        </View>
      ) : (
        <FlatList
          data={filteredSignals}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={screen.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => fetchSignals(true)}
              tintColor="#22D3EE"
            />
          }
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────

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
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    marginHorizontal: 16,
    marginTop: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: "#1E293B",
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#334155",
  },
  searchInput: {
    flex: 1,
    fontSize: 14,
    color: "#F1F5F9",
  },
  filterRow: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    flexWrap: "wrap",
  },
  filterChip: {
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 99,
    borderWidth: 1,
    borderColor: "#334155",
    backgroundColor: "#1E293B",
  },
  filterChipActive: {
    backgroundColor: "#1E3A5F",
    borderColor: "#3B82F6",
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#64748B",
  },
  filterChipTextActive: {
    color: "#60A5FA",
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
