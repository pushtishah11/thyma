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

export type DayPoint = {
  date: string
  logged: boolean
  energy: number | null
  mood: number | null
  sleep_hours: number | null
}

export type SymptomTrend = {
  symptom: string
  days: number
  percent_of_logged_days: number
  avg_severity: number
}

export type Trends = {
  start: string
  end: string
  days_in_range: number
  days_logged: number
  avg_energy: number | null
  avg_mood: number | null
  avg_sleep_hours: number | null
  daily: DayPoint[]
  symptoms: SymptomTrend[]
}

export type Cycle = {
  id: string
  start_date: string
  end_date: string | null
  notes: string | null
}

export type CycleInput = {
  start_date: string
  end_date: string | null
  notes: string | null
}

export type CycleStat = {
  start_date: string
  end_date: string | null
  length_days: number | null
  period_days: number | null
  long_gap: boolean
}

export type CycleSummary = {
  cycles: CycleStat[]
  completed_count: number
  mean_length: number | null
  min_length: number | null
  max_length: number | null
  last_start: string | null
  days_since_last_start: number | null
  gap_threshold: number
  current_gap_over_threshold: boolean
}

export type MedKind = 'medication' | 'supplement'

export type Med = {
  id: string
  name: string
  kind: MedKind
  dose: number | null
  dose_unit: string | null
  frequency: string | null
  start_date: string
  end_date: string | null
  notes: string | null
}

export type MedInput = {
  name: string
  kind: MedKind
  dose: number | null
  dose_unit: string | null
  frequency: string | null
  start_date: string
  end_date?: string | null
  notes?: string | null
}

// One active med on one day; taken is null until it's marked either way.
export type DayDose = {
  medication: Med
  taken: boolean | null
  time_taken: string | null
  notes: string | null
}

export type Adherence = {
  start: string
  end: string
  active_days: number
  taken_days: number
  not_taken_days: number
  unmarked_days: number
  percent_taken: number | null
}
