import React, { useEffect } from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CheckCircle } from "lucide-react-native";

export default function CompleteScreen() {
  const insets = useSafeAreaInsets();
  const { competitorsFound, signalsSeeded, competitorsCount, message } = useLocalSearchParams<{
    competitorsFound: string;
    signalsSeeded: string;
    competitorsCount: string;
    message: string;
  }>();

  useEffect(() => {
    const timer = setTimeout(() => {
      router.replace("/(app)" as any);
    }, 1800);
    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={[styles.content, { paddingTop: Math.max(insets.top, 20) + 12 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.completeSection}>
          <View style={styles.completeLogoWrap}>
            <View style={styles.completeRing}>
              <CheckCircle size={48} color="#4ADE80" />
            </View>
          </View>
          <Text style={styles.completeTitle}>War Room Active</Text>
          <Text style={styles.completeDesc}>
            {message ?? "The competitive landscape analysis has completed successfully."}
          </Text>

          <View style={styles.completeStats}>
            <View style={styles.completeStat}>
              <Text style={styles.completeStatValue}>{competitorsFound ?? "0"}</Text>
              <Text style={styles.completeStatLabel}>Competitors</Text>
            </View>
            <View style={styles.completeStat}>
              <Text style={styles.completeStatValue}>{signalsSeeded ?? "0"}</Text>
              <Text style={styles.completeStatLabel}>Signals</Text>
            </View>
            <View style={styles.completeStat}>
              <Text style={styles.completeStatValue}>{competitorsCount ?? "0"}</Text>
              <Text style={styles.completeStatLabel}>Threat levels</Text>
            </View>
          </View>

          <ActivityIndicator size="small" color="#22D3EE" style={{ marginTop: 24 }} />
          <Text style={styles.redirectText}>Opening strategic command room…</Text>
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
  completeSection: {
    flex: 1,
    alignItems: "center",
    paddingTop: 60,
    paddingHorizontal: 24,
  },
  completeLogoWrap: {
    marginBottom: 24,
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
    shadowColor: "#4ADE80",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 6,
  },
  completeTitle: {
    fontSize: 26,
    fontWeight: "800",
    color: "#4ADE80",
    marginBottom: 8,
  },
  completeDesc: {
    fontSize: 14,
    color: "#94A3B8",
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: 16,
    marginBottom: 28,
  },
  completeStats: {
    flexDirection: "row",
    gap: 10,
    width: "100%",
  },
  completeStat: {
    flex: 1,
    backgroundColor: "#0F172A",
    borderRadius: 14,
    padding: 16,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#1E293B",
  },
  completeStatValue: {
    fontSize: 26,
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
    textAlign: "center",
  },
  redirectText: {
    fontSize: 12,
    color: "#475569",
    marginTop: 10,
    fontStyle: "italic",
  },
});
