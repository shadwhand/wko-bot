import { useEffect, useRef } from 'react'

interface ConfirmDialogProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: 'danger' | 'default'
  onConfirm: () => void
  onCancel: () => void
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (open && !dialog.open) {
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  }, [open])

  if (!open) return null

  return (
    <dialog
      ref={dialogRef}
      style={{
        background: 'var(--color-bg-secondary, #21262d)',
        color: 'var(--color-text-primary, #e6edf3)',
        border: '1px solid var(--color-border, #30363d)',
        borderRadius: '8px',
        padding: '20px',
        maxWidth: '400px',
      }}
      onClose={onCancel}
    >
      <h3 style={{ margin: '0 0 8px', fontSize: '16px' }}>{title}</h3>
      <p style={{ margin: '0 0 16px', fontSize: '14px', color: 'var(--color-text-secondary, #8b949e)' }}>
        {message}
      </p>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
        <button
          onClick={onCancel}
          style={{
            padding: '6px 14px',
            border: '1px solid var(--color-border, #30363d)',
            borderRadius: '6px',
            background: 'transparent',
            color: 'var(--color-text-primary, #e6edf3)',
            cursor: 'pointer',
            fontSize: '13px',
          }}
        >
          {cancelLabel}
        </button>
        <button
          onClick={onConfirm}
          style={{
            padding: '6px 14px',
            border: 'none',
            borderRadius: '6px',
            background: variant === 'danger'
              ? 'var(--color-danger, #f85149)'
              : 'var(--color-accent, #58a6ff)',
            color: '#fff',
            cursor: 'pointer',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          {confirmLabel}
        </button>
      </div>
    </dialog>
  )
}
