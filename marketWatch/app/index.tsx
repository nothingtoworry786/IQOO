import { useState, useEffect } from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { Redirect } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { api } from "../services/apiClient";

/**
 * Root index — checks if onboarding has been completed by querying the backend.
 * - If competitors exist → redirect to main app (tabs)
 * - If no competitors → redirect to onboarding flow
 * - While checking → show a brief loading splash
 */
export default function RootIndex() {
  const [status, setStatus] = useState<"loading" | "onboarded" | "onboarding">("loading");

  useEffect(() => {
    let mounted = true;

    async function checkOnboarding() {
      try {
        const competitors = await api.competitors.list(1);
        if (mounted) {
          setStatus(competitors.length > 0 ? "onboarded" : "onboarding");
        }
      } catch {
        // Backend unreachable — assume not onboarded and show onboarding
        if (mounted) {
          setStatus("onboarding");
        }
      }
    }

    checkOnboarding();

    return () => {
      mounted = false;
    };
  }, []);

  if (status === "loading") {
    return (
      <View style={styles.container}>
        <StatusBar style="light" />
        <ActivityIndicator size="large" color="#22D3EE" />
        <Text style={styles.loadingText}>INITIALISING…</Text>
      </View>
    );
  }

  if (status === "onboarded") {
    return <Redirect href={"/(app)" as any} />;
  }

  return <Redirect href={"/(onboarding)" as any} />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0B1121",
    gap: 16,
  },
  loadingText: {
    fontSize: 12,
    fontFamily: "Courier New",
    color: "#475569",
    letterSpacing: 1,
  },
});
