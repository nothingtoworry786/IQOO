import { Stack } from "expo-router";

/**
 * Layout for public (auth) routes — login, registration, forgot password.
 * Uses a simple stack navigator with no header.
 */
export default function AuthLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: "slide_from_right",
        contentStyle: { backgroundColor: "#0F172A" },
      }}
    >
      <Stack.Screen name="login" />
    </Stack>
  );
}
