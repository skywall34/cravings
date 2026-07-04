// Non-component taste-profile helpers — split out of StatsCharts.tsx so that
// file can stay component-only (react-refresh/only-export-components).
import type { SwipeStats } from './api'
import { CUISINE_EMOJI } from './cuisineEmoji'

export function pct(right: number, left: number): number {
  const t = right + left
  return t > 0 ? right / t : 0
}

export function cap(s: string): string {
  return s ? s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, ' ') : s
}

export function formatHour(h: number): string {
  const display = h % 12 || 12
  const next = ((h + 1) % 12) || 12
  const nextSuffix = (h + 1) >= 12 && (h + 1) < 24 ? 'pm' : 'am'
  return `${display}–${next}${nextSuffix}`
}

export interface TasteProfile {
  persona: string
  personaDesc: string
  overallYes: number
  topCuisine: { cuisine: string; right: number; left: number }
  sureThing: { cuisine: string; right: number; left: number }
  topFlavor: [string, number]
  peakHour: { hour: number; right: number; left: number } | undefined
  insights: { icon: string; title: string; text: string }[]
}

export function deriveTasteProfile(stats: SwipeStats): TasteProfile {
  const cuisines = [...stats.cuisine_breakdown].sort((a, b) => (b.right + b.left) - (a.right + a.left))
  const topCuisine = cuisines[0] ?? { cuisine: 'unknown', right: 0, left: 0 }
  const totalRight = stats.cuisine_breakdown.reduce((s, c) => s + c.right, 0)
  const totalLeft = stats.cuisine_breakdown.reduce((s, c) => s + c.left, 0)
  const overallYes = pct(totalRight, totalLeft)

  const sureThing = [...cuisines]
    .filter(c => c.right + c.left >= 8)
    .sort((a, b) => pct(b.right, b.left) - pct(a.right, a.left))[0] ?? topCuisine

  const flavors = Object.entries(stats.flavor_profile).sort((a, b) => b[1] - a[1])
  const topFlavor: [string, number] = flavors[0] ? [flavors[0][0], flavors[0][1]] : ['Spicy', 0]

  const peakHour = [...stats.hour_breakdown].sort((a, b) => b.right - a.right)[0]

  // Adventurous vs cozy axis derived from cuisine variety (how broadly the user
  // says yes across cuisines) now that explicit mood is gone.
  const likedCuisines = cuisines.filter(c => c.right > 0).length
  const triedCuisines = cuisines.filter(c => c.right + c.left > 0).length || 1
  const variety = likedCuisines / triedCuisines

  const flavorWord: Record<string, string> = {
    Spicy: 'Heat-Seeker', Rich: 'Comfort Gourmand', Fresh: 'Clean-Eater',
    Sweet: 'Sweet Tooth', Umami: 'Savory Hunter',
  }
  const word = flavorWord[topFlavor[0]] ?? 'Explorer'
  let persona: string, personaDesc: string
  if (variety > 0.6) {
    persona = `The Adventurous ${word}`
    personaDesc = `You say yes across a wide range of cuisines — and lean ${topFlavor[0].toLowerCase()}. Comfort food is a sometimes thing.`
  } else if (variety < 0.35) {
    persona = `The Cozy ${word}`
    personaDesc = `You know what you love — usually something ${topFlavor[0].toLowerCase()} — and you order it with confidence.`
  } else {
    persona = `The Balanced ${word}`
    personaDesc = `You mix the familiar with the new, with a clear pull toward ${topFlavor[0].toLowerCase()} flavors.`
  }

  const flavorIcon: Record<string, string> = { Spicy: '🌶️', Rich: '🧈', Fresh: '🥬', Sweet: '🍯', Umami: '🍄' }
  const insights = [
    {
      icon: CUISINE_EMOJI[sureThing.cuisine] ?? '🍽️',
      title: `${cap(sureThing.cuisine)} is your sure thing`,
      text: `You say yes ${Math.round(pct(sureThing.right, sureThing.left) * 100)}% of the time it shows up.`,
    },
    {
      icon: flavorIcon[topFlavor[0]] ?? '✨',
      title: `${topFlavor[0]} runs your palate`,
      text: `It's the strongest signal in your flavor profile, at ${topFlavor[1]}/100.`,
    },
    {
      icon: '🕗',
      title: peakHour ? `Peak craving: ${formatHour(peakHour.hour)}` : 'Craving data incoming',
      text: peakHour ? `That's when you green-light the most dishes — ${peakHour.right} yes-swipes.` : 'Keep swiping to see your peak hours.',
    },
  ]

  return { persona, personaDesc, overallYes, topCuisine, sureThing, topFlavor, peakHour, insights }
}
