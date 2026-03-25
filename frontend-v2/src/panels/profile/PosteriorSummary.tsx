import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { DataTable } from '../../shared/DataTable'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'

export function PosteriorSummary() {
  const model = useDataStore(s => s.model)
  const loading = useDataStore(s => s.loading.has('model'))
  const error = useDataStore(s => s.errors['model'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!model) return <PanelEmpty message="No model data" />

  // Build rows from model parameters
  const params = [
    { param: 'mFTP', value: model.mFTP, unit: 'W' },
    { param: 'Pmax', value: model.Pmax, unit: 'W' },
    { param: 'FRC', value: model.FRC, unit: 'kJ' },
    { param: 'TTE', value: model.TTE, unit: 'min' },
    { param: 'mVO2max', value: model.mVO2max_ml_min_kg, unit: 'ml/min/kg' },
  ].filter(p => p.value != null)

  const columns = [
    { key: 'param', label: 'Parameter' },
    {
      key: 'value',
      label: 'Estimate',
      render: (row: any) =>
        row.unit === 'kJ'
          ? `${(row.value / 1000).toFixed(1)} ${row.unit}`
          : `${typeof row.value === 'number' ? (row.value < 100 ? row.value.toFixed(1) : Math.round(row.value)) : row.value} ${row.unit}`,
    },
  ]

  return (
    <Tooltip
      label="Posterior"
      fullName="Model Parameter Summary"
      derivation="Parameters from the power-duration model fit to your 90-day MMP envelope."
      context="mFTP = modeled FTP (not 95% of 20min). FRC = anaerobic capacity above FTP. TTE = time to exhaustion at FTP."
    >
      <DataTable data={params} columns={columns} keyField="param" />
    </Tooltip>
  )
}

registerPanel({
  id: 'posterior-summary',
  label: 'Posterior Summary',
  category: 'profile',
  description: 'PD model parameter estimates',
  component: PosteriorSummary,
  dataKeys: ['model'],
})
