// Every request to the backend goes through this file.

import type { Health } from './types'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
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
