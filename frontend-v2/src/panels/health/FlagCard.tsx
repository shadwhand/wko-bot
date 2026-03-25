import { Tooltip } from '../../components/Tooltip'
import styles from './FlagCard.module.css'

interface FlagCardProps {
  name: string
  status: 'ok' | 'warning' | 'danger'
  value: number | string
  threshold?: number | string
  detail?: string
  tooltip: {
    fullName: string
    derivation: string
    context?: string
  }
}

export function FlagCard({ name, status, value, threshold, detail, tooltip }: FlagCardProps) {
  return (
    <Tooltip label={name} {...tooltip}>
      <div className={`${styles.card} ${styles[status]}`}>
        <div className={styles.header}>
          <span className={styles.statusDot} />
          <span className={styles.name}>{name}</span>
        </div>
        <div className={styles.value}>{value}</div>
        {threshold != null && (
          <div className={styles.threshold}>
            Threshold: {threshold}
          </div>
        )}
        {detail && <div className={styles.detail}>{detail}</div>}
      </div>
    </Tooltip>
  )
}
