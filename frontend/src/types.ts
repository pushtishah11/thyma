// Shapes returned by the API. Kept in sync with backend/app/schemas.py by hand.

export type Health = {
  status: 'ok' | 'error'
  db: 'ok' | 'error'
}
