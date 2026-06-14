import { useState, useEffect } from "react";
import { View, Text, ActivityIndicator, StyleSheet } from "react-native";
import { Redirect } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { api } from "../services/apiClient";

export default function RootIndex() {
  const [status, setStatus] = useState<"loading" | "onboarded" | "onboarding">("loading");

  useEffect(() => {
    let mounted = true;
    api.competitors
      .list(1)
      .then((competitors) => {
        if (mounted) setStatus(competitors.length > 0 ? "onboarded" : "onboarding");
      })
      .catch(() => {
        if (mounted) setStatus("onboarding");
      });
    return () => { mounted = false; };
  }, []);

  if (status === "loading") {
    return (
      <View style={styles.container}>
        <StatusBar style="light" />
        <ActivityIndicator size="large" color="#8B5CF6" />
        <Text style={styles.loadingText}>INITIALISING…</Text>
      </View>
    );
  }

  if (status === "onboarded") {
    return <Redirect href={"/(app)" as never} />;
  }

  return <Redirect href={"/(onboarding)" as never} />;
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
