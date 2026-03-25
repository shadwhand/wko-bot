import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { MetricBig } from '../../shared/MetricBig'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
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
        <Tooltip
          label="TSB"
          fullName="Training Stress Balance (TSB)"
          derivation="CTL minus ATL. Positive = fresh, negative = fatigued."
          context="Race-ready zone: +5 to +25. Below -20 = high overreach risk."
        >
          <MetricBig
            value={fitness.TSB}
            label="TSB"
            color={tsbColor(fitness.TSB)}
          />
        </Tooltip>
      </div>
      <div className={styles.row}>
        <Tooltip
          label="CTL"
          fullName="Chronic Training Load (CTL)"
          derivation="Exponentially weighted average of daily TSS, 42-day time constant."
          context="Higher = more fit. Typical target: 60-100 for competitive amateur."
        >
          <Metric value={fitness.CTL} label="CTL" color={COLORS.ctl} />
        </Tooltip>
        <Tooltip
          label="ATL"
          fullName="Acute Training Load (ATL)"
          derivation="Exponentially weighted average of daily TSS, 7-day time constant."
          context="Higher = more fatigued. Spikes indicate recent hard training."
        >
          <Metric value={fitness.ATL} label="ATL" color={COLORS.atl} />
        </Tooltip>
      </div>
    </div>
  )
}

registerPanel({
  id: 'tsb-status',
  label: 'TSB Status',
  category: 'status',
  description: 'Current form (TSB), fitness (CTL), fatigue (ATL)',
  component: TSBStatus,
  dataKeys: ['fitness'],
})
