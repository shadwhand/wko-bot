import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useLayoutStore } from './layoutStore'
import { getPanelComponent } from './PanelRegistry'
import { PanelWrapper } from './PanelWrapper'
import { PanelCatalogModal } from '../components/PanelCatalogModal'
import { ConfirmDialog } from '../components/ConfirmDialog'
import styles from './EditMode.module.css'

/** Sortable wrapper for each panel in edit mode */
function SortablePanel({
  panelId,
  tabId,
}: {
  panelId: string
  tabId: string
}) {
  const removePanel = useLayoutStore(s => s.removePanel)
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: panelId })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  const Component = getPanelComponent(panelId)

  return (
    <div ref={setNodeRef} style={style}>
      <PanelWrapper
        panelId={panelId}
        editMode={true}
        onRemove={() => removePanel(tabId, panelId)}
        dragHandleProps={{ ...attributes, ...listeners }}
      >
        {Component ? (
          <Component />
        ) : (
          <div className={styles.placeholder}>
            Panel "{panelId}" — not yet implemented
          </div>
        )}
      </PanelWrapper>
    </div>
  )
}

/** Editable tab bar with rename + remove */
function EditableTabBar() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const setActiveTab = useLayoutStore(s => s.setActiveTab)
  const addTab = useLayoutStore(s => s.addTab)
  const removeTab = useLayoutStore(s => s.removeTab)
  const renameTab = useLayoutStore(s => s.renameTab)
  const [editingTabId, setEditingTabId] = useState<string | null>(null)
  const [editingLabel, setEditingLabel] = useState('')

  const handleStartRename = (tabId: string, label: string) => {
    setEditingTabId(tabId)
    setEditingLabel(label)
  }

  const handleFinishRename = () => {
    if (editingTabId && editingLabel.trim()) {
      renameTab(editingTabId, editingLabel.trim())
    }
    setEditingTabId(null)
  }

  const handleAddTab = () => {
    const name = prompt('Tab name (max 30 chars):')
    if (name?.trim()) {
      addTab(name.trim())
    }
  }

  return (
    <div className={styles.editTabBar}>
      {layout.tabs.map(tab => (
        <div
          key={tab.id}
          className={`${styles.editTab} ${tab.id === activeTabId ? styles.activeEditTab : ''}`}
        >
          {editingTabId === tab.id ? (
            <input
              className={styles.tabNameInput}
              value={editingLabel}
              onChange={e => setEditingLabel(e.target.value)}
              onBlur={handleFinishRename}
              onKeyDown={e => {
                if (e.key === 'Enter') handleFinishRename()
                if (e.key === 'Escape') setEditingTabId(null)
              }}
              maxLength={30}
              autoFocus
            />
          ) : (
            <button
              className={styles.tabButton}
              onClick={() => setActiveTab(tab.id)}
              onDoubleClick={() => handleStartRename(tab.id, tab.label)}
              title="Click to switch, double-click to rename"
            >
              {tab.label}
            </button>
          )}
          {layout.tabs.length > 1 && (
            <button
              className={styles.tabRemove}
              onClick={() => removeTab(tab.id)}
              aria-label={`Remove ${tab.label} tab`}
              title="Remove tab"
            >
              ×
            </button>
          )}
        </div>
      ))}
      <button
        className={styles.addTabButton}
        onClick={handleAddTab}
        aria-label="Add tab"
        title="Add new tab"
      >
        +
      </button>
    </div>
  )
}

export function EditMode() {
  const layout = useLayoutStore(s => s.layout)
  const activeTabId = useLayoutStore(s => s.activeTabId)
  const exitEditMode = useLayoutStore(s => s.exitEditMode)
  const resetToDefault = useLayoutStore(s => s.resetToDefault)
  const reorderPanels = useLayoutStore(s => s.reorderPanels)
  const addPanel = useLayoutStore(s => s.addPanel)

  const [catalogOpen, setCatalogOpen] = useState(false)
  const [resetDialogOpen, setResetDialogOpen] = useState(false)

  const activeTab = layout.tabs.find(t => t.id === activeTabId)
  const panelIds = activeTab?.panels ?? []

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return

    const oldIndex = panelIds.indexOf(active.id as string)
    const newIndex = panelIds.indexOf(over.id as string)
    if (oldIndex !== -1 && newIndex !== -1) {
      reorderPanels(activeTabId, oldIndex, newIndex)
    }
  }

  const handleReset = () => {
    resetToDefault()
    setResetDialogOpen(false)
  }

  return (
    <div className={styles.editContainer}>
      {/* Edit mode toolbar */}
      <div className={styles.toolbar}>
        <span className={styles.toolbarLabel}>Editing Layout</span>
        <div className={styles.toolbarActions}>
          <button
            className={styles.resetButton}
            onClick={() => setResetDialogOpen(true)}
          >
            Reset to Default
          </button>
          <button
            className={styles.cancelButton}
            onClick={() => exitEditMode(false)}
          >
            Cancel
          </button>
          <button
            className={styles.doneButton}
            onClick={() => exitEditMode(true)}
          >
            Done
          </button>
        </div>
      </div>

      {/* Editable tab bar */}
      <EditableTabBar />

      {/* Sortable panel grid */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext items={panelIds} strategy={verticalListSortingStrategy}>
          <div className={styles.panelGrid}>
            {panelIds.map(panelId => (
              <SortablePanel
                key={panelId}
                panelId={panelId}
                tabId={activeTabId}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>

      {/* Add panel button */}
      <div className={styles.addPanelArea}>
        <button
          className={styles.addPanelButton}
          onClick={() => setCatalogOpen(true)}
        >
          + Add Panel
        </button>
      </div>

      {/* Panel catalog modal */}
      <PanelCatalogModal
        open={catalogOpen}
        existingPanels={panelIds}
        onSelect={panelId => addPanel(activeTabId, panelId)}
        onClose={() => setCatalogOpen(false)}
      />

      {/* Reset confirmation dialog */}
      <ConfirmDialog
        open={resetDialogOpen}
        title="Reset Layout"
        message="Reset to default? This replaces your current layout."
        confirmLabel="Reset"
        variant="danger"
        onConfirm={handleReset}
        onCancel={() => setResetDialogOpen(false)}
      />
    </div>
  )
}
