import { useState } from "react";
import { StyleSheet } from "react-native";
import { StatusBar } from "expo-status-bar";
import { Stack } from "expo-router";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AuthProvider } from "../contexts/AuthContext";
import AnimatedSplashScreen from "../src/components/AnimatedSplashScreen";

/**
 * Root layout — wraps the entire app with:
 *  - SafeAreaProvider and GestureHandlerRootView
 *  - AuthProvider (mounts immediately so token check runs during splash)
 *  - AnimatedSplashScreen shown until onFinish fires (≈3.2 s)
 */
export default function RootLayout() {
  const [splashDone, setSplashDone] = useState(false);

  return (
    <SafeAreaProvider>
      <GestureHandlerRootView style={styles.root}>
        <AuthProvider>
          {!splashDone ? (
            <AnimatedSplashScreen onFinish={() => setSplashDone(true)} />
          ) : (
            <>
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
            </>
          )}
        </AuthProvider>
      </GestureHandlerRootView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#0F172A",
  },
});
