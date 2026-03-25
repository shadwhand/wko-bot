import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './Feasibility.module.css'

export function Feasibility() {
  const fitness = useDataStore(s => s.fitness)
  const loading = useDataStore(s => s.loading.has('fitness'))
  const error = useDataStore(s => s.errors['fitness'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!fitness) return <PanelEmpty message="No fitness data for feasibility" />

  // Feasibility projection based on current CTL
  // This is a simplified version; the full version uses the backend endpoint
  const currentCTL = fitness.CTL ?? 0
  const maxSustainableRamp = 5 // TSS/wk typical max
  const weeksAvailable = 12 // default planning horizon

  return (
    <Tooltip
      label="Feasibility"
      fullName="CTL Feasibility Projection"
      derivation={`Current CTL: ${currentCTL.toFixed(0)}. Max sustainable ramp rate: ~${maxSustainableRamp} TSS/day per week.`}
      context="Ramp rate >7 TSS/wk sustained risks overtraining. Plan 8-16 weeks for significant CTL gains."
    >
      <div className={styles.card}>
        <div className={styles.metrics}>
          <Metric value={Math.round(currentCTL)} label="Current CTL" />
          <Metric
            value={Math.round(currentCTL + maxSustainableRamp * weeksAvailable)}
            label={`Projected (${weeksAvailable}wk)`}
          />
          <Metric value={maxSustainableRamp} label="Max Ramp (TSS/wk)" />
        </div>
        <div className={styles.note}>
          Use the backend feasibility endpoint for precise projection with target CTL.
        </div>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'feasibility',
  label: 'Feasibility',
  category: 'profile',
  description: 'CTL feasibility projection based on current fitness',
  component: Feasibility,
  dataKeys: ['fitness'],
})
