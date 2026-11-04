// Shapes returned by the API. Kept in sync with backend/app/schemas.py by hand.
// Dates are ISO strings: 'YYYY-MM-DD'.

export type Health = {
  status: 'ok' | 'error'
  db: 'ok' | 'error'
}

export type Condition = 'pcos' | 'thyroid'

export type Me = {
  id: string
  email: string | null
  conditions: Condition[]
  track_cycles: boolean
  track_weight: boolean
  ai_consent_at: string | null
  created_at: string
}

export type MePatch = Partial<{
  conditions: Condition[]
  track_cycles: boolean
  track_weight: boolean
  ai_consent: boolean
}>

export type TrackedSymptom = {
  id: string
  symptom: string
  position: number
  active: boolean
}

export type Severity = 1 | 2 | 3

export type LogSymptom = {
  symptom: string
  severity: Severity
}

export type Log = {
  date: string
  energy: number | null
  mood: number | null
  sleep_hours: number | null
  weight: number | null
  notes: string | null
  symptoms: LogSymptom[]
  updated_at: string
}

// PUT replaces the whole day, so every field is sent every time.
export type LogInput = {
  energy: number | null
  mood: number | null
  sleep_hours: number | null
  weight: number | null
  notes: string | null
  symptoms: LogSymptom[]
}
