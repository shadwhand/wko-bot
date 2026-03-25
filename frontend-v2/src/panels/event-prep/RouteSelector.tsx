import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { registerPanel } from '../../layout/PanelRegistry'

export function RouteSelector() {
  const routes = useDataStore(s => s.routes)
  const selectedRouteId = useDataStore(s => s.selectedRouteId)
  const setSelectedRoute = useDataStore(s => s.setSelectedRoute)
  const loading = useDataStore(s => s.loading.has('routes'))
  const error = useDataStore(s => s.errors['routes'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!routes || routes.length === 0) {
    return <PanelEmpty message="No routes available. Import a route first." />
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <label
        htmlFor="route-select"
        style={{ fontSize: '13px', color: 'var(--color-text-secondary)', fontWeight: 500 }}
      >
        Target Route:
      </label>
      <select
        id="route-select"
        value={selectedRouteId ?? ''}
        onChange={e => {
          const val = e.target.value
          setSelectedRoute(val ? Number(val) : null)
        }}
        style={{
          padding: '6px 10px',
          border: '1px solid var(--color-border, #30363d)',
          borderRadius: '6px',
          background: 'var(--color-bg-primary, #161b22)',
          color: 'var(--color-text-primary, #e6edf3)',
          fontSize: '13px',
          flex: 1,
          maxWidth: '400px',
        }}
      >
        <option value="">Select a route...</option>
        {routes.map((r: any) => (
          <option key={r.id} value={r.id}>
            {r.name} ({r.distance_km?.toFixed(1) ?? '?'} km, {r.elevation_m?.toFixed(0) ?? '?'} m)
          </option>
        ))}
      </select>
    </div>
  )
}

registerPanel({
  id: 'route-selector',
  label: 'Route Selector',
  category: 'event-prep',
  description: 'Dropdown that selects the target route for Event Prep analysis',
  component: RouteSelector,
  dataKeys: ['routes', 'selectedRouteId'],
})
