// Every request to the backend goes through this file.

import type {
  Adherence,
  Cycle,
  CycleInput,
  CycleSummary,
  DayDose,
  FoodTag,
  Health,
  LabInput,
  LabMarker,
  LabResult,
  Log,
  LogInput,
  Meal,
  MealInput,
  Me,
  Med,
  MedInput,
  MePatch,
  TrackedSymptom,
  Trends,
} from './types'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// FastAPI errors look like {detail: "..."} for our own errors, or
// {detail: [{msg, loc, ...}]} when request validation fails.
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) return "Some values aren't valid. Check them and try again."
  } catch {
    // Not JSON (e.g. the proxy couldn't reach the API).
  }
  return res.status >= 500 ? "Couldn't reach Thyma's server." : res.statusText
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    })
  } catch {
    throw new ApiError(0, "Couldn't reach Thyma's server.")
  }
  if (!res.ok) throw new ApiError(res.status, await errorMessage(res))
  return (res.status === 204 ? undefined : await res.json()) as T
}

export async function getHealth(): Promise<Health> {
  const res = await fetch('/api/health')
  // A 503 still carries {status, db}: the API is up but the database isn't.
  // Anything else (like the proxy failing to reach FastAPI) is a real error.
  if (res.ok || res.status === 503) {
    return res.json()
  }
  throw new ApiError(res.status, res.statusText)
}

export const getMe = () => request<Me>('/me')

export const patchMe = (patch: MePatch) =>
  request<Me>('/me', { method: 'PATCH', body: JSON.stringify(patch) })

export const getTrackedSymptoms = () => request<TrackedSymptom[]>('/tracked-symptoms')

export const getLogs = (start: string, end: string) =>
  request<Log[]>(`/logs?${new URLSearchParams({ start, end })}`)

export const putLog = (date: string, log: LogInput) =>
  request<Log>(`/logs/${date}`, { method: 'PUT', body: JSON.stringify(log) })

export const getTrends = (start: string, end: string) =>
  request<Trends>(`/trends?${new URLSearchParams({ start, end })}`)

export const addTrackedSymptom = (symptom: string) =>
  request<TrackedSymptom>('/tracked-symptoms', {
    method: 'POST',
    body: JSON.stringify({ symptom }),
  })

export const getCycles = () => request<Cycle[]>('/cycles')

export const getCycleSummary = (gapThreshold: number, today: string) =>
  request<CycleSummary>(
    `/cycles/summary?${new URLSearchParams({ gap_threshold: String(gapThreshold), today })}`,
  )

export const addCycle = (cycle: CycleInput) =>
  request<Cycle>('/cycles', { method: 'POST', body: JSON.stringify(cycle) })

export const patchCycle = (id: string, changes: Partial<CycleInput>) =>
  request<Cycle>(`/cycles/${id}`, { method: 'PATCH', body: JSON.stringify(changes) })

export const deleteCycle = (id: string) => request<void>(`/cycles/${id}`, { method: 'DELETE' })

export const getMeds = () => request<Med[]>('/meds')

export const addMed = (med: MedInput) =>
  request<Med>('/meds', { method: 'POST', body: JSON.stringify(med) })

export const patchMed = (id: string, changes: Partial<MedInput>) =>
  request<Med>(`/meds/${id}`, { method: 'PATCH', body: JSON.stringify(changes) })

export const deleteMed = (id: string) => request<void>(`/meds/${id}`, { method: 'DELETE' })

export const changeDose = (
  id: string,
  change: { dose: number; dose_unit: string | null; effective_date: string },
) => request<Med>(`/meds/${id}/change-dose`, { method: 'POST', body: JSON.stringify(change) })

export const getAdherence = (id: string, start: string, end: string) =>
  request<Adherence>(`/meds/${id}/adherence?${new URLSearchParams({ start, end })}`)

export const getDoses = (date: string) =>
  request<DayDose[]>(`/doses?${new URLSearchParams({ date })}`)

export const putDose = (medId: string, date: string, taken: boolean, timeTaken: string | null) =>
  request<DayDose>(`/doses/${medId}/${date}`, {
    method: 'PUT',
    body: JSON.stringify({ taken, time_taken: timeTaken }),
  })

export const getMealsForDay = (date: string) =>
  request<Meal[]>(`/meals?${new URLSearchParams({ date })}`)

export const getMealsInRange = (start: string, end: string) =>
  request<Meal[]>(`/meals?${new URLSearchParams({ start, end })}`)

export const addMeal = (meal: MealInput) =>
  request<Meal>('/meals', { method: 'POST', body: JSON.stringify(meal) })

export const deleteMeal = (id: string) => request<void>(`/meals/${id}`, { method: 'DELETE' })

export const suggestTags = (description: string) =>
  request<{ tags: string[] }>('/meals/suggest-tags', {
    method: 'POST',
    body: JSON.stringify({ description }),
  })

export const getFoodTags = () => request<FoodTag[]>('/food-tags')

export const addFoodTag = (displayName: string) =>
  request<FoodTag>('/food-tags', {
    method: 'POST',
    body: JSON.stringify({ display_name: displayName }),
  })

export const getMarkers = () => request<LabMarker[]>('/markers')

export const getLabs = () => request<LabResult[]>('/labs')

export const addLab = (lab: LabInput) =>
  request<LabResult>('/labs', { method: 'POST', body: JSON.stringify(lab) })

export const patchLab = (id: string, changes: Partial<LabInput>) =>
  request<LabResult>(`/labs/${id}`, { method: 'PATCH', body: JSON.stringify(changes) })

export const deleteLab = (id: string) => request<void>(`/labs/${id}`, { method: 'DELETE' })
