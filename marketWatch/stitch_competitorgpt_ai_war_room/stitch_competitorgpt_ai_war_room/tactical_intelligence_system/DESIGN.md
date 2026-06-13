---
name: Tactical Intelligence System
colors:
  surface: '#13121b'
  surface-dim: '#13121b'
  surface-bright: '#393842'
  surface-container-lowest: '#0e0d16'
  surface-container-low: '#1b1b24'
  surface-container: '#1f1f28'
  surface-container-high: '#2a2933'
  surface-container-highest: '#35343e'
  on-surface: '#e4e1ee'
  on-surface-variant: '#c7c4d8'
  inverse-surface: '#e4e1ee'
  inverse-on-surface: '#302f39'
  outline: '#918fa1'
  outline-variant: '#464555'
  surface-tint: '#c4c0ff'
  primary: '#c4c0ff'
  on-primary: '#2000a4'
  primary-container: '#8781ff'
  on-primary-container: '#1b0091'
  inverse-primary: '#4f44e2'
  secondary: '#a2e7ff'
  on-secondary: '#003642'
  secondary-container: '#00d2fd'
  on-secondary-container: '#005669'
  tertiary: '#ffb785'
  on-tertiary: '#502500'
  tertiary-container: '#db761f'
  on-tertiary-container: '#461f00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e3dfff'
  primary-fixed-dim: '#c4c0ff'
  on-primary-fixed: '#100069'
  on-primary-fixed-variant: '#3622ca'
  secondary-fixed: '#b4ebff'
  secondary-fixed-dim: '#3cd7ff'
  on-secondary-fixed: '#001f27'
  on-secondary-fixed-variant: '#004e5f'
  tertiary-fixed: '#ffdcc6'
  tertiary-fixed-dim: '#ffb785'
  on-tertiary-fixed: '#301400'
  on-tertiary-fixed-variant: '#713700'
  background: '#13121b'
  on-background: '#e4e1ee'
  surface-variant: '#35343e'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  data-lg:
    fontFamily: JetBrains Mono
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  data-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin: 32px
  container-max: 1440px
---

## Brand & Style
The design system is engineered for high-stakes decision-making and competitive intelligence. It evokes the atmosphere of a strategic military operations center—focused, authoritative, and technologically advanced. The aesthetic balances a dark, high-contrast environment with vibrant signal colors to prioritize information hierarchy and rapid data processing.

The style is **Modern/Technological** with a focus on precision. It utilizes deep blacks and cool grays to reduce eye strain during long-duration monitoring, while employing "electric" accents to draw attention to critical insights. Subtle glows and kinetic pulse animations are used sparingly to indicate live data streams or high-priority threats without cluttering the visual field.

## Colors
This design system uses a deeply saturated dark palette to establish a "command center" feel. 

- **Primary (Electric Purple):** Used for primary actions, active navigation states, and branding elements.
- **Accent (Cyan):** Reserved for technical readouts, secondary highlights, and scanning animations.
- **Semantic Colors:** Warning (Orange), Success (Green), and Danger (Red) follow industry standards for rapid recognition of system health and competitive threats.
- **Neutrals:** The background, surface, and elevated surface tiers create a clear spatial hierarchy, allowing data-heavy cards to pop against the void.

## Typography
The typography strategy employs a dual-font system to separate narrative from intelligence.

- **Inter:** Used for all interface labels, headlines, and standard body text. It provides maximum legibility and a modern, professional feel.
- **JetBrains Mono:** Used exclusively for data points, signal logs, timestamps, and coordinates. The monospaced nature ensures that fluctuating numbers do not cause layout shifts and conveys a "raw data" technical aesthetic.
- **Hierarchy:** Use uppercase for `label-sm` to denote system-level metadata.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a 12-column structure for desktop. To maintain the intensity of a dashboard, density is kept medium-to-high.

- **Gaps:** A standard 24px gutter is used between major dashboard modules to ensure clarity.
- **Padding:** Internal card padding is standardized at 24px, while dense data tables may drop to 12px.
- **Breakpoints:**
  - **Mobile (<768px):** Single column, 16px margins, 16px gutters.
  - **Tablet (768px - 1024px):** 6-column grid.
  - **Desktop (>1024px):** Full 12-column grid with a 1440px max-width container.

## Elevation & Depth
Depth is created through **Tonal Layering** and subtle luminosity rather than traditional drop shadows.

- **Background:** `#0A0A0F` serves as the foundation.
- **Surface:** `#111118` for primary dashboard cards. These should have a subtle 1px border of `#2A2A3A`.
- **Surface Elevated:** `#1A1A24` for popovers, tooltips, and modals. 
- **Luminosity:** High-priority cards (Danger/Warning) can feature a 15% opacity outer glow of their respective semantic color to simulate a glowing HUD (Head-Up Display) element.

## Shapes
The shape language is structured and architectural. 
- **Cards:** Use a 16px radius (`rounded-lg`) to soften the high-contrast UI and make the platform feel modern.
- **Buttons & Inputs:** Use a 12px radius for a distinct, tactile feel.
- **Icons:** Use sharp or slightly rounded (2px) inner corners to maintain the "military spec" precision.

## Components

### Buttons
- **Primary:** Background `#6C63FF`, Text `#FFFFFF`. On hover, add a subtle Cyan glow.
- **Secondary:** Border `1px solid #2A2A3A`, Background `transparent`. Text `#00D4FF`.
- **States:** 12px corner radius. Pulse animation on "Critical Action" buttons.

### Cards
- **Standard:** Background `#111118`, Border `1px solid #2A2A3A`, 16px radius.
- **Header:** Cards should include a `label-sm` header using JetBrains Mono to identify the data source or "Signal Origin."

### Inputs & Selects
- **Field:** Background `#0A0A0F`, Border `1px solid #2A2A3A`. 
- **Active State:** Border shifts to `#00D4FF` (Cyan) with a soft inner glow.

### Indicators & Chips
- **Status Chips:** Small, pill-shaped elements with 10% opacity backgrounds of the semantic color and 100% opacity text (e.g., Green text on dark green tint).
- **Critical Pulse:** For "Danger" status, use a CSS keyframe pulse on the border-color or a small 8px dot next to the label.

### Data Visualizations
- **Charts:** Use thin 1px lines. Fill areas with 10% opacity gradients of Primary or Accent colors.
- **Grids:** Background grids within charts should use `#1A1A24` at 0.5px width.