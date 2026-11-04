// Date helpers. The API speaks ISO 'YYYY-MM-DD'; "today" is the user's local day,
// not UTC, so a log made at 11pm lands on the right date.

export function toIso(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function todayIso(): string {
  return toIso(new Date())
}

// Parse as a local date. new Date('2026-01-15') would be UTC midnight,
// which is the previous day in timezones west of UTC.
export function fromIso(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function addDays(iso: string, days: number): string {
  const d = fromIso(iso)
  d.setDate(d.getDate() + days)
  return toIso(d)
}

export function formatLong(iso: string): string {
  return fromIso(iso).toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  })
}
