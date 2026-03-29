import { useEffect } from 'react'
import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './GapAnalysis.module.css'

export function GapAnalysis() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const routeAnalysis = useDataStore(s =>
    s.selectedRouteId != null ? s.routeAnalysis[s.selectedRouteId] : null
  )
  const loading = useDataStore(s => s.loading.has('routeAnalysis'))
  const error = useDataStore(s => s.errors['routeAnalysis'])
  const fetchRouteAnalysis = useDataStore(s => s.fetchRouteAnalysis)

  // Fetch route analysis when selectedRouteId changes
  useEffect(() => {
    if (selectedRouteId != null && !routeAnalysis) {
      fetchRouteAnalysis(selectedRouteId)
    }
  }, [selectedRouteId, routeAnalysis, fetchRouteAnalysis])

  if (!selectedRouteId) {
    return <PanelEmpty message="Select a route to see gap analysis" />
  }
  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />

  const gapData = routeAnalysis?.gap_analysis
  if (!gapData) {
    return <PanelEmpty message="No gap analysis data for this route" />
  }
  if (gapData.error) {
    return <PanelError message={gapData.error} />
  }

  const gap = gapData
  const feasible = gap.feasible

  return (
    <Tooltip
      label="GapAnalysis"
      fullName="Gap Analysis — Feasibility Assessment"
      derivation="Monte Carlo simulation comparing your PD model to route power demands."
      context={`${feasible ? 'Feasible' : 'Not feasible'} given current fitness. Bottleneck: ${gap.bottleneck ?? 'none'}.`}
    >
      <div className={`${styles.card} ${feasible ? styles.feasible : styles.notFeasible}`}>
        <div className={styles.verdict}>
          <span className={styles.verdictIcon}>{feasible ? '\u2713' : '\u2717'}</span>
          <span className={styles.verdictText}>
            {feasible ? 'Feasible' : 'Not Feasible'}
          </span>
        </div>
        {gap.bottleneck && (
          <div className={styles.bottleneck}>
            <span className={styles.bottleneckLabel}>Bottleneck:</span>
            <span>{gap.bottleneck}</span>
          </div>
        )}
        {gap.margin != null && (
          <div className={styles.margin}>
            Margin: {(gap.margin * 100).toFixed(1)}%
          </div>
        )}
        {gap.message && (
          <div className={styles.message}>{gap.message}</div>
        )}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'gap-analysis',
  label: 'Gap Analysis',
  category: 'event-prep',
  description: 'Feasible/not feasible card with bottleneck identification',
  component: GapAnalysis,
  dataKeys: ['selectedRouteId', 'routeAnalysis'],
})
