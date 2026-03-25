import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function AthleteConfig() {
  const config = useDataStore(s => s.config)
  const loading = useDataStore(s => s.loading.has('config'))
  const error = useDataStore(s => s.errors['config'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!config) return <PanelEmpty message="No config data" />

  // Display config as key-value pairs
  const rows = Object.entries(config)
    .filter(([k]) => !k.startsWith('_'))
    .map(([key, value]) => ({
      key,
      value: typeof value === 'object' ? JSON.stringify(value) : String(value ?? '\u2014'),
    }))

  const columns = [
    { key: 'key', label: 'Setting' },
    { key: 'value', label: 'Value' },
  ]

  return (
    <Tooltip
      label="Config"
      fullName="Athlete Configuration"
      derivation="Settings stored in the backend config (wko5.db). Edit via API or config file."
      context="Key settings: FTP, weight, CdA, max HR. These drive all derived metrics."
    >
      <DataTable data={rows} columns={columns} keyField="key" />
    </Tooltip>
  )
}

registerPanel({
  id: 'athlete-config',
  label: 'Athlete Config',
  category: 'profile',
  description: 'Athlete configuration display (read-only)',
  component: AthleteConfig,
  dataKeys: ['config'],
})
