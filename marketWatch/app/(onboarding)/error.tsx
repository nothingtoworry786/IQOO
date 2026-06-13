import React from "react";
import {
  Text,
  View,
  ScrollView,
  StyleSheet,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { AlertTriangle } from "lucide-react-native";
import Button from "../../src/components/ui/Button";

export default function ErrorScreen() {
  const insets = useSafeAreaInsets();
  const { error } = useLocalSearchParams<{ error: string }>();

  const handleRestart = () => {
    router.replace("/(onboarding)/profile");
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      <ScrollView
        style={{ flex: 1 }}
        contentContainerStyle={[styles.content, { paddingTop: Math.max(insets.top, 20) + 12 }]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.errorSection}>
          <View style={styles.errorIconWrap}>
            <AlertTriangle size={40} color="#F87171" />
          </View>
          <Text style={styles.errorTitle}>Initialisation Error</Text>
          <Text style={styles.errorDesc}>
            {error ?? "Could not build workspace. Is the API online?"}
          </Text>
          <Button
            variant="secondary"
            text="Restart Setup"
            onPress={handleRestart}
            textStyle={{ color: "#8B5CF6" }}
            style={{ paddingHorizontal: 32 }}
          />
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
  errorSection: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingTop: 80,
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
    fontSize: 22,
    fontWeight: "800",
    color: "#F87171",
    marginBottom: 8,
  },
  errorDesc: {
    fontSize: 14,
    color: "#94A3B8",
    textAlign: "center",
    lineHeight: 22,
    paddingHorizontal: 16,
    marginBottom: 28,
  },
});
