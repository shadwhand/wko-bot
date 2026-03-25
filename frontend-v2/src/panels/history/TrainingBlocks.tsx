import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Metric } from '../../shared/Metric'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function TrainingBlocks() {
  // Training blocks come from the activities + model data
  // The backend returns block stats via a computed endpoint
  const activities = useDataStore(s => s.activities)
  const loading = useDataStore(s => s.loading.has('activities'))
  const error = useDataStore(s => s.errors['activities'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!activities || activities.length === 0) {
    return <PanelEmpty message="No training data for block analysis" />
  }

  // Compute basic block stats from activities (last 4 weeks)
  const now = new Date()
  const fourWeeksAgo = new Date(now.getTime() - 28 * 86_400_000)
  const recent = activities.filter((a: any) =>
    new Date(a.start_time) >= fourWeeksAgo
  )

  const totalHours = recent.reduce((sum: number, a: any) =>
    sum + ((a.total_elapsed_time ?? 0) / 3600), 0)
  const totalTSS = recent.reduce((sum: number, a: any) =>
    sum + (a.training_stress_score ?? 0), 0)
  const avgIF = recent.filter((a: any) => a.intensity_factor != null)
    .reduce((sum: number, a: any, _, arr) =>
      sum + (a.intensity_factor / arr.length), 0)
  const avgPower = recent.filter((a: any) => a.avg_power != null)
    .reduce((sum: number, a: any, _, arr) =>
      sum + (a.avg_power / arr.length), 0)

  return (
    <Tooltip
      label="TrainingBlocks"
      fullName="Training Block Summary (Last 4 Weeks)"
      derivation="Aggregated volume, intensity, and power from the last 28 days of rides."
      context="Compare blocks over time to track progressive overload and recovery periods."
    >
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
        <Metric value={recent.length} label="Rides" />
        <Metric value={totalHours.toFixed(1)} label="Hours" />
        <Metric value={Math.round(totalTSS)} label="Total TSS" />
        <Metric value={avgIF.toFixed(2)} label="Avg IF" />
        <Metric value={Math.round(avgPower)} label="Avg Power" unit="W" />
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'training-blocks',
  label: 'Training Blocks',
  category: 'history',
  description: 'Block stats — volume, intensity, power (last 4 weeks)',
  component: TrainingBlocks,
  dataKeys: ['activities'],
})
