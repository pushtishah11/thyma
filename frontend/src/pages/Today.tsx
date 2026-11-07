import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { addTrackedSymptom, getLogs, getTrackedSymptoms, putLog } from '../api'
import Icon from '../components/Icon'
import MedChecklist from '../components/MedChecklist'
import RatingPicker from '../components/RatingPicker'
import SleepStepper from '../components/SleepStepper'
import SymptomChip from '../components/SymptomChip'
import { addDays, formatLong, todayIso } from '../dates'
import ui from '../styles/ui.module.css'
import type { Log, LogInput, Severity } from '../types'
import styles from './Today.module.css'

const ENERGY_WORDS: [string, string, string, string, string] = [
  'Drained',
  'Low',
  'Okay',
  'Good',
  'Energized',
]
const MOOD_WORDS: [string, string, string, string, string] = [
  'Very low',
  'Low',
  'Okay',
  'Good',
  'Great',
]

// What's on screen.
type Draft = {
  energy: number | null
  mood: number | null
  sleep: number | null
  notes: string
  symptoms: Record<string, Severity>
}

type Loaded = {
  date: string
  chips: string[]
  saved: Draft
  hasLog: boolean
  // Not shown on this page, but PUT replaces the whole day, so we send it back
  // unchanged instead of wiping a weight logged elsewhere.
  weight: number | null
}

type SaveState =
  | { kind: 'idle' }
  | { kind: 'saving' }
  | { kind: 'saved' }
  | { kind: 'error'; message: string }

const EMPTY: Draft = { energy: null, mood: null, sleep: null, notes: '', symptoms: {} }

function draftFromLog(log: Log | undefined): Draft {
  if (!log) return EMPTY
  return {
    energy: log.energy,
    mood: log.mood,
    sleep: log.sleep_hours,
    notes: log.notes ?? '',
    symptoms: Object.fromEntries(log.symptoms.map((s) => [s.symptom, s.severity])),
  }
}

function toInput(draft: Draft, weight: number | null): LogInput {
  const notes = draft.notes.trim()
  return {
    energy: draft.energy,
    mood: draft.mood,
    sleep_hours: draft.sleep,
    weight,
    notes: notes === '' ? null : notes,
    symptoms: Object.entries(draft.symptoms).map(([symptom, severity]) => ({ symptom, severity })),
  }
}

const sameDraft = (a: Draft, b: Draft) => JSON.stringify(a) === JSON.stringify(b)

function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

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
        setLoaded({ date, chips, saved, hasLog: logs.length > 0, weight: logs[0]?.weight ?? null })
        setDraft(saved)
        setLoadError(null)
      })
      .catch((e: Error) => active && setLoadError({ date, message: e.message }))
    return () => {
      active = false
    }
  }, [date, retry])

  // "Saved" shows briefly, then the save bar tucks itself away.
  useEffect(() => {
    if (save.kind !== 'saved') return
    const timer = setTimeout(() => setSave({ kind: 'idle' }), 2000)
    return () => clearTimeout(timer)
  }, [save])

  const ready = loaded !== null && loaded.date === date
  const dirty = ready && !sameDraft(draft, loaded.saved)
  const isToday = date === today

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

  function symptomAdded(name: string) {
    if (!loaded) return
    if (!loaded.chips.includes(name)) setLoaded({ ...loaded, chips: [...loaded.chips, name] })
    // You added it because you have it today, so start it at mild.
    edit({ symptoms: { ...draft.symptoms, [name]: draft.symptoms[name] ?? 1 } })
  }

  async function onSave() {
    if (!loaded) return
    setSave({ kind: 'saving' })
    try {
      const log = await putLog(date, toInput(draft, loaded.weight))
      const saved = draftFromLog(log)
      setLoaded({ ...loaded, saved, hasLog: true })
      setDraft(saved)
      setSave({ kind: 'saved' })
    } catch (e) {
      setSave({ kind: 'error', message: (e as Error).message })
    }
  }

  const loggedCount = Object.keys(draft.symptoms).length

  return (
    <>
      <div className={styles.top}>
        <div>
          <h1 className={ui.pageTitle}>{isToday ? greeting() : formatLong(date)}</h1>
          <p className={ui.pageSub}>
            {isToday ? `${formatLong(date)} · How's today going?` : 'Looking back at a past day'}
          </p>
        </div>
        <div className={styles.dateNav}>
          <button
            type="button"
            className={styles.arrow}
            onClick={() => goTo(addDays(date, -1))}
            aria-label="Previous day"
          >
            <Icon name="left" />
          </button>
          {!isToday && (
            <button type="button" className={styles.todayButton} onClick={() => goTo(today)}>
              Today
            </button>
          )}
          <button
            type="button"
            className={styles.arrow}
            onClick={() => goTo(addDays(date, 1))}
            disabled={isToday}
            aria-label="Next day"
          >
            <Icon name="right" />
          </button>
        </div>
      </div>

      {loadError?.date === date && (
        <div className={ui.card} role="alert">
          <p className={ui.error}>{loadError.message}</p>
          <button type="button" className={ui.secondary} onClick={() => setRetry((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}

      {!ready && loadError?.date !== date && <p className={ui.hint}>Loading…</p>}

      {ready && (
        <form
          className={styles.form}
          onSubmit={(e) => {
            e.preventDefault()
            onSave()
          }}
        >
          <section className={ui.card}>
            <div className={ui.cardHead}>
              <h2 className={ui.cardTitle}>
                <Icon name="pulse" /> How you're feeling
              </h2>
              {loaded.hasLog && (
                <span className={styles.badge}>
                  <Icon name="check" size={14} /> Logged
                </span>
              )}
            </div>
            <RatingPicker
              label="Energy"
              words={ENERGY_WORDS}
              value={draft.energy}
              onChange={(energy) => edit({ energy })}
            />
            <RatingPicker
              label="Mood"
              words={MOOD_WORDS}
              value={draft.mood}
              onChange={(mood) => edit({ mood })}
            />
          </section>

          <section className={ui.card}>
            <div className={ui.cardHead}>
              <h2 className={ui.cardTitle}>
                <Icon name="spark" /> Symptoms
                {loggedCount > 0 && <span className={styles.count}>{loggedCount}</span>}
              </h2>
              <span className={styles.legend} aria-hidden="true">
                Tap to cycle
                <span className={styles.swatch} data-severity="1" /> mild
                <span className={styles.swatch} data-severity="2" /> moderate
                <span className={styles.swatch} data-severity="3" /> severe
              </span>
            </div>
            {loaded.chips.length === 0 && (
              <p className={ui.hint}>
                No symptoms yet. <Link to="/settings">Pick your conditions</Link> for a starting
                list, or add your own below.
              </p>
            )}
            <div className={styles.chips}>
              {loaded.chips.map((name) => (
                <SymptomChip
                  key={name}
                  name={name}
                  severity={draft.symptoms[name] ?? null}
                  onTap={() => cycleSymptom(name)}
                />
              ))}
              <AddSymptom onAdded={symptomAdded} existing={loaded.chips} />
            </div>
          </section>

          <section className={ui.card}>
            <div className={ui.cardHead}>
              <h2 className={ui.cardTitle}>
                <Icon name="pill" /> Meds &amp; supplements
              </h2>
              <span className={ui.hint}>Saves as you tap</span>
            </div>
            <MedChecklist date={date} />
          </section>

          <section className={ui.card}>
            <div className={ui.cardHead}>
              <h2 className={ui.cardTitle}>
                <Icon name="moon" /> Sleep last night
              </h2>
            </div>
            <SleepStepper value={draft.sleep} onChange={(sleep) => edit({ sleep })} />
          </section>

          <section className={ui.card}>
            <label className={styles.field}>
              <span className={ui.cardTitle}>
                <Icon name="note" /> Notes
              </span>
              <textarea
                className={styles.notes}
                rows={3}
                maxLength={2000}
                placeholder="Anything worth remembering about today?"
                value={draft.notes}
                onChange={(e) => edit({ notes: e.target.value })}
              />
            </label>
          </section>

          {(dirty || save.kind !== 'idle') && (
            <div className={styles.saveBar} data-dirty={dirty}>
              <span
                aria-live="polite"
                className={save.kind === 'error' ? styles.saveError : styles.saveStatus}
              >
                {save.kind === 'saved' && (
                  <>
                    <Icon name="check" size={16} /> Saved
                  </>
                )}
                {save.kind === 'error' && save.message}
                {save.kind === 'saving' && 'Saving…'}
                {save.kind === 'idle' && 'Unsaved changes'}
              </span>
              <button
                type="submit"
                className={ui.primary}
                disabled={!dirty || save.kind === 'saving'}
              >
                Save
              </button>
            </div>
          )}
        </form>
      )}
    </>
  )
}

function AddSymptom({
  onAdded,
  existing,
}: {
  onAdded: (name: string) => void
  existing: string[]
}) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  function close() {
    setOpen(false)
    setName('')
    setError(null)
  }

  async function add() {
    const clean = name.trim().toLowerCase().split(/\s+/).join(' ')
    if (!clean) return
    if (existing.includes(clean)) {
      // Already a chip: just log it instead of erroring.
      onAdded(clean)
      return close()
    }
    setBusy(true)
    try {
      const chip = await addTrackedSymptom(clean)
      onAdded(chip.symptom)
      close()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <button type="button" className={styles.addChip} onClick={() => setOpen(true)}>
        <Icon name="plus" size={16} /> Add
      </button>
    )
  }

  return (
    <div className={styles.addRow}>
      <input
        className={styles.addInput}
        autoFocus
        maxLength={40}
        placeholder="e.g. joint pain"
        aria-label="New symptom"
        value={name}
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => {
          // Enter adds the chip instead of submitting the whole day's log.
          if (e.key === 'Enter') {
            e.preventDefault()
            add()
          }
          if (e.key === 'Escape') close()
        }}
      />
      <button type="button" className={ui.secondary} onClick={add} disabled={busy || !name.trim()}>
        Add
      </button>
      <button type="button" className={styles.iconButton} onClick={close} aria-label="Cancel">
        <Icon name="close" size={16} />
      </button>
      {error && <p className={ui.error}>{error}</p>}
    </div>
  )
}
