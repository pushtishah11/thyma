import { useEffect, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { addLab, deleteLab, getLabs, getMarkers, patchLab } from '../api'
import { AXIS, TOOLTIP } from '../charts'
import Icon from '../components/Icon'
import { fromIso, mediumDate, toIso, todayIso } from '../dates'
import {
  CATEGORY_LABEL,
  flagLabel,
  groupResults,
  rangeLabel,
  rangesDiffer,
  splitByUnit,
  yScale,
  type MarkerGroup,
} from '../labs'
import ui from '../styles/ui.module.css'
import type { LabFlag, LabInput, LabMarker, LabResult, MarkerCategory } from '../types'
import styles from './Labs.module.css'

type Data = { markers: LabMarker[]; results: LabResult[] }

export default function Labs() {
  const today = todayIso()
  const [data, setData] = useState<Data | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let active = true
    Promise.all([getMarkers(), getLabs()])
      .then(([markers, results]) => {
        if (!active) return
        setData({ markers, results })
        setError(null)
      })
      .catch((e: Error) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [reload])

  const refresh = () => setReload((n) => n + 1)
  const groups = data ? groupResults(data.markers, data.results) : []

  return (
    <>
      <div>
        <h1 className={ui.pageTitle}>Labs</h1>
        <p className={ui.pageSub}>
          Your results over time, each compared with the range printed on its own report
        </p>
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
          <AddResult data={data} today={today} onAdded={refresh} />

          {groups.length === 0 && (
            <section className={`${ui.card} ${ui.empty}`}>
              <Icon name="flask" size={32} />
              <p>
                No lab results yet. Add a value from one of your reports above. Uploading a
                whole report comes later.
              </p>
            </section>
          )}

          {groups.map((g) => (
            <section key={g.category} className={styles.group}>
              <h2 className={styles.groupTitle}>{g.label}</h2>
              {g.markers.map((m) => (
                <MarkerCard
                  key={m.key}
                  group={m}
                  markers={data.markers}
                  results={data.results}
                  today={today}
                  onChange={refresh}
                />
              ))}
            </section>
          ))}
        </>
      )}
    </>
  )
}

function AddResult({ data, today, onAdded }: { data: Data; today: string; onAdded: () => void }) {
  const startOpen = data.results.length === 0
  const [open, setOpen] = useState(startOpen)
  const [formKey, setFormKey] = useState(0)

  if (!open) {
    return (
      <button
        type="button"
        className={`${ui.secondary} ${styles.addButton}`}
        onClick={() => setOpen(true)}
      >
        <Icon name="plus" size={16} /> Add a lab result
      </button>
    )
  }

  return (
    <section className={ui.card}>
      <div className={ui.cardHead}>
        <h2 className={ui.cardTitle}>
          <Icon name="flask" /> Add a lab result
        </h2>
        <span className={ui.hint}>Copy it exactly as your report shows it</span>
      </div>
      <LabForm
        key={formKey}
        markers={data.markers}
        results={data.results}
        today={today}
        submitLabel="Add result"
        onCancel={startOpen ? undefined : () => setOpen(false)}
        onSubmit={async (lab) => {
          await addLab(lab)
          setFormKey((k) => k + 1) // a fresh form for the next value from the same report
          onAdded()
        }}
      />
    </section>
  )
}

type FormValues = {
  date: string
  marker_key: string
  value_text: string
  unit: string
  ref_low: string
  ref_high: string
}

const toForm = (r: LabResult): FormValues => ({
  date: r.date,
  marker_key: r.marker_key ?? '',
  value_text: r.value_text,
  unit: r.unit,
  ref_low: r.ref_low === null ? '' : String(r.ref_low),
  ref_high: r.ref_high === null ? '' : String(r.ref_high),
})

function toInput(v: FormValues): LabInput {
  return {
    date: v.date,
    marker_key: v.marker_key,
    value_text: v.value_text.trim(),
    unit: v.unit.trim(),
    ref_low: v.ref_low === '' ? null : Number(v.ref_low),
    ref_high: v.ref_high === '' ? null : Number(v.ref_high),
  }
}

function LabForm({
  initial,
  markers,
  results,
  today,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial?: LabResult
  markers: LabMarker[]
  results: LabResult[]
  today: string
  submitLabel: string
  onSubmit: (lab: LabInput, changed: Partial<LabInput>) => Promise<void>
  onCancel?: () => void
}) {
  const [values, setValues] = useState<FormValues>(
    initial
      ? toForm(initial)
      : { date: today, marker_key: '', value_text: '', unit: '', ref_low: '', ref_high: '' },
  )
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const set = (field: keyof FormValues, value: string) => setValues((v) => ({ ...v, [field]: value }))

  // Picking a marker fills in the unit and range from your latest result for it, if the
  // fields are still empty. Reports from the same lab usually repeat them.
  function pickMarker(key: string) {
    const latest = results.filter((r) => r.marker_key === key).at(-1)
    setValues((v) => ({
      ...v,
      marker_key: key,
      unit: v.unit || latest?.unit || '',
      ref_low: v.ref_low || v.ref_high ? v.ref_low : latest ? toForm(latest).ref_low : '',
      ref_high: v.ref_low || v.ref_high ? v.ref_high : latest ? toForm(latest).ref_high : '',
    }))
  }

  const unitsSeen = [
    ...new Set(results.filter((r) => r.marker_key === values.marker_key).map((r) => r.unit)),
  ]

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    const lab = toInput(values)
    if (lab.ref_low !== null && lab.ref_high !== null && lab.ref_low > lab.ref_high) {
      setError("The low end of the range can't be above the high end.")
      return
    }
    // For an edit, send only what changed, so a report's own marker name is kept
    // unless you change the marker.
    const before = initial ? toInput(toForm(initial)) : null
    const changed = Object.fromEntries(
      Object.entries(lab).filter(([k, v]) => !before || before[k as keyof LabInput] !== v),
    ) as Partial<LabInput>
    setBusy(true)
    setError(null)
    try {
      await onSubmit(lab, changed)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const byCategory = new Map<MarkerCategory, LabMarker[]>()
  for (const m of markers) byCategory.set(m.category, [...(byCategory.get(m.category) ?? []), m])
  const ready = values.marker_key && values.value_text.trim() && values.unit.trim() && values.date

  return (
    <form className={styles.form} onSubmit={submit}>
      <div className={styles.row2}>
        <label className={styles.field}>
          <span>Test</span>
          <select
            required
            value={values.marker_key}
            onChange={(e) => pickMarker(e.target.value)}
          >
            <option value="" disabled>
              Choose a test
            </option>
            {[...byCategory].map(([category, list]) => (
              <optgroup key={category} label={CATEGORY_LABEL[category]}>
                {list.map((m) => (
                  <option key={m.key} value={m.key}>
                    {m.display_name}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
        <label className={styles.field}>
          <span>Date collected</span>
          <input
            type="date"
            required
            max={today}
            value={values.date}
            onChange={(e) => set('date', e.target.value)}
          />
        </label>
      </div>
      <div className={styles.row2}>
        <label className={styles.field}>
          <span>Value</span>
          <input
            required
            maxLength={20}
            placeholder="e.g. 2.1 or <0.5"
            value={values.value_text}
            onChange={(e) => set('value_text', e.target.value)}
          />
        </label>
        <label className={styles.field}>
          <span>Unit</span>
          <input
            required
            maxLength={20}
            placeholder="e.g. mIU/L"
            list="lab-units"
            value={values.unit}
            onChange={(e) => set('unit', e.target.value)}
          />
          <datalist id="lab-units">
            {unitsSeen.map((u) => (
              <option key={u} value={u} />
            ))}
          </datalist>
        </label>
      </div>
      <fieldset className={styles.range}>
        <legend>
          Reference range on the report <em>(optional)</em>
        </legend>
        <div className={styles.row2}>
          <label className={styles.field}>
            <span>Low</span>
            <input
              type="number"
              inputMode="decimal"
              min="0"
              step="any"
              value={values.ref_low}
              onChange={(e) => set('ref_low', e.target.value)}
            />
          </label>
          <label className={styles.field}>
            <span>High</span>
            <input
              type="number"
              inputMode="decimal"
              min="0"
              step="any"
              value={values.ref_high}
              onChange={(e) => set('ref_high', e.target.value)}
            />
          </label>
        </div>
        <p className={ui.hint}>
          For a range printed like "&lt;34", fill in only High. For "&gt;39", only Low.
        </p>
      </fieldset>
      {error && <p className={ui.error}>{error}</p>}
      <div className={styles.actions}>
        {onCancel && (
          <button type="button" className={ui.secondary} onClick={onCancel}>
            Cancel
          </button>
        )}
        <button type="submit" className={ui.primary} disabled={busy || !ready}>
          {submitLabel}
        </button>
      </div>
    </form>
  )
}

function FlagPill({ flag }: { flag: LabFlag | null }) {
  const tone = flag === 'below' || flag === 'above' ? styles.out : flag ? styles.within : ''
  return <span className={`${styles.pill} ${tone}`}>{flagLabel(flag)}</span>
}

function MarkerCard({
  group,
  markers,
  results,
  today,
  onChange,
}: {
  group: MarkerGroup
  markers: LabMarker[]
  results: LabResult[]
  today: string
  onChange: () => void
}) {
  const [showAll, setShowAll] = useState(false)
  const latest = group.results[group.results.length - 1]
  const series = splitByUnit(group.results)
  const count = group.results.length

  return (
    <article className={ui.card}>
      <div className={styles.cardTop}>
        <div className={styles.titleBlock}>
          <h3 className={styles.name}>{group.name}</h3>
          <span className={ui.hint}>
            {count} {count === 1 ? 'result' : 'results'} · latest {mediumDate(latest.date)}
          </span>
        </div>
        <div className={styles.latest}>
          <span className={styles.latestValue}>
            {latest.value_text} <span className={styles.unit}>{latest.unit}</span>
          </span>
          <FlagPill flag={latest.flag} />
        </div>
      </div>

      {series.length > 1 && (
        <p className={styles.note}>
          These results use {series.length} different units ({series.map((s) => s.unit).join(', ')}
          ). Each unit has its own chart. Values aren't converted.
        </p>
      )}
      {series.map((s) => (
        <MarkerChart key={s.unit} unit={s.unit} results={s.results} labelled={series.length > 1} />
      ))}

      <button
        type="button"
        className={`${ui.linkButton} ${styles.toggle}`}
        onClick={() => setShowAll((v) => !v)}
        aria-expanded={showAll}
      >
        {showAll ? 'Hide results' : `Show all ${count} ${count === 1 ? 'result' : 'results'}`}
      </button>
      {showAll && (
        <ResultList
          rows={[...group.results].reverse()}
          markers={markers}
          results={results}
          today={today}
          onChange={onChange}
        />
      )}
    </article>
  )
}

type Point = LabResult & { t: number }

const dateTick = (t: number) => mediumDate(toIso(new Date(t)))

function MarkerChart({
  unit,
  results,
  labelled,
}: {
  unit: string
  results: LabResult[]
  labelled: boolean
}) {
  const points: Point[] = results.map((r) => ({ ...r, t: fromIso(r.date).getTime() }))
  const latest = results[results.length - 1]
  const band = latest.ref_low !== null || latest.ref_high !== null ? latest : null
  const y = yScale(results, band)
  // Real time on the x axis, so uneven gaps between tests look uneven.
  const first = points[0].t
  const last = points[points.length - 1].t
  const xPad = Math.max((last - first) * 0.06, 12 * 86_400_000)
  const bandText = band && rangeLabel(band)

  return (
    <figure className={styles.chart}>
      {labelled && <figcaption className={styles.unitLabel}>{unit}</figcaption>}
      <ResponsiveContainer width="100%" height={190}>
        <LineChart data={points} margin={{ top: 10, right: 12, bottom: 0, left: -12 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          {band && (
            <ReferenceArea
              // An open end ("up to 34") runs to the edge of the axis.
              y1={band.ref_low ?? y.domain[0]}
              y2={band.ref_high ?? y.domain[1]}
              fill="var(--band)"
              fillOpacity={1}
              stroke="none"
              ifOverflow="hidden"
            />
          )}
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={[first - xPad, last + xPad]}
            tickFormatter={dateTick}
            tickCount={4}
            {...AXIS}
          />
          <YAxis domain={y.domain} ticks={y.ticks} width={52} {...AXIS} />
          <Tooltip
            {...TOOLTIP}
            cursor={{ stroke: 'var(--border)' }}
            content={({ active, payload }) => {
              const p = payload?.[0]?.payload as Point | undefined
              if (!active || !p) return null
              const range = rangeLabel(p)
              return (
                <div className={styles.tooltip}>
                  <strong>{mediumDate(p.date)}</strong>
                  <span>
                    {p.value_text} {p.unit}
                  </span>
                  <span className={ui.hint}>{range ? `Range ${range}` : 'No range given'}</span>
                  <FlagPill flag={p.flag} />
                </div>
              )
            }}
          />
          <Line
            dataKey="value"
            type="linear"
            stroke="var(--accent)"
            strokeWidth={2}
            isAnimationActive={false}
            activeDot={false}
            dot={(props: { cx?: number; cy?: number; payload?: Point }) => {
              const { cx, cy, payload } = props
              if (cx === undefined || cy === undefined || !payload) return <g key={payload?.id ?? 'none'} />
              const out = payload.flag === 'below' || payload.flag === 'above'
              return (
                <circle
                  key={payload.id}
                  cx={cx}
                  cy={cy}
                  r={out ? 6 : 4}
                  fill={out ? 'var(--flag)' : 'var(--accent)'}
                  stroke="var(--surface)"
                  strokeWidth={2}
                />
              )
            }}
          />
        </LineChart>
      </ResponsiveContainer>
      <p className={styles.legend}>
        {bandText && (
          <span>
            <i className={styles.bandSwatch} /> Range on your latest report ({bandText})
          </span>
        )}
        <span>
          <i className={styles.outSwatch} /> Outside the range on its own report
        </span>
      </p>
      {rangesDiffer(results) && (
        <p className={ui.hint}>Your reports printed different ranges for this test.</p>
      )}
    </figure>
  )
}

function ResultList({
  rows,
  markers,
  results,
  today,
  onChange,
}: {
  rows: LabResult[]
  markers: LabMarker[]
  results: LabResult[]
  today: string
  onChange: () => void
}) {
  const [editing, setEditing] = useState<string | null>(null)

  async function remove(r: LabResult) {
    if (!window.confirm(`Delete the ${r.raw_marker} result from ${mediumDate(r.date)}?`)) return
    try {
      await deleteLab(r.id)
      onChange()
    } catch (e) {
      window.alert((e as Error).message)
    }
  }

  return (
    <ul className={styles.list}>
      {rows.map((r) => {
        if (editing === r.id) {
          return (
            <li key={r.id} className={styles.row}>
              <LabForm
                initial={r}
                markers={markers}
                results={results}
                today={today}
                submitLabel="Save changes"
                onCancel={() => setEditing(null)}
                onSubmit={async (_lab, changed) => {
                  if (Object.keys(changed).length > 0) await patchLab(r.id, changed)
                  setEditing(null)
                  onChange()
                }}
              />
            </li>
          )
        }
        const range = rangeLabel(r)
        return (
          <li key={r.id} className={styles.row}>
            <div className={styles.rowMain}>
              <span className={styles.rowDate}>{mediumDate(r.date)}</span>
              <span className={styles.rowValue}>
                {r.value_text} {r.unit}
              </span>
              <span className={ui.hint}>
                {range ? `Range ${range}` : 'No range'}
                {r.from_report && ' · from a report'}
              </span>
            </div>
            <FlagPill flag={r.flag} />
            <div className={styles.rowActions}>
              <button
                type="button"
                className={styles.iconButton}
                onClick={() => setEditing(r.id)}
                aria-label={`Edit the result from ${mediumDate(r.date)}`}
              >
                <Icon name="edit" size={16} />
              </button>
              <button
                type="button"
                className={`${styles.iconButton} ${styles.danger}`}
                onClick={() => remove(r)}
                aria-label={`Delete the result from ${mediumDate(r.date)}`}
              >
                <Icon name="trash" size={16} />
              </button>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
