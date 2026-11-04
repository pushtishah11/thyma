import { useEffect, useState } from 'react'

import { getMe, patchMe } from '../api'
import HealthStatus from '../components/HealthStatus'
import type { Condition, Me } from '../types'
import styles from './Settings.module.css'

const CONDITIONS: { key: Condition; label: string }[] = [
  { key: 'pcos', label: 'PCOS' },
  { key: 'thyroid', label: "Thyroid (Hashimoto's, hypothyroidism)" },
]

export default function Settings() {
  const [me, setMe] = useState<Me | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    getMe()
      .then((m) => active && setMe(m))
      .catch((e: Error) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [])

  async function toggleCondition(key: Condition, on: boolean) {
    if (!me) return
    const conditions = on ? [...me.conditions, key] : me.conditions.filter((c) => c !== key)
    setSaving(true)
    setError(null)
    try {
      setMe(await patchMe({ conditions }))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <h1 className={styles.title}>Settings</h1>

      <section className={styles.card}>
        <h2 className={styles.cardTitle}>Your conditions</h2>
        <p className={styles.hint}>
          These pick the starting symptom chips on the Today page. Unticking one keeps the chips you
          already have, so your history stays intact.
        </p>
        {me === null && !error && <p className={styles.hint}>Loading…</p>}
        {me &&
          CONDITIONS.map(({ key, label }) => (
            <label key={key} className={styles.check}>
              <input
                type="checkbox"
                checked={me.conditions.includes(key)}
                disabled={saving}
                onChange={(e) => toggleCondition(key, e.target.checked)}
              />
              {label}
            </label>
          ))}
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
      </section>

      <HealthStatus />
    </>
  )
}
