import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { getLogs, getTrackedSymptoms, putLog } from '../api'
import RatingPicker from '../components/RatingPicker'
import SymptomChip from '../components/SymptomChip'
import { addDays, formatLong, todayIso } from '../dates'
import type { Log, LogInput, Severity } from '../types'
import styles from './Today.module.css'

// What's on screen. Sleep is kept as the raw input text so typing "7." works.
type Draft = {
  energy: number | null
  mood: number | null
  sleep: string
  notes: string
  symptoms: Record<string, Severity>
}

type Loaded = {
  date: string
  chips: string[]
  saved: Draft
  // Not shown on this page, but PUT replaces the whole day, so we send it back
  // unchanged instead of wiping a weight logged elsewhere.
  weight: number | null
}

type SaveState =
  | { kind: 'idle' }
  | { kind: 'saving' }
  | { kind: 'saved' }
  | { kind: 'error'; message: string }

const EMPTY: Draft = { energy: null, mood: null, sleep: '', notes: '', symptoms: {} }

function draftFromLog(log: Log | undefined): Draft {
  if (!log) return EMPTY
  return {
    energy: log.energy,
    mood: log.mood,
    sleep: log.sleep_hours === null ? '' : String(log.sleep_hours),
    notes: log.notes ?? '',
    symptoms: Object.fromEntries(log.symptoms.map((s) => [s.symptom, s.severity])),
  }
}

function toInput(draft: Draft, weight: number | null): LogInput {
  const notes = draft.notes.trim()
  return {
    energy: draft.energy,
    mood: draft.mood,
    sleep_hours: draft.sleep.trim() === '' ? null : Number(draft.sleep),
    weight,
    notes: notes === '' ? null : notes,
    symptoms: Object.entries(draft.symptoms).map(([symptom, severity]) => ({ symptom, severity })),
  }
}

const sameDraft = (a: Draft, b: Draft) => JSON.stringify(a) === JSON.stringify(b)

export default function Today() {
  const today = todayIso()
  const [date, setDate] = useState(today)
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [draft, setDraft] = useState<Draft>(EMPTY)
  const [loadError, setLoadError] = useState<{ date: string; message: string } | null>(null)
  const [save, setSave] = useState<SaveState>({ kind: 'idle' })
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let active = true
    Promise.all([getTrackedSymptoms(), getLogs(date, date)])
      .then(([tracked, logs]) => {
        if (!active) return
        const saved = draftFromLog(logs[0])
        // Keep any symptom logged that day even if its chip was hidden since,
        // so saving doesn't silently drop it.
        const chips = tracked.map((t) => t.symptom)
        for (const name of Object.keys(saved.symptoms)) {
          if (!chips.includes(name)) chips.push(name)
        }
        setLoaded({ date, chips, saved, weight: logs[0]?.weight ?? null })
        setDraft(saved)
        setLoadError(null)
      })
      .catch((e: Error) => active && setLoadError({ date, message: e.message }))
    return () => {
      active = false
    }
  }, [date, retry])

  const ready = loaded !== null && loaded.date === date
  const dirty = ready && !sameDraft(draft, loaded.saved)

  function goTo(next: string) {
    if (next > today) return
    if (dirty && !window.confirm('You have unsaved changes for this day. Leave without saving?')) {
      return
    }
    setSave({ kind: 'idle' })
    setDate(next)
  }

  function edit(change: Partial<Draft>) {
    setDraft((d) => ({ ...d, ...change }))
    setSave({ kind: 'idle' })
  }

  function cycleSymptom(name: string) {
    // Tapping cycles mild -> moderate -> severe -> off.
    const current = draft.symptoms[name]
    const symptoms = { ...draft.symptoms }
    if (current === 3) delete symptoms[name]
    else symptoms[name] = ((current ?? 0) + 1) as Severity
    edit({ symptoms })
  }

  async function onSave() {
    if (!loaded) return
    setSave({ kind: 'saving' })
    try {
      const log = await putLog(date, toInput(draft, loaded.weight))
      const saved = draftFromLog(log)
      setLoaded({ ...loaded, saved })
      setDraft(saved)
      setSave({ kind: 'saved' })
    } catch (e) {
      setSave({ kind: 'error', message: (e as Error).message })
    }
  }

  return (
    <>
      <div className={styles.dateBar}>
        <button
          type="button"
          className={styles.arrow}
          onClick={() => goTo(addDays(date, -1))}
          aria-label="Previous day"
        >
          ‹
        </button>
        <div className={styles.dateText}>
          <h1 className={styles.title}>{date === today ? 'Today' : formatLong(date)}</h1>
          {date === today && <span className={styles.subtle}>{formatLong(date)}</span>}
        </div>
        <button
          type="button"
          className={styles.arrow}
          onClick={() => goTo(addDays(date, 1))}
          disabled={date >= today}
          aria-label="Next day"
        >
          ›
        </button>
      </div>

      {loadError?.date === date && (
        <div className={styles.card} role="alert">
          <p className={styles.error}>{loadError.message}</p>
          <button type="button" className={styles.secondary} onClick={() => setRetry((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}

      {!ready && loadError?.date !== date && <p className={styles.subtle}>Loading…</p>}

      {ready && (
        <form
          className={styles.form}
          onSubmit={(e) => {
            e.preventDefault()
            onSave()
          }}
        >
          <section className={styles.card}>
            <RatingPicker
              label="Energy"
              low="Drained"
              high="Energized"
              value={draft.energy}
              onChange={(energy) => edit({ energy })}
            />
            <RatingPicker
              label="Mood"
              low="Low"
              high="Great"
              value={draft.mood}
              onChange={(mood) => edit({ mood })}
            />
          </section>

          <section className={styles.card}>
            <div className={styles.sectionHead}>
              <h2 className={styles.cardTitle}>Symptoms</h2>
              <span className={styles.subtle}>Tap: mild → moderate → severe → off</span>
            </div>
            {loaded.chips.length === 0 ? (
              <p className={styles.subtle}>
                No symptoms to track yet. <Link to="/settings">Pick your conditions in Settings</Link>{' '}
                to get a starting list.
              </p>
            ) : (
              <div className={styles.chips}>
                {loaded.chips.map((name) => (
                  <SymptomChip
                    key={name}
                    name={name}
                    severity={draft.symptoms[name] ?? null}
                    onTap={() => cycleSymptom(name)}
                  />
                ))}
              </div>
            )}
          </section>

          <section className={styles.card}>
            <label className={styles.field}>
              <span className={styles.cardTitle}>Sleep (hours)</span>
              <input
                className={styles.sleep}
                type="number"
                inputMode="decimal"
                min={0}
                max={24}
                step={0.5}
                value={draft.sleep}
                onChange={(e) => edit({ sleep: e.target.value })}
              />
            </label>
            <label className={styles.field}>
              <span className={styles.cardTitle}>Notes</span>
              <textarea
                className={styles.notes}
                rows={3}
                maxLength={2000}
                value={draft.notes}
                onChange={(e) => edit({ notes: e.target.value })}
              />
            </label>
          </section>

          <div className={styles.saveBar}>
            <button
              type="submit"
              className={styles.primary}
              disabled={!dirty || save.kind === 'saving'}
            >
              {save.kind === 'saving' ? 'Saving…' : 'Save'}
            </button>
            <span aria-live="polite" className={save.kind === 'error' ? styles.error : styles.subtle}>
              {save.kind === 'saved' && 'Saved'}
              {save.kind === 'error' && save.message}
              {save.kind === 'idle' && dirty && 'Unsaved changes'}
            </span>
          </div>
        </form>
      )}
    </>
  )
}
