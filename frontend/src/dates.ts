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

export function shortDate(iso: string): string {
  return fromIso(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

// Whole days from one ISO date to another (b - a).
export function daysBetween(a: string, b: string): number {
  return Math.round((fromIso(b).getTime() - fromIso(a).getTime()) / 86_400_000)
}

// "Dec 3", or "Dec 3, 2025" when the year isn't this one.
export function mediumDate(iso: string): string {
  const d = fromIso(iso)
  const sameYear = d.getFullYear() === new Date().getFullYear()
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
  })
}

// Current local time as 'HH:MM'.
export function nowTime(): string {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
