// frontend-v2/src/ride/PlannedVsCompleted.tsx
import type { RideDetail } from '../api/types';
import { COLORS } from '../shared/tokens';

interface Props {
  ride: RideDetail;
}

/**
 * Side-by-side planned vs actual comparison.
 * Only renders if the ride summary contains planned workout data.
 * The planned field is optional and comes from TrainingPeaks import.
 */
export function PlannedVsCompleted({ ride }: Props) {
  const summary = ride.summary as Record<string, unknown> | undefined;
  const planned = summary?.planned as
    | { description?: string; duration?: number; tss?: number }
    | undefined;

  if (!planned) return null;

  const actual = ride.summary;
  const durCompliance =
    planned.duration && actual?.total_elapsed_time
      ? ((actual.total_elapsed_time / planned.duration) * 100).toFixed(0)
      : null;
  const tssCompliance =
    planned.tss && actual?.training_stress_score
      ? ((actual.training_stress_score / planned.tss) * 100).toFixed(0)
      : null;

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 16,
        padding: 12,
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border)',
        borderRadius: 8,
        marginBottom: 16,
        fontSize: '0.85rem',
      }}
    >
      <div>
        <h4
          style={{
            color: COLORS.muted,
            marginBottom: 6,
            fontSize: '0.8rem',
          }}
        >
          Planned
        </h4>
        {planned.description && (
          <div style={{ color: COLORS.muted, marginBottom: 4 }}>
            {planned.description}
          </div>
        )}
        <div>
          Duration:{' '}
          {planned.duration
            ? `${Math.round(planned.duration / 60)} min`
            : '--'}
        </div>
        <div>TSS: {planned.tss ?? '--'}</div>
      </div>
      <div>
        <h4
          style={{
            color: COLORS.muted,
            marginBottom: 6,
            fontSize: '0.8rem',
          }}
        >
          Completed
        </h4>
        <div>
          Duration:{' '}
          {actual?.total_elapsed_time
            ? `${Math.round(actual.total_elapsed_time / 60)} min`
            : '--'}
        </div>
        <div>TSS: {actual?.training_stress_score?.toFixed(0) ?? '--'}</div>
        {durCompliance && (
          <div style={{ color: COLORS.primary }}>
            Duration compliance: {durCompliance}%
          </div>
        )}
        {tssCompliance && (
          <div style={{ color: COLORS.primary }}>
            Intensity compliance: {tssCompliance}%
          </div>
        )}
      </div>
    </div>
  );
}
