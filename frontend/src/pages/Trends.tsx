import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { getTrends } from '../api'
import { addDays, fromIso, todayIso } from '../dates'
import type { Trends as TrendsData } from '../types'
import styles from './Trends.module.css'

const RANGES = [30, 90, 180] as const
type Range = (typeof RANGES)[number]

// Shared chart styling: recessive grid and axes, text in text colors.
const AXIS = { stroke: 'var(--border)', tick: { fill: 'var(--muted)', fontSize: 12 } }
const TOOLTIP = {
  contentStyle: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text)',
  },
  labelStyle: { color: 'var(--text-strong)', fontWeight: 600 },
}

const shortDate = (iso: string) =>
  fromIso(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

export default function Trends() {
  const [range, setRange] = useState<Range>(30)
  const [data, setData] = useState<{ range: Range; trends: TrendsData } | null>(null)
  const [error, setError] = useState<{ range: Range; message: string } | null>(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let active = true
    const end = todayIso()
    getTrends(addDays(end, -(range - 1)), end)
      .then((trends) => {
        if (!active) return
        setData({ range, trends })
        setError(null)
      })
      .catch((e: Error) => active && setError({ range, message: e.message }))
    return () => {
      active = false
    }
  }, [range, retry])

  const trends = data?.range === range ? data.trends : null
  const failed = error?.range === range

  return (
    <>
      <div className={styles.head}>
        <h1 className={styles.title}>Trends</h1>
        <div className={styles.toggle} role="group" aria-label="Date range">
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              aria-pressed={range === r}
              className={styles.toggleButton}
              onClick={() => setRange(r)}
            >
              {r} days
            </button>
          ))}
        </div>
      </div>

      {failed && (
        <div className={styles.card} role="alert">
          <p className={styles.error}>{error.message}</p>
          <button type="button" className={styles.secondary} onClick={() => setRetry((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}

      {!trends && !failed && <p className={styles.subtle}>Loading…</p>}

      {trends && trends.days_logged === 0 && (
        <div className={styles.card}>
          <p className={styles.subtle}>
            Nothing logged in the last {range} days. <Link to="/today">Log a day</Link> and your
            trends will show up here.
          </p>
        </div>
      )}

      {trends && trends.days_logged > 0 && <Charts trends={trends} />}
    </>
  )
}

function Charts({ trends }: { trends: TrendsData }) {
  const daily = trends.daily.map((d) => ({ ...d, label: shortDate(d.date) }))
  const hasSleep = trends.daily.some((d) => d.sleep_hours !== null)

  return (
    <>
      <p className={styles.subtle}>
        You logged {trends.days_logged} of {trends.days_in_range} days. Gaps in the lines are days
        with no log.
      </p>

      <section className={styles.card}>
        <h2 className={styles.cardTitle}>Energy and mood</h2>
        <p className={styles.caption}>1 = lowest, 5 = highest</p>
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={daily} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}>
            <CartesianGrid stroke="var(--grid)" vertical={false} />
            <XAxis dataKey="label" {...AXIS} minTickGap={24} />
            <YAxis domain={[1, 5]} ticks={[1, 2, 3, 4, 5]} {...AXIS} />
            <Tooltip {...TOOLTIP} />
            <Legend wrapperStyle={{ fontSize: 13, color: 'var(--text)' }} />
            <Line
              name="Energy"
              dataKey="energy"
              stroke="var(--series-1)"
              strokeWidth={2}
              dot={{ r: 3.5, fill: 'var(--series-1)', stroke: 'var(--surface)', strokeWidth: 1.5 }}
              activeDot={{ r: 5, stroke: 'var(--surface)', strokeWidth: 2 }}
              connectNulls={false}
              isAnimationActive={false}
            />
            <Line
              name="Mood"
              dataKey="mood"
              stroke="var(--series-2)"
              strokeWidth={2}
              dot={{ r: 3.5, fill: 'var(--series-2)', stroke: 'var(--surface)', strokeWidth: 1.5 }}
              activeDot={{ r: 5, stroke: 'var(--surface)', strokeWidth: 2 }}
              connectNulls={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </section>

      <section className={styles.card}>
        <h2 className={styles.cardTitle}>Sleep</h2>
        <p className={styles.caption}>Hours per night</p>
        {hasSleep ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={daily} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="label" {...AXIS} minTickGap={24} />
              <YAxis domain={[0, 'dataMax + 1']} allowDecimals={false} {...AXIS} />
              <Tooltip {...TOOLTIP} formatter={(v) => [`${v} h`, 'Sleep']} />
              <Line
                name="Sleep"
                dataKey="sleep_hours"
                stroke="var(--accent)"
                strokeWidth={2}
                dot={{ r: 3.5, fill: 'var(--accent)', stroke: 'var(--surface)', strokeWidth: 1.5 }}
                activeDot={{ r: 5, stroke: 'var(--surface)', strokeWidth: 2 }}
                connectNulls={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className={styles.subtle}>No sleep logged in this range.</p>
        )}
      </section>

      <section className={styles.card}>
        <h2 className={styles.cardTitle}>Symptoms</h2>
        <p className={styles.caption}>
          Share of logged days each symptom appeared, with its average severity (1 mild – 3
          severe)
        </p>
        {trends.symptoms.length === 0 ? (
          <p className={styles.subtle}>No symptoms logged in this range.</p>
        ) : (
          <SymptomBars trends={trends} />
        )}
      </section>
    </>
  )
}

function SymptomBars({ trends }: { trends: TrendsData }) {
  const rows = trends.symptoms.map((s) => ({
    ...s,
    label: `${s.percent_of_logged_days}% · avg ${s.avg_severity.toFixed(1)}`,
  }))
  return (
    <ResponsiveContainer width="100%" height={rows.length * 36 + 16}>
      <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 96, bottom: 0, left: 0 }}>
        <XAxis type="number" domain={[0, 100]} hide />
        <YAxis
          type="category"
          dataKey="symptom"
          width={130}
          {...AXIS}
          tick={{ fill: 'var(--text)', fontSize: 13 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          {...TOOLTIP}
          cursor={{ fill: 'var(--accent-soft)' }}
          formatter={(_v, _n, item) => {
            const s = item.payload as (typeof rows)[number]
            return [
              `${s.days} of ${trends.days_logged} logged days, avg severity ${s.avg_severity.toFixed(1)}`,
              s.symptom,
            ]
          }}
          labelFormatter={() => ''}
        />
        <Bar
          dataKey="percent_of_logged_days"
          fill="var(--accent)"
          barSize={18}
          radius={[0, 4, 4, 0]}
          isAnimationActive={false}
        >
          <LabelList dataKey="label" position="right" fill="var(--text)" fontSize={12} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
