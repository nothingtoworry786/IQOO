import { useRef, useCallback, type ReactNode } from "react";
import {
  Pressable,
  View,
  Text,
  Animated,
  StyleSheet,
  type ViewStyle,
  type GestureResponderEvent,
  type StyleProp,
} from "react-native";
import type { CardVariant, CardPriority, CardAction } from "@/types";
import { useResponsive, responsiveValue } from "@/hooks/useResponsive";

// ──────────────────────────────────────────────────────────────
// Colour maps
// ──────────────────────────────────────────────────────────────

const CARD_BG: Record<CardVariant, string> = {
  default: "#1E293B",
  elevated: "#1E293B",
  bordered: "transparent",
  ghost: "transparent",
};

const CARD_BORDER: Record<CardVariant, { width: number; color: string }> = {
  default: { width: 1, color: "#334155" },
  elevated: { width: 1, color: "#334155" },
  bordered: { width: 2, color: "#334155" },
  ghost: { width: 0, color: "transparent" },
};

const PRIORITY_ACCENT: Record<CardPriority, string> = {
  none: "transparent",
  low: "#4ADE80",
  medium: "#FBBF24",
  high: "#FB923C",
  critical: "#F87171",
};

const PRIORITY_BG: Record<CardPriority, string> = {
  none: "transparent",
  low: "#166534",
  medium: "#713F12",
  high: "#7C2D12",
  critical: "#7F1D1D",
};

const PRIORITY_TEXT: Record<CardPriority, string> = {
  none: "#94A3B8",
  low: "#4ADE80",
  medium: "#FBBF24",
  high: "#FB923C",
  critical: "#F87171",
};

const PRIORITY_BADGE_LABEL: Record<CardPriority, string> = {
  none: "",
  low: "LOW",
  medium: "MEDIUM",
  high: "HIGH",
  critical: "CRITICAL",
};

// ──────────────────────────────────────────────────────────────
// Props
// ──────────────────────────────────────────────────────────────

export interface CardProps {
  /** Primary content rendered inside the card body */
  children: ReactNode;
  /** Optional card header title */
  title?: string;
  /** Optional subtitle rendered below the title */
  subtitle?: string;
  /** Optional icon node rendered beside the title */
  icon?: ReactNode;
  /** Visual variant of the card */
  variant?: CardVariant;
  /** Priority level that sets the left accent border and badge */
  priority?: CardPriority;
  /** Optional action rendered at the bottom-right of the card */
  action?: CardAction;
  /** Additional style overrides */
  style?: StyleProp<ViewStyle>;
  /** Optional press handler for the entire card */
  onPress?: () => void;
  /** Optional long-press handler */
  onLongPress?: () => void;
  /** Disables press interactions */
  disabled?: boolean;
}

// ──────────────────────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────────────────────

export default function Card({
  children,
  title,
  subtitle,
  icon,
  variant = "default",
  priority = "none",
  action,
  style,
  onPress,
  onLongPress,
  disabled = false,
}: CardProps) {
  const { isMobile, isTablet } = useResponsive();
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = useCallback(
    (_event: GestureResponderEvent) => {
      Animated.spring(scaleAnim, {
        toValue: 0.97,
        useNativeDriver: true,
        speed: 50,
        bounciness: 4,
      }).start();
    },
    [scaleAnim],
  );

  const handlePressOut = useCallback(
    (_event: GestureResponderEvent) => {
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        speed: 50,
        bounciness: 6,
      }).start();
    },
    [scaleAnim],
  );

  const paddingX = responsiveValue(12, 20, 28)(isMobile, isTablet);
  const paddingY = responsiveValue(14, 18, 22)(isMobile, isTablet);

  const borderColor = CARD_BORDER[variant].color;
  const borderWidth = CARD_BORDER[variant].width;

  const hasTopContent = Boolean(title || subtitle || icon || priority !== "none");
  const hasAction = Boolean(action);

  // ── Card body ──────────────────────────────────────────
  const cardContent = (
    <Animated.View
      style={[
        styles.cardBase,
        {
          backgroundColor: CARD_BG[variant],
          borderColor,
          borderWidth,
          borderLeftColor: priority === "none" ? borderColor : PRIORITY_ACCENT[priority],
          borderLeftWidth: priority === "none" ? borderWidth : 4,
          transform: [{ scale: scaleAnim }],
        },
        style,
      ]}
    >
      {/* Shadow overlay for elevated variant */}
      {variant === "elevated" && (
        <View
          style={[
            StyleSheet.absoluteFill,
            { borderRadius: 16, backgroundColor: "rgba(0,0,0,0.2)" },
          ]}
          pointerEvents="none"
        />
      )}

      {/* ── Header ──────────────────────────────────────── */}
      {hasTopContent && (
        <View
          style={{
            paddingHorizontal: paddingX,
            paddingTop: paddingY,
            paddingBottom: 0,
          }}
        >
          <View style={styles.headerRow}>
            <View style={styles.headerContent}>
              {/* Icon + Title */}
              {(icon || title) && (
                <View style={styles.titleRow}>
                  {icon && <View style={styles.iconWrapper}>{icon}</View>}
                  {title && (
                    <Text style={styles.titleText}>{title}</Text>
                  )}
                </View>
              )}

              {/* Subtitle */}
              {subtitle && (
                <Text style={styles.subtitleText}>{subtitle}</Text>
              )}
            </View>

            {/* Priority badge */}
            {priority !== "none" && (
              <View
                style={[
                  styles.priorityBadge,
                  { backgroundColor: PRIORITY_BG[priority] },
                ]}
              >
                <Text
                  style={[
                    styles.priorityBadgeText,
                    { color: PRIORITY_TEXT[priority] },
                  ]}
                >
                  {PRIORITY_BADGE_LABEL[priority]}
                </Text>
              </View>
            )}
          </View>
        </View>
      )}

      {/* ── Body ─────────────────────────────────────────── */}
      <View
        style={{
          paddingHorizontal: paddingX,
          paddingTop: hasTopContent ? 12 : paddingY,
          paddingBottom: hasAction ? 8 : paddingY,
        }}
      >
        {children}
      </View>

      {/* ── Action footer ────────────────────────────────── */}
      {hasAction && (
        <View
          style={{
            paddingHorizontal: paddingX,
            paddingBottom: paddingY,
          }}
        >
          <Pressable
            onPress={action!.onPress}
            disabled={disabled}
            hitSlop={8}
          >
            {({ pressed }) => (
              <View
                style={[
                  styles.actionButton,
                  pressed && styles.actionButtonPressed,
                ]}
              >
                <Text style={styles.actionButtonText}>
                  {action!.label}
                </Text>
              </View>
            )}
          </Pressable>
        </View>
      )}
    </Animated.View>
  );

  // ── Interactive wrapper ──────────────────────────────────
  if (onPress || onLongPress) {
    return (
      <Pressable
        onPress={onPress}
        onLongPress={onLongPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled}
        accessibilityRole="button"
        accessibilityState={{ disabled }}
      >
        {cardContent}
      </Pressable>
    );
  }

  return cardContent;
}

// ──────────────────────────────────────────────────────────────
// Styles
// ──────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  cardBase: {
    borderRadius: 16,
    overflow: "hidden",
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
  },
  headerContent: {
    flex: 1,
    paddingRight: 12,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  iconWrapper: {
    flexShrink: 0,
  },
  titleText: {
    flex: 1,
    fontSize: 16,
    fontWeight: "600",
    color: "#F1F5F9",
  },
  subtitleText: {
    marginTop: 4,
    fontSize: 14,
    lineHeight: 20,
    color: "#94A3B8",
  },
  priorityBadge: {
    flexShrink: 0,
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 2,
  },
  priorityBadgeText: {
    fontSize: 10,
    fontWeight: "700",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  actionButton: {
    alignSelf: "flex-end",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#334155",
    backgroundColor: "#1E293B",
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  actionButtonPressed: {
    backgroundColor: "#2A3A54",
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#22D3EE",
  },
});
