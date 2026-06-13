import React from "react";
import { View, Text, Pressable, StyleSheet } from "react-native";
import { ArrowLeft } from "lucide-react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

interface OnboardingHeaderProps {
  currentStep: string;
  onBack: () => void;
}

export default function OnboardingHeader({ currentStep, onBack }: OnboardingHeaderProps) {
  const insets = useSafeAreaInsets();
  const showBackButton = currentStep === "goals" || currentStep === "competitors";
  const showHeader = currentStep === "profile" || showBackButton;

  if (!showHeader) return null;

  return (
    <View style={[hdr.container, { paddingTop: Math.max(insets.top, 20) + 12 }]}>
      <View style={hdr.left}>
        {showBackButton && (
          <Pressable style={hdr.backBtn} onPress={onBack} accessibilityRole="button" accessibilityLabel="Go Back">
            <ArrowLeft size={18} color="#22D3EE" />
          </Pressable>
        )}
      </View>
      <View style={hdr.center}>
        <Text style={hdr.title}>MarketWatch</Text>
      </View>
      <View style={hdr.right}>
        <Text style={hdr.stepText}>
          {currentStep === "profile" && "1/3"}
          {currentStep === "goals" && "2/3"}
          {currentStep === "competitors" && "3/3"}
        </Text>
      </View>
    </View>
  );
}

const hdr = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: "#0F172A",
    borderBottomWidth: 1,
    borderBottomColor: "#1E293B",
  },
  left: {
    width: 60,
    alignItems: "flex-start",
  },
  backBtn: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: "#164E6330",
    borderColor: "#22D3EE30",
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  center: {
    flex: 1,
    alignItems: "center",
  },
  title: {
    fontSize: 14,
    fontWeight: "800",
    color: "#F8FAFC",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  right: {
    width: 60,
    alignItems: "flex-end",
  },
  stepText: {
    fontSize: 11,
    fontWeight: "700",
    color: "#22D3EE",
    backgroundColor: "#164E6330",
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: "#22D3EE30",
  },
});
