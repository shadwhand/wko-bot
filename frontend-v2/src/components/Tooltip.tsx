import { useState, useRef, useEffect, useCallback, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
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
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null)
  const triggerRef = useRef<HTMLDivElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    // Position above the trigger, centered horizontally
    setPosition({
      top: rect.top + window.scrollY,
      left: rect.left + window.scrollX + rect.width / 2,
    })
  }, [])

  useEffect(() => {
    if (!visible) return
    updatePosition()
    // Reposition on scroll/resize while visible
    window.addEventListener('scroll', updatePosition, true)
    window.addEventListener('resize', updatePosition)
    return () => {
      window.removeEventListener('scroll', updatePosition, true)
      window.removeEventListener('resize', updatePosition)
    }
  }, [visible, updatePosition])

  // After rendering the portal tooltip, clamp it within the viewport
  useEffect(() => {
    if (!visible || !tooltipRef.current || !position) return
    const el = tooltipRef.current
    const rect = el.getBoundingClientRect()
    // Prevent horizontal overflow
    if (rect.left < 8) {
      el.style.transform = `translateX(${8 - rect.left}px)`
    } else if (rect.right > window.innerWidth - 8) {
      el.style.transform = `translateX(${window.innerWidth - 8 - rect.right}px)`
    }
  }, [visible, position])

  return (
    <div
      className={styles.wrapper}
      ref={triggerRef}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      aria-describedby={visible ? `tooltip-${label}` : undefined}
    >
      {children}
      {visible && position && createPortal(
        <div
          id={`tooltip-${label}`}
          ref={tooltipRef}
          role="tooltip"
          className={styles.tooltip}
          style={{
            position: 'absolute',
            top: position.top,
            left: position.left,
          }}
        >
          <div className={styles.title}>{fullName}</div>
          <div className={styles.derivation}>{derivation}</div>
          {context && <div className={styles.context}>{context}</div>}
        </div>,
        document.body,
      )}
    </div>
  )
}
