// Every request to the backend goes through this file.

import type { Health, Log, LogInput, Me, MePatch, TrackedSymptom } from './types'

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
