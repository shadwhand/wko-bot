import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { FlagCard } from './FlagCard'
import { registerPanel } from '../../layout/PanelRegistry'

export function PanicTraining() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  const flag = (flags.flags ?? []).find((f) => f.name === 'panic_training')
  if (!flag) return <PanelEmpty message="Panic training check not available" />

  return (
    <FlagCard
      name="Panic Training"
      status={flag.status}
      value={typeof flag.value === 'number' ? `${flag.value.toFixed(0)} TSS/wk` : flag.value}
      detail={flag.detail}
      tooltip={{
        fullName: 'Panic Training Detection',
        derivation: 'Sudden jump in weekly TSS following a low-load period.',
        context: 'Sudden volume spikes after detraining increase injury risk. Ramp gradually.',
      }}
    />
  )
}

registerPanel({
  id: 'panic-training',
  label: 'Panic Training',
  category: 'health',
  description: 'Detects sudden intensity spikes after low-load periods',
  component: PanicTraining,
  dataKeys: ['clinicalFlags'],
})
