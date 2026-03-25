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
    { label: 'Avg Power', value: fmt(s.avg_power, 0, ' W') },
    { label: 'Max Power', value: fmt(s.max_power, 0, ' W') },
    { label: 'NP', value: fmt(s.normalized_power, 0, ' W') },
    { label: 'Avg HR', value: fmt(s.avg_heart_rate, 0, ' bpm') },
    { label: 'Max HR', value: fmt(s.max_heart_rate, 0, ' bpm') },
    { label: 'IF', value: fmt(s.intensity_factor, 2) },
    { label: 'TSS', value: fmt(s.training_stress_score, 0) },
    {
      label: 'VI',
      value: fmt(
        s.normalized_power && s.avg_power
          ? s.normalized_power / s.avg_power
          : null,
        2,
      ),
    },
  ];

  return (
    <div className={styles.metricsBar}>
      {metrics.map(m => (
        <div key={m.label} className={styles.metric}>
          <div className={styles.value}>{m.value}</div>
          <div className={styles.label}>{m.label}</div>
        </div>
      ))}
    </div>
  );
}
