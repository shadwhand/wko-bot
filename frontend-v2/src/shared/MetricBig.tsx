import styles from './Metric.module.css'

interface MetricBigProps {
  value: number | string | null | undefined
  label: string
  unit?: string
  color?: string
  decimals?: number
}

export function MetricBig({ value, label, unit, color, decimals = 0 }: MetricBigProps) {
  const display =
    value == null
      ? '--'
      : typeof value === 'number'
        ? value.toFixed(decimals)
        : value

  return (
    <div className={styles.metricBig}>
      <span className={styles.bigValue} style={color ? { color } : undefined}>
        {display}
        {unit && <span className={styles.bigUnit}>{unit}</span>}
      </span>
      <span className={styles.bigLabel}>{label}</span>
    </div>
  )
}
