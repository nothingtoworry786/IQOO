import { useState, useEffect, useRef, useCallback } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  TextInput,
  Pressable,
  ActivityIndicator,
  Animated,
} from "react-native";
import { router } from "expo-router";
import { StatusBar } from "expo-status-bar";
import {
  Zap,
  Search,
  Shield,
  RadioTower,
  BrainCircuit,
  CheckCircle,
  AlertTriangle,
  Users,
  Sparkles,
} from "lucide-react-native";
import { api } from "../../services/apiClient";

// ─────────────────────────────────────────────────────────────────────────────
// Agent Step Config
// ─────────────────────────────────────────────────────────────────────────────

interface AgentStep {
  label: string;
  icon: any;
  color: string;
  duration: number; // ms to simulate
}

const AGENT_STEPS: AgentStep[] = [
  { label: "Identifying competitors in your market…", icon: Search, color: "#22D3EE", duration: 1200 },
  { label: "Analyzing competitive landscape…", icon: Shield, color: "#A78BFA", duration: 1000 },
  { label: "Seeding intelligence signals…", icon: RadioTower, color: "#FB923C", duration: 900 },
  { label: "Generating strategic predictions…", icon: BrainCircuit, color: "#4ADE80", duration: 800 },
  { label: "Initialising your War Room…", icon: Sparkles, color: "#22D3EE", duration: 600 },
];

// ─────────────────────────────────────────────────────────────────────────────
// StepRow Component
// ─────────────────────────────────────────────────────────────────────────────

function StepRow({
  step,
  index,
  activeStep,
  completed,
}: {
  step: AgentStep;
  index: number;
  activeStep: number;
  completed: boolean;
}) {
  const opacity = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  const isActive = index === activeStep;
  const isDone = index < activeStep || completed;

  useEffect(() => {
    if (isActive || isDone) {
      Animated.parallel([
        Animated.timing(opacity, { toValue: 1, duration: 400, useNativeDriver: true }),
        Animated.timing(slideAnim, { toValue: 0, duration: 400, useNativeDriver: true }),
      ]).start();
    }
  }, [isActive, isDone]);

  const Icon = step.icon;

  return (
    <Animated.View
      style={[stepRow.container, { opacity, transform: [{ translateY: slideAnim }] }]}
    >
      <View style={[stepRow.iconWrap, {
        backgroundColor: isDone ? "#052E16" : isActive ? "#164E63" : "#1E293B",
        borderColor: isDone ? "#4ADE80" : isActive ? "#22D3EE" : "#334155",
      }]}>
        {isDone ? (
          <CheckCircle size={18} color="#4ADE80" />
        ) : (
          <Icon size={16} color={isActive ? step.color : "#475569"} />
        )}
      </View>
      <Text style={[stepRow.label, {
        color: isDone ? "#4ADE80" : isActive ? "#F1F5F9" : "#475569",
      }]}>
        {step.label}
      </Text>
      {isActive && !completed && (
        <ActivityIndicator size="small" color={step.color} />
      )}
    </Animated.View>
  );
}

const stepRow = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  iconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  label: {
    flex: 1,
    fontSize: 13,
    fontWeight: "600",
    letterSpacing: 0.2,
  },
});

// ─────────────────────────────────────────────────────────────────────────────
// Animated Pulse Ring
// ─────────────────────────────────────────────────────────────────────────────

function PulseRing() {
  const scale = useRef(new Animated.Value(1)).current;
  const opacity = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.parallel([
          Animated.timing(scale, {
            toValue: 1.5,
            duration: 1500,
            useNativeDriver: true,
          }),
          Animated.timing(opacity, {
            toValue: 0,
            duration: 1500,
            useNativeDriver: true,
          }),
        ]),
        Animated.timing(scale, { toValue: 1, duration: 0, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.4, duration: 0, useNativeDriver: true }),
      ]),
    ).start();
  }, []);

  return (
    <Animated.View
      style={{
        position: "absolute",
        width: 80,
        height: 80,
        borderRadius: 40,
        borderWidth: 2,
        borderColor: "#22D3EE",
        opacity,
        transform: [{ scale }],
      }}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Onboarding Screen
// ─────────────────────────────────────────────────────────────────────────────

type OnboardingPhase = "welcome" | "processing" | "complete" | "error";

export default function OnboardingScreen() {
  const [companyName, setCompanyName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [phase, setPhase] = useState<OnboardingPhase>("welcome");
  const [activeStep, setActiveStep] = useState(-1);
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState<any>(null);

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(30)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 800, useNativeDriver: true }),
      Animated.timing(slideAnim, { toValue: 0, duration: 600, useNativeDriver: true }),
    ]).start();
  }, []);

  // Redirect to dashboard when complete
  useEffect(() => {
    if (phase === "complete" && result) {
      const timer = setTimeout(() => {
        router.replace("/(app)" as any);
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [phase, result]);

  // Run agent steps
  const runAgentSteps = useCallback(async () => {
    for (let i = 0; i < AGENT_STEPS.length; i++) {
      setActiveStep(i);
      await new Promise((resolve) => setTimeout(resolve, AGENT_STEPS[i].duration));
    }
    setActiveStep(AGENT_STEPS.length - 1);
  }, []);

  const handleStart = useCallback(async () => {
    if (!companyName.trim() || !websiteUrl.trim()) return;

    setPhase("processing");
    setErrorMessage("");

    try {
      // Run agent steps in parallel with the actual API call
      const [discoverResult] = await Promise.all([
        api.competitors.discover({
          company_name: companyName.trim(),
          website_url: websiteUrl.trim(),
        }),
        runAgentSteps(),
      ]);

      setResult(discoverResult);
      setPhase("complete");
    } catch (err: any) {
      setErrorMessage(err?.message ?? "Failed to connect to the backend. Is the server running?");
      setPhase("error");
    }
  }, [companyName, websiteUrl, runAgentSteps]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <StatusBar style="light" />

      {/* ── Welcome Phase ──────────────────────────────────────────────── */}
      {phase === "welcome" && (
        <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
          {/* Hero */}
          <View style={styles.heroSection}>
            <View style={styles.logoWrap}>
              <PulseRing />
              <View style={styles.logoInner}>
                <Shield size={28} color="#22D3EE" />
              </View>
            </View>
            <Text style={styles.heroTitle}>MarketWatch</Text>
            <Text style={styles.heroSubtitle}>Competitive Intelligence War Room</Text>
            <Text style={styles.heroDesc}>
              Track competitors, detect market signals, get AI-powered predictions — all in one place.
            </Text>
          </View>

          {/* Feature highlights */}
          <View style={styles.featureRow}>
            {[
              { icon: RadioTower, label: "Signal Detection", color: "#FB923C" },
              { icon: BrainCircuit, label: "Predictions", color: "#A78BFA" },
              { icon: Users, label: "Competitor Tracking", color: "#22D3EE" },
            ].map((f, i) => (
              <View key={i} style={styles.featureCard}>
                <View style={[styles.featureIcon, { backgroundColor: f.color + "15", borderColor: f.color + "40" }]}>
                  <f.icon size={18} color={f.color} />
                </View>
                <Text style={styles.featureLabel}>{f.label}</Text>
              </View>
            ))}
          </View>

          {/* Form */}
          <View style={styles.formSection}>
            <Text style={styles.formTitle}>Set Up Your War Room</Text>
            <Text style={styles.formDesc}>
              Enter your company details to discover competitors and seed intelligence data.
            </Text>

            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Company Name</Text>
              <View style={styles.inputWrap}>
                <Text style={styles.inputPrefix}>🏢</Text>
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
                  onSubmitEditing={handleStart}
                />
              </View>
            </View>

            <Pressable
              style={[
                styles.startBtn,
                (!companyName.trim() || !websiteUrl.trim()) && styles.startBtnDisabled,
              ]}
              onPress={handleStart}
              disabled={!companyName.trim() || !websiteUrl.trim()}
            >
              <Zap size={18} color={!companyName.trim() || !websiteUrl.trim() ? "#475569" : "#0F172A"} />
              <Text style={[
                styles.startBtnText,
                (!companyName.trim() || !websiteUrl.trim()) && styles.startBtnTextDisabled,
              ]}>
                Initialise War Room
              </Text>
            </Pressable>
          </View>
        </Animated.View>
      )}

      {/* ── Processing Phase ────────────────────────────────────────────── */}
      {phase === "processing" && (
        <View style={styles.processingSection}>
          <View style={styles.processingHeader}>
            <View style={styles.processingLogoWrap}>
              <PulseRing />
              <View style={styles.logoInner}>
                <ActivityIndicator size="large" color="#22D3EE" />
              </View>
            </View>
            <Text style={styles.processingTitle}>Deploying Intelligence Agents</Text>
            <Text style={styles.processingDesc}>
              Scanning markets, analyzing signals, and building your competitive landscape…
            </Text>
          </View>

          <View style={styles.stepsContainer}>
            {AGENT_STEPS.map((step, i) => (
              <StepRow
                key={i}
                step={step}
                index={i}
                activeStep={activeStep}
                completed={false}
              />
            ))}
          </View>

          <View style={styles.processingFooter}>
            <View style={styles.progressTrack}>
              <View
                style={[
                  styles.progressFill,
                  { width: `${((activeStep + 1) / AGENT_STEPS.length) * 100}%` },
                ]}
              />
            </View>
            <Text style={styles.progressText}>
              Agent {Math.min(activeStep + 2, AGENT_STEPS.length)} of {AGENT_STEPS.length}
            </Text>
          </View>
        </View>
      )}

      {/* ── Complete Phase ──────────────────────────────────────────────── */}
      {phase === "complete" && result && (
        <View style={styles.completeSection}>
          <View style={styles.completeLogoWrap}>
            <View style={styles.completeRing}>
              <CheckCircle size={48} color="#4ADE80" />
            </View>
          </View>
          <Text style={styles.completeTitle}>War Room Ready</Text>
          <Text style={styles.completeDesc}>
            {result.message ?? "Your competitive intelligence dashboard is ready."}
          </Text>

          <View style={styles.completeStats}>
            <View style={styles.completeStat}>
              <Text style={styles.completeStatValue}>{result.competitors_found}</Text>
              <Text style={styles.completeStatLabel}>Competitors</Text>
            </View>
            <View style={styles.completeStat}>
              <Text style={styles.completeStatValue}>{result.signals_seeded}</Text>
              <Text style={styles.completeStatLabel}>Signals</Text>
            </View>
            <View style={styles.completeStat}>
              <Text style={styles.completeStatValue}>{result.competitors.length}</Text>
              <Text style={styles.completeStatLabel}>Threats</Text>
            </View>
          </View>

          <ActivityIndicator size="small" color="#22D3EE" style={{ marginTop: 20 }} />
          <Text style={styles.redirectText}>Entering War Room…</Text>
        </View>
      )}

      {/* ── Error Phase ────────────────────────────────────────────────── */}
      {phase === "error" && (
        <View style={styles.errorSection}>
          <View style={styles.errorIconWrap}>
            <AlertTriangle size={40} color="#F87171" />
          </View>
          <Text style={styles.errorTitle}>Connection Failed</Text>
          <Text style={styles.errorDesc}>{errorMessage}</Text>
          <Pressable
            style={styles.retryBtn}
            onPress={() => setPhase("welcome")}
          >
            <Text style={styles.retryBtnText}>Try Again</Text>
          </Pressable>
        </View>
      )}

      <View style={{ height: 40 }} />
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

  // Welcome
  heroSection: {
    alignItems: "center",
    paddingTop: 60,
    paddingHorizontal: 24,
    paddingBottom: 24,
  },
  logoWrap: {
    width: 80,
    height: 80,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
  },
  logoInner: {
    width: 60,
    height: 60,
    borderRadius: 16,
    backgroundColor: "#164E63",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#22D3EE55",
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: "900",
    color: "#F8FAFC",
    letterSpacing: -1,
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 14,
    color: "#22D3EE",
    fontWeight: "600",
    letterSpacing: 0.8,
    marginBottom: 12,
    textTransform: "uppercase",
  },
  heroDesc: {
    fontSize: 14,
    color: "#64748B",
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: 20,
  },

  // Features
  featureRow: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 24,
    marginBottom: 28,
  },
  featureCard: {
    flex: 1,
    backgroundColor: "#1E293B",
    borderRadius: 14,
    padding: 14,
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderColor: "#334155",
  },
  featureIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
  },
  featureLabel: {
    fontSize: 10,
    fontWeight: "700",
    color: "#94A3B8",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    textAlign: "center",
  },

  // Form
  formSection: {
    paddingHorizontal: 24,
    gap: 12,
  },
  formTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#F1F5F9",
    marginBottom: 4,
  },
  formDesc: {
    fontSize: 13,
    color: "#64748B",
    lineHeight: 20,
    marginBottom: 4,
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
    backgroundColor: "#1E293B",
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
    paddingVertical: 14,
    fontSize: 14,
    color: "#F1F5F9",
  },
  startBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#22D3EE",
    borderRadius: 14,
    paddingVertical: 16,
    marginTop: 8,
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 6,
  },
  startBtnDisabled: {
    backgroundColor: "#1E293B",
    borderWidth: 1,
    borderColor: "#334155",
    shadowOpacity: 0,
    elevation: 0,
  },
  startBtnText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0F172A",
    letterSpacing: 0.3,
  },
  startBtnTextDisabled: {
    color: "#475569",
  },

  // Processing
  processingSection: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 20,
  },
  processingHeader: {
    alignItems: "center",
    marginBottom: 32,
  },
  processingLogoWrap: {
    width: 80,
    height: 80,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 16,
  },
  processingTitle: {
    fontSize: 20,
    fontWeight: "800",
    color: "#F8FAFC",
    marginBottom: 8,
  },
  processingDesc: {
    fontSize: 13,
    color: "#64748B",
    textAlign: "center",
    lineHeight: 20,
    paddingHorizontal: 20,
  },
  stepsContainer: {
    backgroundColor: "#1E293B",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#334155",
    paddingVertical: 8,
    marginBottom: 24,
  },
  processingFooter: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  progressTrack: {
    flex: 1,
    height: 4,
    backgroundColor: "#1E293B",
    borderRadius: 2,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    backgroundColor: "#22D3EE",
    borderRadius: 2,
  },
  progressText: {
    fontSize: 11,
    fontWeight: "600",
    color: "#64748B",
    minWidth: 60,
    textAlign: "right",
  },

  // Complete
  completeSection: {
    flex: 1,
    alignItems: "center",
    paddingTop: 80,
    paddingHorizontal: 24,
  },
  completeLogoWrap: {
    marginBottom: 20,
  },
  completeRing: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: "#052E16",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#4ADE80",
  },
  completeTitle: {
    fontSize: 24,
    fontWeight: "800",
    color: "#4ADE80",
    marginBottom: 8,
  },
  completeDesc: {
    fontSize: 14,
    color: "#94A3B8",
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  completeStats: {
    flexDirection: "row",
    gap: 12,
  },
  completeStat: {
    backgroundColor: "#1E293B",
    borderRadius: 14,
    padding: 16,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#334155",
    minWidth: 90,
  },
  completeStatValue: {
    fontSize: 24,
    fontWeight: "800",
    color: "#22D3EE",
  },
  completeStatLabel: {
    fontSize: 9,
    fontWeight: "700",
    color: "#475569",
    letterSpacing: 0.8,
    textTransform: "uppercase",
    marginTop: 4,
  },
  redirectText: {
    fontSize: 12,
    color: "#475569",
    marginTop: 8,
    fontStyle: "italic",
  },

  // Error
  errorSection: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingTop: 120,
    paddingHorizontal: 24,
  },
  errorIconWrap: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "#450A0A",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "#F87171",
    marginBottom: 20,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: "#F87171",
    marginBottom: 8,
  },
  errorDesc: {
    fontSize: 14,
    color: "#94A3B8",
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: 20,
    marginBottom: 24,
  },
  retryBtn: {
    paddingHorizontal: 32,
    paddingVertical: 14,
    backgroundColor: "#1E293B",
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#334155",
  },
  retryBtnText: {
    fontSize: 15,
    fontWeight: "600",
    color: "#22D3EE",
  },
});
