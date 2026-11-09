// Pure helpers for the Labs page: grouping, unit splitting, labels and chart bounds.

import type { LabFlag, LabMarker, LabResult, MarkerCategory } from './types'

export const CATEGORY_LABEL: Record<MarkerCategory, string> = {
  thyroid: 'Thyroid',
  androgens: 'Androgens',
  reproductive: 'Reproductive hormones',
  metabolic: 'Metabolic',
  other: 'Other',
}

const CATEGORY_ORDER = Object.keys(CATEGORY_LABEL) as MarkerCategory[]

// Words only: below / within / above the range printed on that report. Never "normal".
export function flagLabel(flag: LabFlag | null): string {
  if (flag === 'below') return 'Below range'
  if (flag === 'above') return 'Above range'
  if (flag === 'within') return 'Within range'
  return 'No range'
}

// The range as printed when we have that text, otherwise built from the two ends.
export function rangeLabel(r: Pick<LabResult, 'ref_low' | 'ref_high' | 'ref_text'>): string | null {
  if (r.ref_text) return r.ref_text
  if (r.ref_low !== null && r.ref_high !== null) return `${r.ref_low}–${r.ref_high}`
  if (r.ref_high !== null) return `up to ${r.ref_high}`
  if (r.ref_low !== null) return `${r.ref_low} or more`
  return null
}

export type MarkerGroup = {
  key: string
  name: string
  results: LabResult[] // oldest first, as the API returns them
}

export type CategoryGroup = {
  category: MarkerCategory
  label: string
  markers: MarkerGroup[]
}

// Results grouped by category, then by marker, in catalog order. Only markers that have
// results appear. A result with no matched marker (possible from M4 reports) goes under
// "Other" with the name printed on the report.
export function groupResults(markers: LabMarker[], results: LabResult[]): CategoryGroup[] {
  const byKey = new Map<string, MarkerGroup>()
  const categoryOf = new Map<string, MarkerCategory>()

  for (const m of markers) {
    byKey.set(m.key, { key: m.key, name: m.display_name, results: [] })
    categoryOf.set(m.key, m.category)
  }
  for (const r of results) {
    const key = r.marker_key ?? `raw:${r.raw_marker.toLowerCase()}`
    if (!byKey.has(key)) {
      byKey.set(key, { key, name: r.raw_marker, results: [] })
      categoryOf.set(key, 'other')
    }
    byKey.get(key)!.results.push(r)
  }

  return CATEGORY_ORDER.map((category) => ({
    category,
    label: CATEGORY_LABEL[category],
    markers: [...byKey.values()].filter(
      (g) => g.results.length > 0 && categoryOf.get(g.key) === category,
    ),
  })).filter((c) => c.markers.length > 0)
}

// Units are never converted or mixed: each unit becomes its own series.
export function splitByUnit(results: LabResult[]): { unit: string; results: LabResult[] }[] {
  const byUnit = new Map<string, LabResult[]>()
  for (const r of results) {
    const list = byUnit.get(r.unit) ?? []
    list.push(r)
    byUnit.set(r.unit, list)
  }
  return [...byUnit].map(([unit, list]) => ({ unit, results: list }))
}

// A round step for about four gaps: 1, 2, 2.5 or 5 times a power of ten.
function niceStep(raw: number): number {
  const power = 10 ** Math.floor(Math.log10(raw))
  const f = raw / power
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * power
}

// Y-axis bounds and round tick values that fit every value and the band, with some room
// around them. Lab values are never negative, so the bottom stops at 0. When the range
// has no low end ("up to 34"), the axis starts at 0 so the whole band shows.
export function yScale(
  results: LabResult[],
  band: LabResult | null,
): { domain: [number, number]; ticks: number[] } {
  const numbers = results.map((r) => r.value)
  if (band?.ref_low != null) numbers.push(band.ref_low)
  if (band?.ref_high != null) numbers.push(band.ref_high)
  if (band && band.ref_low === null) numbers.push(0)
  const lo = Math.min(...numbers)
  const hi = Math.max(...numbers)
  const span = hi - lo || Math.abs(hi) || 1
  const step = niceStep((span * 1.3) / 4)
  const decimals = Math.max(0, -Math.floor(Math.log10(step)) + 1)
  const round = (v: number) => Number(v.toFixed(decimals))
  const bottom = Math.max(0, Math.floor((lo - span * 0.1) / step) * step)
  const top = Math.ceil((hi + span * 0.1) / step) * step
  const ticks: number[] = []
  for (let v = bottom; v <= top + step / 2; v += step) ticks.push(round(v))
  return { domain: [ticks[0], ticks[ticks.length - 1]], ticks }
}

// Did the reports use different ranges for this marker? Each point is still flagged
// against its own report's range, so the page says so when they differ.
export function rangesDiffer(results: LabResult[]): boolean {
  const seen = new Set(results.map((r) => `${r.ref_low}|${r.ref_high}`))
  return seen.size > 1
}
