import { Tabs } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { LayoutDashboard, Users, MessageCircle, UserCircle } from "lucide-react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function AppLayout() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 64 + insets.bottom;

  return (
    <>
      <StatusBar style="light" />
      <Tabs
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: "#0F172A",
            borderTopColor: "#334155",
            borderTopWidth: 1,
            height: tabBarHeight,
            paddingBottom: insets.bottom + 8,
            paddingTop: 6,
          },
          tabBarActiveTintColor: "#22D3EE",
          tabBarInactiveTintColor: "#64748B",
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: "600",
            letterSpacing: 0.5,
          },
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Home",
            tabBarIcon: ({ color, size }) => (
              <LayoutDashboard color={color} size={size} />
            ),
          }}
        />
        <Tabs.Screen
          name="competitors"
          options={{
            title: "Competitors",
            tabBarIcon: ({ color, size }) => (
              <Users color={color} size={size} />
            ),
          }}
        />
        <Tabs.Screen
          name="chatbot"
          options={{
            title: "Chatbot",
            tabBarIcon: ({ color, size }) => (
              <MessageCircle color={color} size={size} />
            ),
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{
            title: "Profile",
            tabBarIcon: ({ color, size }) => (
              <UserCircle color={color} size={size} />
            ),
          }}
        />
        {/* Screens accessible via navigation but not shown in tab bar */}
        <Tabs.Screen name="signals" options={{ href: null }} />
        <Tabs.Screen name="predictions" options={{ href: null }} />
        <Tabs.Screen name="warroom" options={{ href: null }} />
      </Tabs>
    </>
  );
}
