const MOODS = ['Any', 'Comfort', 'Adventurous', 'Light'] as const
const DIETS = ['Standard', 'Vegetarian', 'Vegan', 'Restricted'] as const

export type MoodOption = (typeof MOODS)[number]
export type DietOption = (typeof DIETS)[number]

export function moodToApi(m: MoodOption): string {
  return m === 'Any' ? 'no_preference' : m.toLowerCase()
}

export function dietToApi(d: DietOption): string {
  return d.toLowerCase()
}

interface MoodSelectorProps {
  mood: MoodOption
  dietary: DietOption
  onMoodChange: (m: MoodOption) => void
  onDietaryChange: (d: DietOption) => void
}

const ACCENT = '#E85D04'

function Pill({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      style={{
        padding: '5px 12px', borderRadius: 100, fontSize: '0.75rem', fontWeight: 700,
        cursor: 'pointer', border: '1.5px solid', transition: 'all 0.15s ease',
        letterSpacing: '0.02em', whiteSpace: 'nowrap', fontFamily: 'inherit',
        background: active ? ACCENT : 'transparent',
        borderColor: active ? ACCENT : '#E8E0D8',
        color: active ? '#FFFFFF' : '#6B6B6B',
        boxShadow: active ? `0 2px 8px rgba(232,93,4,0.3)` : 'none',
      }}
      onClick={onClick}
      onMouseEnter={e => { if (!active) { e.currentTarget.style.borderColor = ACCENT; e.currentTarget.style.color = ACCENT } }}
      onMouseLeave={e => { if (!active) { e.currentTarget.style.borderColor = '#E8E0D8'; e.currentTarget.style.color = '#6B6B6B' } }}
    >
      {label}
    </button>
  )
}

export function MoodSelector({ mood, dietary, onMoodChange, onDietaryChange }: MoodSelectorProps) {
  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#B0A89E', letterSpacing: '0.08em', textTransform: 'uppercase', minWidth: 34, flexShrink: 0 }}>
          Mood
        </span>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {MOODS.map(m => (
            <Pill key={m} label={m} active={mood === m} onClick={() => onMoodChange(m)} />
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#B0A89E', letterSpacing: '0.08em', textTransform: 'uppercase', minWidth: 34, flexShrink: 0 }}>
          Diet
        </span>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {DIETS.map(d => (
            <Pill key={d} label={d} active={dietary === d} onClick={() => onDietaryChange(d)} />
          ))}
        </div>
      </div>
    </div>
  )
}
