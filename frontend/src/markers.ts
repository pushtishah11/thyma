import { addDays } from './dates'
import { doseLabel } from './format'
import type { Med } from './types'

export type Marker = { date: string; text: string }

// Start, stop and dose-change markers for the meds and supplements, inside start..end.
// A dose change is stored as "old row ends, new row starts the next day"; that pair is
// shown as one "dose changed" marker instead of a stop and a start.
export function medMarkers(meds: Med[], start: string, end: string): Marker[] {
  const inRange = (d: string) => start <= d && d <= end
  const markers: Marker[] = []
  const continued = new Set<string>() // ids of rows whose end is really a dose change

  for (const med of meds) {
    const previous = meds.find(
      (p) => p.name === med.name && p.end_date === addDays(med.start_date, -1),
    )
    if (previous) continued.add(previous.id)
    if (!inRange(med.start_date)) continue
    const dose = doseLabel(med)
    markers.push({
      date: med.start_date,
      text: previous
        ? `${med.name} changed to ${dose || 'a new dose'}`
        : `${med.name}${dose ? ` ${dose}` : ''} started`,
    })
  }
  for (const med of meds) {
    if (med.end_date && inRange(med.end_date) && !continued.has(med.id)) {
      markers.push({ date: med.end_date, text: `${med.name} stopped` })
    }
  }
  return markers.sort((a, b) => a.date.localeCompare(b.date))
}
