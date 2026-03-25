// frontend-v2/src/ride/IntervalCards.tsx
import type { RideInterval } from '../api/types';
import { fmtElapsed } from '../shared/chart-utils';
import styles from './IntervalCards.module.css';

interface Props {
  intervals: RideInterval[];
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
        const left = xScale(interval.start) + marginLeft;
        const width = Math.max(40, xScale(interval.end) - xScale(interval.start));

        return (
          <div
            key={i}
            className={styles.card}
            style={{ left, width }}
          >
            <span className={styles.power}>{interval.avg_power ?? '--'}W</span>
            {' '}
            <span>{fmtElapsed(interval.duration)}</span>
            {interval.avg_hr != null && <span> {interval.avg_hr}bpm</span>}
          </div>
        );
      })}
    </div>
  );
}
