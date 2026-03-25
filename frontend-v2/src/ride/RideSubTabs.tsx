// frontend-v2/src/ride/RideSubTabs.tsx

const TABS = [
  { id: 'timeline', label: 'Timeline' },
  { id: 'power', label: 'Power' },
  { id: 'hr', label: 'HR' },
  { id: 'zones', label: 'Zones' },
  { id: 'data', label: 'Data' },
] as const;

type TabId = typeof TABS[number]['id'];

interface Props {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
}

export function RideSubTabs({ activeTab, onTabChange }: Props) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 0,
        borderBottom: '1px solid var(--border)',
        marginBottom: 16,
      }}
    >
      {TABS.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          style={{
            padding: '8px 16px',
            background: 'none',
            border: 'none',
            borderBottom:
              activeTab === tab.id
                ? '2px solid var(--accent)'
                : '2px solid transparent',
            color:
              activeTab === tab.id
                ? 'var(--text-primary)'
                : 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontFamily: 'inherit',
          }}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export type { TabId };
