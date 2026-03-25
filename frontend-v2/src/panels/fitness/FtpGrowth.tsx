// frontend-v2/src/panels/fitness/FtpGrowth.tsx
import { useCallback } from 'react';
import * as d3 from 'd3';
import { useDataStore } from '../../store/data-store';
import { ChartContainer } from '../../shared/ChartContainer';
import { COLORS } from '../../shared/tokens';
import { styleAxis } from '../../shared/chart-utils';
import { PanelSkeleton } from '../../shared/PanelSkeleton';
import { PanelError } from '../../shared/PanelError';
import { PanelEmpty } from '../../shared/PanelEmpty';
import { registerPanel } from '../../layout/PanelRegistry';
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
  const phaseColor = phase === 'plateau' ? COLORS.warning : phase === 'rapid' ? COLORS.success : COLORS.primary;
  const growthRate = ftpGrowth.improvement_rate_w_per_year;
  const rSquared = ftpGrowth.r_squared;
  const trainingAge = ftpGrowth.training_age_weeks;

  return (
    <div className={styles.wrapper}>
      <div className={styles.cards}>
        {growthRate != null && (
          <div className={styles.card}>
            <div className={styles.value}>{growthRate.toFixed(1)}</div>
            <div className={styles.label}>W/year</div>
          </div>
        )}
        <div className={styles.card}>
          <div className={styles.value} style={{ color: phaseColor, fontSize: '1.1rem' }}>{phase}</div>
          <div className={styles.label}>Phase</div>
        </div>
        {trainingAge != null && (
          <div className={styles.card}>
            <div className={styles.value}>{(trainingAge / 52).toFixed(1)}</div>
            <div className={styles.label}>Training Years</div>
          </div>
        )}
        {rSquared != null && (
          <div className={styles.card}>
            <div className={styles.value}>{rSquared.toFixed(2)}</div>
            <div className={styles.label}>R&sup2; (fit)</div>
          </div>
        )}
      </div>
      {ftpGrowth.data_points && ftpGrowth.data_points.length > 0 ? (
        <FtpGrowthChart data={ftpGrowth} />
      ) : (
        <div className={styles.fallback}>
          See Rolling FTP panel for trend chart
        </div>
      )}
    </div>
  );
}

function FtpGrowthChart({ data }: { data: FtpGrowthResponse }) {
  const history = data.data_points || [];

  const renderChart = useCallback((svgEl: SVGSVGElement, width: number) => {
    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();

    if (!history.length) return;

    const innerW = width - MARGIN.left - MARGIN.right;
    const innerH = CHART_HEIGHT;
    const totalH = innerH + MARGIN.top + MARGIN.bottom;
    svg.attr('width', width).attr('height', totalH);

    const g = svg.append('g').attr('transform', `translate(${MARGIN.left},${MARGIN.top})`);

    const dates = history.map(h => new Date(h.date));
    const ftps = history.map(h => h.mFTP);

    const x = d3.scaleTime().domain(d3.extent(dates) as [Date, Date]).range([0, innerW]);
    const y = d3.scaleLinear()
      .domain([d3.min(ftps)! * 0.95, d3.max(ftps)! * 1.05])
      .range([innerH, 0]);

    // Scatter points
    g.selectAll('circle').data(history).enter().append('circle')
      .attr('cx', (_, i) => x(dates[i]))
      .attr('cy', (_, i) => y(ftps[i]))
      .attr('r', 4)
      .attr('fill', COLORS.primary)
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
        .attr('fill', 'none').attr('stroke', COLORS.primary)
        .attr('stroke-width', 2).attr('stroke-dasharray', '6,3')
        .attr('opacity', 0.6);
    }

    // Axes
    const xAxisG = g.append('g').attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6).tickFormat(d3.timeFormat('%b %y') as unknown as (d: d3.NumberValue) => string));
    styleAxis(xAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);

    const yAxisG = g.append('g')
      .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d}W`));
    styleAxis(yAxisG as unknown as d3.Selection<SVGGElement, unknown, null, undefined>);
  }, [history, data.slope, data.intercept]);

  return (
    <ChartContainer renderChart={renderChart} minHeight={CHART_HEIGHT + MARGIN.top + MARGIN.bottom} />
  );
}

// -- Panel Registration --
registerPanel({
  id: 'ftp-growth',
  label: 'FTP Growth',
  category: 'fitness',
  description: 'FTP improvement rate, training phase, and scatter plot with log-fit curve',
  component: FtpGrowth,
  dataKeys: ['ftpGrowth'],
});
