import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Pressable,
  RefreshControl,
  TextInput,
  Dimensions,
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
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Award,
  BookOpen,
  Dna,
} from "lucide-react-native";
import Svg, { Path, Line, Circle } from "react-native-svg";
import {
  api,
  type Competitor,
  type Signal,
  type Prediction,
} from "../../services/apiClient";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

// ─────────────────────────────────────────────────────────────────────────────
// Color Palette (MarketWatch: Cyan, Green, Amber)
// ─────────────────────────────────────────────────────────────────────────────

const BRAND_PURPLE = "#8B5CF6";
const BRAND_GROWTH_GREEN = "#4ADE80";
const BRAND_AMBER = "#F59E0B";

const SIGNAL_COLORS: Record<string, string> = {
  Hiring: "#38BDF8",
  Funding: "#4ADE80",
  Marketing: "#FB923C",
  Product: "#A78BFA",
  Expansion: "#F87171",
  Leadership: "#FBBF24",
  Sentiment: "#E2E8F0",
};

const THREAT_COLORS: Record<string, string> = {
  critical: "#F87171",
  high: "#FB923C",
  medium: "#FBBF24",
  low: "#4ADE80",
};

// ─────────────────────────────────────────────────────────────────────────────
// Subcomponents
// ─────────────────────────────────────────────────────────────────────────────

function SignalBadge({ type, size = "sm" }: { type: string; size?: "sm" | "md" }) {
  const color = SIGNAL_COLORS[type] ?? "#94A3B8";
  const isMd = size === "md";
  return (
    <View style={[sigBadge.pill, {
      backgroundColor: color + "18",
      borderColor: color + "40",
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

function ThreatBadge({ level }: { level: string }) {
  const color = THREAT_COLORS[level] ?? "#94A3B8";
  return (
    <View style={[tb.pill, { backgroundColor: color + "18", borderColor: color + "40" }]}>
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

function ImpactBar({ score, maxScore = 10 }: { score: number; maxScore?: number }) {
  const pct = Math.min((score / maxScore) * 100, 100);
  const color = score >= 8 ? "#EF4444" : score >= 6 ? "#F97316" : score >= 4 ? "#FBBF24" : "#10B981";
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

const FILTER_OPTIONS = [
  { label: "All", value: "all", icon: Users },
  { label: "Funding", value: "Funding", icon: TrendingUp },
  { label: "Hiring", value: "Hiring", icon: Users },
  { label: "Product", value: "Product", icon: BrainCircuit },
  { label: "Marketing", value: "Marketing", icon: RadioTower },
];

// ─────────────────────────────────────────────────────────────────────────────
// Interactive SVG Threat Gauge
// ─────────────────────────────────────────────────────────────────────────────

function ThreatGauge({ level }: { level: string }) {
  const color = THREAT_COLORS[level] ?? "#94A3B8";

  // Calculate needle angle based on threat level
  let rotationDeg = 0;
  if (level === "low") rotationDeg = -60;
  else if (level === "medium") rotationDeg = -20;
  else if (level === "high") rotationDeg = 20;
  else if (level === "critical") rotationDeg = 60;

  return (
    <View style={gauge.container}>
      <View style={gauge.canvasWrap}>
        <Svg width={180} height={100} viewBox="0 0 180 100">
          {/* Low arc */}
          <Path d="M 20 90 A 70 70 0 0 1 50 30" fill="none" stroke="#10B981" strokeWidth={12} strokeLinecap="round" />
          {/* Medium arc */}
          <Path d="M 54 27 A 70 70 0 0 1 90 20" fill="none" stroke="#FBBF24" strokeWidth={12} />
          {/* High arc */}
          <Path d="M 90 20 A 70 70 0 0 1 126 27" fill="none" stroke="#F97316" strokeWidth={12} />
          {/* Critical arc */}
          <Path d="M 130 30 A 70 70 0 0 1 160 90" fill="none" stroke="#EF4444" strokeWidth={12} strokeLinecap="round" />

          {/* Needle Base Circle */}
          <Circle cx={90} cy={90} r={10} fill="#1E293B" stroke={color} strokeWidth={3} />
          <Circle cx={90} cy={90} r={4} fill={color} />

          {/* Needle pointer */}
          <Line
            x1={90}
            y1={90}
            x2={90}
            y2={35}
            stroke={color}
            strokeWidth={4}
            strokeLinecap="round"
            transform={`rotate(${rotationDeg}, 90, 90)`}
          />
        </Svg>
      </View>
      <View style={gauge.legend}>
        <Text style={[gauge.levelName, { color }]}>{level.toUpperCase()} THREAT LEVEL</Text>
        <Text style={gauge.desc}>
          {level === "low" && "Stable market presence. Low GTM noise."}
          {level === "medium" && "Moderate traction. Launching steady features."}
          {level === "high" && "High expansion activity. Watch pricing models."}
          {level === "critical" && "Aggressive growth campaign. Immediate counter needed."}
        </Text>
      </View>
    </View>
  );
}

const gauge = StyleSheet.create({
  container: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#334155",
    padding: 16,
    alignItems: "center",
    marginBottom: 14,
  },
  canvasWrap: {
    height: 100,
    width: 180,
    justifyContent: "flex-end",
  },
  legend: {
    alignItems: "center",
    marginTop: 8,
    gap: 4,
  },
  levelName: {
    fontSize: 14,
    fontWeight: "800",
    letterSpacing: 0.5,
  },
  desc: {
    fontSize: 11,
    color: "#64748B",
    textAlign: "center",
    paddingHorizontal: 16,
    lineHeight: 15,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Sales Playbook
// ─────────────────────────────────────────────────────────────────────────────

function SalesPlaybook({ competitorName }: { competitorName: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <View style={playbook.container}>
      <Pressable style={playbook.header} onPress={() => setExpanded(!expanded)}>
        <View style={playbook.titleRow}>
          <BookOpen size={16} color={BRAND_PURPLE} />
          <Text style={playbook.title}>Sales Playbook vs {competitorName}</Text>
        </View>
        {expanded ? <ChevronUp size={16} color="#64748B" /> : <ChevronDown size={16} color="#64748B" />}
      </Pressable>

      {expanded && (
        <View style={playbook.body}>
          {/* Card 1: Objection handling */}
          <View style={playbook.sectionCard}>
            <View style={playbook.sectionBadge}>
              <Award size={12} color="#10B981" />
              <Text style={playbook.badgeText}>Objection Handling</Text>
            </View>
            <Text style={playbook.scenarioText}>
              "Prospect: We are evaluating {competitorName} because their price tier is lower."
            </Text>
            <Text style={playbook.scriptText}>
              "Response Script: While {competitorName} offers low entry fees, their platform relies entirely on third-party cloud APIs with variable performance. MarketWatch provides local Gemma-powered models that run fully on-device, saving you 40% in api network delays and offering offline security compliance."
            </Text>
          </View>

          {/* Card 2: Landmines */}
          <View style={playbook.sectionCard}>
            <View style={[playbook.sectionBadge, { backgroundColor: "#EF444415", borderColor: "#EF444440" }]}>
              <Zap size={12} color="#EF4444" />
              <Text style={[playbook.badgeText, { color: "#EF4444" }]}>Landmines to Lay</Text>
            </View>
            <View style={playbook.bullets}>
              <Text style={playbook.bullet}>• "Ask them how they guarantee offline operation when field managers go remote."</Text>
              <Text style={playbook.bullet}>• "Inquire about user data security, as their models export queries to cloud servers."</Text>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

const playbook = StyleSheet.create({
  container: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#334155",
    overflow: "hidden",
    marginBottom: 14,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    backgroundColor: "#11182750",
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  title: {
    fontSize: 13,
    fontWeight: "700",
    color: "#F1F5F9",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  body: {
    padding: 16,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: "#33415550",
  },
  sectionCard: {
    backgroundColor: "#0F172A",
    borderRadius: 10,
    padding: 12,
    borderWidth: 1,
    borderColor: "#33415550",
    gap: 8,
  },
  sectionBadge: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 4,
    backgroundColor: "#10B98115",
    borderColor: "#10B98140",
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#10B981",
  },
  scenarioText: {
    fontSize: 12,
    color: "#94A3B8",
    fontStyle: "italic",
    lineHeight: 17,
  },
  scriptText: {
    fontSize: 12,
    color: "#F1F5F9",
    lineHeight: 18,
    fontWeight: "500",
  },
  bullets: {
    gap: 6,
  },
  bullet: {
    fontSize: 12,
    color: "#F1F5F9",
    lineHeight: 18,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// DNA Comparison Matrix
// ─────────────────────────────────────────────────────────────────────────────

function DNAMatrix({ competitorName, domain }: { competitorName: string; domain: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <View style={dna.container}>
      <Pressable style={dna.header} onPress={() => setExpanded(!expanded)}>
        <View style={dna.titleRow}>
          <Dna size={16} color={BRAND_GROWTH_GREEN} />
          <Text style={dna.title}>Competitor DNA Comparison</Text>
        </View>
        {expanded ? <ChevronUp size={16} color="#64748B" /> : <ChevronDown size={16} color="#64748B" />}
      </Pressable>

      {expanded && (
        <View style={dna.body}>
          {/* Table Headers */}
          <View style={dna.row}>
            <Text style={[dna.cell, dna.headerCell, { flex: 1.2 }]}>Metric</Text>
            <Text style={[dna.cell, dna.headerCell, { color: BRAND_PURPLE }]}>MarketWatch (Us)</Text>
            <Text style={[dna.cell, dna.headerCell, { color: BRAND_AMBER }]}>{competitorName}</Text>
          </View>
          
          {/* Rows */}
          {[
            { metric: "Deployment", us: "Local Gemma 3", them: "Cloud API Only" },
            { metric: "Data Privacy", us: "Zero Leakage", them: "External Server" },
            { metric: "Offline Support", us: "Full SQLite RAG", them: "Disabled" },
            { metric: "Engine Velocity", us: "10ms Latency", them: "50-100ms API" },
          ].map((item, idx) => (
            <View key={idx} style={[dna.row, idx % 2 === 0 && dna.rowAlt]}>
              <Text style={[dna.cell, { fontWeight: "700", color: "#94A3B8", flex: 1.2 }]}>{item.metric}</Text>
              <Text style={[dna.cell, { color: BRAND_GROWTH_GREEN, fontWeight: "600" }]}>{item.us}</Text>
              <Text style={[dna.cell, { color: "#E2E8F0" }]}>{item.them}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
}

const dna = StyleSheet.create({
  container: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#334155",
    overflow: "hidden",
    marginBottom: 14,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    backgroundColor: "#11182750",
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  title: {
    fontSize: 13,
    fontWeight: "700",
    color: "#F1F5F9",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  body: {
    padding: 12,
  },
  row: {
    flexDirection: "row",
    paddingVertical: 10,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#33415530",
    alignItems: "center",
  },
  rowAlt: {
    backgroundColor: "#0F172A50",
    borderRadius: 6,
  },
  cell: {
    flex: 1,
    fontSize: 12,
    color: "#F1F5F9",
  },
  headerCell: {
    fontWeight: "800",
    textTransform: "uppercase",
    fontSize: 10,
    letterSpacing: 0.5,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Competitor Card (Redesigned for MarketWatch list)
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
          <ChevronRight size={18} color="#475569" />
        </View>

        <View style={cc.metaRow}>
          <View style={cc.metaChip}>
            <Eye size={11} color="#94A3B8" />
            <Text style={cc.metaText}>{competitor.market_scope ?? "National"}</Text>
          </View>
          {signalCount !== undefined && (
            <View style={[cc.metaChip, { borderColor: BRAND_PURPLE + "40" }]}>
              <RadioTower size={11} color={BRAND_PURPLE} />
              <Text style={[cc.metaText, { color: BRAND_PURPLE }]}>{signalCount} signals</Text>
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
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#334155",
    overflow: "hidden",
    marginBottom: 10,
  },
  leftAccent: {
    width: 4,
    backgroundColor: BRAND_PURPLE,
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
    backgroundColor: "#164E6330",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: BRAND_PURPLE + "55",
  },
  avatarText: {
    fontSize: 17,
    fontWeight: "800",
    color: BRAND_PURPLE,
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
// Competitor Detail View (Redesigned)
// ─────────────────────────────────────────────────────────────────────────────

type DetailTab = "timeline" | "predictions";

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
  const [activeTab, setActiveTab] = useState<DetailTab>("timeline");

  useEffect(() => {
    async function load() {
      try {
        const [sigData, predData] = await Promise.all([
          api.signals.list({ competitor_id: competitor.id, sort_by: "newest", limit: 50 }),
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
          <ArrowLeft size={18} color={BRAND_PURPLE} />
          <Text style={detail.backText}>Back to Competitors</Text>
        </Pressable>
      </View>

      <ScrollView contentContainerStyle={detail.scrollContent} showsVerticalScrollIndicator={false}>
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

        {/* Stats Grid */}
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

        {/* Interactive SVG Threat Alert Gauge */}
        <ThreatGauge level={competitor.market_scope ? "high" : topThreat?.threat_level ?? "medium"} />

        {/* DNA Matrix */}
        <DNAMatrix competitorName={competitor.name} domain={competitor.industry} />

        {/* GTM Objection Handler & Sales Playbook */}
        <SalesPlaybook competitorName={competitor.name} />

        {/* Segmented Tab Bar */}
        <View style={detail.segmentRow}>
          <Pressable
            style={[detail.segment, activeTab === "timeline" && detail.segmentActive]}
            onPress={() => setActiveTab("timeline")}
          >
            <RadioTower size={14} color={activeTab === "timeline" ? BRAND_PURPLE : "#64748B"} />
            <Text style={[detail.segmentText, activeTab === "timeline" && detail.segmentTextActive]}>
              Timeline Feed ({signals.length})
            </Text>
          </Pressable>
          <Pressable
            style={[detail.segment, activeTab === "predictions" && detail.segmentActive]}
            onPress={() => setActiveTab("predictions")}
          >
            <BrainCircuit size={14} color={activeTab === "predictions" ? BRAND_GROWTH_GREEN : "#64748B"} />
            <Text style={[detail.segmentText, activeTab === "predictions" && detail.segmentTextActive]}>
              Move Predictions ({predictions.length})
            </Text>
          </Pressable>
        </View>

        {/* Tab Content */}
        {loading ? (
          <ActivityIndicator size="large" color={BRAND_PURPLE} style={{ marginVertical: 40 }} />
        ) : activeTab === "timeline" ? (
          signals.length === 0 ? (
            <View style={detail.emptyState}>
              <RadioTower size={28} color="#334155" />
              <Text style={detail.emptyText}>No signals detected for this competitor</Text>
            </View>
          ) : (
            /* Vertical Timeline Feed */
            <View style={detail.timelineContainer}>
              <View style={detail.timelineLine} />
              {signals.map((s, idx) => {
                const badgeColor = SIGNAL_COLORS[s.signal_type] ?? "#94A3B8";
                return (
                  <View key={s.id} style={detail.timelineItem}>
                    {/* Timeline Node dot */}
                    <View style={[detail.timelineNode, { borderColor: badgeColor, backgroundColor: "#0B1121" }]}>
                      <View style={[detail.timelineInnerDot, { backgroundColor: badgeColor }]} />
                    </View>

                    {/* Timeline Card */}
                    <View style={detail.timelineContent}>
                      <View style={detail.signalTopRow}>
                        <SignalBadge type={s.signal_type} size="md" />
                        <Text style={detail.signalSource}>{s.source}</Text>
                      </View>
                      <Text style={detail.signalTitle}>{s.title}</Text>
                      {s.description && (
                        <Text style={detail.signalDesc}>{s.description}</Text>
                      )}
                      <View style={detail.signalScores}>
                        <View style={detail.signalScoreItem}>
                          <Text style={detail.scoreLabel}>Impact</Text>
                          <ImpactBar score={s.impact_score} />
                        </View>
                        <View style={detail.signalScoreItem}>
                          <Text style={detail.scoreLabel}>Urgency</Text>
                          <ImpactBar score={s.urgency_score} />
                        </View>
                      </View>
                    </View>
                  </View>
                );
              })}
            </View>
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
    gap: 8,
  },
  backText: {
    fontSize: 14,
    fontWeight: "700",
    color: "#F1F5F9",
    textTransform: "uppercase",
    letterSpacing: 0.5,
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
    backgroundColor: "#164E6330",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: BRAND_PURPLE + "55",
  },
  profileAvatarText: {
    fontSize: 22,
    fontWeight: "800",
    color: BRAND_PURPLE,
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
    color: "#64748B",
    marginTop: 10,
    borderTopWidth: 1,
    borderTopColor: "#33415550",
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
    color: "#64748B",
    letterSpacing: 0.8,
    textTransform: "uppercase",
    marginTop: 2,
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
  timelineContainer: {
    position: "relative",
    paddingLeft: 20,
  },
  timelineLine: {
    position: "absolute",
    left: 7,
    top: 10,
    bottom: 10,
    width: 2,
    backgroundColor: "#33415550",
  },
  timelineItem: {
    position: "relative",
    marginBottom: 16,
    paddingLeft: 10,
  },
  timelineNode: {
    position: "absolute",
    left: -20,
    top: 14,
    width: 16,
    height: 16,
    borderRadius: 8,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
    zIndex: 10,
  },
  timelineInnerDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  timelineContent: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: "#334155",
  },
  signalTopRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 8,
  },
  signalSource: {
    fontSize: 10,
    color: "#64748B",
    fontStyle: "italic",
  },
  signalTitle: {
    fontSize: 15,
    fontWeight: "700",
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
    fontSize: 9,
    fontWeight: "700",
    color: "#64748B",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  predictionCard: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: "#334155",
    borderLeftWidth: 4,
    borderLeftColor: BRAND_GROWTH_GREEN,
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
    backgroundColor: BRAND_GROWTH_GREEN,
    borderRadius: 2,
  },
  confText: {
    fontSize: 10,
    fontWeight: "700",
    color: BRAND_GROWTH_GREEN,
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
    color: "#64748B",
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

  // Filter by search
  const filtered = competitors.filter((c) => {
    const matchesSearch = searchQuery === "" ||
      c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.industry?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <View style={screen.container}>
      {/* Sticky Search + Filter Header */}
      <View style={screen.stickyHeader}>
        <View style={screen.titleRow}>
          <View style={screen.titleGroup}>
            <Users size={20} color={BRAND_PURPLE} />
            <View>
              <Text style={screen.title}>Competitor Targets</Text>
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
            placeholder="Search targets..."
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
                <Icon size={12} color={isActive ? BRAND_PURPLE : "#64748B"} />
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
            tintColor={BRAND_PURPLE}
          />
        }
      >
        {loading ? (
          <View style={screen.centered}>
            <ActivityIndicator size="large" color={BRAND_PURPLE} />
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
                : "Go to Home to initialise your MarketWatch dashboard"}
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
    borderColor: BRAND_PURPLE,
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: "600",
    color: "#64748B",
  },
  filterChipTextActive: {
    color: BRAND_PURPLE,
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
    color: "#64748B",
    textAlign: "center",
    lineHeight: 20,
    paddingHorizontal: 20,
  },
});
