import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { registerPanel } from '../../layout/PanelRegistry'

export function RecentRides() {
  const activities = useDataStore(s => s.activities)
  const loading = useDataStore(s => s.loading.has('activities'))
  const error = useDataStore(s => s.errors['activities'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!activities || activities.length === 0) {
    return <PanelEmpty message="No recent rides" />
  }

  const recent = activities.slice(0, 5)

  const columns = [
    {
      key: 'start_time',
      label: 'Date',
      render: (row: any) => new Date(row.start_time).toLocaleDateString(),
    },
    {
      key: 'sub_sport',
      label: 'Type',
      render: (row: any) => row.sub_sport ?? 'ride',
    },
    {
      key: 'total_elapsed_time',
      label: 'Duration',
      render: (row: any) => {
        const v = row.total_elapsed_time
        if (v == null) return '--'
        const h = Math.floor(v / 3600)
        const m = Math.floor((v % 3600) / 60)
        return h > 0 ? `${h}h ${m}m` : `${m}m`
      },
    },
    {
      key: 'normalized_power',
      label: 'NP',
      render: (row: any) =>
        row.normalized_power != null ? `${Math.round(row.normalized_power)}W` : '--',
    },
    {
      key: 'training_stress_score',
      label: 'TSS',
      render: (row: any) =>
        row.training_stress_score != null
          ? Math.round(row.training_stress_score).toString()
          : '--',
    },
  ]

  return (
    <DataTable
      data={recent}
      columns={columns}
      keyField="id"
    />
  )
}

registerPanel({
  id: 'recent-rides',
  label: 'Recent Rides',
  category: 'status',
  description: 'Last 5 rides with key metrics',
  component: RecentRides,
  dataKeys: ['activities'],
})
