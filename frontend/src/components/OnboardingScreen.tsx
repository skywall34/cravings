import { useState, useEffect } from 'react'
import { postOnboarding } from '../api'
import type { GuestPrefs } from '../api'

const PREFS = [
  { key: 'spice',    label: 'Spice',    emoji: '🌶️', lo: 'Mild',   hi: 'Fiery'   },
  { key: 'sweet',    label: 'Sweet',    emoji: '🍯', lo: 'Savory', hi: 'Sweet'   },
  { key: 'sour',     label: 'Sour',     emoji: '🍋', lo: 'Mellow', hi: 'Tangy'   },
  { key: 'texture',  label: 'Texture',  emoji: '🥢', lo: 'Soft',   hi: 'Crunchy' },
  { key: 'richness', label: 'Richness', emoji: '🧈', lo: 'Light',  hi: 'Rich'    },
] as const

type PrefKey = (typeof PREFS)[number]['key']

const DIETARY_OPTIONS: { key: string; label: string }[] = [
  { key: 'vegetarian',       label: 'Vegetarian' },
  { key: 'vegan',            label: 'Vegan' },
  { key: 'gluten_free',      label: 'Gluten-free' },
  { key: 'dairy_free',       label: 'Dairy-free' },
  { key: 'halal',            label: 'Halal' },
  { key: 'kosher',           label: 'Kosher' },
  { key: 'contains_nuts',    label: 'No nuts' },
  { key: 'contains_shellfish', label: 'No shellfish' },
  { key: 'contains_soy',    label: 'No soy' },
  { key: 'contains_eggs',   label: 'No eggs' },
]

interface PrefSliderProps {
  emoji: string
  label: string
  lo: string
  hi: string
  value: number
  onChange: (val: number) => void
}

function PrefSlider({ emoji, label, lo, hi, value, onChange }: PrefSliderProps) {
  const pct = ((value + 1) / 2) * 100
  const displayVal = value === 0 ? 'Neutral' : value > 0 ? `+${(value * 100).toFixed(0)}%` : `${(value * 100).toFixed(0)}%`

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ fontSize: '1.1rem', lineHeight: 1 }}>{emoji}</span>
        <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#1A1A1A', flex: 1 }}>{label}</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#B0A89E', minWidth: 40, textAlign: 'right' }}>
          {displayVal}
        </span>
      </div>
      <div style={{ position: 'relative', height: 6, background: '#E8E0D8', borderRadius: 3, overflow: 'visible' }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, height: '100%', borderRadius: 3,
          width: `${pct}%`,
          background: 'linear-gradient(90deg, rgba(232,93,4,0.6), #E85D04)',
          pointerEvents: 'none', transition: 'width 0.1s ease',
        }} />
        <input
          type="range" min={-100} max={100} step={5}
          value={Math.round(value * 100)}
          onChange={e => onChange(parseInt(e.target.value) / 100)}
          className="onboarding-slider"
          style={{
            position: 'absolute', top: '50%', left: 0, width: '100%',
            transform: 'translateY(-50%)', appearance: 'none',
            background: 'transparent', cursor: 'pointer', margin: 0, padding: 0, height: 20,
          }}
        />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#B0A89E', fontWeight: 600, letterSpacing: '0.03em' }}>
        <span>{lo}</span>
        <span>{hi}</span>
      </div>
    </div>
  )
}

interface OnboardingScreenProps {
  onComplete: (dietary: GuestPrefs) => void
  onSkip: (dietary: GuestPrefs) => void
  hasExistingProfile?: boolean
  isRegistered?: boolean
  initialDietary?: GuestPrefs
}

export function OnboardingScreen({
  onComplete,
  onSkip,
  hasExistingProfile = false,
  isRegistered = false,
  initialDietary,
}: OnboardingScreenProps) {
  const [prefs, setPrefs] = useState<Record<PrefKey, number>>({
    spice: 0, sweet: 0, sour: 0, texture: 0, richness: 0,
  })
  const [dietaryRestrictions, setDietaryRestrictions] = useState<Set<string>>(
    new Set(initialDietary?.dietaryRestrictions ?? [])
  )
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    const style = document.createElement('style')
    style.id = 'onboarding-slider-css'
    style.textContent = `
      .onboarding-slider::-webkit-slider-thumb {
        -webkit-appearance: none; appearance: none;
        width: 20px; height: 20px; border-radius: 50%;
        background: #E85D04; border: 3px solid white;
        box-shadow: 0 2px 8px rgba(232,93,4,0.35); cursor: pointer;
        transition: transform 0.15s ease;
      }
      .onboarding-slider::-webkit-slider-thumb:hover { transform: scale(1.2); }
      .onboarding-slider::-moz-range-thumb {
        width: 20px; height: 20px; border-radius: 50%;
        background: #E85D04; border: 3px solid white;
        box-shadow: 0 2px 8px rgba(232,93,4,0.35); cursor: pointer;
      }
    `
    if (!document.getElementById('onboarding-slider-css')) {
      document.head.appendChild(style)
    }
    return () => { document.getElementById('onboarding-slider-css')?.remove() }
  }, [])

  const handleChange = (key: PrefKey, val: number) => {
    setPrefs(p => ({ ...p, [key]: val }))
  }

  const toggleDietary = (key: string) => {
    setDietaryRestrictions(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const PREF_KEY_MAP: Record<string, string> = {
    spice: 'spice_level',
    sweet: 'sweetness',
    sour: 'sourness',
    texture: 'texture_softness',
    richness: 'richness',
  }

  const guestPrefs: GuestPrefs = {
    dietaryRestrictions: Array.from(dietaryRestrictions),
    safetyOverrides: [],
    tastePrefs: Object.fromEntries(
      Object.entries(prefs).map(([k, v]) => [PREF_KEY_MAP[k] ?? k, v])
    ),
  }

  const handleStart = async () => {
    setSaving(true)
    try {
      if (isRegistered) {
        await postOnboarding(prefs)
      }
    } catch {
      // non-fatal — still proceed
    } finally {
      setSaving(false)
      onComplete(guestPrefs)
    }
  }

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <div style={{ padding: '16px 0 20px', textAlign: 'center' }}>
        <p style={{ fontSize: '0.95rem', color: '#6B6B6B', lineHeight: 1.6, margin: 0 }}>
          {hasExistingProfile
            ? 'Update your taste profile, or skip to use your saved one.'
            : 'Let\'s learn your taste. A few quick questions — or just dive in.'}
        </p>
      </div>

      <div style={{
        width: '100%', background: '#FFFFFF', borderRadius: 24,
        boxShadow: '0 8px 40px rgba(232, 93, 4, 0.12), 0 2px 8px rgba(0,0,0,0.06)',
        padding: '28px 28px 24px', display: 'flex', flexDirection: 'column', gap: 24,
      }}>
        {/* Dietary restrictions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1A1A1A', margin: 0 }}>
            Dietary restrictions
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#B0A89E', margin: '-4px 0 0', lineHeight: 1.5 }}>
            We'll filter out items that don't fit.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {DIETARY_OPTIONS.map(opt => {
              const active = dietaryRestrictions.has(opt.key)
              return (
                <button
                  key={opt.key}
                  onClick={() => toggleDietary(opt.key)}
                  style={{
                    padding: '6px 14px', borderRadius: 100, fontSize: '0.8rem', fontWeight: 600,
                    border: active ? '2px solid #E85D04' : '2px solid #E8E0D8',
                    background: active ? 'rgba(232,93,4,0.08)' : '#FAFAF9',
                    color: active ? '#E85D04' : '#6B6B6B',
                    cursor: 'pointer', fontFamily: 'inherit',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {opt.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Taste sliders */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#1A1A1A', margin: 0 }}>
            Your taste profile
          </h2>
          <p style={{ fontSize: '0.82rem', color: '#B0A89E', margin: '-4px 0 0', lineHeight: 1.5 }}>
            Drag sliders to set your preferences. Everything can change as you swipe.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {PREFS.map(pref => (
              <PrefSlider
                key={pref.key}
                emoji={pref.emoji}
                label={pref.label}
                lo={pref.lo}
                hi={pref.hi}
                value={prefs[pref.key]}
                onChange={val => handleChange(pref.key, val)}
              />
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, paddingTop: 4 }}>
          <button
            style={{
              width: '100%', padding: '16px', border: 'none', borderRadius: 100,
              background: '#E85D04', color: '#FFFFFF', fontSize: '1rem', fontWeight: 700,
              cursor: saving ? 'not-allowed' : 'pointer', letterSpacing: '0.02em',
              transition: 'opacity 0.15s ease, transform 0.15s ease',
              boxShadow: '0 4px 20px rgba(232,93,4,0.25)', fontFamily: 'inherit',
              opacity: saving ? 0.7 : 1,
            }}
            onClick={() => void handleStart()}
            disabled={saving}
            onMouseEnter={e => { if (!saving) { e.currentTarget.style.opacity = '0.9'; e.currentTarget.style.transform = 'translateY(-1px)' } }}
            onMouseLeave={e => { e.currentTarget.style.opacity = saving ? '0.7' : '1'; e.currentTarget.style.transform = 'translateY(0)' }}
          >
            Start Swiping →
          </button>
          <button
            style={{
              background: 'none', border: 'none', fontSize: '0.82rem', fontWeight: 600,
              color: '#B0A89E', cursor: 'pointer', letterSpacing: '0.03em',
              transition: 'color 0.15s ease', padding: '4px 8px', fontFamily: 'inherit',
            }}
            onClick={() => onSkip(guestPrefs)}
            onMouseEnter={e => { e.currentTarget.style.color = '#E85D04' }}
            onMouseLeave={e => { e.currentTarget.style.color = '#B0A89E' }}
          >
            {hasExistingProfile ? 'use saved profile →' : 'skip for now →'}
          </button>
        </div>
      </div>
    </div>
  )
}
