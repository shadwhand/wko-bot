// frontend-v2/src/ride/RideDetail.tsx
import { useEffect, useState } from 'react';
import { useDataStore } from '../store/data-store';
import { RideMetricsBar } from './RideMetricsBar';
import { PlannedVsCompleted } from './PlannedVsCompleted';
import { RideTimeSeries } from './RideTimeSeries';
import { RideSubTabs } from './RideSubTabs';
import type { TabId } from './RideSubTabs';
import styles from './RideDetail.module.css';

interface Props {
  rideId: number;
  onBack: () => void;
}

export function RideDetail({ rideId, onBack }: Props) {
  const ride = useDataStore(s => s.rides[rideId]);
  const loading = useDataStore(s => s.loading.has(`ride:${rideId}`));
  const error = useDataStore(s => s.errors[`ride:${rideId}`]);
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
        <button className={styles.backLink} onClick={onBack}>
          &larr; Back
        </button>
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
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : '';

  return (
    <div className={styles.page}>
      <button className={styles.backLink} onClick={onBack}>
        &larr; Back
      </button>

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
        <div className={styles.placeholder}>
          Power analysis coming in next phase
        </div>
      )}

      {activeTab === 'hr' && (
        <div className={styles.placeholder}>
          HR analysis coming in next phase
        </div>
      )}

      {activeTab === 'zones' && (
        <div className={styles.placeholder}>
          Zone distribution coming in next phase
        </div>
      )}

      {activeTab === 'data' && (
        <div className={styles.placeholder}>
          Raw data table coming in next phase
        </div>
      )}
    </div>
  );
}
