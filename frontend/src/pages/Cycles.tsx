import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { addCycle, deleteCycle, getCycles, getCycleSummary, patchCycle } from '../api'
import { AXIS, TOOLTIP } from '../charts'
import Icon from '../components/Icon'
import { formatLong, shortDate, todayIso } from '../dates'
import ui from '../styles/ui.module.css'
import type { Cycle, CycleInput, CycleStat, CycleSummary } from '../types'
import styles from './Cycles.module.css'

const THRESHOLD_KEY = 'thyma.gapThreshold'
const DEFAULT_THRESHOLD = 35

// The threshold is a per-browser preference, so it lives in localStorage.
// Storage can be unavailable (private windows), so every access is guarded.
function loadThreshold(): number {
  try {
    const n = Number(localStorage.getItem(THRESHOLD_KEY))
    return Number.isInteger(n) && n >= 1 && n <= 365 ? n : DEFAULT_THRESHOLD
  } catch {
    return DEFAULT_THRESHOLD
  }
}

function saveThreshold(n: number) {
  try {
    localStorage.setItem(THRESHOLD_KEY, String(n))
  } catch {
    // Not saved; the page still works with the value in memory.
  }
}

type Data = { cycles: Cycle[]; summary: CycleSummary }

export default function Cycles() {
  const today = todayIso()
  const [threshold, setThreshold] = useState(loadThreshold)
  const [data, setData] = useState<Data | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let active = true
    Promise.all([getCycles(), getCycleSummary(threshold, today)])
      .then(([cycles, summary]) => {
        if (!active) return
        setData({ cycles, summary })
        setError(null)
      })
      .catch((e: Error) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [threshold, today, reload])

  const refresh = () => setReload((n) => n + 1)

  function changeThreshold(n: number) {
    const next = Math.min(365, Math.max(1, n))
    setThreshold(next)
    saveThreshold(next)
  }

  return (
    <>
      <div>
        <h1 className={ui.pageTitle}>Cycles</h1>
        <p className={ui.pageSub}>Your cycle history as logged. No predictions, no 28-day rule.</p>
      </div>

      {error && (
        <div className={ui.card} role="alert">
          <p className={ui.error}>{error}</p>
          <button type="button" className={ui.secondary} onClick={refresh}>
            Try again
          </button>
        </div>
      )}

      {!data && !error && <p className={ui.hint}>Loading…</p>}

      {data && (
        <>
          <div className={ui.pair}>
            <NowCard data={data} today={today} onChange={refresh} />
            <LogPeriod today={today} onAdded={refresh} />
          </div>
          {data.summary.completed_count > 0 && <Stats summary={data.summary} />}
          <div className={ui.pair}>
            {data.summary.completed_count > 0 && (
              <LengthsChart
                summary={data.summary}
                threshold={threshold}
                onThreshold={changeThreshold}
              />
            )}
            {data.cycles.length > 0 && <History data={data} today={today} onChange={refresh} />}
          </div>
        </>
      )}
    </>
  )
}

function NowCard({ data, today, onChange }: { data: Data; today: string; onChange: () => void }) {
  const { summary, cycles } = data
  const latest = cycles[0] // newest first
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(action: () => Promise<unknown>) {
    setBusy(true)
    setError(null)
    try {
      await action()
      onChange()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (summary.last_start === null || summary.days_since_last_start === null) {
    return (
      <section className={`${ui.card} ${ui.empty}`}>
        <Icon name="drop" size={32} />
        <p>No periods logged yet. Add your most recent one below, or tap the button if it's today.</p>
        <button
          type="button"
          className={ui.primary}
          disabled={busy}
          onClick={() => run(() => addCycle({ start_date: today, end_date: null, notes: null }))}
        >
          My period started today
        </button>
        {error && <p className={ui.error}>{error}</p>}
      </section>
    )
  }

  const days = summary.days_since_last_start
  // Offer "ended today" while the latest period has no end date and is recent enough
  // that it could plausibly still be going.
  const canEnd = latest && latest.end_date === null && days <= 14 && latest.start_date <= today
  const startedToday = summary.last_start === today

  return (
    <section className={`${ui.card} ${styles.now}`}>
      <div className={styles.nowMain}>
        <span className={styles.nowNumber}>{days}</span>
        <span className={styles.nowLabel}>
          {days === 1 ? 'day' : 'days'} since your last period started
          <span className={styles.nowDate}>{formatLong(summary.last_start)}</span>
        </span>
      </div>
      {summary.current_gap_over_threshold && (
        <p className={styles.note}>
          That's longer than your {summary.gap_threshold}-day marker. This is just what's logged,
          not a judgment.
        </p>
      )}
      <div className={styles.actions}>
        {canEnd && (
          <button
            type="button"
            className={ui.secondary}
            disabled={busy}
            onClick={() => run(() => patchCycle(latest.id, { end_date: today }))}
          >
            <Icon name="check" size={16} /> Period ended today
          </button>
        )}
        {!startedToday && (
          <button
            type="button"
            className={ui.primary}
            disabled={busy}
            onClick={() => run(() => addCycle({ start_date: today, end_date: null, notes: null }))}
          >
            <Icon name="drop" size={16} /> Period started today
          </button>
        )}
      </div>
      {error && <p className={ui.error}>{error}</p>}
    </section>
  )
}

function CycleForm({
  initial,
  today,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial: CycleInput
  today: string
  submitLabel: string
  onSubmit: (value: CycleInput) => Promise<void>
  onCancel?: () => void
}) {
  const [start, setStart] = useState(initial.start_date)
  const [end, setEnd] = useState(initial.end_date ?? '')
  const [notes, setNotes] = useState(initial.notes ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (end && end < start) {
      setError("The last day can't be before the first day.")
      return
    }
    setBusy(true)
    setError(null)
    try {
      await onSubmit({ start_date: start, end_date: end || null, notes: notes.trim() || null })
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <div className={styles.dates}>
        <label className={styles.field}>
          <span>First day</span>
          <input
            type="date"
            required
            max={today}
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </label>
        <label className={styles.field}>
          <span>
            Last day <em>(optional)</em>
          </span>
          <input
            type="date"
            min={start}
            max={today}
            value={end}
            onChange={(e) => setEnd(e.target.value)}
          />
        </label>
      </div>
      <label className={styles.field}>
        <span>
          Notes <em>(optional)</em>
        </span>
        <input
          type="text"
          maxLength={2000}
          placeholder="Anything you want to remember"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </label>
      {error && <p className={ui.error}>{error}</p>}
      <div className={styles.formActions}>
        {onCancel && (
          <button type="button" className={ui.secondary} onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" className={ui.primary} disabled={busy || !start}>
          {submitLabel}
        </button>
      </div>
    </form>
  )
}

function LogPeriod({ today, onAdded }: { today: string; onAdded: () => void }) {
  const [open, setOpen] = useState(false)
  const [formKey, setFormKey] = useState(0)

  return (
    <section className={ui.card}>
      <div className={ui.cardHead}>
        <h2 className={ui.cardTitle}>
          <Icon name="calendar" /> Log a past period
        </h2>
        {!open && (
          <button type="button" className={ui.linkButton} onClick={() => setOpen(true)}>
            Add
          </button>
        )}
      </div>
      {open ? (
        <CycleForm
          key={formKey}
          initial={{ start_date: today, end_date: null, notes: null }}
          today={today}
          submitLabel="Save period"
          onCancel={() => setOpen(false)}
          onSubmit={async (value) => {
            await addCycle(value)
            setFormKey((k) => k + 1) // reset the form for the next one
            onAdded()
          }}
        />
      ) : (
        <p className={ui.hint}>
          Add earlier periods to see how long your cycles have been. Even a few help.
        </p>
      )}
    </section>
  )
}

function Stats({ summary }: { summary: CycleSummary }) {
  const tiles = [
    { label: 'Average cycle', value: summary.mean_length?.toFixed(1) ?? '–', unit: 'days' },
    { label: 'Shortest', value: String(summary.min_length ?? '–'), unit: 'days' },
    { label: 'Longest', value: String(summary.max_length ?? '–'), unit: 'days' },
    { label: 'Cycles measured', value: String(summary.completed_count), unit: '' },
  ]
  return (
    <div className={styles.tiles}>
      {tiles.map((t) => (
        <div key={t.label} className={styles.tile}>
          <span className={styles.tileLabel}>{t.label}</span>
          <span className={styles.tileValue}>
            {t.value} <span className={styles.tileUnit}>{t.unit}</span>
          </span>
        </div>
      ))}
    </div>
  )
}

function LengthsChart({
  summary,
  threshold,
  onThreshold,
}: {
  summary: CycleSummary
  threshold: number
  onThreshold: (n: number) => void
}) {
  const rows = summary.cycles
    .filter((c): c is CycleStat & { length_days: number } => c.length_days !== null)
    .map((c) => ({ ...c, label: shortDate(c.start_date) }))
  const longCount = rows.filter((r) => r.long_gap).length

  return (
    <section className={ui.card}>
      <div className={ui.cardHead}>
        <h2 className={ui.cardTitle}>
          <Icon name="cycle" /> Cycle lengths
        </h2>
        <div className={styles.threshold}>
          <span>Mark longer than</span>
          <button
            type="button"
            className={styles.tStep}
            onClick={() => onThreshold(threshold - 1)}
            aria-label="Lower the marker by one day"
          >
            <Icon name="minus" size={14} />
          </button>
          <strong>{threshold}</strong>
          <button
            type="button"
            className={styles.tStep}
            onClick={() => onThreshold(threshold + 1)}
            aria-label="Raise the marker by one day"
          >
            <Icon name="plus" size={14} />
          </button>
          <span>days</span>
        </div>
      </div>
      <p className={ui.hint}>
        Each bar is one cycle, from the first day of a period to the first day of the next. The
        dashed line is your {threshold}-day marker.{' '}
        {longCount > 0
          ? `${longCount} of ${rows.length} ${longCount === 1 ? 'was' : 'were'} longer (darker bars).`
          : 'None were longer.'}
      </p>
      <ResponsiveContainer width="100%" height={230}>
        <BarChart data={rows} margin={{ top: 20, right: 8, bottom: 0, left: -24 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="label" {...AXIS} />
          <YAxis allowDecimals={false} {...AXIS} />
          <Tooltip
            {...TOOLTIP}
            cursor={{ fill: 'var(--accent-soft)' }}
            formatter={(v) => [`${v} days`, 'Cycle length']}
            labelFormatter={(label) => `Started ${label}`}
          />
          <ReferenceLine y={threshold} stroke="var(--muted)" strokeDasharray="4 4" />
          <Bar dataKey="length_days" radius={[4, 4, 0, 0]} maxBarSize={36} isAnimationActive={false}>
            {rows.map((r) => (
              <Cell key={r.start_date} fill={r.long_gap ? 'var(--accent)' : 'var(--sev-3)'} />
            ))}
            <LabelList dataKey="length_days" position="top" fill="var(--text)" fontSize={12} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  )
}

function History({ data, today, onChange }: { data: Data; today: string; onChange: () => void }) {
  const [editing, setEditing] = useState<string | null>(null)
  const stats = new Map(data.summary.cycles.map((s) => [s.start_date, s]))

  async function remove(cycle: Cycle) {
    if (!window.confirm(`Delete the period that started ${formatLong(cycle.start_date)}?`)) return
    try {
      await deleteCycle(cycle.id)
      onChange()
    } catch (e) {
      window.alert((e as Error).message)
    }
  }

  return (
    <section className={ui.card}>
      <div className={ui.cardHead}>
        <h2 className={ui.cardTitle}>
          <Icon name="drop" /> History
        </h2>
        <span className={ui.hint}>{data.cycles.length} logged</span>
      </div>
      <ul className={styles.list}>
        {data.cycles.map((cycle) => {
          const s = stats.get(cycle.start_date)
          if (editing === cycle.id) {
            return (
              <li key={cycle.id} className={styles.row}>
                <CycleForm
                  initial={cycle}
                  today={today}
                  submitLabel="Save changes"
                  onCancel={() => setEditing(null)}
                  onSubmit={async (value) => {
                    await patchCycle(cycle.id, value)
                    setEditing(null)
                    onChange()
                  }}
                />
              </li>
            )
          }
          return (
            <li key={cycle.id} className={styles.row}>
              <div className={styles.rowMain}>
                <span className={styles.rowDates}>
                  {shortDate(cycle.start_date)}
                  {cycle.end_date && ` – ${shortDate(cycle.end_date)}`}
                </span>
                <span className={styles.rowMeta}>
                  {s?.period_days ? `${s.period_days}-day period` : 'Last day not logged'}
                  {' · '}
                  {s?.length_days != null ? `${s.length_days}-day cycle` : 'Current cycle'}
                  {s?.long_gap && <span className={styles.tag}>longer than {data.summary.gap_threshold}</span>}
                </span>
                {cycle.notes && <span className={styles.rowNotes}>{cycle.notes}</span>}
              </div>
              <div className={styles.rowActions}>
                <button
                  type="button"
                  className={styles.iconButton}
                  onClick={() => setEditing(cycle.id)}
                  aria-label={`Edit the period that started ${formatLong(cycle.start_date)}`}
                >
                  <Icon name="edit" size={17} />
                </button>
                <button
                  type="button"
                  className={styles.iconButton}
                  onClick={() => remove(cycle)}
                  aria-label={`Delete the period that started ${formatLong(cycle.start_date)}`}
                >
                  <Icon name="trash" size={17} />
                </button>
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
