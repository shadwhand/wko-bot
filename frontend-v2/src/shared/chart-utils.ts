// frontend-v2/src/shared/chart-utils.ts
import * as d3 from 'd3';
import { COLORS, AXIS } from './tokens';

/* ── Duration Formatters ─────────────────────────────────────────── */

/** Format seconds to short axis label: 1s, 5min, 60min */
export function fmtDurationShort(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  return `${Math.round(seconds / 60)}min`;
}

/** Format seconds to readable tooltip: Xmin Ys */
export function fmtDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  const min = Math.floor(seconds / 60);
  const sec = seconds % 60;
  if (sec === 0) return `${min}min`;
  return `${min}min ${sec}s`;
}

/** Format elapsed seconds to H:MM:SS or MM:SS */
export function fmtElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const mm = m < 10 ? `0${m}` : `${m}`;
  const ss = s < 10 ? `0${s}` : `${s}`;
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

/* ── Axis Helpers ────────────────────────────────────────────────── */

/** Apply standard axis styling (font, color) to a D3 axis group */
export function styleAxis(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  options?: { hideAxisLine?: boolean }
): void {
  g.selectAll('text')
    .style('fill', AXIS.fontColor)
    .style('font-size', `${AXIS.fontSize}px`);
  g.selectAll('.domain, line')
    .style('stroke', AXIS.gridColor);
  if (options?.hideAxisLine) {
    g.selectAll('.domain').remove();
  }
}

/** Draw horizontal grid lines using a y-scale */
export function drawGridY(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  yScale: d3.ScaleLinear<number, number>,
  width: number,
  ticks = 6
): void {
  g.append('g')
    .attr('class', 'grid')
    .call(
      d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat('' as unknown as (d: d3.NumberValue) => string)
        .ticks(ticks)
    )
    .selectAll('line')
    .style('stroke', AXIS.gridColor)
    .style('stroke-opacity', AXIS.gridOpacity);
  g.selectAll('.grid .domain').remove();
}

/* ── Tooltip Positioning ─────────────────────────────────────────── */

/** Calculate tooltip left position, flipping to avoid overflow */
export function tooltipLeft(
  cursorX: number,
  marginLeft: number,
  tipWidth: number,
  containerWidth: number,
  offset = 12
): number {
  let left = cursorX + marginLeft + offset;
  if (left + tipWidth > containerWidth) {
    left = cursorX + marginLeft - tipWidth - offset;
  }
  return left;
}

/* ── Zone Color Helpers ──────────────────────────────────────────── */

/** TSB status color: green > 5, amber -10 to 5, red < -10 */
export function tsbColor(tsb: number): string {
  if (tsb > 5) return COLORS.success;
  if (tsb >= -10) return COLORS.warning;
  return COLORS.danger;
}

/** Demand ratio color: green < 0.85, amber 0.85-0.95, red >= 0.95 */
export function demandColor(ratio: number): string {
  if (ratio >= 0.95) return COLORS.danger;
  if (ratio >= 0.85) return COLORS.warning;
  return COLORS.success;
}

/** Demand ratio opacity for segment overlay fills */
export function demandOpacity(ratio: number): number {
  if (ratio > 1.0) return 0.4;
  if (ratio >= 0.95) return 0.25;
  if (ratio >= 0.85) return 0.2;
  return 0.15;
}

/** IF distribution bar color: blue < 0.55, amber 0.55-0.70, red > 0.70 */
export function ifZoneColor(ifValue: number): string {
  if (ifValue >= 0.70) return COLORS.danger;
  if (ifValue >= 0.55) return COLORS.warning;
  return COLORS.primary;
}

/** Power zone color for ride time series zone shading */
export function powerZoneColor(zone: number): string {
  const zoneColors: Record<number, string> = {
    1: '#636e7b', // Recovery - gray
    2: '#3fb950', // Endurance - green
    3: '#58a6ff', // Tempo - blue
    4: '#d29922', // Threshold - amber
    5: '#f0883e', // VO2max - orange
    6: '#f85149', // Anaerobic - red
    7: '#f778ba', // Neuromuscular - pink
  };
  return zoneColors[zone] || COLORS.muted;
}

/* ── Rolling Average ─────────────────────────────────────────────── */

/** Compute rolling average of a numeric array */
export function rollingAvg(
  values: (number | null)[],
  window: number
): (number | null)[] {
  if (window < 2) return [...values];
  const out: (number | null)[] = [];
  let sum = 0;
  let count = 0;
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v != null) { sum += v; count++; }
    if (i >= window) {
      const old = values[i - window];
      if (old != null) { sum -= old; count--; }
    }
    out.push(count > 0 ? sum / count : null);
  }
  return out;
}

/* ── Bisect Helper ───────────────────────────────────────────────── */

/** Find nearest data point to a cursor position using bisect */
export function findNearest<T>(
  data: T[],
  accessor: (d: T) => number,
  target: number
): T | null {
  if (!data.length) return null;
  const bisect = d3.bisector(accessor).left;
  const i = bisect(data, target, 1);
  const d0 = data[i - 1];
  const d1 = data[i];
  if (!d0) return d1 || null;
  if (!d1) return d0;
  return target - accessor(d0) > accessor(d1) - target ? d1 : d0;
}
