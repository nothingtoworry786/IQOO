import { Stack } from "expo-router";

/**
 * Onboarding layout — no tabs, clean stack navigator for the onboarding flow.
 * Contains only the index (main onboarding screen).
 */
export default function OnboardingLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: "fade",
        contentStyle: { backgroundColor: "#0B1121" },
      }}
    >
      <Stack.Screen name="index" />
    </Stack>
  );
}
