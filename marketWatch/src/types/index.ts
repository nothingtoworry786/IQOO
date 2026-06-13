/** Priority levels for alerts and signals */
export type PriorityLevel = "low" | "medium" | "high" | "critical";

/** Alignment positions for card headers */
export type Alignment = "left" | "center" | "right";

/** Signal type classification */
export type SignalType = "threat" | "opportunity" | "neutral";

/** Breakpoint identifiers for responsive layouts */
export type Breakpoint = "mobile" | "tablet" | "largeTablet";

/** Responsive scaling multipliers for typography and spacing */
export interface ResponsiveScale {
  /** Font size multiplier based on screen width */
  font: number;
  /** Spacing/margin/padding multiplier based on screen width */
  spacing: number;
  /** Icon size multiplier based on screen width */
  icon: number;
}

/** Active responsive breakpoints state */
export interface ResponsiveState {
  /** Current breakpoint identifier */
  breakpoint: Breakpoint;
  /** Whether the screen is mobile-sized (< 640px) */
  isMobile: boolean;
  /** Whether the screen is tablet-sized (640px - 1024px) */
  isTablet: boolean;
  /** Whether the screen is large tablet/foldable (1024px+) */
  isLargeTablet: boolean;
  /** Current screen width in dp */
  width: number;
  /** Current screen height in dp */
  height: number;
  /** Orientation portrait vs landscape */
  isPortrait: boolean;
  /** Scaling multipliers for responsive design */
  scale: ResponsiveScale;
}

/** Card component visual variant */
export type CardVariant = "default" | "elevated" | "bordered" | "ghost";

/** Card component priority accent */
export type CardPriority = "none" | PriorityLevel;

/** Card component action event */
export interface CardAction {
  /** Label for the action button */
  label: string;
  /** Callback when action is pressed */
  onPress: () => void;
  /** Optional icon name from lucide-react-native */
  icon?: string;
}
