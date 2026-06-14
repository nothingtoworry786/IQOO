import { useEffect } from "react";
import { Stack, router } from "expo-router";
import { useAuth } from "../../contexts/AuthContext";

/**
 * Layout for public auth routes (login, signup).
 * Redirects to the main app if the user is already authenticated.
 */
export default function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/(app)" as never);
    }
  }, [isAuthenticated, isLoading]);

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: "slide_from_right",
        contentStyle: { backgroundColor: "#0B1121" },
      }}
    >
      <Stack.Screen name="login" />
      <Stack.Screen name="signup" />
    </Stack>
  );
}
