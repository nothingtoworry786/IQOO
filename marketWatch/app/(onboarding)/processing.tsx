import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  Animated,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  Search,
  Shield,
  RadioTower,
  BrainCircuit,
  CheckCircle,
  Sparkles,
} from "lucide-react-native";
import { api } from "../../services/apiClient";
import { setItem } from "../../services/storage";

interface AgentStep {
  label: string;
  icon: any;
  color: string;
  duration: number;
}

const AGENT_STEPS: AgentStep[] = [
  { label: "Identifying competitors in your domain…", icon: Search, color: "#22D3EE", duration: 1200 },
  { label: "Analyzing GTM strategy & positioning…", icon: Shield, color: "#A78BFA", duration: 1000 },
  { label: "Seeding intelligence signals…", icon: RadioTower, color: "#FB923C", duration: 900 },
  { label: "Generating strategic predictions…", icon: BrainCircuit, color: "#4ADE80", duration: 800 },
  { label: "Configuring your War Room dashboard…", icon: Sparkles, color: "#22D3EE", duration: 600 },
];

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
  const slideAnim = useRef(new Animated.Value(15)).current;

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
      style={[stepRowStyle.container, { opacity, transform: [{ translateY: slideAnim }] }]}
    >
      <View style={[stepRowStyle.iconWrap, {
        backgroundColor: isDone ? "#052E16" : isActive ? "#164E63" : "#1E293B",
        borderColor: isDone ? "#4ADE80" : isActive ? "#22D3EE" : "#334155",
      }]}>
        {isDone ? (
          <CheckCircle size={18} color="#4ADE80" />
        ) : (
          <Icon size={16} color={isActive ? step.color : "#475569"} />
        )}
      </View>
      <Text style={[stepRowStyle.label, {
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

const stepRowStyle = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingVertical: 12,
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

export default function ProcessingScreen() {
  const insets = useSafeAreaInsets();
  const { companyName, websiteUrl } = useLocalSearchParams<{ companyName: string; websiteUrl: string }>();
  const [activeStep, setActiveStep] = useState(-1);

  const runAgentSteps = useCallback(async () => {
    for (let i = 0; i < AGENT_STEPS.length; i++) {
      setActiveStep(i);
      await new Promise((resolve) => setTimeout(resolve, AGENT_STEPS[i].duration));
    }
    setActiveStep(AGENT_STEPS.length);
  }, []);

  useEffect(() => {
    let active = true;

    async function executeDiscovery() {
      if (!companyName || !websiteUrl) {
        router.replace("/(onboarding)/profile");
        return;
      }

      try {
        const [discoverResult] = await Promise.all([
          api.competitors.discover({
            company_name: companyName,
            website_url: websiteUrl,
          }),
          runAgentSteps(),
        ]);

        if (active) {
          // Cache company name so Profile screen can display it
          await setItem("cache_company_name", companyName);
          router.replace({
            pathname: "/(onboarding)/complete",
            params: {
              competitorsFound: discoverResult.competitors_found,
              signalsSeeded: discoverResult.signals_seeded,
              competitorsCount: discoverResult.competitors.length,
              message: discoverResult.message ?? "",
            },
          });
        }
      } catch (err: any) {
        if (active) {
          router.replace({
            pathname: "/(onboarding)/error",
            params: {
              error: err?.message ?? "Could not build workspace. Is the API online?",
            },
          });
        }
      }
    }

    executeDiscovery();

    return () => {
      active = false;
    };
  }, [companyName, websiteUrl, runAgentSteps]);

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={[styles.content, { paddingTop: Math.max(insets.top, 20) + 12 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.processingSection}>
          <View style={styles.processingHeader}>
            <View style={styles.processingLogoWrap}>
              <PulseRing />
              <View style={styles.logoInner}>
                <Shield size={28} color="#22D3EE" />
              </View>
            </View>
            <Text style={styles.processingTitle}>Deploying Intelligence Agents</Text>
            <Text style={styles.processingDesc}>
              Scanning repositories, financial announcements, pricing API calls, and marketing copy for your business vertical…
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
              Deploying {Math.min(activeStep + 2, AGENT_STEPS.length)} / {AGENT_STEPS.length}
            </Text>
          </View>
        </View>
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0B1121",
  },
  content: {
    paddingBottom: 40,
  },
  processingSection: {
    flex: 1,
    paddingTop: 40,
    paddingHorizontal: 24,
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
    position: "relative",
  },
  logoInner: {
    width: 60,
    height: 60,
    borderRadius: 18,
    backgroundColor: "#164E63",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#22D3EE",
  },
  processingTitle: {
    fontSize: 22,
    fontWeight: "800",
    color: "#F8FAFC",
    marginBottom: 8,
  },
  processingDesc: {
    fontSize: 13,
    color: "#64748B",
    textAlign: "center",
    lineHeight: 20,
    paddingHorizontal: 16,
  },
  stepsContainer: {
    backgroundColor: "#0F172A",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1E293B",
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
    fontWeight: "700",
    color: "#64748B",
    minWidth: 90,
    textAlign: "right",
  },
});
