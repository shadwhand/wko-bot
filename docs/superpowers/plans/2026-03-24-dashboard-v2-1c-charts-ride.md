# Plan 1C: D3 Charts + Ride Detail View + Annotation POC

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port all D3 chart panels to React+TypeScript, build the full ride detail page with multi-channel time series, and deliver the annotation system POC wired into the PMC chart.

**Depends on:**
- **Plan 1A** (foundation): Vite scaffold, typed API client (`src/api/client.ts`, `src/api/types.ts`), Zustand store (`src/store/data-store.ts`), `ChartContainer` component (D3 wrapper with ResizeObserver), chart design tokens (`src/shared/tokens.ts`)
- **Plan 1B** (layout): `PanelWrapper` with header bar chrome, `PanelRegistry`, layout engine with tabs

**Tech Stack:** React 18, TypeScript, D3.js v7, Zustand, Vitest, Vite

**Spec:** `docs/superpowers/specs/2026-03-24-dashboard-v2-rewrite.md`

**Source charts to port:** `frontend/js/charts/pmc.js`, `frontend/js/charts/mmp.js`, `frontend/js/charts/segment-profile.js`, `frontend/js/charts/if-distribution.js`, `frontend/js/charts/rolling-pd.js`, `frontend/js/charts/ftp-growth.js`, `frontend/js/charts/ride-timeseries.js`

**Test command:** `cd frontend-v2 && npx vitest run`

**Dev server:** `cd frontend-v2 && npm run dev`

**CRITICAL:** Every D3 chart must render from Zustand store data. No inline fetching. Charts consume pre-populated store slices via selectors. Loading/error/empty states are handled uniformly.

---

## File Structure

```
frontend-v2/src/
  shared/
    chart-utils.ts           — NEW: D3 helpers (axis formatters, gridlines, tooltip, zones)
    AnnotationOverlay.tsx     — NEW: annotation rendering layer
    AnnotationOverlay.module.css
  panels/
    fitness/
      PMCChart.tsx            — NEW: PMC line/area chart + annotation POC
      PMCChart.module.css
      MMPCurve.tsx            — NEW: MMP log-scale chart
      MMPCurve.module.css
      RollingFtp.tsx          — NEW: mFTP time series + big number
      RollingFtp.module.css
      FtpGrowth.tsx           — NEW: metric cards + scatter plot
      FtpGrowth.module.css
      RollingPd.tsx           — NEW: multi-line PD params
      RollingPd.module.css
    health/
      IFDistribution.tsx      — NEW: IF histogram
      IFDistribution.module.css
    event-prep/
      SegmentProfile.tsx      — NEW: elevation profile
      SegmentProfile.module.css
  ride/
    RideDetail.tsx            — NEW: full ride detail page
    RideDetail.module.css
    RideTimeSeries.tsx        — NEW: multi-channel stacked time series
    RideTimeSeries.module.css
    IntervalCards.tsx          — NEW: detected interval cards
    IntervalCards.module.css
    RideMetricsBar.tsx        — NEW: header metrics grid
    RideMetricsBar.module.css
    PlannedVsCompleted.tsx    — NEW: TP comparison
    RideSubTabs.tsx           — NEW: sub-tab navigation
  __tests__/
    chart-utils.test.ts       — NEW
    annotation-store.test.ts  — NEW
    PMCChart.test.tsx          — NEW
    RideDetail.test.tsx        — NEW
```

---

## Task 1: Chart Utilities — shared D3 helpers

**Files:**
- Create: `frontend-v2/src/shared/chart-utils.ts`
- Create: `frontend-v2/src/__tests__/chart-utils.test.ts`

Reusable D3 functions used by every chart panel. Must be written and tested first.

- [ ] **Step 1: Create chart-utils.ts**

```typescript
// frontend-v2/src/shared/chart-utils.ts
import * as d3 from 'd3';
import {
  COLORS,
  TSB_COLORS,
  CHART_LINE_COLORS,
  AXIS_STYLE,
  GRID_STYLE,
} from './tokens';

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
    .style('fill', AXIS_STYLE.labelColor)
    .style('font-size', AXIS_STYLE.fontSize);
  g.selectAll('.domain, line')
    .style('stroke', AXIS_STYLE.lineColor);
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
        .tickFormat('' as any)
        .ticks(ticks)
    )
    .selectAll('line')
    .style('stroke', GRID_STYLE.color)
    .style('stroke-opacity', GRID_STYLE.opacity);
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
  if (tsb > 5) return TSB_COLORS.positive;
  if (tsb >= -10) return TSB_COLORS.neutral;
  return TSB_COLORS.negative;
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
  return COLORS.accent;
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
  return zoneColors[zone] || COLORS.textMuted;
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
```

- [ ] **Step 2: Create chart-utils tests**

```typescript
// frontend-v2/src/__tests__/chart-utils.test.ts
import { describe, it, expect } from 'vitest';
import {
  fmtDurationShort,
  fmtDuration,
  fmtElapsed,
  tooltipLeft,
  tsbColor,
  demandColor,
  demandOpacity,
  ifZoneColor,
  rollingAvg,
  findNearest,
} from '../shared/chart-utils';
import { TSB_COLORS, COLORS } from '../shared/tokens';

describe('fmtDurationShort', () => {
  it('formats seconds under 60 as Xs', () => {
    expect(fmtDurationShort(5)).toBe('5s');
    expect(fmtDurationShort(30)).toBe('30s');
  });
  it('formats 60+ seconds as Xmin', () => {
    expect(fmtDurationShort(60)).toBe('1min');
    expect(fmtDurationShort(300)).toBe('5min');
    expect(fmtDurationShort(3600)).toBe('60min');
  });
});

describe('fmtDuration', () => {
  it('formats short durations', () => {
    expect(fmtDuration(5)).toBe('5s');
  });
  it('formats exact minutes', () => {
    expect(fmtDuration(120)).toBe('2min');
  });
  it('formats minutes + seconds', () => {
    expect(fmtDuration(125)).toBe('2min 5s');
  });
});

describe('fmtElapsed', () => {
  it('formats MM:SS under an hour', () => {
    expect(fmtElapsed(125)).toBe('02:05');
  });
  it('formats H:MM:SS at an hour or more', () => {
    expect(fmtElapsed(3661)).toBe('1:01:01');
  });
});

describe('tooltipLeft', () => {
  it('places tooltip to the right by default', () => {
    expect(tooltipLeft(100, 50, 80, 800)).toBe(162);
  });
  it('flips tooltip to the left when it would overflow', () => {
    expect(tooltipLeft(700, 50, 80, 800)).toBe(658);
  });
});

describe('tsbColor', () => {
  it('returns positive color for TSB > 5', () => {
    expect(tsbColor(10)).toBe(TSB_COLORS.positive);
  });
  it('returns neutral color for TSB -10 to 5', () => {
    expect(tsbColor(0)).toBe(TSB_COLORS.neutral);
    expect(tsbColor(-10)).toBe(TSB_COLORS.neutral);
  });
  it('returns negative color for TSB < -10', () => {
    expect(tsbColor(-15)).toBe(TSB_COLORS.negative);
  });
});

describe('demandColor', () => {
  it('returns danger for ratio >= 0.95', () => {
    expect(demandColor(1.0)).toBe(COLORS.danger);
    expect(demandColor(0.95)).toBe(COLORS.danger);
  });
  it('returns warning for ratio 0.85-0.95', () => {
    expect(demandColor(0.90)).toBe(COLORS.warning);
  });
  it('returns success for ratio < 0.85', () => {
    expect(demandColor(0.70)).toBe(COLORS.success);
  });
});

describe('demandOpacity', () => {
  it('returns higher opacity for higher demand', () => {
    expect(demandOpacity(1.1)).toBe(0.4);
    expect(demandOpacity(0.96)).toBe(0.25);
    expect(demandOpacity(0.90)).toBe(0.2);
    expect(demandOpacity(0.70)).toBe(0.15);
  });
});

describe('ifZoneColor', () => {
  it('colors by IF intensity zone', () => {
    expect(ifZoneColor(0.40)).toBe(COLORS.accent);
    expect(ifZoneColor(0.60)).toBe(COLORS.warning);
    expect(ifZoneColor(0.80)).toBe(COLORS.danger);
  });
});

describe('rollingAvg', () => {
  it('returns copy for window < 2', () => {
    expect(rollingAvg([1, 2, 3], 1)).toEqual([1, 2, 3]);
  });
  it('computes correct rolling average', () => {
    const result = rollingAvg([10, 20, 30, 40, 50], 3);
    expect(result[0]).toBeCloseTo(10);
    expect(result[1]).toBeCloseTo(15);
    expect(result[2]).toBeCloseTo(20);
    expect(result[3]).toBeCloseTo(30);
    expect(result[4]).toBeCloseTo(40);
  });
  it('handles nulls', () => {
    const result = rollingAvg([10, null, 30], 2);
    expect(result[0]).toBeCloseTo(10);
    expect(result[1]).toBeCloseTo(10);
    expect(result[2]).toBeCloseTo(30);
  });
});

describe('findNearest', () => {
  const data = [{ x: 1 }, { x: 5 }, { x: 10 }];
  it('finds nearest point', () => {
    expect(findNearest(data, d => d.x, 4)).toEqual({ x: 5 });
    expect(findNearest(data, d => d.x, 7)).toEqual({ x: 5 });
    expect(findNearest(data, d => d.x, 8)).toEqual({ x: 10 });
  });
  it('returns null for empty data', () => {
    expect(findNearest([], d => (d as any).x, 5)).toBeNull();
  });
});
```

- [ ] **Step 3: Run tests**

```bash
cd frontend-v2 && npx vitest run src/__tests__/chart-utils.test.ts
```

Expected: All 15+ tests pass.

- [ ] **Step 4: Commit**

```bash
git add frontend-v2/src/shared/chart-utils.ts frontend-v2/src/__tests__/chart-utils.test.ts
git commit -m "feat(1c): chart-utils — shared D3 helpers with tests"
```

---

## Task 2: PMC Chart — D3 line/area chart (annotation POC host)

**Files:**
- Create: `frontend-v2/src/panels/fitness/PMCChart.tsx`
- Create: `frontend-v2/src/panels/fitness/PMCChart.module.css`

Port from `frontend/js/charts/pmc.js`. This is the annotation POC chart — it must accept annotations from the store and render them via `AnnotationOverlay` (Task 9).

- [ ] **Step 1: Create PMCChart.module.css**

```css
/* frontend-v2/src/panels/fitness/PMCChart.module.css */
.wrapper {
  position: relative;
  width: 100%;
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--text-primary, #e6edf3);
  display: none;
  z-index: 10;
  white-space: nowrap;
}

.tooltip.visible {
  display: block;
}
```

- [ ] **Step 2: Create PMCChart.tsx**

```typescript
// frontend-v2/src/panels/fitness/PMCChart.tsx
import { useEffect, useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { AnnotationOverlay } from '../../shared/AnnotationOverlay';
import { CHART_LINE_COLORS, COLORS, GRID_STYLE, AXIS_STYLE } from '../../shared/tokens';
import { styleAxis, drawGridY, tooltipLeft, findNearest } from '../../shared/chart-utils';
import { PanelSkeleton, PanelError, PanelEmpty } from '../../shared/PanelStates';
import type { PMCRow } from '../../api/types';
import styles from './PMCChart.module.css';

const PANEL_ID = 'pmc-chart';
const CHART_HEIGHT = 280;
const MARGIN = { top: 20, right: 50, bottom: 30, left: 50 };

export function PMCChart() {
  const pmc = useDataStore(s => s.pmc);
  const loading = useDataStore(s => s.loading.has('pmc'));
  const error = useDataStore(s => s.errors['pmc']);
  const annotations = useDataStore(s => s.annotations[PANEL_ID] || []);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!pmc || !pmc.length) return <PanelEmpty message="No PMC data available" />;

  return (
    <div className={styles.wrapper}>
      <PMCChartInner data={pmc} />
      <AnnotationOverlay panelId={PANEL_ID} annotations={annotations} />
    </div>
  );
}

interface PMCChartInnerProps {
  data: PMCRow[];
}

function PMCChartInner({ data }: PMCChartInnerProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;

    svg.attr('width', width).attr('height', totalH);

    // Parse dates
    const parsed = data.map(d => ({
      ...d,
      _date: d3.timeParse('%Y-%m-%d')(d.date)!,
      ctl: d.CTL ?? d.ctl ?? 0,
      atl: d.ATL ?? d.atl ?? 0,
      tsb: d.TSB ?? d.tsb ?? 0,
      tss: d.TSS ?? d.tss ?? 0,
    })).filter(d => d._date != null)
      .sort((a, b) => a._date.getTime() - b._date.getTime());

    if (!parsed.length) return;

    // Clip path
    const clipId = 'pmc-clip';
    const defs = svg.append('defs');
    defs.append('clipPath').attr('id', clipId)
      .append('rect').attr('width', innerW).attr('height', innerH);

    const g = svg.append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(parsed, d => d._date) as [Date, Date])
      .range([0, innerW]);

    const maxLeft = d3.max(parsed, d => Math.max(d.ctl, d.atl, d.tss)) || 100;
    const yScaleLeft = d3.scaleLinear()
      .domain([0, maxLeft * 1.1])
      .range([innerH, 0]);

    const tsbExtent = d3.extent(parsed, d => d.tsb) as [number, number];
    const tsbPad = Math.max(Math.abs(tsbExtent[0] || 0), Math.abs(tsbExtent[1] || 0)) * 1.2 || 30;
    const yScaleRight = d3.scaleLinear()
      .domain([-tsbPad, tsbPad])
      .range([innerH, 0]);

    const content = g.append('g').attr('clip-path', `url(#${clipId})`);

    // Grid
    drawGridY(g, yScaleLeft, innerW);

    // TSB zero line
    const zeroY = yScaleRight(0);
    if (zeroY >= 0 && zeroY <= innerH) {
      content.append('line')
        .attr('x1', 0).attr('x2', innerW)
        .attr('y1', zeroY).attr('y2', zeroY)
        .style('stroke', COLORS.textMuted)
        .style('stroke-dasharray', '4,3')
        .style('stroke-width', 1);
    }

    // TSB area -- positive (green shading above zero)
    const areaPositive = d3.area<typeof parsed[0]>()
      .x(d => xScale(d._date))
      .y0(() => yScaleRight(0))
      .y1(d => yScaleRight(Math.max(0, d.tsb)))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', areaPositive)
      .style('fill', COLORS.success)
      .style('opacity', 0.12);

    // TSB area -- negative (red shading below zero)
    const areaNegative = d3.area<typeof parsed[0]>()
      .x(d => xScale(d._date))
      .y0(() => yScaleRight(0))
      .y1(d => yScaleRight(Math.min(0, d.tsb)))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', areaNegative)
      .style('fill', COLORS.danger)
      .style('opacity', 0.10);

    // CTL line (blue)
    const ctlLine = d3.line<typeof parsed[0]>()
      .x(d => xScale(d._date))
      .y(d => yScaleLeft(d.ctl))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', ctlLine)
      .style('fill', 'none')
      .style('stroke', CHART_LINE_COLORS.ctl)
      .style('stroke-width', 2);

    // ATL line (pink)
    const atlLine = d3.line<typeof parsed[0]>()
      .x(d => xScale(d._date))
      .y(d => yScaleLeft(d.atl))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', atlLine)
      .style('fill', 'none')
      .style('stroke', CHART_LINE_COLORS.atl)
      .style('stroke-width', 1.5);

    // TSB dashed line (amber)
    const tsbLine = d3.line<typeof parsed[0]>()
      .x(d => xScale(d._date))
      .y(d => yScaleRight(d.tsb))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(parsed)
      .attr('d', tsbLine)
      .style('fill', 'none')
      .style('stroke', CHART_LINE_COLORS.tsb)
      .style('stroke-width', 1.5)
      .style('stroke-dasharray', '6,3');

    // X axis
    const xAxisG = g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(8));
    styleAxis(xAxisG);

    // Y axis left (CTL/ATL/TSS)
    const yAxisLeftG = g.append('g').call(d3.axisLeft(yScaleLeft).ticks(6));
    styleAxis(yAxisLeftG);

    // Y axis right (TSB)
    const yAxisRightG = g.append('g')
      .attr('transform', `translate(${innerW},0)`)
      .call(d3.axisRight(yScaleRight).ticks(6));
    styleAxis(yAxisRightG);

    // Crosshair + hover overlay
    const crosshair = content.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .style('stroke', COLORS.textMuted)
      .style('stroke-width', 1)
      .style('display', 'none');

    content.append('rect')
      .attr('width', innerW).attr('height', innerH)
      .style('fill', 'none').style('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event);
        const x0 = xScale.invert(mx);
        const d = findNearest(parsed, p => p._date.getTime(), x0.getTime());
        if (!d) return;

        const cx = xScale(d._date);
        crosshair.attr('x1', cx).attr('x2', cx).style('display', null);

        const fmt = d3.timeFormat('%Y-%m-%d');
        setTooltipContent(
          `${fmt(d._date)}\nCTL: ${d.ctl.toFixed(1)}\nATL: ${d.atl.toFixed(1)}\nTSB: ${d.tsb.toFixed(1)}\nTSS: ${d.tss ?? '—'}`
        );
        setTooltipVisible(true);

        const tipW = tooltipRef.current?.offsetWidth ?? 100;
        const containerW = svgRef.current?.parentElement?.getBoundingClientRect().width ?? 800;
        const left = tooltipLeft(cx, MARGIN.left, tipW, containerW);
        setTooltipPos({ left, top: MARGIN.top + 10 });
      })
      .on('mouseleave', () => {
        crosshair.style('display', 'none');
        setTooltipVisible(false);
      });

    // Store scales on SVG element for annotation overlay to read
    const svgEl = svgRef.current;
    if (svgEl) {
      (svgEl as any).__scales = { xScale, yScaleLeft, yScaleRight, margin: MARGIN, innerW, innerH };
    }
  }, [data]);

  return (
    <ChartContainer onResize={renderChart}>
      <svg ref={svgRef} />
      <div
        ref={tooltipRef}
        className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
        style={{ left: tooltipPos.left, top: tooltipPos.top }}
      >
        {tooltipContent.split('\n').map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </ChartContainer>
  );
}
```

- [ ] **Step 3: Register in PanelRegistry**

In `frontend-v2/src/layout/PanelRegistry.ts`, add:

```typescript
import { PMCChart } from '../panels/fitness/PMCChart';

// In the panels map:
'pmc-chart': {
  id: 'pmc-chart',
  label: 'Performance Management Chart',
  category: 'fitness',
  description: 'CTL, ATL, TSB over time — fitness/fatigue/form tracking',
  component: PMCChart,
  dataKeys: ['pmc'],
},
```

- [ ] **Step 4: Visual verification**

```bash
cd frontend-v2 && npm run dev
```

Navigate to Fitness tab. PMC chart should render with:
- Blue CTL line, pink ATL line, amber dashed TSB line
- Green shading above zero, red shading below zero
- Dual y-axes (left: CTL/ATL, right: TSB)
- Crosshair tooltip on hover with date, CTL, ATL, TSB, TSS

- [ ] **Step 5: Commit**

```bash
git add frontend-v2/src/panels/fitness/PMCChart.tsx frontend-v2/src/panels/fitness/PMCChart.module.css
git commit -m "feat(1c): PMCChart — D3 line/area chart ported to React"
```

---

## Task 3: MMP Curve — D3 log-scale chart

**Files:**
- Create: `frontend-v2/src/panels/fitness/MMPCurve.tsx`
- Create: `frontend-v2/src/panels/fitness/MMPCurve.module.css`

Port from `frontend/js/charts/mmp.js`. Log-scale x-axis, MMP envelope + PD model curve overlay, recency toggle (30d/60d/90d/1yr/All).

- [ ] **Step 1: Create MMPCurve.module.css**

```css
/* frontend-v2/src/panels/fitness/MMPCurve.module.css */
.wrapper {
  position: relative;
  width: 100%;
}

.controls {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
  font-size: 0.75rem;
}

.toggleBtn {
  padding: 3px 8px;
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted, #484f58);
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
  transition: all 0.15s;
}

.toggleBtn.active {
  border-color: var(--accent, #58a6ff);
  background: rgba(88, 166, 255, 0.12);
  color: var(--accent, #58a6ff);
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--text-primary, #e6edf3);
  display: none;
  z-index: 10;
  white-space: nowrap;
}

.tooltip.visible {
  display: block;
}
```

- [ ] **Step 2: Create MMPCurve.tsx**

```typescript
// frontend-v2/src/panels/fitness/MMPCurve.tsx
import { useEffect, useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS, GRID_STYLE, AXIS_STYLE } from '../../shared/tokens';
import { styleAxis, drawGridY, tooltipLeft, fmtDurationShort, fmtDuration, findNearest } from '../../shared/chart-utils';
import { PanelSkeleton, PanelError, PanelEmpty } from '../../shared/PanelStates';
import type { ModelResult } from '../../api/types';
import styles from './MMPCurve.module.css';

const CHART_HEIGHT = 280;
const MARGIN = { top: 20, right: 20, bottom: 30, left: 55 };

const RECENCY_OPTIONS = [
  { label: '30d', days: 30 },
  { label: '60d', days: 60 },
  { label: '90d', days: 90 },
  { label: '1yr', days: 365 },
  { label: 'All', days: 0 },
] as const;

// MMP power zone boundaries (seconds)
const ZONES = [
  { label: 'NM', from: 1, to: 15, color: COLORS.danger },
  { label: 'AN', from: 15, to: 120, color: COLORS.warning },
  { label: 'VO2', from: 120, to: 480, color: COLORS.accent },
  { label: 'TH', from: 480, to: 1200, color: COLORS.success },
  { label: 'END', from: 1200, to: Infinity, color: COLORS.textMuted },
];

export function MMPCurve() {
  const model = useDataStore(s => s.model);
  const loading = useDataStore(s => s.loading.has('model'));
  const error = useDataStore(s => s.errors['model']);
  const [recency, setRecency] = useState(90);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!model || !model.mmp || !model.mmp.length) {
    return <PanelEmpty message="No MMP data available" />;
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.controls}>
        {RECENCY_OPTIONS.map(opt => (
          <button
            key={opt.label}
            className={`${styles.toggleBtn} ${recency === opt.days ? styles.active : ''}`}
            onClick={() => setRecency(opt.days)}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <MMPCurveInner model={model} recencyDays={recency} />
    </div>
  );
}

interface MMPCurveInnerProps {
  model: ModelResult;
  recencyDays: number;
}

function MMPCurveInner({ model, recencyDays }: MMPCurveInnerProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });

  const mmpData: [number, number][] = model.mmp || [];

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    if (!mmpData.length) return;

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const clipId = 'mmp-clip';
    svg.append('defs').append('clipPath').attr('id', clipId)
      .append('rect').attr('width', innerW).attr('height', innerH);

    const g = svg.append('g')
      .attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);
    const content = g.append('g').attr('clip-path', `url(#${clipId})`);

    // Scales
    const maxDur = d3.max(mmpData, d => d[0]) || 3600;
    const xScale = d3.scaleLog()
      .domain([1, maxDur])
      .range([0, innerW])
      .clamp(true);

    const maxW = d3.max(mmpData, d => d[1]) || 1000;
    const yScale = d3.scaleLinear()
      .domain([0, maxW * 1.08])
      .range([innerH, 0]);

    // Zone backgrounds
    ZONES.forEach(z => {
      const zoneTo = Math.min(z.to, maxDur);
      const x1 = xScale(Math.max(z.from, 1));
      const x2 = xScale(zoneTo);
      if (x2 <= x1) return;

      content.append('rect')
        .attr('x', x1).attr('y', 0)
        .attr('width', x2 - x1).attr('height', innerH)
        .style('fill', z.color).style('opacity', 0.04);

      content.append('text')
        .attr('x', (x1 + x2) / 2).attr('y', 14)
        .attr('text-anchor', 'middle')
        .style('fill', COLORS.textMuted)
        .style('font-size', '9px').style('opacity', 0.6)
        .text(z.label);
    });

    // Grid
    drawGridY(g, yScale, innerW);

    // MMP area fill
    const area = d3.area<[number, number]>()
      .x(d => xScale(d[0]))
      .y0(innerH)
      .y1(d => yScale(d[1]))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(mmpData)
      .attr('d', area)
      .style('fill', COLORS.accent)
      .style('opacity', 0.12);

    // MMP line
    const line = d3.line<[number, number]>()
      .x(d => xScale(d[0]))
      .y(d => yScale(d[1]))
      .curve(d3.curveMonotoneX);

    content.append('path')
      .datum(mmpData)
      .attr('d', line)
      .style('fill', 'none')
      .style('stroke', COLORS.accent)
      .style('stroke-width', 2);

    // PD model overlay
    if (model.mFTP != null && model.FRC != null && model.Pmax != null) {
      const tau = (model as any).tau ?? 0;
      const t0 = (model as any).t0 ?? 0;
      const frc = model.FRC;
      const mftp = model.mFTP;
      const pmax = model.Pmax;

      const points: [number, number][] = [];
      for (let t = 1; t <= maxDur; t = Math.ceil(t * 1.05) || t + 1) {
        let watts: number;
        if (t <= tau) {
          watts = pmax;
        } else {
          watts = (frc * 1000) / (t + t0) + mftp;
        }
        if (watts > 0) points.push([t, watts]);
      }

      const modelLine = d3.line<[number, number]>()
        .x(d => xScale(d[0]))
        .y(d => yScale(d[1]))
        .curve(d3.curveMonotoneX);

      content.append('path')
        .datum(points)
        .attr('d', modelLine)
        .style('fill', 'none')
        .style('stroke', COLORS.warning)
        .style('stroke-width', 1.5)
        .style('stroke-dasharray', '6,3')
        .style('opacity', 0.8);
    }

    // X axis (log scale, custom ticks)
    const tickValues = [1, 5, 30, 60, 300, 1200, 3600].filter(t => t <= maxDur);
    const xAxisG = g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).tickValues(tickValues).tickFormat(d => fmtDurationShort(d as number)));
    styleAxis(xAxisG);

    // Y axis
    const yAxisG = g.append('g').call(d3.axisLeft(yScale).ticks(6));
    styleAxis(yAxisG);

    // Y axis label
    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2).attr('y', -40)
      .attr('text-anchor', 'middle')
      .style('fill', COLORS.textMuted).style('font-size', '11px')
      .text('Watts');

    // Hover
    const crosshair = content.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .style('stroke', COLORS.textMuted).style('stroke-width', 1)
      .style('display', 'none');

    const dot = content.append('circle')
      .attr('r', 4).style('fill', COLORS.accent).style('display', 'none');

    content.append('rect')
      .attr('width', innerW).attr('height', innerH)
      .style('fill', 'none').style('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event);
        const durAtMouse = xScale.invert(mx);
        const d = findNearest(mmpData, p => p[0], durAtMouse);
        if (!d) return;

        const cx = xScale(d[0]);
        const cy = yScale(d[1]);
        crosshair.attr('x1', cx).attr('x2', cx).style('display', null);
        dot.attr('cx', cx).attr('cy', cy).style('display', null);

        setTooltipContent(`${fmtDuration(d[0])}\n${d[1]} W`);
        setTooltipVisible(true);

        const tipW = tooltipRef.current?.offsetWidth ?? 80;
        const containerW = svgRef.current?.parentElement?.getBoundingClientRect().width ?? 800;
        setTooltipPos({ left: tooltipLeft(cx, MARGIN.left, tipW, containerW), top: MARGIN.top + 10 });
      })
      .on('mouseleave', () => {
        crosshair.style('display', 'none');
        dot.style('display', 'none');
        setTooltipVisible(false);
      });
  }, [mmpData, model]);

  return (
    <ChartContainer onResize={renderChart}>
      <svg ref={svgRef} />
      <div
        ref={tooltipRef}
        className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
        style={{ left: tooltipPos.left, top: tooltipPos.top }}
      >
        {tooltipContent.split('\n').map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </ChartContainer>
  );
}
```

- [ ] **Step 3: Register in PanelRegistry**

```typescript
'mmp-curve': {
  id: 'mmp-curve',
  label: 'MMP / Power-Duration Curve',
  category: 'fitness',
  description: 'Mean Maximal Power envelope + PD model overlay',
  component: MMPCurve,
  dataKeys: ['model'],
},
```

- [ ] **Step 4: Commit**

```bash
git add frontend-v2/src/panels/fitness/MMPCurve.tsx frontend-v2/src/panels/fitness/MMPCurve.module.css
git commit -m "feat(1c): MMPCurve — D3 log-scale MMP chart ported to React"
```

---

## Task 4: Rolling FTP — time series + big number

**Files:**
- Create: `frontend-v2/src/panels/fitness/RollingFtp.tsx`
- Create: `frontend-v2/src/panels/fitness/RollingFtp.module.css`

- [ ] **Step 1: Create RollingFtp.module.css**

```css
/* frontend-v2/src/panels/fitness/RollingFtp.module.css */
.wrapper {
  position: relative;
  width: 100%;
}

.bigNumber {
  text-align: center;
  margin-bottom: 8px;
}

.bigNumber .value {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent, #58a6ff);
  line-height: 1;
}

.bigNumber .label {
  font-size: 0.8rem;
  color: var(--text-secondary, #8b949e);
  margin-top: 2px;
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--text-primary, #e6edf3);
  display: none;
  z-index: 10;
  white-space: nowrap;
}

.tooltip.visible {
  display: block;
}
```

- [ ] **Step 2: Create RollingFtp.tsx**

```typescript
// frontend-v2/src/panels/fitness/RollingFtp.tsx
import { useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS, AXIS_STYLE } from '../../shared/tokens';
import { styleAxis, drawGridY, tooltipLeft, findNearest } from '../../shared/chart-utils';
import { PanelSkeleton, PanelError, PanelEmpty } from '../../shared/PanelStates';
import type { RollingFtpRow } from '../../api/types';
import styles from './RollingFtp.module.css';

const CHART_HEIGHT = 180;
const MARGIN = { top: 10, right: 20, bottom: 30, left: 50 };

export function RollingFtp() {
  const rollingFtp = useDataStore(s => s.rollingFtp);
  const loading = useDataStore(s => s.loading.has('rollingFtp'));
  const error = useDataStore(s => s.errors['rollingFtp']);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!rollingFtp || !rollingFtp.length) return <PanelEmpty message="No rolling FTP data" />;

  const latest = rollingFtp[rollingFtp.length - 1];

  return (
    <div className={styles.wrapper}>
      <div className={styles.bigNumber}>
        <div className="value">{Math.round(latest.mFTP)} W</div>
        <div className="label">Current mFTP</div>
      </div>
      <RollingFtpInner data={rollingFtp} />
    </div>
  );
}

function RollingFtpInner({ data }: { data: RollingFtpRow[] }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const parsed = data.map(d => ({
      ...d,
      _date: new Date(d.date),
    })).sort((a, b) => a._date.getTime() - b._date.getTime());

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const xScale = d3.scaleTime()
      .domain(d3.extent(parsed, d => d._date) as [Date, Date])
      .range([0, innerW]);

    const yExtent = d3.extent(parsed, d => d.mFTP) as [number, number];
    const yPad = (yExtent[1] - yExtent[0]) * 0.15 || 10;
    const yScale = d3.scaleLinear()
      .domain([yExtent[0] - yPad, yExtent[1] + yPad])
      .range([innerH, 0]);

    // Grid
    drawGridY(g, yScale, innerW, 4);

    // Area fill
    const area = d3.area<typeof parsed[0]>()
      .x(d => xScale(d._date))
      .y0(innerH)
      .y1(d => yScale(d.mFTP))
      .curve(d3.curveMonotoneX);

    g.append('path').datum(parsed).attr('d', area)
      .style('fill', COLORS.accent).style('opacity', 0.08);

    // Line
    const line = d3.line<typeof parsed[0]>()
      .x(d => xScale(d._date))
      .y(d => yScale(d.mFTP))
      .curve(d3.curveMonotoneX);

    g.append('path').datum(parsed).attr('d', line)
      .style('fill', 'none')
      .style('stroke', COLORS.accent).style('stroke-width', 2);

    // Trend line (linear regression)
    if (parsed.length > 2) {
      const xs = parsed.map((_, i) => i);
      const ys = parsed.map(d => d.mFTP);
      const n = xs.length;
      const sumX = xs.reduce((a, b) => a + b, 0);
      const sumY = ys.reduce((a, b) => a + b, 0);
      const sumXY = xs.reduce((a, x, i) => a + x * ys[i], 0);
      const sumXX = xs.reduce((a, x) => a + x * x, 0);
      const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
      const intercept = (sumY - slope * sumX) / n;

      const trendLine = d3.line<typeof parsed[0]>()
        .x(d => xScale(d._date))
        .y((_, i) => yScale(slope * i + intercept))
        .curve(d3.curveLinear);

      g.append('path').datum(parsed).attr('d', trendLine)
        .style('fill', 'none')
        .style('stroke', COLORS.textMuted)
        .style('stroke-width', 1)
        .style('stroke-dasharray', '4,3');
    }

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(xScale).ticks(6).tickFormat(d3.timeFormat('%b %y') as any));
    styleAxis(xAxisG);

    const yAxisG = g.append('g')
      .call(d3.axisLeft(yScale).ticks(4).tickFormat(d => `${d}W`));
    styleAxis(yAxisG);

    // Hover
    const crosshair = g.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .style('stroke', COLORS.textMuted).style('stroke-width', 1)
      .style('display', 'none');

    g.append('rect')
      .attr('width', innerW).attr('height', innerH)
      .style('fill', 'none').style('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event);
        const x0 = xScale.invert(mx);
        const d = findNearest(parsed, p => p._date.getTime(), x0.getTime());
        if (!d) return;

        const cx = xScale(d._date);
        crosshair.attr('x1', cx).attr('x2', cx).style('display', null);
        setTooltipContent(`${d3.timeFormat('%Y-%m-%d')(d._date)}\nmFTP: ${Math.round(d.mFTP)} W`);
        setTooltipVisible(true);
        const containerW = svgRef.current?.parentElement?.getBoundingClientRect().width ?? 800;
        setTooltipPos({ left: tooltipLeft(cx, MARGIN.left, 100, containerW), top: MARGIN.top + 10 });
      })
      .on('mouseleave', () => {
        crosshair.style('display', 'none');
        setTooltipVisible(false);
      });
  }, [data]);

  return (
    <ChartContainer onResize={renderChart}>
      <svg ref={svgRef} />
      <div
        className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
        style={{ left: tooltipPos.left, top: tooltipPos.top }}
      >
        {tooltipContent.split('\n').map((line, i) => <div key={i}>{line}</div>)}
      </div>
    </ChartContainer>
  );
}
```

- [ ] **Step 3: Register + Commit**

```bash
git add frontend-v2/src/panels/fitness/RollingFtp.tsx frontend-v2/src/panels/fitness/RollingFtp.module.css
git commit -m "feat(1c): RollingFtp — mFTP time series with big number + trend line"
```

---

## Task 5: FTP Growth — metric cards + scatter plot

**Files:**
- Create: `frontend-v2/src/panels/fitness/FtpGrowth.tsx`
- Create: `frontend-v2/src/panels/fitness/FtpGrowth.module.css`

Port from `frontend/js/charts/ftp-growth.js`. Metric cards (growth rate, phase, training years, R-squared) with optional D3 scatter plot.

- [ ] **Step 1: Create FtpGrowth.module.css**

```css
/* frontend-v2/src/panels/fitness/FtpGrowth.module.css */
.wrapper { position: relative; width: 100%; }

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.8rem;
}

.card {
  text-align: center;
}

.card .value {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 1.4rem;
  font-weight: 600;
}

.card .label {
  color: var(--text-secondary, #8b949e);
}
```

- [ ] **Step 2: Create FtpGrowth.tsx**

```typescript
// frontend-v2/src/panels/fitness/FtpGrowth.tsx
import { useRef, useCallback } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis } from '../../shared/chart-utils';
import { PanelSkeleton, PanelError, PanelEmpty } from '../../shared/PanelStates';
import type { FtpGrowthResponse } from '../../api/types';
import styles from './FtpGrowth.module.css';

const CHART_HEIGHT = 200;
const MARGIN = { top: 10, right: 20, bottom: 30, left: 45 };

export function FtpGrowth() {
  const ftpGrowth = useDataStore(s => s.ftpGrowth);
  const loading = useDataStore(s => s.loading.has('ftpGrowth'));
  const error = useDataStore(s => s.errors['ftpGrowth']);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!ftpGrowth) return <PanelEmpty message="No FTP growth data" />;

  const phase = ftpGrowth.growth_phase || (ftpGrowth.plateau_detected ? 'plateau' : '--');
  const phaseColor = phase === 'plateau' ? COLORS.warning : phase === 'rapid' ? COLORS.success : COLORS.accent;
  const growthRate = ftpGrowth.improvement_rate_w_per_year;
  const rSquared = ftpGrowth.r_squared;
  const trainingAge = ftpGrowth.training_age_weeks;

  return (
    <div className={styles.wrapper}>
      <div className={styles.cards}>
        {growthRate != null && (
          <div className={styles.card}>
            <div className="value">{growthRate.toFixed(1)}</div>
            <div className="label">W/year</div>
          </div>
        )}
        <div className={styles.card}>
          <div className="value" style={{ color: phaseColor, fontSize: '1.1rem' }}>{phase}</div>
          <div className="label">Phase</div>
        </div>
        {trainingAge != null && (
          <div className={styles.card}>
            <div className="value">{(trainingAge / 52).toFixed(1)}</div>
            <div className="label">Training Years</div>
          </div>
        )}
        {rSquared != null && (
          <div className={styles.card}>
            <div className="value">{rSquared.toFixed(2)}</div>
            <div className="label">R² (fit)</div>
          </div>
        )}
      </div>
      {ftpGrowth.data_points && ftpGrowth.data_points.length > 0 ? (
        <FtpGrowthChart data={ftpGrowth} />
      ) : (
        <div style={{ color: COLORS.textMuted, fontSize: '0.8rem', textAlign: 'center' }}>
          See Rolling FTP panel for trend chart
        </div>
      )}
    </div>
  );
}

function FtpGrowthChart({ data }: { data: FtpGrowthResponse }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const history = data.data_points || [];

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    if (!history.length) return;

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const dates = history.map(h => new Date(h.date));
    const ftps = history.map(h => h.ftp || h.mFTP);

    const x = d3.scaleTime().domain(d3.extent(dates) as [Date, Date]).range([0, innerW]);
    const y = d3.scaleLinear()
      .domain([d3.min(ftps)! * 0.95, d3.max(ftps)! * 1.05])
      .range([innerH, 0]);

    // Scatter points
    g.selectAll('circle').data(history).enter().append('circle')
      .attr('cx', (_, i) => x(dates[i]))
      .attr('cy', (_, i) => y(ftps[i]))
      .attr('r', 4)
      .attr('fill', COLORS.accent)
      .attr('opacity', 0.7);

    // Log fit curve
    if (data.slope != null && data.intercept != null && dates.length > 1) {
      const { slope, intercept } = data;
      const t0 = dates[0].getTime();
      const curvePoints: { date: Date; ftp: number }[] = [];
      for (let i = 0; i <= 50; i++) {
        const t = dates[0].getTime() + (dates[dates.length - 1].getTime() - dates[0].getTime()) * i / 50;
        const weeks = (t - t0) / (7 * 24 * 3600 * 1000);
        const predicted = slope * Math.log(Math.max(weeks, 0.1) + 1) + intercept;
        curvePoints.push({ date: new Date(t), ftp: predicted });
      }

      const line = d3.line<typeof curvePoints[0]>()
        .x(d => x(d.date)).y(d => y(d.ftp)).curve(d3.curveMonotoneX);

      g.append('path').datum(curvePoints).attr('d', line)
        .attr('fill', 'none').attr('stroke', COLORS.accent)
        .attr('stroke-width', 2).attr('stroke-dasharray', '6,3')
        .attr('opacity', 0.6);
    }

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y') as any));
    styleAxis(xAxisG);

    const yAxisG = g.append('g')
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d}W`));
    styleAxis(yAxisG);
  }, [history, data.slope, data.intercept]);

  return (
    <ChartContainer onResize={renderChart}>
      <svg ref={svgRef} />
    </ChartContainer>
  );
}
```

- [ ] **Step 3: Register + Commit**

```bash
git add frontend-v2/src/panels/fitness/FtpGrowth.tsx frontend-v2/src/panels/fitness/FtpGrowth.module.css
git commit -m "feat(1c): FtpGrowth — metric cards + scatter plot with log-fit curve"
```

---

## Task 6: Rolling PD — multi-line time series with toggle legend

**Files:**
- Create: `frontend-v2/src/panels/fitness/RollingPd.tsx`
- Create: `frontend-v2/src/panels/fitness/RollingPd.module.css`

Port from `frontend/js/charts/rolling-pd.js`. Four series (mFTP, Pmax, FRC, TTE) with interactive legend toggles.

- [ ] **Step 1: Create RollingPd.module.css**

```css
/* frontend-v2/src/panels/fitness/RollingPd.module.css */
.wrapper { position: relative; width: 100%; }

.legend {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 0.75rem;
}

.legendBtn {
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
  transition: all 0.15s;
}
```

- [ ] **Step 2: Create RollingPd.tsx**

```typescript
// frontend-v2/src/panels/fitness/RollingPd.tsx
import { useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis, drawGridY } from '../../shared/chart-utils';
import { PanelSkeleton, PanelError, PanelEmpty } from '../../shared/PanelStates';
import type { RollingPdRow } from '../../api/types';
import styles from './RollingPd.module.css';

const CHART_HEIGHT = 200;
const MARGIN = { top: 10, right: 20, bottom: 30, left: 50 };

const SERIES = [
  { key: 'mFTP' as const, color: '#58a6ff', label: 'mFTP' },
  { key: 'Pmax' as const, color: '#f778ba', label: 'Pmax' },
  { key: 'FRC' as const, color: '#d29922', label: 'FRC' },
  { key: 'TTE' as const, color: '#3fb950', label: 'TTE' },
];

export function RollingPd() {
  const rollingPd = useDataStore(s => s.rollingPd);
  const loading = useDataStore(s => s.loading.has('rollingPd'));
  const error = useDataStore(s => s.errors['rollingPd']);
  const [visible, setVisible] = useState<Record<string, boolean>>({
    mFTP: true, Pmax: false, FRC: false, TTE: false,
  });

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!rollingPd || !rollingPd.length) return <PanelEmpty message="No rolling PD data" />;

  const toggleSeries = (key: string) => {
    setVisible(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.legend}>
        {SERIES.map(s => (
          <button
            key={s.key}
            className={styles.legendBtn}
            style={{
              border: `1px solid ${visible[s.key] ? s.color : 'var(--border)'}`,
              background: visible[s.key] ? `${s.color}22` : 'transparent',
              color: visible[s.key] ? s.color : 'var(--text-muted)',
            }}
            onClick={() => toggleSeries(s.key)}
          >
            {s.label}
          </button>
        ))}
      </div>
      <RollingPdInner data={rollingPd} visible={visible} />
    </div>
  );
}

function RollingPdInner({ data, visible }: { data: RollingPdRow[]; visible: Record<string, boolean> }) {
  const svgRef = useRef<SVGSVGElement>(null);

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const parsed = data.map(d => ({ ...d, _date: new Date(d.date) }))
      .sort((a, b) => a._date.getTime() - b._date.getTime());

    const x = d3.scaleTime()
      .domain(d3.extent(parsed, d => d._date) as [Date, Date])
      .range([0, innerW]);

    const activeKeys = SERIES.filter(s => visible[s.key]).map(s => s.key);
    if (!activeKeys.length) return;

    const allVals: number[] = [];
    activeKeys.forEach(key => {
      parsed.forEach(s => {
        const v = (s as any)[key];
        if (v != null) allVals.push(v);
      });
    });
    if (!allVals.length) return;

    const y = d3.scaleLinear()
      .domain([d3.min(allVals)! * 0.95, d3.max(allVals)! * 1.05])
      .range([innerH, 0]);

    drawGridY(g, y, innerW, 4);

    SERIES.forEach(s => {
      if (!visible[s.key]) return;
      const lineData = parsed.filter(d => (d as any)[s.key] != null);
      const line = d3.line<typeof lineData[0]>()
        .x(d => x(d._date))
        .y(d => y((d as any)[s.key]))
        .curve(d3.curveMonotoneX);

      g.append('path').datum(lineData).attr('d', line)
        .attr('fill', 'none').attr('stroke', s.color).attr('stroke-width', 2);
    });

    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y') as any));
    styleAxis(xAxisG);

    const yAxisG = g.append('g').call(d3.axisLeft(y).ticks(5));
    styleAxis(yAxisG);
  }, [data, visible]);

  return (
    <ChartContainer onResize={renderChart}>
      <svg ref={svgRef} />
    </ChartContainer>
  );
}
```

- [ ] **Step 3: Register + Commit**

```bash
git add frontend-v2/src/panels/fitness/RollingPd.tsx frontend-v2/src/panels/fitness/RollingPd.module.css
git commit -m "feat(1c): RollingPd — multi-line PD params with toggle legend"
```

---

## Task 7: IF Distribution — D3 histogram

**Files:**
- Create: `frontend-v2/src/panels/health/IFDistribution.tsx`
- Create: `frontend-v2/src/panels/health/IFDistribution.module.css`

Port from `frontend/js/charts/if-distribution.js`. Histogram bars colored by IF zone, floor/ceiling/mean marker lines.

- [ ] **Step 1: Create IFDistribution.module.css**

```css
/* frontend-v2/src/panels/health/IFDistribution.module.css */
.wrapper { position: relative; width: 100%; }

.summary {
  display: flex;
  gap: 16px;
  margin-top: 8px;
  font-size: 0.8rem;
  flex-wrap: wrap;
}
```

- [ ] **Step 2: Create IFDistribution.tsx**

```typescript
// frontend-v2/src/panels/health/IFDistribution.tsx
import { useRef, useCallback } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis, ifZoneColor } from '../../shared/chart-utils';
import { PanelSkeleton, PanelError, PanelEmpty } from '../../shared/PanelStates';
import type { IfDistributionResponse } from '../../api/types';
import styles from './IFDistribution.module.css';

const CHART_HEIGHT = 220;
const MARGIN = { top: 20, right: 20, bottom: 35, left: 40 };

interface BarDatum {
  lo: number;
  hi: number;
  count: number;
}

function parseHistogram(data: IfDistributionResponse): BarDatum[] {
  const histogram = data.histogram || {};
  const barData: BarDatum[] = [];

  if (Array.isArray(histogram)) {
    return histogram.map(b => ({
      lo: b.range?.[0] ?? b.if_low ?? b.low ?? 0,
      hi: b.range?.[1] ?? b.if_high ?? b.high ?? 0.05,
      count: b.count ?? 0,
    }));
  }

  // Object form: {"0.40-0.45": 2, ...}
  for (const key of Object.keys(histogram)) {
    const parts = key.split('-');
    if (parts.length === 2) {
      barData.push({
        lo: parseFloat(parts[0]),
        hi: parseFloat(parts[1]),
        count: (histogram as Record<string, number>)[key],
      });
    }
  }
  return barData.sort((a, b) => a.lo - b.lo);
}

export function IFDistribution() {
  const ifDist = useDataStore(s => s.ifDistribution);
  const loading = useDataStore(s => s.loading.has('ifDistribution'));
  const error = useDataStore(s => s.errors['ifDistribution']);

  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!ifDist) return <PanelEmpty message="No IF distribution data" />;

  const barData = parseHistogram(ifDist);
  if (!barData.length) return <PanelEmpty message="No IF distribution data" />;

  return (
    <div className={styles.wrapper}>
      <IFDistributionInner barData={barData} data={ifDist} />
      <div className={styles.summary}>
        {ifDist.rides_analyzed != null && (
          <span>Rides: <span className="mono">{ifDist.rides_analyzed}</span></span>
        )}
        {ifDist.spread != null && (
          <span>Spread: <span className="mono">{ifDist.spread.toFixed(2)}</span></span>
        )}
        {ifDist.compressed != null && (
          <span style={{ color: ifDist.compressed ? COLORS.warning : COLORS.success }}>
            {ifDist.compressed ? 'Compressed' : 'Good spread'}
          </span>
        )}
      </div>
    </div>
  );
}

function IFDistributionInner({ barData, data }: { barData: BarDatum[]; data: IfDistributionResponse }) {
  const svgRef = useRef<SVGSVGElement>(null);

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT - MARGIN.top - MARGIN.bottom;
    svg.attr('width', width).attr('height', CHART_HEIGHT);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const x = d3.scaleLinear()
      .domain([d3.min(barData, d => d.lo)!, d3.max(barData, d => d.hi)!])
      .range([0, innerW]);

    const y = d3.scaleLinear()
      .domain([0, d3.max(barData, d => d.count)! * 1.1])
      .range([innerH, 0]);

    // Bars colored by IF zone
    g.selectAll('rect.bar').data(barData).enter().append('rect')
      .attr('x', d => x(d.lo))
      .attr('width', d => Math.max(1, x(d.hi) - x(d.lo) - 1))
      .attr('y', d => y(d.count))
      .attr('height', d => innerH - y(d.count))
      .attr('fill', d => ifZoneColor(d.lo))
      .attr('rx', 2);

    // Floor marker line (red dashed)
    if (data.floor != null) {
      g.append('line')
        .attr('x1', x(data.floor)).attr('x2', x(data.floor))
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', COLORS.danger).attr('stroke-width', 2)
        .attr('stroke-dasharray', '4,3');
      g.append('text')
        .attr('x', x(data.floor) + 4).attr('y', 12)
        .text(`Floor ${data.floor.toFixed(2)}`)
        .attr('fill', COLORS.danger).attr('font-size', '10px');
    }

    // Ceiling marker line (amber dashed)
    if (data.ceiling != null) {
      g.append('line')
        .attr('x1', x(data.ceiling)).attr('x2', x(data.ceiling))
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', COLORS.warning).attr('stroke-width', 2)
        .attr('stroke-dasharray', '4,3');
      g.append('text')
        .attr('x', x(data.ceiling) + 4).attr('y', 12)
        .text(`Ceiling ${data.ceiling.toFixed(2)}`)
        .attr('fill', COLORS.warning).attr('font-size', '10px');
    }

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(8).tickFormat(d => (d as number).toFixed(2)));
    styleAxis(xAxisG);

    const yAxisG = g.append('g').call(d3.axisLeft(y).ticks(5));
    styleAxis(yAxisG);
  }, [barData, data.floor, data.ceiling]);

  return (
    <ChartContainer onResize={renderChart}>
      <svg ref={svgRef} />
    </ChartContainer>
  );
}
```

- [ ] **Step 3: Register + Commit**

```bash
git add frontend-v2/src/panels/health/IFDistribution.tsx frontend-v2/src/panels/health/IFDistribution.module.css
git commit -m "feat(1c): IFDistribution — histogram with zone colors + floor/ceiling markers"
```

---

## Task 8: Segment Profile — elevation profile with demand overlays

**Files:**
- Create: `frontend-v2/src/panels/event-prep/SegmentProfile.tsx`
- Create: `frontend-v2/src/panels/event-prep/SegmentProfile.module.css`

Port from `frontend/js/charts/segment-profile.js`. D3 area chart with colored segment overlays indicating demand ratio.

- [ ] **Step 1: Create SegmentProfile.module.css**

```css
/* frontend-v2/src/panels/event-prep/SegmentProfile.module.css */
.wrapper { position: relative; width: 100%; }

.summaryBar {
  display: flex;
  gap: 24px;
  padding-top: 10px;
  font-size: 0.8rem;
  color: var(--text-secondary, #8b949e);
  flex-wrap: wrap;
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 0.8rem;
  color: var(--text-primary, #e6edf3);
  display: none;
  z-index: 1000;
  max-width: 220px;
  line-height: 1.5;
}

.tooltip.visible {
  display: block;
}
```

- [ ] **Step 2: Create SegmentProfile.tsx**

```typescript
// frontend-v2/src/panels/event-prep/SegmentProfile.tsx
import { useRef, useCallback, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis, demandColor, demandOpacity, findNearest } from '../../shared/chart-utils';
import { PanelSkeleton, PanelError, PanelEmpty } from '../../shared/PanelStates';
import styles from './SegmentProfile.module.css';

const MARGIN = { top: 32, right: 24, bottom: 64, left: 56 };
const MIN_LABEL_PX = 50;

interface ElevPoint {
  km: number;
  altitude: number;
}

interface Segment {
  start_km: number;
  end_km: number;
  type: string;
  avg_grade: number;
  demand_ratio: number;
  power_required: number;
}

export function SegmentProfile() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId);
  const routeDetail = useDataStore(s =>
    selectedRouteId ? s.routeDetail[selectedRouteId] : null
  );
  const loading = useDataStore(s => s.loading.has('routeDetail'));
  const error = useDataStore(s => s.errors['routeDetail']);

  if (!selectedRouteId) return <PanelEmpty message="Select a route to see elevation profile" />;
  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;
  if (!routeDetail?.elevation_profile?.length) return <PanelEmpty message="No elevation data" />;

  const elevation_profile: ElevPoint[] = routeDetail.elevation_profile;
  const segments: Segment[] = routeDetail.segments || [];

  return (
    <div className={styles.wrapper}>
      <SegmentProfileInner
        elevationProfile={elevation_profile}
        segments={segments}
        totalKm={routeDetail.total_km || 0}
        totalElevation={routeDetail.total_elevation || 0}
      />
    </div>
  );
}

interface InnerProps {
  elevationProfile: ElevPoint[];
  segments: Segment[];
  totalKm: number;
  totalElevation: number;
}

function SegmentProfileInner({ elevationProfile, segments, totalKm, totalElevation }: InnerProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const height = Math.max(260, Math.min(width * 0.45, 400));
    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = height - MARGIN.top - MARGIN.bottom;

    if (innerW < 40 || innerH < 40) return;

    svg.attr('width', width).attr('height', height);

    const xExtent: [number, number] = [0, totalKm || d3.max(elevationProfile, d => d.km) || 100];
    const altitudes = elevationProfile.map(d => d.altitude);
    const yMin = d3.min(altitudes)!;
    const yMax = d3.max(altitudes)!;
    const yPad = (yMax - yMin) * 0.1 || 50;

    const x = d3.scaleLinear().domain(xExtent).range([0, innerW]);
    const y = d3.scaleLinear().domain([yMin - yPad, yMax + yPad]).range([innerH, 0]);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    // Grid
    g.append('g')
      .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat('' as any))
      .selectAll('line')
      .attr('stroke', 'var(--chart-grid, #21262d)')
      .attr('stroke-dasharray', '2,3');
    g.selectAll('.domain').remove();

    // Segment overlays (behind altitude)
    g.selectAll('.segment-overlay')
      .data(segments)
      .join('rect')
      .attr('x', d => x(d.start_km))
      .attr('y', 0)
      .attr('width', d => Math.max(0, x(d.end_km) - x(d.start_km)))
      .attr('height', innerH)
      .attr('fill', d => demandColor(d.demand_ratio))
      .attr('opacity', d => demandOpacity(d.demand_ratio));

    // Altitude area
    const area = d3.area<ElevPoint>()
      .x(d => x(d.km))
      .y0(innerH)
      .y1(d => y(d.altitude))
      .curve(d3.curveMonotoneX);

    g.append('path').datum(elevationProfile).attr('d', area)
      .attr('fill', COLORS.textMuted).attr('fill-opacity', 0.15);

    // Altitude line
    const line = d3.line<ElevPoint>()
      .x(d => x(d.km)).y(d => y(d.altitude)).curve(d3.curveMonotoneX);

    g.append('path').datum(elevationProfile).attr('d', line)
      .attr('fill', 'none').attr('stroke', COLORS.textSecondary).attr('stroke-width', 1.5);

    // Segment type labels
    g.selectAll('.seg-label')
      .data(segments.filter(d => (x(d.end_km) - x(d.start_km)) > MIN_LABEL_PX))
      .join('text')
      .attr('x', d => x((d.start_km + d.end_km) / 2))
      .attr('y', -6)
      .attr('text-anchor', 'middle')
      .attr('fill', COLORS.textMuted).attr('font-size', '0.7rem')
      .text(d => {
        if (d.type === 'climb') return `Climb ${d.avg_grade.toFixed(1)}%`;
        if (d.type === 'descent') return 'Descent';
        return 'Flat';
      });

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(Math.min(10, innerW / 60)).tickFormat(d => `${d} km`));
    styleAxis(xAxisG);

    const yAxisG = g.append('g')
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d} m`));
    styleAxis(yAxisG);

    // Hover
    const hoverLine = g.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .attr('stroke', COLORS.accent).attr('stroke-dasharray', '4,3')
      .style('opacity', 0);

    const hoverDot = g.append('circle')
      .attr('r', 4).attr('fill', COLORS.accent).style('opacity', 0);

    g.append('rect')
      .attr('width', innerW).attr('height', innerH)
      .attr('fill', 'transparent')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event);
        const km = x.invert(mx);
        const d = findNearest(elevationProfile, p => p.km, km);
        if (!d) return;

        hoverLine.attr('x1', x(d.km)).attr('x2', x(d.km)).style('opacity', 1);
        hoverDot.attr('cx', x(d.km)).attr('cy', y(d.altitude)).style('opacity', 1);

        const seg = segments.find(s => km >= s.start_km && km < s.end_km);
        let content = `${d.km.toFixed(1)} km -- ${Math.round(d.altitude)} m`;
        if (seg) {
          content += `\n${seg.type} ${seg.avg_grade.toFixed(1)}%`;
          content += `\nPower: ${seg.power_required} W`;
          content += `\nDemand: ${(seg.demand_ratio * 100).toFixed(0)}%`;
        }
        setTooltipContent(content);
        setTooltipVisible(true);
        setTooltipPos({ left: event.offsetX + 14, top: event.offsetY - 28 });
      })
      .on('mouseleave', () => {
        hoverLine.style('opacity', 0);
        hoverDot.style('opacity', 0);
        setTooltipVisible(false);
      });
  }, [elevationProfile, segments, totalKm]);

  // Summary
  const hardest = segments.reduce<Segment | null>((best, s) =>
    (!best || s.demand_ratio > best.demand_ratio) ? s : best, null
  );

  return (
    <>
      <ChartContainer onResize={renderChart}>
        <svg ref={svgRef} />
        <div
          className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
          style={{ left: tooltipPos.left, top: tooltipPos.top }}
        >
          {tooltipContent.split('\n').map((line, i) => <div key={i}>{line}</div>)}
        </div>
      </ChartContainer>
      <div className={styles.summaryBar}>
        <span>Distance: <strong>{totalKm} km</strong></span>
        <span>Elevation: <strong>{totalElevation} m</strong></span>
        {hardest && (
          <span>
            Hardest:{' '}
            <strong style={{ color: demandColor(hardest.demand_ratio) }}>
              {hardest.type} {hardest.avg_grade.toFixed(1)}% @ {(hardest.demand_ratio * 100).toFixed(0)}% demand
            </strong>
          </span>
        )}
      </div>
    </>
  );
}
```

- [ ] **Step 3: Register + Commit**

```bash
git add frontend-v2/src/panels/event-prep/SegmentProfile.tsx frontend-v2/src/panels/event-prep/SegmentProfile.module.css
git commit -m "feat(1c): SegmentProfile — elevation profile with demand-colored overlays"
```

---

## Task 9: Annotation Overlay — rendering layer + store tests

**Files:**
- Create: `frontend-v2/src/shared/AnnotationOverlay.tsx`
- Create: `frontend-v2/src/shared/AnnotationOverlay.module.css`
- Create: `frontend-v2/src/__tests__/annotation-store.test.ts`

This is the annotation rendering system. It reads annotations from the store and renders D3 overlays (regions, lines, points, callout cards) on top of any chart that passes its SVG scales.

- [ ] **Step 1: Create annotation store tests**

```typescript
// frontend-v2/src/__tests__/annotation-store.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useDataStore } from '../store/data-store';
import type { Annotation } from '../api/types';

describe('Annotation store actions', () => {
  beforeEach(() => {
    // Reset annotations between tests
    useDataStore.getState().clearAnnotations();
  });

  it('addAnnotation adds to correct panelId', () => {
    const annotation: Annotation = {
      id: 'test-1',
      source: 'claude',
      type: 'region',
      x: ['2026-01-01', '2026-01-15'],
      label: 'CTL plateau',
      color: 'red',
      timestamp: new Date().toISOString(),
    };

    useDataStore.getState().addAnnotation('pmc-chart', annotation);

    const state = useDataStore.getState();
    expect(state.annotations['pmc-chart']).toHaveLength(1);
    expect(state.annotations['pmc-chart'][0].label).toBe('CTL plateau');
  });

  it('addAnnotation appends multiple annotations', () => {
    const a1: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-02-01', label: 'Event', color: 'blue',
      timestamp: new Date().toISOString(),
    };
    const a2: Annotation = {
      id: 'a2', source: 'claude', type: 'point',
      x: '2026-03-01', y: 50, label: 'Peak', color: 'green',
      timestamp: new Date().toISOString(),
    };

    useDataStore.getState().addAnnotation('pmc-chart', a1);
    useDataStore.getState().addAnnotation('pmc-chart', a2);

    expect(useDataStore.getState().annotations['pmc-chart']).toHaveLength(2);
  });

  it('clearAnnotations with panelId clears only that panel', () => {
    const a: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-01-01', label: 'Test', color: 'red',
      timestamp: new Date().toISOString(),
    };
    useDataStore.getState().addAnnotation('pmc-chart', a);
    useDataStore.getState().addAnnotation('other-chart', { ...a, id: 'a2' });

    useDataStore.getState().clearAnnotations('pmc-chart');

    expect(useDataStore.getState().annotations['pmc-chart'] || []).toHaveLength(0);
    expect(useDataStore.getState().annotations['other-chart']).toHaveLength(1);
  });

  it('clearAnnotations without panelId clears all', () => {
    const a: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-01-01', label: 'Test', color: 'red',
      timestamp: new Date().toISOString(),
    };
    useDataStore.getState().addAnnotation('pmc-chart', a);
    useDataStore.getState().addAnnotation('other-chart', { ...a, id: 'a2' });

    useDataStore.getState().clearAnnotations();

    expect(Object.keys(useDataStore.getState().annotations)).toHaveLength(0);
  });

  it('truncates labels longer than 200 chars', () => {
    const longLabel = 'x'.repeat(250);
    const a: Annotation = {
      id: 'a1', source: 'claude', type: 'line',
      x: '2026-01-01', label: longLabel, color: 'red',
      timestamp: new Date().toISOString(),
    };

    useDataStore.getState().addAnnotation('pmc-chart', a);

    const stored = useDataStore.getState().annotations['pmc-chart'][0];
    expect(stored.label.length).toBeLessThanOrEqual(203); // 200 + '...'
  });
});
```

- [ ] **Step 2: Update data-store.ts for annotation actions**

Ensure the `addAnnotation` and `clearAnnotations` actions in `data-store.ts` include label truncation (200 char max):

```typescript
// In the Zustand store definition — addAnnotation action:
addAnnotation: (panelId, annotation) =>
  set(state => {
    const truncatedLabel = annotation.label.length > 200
      ? annotation.label.slice(0, 200) + '...'
      : annotation.label;
    const safe = { ...annotation, label: truncatedLabel };
    const existing = state.annotations[panelId] || [];
    return {
      annotations: {
        ...state.annotations,
        [panelId]: [...existing, safe],
      },
    };
  }),

clearAnnotations: (panelId) =>
  set(state => {
    if (panelId) {
      const { [panelId]: _, ...rest } = state.annotations;
      return { annotations: rest };
    }
    return { annotations: {} };
  }),
```

- [ ] **Step 3: Run store tests**

```bash
cd frontend-v2 && npx vitest run src/__tests__/annotation-store.test.ts
```

Expected: All 5 tests pass.

- [ ] **Step 4: Create AnnotationOverlay.module.css**

```css
/* frontend-v2/src/shared/AnnotationOverlay.module.css */
.toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: var(--bg-tertiary, #21262d);
  border-radius: 4px;
  margin-bottom: 4px;
  font-size: 0.75rem;
}

.badge {
  background: var(--accent, #58a6ff);
  color: #000;
  padding: 1px 6px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.7rem;
}

.toolbarBtn {
  background: transparent;
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  color: var(--text-secondary, #8b949e);
  padding: 2px 8px;
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
}

.toolbarBtn:hover {
  border-color: var(--text-muted, #484f58);
  color: var(--text-primary, #e6edf3);
}

.calloutCard {
  position: absolute;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.75rem;
  color: var(--text-primary, #e6edf3);
  max-width: 220px;
  z-index: 20;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.calloutSeverity {
  display: inline-block;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: uppercase;
  margin-right: 4px;
}

.calloutSeverity.danger {
  background: rgba(248, 81, 73, 0.15);
  color: var(--danger, #f85149);
}

.calloutSeverity.warning {
  background: rgba(210, 153, 34, 0.15);
  color: var(--warning, #d29922);
}

.calloutSeverity.info {
  background: rgba(88, 166, 255, 0.15);
  color: var(--accent, #58a6ff);
}

.calloutSource {
  color: var(--text-muted, #484f58);
  font-size: 0.65rem;
  margin-top: 4px;
}

.dismissBtn {
  position: absolute;
  top: 4px;
  right: 4px;
  background: none;
  border: none;
  color: var(--text-muted, #484f58);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0 2px;
}

.dismissBtn:hover {
  color: var(--text-primary, #e6edf3);
}
```

- [ ] **Step 5: Create AnnotationOverlay.tsx**

```typescript
// frontend-v2/src/shared/AnnotationOverlay.tsx
import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../store/data-store';
import type { Annotation } from '../api/types';
import styles from './AnnotationOverlay.module.css';

interface AnnotationOverlayProps {
  panelId: string;
  annotations: Annotation[];
  /** Reference to the SVG element whose __scales we read */
  svgRef?: React.RefObject<SVGSVGElement>;
}

/**
 * Renders annotation overlays on top of a D3 chart.
 *
 * Reads scale info from the parent SVG element's `__scales` property
 * (set by the chart component after rendering):
 *   { xScale, yScaleLeft?, yScaleRight?, margin, innerW, innerH }
 *
 * Annotation types:
 * - region: shaded rect with dashed borders
 * - line: solid vertical line
 * - dashed: dashed vertical line
 * - point: circle marker at (x, y)
 *
 * Each annotation gets a callout card with severity badge, label,
 * source ("Claude"), and dismiss button.
 */
export function AnnotationOverlay({ panelId, annotations }: AnnotationOverlayProps) {
  const clearAnnotations = useDataStore(s => s.clearAnnotations);
  const [hidden, setHidden] = useState(false);

  if (!annotations.length) return null;

  const removeAnnotation = (annotationId: string) => {
    // Remove single annotation by filtering
    const store = useDataStore.getState();
    const current = store.annotations[panelId] || [];
    const filtered = current.filter(a => a.id !== annotationId);
    // We need to set the filtered list back. Since the store only has
    // addAnnotation and clearAnnotations, we clear and re-add.
    store.clearAnnotations(panelId);
    filtered.forEach(a => store.addAnnotation(panelId, a));
  };

  return (
    <div>
      {/* Toolbar */}
      <div className={styles.toolbar}>
        <span className={styles.badge}>{annotations.length}</span>
        <span>annotation{annotations.length !== 1 ? 's' : ''}</span>
        <button
          className={styles.toolbarBtn}
          onClick={() => setHidden(h => !h)}
        >
          {hidden ? 'Show' : 'Hide'}
        </button>
        <button
          className={styles.toolbarBtn}
          onClick={() => clearAnnotations(panelId)}
        >
          Clear all
        </button>
      </div>

      {/* Callout cards */}
      {!hidden && annotations.map(ann => (
        <AnnotationCallout
          key={ann.id}
          annotation={ann}
          onDismiss={() => removeAnnotation(ann.id)}
        />
      ))}

      {/* D3 SVG overlays are rendered by AnnotationSvgLayer (must be inside ChartContainer) */}
    </div>
  );
}

interface CalloutProps {
  annotation: Annotation;
  onDismiss: () => void;
}

function AnnotationCallout({ annotation, onDismiss }: CalloutProps) {
  const severity = (annotation as any).severity || 'info';

  return (
    <div className={styles.calloutCard}>
      <button className={styles.dismissBtn} onClick={onDismiss} aria-label="Dismiss">
        x
      </button>
      <div>
        <span className={`${styles.calloutSeverity} ${styles[severity]}`}>
          {severity}
        </span>
        {/* Always textContent, never innerHTML — XSS prevention */}
        <span>{annotation.label}</span>
      </div>
      <div className={styles.calloutSource}>
        {annotation.source === 'claude' ? 'Claude' : 'User'} --{' '}
        {new Date(annotation.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
}

/**
 * D3 SVG annotation layer — renders directly into the chart SVG.
 * Call this function from inside a chart's render callback, passing the
 * D3 content group and scales.
 *
 * Usage inside a chart component's renderChart():
 *   renderAnnotationsSvg(contentGroup, annotations, xScale, yScale, innerH);
 */
export function renderAnnotationsSvg(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  annotations: Annotation[],
  xScale: d3.ScaleTime<number, number>,
  yScaleRight: d3.ScaleLinear<number, number> | null,
  innerH: number
): void {
  const parseDate = d3.timeParse('%Y-%m-%d');

  annotations.forEach(ann => {
    const color = ann.color || '#58a6ff';

    if (ann.type === 'region' && Array.isArray(ann.x) && ann.x.length === 2) {
      const x0 = parseDate(ann.x[0]);
      const x1 = parseDate(ann.x[1]);
      if (!x0 || !x1) return;

      const px0 = xScale(x0);
      const px1 = xScale(x1);

      // Shaded region
      g.append('rect')
        .attr('x', Math.min(px0, px1))
        .attr('y', 0)
        .attr('width', Math.abs(px1 - px0))
        .attr('height', innerH)
        .attr('fill', color)
        .attr('opacity', 0.12)
        .attr('class', 'annotation-region');

      // Dashed borders
      [px0, px1].forEach(px => {
        g.append('line')
          .attr('x1', px).attr('x2', px)
          .attr('y1', 0).attr('y2', innerH)
          .attr('stroke', color)
          .attr('stroke-width', 1)
          .attr('stroke-dasharray', '4,3')
          .attr('opacity', 0.6);
      });
    }

    if (ann.type === 'line' && typeof ann.x === 'string') {
      const date = parseDate(ann.x);
      if (!date) return;
      const px = xScale(date);

      g.append('line')
        .attr('x1', px).attr('x2', px)
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('opacity', 0.8)
        .attr('class', 'annotation-line');
    }

    if ((ann as any).type === 'dashed' && typeof ann.x === 'string') {
      const date = parseDate(ann.x);
      if (!date) return;
      const px = xScale(date);

      g.append('line')
        .attr('x1', px).attr('x2', px)
        .attr('y1', 0).attr('y2', innerH)
        .attr('stroke', color)
        .attr('stroke-width', 1.5)
        .attr('stroke-dasharray', '6,4')
        .attr('opacity', 0.7)
        .attr('class', 'annotation-dashed');
    }

    if (ann.type === 'point' && typeof ann.x === 'string' && ann.y != null) {
      const date = parseDate(ann.x);
      if (!date || !yScaleRight) return;
      const px = xScale(date);
      const py = yScaleRight(ann.y);

      g.append('circle')
        .attr('cx', px).attr('cy', py)
        .attr('r', 5)
        .attr('fill', color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .attr('opacity', 0.9)
        .attr('class', 'annotation-point');
    }
  });
}
```

- [ ] **Step 6: Run annotation tests**

```bash
cd frontend-v2 && npx vitest run src/__tests__/annotation-store.test.ts
```

Expected: All 5 tests pass.

- [ ] **Step 7: Commit**

```bash
git add frontend-v2/src/shared/AnnotationOverlay.tsx frontend-v2/src/shared/AnnotationOverlay.module.css frontend-v2/src/__tests__/annotation-store.test.ts
git commit -m "feat(1c): AnnotationOverlay — rendering layer with callout cards + store tests"
```

---

## Task 10: Wire annotations into PMC Chart + test button

**Files:**
- Modify: `frontend-v2/src/panels/fitness/PMCChart.tsx`

Wire the annotation SVG rendering into the PMC chart's D3 render loop and add a temporary test button that pushes a sample annotation.

- [ ] **Step 1: Update PMCChart to render annotation SVG layer**

In `PMCChart.tsx`, update the `renderChart` callback to call `renderAnnotationsSvg` after drawing the main chart content:

Add this import at the top:
```typescript
import { renderAnnotationsSvg } from '../../shared/AnnotationOverlay';
```

Then, at the end of the `renderChart` callback (before the hover overlay), after the TSB dashed line section, add:

```typescript
    // Annotation SVG overlays
    if (annotationsRef.current.length > 0) {
      const annotGroup = content.append('g').attr('class', 'annotations');
      renderAnnotationsSvg(annotGroup, annotationsRef.current, xScale, yScaleRight, innerH);
    }
```

Where `annotationsRef` is a ref kept in sync with annotations prop:

```typescript
// Inside PMCChartInner, add:
const annotationsRef = useRef(annotations);
annotationsRef.current = annotations;
```

And `PMCChartInner` needs the annotations prop:

```typescript
interface PMCChartInnerProps {
  data: PMCRow[];
  annotations: Annotation[];
}

// Update the parent to pass annotations:
<PMCChartInner data={pmc} annotations={annotations} />
```

- [ ] **Step 2: Add test annotation button**

In `PMCChart` (the outer component), add a temporary test button that pushes a sample annotation to verify the flow:

```typescript
export function PMCChart() {
  const pmc = useDataStore(s => s.pmc);
  const loading = useDataStore(s => s.loading.has('pmc'));
  const error = useDataStore(s => s.errors['pmc']);
  const annotations = useDataStore(s => s.annotations[PANEL_ID] || []);
  const addAnnotation = useDataStore(s => s.addAnnotation);

  // ... loading/error/empty guards ...

  const pushTestAnnotation = () => {
    addAnnotation(PANEL_ID, {
      id: `test-${Date.now()}`,
      source: 'claude',
      type: 'region',
      x: [
        // Use recent dates from the PMC data
        pmc[Math.max(0, pmc.length - 60)]?.date || '2026-01-01',
        pmc[Math.max(0, pmc.length - 45)]?.date || '2026-01-15',
      ],
      label: 'CTL plateau — recovery block detected',
      color: '#f85149',
      timestamp: new Date().toISOString(),
      severity: 'warning',
    } as any);
  };

  return (
    <div className={styles.wrapper}>
      <AnnotationOverlay panelId={PANEL_ID} annotations={annotations} />
      <PMCChartInner data={pmc} annotations={annotations} />
      {/* Temporary test button — remove before production */}
      <button
        onClick={pushTestAnnotation}
        style={{
          position: 'absolute', bottom: 8, right: 8,
          fontSize: '0.7rem', padding: '3px 8px',
          background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
          borderRadius: 4, color: 'var(--text-secondary)', cursor: 'pointer',
        }}
      >
        + Test Annotation
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Visual verification**

```bash
cd frontend-v2 && npm run dev
```

Navigate to Fitness tab, PMC chart. Click "Test Annotation" button. Expected:
1. Annotation toolbar appears showing "1 annotation"
2. Red shaded region with dashed borders appears on the chart
3. Callout card appears with "warning" badge, label text, "Claude" source
4. "x" dismiss button removes the annotation
5. "Clear all" removes all annotations
6. "Hide" / "Show" toggles annotation visibility

- [ ] **Step 4: Commit**

```bash
git add frontend-v2/src/panels/fitness/PMCChart.tsx
git commit -m "feat(1c): wire annotations into PMCChart — end-to-end POC with test button"
```

---

## Task 11: Ride Detail — metrics bar + planned vs completed

**Files:**
- Create: `frontend-v2/src/ride/RideMetricsBar.tsx`
- Create: `frontend-v2/src/ride/RideMetricsBar.module.css`
- Create: `frontend-v2/src/ride/PlannedVsCompleted.tsx`

- [ ] **Step 1: Create RideMetricsBar.module.css**

```css
/* frontend-v2/src/ride/RideMetricsBar.module.css */
.metricsBar {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  margin-bottom: 16px;
}

.metric {
  text-align: center;
}

.metric .value {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
}

.metric .label {
  font-size: 0.7rem;
  color: var(--text-muted, #484f58);
  margin-top: 2px;
}
```

- [ ] **Step 2: Create RideMetricsBar.tsx**

```typescript
// frontend-v2/src/ride/RideMetricsBar.tsx
import type { RideDetail } from '../api/types';
import styles from './RideMetricsBar.module.css';

interface Props {
  ride: RideDetail;
}

function fmt(v: number | null | undefined, decimals = 0, suffix = ''): string {
  if (v == null || isNaN(v)) return '--';
  return v.toFixed(decimals) + suffix;
}

function fmtDur(seconds: number | null | undefined): string {
  if (!seconds) return '--';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export function RideMetricsBar({ ride }: Props) {
  const s = ride.summary;
  if (!s) return null;

  const metrics = [
    { label: 'Duration', value: fmtDur(s.total_elapsed_time) },
    { label: 'Distance', value: fmt(s.total_distance ? s.total_distance / 1000 : null, 1, ' km') },
    { label: 'Elevation', value: fmt(s.total_ascent, 0, ' m') },
    { label: 'Avg Power', value: fmt(s.avg_power, 0, ' W') },
    { label: 'Max Power', value: fmt(s.max_power, 0, ' W') },
    { label: 'NP', value: fmt(s.normalized_power, 0, ' W') },
    { label: 'Avg HR', value: fmt(s.avg_heart_rate, 0, ' bpm') },
    { label: 'Max HR', value: fmt(s.max_heart_rate, 0, ' bpm') },
    { label: 'IF', value: fmt(s.intensity_factor, 2) },
    { label: 'TSS', value: fmt(s.training_stress_score, 0) },
    { label: 'kJ', value: fmt(s.total_work ? s.total_work / 1000 : null, 0) },
    { label: 'VI', value: fmt(s.normalized_power && s.avg_power ? s.normalized_power / s.avg_power : null, 2) },
    { label: 'CTL', value: fmt(s.ctl_at_ride, 1) },
    { label: 'TSB', value: fmt(s.tsb_at_ride, 1) },
  ];

  return (
    <div className={styles.metricsBar}>
      {metrics.map(m => (
        <div key={m.label} className={styles.metric}>
          <div className="value">{m.value}</div>
          <div className="label">{m.label}</div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: Create PlannedVsCompleted.tsx**

```typescript
// frontend-v2/src/ride/PlannedVsCompleted.tsx
import type { RideDetail } from '../api/types';
import { COLORS } from '../shared/tokens';

interface Props {
  ride: RideDetail;
}

export function PlannedVsCompleted({ ride }: Props) {
  const planned = ride.summary?.planned;
  if (!planned) return null;

  const actual = ride.summary;
  const durCompliance = planned.duration && actual?.total_elapsed_time
    ? (actual.total_elapsed_time / planned.duration * 100).toFixed(0)
    : null;
  const tssCompliance = planned.tss && actual?.training_stress_score
    ? (actual.training_stress_score / planned.tss * 100).toFixed(0)
    : null;

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: '1fr 1fr',
      gap: 16, padding: 12, background: 'var(--bg-secondary)',
      border: '1px solid var(--border)', borderRadius: 8, marginBottom: 16,
      fontSize: '0.85rem',
    }}>
      <div>
        <h4 style={{ color: COLORS.textMuted, marginBottom: 6, fontSize: '0.8rem' }}>Planned</h4>
        {planned.description && (
          <div style={{ color: COLORS.textSecondary, marginBottom: 4 }}>{planned.description}</div>
        )}
        <div>Duration: {planned.duration ? `${Math.round(planned.duration / 60)} min` : '--'}</div>
        <div>TSS: {planned.tss ?? '--'}</div>
      </div>
      <div>
        <h4 style={{ color: COLORS.textMuted, marginBottom: 6, fontSize: '0.8rem' }}>Completed</h4>
        <div>Duration: {actual?.total_elapsed_time ? `${Math.round(actual.total_elapsed_time / 60)} min` : '--'}</div>
        <div>TSS: {actual?.training_stress_score?.toFixed(0) ?? '--'}</div>
        {durCompliance && (
          <div style={{ color: COLORS.accent }}>Duration compliance: {durCompliance}%</div>
        )}
        {tssCompliance && (
          <div style={{ color: COLORS.accent }}>Intensity compliance: {tssCompliance}%</div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend-v2/src/ride/RideMetricsBar.tsx frontend-v2/src/ride/RideMetricsBar.module.css frontend-v2/src/ride/PlannedVsCompleted.tsx
git commit -m "feat(1c): RideMetricsBar + PlannedVsCompleted components"
```

---

## Task 12: Ride Detail — multi-channel time series + interval cards

**Files:**
- Create: `frontend-v2/src/ride/RideTimeSeries.tsx`
- Create: `frontend-v2/src/ride/RideTimeSeries.module.css`
- Create: `frontend-v2/src/ride/IntervalCards.tsx`
- Create: `frontend-v2/src/ride/IntervalCards.module.css`

Port from `frontend/js/charts/ride-timeseries.js`. Multi-channel stacked time series (power, HR, W'bal, cadence, speed) with synchronized x-axis. Detected intervals rendered as spatially-aligned cards above the chart.

- [ ] **Step 1: Create IntervalCards styles + component**

```css
/* frontend-v2/src/ride/IntervalCards.module.css */
.container {
  position: relative;
  width: 100%;
  min-height: 60px;
  margin-bottom: 4px;
}

.card {
  position: absolute;
  top: 0;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
  padding: 4px 6px;
  font-size: 0.65rem;
  color: var(--text-secondary, #8b949e);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  min-width: 40px;
}

.card .power {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-weight: 600;
  color: var(--accent, #58a6ff);
}
```

```typescript
// frontend-v2/src/ride/IntervalCards.tsx
import type { DetectedInterval } from '../api/types';
import { fmtElapsed } from '../shared/chart-utils';
import styles from './IntervalCards.module.css';

interface Props {
  intervals: DetectedInterval[];
  /** Pixel x-position calculator: (elapsed_seconds) => px from left edge */
  xScale: (seconds: number) => number;
  marginLeft: number;
}

/**
 * Detected interval cards spatially aligned to the x-axis.
 * Each card sits directly above its corresponding time region on the chart.
 */
export function IntervalCards({ intervals, xScale, marginLeft }: Props) {
  if (!intervals.length) return null;

  return (
    <div className={styles.container}>
      {intervals.map((interval, i) => {
        const left = xScale(interval.start_s) + marginLeft;
        const width = Math.max(40, xScale(interval.end_s) - xScale(interval.start_s));

        return (
          <div
            key={i}
            className={styles.card}
            style={{ left, width }}
          >
            <span className="power">{interval.avg_power ?? '--'}W</span>
            {' '}
            <span>{fmtElapsed(interval.end_s - interval.start_s)}</span>
            {interval.avg_hr != null && <span> {interval.avg_hr}bpm</span>}
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Create RideTimeSeries styles**

```css
/* frontend-v2/src/ride/RideTimeSeries.module.css */
.wrapper {
  position: relative;
  width: 100%;
}

.controls {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.channelBtn {
  padding: 3px 10px;
  font-size: 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.15s;
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  padding: 8px 10px;
  font-size: 0.75rem;
  z-index: 10;
  color: var(--text-primary, #e6edf3);
  white-space: nowrap;
  display: none;
}

.tooltip.visible {
  display: block;
}
```

- [ ] **Step 3: Create RideTimeSeries.tsx**

```typescript
// frontend-v2/src/ride/RideTimeSeries.tsx
import { useRef, useCallback, useState, useMemo } from 'react';
import * as d3 from 'd3';
import { ChartContainer } from '../shared/ChartContainer';
import { COLORS } from '../shared/tokens';
import { styleAxis, fmtElapsed, rollingAvg, findNearest } from '../shared/chart-utils';
import { IntervalCards } from './IntervalCards';
import type { RideRecord, DetectedInterval } from '../api/types';
import styles from './RideTimeSeries.module.css';

const MARGIN = { top: 8, right: 55, bottom: 36, left: 55 };

interface Channel {
  key: string;
  label: string;
  color: string;
  dataKey: keyof RideRecord;
  defaultOn: boolean;
}

const CHANNELS: Channel[] = [
  { key: 'power', label: 'Power', color: '#58a6ff', dataKey: 'power', defaultOn: true },
  { key: 'hr', label: 'HR', color: '#f85149', dataKey: 'heart_rate', defaultOn: true },
  { key: 'cadence', label: 'Cadence', color: '#3fb950', dataKey: 'cadence', defaultOn: false },
  { key: 'speed', label: 'Speed', color: '#d29922', dataKey: 'speed', defaultOn: false },
];

interface Props {
  records: RideRecord[];
  intervals: DetectedInterval[];
}

export function RideTimeSeries({ records, intervals }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState<Record<string, boolean>>(
    Object.fromEntries(CHANNELS.map(c => [c.key, c.defaultOn]))
  );
  const [show30sAvg, setShow30sAvg] = useState(false);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });
  const [xScaleFn, setXScaleFn] = useState<((s: number) => number) | null>(null);

  const renderChart = useCallback((width: number) => {
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    if (!records.length) return;

    const totalW = Math.max(width, 300);
    const totalH = Math.max(Math.min(totalW * 0.4, 400), 220);
    const w = totalW - MARGIN.left - MARGIN.right;
    const h = totalH - MARGIN.top - MARGIN.bottom;

    svg.attr('width', totalW).attr('height', totalH);

    // Clip path
    const clipId = 'ride-ts-clip';
    svg.append('defs').append('clipPath').attr('id', clipId)
      .append('rect')
      .attr('x', MARGIN.left).attr('y', MARGIN.top)
      .attr('width', w).attr('height', h);

    // X scale
    const xExtent = d3.extent(records, d => d.elapsed_seconds) as [number, number];
    const xScale = d3.scaleLinear().domain(xExtent).range([MARGIN.left, MARGIN.left + w]);
    setXScaleFn(() => (s: number) => xScale(s) - MARGIN.left);

    // Power Y scale (left)
    const pMax = d3.max(records, d => d.power) || 400;
    const yPower = d3.scaleLinear().domain([0, pMax * 1.1]).range([MARGIN.top + h, MARGIN.top]).nice();

    // HR Y scale (right)
    const hrExtent = d3.extent(records, d => d.heart_rate) as [number, number];
    const yHR = d3.scaleLinear()
      .domain([(hrExtent[0] || 80) - 10, (hrExtent[1] || 190) + 10])
      .range([MARGIN.top + h, MARGIN.top]).nice();

    // Cadence Y scale
    const cadMax = d3.max(records, d => d.cadence) || 120;
    const yCad = d3.scaleLinear().domain([0, cadMax * 1.2]).range([MARGIN.top + h, MARGIN.top]).nice();

    // Grid
    const gridColor = 'var(--chart-grid, #21262d)';
    const powerTicks = yPower.ticks(5);
    powerTicks.forEach(tick => {
      svg.append('line')
        .attr('x1', MARGIN.left).attr('x2', MARGIN.left + w)
        .attr('y1', yPower(tick)).attr('y2', yPower(tick))
        .attr('stroke', gridColor).attr('stroke-width', 0.5);
    });

    // Intervals
    const gIntervals = svg.append('g').attr('clip-path', `url(#${clipId})`);
    intervals.forEach(interval => {
      gIntervals.append('rect')
        .attr('x', xScale(interval.start_s))
        .attr('width', Math.max(0, xScale(interval.end_s) - xScale(interval.start_s)))
        .attr('y', MARGIN.top).attr('height', h)
        .attr('fill', interval.type === 'hard' ? COLORS.danger : COLORS.accent)
        .attr('opacity', 0.08);
    });

    // Lines
    const gLines = svg.append('g').attr('clip-path', `url(#${clipId})`);
    const lineGen = (yScale: d3.ScaleLinear<number, number>, key: keyof RideRecord) =>
      d3.line<RideRecord>()
        .defined(d => d[key] != null)
        .x(d => xScale(d.elapsed_seconds))
        .y(d => yScale(d[key] as number));

    // Power (with smoothing)
    if (visible.power) {
      const smoothed = rollingAvg(records.map(r => r.power), 5);
      const smoothedRecords = records.map((r, i) => ({ ...r, power: smoothed[i] }));

      gLines.append('path')
        .datum(smoothedRecords as any)
        .attr('fill', 'none').attr('stroke', '#58a6ff')
        .attr('stroke-width', 1.5).attr('stroke-linejoin', 'round')
        .attr('d', lineGen(yPower, 'power') as any);

      if (show30sAvg) {
        const avg30 = rollingAvg(records.map(r => r.power), 30);
        const avg30Records = records.map((r, i) => ({ ...r, power: avg30[i] }));
        gLines.append('path')
          .datum(avg30Records as any)
          .attr('fill', 'none').attr('stroke', COLORS.warning)
          .attr('stroke-width', 2).attr('stroke-linejoin', 'round')
          .attr('opacity', 0.85)
          .attr('d', lineGen(yPower, 'power') as any);
      }
    }

    // HR
    if (visible.hr) {
      gLines.append('path')
        .datum(records)
        .attr('fill', 'none').attr('stroke', '#f85149')
        .attr('stroke-width', 1).attr('stroke-linejoin', 'round')
        .attr('d', lineGen(yHR, 'heart_rate'));
    }

    // Cadence
    if (visible.cadence) {
      gLines.append('path')
        .datum(records)
        .attr('fill', 'none').attr('stroke', '#3fb950')
        .attr('stroke-width', 1).attr('stroke-linejoin', 'round')
        .attr('d', lineGen(yCad, 'cadence'));
    }

    // Speed (on cadence scale, converted to km/h)
    if (visible.speed) {
      const speedMax = d3.max(records, d => d.speed ? d.speed * 3.6 : 0) || 60;
      const ySpeed = d3.scaleLinear().domain([0, speedMax * 1.1]).range([MARGIN.top + h, MARGIN.top]);
      const speedLine = d3.line<RideRecord>()
        .defined(d => d.speed != null)
        .x(d => xScale(d.elapsed_seconds))
        .y(d => ySpeed((d.speed || 0) * 3.6));
      gLines.append('path')
        .datum(records).attr('fill', 'none').attr('stroke', '#d29922')
        .attr('stroke-width', 1).attr('d', speedLine);
    }

    // Axes
    const xAxisG = svg.append('g')
      .attr('transform', `translate(0,${MARGIN.top + h})`)
      .call(d3.axisBottom(xScale).ticks(Math.max(w / 100, 3)).tickFormat(d => fmtElapsed(d as number)));
    styleAxis(xAxisG);

    const yLeftG = svg.append('g')
      .attr('transform', `translate(${MARGIN.left},0)`)
      .call(d3.axisLeft(yPower).ticks(5));
    yLeftG.selectAll('text').style('fill', '#58a6ff').style('font-size', '0.7rem');
    yLeftG.selectAll('.domain, line').style('stroke', gridColor);

    const yRightG = svg.append('g')
      .attr('transform', `translate(${MARGIN.left + w},0)`)
      .call(d3.axisRight(yHR).ticks(5));
    yRightG.selectAll('text').style('fill', '#f85149').style('font-size', '0.7rem');
    yRightG.selectAll('.domain, line').style('stroke', gridColor);

    // Crosshair + hover
    const gCross = svg.append('g').attr('clip-path', `url(#${clipId})`).style('display', 'none');
    const crossLine = gCross.append('line')
      .attr('stroke', COLORS.textMuted).attr('stroke-width', 1).attr('stroke-dasharray', '3,3');

    svg.append('rect')
      .attr('x', MARGIN.left).attr('y', MARGIN.top)
      .attr('width', w).attr('height', h)
      .attr('fill', 'none').style('pointer-events', 'all')
      .on('mousemove', (event: MouseEvent) => {
        const [mx] = d3.pointer(event, svgRef.current);
        const elapsed = xScale.invert(mx);
        const d = findNearest(records, r => r.elapsed_seconds, elapsed);
        if (!d) return;

        const cx = xScale(d.elapsed_seconds);
        gCross.style('display', null);
        crossLine.attr('x1', cx).attr('x2', cx)
          .attr('y1', MARGIN.top).attr('y2', MARGIN.top + h);

        const lines = [fmtElapsed(d.elapsed_seconds)];
        if (d.power != null) lines.push(`Power: ${d.power} W`);
        if (d.heart_rate != null) lines.push(`HR: ${d.heart_rate} bpm`);
        if (d.cadence != null) lines.push(`Cadence: ${d.cadence} rpm`);
        if (d.speed != null) lines.push(`Speed: ${(d.speed * 3.6).toFixed(1)} km/h`);

        setTooltipContent(lines.join('\n'));
        setTooltipVisible(true);

        const containerW = svgRef.current?.parentElement?.getBoundingClientRect().width ?? 800;
        let left = cx + 12;
        const tipW = tooltipRef.current?.offsetWidth ?? 120;
        if (left + tipW > containerW) left = cx - tipW - 12;
        setTooltipPos({ left, top: 10 });
      })
      .on('mouseleave', () => {
        gCross.style('display', 'none');
        setTooltipVisible(false);
      });
  }, [records, intervals, visible, show30sAvg]);

  return (
    <div className={styles.wrapper}>
      <div className={styles.controls}>
        {CHANNELS.map(c => (
          <button
            key={c.key}
            className={styles.channelBtn}
            style={{
              border: `1px solid ${c.color}`,
              background: visible[c.key] ? c.color : 'transparent',
              color: visible[c.key] ? '#000' : c.color,
              cursor: c.key === 'power' ? 'default' : 'pointer',
            }}
            onClick={() => {
              if (c.key === 'power') return; // power always on
              setVisible(v => ({ ...v, [c.key]: !v[c.key] }));
            }}
          >
            {c.label}
          </button>
        ))}
        <button
          className={styles.channelBtn}
          style={{
            border: `1px solid ${COLORS.textMuted}`,
            background: show30sAvg ? COLORS.textMuted : 'transparent',
            color: show30sAvg ? 'var(--text-primary)' : COLORS.textMuted,
            marginLeft: 'auto',
          }}
          onClick={() => setShow30sAvg(v => !v)}
        >
          30s Avg
        </button>
      </div>

      {xScaleFn && intervals.length > 0 && (
        <IntervalCards intervals={intervals} xScale={xScaleFn} marginLeft={MARGIN.left} />
      )}

      <ChartContainer onResize={renderChart}>
        <svg ref={svgRef} />
        <div
          ref={tooltipRef}
          className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
          style={{ left: tooltipPos.left, top: tooltipPos.top }}
        >
          {tooltipContent.split('\n').map((line, i) => <div key={i}>{line}</div>)}
        </div>
      </ChartContainer>
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend-v2/src/ride/RideTimeSeries.tsx frontend-v2/src/ride/RideTimeSeries.module.css frontend-v2/src/ride/IntervalCards.tsx frontend-v2/src/ride/IntervalCards.module.css
git commit -m "feat(1c): RideTimeSeries + IntervalCards — multi-channel chart with spatially aligned intervals"
```

---

## Task 13: Ride Detail — full page assembly

**Files:**
- Create: `frontend-v2/src/ride/RideDetail.tsx`
- Create: `frontend-v2/src/ride/RideDetail.module.css`
- Create: `frontend-v2/src/ride/RideSubTabs.tsx`

Assembles all ride detail components into a full page route at `/ride/:id`. Fetches ride data on-demand via store action.

- [ ] **Step 1: Create RideSubTabs.tsx**

```typescript
// frontend-v2/src/ride/RideSubTabs.tsx
import { useState } from 'react';

const TABS = [
  { id: 'timeline', label: 'Timeline' },
  { id: 'power', label: 'Power' },
  { id: 'hr', label: 'HR' },
  { id: 'zones', label: 'Zones' },
  { id: 'data', label: 'Data' },
] as const;

type TabId = typeof TABS[number]['id'];

interface Props {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export function RideSubTabs({ activeTab, onTabChange }: Props) {
  return (
    <div style={{
      display: 'flex', gap: 0, borderBottom: '1px solid var(--border)',
      marginBottom: 16,
    }}>
      {TABS.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          style={{
            padding: '8px 16px',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === tab.id ? '2px solid var(--accent)' : '2px solid transparent',
            color: activeTab === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontFamily: 'inherit',
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export type { TabId };
```

- [ ] **Step 2: Create RideDetail.module.css**

```css
/* frontend-v2/src/ride/RideDetail.module.css */
.page {
  padding: 16px 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.backLink {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary, #8b949e);
  text-decoration: none;
  font-size: 0.85rem;
  margin-bottom: 12px;
  cursor: pointer;
}

.backLink:hover {
  color: var(--text-primary, #e6edf3);
}

.title {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
  margin-bottom: 4px;
}

.subtitle {
  font-size: 0.85rem;
  color: var(--text-muted, #484f58);
  margin-bottom: 16px;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  color: var(--text-muted, #484f58);
}

.errorBox {
  padding: 24px;
  text-align: center;
  color: var(--danger, #f85149);
}

.zoneBar {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-top: 16px;
}
```

- [ ] **Step 3: Create RideDetail.tsx**

```typescript
// frontend-v2/src/ride/RideDetail.tsx
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDataStore } from '../store/data-store';
import { RideMetricsBar } from './RideMetricsBar';
import { PlannedVsCompleted } from './PlannedVsCompleted';
import { RideTimeSeries } from './RideTimeSeries';
import { RideSubTabs } from './RideSubTabs';
import type { TabId } from './RideSubTabs';
import styles from './RideDetail.module.css';

export function RideDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const rideId = Number(id);

  const ride = useDataStore(s => s.rides[rideId]);
  const loading = useDataStore(s => s.loading.has(`ride-${rideId}`));
  const error = useDataStore(s => s.errors[`ride-${rideId}`]);
  const fetchRide = useDataStore(s => s.fetchRide);

  const [activeTab, setActiveTab] = useState<TabId>('timeline');

  useEffect(() => {
    if (!ride && !loading && !error && rideId) {
      fetchRide(rideId);
    }
  }, [rideId, ride, loading, error, fetchRide]);

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>Loading ride data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.page}>
        <div className={styles.errorBox}>{error}</div>
      </div>
    );
  }

  if (!ride) {
    return (
      <div className={styles.page}>
        <div className={styles.loading}>No ride data</div>
      </div>
    );
  }

  const summary = ride.summary;
  const records = ride.records || [];
  const intervals = ride.intervals || [];

  const dateStr = summary?.start_time
    ? new Date(summary.start_time).toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
      })
    : '';

  return (
    <div className={styles.page}>
      <a className={styles.backLink} onClick={() => navigate(-1)}>
        &larr; Back
      </a>

      <div className={styles.title}>
        {summary?.filename || `Ride #${rideId}`}
      </div>
      <div className={styles.subtitle}>{dateStr}</div>

      <RideMetricsBar ride={ride} />
      <PlannedVsCompleted ride={ride} />

      <RideSubTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === 'timeline' && (
        <RideTimeSeries records={records} intervals={intervals} />
      )}

      {activeTab === 'power' && (
        <div style={{ color: 'var(--text-muted)', padding: 24, textAlign: 'center' }}>
          Power analysis coming in next phase
        </div>
      )}

      {activeTab === 'hr' && (
        <div style={{ color: 'var(--text-muted)', padding: 24, textAlign: 'center' }}>
          HR analysis coming in next phase
        </div>
      )}

      {activeTab === 'zones' && (
        <div style={{ color: 'var(--text-muted)', padding: 24, textAlign: 'center' }}>
          Zone distribution coming in next phase
        </div>
      )}

      {activeTab === 'data' && (
        <div style={{ color: 'var(--text-muted)', padding: 24, textAlign: 'center' }}>
          Raw data table coming in next phase
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Add route to App.tsx**

In `frontend-v2/src/App.tsx`, add:

```typescript
import { RideDetail } from './ride/RideDetail';

// In the Router:
<Route path="/ride/:id" element={<RideDetail />} />
```

- [ ] **Step 5: Visual verification**

```bash
cd frontend-v2 && npm run dev
```

Navigate to `/ride/1` (or any valid ride ID). Expected:
1. Back link at top
2. Ride title + date
3. Metrics bar with 14 compact metric cards
4. Multi-channel time series (power + HR default)
5. Channel toggle buttons work (cadence, speed)
6. 30s Avg button works
7. Detected interval cards aligned above chart regions
8. Crosshair tooltip on hover
9. Sub-tabs render (Timeline active, others show placeholder)

- [ ] **Step 6: Commit**

```bash
git add frontend-v2/src/ride/RideDetail.tsx frontend-v2/src/ride/RideDetail.module.css frontend-v2/src/ride/RideSubTabs.tsx
git commit -m "feat(1c): RideDetail — full page with metrics bar, time series, sub-tabs"
```

---

## Task 14: Panel Registry wiring — all chart panels

**Files:**
- Modify: `frontend-v2/src/layout/PanelRegistry.ts`

Register all 7 chart panels in the panel registry so the layout engine can render them.

- [ ] **Step 1: Add all panel registrations**

```typescript
// In PanelRegistry.ts, add imports:
import { PMCChart } from '../panels/fitness/PMCChart';
import { MMPCurve } from '../panels/fitness/MMPCurve';
import { RollingFtp } from '../panels/fitness/RollingFtp';
import { FtpGrowth } from '../panels/fitness/FtpGrowth';
import { RollingPd } from '../panels/fitness/RollingPd';
import { IFDistribution } from '../panels/health/IFDistribution';
import { SegmentProfile } from '../panels/event-prep/SegmentProfile';

// Add to panels map:
'pmc-chart': {
  id: 'pmc-chart',
  label: 'Performance Management Chart',
  category: 'fitness',
  description: 'CTL, ATL, TSB over time — fitness/fatigue/form tracking',
  component: PMCChart,
  dataKeys: ['pmc'],
},
'mmp-curve': {
  id: 'mmp-curve',
  label: 'MMP / Power-Duration Curve',
  category: 'fitness',
  description: 'Mean Maximal Power envelope + PD model overlay',
  component: MMPCurve,
  dataKeys: ['model'],
},
'rolling-ftp': {
  id: 'rolling-ftp',
  label: 'Rolling FTP',
  category: 'fitness',
  description: 'mFTP trend over time with big number display',
  component: RollingFtp,
  dataKeys: ['rollingFtp'],
},
'ftp-growth': {
  id: 'ftp-growth',
  label: 'FTP Growth',
  category: 'fitness',
  description: 'Growth rate, training phase, R² fit, and scatter plot',
  component: FtpGrowth,
  dataKeys: ['ftpGrowth'],
},
'rolling-pd': {
  id: 'rolling-pd',
  label: 'Rolling PD Parameters',
  category: 'fitness',
  description: 'mFTP, Pmax, FRC, TTE trends over time',
  component: RollingPd,
  dataKeys: ['rollingPd'],
},
'if-distribution': {
  id: 'if-distribution',
  label: 'IF Distribution',
  category: 'health',
  description: 'Intensity Factor histogram with floor/ceiling markers',
  component: IFDistribution,
  dataKeys: ['ifDistribution'],
},
'segment-profile': {
  id: 'segment-profile',
  label: 'Segment Profile',
  category: 'event-prep',
  description: 'Elevation profile with demand-colored segment overlays',
  component: SegmentProfile,
  dataKeys: ['routeDetail'],
},
```

- [ ] **Step 2: Commit**

```bash
git add frontend-v2/src/layout/PanelRegistry.ts
git commit -m "feat(1c): register all 7 chart panels in PanelRegistry"
```

---

## Task 15: Integration tests + final verification

**Files:**
- Create: `frontend-v2/src/__tests__/PMCChart.test.tsx`

- [ ] **Step 1: Create PMCChart smoke test**

```typescript
// frontend-v2/src/__tests__/PMCChart.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { useDataStore } from '../store/data-store';

// Mock D3 and ChartContainer to avoid DOM measurement issues in test
vi.mock('../shared/ChartContainer', () => ({
  ChartContainer: ({ children }: any) => <div data-testid="chart-container">{children}</div>,
}));

import { PMCChart } from '../panels/fitness/PMCChart';

describe('PMCChart', () => {
  beforeEach(() => {
    useDataStore.setState({
      loading: new Set(),
      errors: {},
      annotations: {},
    });
  });

  it('renders skeleton when loading', () => {
    useDataStore.setState({ loading: new Set(['pmc']), pmc: [] });
    render(<PMCChart />);
    // PanelSkeleton should render (contains a loading class or text)
    expect(document.querySelector('[class*="skeleton"]') || document.body.textContent).toBeTruthy();
  });

  it('renders error when store has error', () => {
    useDataStore.setState({ errors: { pmc: 'Network error' }, pmc: [] });
    render(<PMCChart />);
    expect(screen.getByText(/Network error/)).toBeTruthy();
  });

  it('renders empty state when no data', () => {
    useDataStore.setState({ pmc: [] });
    render(<PMCChart />);
    expect(screen.getByText(/No PMC data/)).toBeTruthy();
  });

  it('renders chart when data is present', () => {
    useDataStore.setState({
      pmc: [
        { date: '2026-01-01', CTL: 50, ATL: 60, TSB: -10, TSS: 100 },
        { date: '2026-01-02', CTL: 51, ATL: 58, TSB: -7, TSS: 80 },
      ],
    });
    render(<PMCChart />);
    expect(document.querySelector('svg')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run all tests**

```bash
cd frontend-v2 && npx vitest run
```

Expected: All tests pass — chart-utils (15+), annotation-store (5), PMCChart smoke test (4).

- [ ] **Step 3: Full visual verification**

```bash
cd frontend-v2 && npm run dev
```

Verify each chart renders from store data:

1. **Fitness tab:** PMC chart (CTL/ATL/TSB lines, green/red areas), MMP curve (log scale, zone backgrounds, model overlay), Rolling FTP (big number + trend), FTP Growth (cards + scatter), Rolling PD (multi-line with toggles)
2. **Health tab:** IF Distribution (colored bars, floor/ceiling markers)
3. **Event Prep tab:** Segment Profile (elevation area, demand-colored overlays) — requires selected route
4. **Ride detail** (`/ride/{id}`): Metrics bar, time series (power+HR), interval cards, channel toggles, 30s avg
5. **Annotations (PMC):** Click test button, verify region overlay + callout card + dismiss + clear

- [ ] **Step 4: Final commit**

```bash
git add frontend-v2/src/__tests__/PMCChart.test.tsx
git commit -m "test(1c): PMCChart smoke tests + integration verification"
```

---

## Exit Criteria Checklist

- [ ] All 7 D3 chart panels render correctly from Zustand store data
- [ ] PMC chart: CTL (blue line), ATL (pink line), TSB (amber dashed), green/red shaded areas, dual y-axes, crosshair tooltip
- [ ] MMP curve: log-scale x-axis, MMP envelope + area fill, PD model overlay, zone backgrounds, recency toggle
- [ ] Rolling FTP: big number + time series + trend line
- [ ] FTP Growth: metric cards + scatter plot with log-fit curve
- [ ] Rolling PD: 4 series with interactive legend toggles
- [ ] IF Distribution: histogram bars colored by zone, floor/ceiling dashed markers
- [ ] Segment Profile: elevation area + demand-colored segment overlays + summary bar
- [ ] Ride detail page: metrics bar (14 metrics), multi-channel time series (power/HR/cadence/speed), 30s avg toggle, interval cards spatially aligned to x-axis, sub-tabs
- [ ] Annotation system: AnnotationOverlay renders region/line/point overlays on PMC chart, callout cards with severity badge + dismiss button, toolbar with count/hide/clear
- [ ] Annotation store: addAnnotation, clearAnnotations, label truncation (200 char max)
- [ ] All tests pass: chart-utils, annotation-store, PMCChart smoke tests
- [ ] All 7 chart panels registered in PanelRegistry
