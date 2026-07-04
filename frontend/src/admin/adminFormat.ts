// Non-component admin helpers — split out of AdminCharts.tsx so that file can
// stay component-only (react-refresh/only-export-components).

export const ATTR_LABELS: Record<string, string> = {
  spice_level: 'Spice', richness: 'Richness', dairy_content: 'Dairy',
  sauce_heaviness: 'Sauce', texture_softness: 'Softness', savory_umami: 'Umami',
  veggie_density: 'Veggie', sweetness: 'Sweet',
}

export function prettyKey(k: string): string {
  return ATTR_LABELS[k] ?? k.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function fmtDate(iso: string): string {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}
