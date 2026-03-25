import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './OpportunityCost.module.css'

export function OpportunityCost() {
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const routeDetail = useDataStore(s =>
    s.selectedRouteId != null ? s.routeDetail[s.selectedRouteId] : null
  )
  const loading = useDataStore(s => s.loading.has('routeDetail'))
  const error = useDataStore(s => s.errors['routeDetail'])

  if (!selectedRouteId) {
    return <PanelEmpty message="Select a route to see opportunity cost" />
  }
  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!routeDetail?.opportunity_cost) {
    return <PanelEmpty message="No opportunity cost data" />
  }

  const items = routeDetail.opportunity_cost
  // Find max value for bar scaling
  const maxImpact = Math.max(...items.map((i: any) => Math.abs(i.impact ?? i.value ?? 0)), 1)

  return (
    <Tooltip
      label="OpportunityCost"
      fullName="Opportunity Cost — Training Priorities"
      derivation="Ranked training investments by expected time gain on the target route."
      context="Focus training on the highest-impact items for the biggest performance gain."
    >
      <div className={styles.list}>
        {items.map((item: any, idx: number) => {
          const impact = Math.abs(item.impact ?? item.value ?? 0)
          const pct = (impact / maxImpact) * 100

          return (
            <div key={idx} className={styles.row}>
              <div className={styles.label}>{item.name ?? item.label}</div>
              <div className={styles.barContainer}>
                <div
                  className={styles.bar}
                  style={{
                    width: `${pct}%`,
                    background: idx === 0
                      ? 'var(--color-accent, #58a6ff)'
                      : idx < 3
                        ? 'var(--color-success, #3fb950)'
                        : 'var(--color-text-secondary, #8b949e)',
                  }}
                />
              </div>
              <div className={styles.value}>
                {item.impact != null ? `${item.impact > 0 ? '+' : ''}${item.impact.toFixed(1)}s` : '\u2014'}
              </div>
            </div>
          )
        })}
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'opportunity-cost',
  label: 'Opportunity Cost',
  category: 'event-prep',
  description: 'Ranked training priorities — horizontal bar chart',
  component: OpportunityCost,
  dataKeys: ['selectedRouteId', 'routeDetail'],
})
