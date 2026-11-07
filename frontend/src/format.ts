import type { Med } from './types'

// "75 mcg", "2 g", or "" when no dose was given.
export function doseLabel(med: Pick<Med, 'dose' | 'dose_unit'>): string {
  if (med.dose === null) return ''
  return [med.dose, med.dose_unit].filter(Boolean).join(' ')
}
