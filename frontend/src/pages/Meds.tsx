import { useEffect, useState } from 'react'

import { addMed, changeDose, deleteMed, getAdherence, getMeds, patchMed } from '../api'
import Icon from '../components/Icon'
import { addDays, mediumDate, todayIso } from '../dates'
import { doseLabel } from '../format'
import ui from '../styles/ui.module.css'
import type { Adherence, Med, MedInput, MedKind } from '../types'
import styles from './Meds.module.css'

const ADHERENCE_DAYS = 30

export default function Meds() {
  const today = todayIso()
  const [meds, setMeds] = useState<Med[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let active = true
    getMeds()
      .then((m) => {
        if (!active) return
        setMeds(m)
        setError(null)
      })
      .catch((e: Error) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [reload])

  const refresh = () => setReload((n) => n + 1)
  const current = meds?.filter((m) => m.end_date === null || m.end_date >= today) ?? []
  const past = meds?.filter((m) => m.end_date !== null && m.end_date < today) ?? []

  return (
    <>
      <div>
        <h1 className={ui.pageTitle}>Meds &amp; supplements</h1>
        <p className={ui.pageSub}>What you take, at what dose, and since when</p>
      </div>

      {error && (
        <div className={ui.card} role="alert">
          <p className={ui.error}>{error}</p>
          <button type="button" className={ui.secondary} onClick={refresh}>
            Try again
          </button>
        </div>
      )}

      {!meds && !error && <p className={ui.hint}>Loading…</p>}

      {meds && (
        <>
          <AddMed today={today} startOpen={meds.length === 0} onAdded={refresh} />

          {current.length > 0 && (
            <section className={styles.group}>
              <h2 className={styles.groupTitle}>Current</h2>
              {current.map((m) => (
                <MedCard key={m.id} med={m} today={today} onChange={refresh} />
              ))}
            </section>
          )}

          {past.length > 0 && (
            <section className={ui.card}>
              <div className={ui.cardHead}>
                <h2 className={ui.cardTitle}>Past</h2>
                <span className={ui.hint}>Stopped, or an earlier dose</span>
              </div>
              <ul className={styles.pastList}>
                {past.map((m) => (
                  <li key={m.id} className={styles.pastRow}>
                    <span className={styles.pastName}>
                      {m.name} {doseLabel(m) && <span className={styles.dose}>{doseLabel(m)}</span>}
                    </span>
                    <span className={ui.hint}>
                      {mediumDate(m.start_date)} – {mediumDate(m.end_date!)}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </>
  )
}

function AddMed({
  today,
  startOpen,
  onAdded,
}: {
  today: string
  startOpen: boolean
  onAdded: () => void
}) {
  const [open, setOpen] = useState(startOpen)
  const [formKey, setFormKey] = useState(0)

  if (!open) {
    return (
      <button type="button" className={`${ui.secondary} ${styles.addButton}`} onClick={() => setOpen(true)}>
        <Icon name="plus" size={16} /> Add a med or supplement
      </button>
    )
  }

  return (
    <section className={ui.card}>
      <div className={ui.cardHead}>
        <h2 className={ui.cardTitle}>
          <Icon name="pill" /> Add a med or supplement
        </h2>
      </div>
      <MedForm
        key={formKey}
        today={today}
        onCancel={startOpen ? undefined : () => setOpen(false)}
        onSubmit={async (med) => {
          await addMed(med)
          setFormKey((k) => k + 1)
          setOpen(false)
          onAdded()
        }}
      />
    </section>
  )
}

function MedForm({
  today,
  onSubmit,
  onCancel,
}: {
  today: string
  onSubmit: (med: MedInput) => Promise<void>
  onCancel?: () => void
}) {
  const [name, setName] = useState('')
  const [kind, setKind] = useState<MedKind>('supplement')
  const [dose, setDose] = useState('')
  const [unit, setUnit] = useState('')
  const [frequency, setFrequency] = useState('')
  const [start, setStart] = useState(today)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await onSubmit({
        name: name.trim(),
        kind,
        dose: dose === '' ? null : Number(dose),
        dose_unit: dose === '' ? null : unit.trim() || null,
        frequency: frequency.trim() || null,
        start_date: start,
      })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <div className={styles.kind} role="radiogroup" aria-label="Type">
        {(['supplement', 'medication'] as const).map((k) => (
          <button
            key={k}
            type="button"
            role="radio"
            aria-checked={kind === k}
            className={styles.kindOption}
            onClick={() => setKind(k)}
          >
            {k === 'supplement' ? 'Supplement' : 'Medication'}
          </button>
        ))}
      </div>
      <label className={styles.field}>
        <span>Name</span>
        <input
          required
          maxLength={80}
          placeholder={kind === 'supplement' ? 'e.g. Inositol' : 'e.g. Levothyroxine'}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <div className={styles.row3}>
        <label className={styles.field}>
          <span>
            Dose <em>(optional)</em>
          </span>
          <input
            type="number"
            inputMode="decimal"
            min="0"
            step="any"
            placeholder="2"
            value={dose}
            onChange={(e) => setDose(e.target.value)}
          />
        </label>
        <label className={styles.field}>
          <span>Unit</span>
          <input
            maxLength={20}
            placeholder="g, mg, mcg, IU"
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            disabled={dose === ''}
          />
        </label>
        <label className={styles.field}>
          <span>
            How often <em>(optional)</em>
          </span>
          <input
            maxLength={80}
            placeholder="daily"
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
          />
        </label>
      </div>
      <label className={styles.field}>
        <span>Started on</span>
        <input type="date" required value={start} onChange={(e) => setStart(e.target.value)} />
      </label>
      {error && <p className={ui.error}>{error}</p>}
      <div className={styles.actions}>
        {onCancel && (
          <button type="button" className={ui.secondary} onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" className={ui.primary} disabled={busy || !name.trim()}>
          Add
        </button>
      </div>
    </form>
  )
}

function MedCard({ med, today, onChange }: { med: Med; today: string; onChange: () => void }) {
  const [adherence, setAdherence] = useState<Adherence | null>(null)
  const [mode, setMode] = useState<'view' | 'dose'>('view')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const start = addDays(today, -(ADHERENCE_DAYS - 1))
    getAdherence(med.id, start, today)
      .then((a) => active && setAdherence(a))
      .catch(() => active && setAdherence(null))
    return () => {
      active = false
    }
  }, [med.id, today])

  async function run(action: () => Promise<unknown>) {
    setError(null)
    try {
      await action()
      onChange()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  function stop() {
    if (!window.confirm(`Mark ${med.name} as stopped today? Its history is kept.`)) return
    run(() => patchMed(med.id, { end_date: today }))
  }

  function remove() {
    const msg = `Delete ${med.name} and every dose you've ticked for it? Use "Stop" instead if you just stopped taking it.`
    if (!window.confirm(msg)) return
    run(() => deleteMed(med.id))
  }

  return (
    <article className={ui.card}>
      <div className={styles.cardTop}>
        <div className={styles.titleBlock}>
          <h3 className={styles.name}>
            {med.name} {doseLabel(med) && <span className={styles.dose}>{doseLabel(med)}</span>}
          </h3>
          <span className={ui.hint}>
            <span className={styles.kindTag}>{med.kind}</span>
            {med.frequency && ` ${med.frequency} ·`} since {mediumDate(med.start_date)}
          </span>
        </div>
        <AdherenceRing adherence={adherence} />
      </div>

      {mode === 'dose' ? (
        <DoseChange
          med={med}
          today={today}
          onCancel={() => setMode('view')}
          onDone={() => {
            setMode('view')
            onChange()
          }}
        />
      ) : (
        <div className={styles.cardActions}>
          {med.dose !== null && (
            <button type="button" className={ui.secondary} onClick={() => setMode('dose')}>
              <Icon name="edit" size={15} /> Change dose
            </button>
          )}
          <button type="button" className={ui.secondary} onClick={stop}>
            <Icon name="stop" size={14} /> Stop
          </button>
          <button
            type="button"
            className={styles.iconButton}
            onClick={remove}
            aria-label={`Delete ${med.name}`}
          >
            <Icon name="trash" size={17} />
          </button>
        </div>
      )}
      {error && <p className={ui.error}>{error}</p>}
    </article>
  )
}

function AdherenceRing({ adherence }: { adherence: Adherence | null }) {
  if (!adherence || adherence.percent_taken === null) return null
  const pct = adherence.percent_taken
  return (
    <div
      className={styles.ring}
      style={{ '--pct': `${pct}%` } as React.CSSProperties}
      title={`Taken on ${adherence.taken_days} of ${adherence.active_days} days in the last ${ADHERENCE_DAYS} days. ${adherence.unmarked_days} not marked.`}
    >
      <span className={styles.ringValue}>{pct}%</span>
      <span className={styles.ringLabel}>
        {adherence.taken_days}/{adherence.active_days} days
      </span>
    </div>
  )
}

function DoseChange({
  med,
  today,
  onCancel,
  onDone,
}: {
  med: Med
  today: string
  onCancel: () => void
  onDone: () => void
}) {
  const [dose, setDose] = useState('')
  const [unit, setUnit] = useState(med.dose_unit ?? '')
  const [from, setFrom] = useState(today)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await changeDose(med.id, {
        dose: Number(dose),
        dose_unit: unit.trim() || null,
        effective_date: from,
      })
      onDone()
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <p className={ui.hint}>
        The current {doseLabel(med)} is kept in your history and ends the day before the new dose
        starts.
      </p>
      <div className={styles.row3}>
        <label className={styles.field}>
          <span>New dose</span>
          <input
            type="number"
            inputMode="decimal"
            min="0"
            step="any"
            required
            autoFocus
            value={dose}
            onChange={(e) => setDose(e.target.value)}
          />
        </label>
        <label className={styles.field}>
          <span>Unit</span>
          <input maxLength={20} value={unit} onChange={(e) => setUnit(e.target.value)} />
        </label>
        <label className={styles.field}>
          <span>Starting</span>
          <input
            type="date"
            required
            min={addDays(med.start_date, 1)}
            value={from}
            onChange={(e) => setFrom(e.target.value)}
          />
        </label>
      </div>
      {error && <p className={ui.error}>{error}</p>}
      <div className={styles.actions}>
        <button type="button" className={ui.secondary} onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className={ui.primary} disabled={busy || !dose}>
          Save new dose
        </button>
      </div>
    </form>
  )
}
