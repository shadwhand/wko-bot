import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

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

export function CogganRanking() {
  const profile = useDataStore(s => s.profile)
  const loading = useDataStore(s => s.loading.has('profile'))
  const error = useDataStore(s => s.errors['profile'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!profile?.ranking) return <PanelEmpty message="No ranking data" />

  const rows = Object.entries(profile.ranking).map(([duration, rank]) => ({
    duration,
    ranking: RANKING_LABELS[rank as string] ?? rank,
    watts: profile.profile?.watts?.[duration] ?? null,
    wkg: profile.profile?.wkg?.[duration] ?? null,
  }))

  const columns = [
    { key: 'duration', label: 'Duration' },
    {
      key: 'watts',
      label: 'Watts',
      render: (row: any) => row.watts != null ? `${Math.round(row.watts)}W` : '\u2014',
    },
    {
      key: 'wkg',
      label: 'W/kg',
      render: (row: any) => row.wkg != null ? row.wkg.toFixed(2) : '\u2014',
    },
    { key: 'ranking', label: 'Ranking' },
  ]

  return (
    <Tooltip
      label="CogganRanking"
      fullName="Coggan Power Profile Classification"
      derivation="Peak power at each duration classified against Coggan's published categories."
      context="Based on 90-day best efforts. Test key durations to get accurate classification."
    >
      <DataTable data={rows} columns={columns} keyField="duration" />
    </Tooltip>
  )
}

registerPanel({
  id: 'coggan-ranking',
  label: 'Coggan Ranking',
  category: 'profile',
  description: 'Power profile vs Coggan classification table',
  component: CogganRanking,
  dataKeys: ['profile'],
})
