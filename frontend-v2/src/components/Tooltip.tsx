import { useState, useRef, type ReactNode } from 'react'
import styles from './Tooltip.module.css'

interface TooltipProps {
  /** Short metric name (e.g., "CTL") */
  label: string
  /** Full name (e.g., "Chronic Training Load") */
  fullName: string
  /** How derived (e.g., "Exponentially weighted average of daily TSS, 42-day time constant") */
  derivation: string
  /** Training context (e.g., "Higher = more fit. Typical target: 60-100 for competitive amateur") */
  context?: string
  children: ReactNode
}

export function Tooltip({ label, fullName, derivation, context, children }: TooltipProps) {
  const [visible, setVisible] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  return (
    <div
      className={styles.wrapper}
      ref={ref}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      aria-describedby={visible ? `tooltip-${label}` : undefined}
    >
      {children}
      {visible && (
        <div
          id={`tooltip-${label}`}
          role="tooltip"
          className={styles.tooltip}
        >
          <div className={styles.title}>{fullName}</div>
          <div className={styles.derivation}>{derivation}</div>
          {context && <div className={styles.context}>{context}</div>}
        </div>
      )}
    </div>
  )
}
