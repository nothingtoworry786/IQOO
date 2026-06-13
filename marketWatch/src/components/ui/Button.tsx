import React, { useState } from "react";
import {
  Pressable,
  Text,
  StyleSheet,
  type StyleProp,
  type ViewStyle,
  type TextStyle,
  View,
} from "react-native";

interface ButtonProps {
  text: string;
  onPress: () => void;
  variant?: "primary" | "secondary" | "outline";
  icon?: React.ReactNode;
  iconPosition?: "left" | "right";
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}

export default function Button({
  text,
  onPress,
  variant = "primary",
  icon,
  iconPosition = "left",
  disabled = false,
  style,
  textStyle,
}: ButtonProps) {
  const [isPressed, setIsPressed] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const getContainerStyle = () => {
    if (disabled) {
      if (variant === "outline") {
        return [styles.disabledContainer, styles.disabledOutlineBorder];
      }
      return styles.disabledContainer;
    }
    switch (variant) {
      case "outline":
        if (isPressed) return styles.outlinePressed;
        if (isHovered) return styles.outlineHovered;
        return styles.outlineContainer;
      case "secondary":
        if (isPressed) return styles.secondaryPressed;
        if (isHovered) return styles.secondaryHovered;
        return styles.secondaryContainer;
      case "primary":
      default:
        if (isPressed) return styles.primaryPressed;
        if (isHovered) return styles.primaryHovered;
        return styles.primaryContainer;
    }
  };

  const getTextStyle = () => {
    if (disabled) {
      return styles.disabledText;
    }
    switch (variant) {
      case "outline":
        if (isPressed) return styles.outlineTextPressed;
        if (isHovered) return styles.outlineTextHovered;
        return styles.outlineText;
      case "secondary":
        if (isPressed) return styles.secondaryTextPressed;
        if (isHovered) return styles.secondaryTextHovered;
        return styles.secondaryText;
      case "primary":
      default:
        if (isPressed) return styles.primaryTextPressed;
        if (isHovered) return styles.primaryTextHovered;
        return styles.primaryText;
    }
  };

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      onPressIn={() => setIsPressed(true)}
      onPressOut={() => setIsPressed(false)}
      onHoverIn={() => setIsHovered(true)}
      onHoverOut={() => setIsHovered(false)}
      style={[
        styles.btnBase,
        getContainerStyle(),
        style,
      ]}
      accessibilityRole="button"
      accessibilityState={{ disabled }}
    >
      <View style={styles.contentRow}>
        {icon && iconPosition === "left" && <View style={styles.iconWrap}>{icon}</View>}
        <Text style={[styles.textBase, getTextStyle(), textStyle]}>{text}</Text>
        {icon && iconPosition === "right" && <View style={styles.iconWrap}>{icon}</View>}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  btnBase: {
    borderRadius: 12,
    paddingVertical: 15,
    paddingHorizontal: 20,
    alignItems: "center",
    justifyContent: "center",
    flexDirection: "row",
  },
  contentRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  iconWrap: {
    justifyContent: "center",
    alignItems: "center",
  },
  textBase: {
    fontSize: 15,
    fontWeight: "700",
  },
  
  // Primary variant
  primaryContainer: {
    backgroundColor: "#22D3EE",
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  primaryHovered: {
    backgroundColor: "#67E8F9",
    shadowColor: "#22D3EE",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 6,
  },
  primaryPressed: {
    backgroundColor: "#0891B2",
    elevation: 2,
    shadowOpacity: 0.15,
  },
  primaryText: {
    color: "#0F172A",
  },
  primaryTextHovered: {
    color: "#0F172A",
  },
  primaryTextPressed: {
    color: "#0F172A",
  },

  // Secondary variant
  secondaryContainer: {
    backgroundColor: "#1E293B",
    borderWidth: 1,
    borderColor: "#334155",
  },
  secondaryHovered: {
    backgroundColor: "#334155",
    borderWidth: 1,
    borderColor: "#475569",
  },
  secondaryPressed: {
    backgroundColor: "#0F172A",
    borderWidth: 1,
    borderColor: "#1E293B",
  },
  secondaryText: {
    color: "#F1F5F9",
  },
  secondaryTextHovered: {
    color: "#F8FAFC",
  },
  secondaryTextPressed: {
    color: "#94A3B8",
  },

  // Outline variant
  outlineContainer: {
    backgroundColor: "transparent",
    borderWidth: 1,
    borderColor: "#22D3EE",
  },
  outlineHovered: {
    backgroundColor: "#22D3EE14",
    borderWidth: 1,
    borderColor: "#67E8F9",
  },
  outlinePressed: {
    backgroundColor: "#22D3EE33",
    borderWidth: 1,
    borderColor: "#0891B2",
  },
  outlineText: {
    color: "#22D3EE",
  },
  outlineTextHovered: {
    color: "#67E8F9",
  },
  outlineTextPressed: {
    color: "#0891B2",
  },

  // Disabled state
  disabledContainer: {
    backgroundColor: "#1E293B",
    elevation: 0,
    shadowOpacity: 0,
    opacity: 0.6,
  },
  disabledOutlineBorder: {
    borderWidth: 1,
    borderColor: "#334155",
  },
  disabledText: {
    color: "#475569",
  },
});
