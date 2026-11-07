import { useEffect, useState } from 'react'

import { getMe, patchMe } from '../api'
import HealthStatus from '../components/HealthStatus'
import Icon from '../components/Icon'
import ui from '../styles/ui.module.css'
import type { Condition, Me } from '../types'
import styles from './Settings.module.css'

const CONDITIONS: { key: Condition; label: string; detail: string }[] = [
  {
    key: 'pcos',
    label: 'PCOS',
    detail: 'Adds acne, hair thinning, excess hair growth, cravings, bloating, fatigue',
  },
  {
    key: 'thyroid',
    label: 'Thyroid',
    detail: "Hashimoto's or hypothyroidism. Adds fatigue, cold intolerance, brain fog, and more",
  },
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

  async function toggleCondition(key: Condition) {
    if (!me) return
    const on = !me.conditions.includes(key)
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
      <div>
        <h1 className={ui.pageTitle}>Settings</h1>
        <p className={ui.pageSub}>Make Thyma fit what you're tracking</p>
      </div>

      <div className={ui.pair}>
        <section className={ui.card}>
          <div className={ui.cardHead}>
            <h2 className={ui.cardTitle}>Your conditions</h2>
          </div>
          <p className={`${ui.hint} ${styles.intro}`}>
            These pick your starting symptom chips. Turning one off keeps the chips you already have,
            so your history stays intact.
          </p>
          {me === null && !error && <p className={ui.hint}>Loading…</p>}
          {me && (
            <div className={styles.options}>
              {CONDITIONS.map(({ key, label, detail }) => {
                const on = me.conditions.includes(key)
                return (
                  <button
                    key={key}
                    type="button"
                    role="switch"
                    aria-checked={on}
                    className={styles.option}
                    disabled={saving}
                    onClick={() => toggleCondition(key)}
                  >
                    <span className={styles.check} aria-hidden="true">
                      {on && <Icon name="check" size={16} />}
                    </span>
                    <span className={styles.text}>
                      <span className={styles.optionLabel}>{label}</span>
                      <span className={styles.optionDetail}>{detail}</span>
                    </span>
                  </button>
                )
              })}
            </div>
          )}
          {error && (
            <p className={ui.error} role="alert">
              {error}
            </p>
          )}
        </section>

        <HealthStatus />
      </div>
    </>
  )
}
