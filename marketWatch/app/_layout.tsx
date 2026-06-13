import { useEffect, useState } from "react";
import { View, Text, StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";
import { Stack } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { PersonaProvider } from "../store/personaStore";
import AnimatedSplashScreen from "../src/components/AnimatedSplashScreen";

/**
 * Root layout component that wraps the entire application with:
 * - SafeAreaProvider for safe area insets
 * - GestureHandlerRootView for gesture-based interactions
 * - PersonaProvider — global persona/lens context (Founder | Marketing)
 * - Dark mode color scheme
 * - Splash screen / initial loading state
 * - Status bar configuration
 */
export default function RootLayout() {
  const [isReady, setIsReady] = useState(false);

  if (!isReady) {
    return (
      <SafeAreaProvider>
        <GestureHandlerRootView style={styles.root}>
          <AnimatedSplashScreen onFinish={() => setIsReady(true)} />
        </GestureHandlerRootView>
      </SafeAreaProvider>
    );
  }


  return (
    <SafeAreaProvider>
      <GestureHandlerRootView style={styles.root}>
        <PersonaProvider>
          <StatusBar style="light" />
          <Stack
            screenOptions={{
              headerShown: false,
              animation: "slide_from_right",
              contentStyle: { backgroundColor: "#0F172A" },
            }}
          >
            <Stack.Screen name="index" />
            <Stack.Screen name="(onboarding)" />
            <Stack.Screen name="(auth)" />
            <Stack.Screen name="(app)" />
          </Stack>
        </PersonaProvider>
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
  splashContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0F172A",
  },
  splashText: {
    marginTop: 16,
    fontSize: 12,
    fontFamily: "Courier New",
    color: "#94A3B8",
  },
});
