import React, { useEffect, useRef } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  Animated,
} from "react-native";
import { router } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import {
  Shield,
  Search,
  BrainCircuit,
  Zap,
  ArrowRight,
} from "lucide-react-native";
import Button from "../../src/components/ui/Button";

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

export default function WelcomeScreen() {
  const insets = useSafeAreaInsets();

  const handleBegin = () => {
    router.push("/(onboarding)/profile");
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={[styles.content, { paddingTop: Math.max(insets.top, 20) + 12 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.cardContainer}>
          {/* Hero Section */}
          <View style={styles.heroSection}>
            <View style={styles.logoWrap}>
              <PulseRing />
              <View style={styles.logoInner}>
                <Shield size={28} color="#22D3EE" />
              </View>
            </View>
            <Text style={styles.heroTitle}>MarketWatch</Text>
            <Text style={styles.heroSubtitle}>AI Competitive War Room</Text>
            <Text style={styles.heroDesc}>
              Deploy autonomous intelligence agents to automatically scan your competitors' GTM strategy, product rollouts, and positioning.
            </Text>
          </View>

          {/* Key Features List */}
          <View style={styles.featureList}>
            <View style={styles.featureItem}>
              <View style={styles.featureMiniIcon}>
                <Search size={16} color="#22D3EE" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.featureItemTitle}>Autonomous Intelligence</Text>
                <Text style={styles.featureItemText}>
                  Agents monitor job boards, pricing sheets, marketing ads, and feature releases automatically.
                </Text>
              </View>
            </View>

            <View style={styles.featureItem}>
              <View style={styles.featureMiniIcon}>
                <BrainCircuit size={16} color="#22D3EE" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.featureItemTitle}>Strategic GTM Playbooks</Text>
                <Text style={styles.featureItemText}>
                  Receive actionable alerts and counter-strategies as soon as competitors make market moves.
                </Text>
              </View>
            </View>

            <View style={styles.featureItem}>
              <View style={styles.featureMiniIcon}>
                <Zap size={16} color="#22D3EE" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.featureItemTitle}>Instant Command Center</Text>
                <Text style={styles.featureItemText}>
                  Set up a complete threat-monitoring war room in under 5 minutes with zero configuration.
                </Text>
              </View>
            </View>
          </View>

          {/* Begin Button */}
          <View style={styles.btnRow}>
            <Button
              style={{ flex: 1 }}
              text="Begin Setup"
              onPress={handleBegin}
              icon={<ArrowRight size={18} color="#0F172A" />}
              iconPosition="right"
            />
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
  cardContainer: {
    paddingHorizontal: 24,
    gap: 24,
  },
  heroSection: {
    alignItems: "center",
    paddingTop: 36,
    paddingBottom: 12,
  },
  logoWrap: {
    width: 80,
    height: 80,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 20,
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
  heroTitle: {
    fontSize: 32,
    fontWeight: "900",
    color: "#F8FAFC",
    letterSpacing: -1,
    marginBottom: 4,
  },
  heroSubtitle: {
    fontSize: 13,
    color: "#22D3EE",
    fontWeight: "700",
    letterSpacing: 1.2,
    marginBottom: 16,
    textTransform: "uppercase",
  },
  heroDesc: {
    fontSize: 14,
    color: "#94A3B8",
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: 12,
  },
  featureList: {
    gap: 16,
    backgroundColor: "#0F172A",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1E293B",
    padding: 16,
  },
  featureItem: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
  },
  featureMiniIcon: {
    width: 32,
    height: 32,
    borderRadius: 8,
    backgroundColor: "#164E6330",
    borderColor: "#22D3EE30",
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 2,
  },
  featureItemTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#F1F5F9",
    marginBottom: 2,
  },
  featureItemText: {
    fontSize: 12,
    color: "#64748B",
    lineHeight: 18,
  },
  btnRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 12,
  },
});
