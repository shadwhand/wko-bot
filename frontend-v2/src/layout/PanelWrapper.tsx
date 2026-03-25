import { Component, type ReactNode, type ErrorInfo } from 'react'
import { getPanel } from './PanelRegistry'
import styles from './PanelWrapper.module.css'

interface PanelWrapperProps {
  panelId: string
  editMode: boolean
  onRemove?: () => void
  /** dnd-kit drag handle attributes — spread onto the handle element */
  dragHandleProps?: Record<string, unknown>
  children: ReactNode
}

interface ErrorState {
  hasError: boolean
  error: Error | null
}

/** Error boundary that catches render errors in panel content */
class PanelErrorBoundary extends Component<
  { panelId: string; children: ReactNode },
  ErrorState
> {
  state: ErrorState = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): ErrorState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error(`[Panel ${this.props.panelId}] Render error:`, error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.errorContent}>
          <div className={styles.errorIcon}>!</div>
          <div className={styles.errorMessage}>
            This panel encountered an error
          </div>
          <div className={styles.errorDetail}>
            {this.state.error?.message}
          </div>
          <button
            className={styles.retryButton}
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export function PanelWrapper({
  panelId,
  editMode,
  onRemove,
  dragHandleProps,
  children,
}: PanelWrapperProps) {
  const def = getPanel(panelId)
  const label = def?.label ?? panelId

  return (
    <div
      className={`${styles.panel} ${editMode ? styles.editing : ''}`}
      data-panel-id={panelId}
    >
      {/* Structured header bar — dark chrome, drag handle in edit mode */}
      <div
        className={styles.headerBar}
        {...(editMode ? dragHandleProps : {})}
      >
        <span className={styles.title}>{label}</span>

        {/* Legend area — panels can portal content here via panelId */}
        <div className={styles.legend} id={`panel-legend-${panelId}`} />

        {editMode && (
          <button
            className={styles.removeButton}
            onClick={onRemove}
            aria-label={`Remove ${label}`}
            title="Remove panel"
          >
            ×
          </button>
        )}
      </div>

      {/* Content area */}
      <div className={styles.content}>
        <PanelErrorBoundary panelId={panelId}>
          {children}
        </PanelErrorBoundary>
      </div>
    </div>
  )
}
