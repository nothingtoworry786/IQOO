import { useState, useEffect, useCallback, useRef } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  TextInput,
  Pressable,
  ActivityIndicator,
  Alert,
  Animated,
  Dimensions,
} from "react-native";
import {
  ShieldAlert,
  Search,
  RefreshCw,
  Zap,
  TrendingUp,
  Users,
  RadioTower,
  AlertTriangle,
  Target,
  Sparkles,
  Crosshair,
  BarChart3,
  ScanEye,
} from "lucide-react-native";
import { api, type Competitor, type DiscoverResponse } from "../../services/apiClient";
import { usePersona, type Persona } from "../../store/personaStore";

const { width: SCREEN_WIDTH } = Dimensions.get("window");

// ─────────────────────────────────────────────────────────────────────────────
// Persona Switcher Component (Redesigned)
// ─────────────────────────────────────────────────────────────────────────────

function PersonaSwitcher() {
  const { state, setPersona } = usePersona();
  const personas: Persona[] = ["Founder", "Marketing"];
  const glowAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(glowAnim, { toValue: 1, duration: 2000, useNativeDriver: true }),
        Animated.timing(glowAnim, { toValue: 0, duration: 2000, useNativeDriver: true }),
      ]),
    ).start();
  }, []);

  return (
    <View style={switcher.wrapper}>
      <View style={switcher.container}>
        {personas.map((p) => {
          const isActive = state.persona === p;
          const Icon = p === "Founder" ? Target : ScanEye;
          return (
            <Pressable
              key={p}
              style={[
                switcher.pill,
                isActive && switcher.pillActive,
              ]}
              onPress={() => setPersona(p)}
              accessibilityRole="button"
              accessibilityState={{ selected: isActive }}
            >
              <Icon size={16} color={isActive ? "#22D3EE" : "#64748B"} />
              <Text
                style={[
                  switcher.pillText,
                  isActive && switcher.pillTextActive,
                ]}
              >
                {p === "Founder" ? "Founder" : "Marketing"}
              </Text>
              {isActive && <View style={switcher.activeDot} />}
            </Pressable>
          );
        })}
      </View>
      <Text style={switcher.hint}>
        {state.persona === "Founder"
          ? "🔍 Showing funding, expansion & hiring signals"
          : "🎯 Showing campaign, copy & feature signals"}
      </Text>
    </View>
  );
}

const switcher = StyleSheet.create({
  wrapper: {
    gap: 8,
  },
  container: {
    flexDirection: "row",
    gap: 8,
    backgroundColor: "#0F172A",
    borderRadius: 14,
    padding: 5,
    borderWidth: 1,
    borderColor: "#1E293B",
  },
  pill: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 10,
    position: "relative",
  },
  pillActive: {
    backgroundColor: "#164E63",
    borderWidth: 1,
    borderColor: "#22D3EE",
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  pillText: {
    fontSize: 13,
    fontWeight: "600",
    color: "#64748B",
  },
  pillTextActive: {
    color: "#22D3EE",
  },
  activeDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: "#22D3EE",
    position: "absolute",
    bottom: 3,
    right: "50%",
    marginRight: -2.5,
  },
  hint: {
    fontSize: 11,
    color: "#475569",
    textAlign: "center",
    fontStyle: "italic",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// KPI Card Component
// ─────────────────────────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <View style={[kpi.container, { borderColor: color + "30" }]}>
      <View style={[kpi.iconWrap, { backgroundColor: color + "15" }]}>
        {icon}
      </View>
      <Text style={[kpi.value, { color }]}>{value}</Text>
      <Text style={kpi.label}>{label}</Text>
    </View>
  );
}

const kpi = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    padding: 12,
    alignItems: "center",
    gap: 4,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 4,
  },
  value: {
    fontSize: 22,
    fontWeight: "800",
    letterSpacing: -0.5,
  },
  label: {
    fontSize: 9,
    fontWeight: "700",
    color: "#64748B",
    letterSpacing: 0.8,
    textTransform: "uppercase",
    textAlign: "center",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Quick Action Button
// ─────────────────────────────────────────────────────────────────────────────

function QuickAction({
  icon,
  label,
  onPress,
}: {
  icon: React.ReactNode;
  label: string;
  onPress: () => void;
}) {
  return (
    <Pressable style={qa.container} onPress={onPress}>
      <View style={qa.iconWrap}>{icon}</View>
      <Text style={qa.label}>{label}</Text>
    </Pressable>
  );
}

const qa = StyleSheet.create({
  container: {
    alignItems: "center",
    gap: 6,
    padding: 12,
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#334155",
    minWidth: (SCREEN_WIDTH - 64) / 3,
  },
  iconWrap: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: "#0F172A",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#334155",
  },
  label: {
    fontSize: 10,
    fontWeight: "600",
    color: "#94A3B8",
    textAlign: "center",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Competitor Card (Redesigned for Home)
// ─────────────────────────────────────────────────────────────────────────────

const THREAT_GRADIENTS: Record<string, string[]> = {
  high: ["#FB923C", "#F97316"],
  critical: ["#F87171", "#EF4444"],
  medium: ["#FBBF24", "#F59E0B"],
  low: ["#4ADE80", "#22C55E"],
};

function HomeCompetitorCard({ competitor }: { competitor: Competitor }) {
  return (
    <View style={hcc.container}>
      <View style={hcc.leftStrip} />
      <View style={hcc.body}>
        <View style={hcc.topRow}>
          <View style={hcc.nameRow}>
            <View style={hcc.avatar}>
              <Text style={hcc.avatarText}>
                {competitor.name.charAt(0).toUpperCase()}
              </Text>
            </View>
            <View>
              <Text style={hcc.name}>{competitor.name}</Text>
              <Text style={hcc.industry}>{competitor.industry}</Text>
            </View>
          </View>
          <View style={hcc.statusBadge}>
            <View style={hcc.statusDot} />
            <Text style={hcc.statusText}>LIVE</Text>
          </View>
        </View>
        {competitor.website && (
          <Text style={hcc.website} numberOfLines={1}>
            {competitor.website}
          </Text>
        )}
        <View style={hcc.metaRow}>
          <View style={hcc.metaChip}>
            <Text style={hcc.metaChipText}>{competitor.market_scope ?? "National"}</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

const hcc = StyleSheet.create({
  container: {
    flexDirection: "row",
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#334155",
    overflow: "hidden",
    marginBottom: 10,
  },
  leftStrip: {
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
  nameRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  avatar: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: "#164E63",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#22D3EE",
  },
  avatarText: {
    fontSize: 16,
    fontWeight: "800",
    color: "#22D3EE",
  },
  name: {
    fontSize: 15,
    fontWeight: "700",
    color: "#F1F5F9",
  },
  industry: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  statusBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "#052E16",
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: "#4ADE80",
  },
  statusDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: "#4ADE80",
  },
  statusText: {
    fontSize: 9,
    fontWeight: "800",
    color: "#4ADE80",
    letterSpacing: 1,
  },
  website: {
    fontSize: 12,
    color: "#475569",
    marginTop: 6,
  },
  metaRow: {
    flexDirection: "row",
    gap: 6,
    marginTop: 8,
  },
  metaChip: {
    backgroundColor: "#0F172A",
    borderRadius: 99,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: "#334155",
  },
  metaChipText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#64748B",
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Main Dashboard Screen
// ─────────────────────────────────────────────────────────────────────────────

type DiscoveryPhase = "idle" | "loading" | "success" | "error";

export default function DashboardScreen() {
  const [companyName, setCompanyName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [phase, setPhase] = useState<DiscoveryPhase>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [discoveryResult, setDiscoveryResult] = useState<DiscoverResponse | null>(null);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [competitorsLoading, setCompetitorsLoading] = useState(false);

  const { state: personaState } = usePersona();

  // Animations
  const headerFade = useRef(new Animated.Value(0)).current;
  const formSlide = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(headerFade, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }),
      Animated.timing(formSlide, {
        toValue: 0,
        duration: 500,
        delay: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const fetchCompetitors = useCallback(async () => {
    setCompetitorsLoading(true);
    try {
      const data = await api.competitors.list();
      setCompetitors(data);
    } catch (err) {
      console.warn("Could not fetch competitors:", err);
    } finally {
      setCompetitorsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCompetitors();
  }, [fetchCompetitors]);

  const handleDiscover = useCallback(async () => {
    if (!companyName.trim() || !websiteUrl.trim()) {
      Alert.alert("Missing Fields", "Please enter both company name and website URL.");
      return;
    }
    setPhase("loading");
    setErrorMessage("");
    setDiscoveryResult(null);
    try {
      const result = await api.competitors.discover({
        company_name: companyName.trim(),
        website_url: websiteUrl.trim(),
      });
      setDiscoveryResult(result);
      setPhase("success");
      await fetchCompetitors();
    } catch (err: any) {
      setPhase("error");
      setErrorMessage(err?.message ?? "Discovery failed. Is the backend running?");
    }
  }, [companyName, websiteUrl, fetchCompetitors]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      {/* ── Hero Header ────────────────────────────────────────────────── */}
      <Animated.View style={[styles.hero, { opacity: headerFade }]}>
        <View style={styles.heroOverlay} />
        <View style={styles.heroContent}>
          <View style={styles.heroTopRow}>
            <View style={styles.heroTitleGroup}>
              <Text style={styles.heroEyebrow}>COMPETITIVE INTELLIGENCE</Text>
              <Text style={styles.heroTitle}>War Room</Text>
              <Text style={styles.heroSubtitle}>
                Real-time monitoring · {competitors.length} competitors tracked
              </Text>
            </View>
            <Pressable
              onPress={fetchCompetitors}
              style={styles.heroRefresh}
              accessibilityLabel="Refresh"
            >
              <RefreshCw size={16} color="#22D3EE" />
            </Pressable>
          </View>

          {/* KPI Strip */}
          <View style={styles.kpiRow}>
            <KpiCard
              label="Tracked"
              value={competitors.length}
              icon={<Users size={16} color="#22D3EE" />}
              color="#22D3EE"
            />
            <KpiCard
              label="Threats"
              value={competitors.length > 0 ? "3" : "—"}
              icon={<AlertTriangle size={16} color="#F87171" />}
              color="#F87171"
            />
            <KpiCard
              label="Status"
              value={"Live"}
              icon={<RadioTower size={16} color="#4ADE80" />}
              color="#4ADE80"
            />
          </View>
        </View>
      </Animated.View>

      {/* ── Intelligence Lens ──────────────────────────────────────────── */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>INTELLIGENCE LENS</Text>
        <PersonaSwitcher />
      </View>

      {/* ── Quick Actions ──────────────────────────────────────────────── */}
      <View style={styles.section}>
        <Text style={styles.sectionLabel}>QUICK ACTIONS</Text>
        <View style={styles.quickActionsRow}>
          <QuickAction
            icon={<Crosshair size={20} color="#22D3EE" />}
            label="Analyze"
            onPress={() => {}}
          />
          <QuickAction
            icon={<BarChart3 size={20} color="#A78BFA" />}
            label="Reports"
            onPress={() => {}}
          />
          <QuickAction
            icon={<Sparkles size={20} color="#FBBF24" />}
            label="Insights"
            onPress={() => {}}
          />
        </View>
      </View>

      {/* ── Discovery Form ─────────────────────────────────────────────── */}
      <Animated.View style={[styles.section, { transform: [{ translateY: formSlide }] }]}>
        <Text style={styles.sectionLabel}>ADD COMPETITOR TARGET</Text>
        <View style={styles.formCard}>
          <View style={styles.formGlow} />
          <View style={styles.formBody}>
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Company Name</Text>
              <View style={styles.inputWrap}>
                <Search size={16} color="#475569" style={{ marginLeft: 12 }} />
                <TextInput
                  style={styles.input}
                  placeholder="e.g. Zepto, Notion, Stripe"
                  placeholderTextColor="#475569"
                  value={companyName}
                  onChangeText={setCompanyName}
                  autoCapitalize="words"
                  autoCorrect={false}
                  returnKeyType="next"
                />
              </View>
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Website URL</Text>
              <View style={styles.inputWrap}>
                <Text style={styles.inputPrefix}>🌐</Text>
                <TextInput
                  style={styles.input}
                  placeholder="https://yourcompany.com"
                  placeholderTextColor="#475569"
                  value={websiteUrl}
                  onChangeText={setWebsiteUrl}
                  autoCapitalize="none"
                  autoCorrect={false}
                  keyboardType="url"
                  returnKeyType="done"
                  onSubmitEditing={handleDiscover}
                />
              </View>
            </View>

            <Pressable
              style={[styles.discoverBtn, phase === "loading" && styles.discoverBtnLoading]}
              onPress={handleDiscover}
              disabled={phase === "loading"}
            >
              {phase === "loading" ? (
                <ActivityIndicator size="small" color="#0F172A" />
              ) : (
                <>
                  <Zap size={18} color="#0F172A" />
                  <Text style={styles.discoverBtnText}>Discover & Seed</Text>
                </>
              )}
            </Pressable>

            {phase === "error" && (
              <View style={styles.errorBox}>
                <AlertTriangle size={14} color="#F87171" />
                <Text style={styles.errorText}>{errorMessage}</Text>
              </View>
            )}

            {phase === "success" && discoveryResult && (
              <View style={styles.successBox}>
                <Text style={styles.successIcon}>✓</Text>
                <View>
                  <Text style={styles.successTitle}>War Room Initialised</Text>
                  <Text style={styles.successText}>{discoveryResult.message}</Text>
                </View>
              </View>
            )}
          </View>
        </View>
      </Animated.View>

      {/* ── Tracked Competitors ────────────────────────────────────────── */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionLabel}>TRACKED COMPETITORS</Text>
          <View style={styles.sectionRight}>
            {competitorsLoading && <ActivityIndicator size="small" color="#22D3EE" />}
            <Text style={styles.sectionCount}>{competitors.length}</Text>
          </View>
        </View>

        {competitors.length === 0 && !competitorsLoading ? (
          <View style={styles.emptyState}>
            <View style={styles.emptyIconWrap}>
              <TrendingUp size={32} color="#334155" />
            </View>
            <Text style={styles.emptyTitle}>No competitors tracked</Text>
            <Text style={styles.emptyText}>
              Add a company above to seed competitive intelligence data
            </Text>
          </View>
        ) : (
          competitors.map((c) => <HomeCompetitorCard key={c.id} competitor={c} />)
        )}
      </View>

      {/* ── Discovery Result Highlight ─────────────────────────────────── */}
      {discoveryResult && discoveryResult.competitors.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>TOP THREAT</Text>
          <View style={styles.threatCard}>
            <View style={styles.threatHeader}>
              <ShieldAlert size={18} color="#FB923C" />
              <View style={styles.threatTitleGroup}>
                <Text style={styles.threatName}>{discoveryResult.competitors[0].name}</Text>
                <Text style={styles.threatIndustry}>
                  {discoveryResult.competitors[0].industry}
                </Text>
              </View>
              <View style={styles.threatLevelBadge}>
                <Text style={styles.threatLevelText}>
                  {discoveryResult.competitors[0].threat_level.toUpperCase()}
                </Text>
              </View>
            </View>
            <Text style={styles.threatNote}>
              Intelligence data seeded with signals, predictions, and threat briefings.
              Tap the Competitors tab for detailed analysis.
            </Text>
          </View>
        </View>
      )}

      <View style={{ height: 24 }} />
    </ScrollView>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Styles
// ─────────────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0B1121",
  },
  content: {
    paddingBottom: 40,
  },

  // Hero
  hero: {
    backgroundColor: "#0F172A",
    borderBottomWidth: 1,
    borderBottomColor: "#1E293B",
    position: "relative",
  },
  heroOverlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: "transparent",
  },
  heroContent: {
    padding: 20,
    paddingTop: 16,
  },
  heroTopRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 20,
  },
  heroTitleGroup: {},
  heroEyebrow: {
    fontSize: 10,
    fontWeight: "700",
    color: "#22D3EE",
    letterSpacing: 2,
    marginBottom: 4,
    textTransform: "uppercase",
  },
  heroTitle: {
    fontSize: 30,
    fontWeight: "900",
    color: "#F8FAFC",
    letterSpacing: -1,
  },
  heroSubtitle: {
    fontSize: 13,
    color: "#64748B",
    marginTop: 2,
  },
  heroRefresh: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: "#1E293B",
    borderWidth: 1,
    borderColor: "#334155",
    alignItems: "center",
    justifyContent: "center",
  },

  // KPI
  kpiRow: {
    flexDirection: "row",
    gap: 8,
  },

  // Section
  section: {
    paddingHorizontal: 16,
    marginTop: 20,
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 1.5,
    marginBottom: 10,
    textTransform: "uppercase",
  },
  sectionHeaderRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 10,
  },
  sectionRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  sectionCount: {
    fontSize: 14,
    fontWeight: "700",
    color: "#64748B",
  },

  // Quick actions
  quickActionsRow: {
    flexDirection: "row",
    gap: 8,
  },

  // Form
  formCard: {
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#334155",
    backgroundColor: "#1E293B",
    overflow: "hidden",
    position: "relative",
  },
  formGlow: {
    position: "absolute",
    top: -60,
    right: -60,
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: "rgba(34, 211, 238, 0.03)",
  },
  formBody: {
    padding: 16,
    gap: 14,
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#94A3B8",
    marginLeft: 2,
  },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#0F172A",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  inputPrefix: {
    fontSize: 14,
    paddingLeft: 12,
  },
  input: {
    flex: 1,
    paddingHorizontal: 10,
    paddingVertical: 12,
    fontSize: 14,
    color: "#F1F5F9",
  },
  discoverBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#22D3EE",
    borderRadius: 12,
    paddingVertical: 14,
    marginTop: 4,
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  discoverBtnLoading: {
    opacity: 0.7,
  },
  discoverBtnText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0F172A",
    letterSpacing: 0.5,
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    padding: 12,
    borderRadius: 12,
    backgroundColor: "#450A0A",
    borderWidth: 1,
    borderColor: "#F87171",
  },
  errorText: {
    flex: 1,
    fontSize: 13,
    color: "#F87171",
    lineHeight: 20,
  },
  successBox: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    padding: 14,
    borderRadius: 12,
    backgroundColor: "#052E16",
    borderWidth: 1,
    borderColor: "#4ADE80",
  },
  successIcon: {
    fontSize: 20,
    color: "#4ADE80",
    fontWeight: "700",
    marginTop: 1,
  },
  successTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#4ADE80",
    marginBottom: 2,
  },
  successText: {
    fontSize: 12,
    color: "#86EFAC",
    lineHeight: 18,
  },

  // Empty state
  emptyState: {
    alignItems: "center",
    paddingVertical: 40,
    gap: 12,
    backgroundColor: "#1E293B",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#334155",
    borderStyle: "dashed",
  },
  emptyIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: "#0F172A",
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

  // Threat card
  threatCard: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#334155",
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: "#FB923C",
  },
  threatHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 10,
  },
  threatTitleGroup: {
    flex: 1,
  },
  threatName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#F1F5F9",
  },
  threatIndustry: {
    fontSize: 12,
    color: "#64748B",
    marginTop: 1,
  },
  threatLevelBadge: {
    backgroundColor: "#7C2D12",
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderWidth: 1,
    borderColor: "#FB923C",
  },
  threatLevelText: {
    fontSize: 9,
    fontWeight: "800",
    color: "#FB923C",
    letterSpacing: 1,
  },
  threatNote: {
    fontSize: 13,
    color: "#94A3B8",
    lineHeight: 20,
  },
});
