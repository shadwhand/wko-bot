// frontend-v2/src/panels/event-prep/SegmentProfile.tsx
import { useRef, useCallback, useState, useEffect } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis, demandColor, demandOpacity, findNearest } from '../../shared/chart-utils';
import { PanelSkeleton } from '../../shared/PanelSkeleton';
import { PanelError } from '../../shared/PanelError';
import { PanelEmpty } from '../../shared/PanelEmpty';
import { registerPanel } from '../../layout/PanelRegistry';
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

/**
 * SegmentProfile reads selectedRouteId from the store.
 * When route detail data is available (with elevation_profile and segments),
 * it renders the elevation area chart with demand-colored segment overlays.
 *
 * The route detail store slice is keyed by route ID. Fetches automatically
 * when selectedRouteId changes.
 */
export function SegmentProfile() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId);
  const routeDetail = useDataStore(s =>
    s.selectedRouteId != null ? s.routeDetail[s.selectedRouteId] : null
  );
  const loading = useDataStore(s => s.loading.has('routeDetail'));
  const error = useDataStore(s => s.errors['routeDetail']);
  const fetchRouteDetail = useDataStore(s => s.fetchRouteDetail);

  // Fetch route detail when selectedRouteId changes
  useEffect(() => {
    if (selectedRouteId != null && !routeDetail) {
      fetchRouteDetail(selectedRouteId);
    }
  }, [selectedRouteId, routeDetail, fetchRouteDetail]);

  if (!selectedRouteId) return <PanelEmpty message="Select a route to see elevation profile" />;
  if (loading) return <PanelSkeleton />;
  if (error) return <PanelError message={error} />;

  // Render the chart if we have elevation data, otherwise show empty state
  const elevProfile = routeDetail?.elevation_profile ?? routeDetail?.points;
  const segments = routeDetail?.segments;
  if (!elevProfile || elevProfile.length === 0) {
    return <PanelEmpty message="No elevation data for selected route" />;
  }

  return (
    <SegmentProfileChart
      elevationProfile={elevProfile}
      segments={segments ?? []}
      totalKm={routeDetail?.distance_km ?? 0}
      totalElevation={routeDetail?.elevation_m ?? 0}
    />
  );
}

/** Standalone inner chart -- exported for use when data is directly available. */
export function SegmentProfileChart({
  elevationProfile,
  segments,
  totalKm,
  totalElevation,
}: {
  elevationProfile: ElevPoint[];
  segments: Segment[];
  totalKm: number;
  totalElevation: number;
}) {
  return (
    <div className={styles.wrapper}>
      <SegmentProfileInner
        elevationProfile={elevationProfile}
        segments={segments}
        totalKm={totalKm}
        totalElevation={totalElevation}
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
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipContent, setTooltipContent] = useState('');
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({ left: 0, top: 0 });

  const renderChart = useCallback((svgEl: SVGSVGElement, width: number) => {
    const svg = d3.select(svgEl);
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
      .call(d3.axisLeft(y).ticks(5).tickSize(-innerW).tickFormat('' as unknown as (d: d3.NumberValue) => string))
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
      .attr('fill', COLORS.elevation).attr('fill-opacity', 0.15);

    // Altitude line
    const line = d3.line<ElevPoint>()
      .x(d => x(d.km)).y(d => y(d.altitude)).curve(d3.curveMonotoneX);

    g.append('path').datum(elevationProfile).attr('d', line)
      .attr('fill', 'none').attr('stroke', COLORS.muted).attr('stroke-width', 1.5);

    // Segment type labels
    g.selectAll('.seg-label')
      .data(segments.filter(d => (x(d.end_km) - x(d.start_km)) > MIN_LABEL_PX))
      .join('text')
      .attr('x', d => x((d.start_km + d.end_km) / 2))
      .attr('y', -6)
      .attr('text-anchor', 'middle')
      .attr('fill', COLORS.muted).attr('font-size', '0.7rem')
      .text(d => {
        if (d.type === 'climb') return `Climb ${d.avg_grade.toFixed(1)}%`;
        if (d.type === 'descent') return 'Descent';
        return 'Flat';
      });

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(Math.min(10, innerW / 60)).tickFormat(d => `${d} km`));
    styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    const yAxisG = g.append('g')
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d} m`));
    styleAxis(yAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    // Hover
    const hoverLine = g.append('line')
      .attr('y1', 0).attr('y2', innerH)
      .attr('stroke', COLORS.primary).attr('stroke-dasharray', '4,3')
      .style('opacity', 0);

    const hoverDot = g.append('circle')
      .attr('r', 4).attr('fill', COLORS.primary).style('opacity', 0);

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
      <ChartContainer
        renderChart={renderChart}
        minHeight={260}
      />
      <div
        ref={tooltipRef}
        className={`${styles.tooltip} ${tooltipVisible ? styles.visible : ''}`}
        style={{ left: tooltipPos.left, top: tooltipPos.top }}
      >
        {tooltipContent.split('\n').map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
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

// -- Panel Registration --
registerPanel({
  id: 'segment-profile',
  label: 'Segment Profile',
  category: 'event-prep',
  description: 'Elevation profile with demand-colored segment overlays',
  component: SegmentProfile,
  dataKeys: ['selectedRouteId', 'routeDetail'],
});
