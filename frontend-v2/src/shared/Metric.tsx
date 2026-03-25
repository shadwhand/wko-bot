import styles from './Metric.module.css'

interface MetricProps {
  value: number | string | null | undefined
  label: string
  unit?: string
  color?: string
  decimals?: number
}

export function Metric({ value, label, unit, color, decimals = 0 }: MetricProps) {
  const display =
    value == null
      ? '--'
      : typeof value === 'number'
        ? value.toFixed(decimals)
        : value

  return (
    <div className={styles.metric}>
      <span className={styles.value} style={color ? { color } : undefined}>
        {display}
        {unit && <span className={styles.unit}>{unit}</span>}
      </span>
      <span className={styles.label}>{label}</span>
    </div>
  )
}
