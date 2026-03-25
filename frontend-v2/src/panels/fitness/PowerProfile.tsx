import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './PowerProfile.module.css'

/** Coggan ranking thresholds per duration (W/kg) for male Cat 3-5 reference */
const RANKING_LABELS: Record<string, string> = {
  world_class: 'World Class',
  exceptional: 'Exceptional',
  excellent: 'Excellent',
  very_good: 'Very Good',
  good: 'Good',
  moderate: 'Moderate',
  fair: 'Fair',
  untrained: 'Untrained',
}

const DURATIONS = [
  { key: '5', label: '5s', tooltip: 'Peak 5-second power — neuromuscular / sprint' },
  { key: '60', label: '1min', tooltip: 'Peak 1-minute power — anaerobic capacity' },
  { key: '300', label: '5min', tooltip: 'Peak 5-minute power — VO2max' },
  { key: '1200', label: '20min', tooltip: 'Peak 20-minute power — threshold estimate' },
  { key: '3600', label: '60min', tooltip: 'Peak 60-minute power — functional threshold' },
]

export function PowerProfile() {
  const profile = useDataStore(s => s.profile)
  const loading = useDataStore(s => s.loading.has('profile'))
  const error = useDataStore(s => s.errors['profile'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!profile) return <PanelEmpty message="No power profile data" />

  const watts = profile.profile?.watts ?? {}
  const wkg = profile.profile?.wkg ?? {}
  const ranking = profile.ranking ?? {}

  return (
    <div className={styles.grid}>
      {DURATIONS.map(d => {
        const w = watts[d.key]
        const wkgVal = wkg[d.key]
        const rank = ranking[d.key]
        const rankLabel = RANKING_LABELS[rank] ?? rank ?? '--'

        return (
          <Tooltip
            key={d.key}
            label={d.key}
            fullName={`Power Profile — ${d.label}`}
            derivation={d.tooltip}
            context={`Ranking: ${rankLabel}. W/kg is the key metric for climbing and relative fitness.`}
          >
            <div className={styles.cell}>
              <div className={styles.duration}>{d.label}</div>
              <div className={styles.watts}>
                {w != null ? `${Math.round(w)}W` : '--'}
              </div>
              <div className={styles.wkg}>
                {wkgVal != null ? `${wkgVal.toFixed(2)} W/kg` : '--'}
              </div>
              <div className={styles.rank}>{rankLabel}</div>
            </div>
          </Tooltip>
        )
      })}
    </div>
  )
}

registerPanel({
  id: 'power-profile',
  label: 'Power Profile',
  category: 'fitness',
  description: '5s/1min/5min/20min/60min W/kg grid with rankings',
  component: PowerProfile,
  dataKeys: ['profile'],
})
