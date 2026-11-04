import { useEffect, useState } from 'react'

import { getHealth } from '../api'
import type { Health } from '../types'
import styles from './HealthStatus.module.css'

type HealthState =
  | { kind: 'loading' }
  | { kind: 'loaded'; health: Health }
  | { kind: 'unreachable' }

export default function HealthStatus() {
  const [state, setState] = useState<HealthState>({ kind: 'loading' })

  useEffect(() => {
    // Ignore a response that arrives after the component is gone.
    let active = true
    getHealth()
      .then((health) => active && setState({ kind: 'loaded', health }))
      .catch(() => active && setState({ kind: 'unreachable' }))
    return () => {
      active = false
    }
  }, [])

  return (
    <section className={styles.card} aria-live="polite">
      <h2 className={styles.cardTitle}>System status</h2>
      <StatusRow label="API" status={apiStatus(state)} />
      <StatusRow label="Database" status={dbStatus(state)} />
    </section>
  )
}

type Status = 'checking' | 'ok' | 'error'

function apiStatus(state: HealthState): Status {
  if (state.kind === 'loading') return 'checking'
  return state.kind === 'loaded' ? 'ok' : 'error'
}

function dbStatus(state: HealthState): Status {
  if (state.kind === 'loading') return 'checking'
  return state.kind === 'loaded' && state.health.db === 'ok' ? 'ok' : 'error'
}

const STATUS_TEXT: Record<Status, string> = {
  checking: 'Checking…',
  ok: 'OK',
  error: 'Unreachable',
}

function StatusRow({ label, status }: { label: string; status: Status }) {
  return (
    <div className={styles.row}>
      <span>{label}</span>
      <span className={styles.status} data-status={status}>
        <span className={styles.dot} aria-hidden="true" />
        {STATUS_TEXT[status]}
      </span>
    </div>
  )
}
