import { Tabs } from "expo-router";
import { View } from "react-native";
import {
  LayoutDashboard,
  RadioTower,
  BrainCircuit,
  Swords,
  UserCircle,
} from "lucide-react-native";

/**
 * Main authenticated app layout using file-based tab navigation.
 * Each tab is styled with the deep slate dark theme and neon accent highlights.
 */
export default function AppLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: "#0F172A",
          borderTopColor: "#334155",
          borderTopWidth: 1,
          height: 64,
          paddingBottom: 8,
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
          title: "Dashboard",
          tabBarIcon: ({ color, size }) => (
            <LayoutDashboard color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="signals"
        options={{
          title: "Signals",
          tabBarIcon: ({ color, size }) => (
            <RadioTower color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="predictions"
        options={{
          title: "Predictions",
          tabBarIcon: ({ color, size }) => (
            <BrainCircuit color={color} size={size} />
          ),
        }}
      />
      <Tabs.Screen
        name="warroom"
        options={{
          title: "War Room",
          tabBarIcon: ({ color, size }) => (
            <Swords color={color} size={size} />
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
    </Tabs>
  );
}
