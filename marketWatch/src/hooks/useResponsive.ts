import { useWindowDimensions } from "react-native";
import type { Breakpoint, ResponsiveScale, ResponsiveState } from "@/types";

/**
 * Breakpoint thresholds in dp (device-independent pixels).
 * Aligned with Tailwind CSS v3 breakpoint conventions.
 */
const BREAKPOINTS = {
  mobile: 640,
  tablet: 1024,
} as const;

/**
 * Base reference width (375dp = iPhone SE/classic form factor).
 * All scaling multipliers are computed relative to this reference.
 */
const BASE_WIDTH = 375;

/**
 * Computes typography, spacing, and icon scaling multipliers
 * based on the current screen width relative to the base reference.
 *
 * - Font scale grows more slowly (cube root) to prevent text from
 *   becoming uncomfortably large on tablets.
 * - Spacing scale grows linearly so layouts breathe naturally.
 * - Icon scale is halfway between font and spacing rates.
 */
function computeScale(width: number): ResponsiveScale {
  const ratio = width / BASE_WIDTH;
  return {
    font: Math.max(0.75, Math.min(1.5, Math.pow(ratio, 1 / 3))),
    spacing: Math.max(0.75, Math.min(2, ratio)),
    icon: Math.max(0.75, Math.min(1.75, Math.pow(ratio, 1 / 2))),
  };
}

/**
 * Determines the active breakpoint string from a given width.
 */
function getBreakpoint(width: number): Breakpoint {
  if (width >= BREAKPOINTS.tablet) return "largeTablet";
  if (width >= BREAKPOINTS.mobile) return "tablet";
  return "mobile";
}

/**
 * Custom hook that computes active responsive breakpoints and dynamic
 * scaling multipliers for margins, padding, typography, and icons.
 *
 * Usage:
 * ```tsx
 * const { isMobile, isTablet, scale } = useResponsive();
 * const fontSize = 16 * scale.font;
 * const margin = 16 * scale.spacing;
 * ```
 *
 * @returns {ResponsiveState} Current responsive state with breakpoint flags and scaling multipliers.
 */
export function useResponsive(): ResponsiveState {
  const { width, height } = useWindowDimensions();

  const breakpoint = getBreakpoint(width);
  const isMobile = breakpoint === "mobile";
  const isTablet = breakpoint === "tablet";
  const isLargeTablet = breakpoint === "largeTablet";
  const isPortrait = height >= width;
  const scale = computeScale(width);

  return {
    breakpoint,
    isMobile,
    isTablet,
    isLargeTablet,
    width,
    height,
    isPortrait,
    scale,
  } as const;
}

/**
 * Convenience helpers for deriving responsive style values.
 *
 * @example
 * const padding = responsiveValue(16, 24, 32)(isMobile, isTablet);
 * // mobile → 16, tablet → 24, largeTablet → 32
 */
export function responsiveValue<T>(mobile: T, tablet: T, largeTablet: T) {
  return (isMobile: boolean, isTablet: boolean): T => {
    if (isMobile) return mobile;
    if (isTablet) return tablet;
    return largeTablet;
  };
}
