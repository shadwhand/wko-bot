/** Chart design tokens — colors, TSB mapping, axis typography, tooltip template. */

// ─── Semantic chart palette ───────────────────────────────────────

export const COLORS = {
  ctl: '#4dabf7',       // blue — fitness / CTL line
  atl: '#ff6b6b',       // red — fatigue / ATL line
  tsb: '#51cf66',       // green — form / TSB line
  power: '#ffd43b',     // yellow — power data
  hr: '#ff6b6b',        // red — heart rate
  cadence: '#b197fc',   // purple — cadence
  speed: '#38d9a9',     // teal — speed
  elevation: '#868e96', // gray — elevation
  primary: '#4dabf7',   // blue — primary accent
  danger: '#ff6b6b',    // red — danger state
  warning: '#ffd43b',   // amber — warning state
  success: '#51cf66',   // green — ok/success state
  muted: '#868e96',     // gray — secondary text / gridlines
} as const

// ─── TSB color mapping ───────────────────────────────────────────

export function tsbColor(tsb: number): string {
  if (tsb > 5) return COLORS.success    // fresh / green
  if (tsb >= -10) return COLORS.warning // neutral / amber
  return COLORS.danger                  // fatigued / red
}

export function tsbLabel(tsb: number): string {
  if (tsb > 25) return 'Very Fresh'
  if (tsb > 5) return 'Fresh'
  if (tsb >= -10) return 'Neutral'
  if (tsb >= -25) return 'Tired'
  return 'Very Tired'
}

// ─── Alert severity colors ───────────────────────────────────────

export const SEVERITY_COLORS = {
  danger: '#ff6b6b',
  warning: '#ffd43b',
  ok: '#51cf66',
  info: '#4dabf7',
} as const

export type Severity = keyof typeof SEVERITY_COLORS

// ─── Axis typography ─────────────────────────────────────────────

export const AXIS = {
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  fontSize: 11,
  fontColor: '#868e96',
  gridColor: '#30363d',
  gridOpacity: 0.4,
  tickPadding: 8,
} as const

// ─── Tooltip ─────────────────────────────────────────────────────

export const TOOLTIP = {
  background: '#1c2128',
  border: '#30363d',
  textColor: '#e6edf3',
  fontSize: 12,
  padding: 8,
  borderRadius: 6,
  maxWidth: 240,
} as const

// ─── Annotation visual style ─────────────────────────────────────

export const ANNOTATION = {
  regionOpacity: 0.15,
  lineDash: '6,4',
  lineWidth: 2,
  pointRadius: 5,
  badgeFontSize: 10,
  maxLabelLength: 200,
} as const

// ─── Breakpoints ─────────────────────────────────────────────────

export const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
} as const
