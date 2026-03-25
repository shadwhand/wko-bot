import { useDataStore } from '../../store/data-store'
import { PanelSkeleton } from '../../shared/PanelSkeleton'
import { PanelError } from '../../shared/PanelError'
import { PanelEmpty } from '../../shared/PanelEmpty'
import { Tooltip } from '../../components/Tooltip'
import { registerPanel } from '../../layout/PanelRegistry'
import styles from './ClinicalAlert.module.css'

type Severity = 'danger' | 'warning' | 'ok'

export function ClinicalAlert() {
  const flags = useDataStore(s => s.clinicalFlags)
  const loading = useDataStore(s => s.loading.has('clinicalFlags'))
  const error = useDataStore(s => s.errors['clinicalFlags'])

  if (loading) return <PanelSkeleton />
  if (error) return <PanelError message={error} />
  if (!flags) return <PanelEmpty message="No clinical data" />

  // Determine overall severity: worst flag wins
  const flagList = flags.flags ?? []
  const hasDanger = flagList.some((f: any) => f.status === 'danger')
  const hasWarning = flagList.some((f: any) => f.status === 'warning')
  const severity: Severity = hasDanger ? 'danger' : hasWarning ? 'warning' : 'ok'

  const dangerCount = flagList.filter((f: any) => f.status === 'danger').length
  const warningCount = flagList.filter((f: any) => f.status === 'warning').length

  const message =
    severity === 'danger'
      ? `${dangerCount} critical alert${dangerCount > 1 ? 's' : ''} — review Health tab`
      : severity === 'warning'
        ? `${warningCount} warning${warningCount > 1 ? 's' : ''} — review Health tab`
        : 'All clinical checks passed'

  return (
    <Tooltip
      label="Clinical"
      fullName="Clinical Flags Summary"
      derivation="Aggregation of all clinical screening checks (IF floor, panic training, RED-S, overtraining)."
      context="Danger = immediate attention needed. Warning = monitor closely."
    >
      <div className={`${styles.banner} ${styles[severity]}`}>
        <span className={styles.icon}>
          {severity === 'ok' ? '\u2713' : '!'}
        </span>
        <span className={styles.message}>{message}</span>
      </div>
    </Tooltip>
  )
}

registerPanel({
  id: 'clinical-alert',
  label: 'Clinical Alert',
  category: 'status',
  description: 'Summary alert banner with severity color',
  component: ClinicalAlert,
  dataKeys: ['clinicalFlags'],
})
