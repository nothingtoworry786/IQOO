import { useState, useEffect, useCallback } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Pressable,
  RefreshControl,
  TextInput,
} from "react-native";
import {
  Users,
  TrendingUp,
  RefreshCw,
  ChevronRight,
  Zap,
  RadioTower,
  BrainCircuit,
  Search,
  Eye,
} from "lucide-react-native";
import {
  api,
  type Competitor,
  type Signal,
  type Prediction,
} from "../../services/apiClient";

// ─────────────────────────────────────────────────────────────────────────────
// Signal Badge
// ─────────────────────────────────────────────────────────────────────────────

const SIGNAL_COLORS: Record<string, string> = {
  Hiring: "#38BDF8",
  Funding: "#4ADE80",
  Marketing: "#FB923C",
  Product: "#A78BFA",
  Expansion: "#F87171",
  Leadership: "#FBBF24",
  Sentiment: "#E2E8F0",
};

function SignalBadge({ type, size = "sm" }: { type: string; size?: "sm" | "md" }) {
  const color = SIGNAL_COLORS[type] ?? "#94A3B8";
  const isMd = size === "md";
  return (
    <View style={[sigBadge.pill, {
      backgroundColor: color + "18",
      borderColor: color + "50",
      paddingHorizontal: isMd ? 10 : 8,
      paddingVertical: isMd ? 4 : 3,
    }]}>
      <View style={[sigBadge.dot, {
        backgroundColor: color,
        width: isMd ? 6 : 5,
        height: isMd ? 6 : 5,
      }]} />
      <Text style={[sigBadge.text, {
        color,
        fontSize: isMd ? 11 : 10,
      }]}>{type}</Text>
    </View>
  );
}

const sigBadge = StyleSheet.create({
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    borderRadius: 99,
    borderWidth: 1,
  },
  dot: {
    borderRadius: 3,
  },
  text: {
    fontWeight: "700",
    letterSpacing: 0.3,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Threat Badge
// ─────────────────────────────────────────────────────────────────────────────

const THREAT_COLORS: Record<string, string> = {
  critical: "#F87171",
  high: "#FB923C",
  medium: "#FBBF24",
  low: "#4ADE80",
};

function ThreatBadge({ level }: { level: string }) {
  const color = THREAT_COLORS[level] ?? "#94A3B8";
  return (
    <View style={[tb.pill, { backgroundColor: color + "18", borderColor: color + "50" }]}>
      <View style={[tb.dot, { backgroundColor: color }]} />
      <Text style={[tb.text, { color }]}>{level.toUpperCase()}</Text>
    </View>
  );
}

const tb = StyleSheet.create({
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
  },
  dot: {
    width: 5,
    height: 5,
    borderRadius: 3,
  },
  text: {
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 0.8,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Filter Chip
// ─────────────────────────────────────────────────────────────────────────────

const FILTER_OPTIONS: Array<{ label: string; value: string; icon: any }> = [
  { label: "All", value: "all", icon: Users },
  { label: "Funding", value: "Funding", icon: TrendingUp },
  { label: "Hiring", value: "Hiring", icon: Users },
  { label: "Product", value: "Product", icon: BrainCircuit },
  { label: "Marketing", value: "Marketing", icon: RadioTower },
  { label: "Expansion", value: "Expansion", icon: Zap },
];

// ─────────────────────────────────────────────────────────────────────────────
// Impact Bar
// ─────────────────────────────────────────────────────────────────────────────

function ImpactBar({ score, maxScore = 10 }: { score: number; maxScore?: number }) {
  const pct = Math.min((score / maxScore) * 100, 100);
  const color = score >= 8 ? "#F87171" : score >= 6 ? "#FB923C" : score >= 4 ? "#FBBF24" : "#4ADE80";
  return (
    <View style={ib.container}>
      <View style={ib.track}>
        <View style={[ib.fill, { width: `${pct}%`, backgroundColor: color }]} />
      </View>
      <Text style={[ib.label, { color }]}>{score.toFixed(1)}</Text>
    </View>
  );
}

const ib = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  track: {
    flex: 1,
    height: 4,
    backgroundColor: "#0F172A",
    borderRadius: 2,
    overflow: "hidden",
  },
  fill: {
    height: "100%",
    borderRadius: 2,
  },
  label: {
    fontSize: 11,
    fontWeight: "700",
    minWidth: 28,
    textAlign: "right",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Competitor Card (Redesigned)
// ─────────────────────────────────────────────────────────────────────────────

function CompetitorCard({
  competitor,
  onPress,
  signalCount,
}: {
  competitor: Competitor;
  onPress: () => void;
  signalCount?: number;
}) {
  return (
    <Pressable style={cc.container} onPress={onPress}>
      <View style={cc.leftAccent} />
      <View style={cc.body}>
        <View style={cc.topRow}>
          <View style={cc.avatarRow}>
            <View style={cc.avatar}>
              <Text style={cc.avatarText}>{competitor.name.charAt(0).toUpperCase()}</Text>
            </View>
            <View style={cc.nameGroup}>
              <Text style={cc.name}>{competitor.name}</Text>
              <Text style={cc.industry}>{competitor.industry}</Text>
            </View>
          </View>
          <ChevronRight size={18} color="#334155" />
        </View>

        <View style={cc.metaRow}>
          <View style={cc.metaChip}>
            <Eye size={11} color="#64748B" />
            <Text style={cc.metaText}>{competitor.market_scope ?? "National"}</Text>
          </View>
          {signalCount !== undefined && (
            <View style={cc.metaChip}>
              <RadioTower size={11} color="#64748B" />
              <Text style={cc.metaText}>{signalCount} signals</Text>
            </View>
          )}
        </View>
      </View>
    </Pressable>
  );
}

const cc = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#2D3A4E",
    overflow: "hidden",
    marginBottom: 10,
  },
  leftAccent: {
    width: 4,
    backgroundColor: "#22D3EE",
  },
  body: {
    flex: 1,
    padding: 14,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  avatarRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  avatar: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: "#164E63",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#22D3EE55",
  },
  avatarText: {
    fontSize: 17,
    fontWeight: "800",
    color: "#22D3EE",
  },
  nameGroup: {
    gap: 2,
  },
  name: {
    fontSize: 16,
    fontWeight: "700",
    color: "#F1F5F9",
  },
  industry: {
    fontSize: 12,
    color: "#64748B",
  },
  metaRow: {
    flexDirection: "row",
    gap: 6,
    marginTop: 10,
  },
  metaChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#0F172A",
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: "#334155",
  },
  metaText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#64748B",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Competitor Detail View (with Segmented Tabs)
// ─────────────────────────────────────────────────────────────────────────────

type DetailTab = "signals" | "predictions";

function CompetitorDetail({
  competitor,
  onBack,
}: {
  competitor: Competitor;
  onBack: () => void;
}) {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<DetailTab>("signals");

  useEffect(() => {
    async function load() {
      try {
        const [sigData, predData] = await Promise.all([
          api.signals.list({ competitor_id: competitor.id, sort_by: "impact", limit: 50 }),
          api.predictions.list({ competitor_id: competitor.id, limit: 10 }),
        ]);
        setSignals(sigData);
        setPredictions(predData);
      } catch (err) {
        // Silent fail
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [competitor.id]);

  // Aggregate stats
  const avgImpact = signals.length > 0
    ? (signals.reduce((s, sig) => s + sig.impact_score, 0) / signals.length).toFixed(1)
    : "—";
  const avgUrgency = signals.length > 0
    ? (signals.reduce((s, sig) => s + sig.urgency_score, 0) / signals.length).toFixed(1)
    : "—";
  const topThreat = predictions.length > 0
    ? predictions.sort((a, b) => b.confidence - a.confidence)[0]
    : null;

  return (
    <View style={detail.container}>
      {/* Sticky Header */}
      <View style={detail.stickyHeader}>
        <Pressable style={detail.backBtn} onPress={onBack}>
          <ChevronRight size={18} color="#22D3EE" style={{ transform: [{ rotate: "180deg" }] }} />
          <Text style={detail.backText}>Back</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={detail.scrollContent}>
        {/* Profile Card */}
        <View style={detail.profileCard}>
          <View style={detail.profileTopRow}>
            <View style={detail.profileAvatar}>
              <Text style={detail.profileAvatarText}>
                {competitor.name.charAt(0).toUpperCase()}
              </Text>
            </View>
            <View style={detail.profileInfo}>
              <Text style={detail.profileName}>{competitor.name}</Text>
              <Text style={detail.profileIndustry}>{competitor.industry}</Text>
            </View>
          </View>
          {competitor.website && (
            <Text style={detail.profileWebsite}>{competitor.website}</Text>
          )}
        </View>

        {/* Stats Row */}
        <View style={detail.statsRow}>
          <View style={detail.statCard}>
            <Text style={detail.statValue}>{avgImpact}</Text>
            <Text style={detail.statLabel}>Avg Impact</Text>
          </View>
          <View style={detail.statCard}>
            <Text style={detail.statValue}>{avgUrgency}</Text>
            <Text style={detail.statLabel}>Avg Urgency</Text>
          </View>
          <View style={detail.statCard}>
            <Text style={detail.statValue}>{signals.length}</Text>
            <Text style={detail.statLabel}>Signals</Text>
          </View>
          <View style={detail.statCard}>
            <Text style={detail.statValue}>{predictions.length}</Text>
            <Text style={detail.statLabel}>Predictions</Text>
          </View>
        </View>

        {/* Top Prediction Highlight */}
        {topThreat && (
          <View style={detail.topPredCard}>
            <View style={detail.topPredHeader}>
              <BrainCircuit size={16} color="#A78BFA" />
              <Text style={detail.topPredTitle}>Top Prediction</Text>
              <View style={detail.confBadge}>
                <Text style={detail.confBadgeText}>{topThreat.confidence}%</Text>
              </View>
            </View>
            <Text style={detail.topPredText}>{topThreat.prediction}</Text>
          </View>
        )}

        {/* Segmented Tabs */}
        <View style={detail.segmentRow}>
          <Pressable
            style={[detail.segment, activeTab === "signals" && detail.segmentActive]}
            onPress={() => setActiveTab("signals")}
          >
            <RadioTower size={14} color={activeTab === "signals" ? "#22D3EE" : "#64748B"} />
            <Text style={[detail.segmentText, activeTab === "signals" && detail.segmentTextActive]}>
              Signals ({signals.length})
            </Text>
          </Pressable>
          <Pressable
            style={[detail.segment, activeTab === "predictions" && detail.segmentActive]}
            onPress={() => setActiveTab("predictions")}
          >
            <BrainCircuit size={14} color={activeTab === "predictions" ? "#A78BFA" : "#64748B"} />
            <Text style={[detail.segmentText, activeTab === "predictions" && detail.segmentTextActive]}>
              Predictions ({predictions.length})
            </Text>
          </Pressable>
        </View>

        {/* Tab Content */}
        {loading ? (
          <ActivityIndicator size="large" color="#22D3EE" style={{ marginVertical: 40 }} />
        ) : activeTab === "signals" ? (
          signals.length === 0 ? (
            <View style={detail.emptyState}>
              <RadioTower size={28} color="#334155" />
              <Text style={detail.emptyText}>No signals detected for this competitor</Text>
            </View>
          ) : (
            signals.map((s) => (
              <View key={s.id} style={detail.signalCard}>
                <View style={detail.signalTopRow}>
                  <SignalBadge type={s.signal_type} size="md" />
                  <Text style={detail.signalSource}>{s.source}</Text>
                </View>
                <Text style={detail.signalTitle}>{s.title}</Text>
                {s.description && (
                  <Text style={detail.signalDesc} numberOfLines={2}>{s.description}</Text>
                )}
                <View style={detail.signalScores}>
                  <View style={detail.signalScoreItem}>
                    <Text style={detail.scoreLabel}>Impact</Text>
                    <ImpactBar score={s.impact_score} />
                  </View>
                  <View style={detail.signalScoreItem}>
                    <Text style={detail.scoreLabel}>Urgency</Text>
                    <ImpactBar score={s.urgency_score} maxScore={10} />
                  </View>
                </View>
              </View>
            ))
          )
        ) : (
          predictions.length === 0 ? (
            <View style={detail.emptyState}>
              <BrainCircuit size={28} color="#334155" />
              <Text style={detail.emptyText}>No predictions available for this competitor</Text>
            </View>
          ) : (
            predictions.map((p) => (
              <View key={p.id} style={detail.predictionCard}>
                <View style={detail.predTopRow}>
                  <ThreatBadge level={p.threat_level} />
                  <View style={detail.confidenceBar}>
                    <View style={detail.confTrack}>
                      <View style={[detail.confFill, { width: `${p.confidence}%` }]} />
                    </View>
                    <Text style={detail.confText}>{p.confidence}%</Text>
                  </View>
                </View>
                <Text style={detail.predText}>{p.prediction}</Text>
                {p.ai_reasoning && (
                  <View style={detail.reasonRow}>
                    <BrainCircuit size={12} color="#A78BFA" />
                    <Text style={detail.reasonText}>{p.ai_reasoning}</Text>
                  </View>
                )}
              </View>
            ))
          )
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const detail = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0B1121",
  },
  stickyHeader: {
    backgroundColor: "#0F172A",
    borderBottomWidth: 1,
    borderBottomColor: "#1E293B",
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  backText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#22D3EE",
  },
  scrollContent: {
    padding: 16,
  },
  profileCard: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: "#334155",
    marginBottom: 14,
  },
  profileTopRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  profileAvatar: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: "#164E63",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#22D3EE55",
  },
  profileAvatarText: {
    fontSize: 22,
    fontWeight: "800",
    color: "#22D3EE",
  },
  profileInfo: {
    gap: 2,
  },
  profileName: {
    fontSize: 22,
    fontWeight: "800",
    color: "#F8FAFC",
  },
  profileIndustry: {
    fontSize: 13,
    color: "#64748B",
  },
  profileWebsite: {
    fontSize: 12,
    color: "#475569",
    marginTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#334155",
    paddingTop: 10,
  },
  statsRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 14,
  },
  statCard: {
    flex: 1,
    backgroundColor: "#1E293B",
    borderRadius: 12,
    padding: 10,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#334155",
  },
  statValue: {
    fontSize: 18,
    fontWeight: "800",
    color: "#F1F5F9",
  },
  statLabel: {
    fontSize: 8,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 0.8,
    textTransform: "uppercase",
    marginTop: 2,
  },
  topPredCard: {
    backgroundColor: "#1A0F2E",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#4C1D95",
    marginBottom: 14,
  },
  topPredHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 8,
  },
  topPredTitle: {
    flex: 1,
    fontSize: 12,
    fontWeight: "700",
    color: "#A78BFA",
    letterSpacing: 0.5,
  },
  confBadge: {
    backgroundColor: "#2D1B4E",
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  confBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#A78BFA",
  },
  topPredText: {
    fontSize: 13,
    color: "#C4B5FD",
    lineHeight: 20,
  },
  segmentRow: {
    flexDirection: "row",
    backgroundColor: "#0F172A",
    borderRadius: 12,
    padding: 4,
    borderWidth: 1,
    borderColor: "#334155",
    marginBottom: 14,
  },
  segment: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 10,
    borderRadius: 10,
  },
  segmentActive: {
    backgroundColor: "#1E293B",
  },
  segmentText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#64748B",
  },
  segmentTextActive: {
    color: "#F1F5F9",
  },
  signalCard: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#2D3A4E",
  },
  signalTopRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  signalSource: {
    fontSize: 10,
    color: "#475569",
    fontStyle: "italic",
  },
  signalTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#E2E8F0",
    marginBottom: 4,
  },
  signalDesc: {
    fontSize: 13,
    color: "#94A3B8",
    lineHeight: 19,
    marginBottom: 10,
  },
  signalScores: {
    gap: 6,
  },
  signalScoreItem: {
    gap: 3,
  },
  scoreLabel: {
    fontSize: 10,
    fontWeight: "600",
    color: "#475569",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  predictionCard: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#2D3A4E",
    borderLeftWidth: 3,
    borderLeftColor: "#A78BFA",
  },
  predTopRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  confidenceBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  confTrack: {
    width: 50,
    height: 4,
    backgroundColor: "#0F172A",
    borderRadius: 2,
    overflow: "hidden",
  },
  confFill: {
    height: "100%",
    backgroundColor: "#A78BFA",
    borderRadius: 2,
  },
  confText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#A78BFA",
    minWidth: 28,
  },
  predText: {
    fontSize: 14,
    color: "#E2E8F0",
    lineHeight: 21,
  },
  reasonRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 6,
    marginTop: 10,
    backgroundColor: "#0F172A",
    borderRadius: 8,
    padding: 10,
  },
  reasonText: {
    flex: 1,
    fontSize: 12,
    color: "#64748B",
    lineHeight: 17,
    fontStyle: "italic",
  },
  emptyState: {
    alignItems: "center",
    paddingVertical: 40,
    gap: 10,
  },
  emptyText: {
    fontSize: 14,
    color: "#475569",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Main Competitors Screen
// ─────────────────────────────────────────────────────────────────────────────

export default function CompetitorsScreen() {
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [signalsMap, setSignalsMap] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selected, setSelected] = useState<Competitor | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

  const fetchData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const competitorsData = await api.competitors.list();
      setCompetitors(competitorsData);

      // Fetch signal counts for each competitor
      const signalCounts: Record<string, number> = {};
      if (competitorsData.length > 0) {
        const allSignals = await api.signals.list({ limit: 200 });
        for (const sig of allSignals) {
          signalCounts[sig.competitor_id] = (signalCounts[sig.competitor_id] || 0) + 1;
        }
      }
      setSignalsMap(signalCounts);
    } catch (err) {
      console.warn("Could not fetch data:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Show detail view
  if (selected) {
    return <CompetitorDetail competitor={selected} onBack={() => setSelected(null)} />;
  }

  // Filter by search & signal-type filter
  const filtered = competitors.filter((c) => {
    const matchesSearch = searchQuery === "" ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.industry?.toLowerCase().includes(searchQuery.toLowerCase());
    // activeFilter currently shows all (signal-type filter applied in detail view)
    return matchesSearch;
  });

  return (
    <View style={screen.container}>
      {/* Sticky Search + Filter Header */}
      <View style={screen.stickyHeader}>
        <View style={screen.titleRow}>
          <View style={screen.titleGroup}>
            <Users size={20} color="#22D3EE" />
            <View>
              <Text style={screen.title}>Competitors</Text>
              <Text style={screen.subtitle}>
                {competitors.length} tracked · {filtered.length} shown
              </Text>
            </View>
          </View>
          <Pressable onPress={() => fetchData()} style={screen.refreshBtn}>
            <RefreshCw size={16} color="#64748B" />
          </Pressable>
        </View>

        {/* Search */}
        <View style={screen.searchWrap}>
          <Search size={16} color="#475569" />
          <TextInput
            style={screen.searchInput}
            placeholder="Search competitors..."
            placeholderTextColor="#475569"
            value={searchQuery}
            onChangeText={setSearchQuery}
            autoCapitalize="none"
            autoCorrect={false}
            clearButtonMode="while-editing"
          />
        </View>

        {/* Filter chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={screen.filterRow}
          contentContainerStyle={{ gap: 6 }}
        >
          {FILTER_OPTIONS.map((opt) => {
            const isActive = activeFilter === opt.value;
            const Icon = opt.icon;
            return (
              <Pressable
                key={opt.value}
                style={[screen.filterChip, isActive && screen.filterChipActive]}
                onPress={() => setActiveFilter(opt.value)}
              >
                <Icon size={12} color={isActive ? "#22D3EE" : "#64748B"} />
                <Text style={[screen.filterChipText, isActive && screen.filterChipTextActive]}>
                  {opt.label}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      {/* List */}
      <ScrollView
        style={screen.listArea}
        contentContainerStyle={screen.listContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchData(true)}
            tintColor="#22D3EE"
          />
        }
      >
        {loading ? (
          <View style={screen.centered}>
            <ActivityIndicator size="large" color="#22D3EE" />
          </View>
        ) : filtered.length === 0 ? (
          <View style={screen.emptyState}>
            <View style={screen.emptyIconWrap}>
              <TrendingUp size={32} color="#334155" />
            </View>
            <Text style={screen.emptyTitle}>
              {searchQuery ? "No matching competitors" : "No competitors tracked"}
            </Text>
            <Text style={screen.emptyText}>
              {searchQuery
                ? "Try a different search term"
                : "Go to Home to initialise your War Room"}
            </Text>
          </View>
        ) : (
          filtered.map((c) => (
            <CompetitorCard
              key={c.id}
              competitor={c}
              signalCount={signalsMap[c.id] ?? 0}
              onPress={() => setSelected(c)}
            />
          ))
        )}

        <View style={{ height: 20 }} />
      </ScrollView>
    </View>
  );
}

const screen = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0B1121",
  },
  stickyHeader: {
    backgroundColor: "#0F172A",
    borderBottomWidth: 1,
    borderBottomColor: "#1E293B",
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 10,
    gap: 10,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  titleGroup: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
    color: "#F8FAFC",
  },
  subtitle: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  refreshBtn: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: "#1E293B",
    borderWidth: 1,
    borderColor: "#334155",
    alignItems: "center",
    justifyContent: "center",
  },
  searchWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    backgroundColor: "#1E293B",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
    paddingHorizontal: 12,
    paddingVertical: 2,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 10,
    fontSize: 14,
    color: "#F1F5F9",
  },
  filterRow: {
    flexShrink: 0,
  },
  filterChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 99,
    backgroundColor: "#1E293B",
    borderWidth: 1,
    borderColor: "#334155",
  },
  filterChipActive: {
    backgroundColor: "#164E63",
    borderColor: "#22D3EE",
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#64748B",
  },
  filterChipTextActive: {
    color: "#22D3EE",
  },
  listArea: {
    flex: 1,
  },
  listContent: {
    padding: 16,
    paddingBottom: 40,
  },
  centered: {
    paddingVertical: 60,
    alignItems: "center",
  },
  emptyState: {
    alignItems: "center",
    paddingVertical: 60,
    gap: 12,
  },
  emptyIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "#1E293B",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#334155",
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: "#94A3B8",
  },
  emptyText: {
    fontSize: 13,
    color: "#475569",
    textAlign: "center",
    lineHeight: 20,
    paddingHorizontal: 20,
  },
});
