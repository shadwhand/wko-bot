import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { MetricBig } from '../../shared/MetricBig'
import { tsbColor, tsbLabel, COLORS } from '../../shared/tokens'
import styles from './TSBStatus.module.css'

export function TSBStatus() {
  const fitness = useDataStore((s) => s.fitness)
  const loading = useDataStore((s) => s.loading.has('fitness'))
  const error = useDataStore((s) => s.errors['fitness'])
  const refresh = useDataStore((s) => s.refresh)

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} onRetry={refresh} />
  if (!fitness) return <PanelEmpty message="No fitness data available" />

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.title}>Today's Form</span>
        <span className={styles.phase} style={{ color: tsbColor(fitness.TSB) }}>
          {tsbLabel(fitness.TSB)}
        </span>
      </div>
      <div className={styles.hero}>
        <MetricBig
          value={fitness.TSB}
          label="TSB"
          color={tsbColor(fitness.TSB)}
        />
      </div>
      <div className={styles.row}>
        <Metric value={fitness.CTL} label="CTL" color={COLORS.ctl} />
        <Metric value={fitness.ATL} label="ATL" color={COLORS.atl} />
      </div>
    </div>
  )
}
