import React from "react";
import { View, StyleSheet } from "react-native";

interface StepIndicatorProps {
  currentStep: number;
  totalSteps: number;
}

export default function StepIndicator({ currentStep, totalSteps }: StepIndicatorProps) {
  return (
    <View style={ind.container}>
      {Array.from({ length: totalSteps }).map((_, i) => {
        const isCompleted = i < currentStep;
        const isActive = i === currentStep;
        return (
          <View key={i} style={ind.stepContainer}>
            <View
              style={[
                ind.bar,
                isCompleted && ind.barCompleted,
                isActive && ind.barActive,
              ]}
            />
          </View>
        );
      })}
    </View>
  );
}

const ind = StyleSheet.create({
  container: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 24,
    paddingVertical: 16,
    width: "100%",
  },
  stepContainer: {
    flex: 1,
  },
  bar: {
    height: 4,
    backgroundColor: "#1E293B",
    borderRadius: 2,
  },
  barActive: {
    backgroundColor: "#22D3EE",
  },
  barCompleted: {
    backgroundColor: "#22D3EEaa",
  },
});
