import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { registerPanel } from '../../layout/PanelRegistry'

export function RedsScreen() {
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />

  // RED-S screening is not yet provided by the clinical flags API.
  // Show a clear placeholder instead of the misleading "not available" message.
  return (
    <PanelEmpty message="RED-S screening not yet implemented. This panel will activate once the RED-S check is added to the clinical flags API." />
  )
}

registerPanel({
  id: 'reds-screen',
  label: 'RED-S Screen',
  category: 'health',
  description: 'Relative Energy Deficiency screening',
  component: RedsScreen,
  dataKeys: ['clinicalFlags'],
})
