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
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { getMeds, getTrends } from '../api'
import { AXIS, TOOLTIP } from '../charts'
import FoodList from '../components/FoodList'
import Icon, { type IconName } from '../components/Icon'
import { addDays, shortDate, todayIso } from '../dates'
import { type Marker, medMarkers } from '../markers'
import ui from '../styles/ui.module.css'
import type { Med, Trends as TrendsData } from '../types'
import styles from './Trends.module.css'

const RANGES = [30, 90, 180] as const
type Range = (typeof RANGES)[number]

export default function Trends() {
  const [range, setRange] = useState<Range>(30)
  const [data, setData] = useState<{ range: Range; trends: TrendsData } | null>(null)
  const [error, setError] = useState<{ range: Range; message: string } | null>(null)
  const [retry, setRetry] = useState(0)
  const [meds, setMeds] = useState<Med[]>([])

  // Med start/stop markers are extra: if they fail to load, the charts still show.
  useEffect(() => {
    let active = true
    getMeds()
      .then((m) => active && setMeds(m))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [])

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
        <div>
          <h1 className={ui.pageTitle}>Trends</h1>
          <p className={ui.pageSub}>Patterns in what you've logged</p>
        </div>
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
        <div className={ui.card} role="alert">
          <p className={ui.error}>{error.message}</p>
          <button type="button" className={ui.secondary} onClick={() => setRetry((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}

      {!trends && !failed && <p className={ui.hint}>Loading…</p>}

      {trends && trends.days_logged === 0 && (
        <div className={`${ui.card} ${ui.empty}`}>
          <Icon name="trends" size={32} />
          <p>
            Nothing logged in the last {range} days. <Link to="/today">Log a day</Link> and your
            trends will show up here.
          </p>
        </div>
      )}

      {trends && trends.days_logged > 0 && (
        <Charts trends={trends} markers={medMarkers(meds, trends.start, trends.end)} />
      )}

      {trends && <FoodList start={trends.start} end={trends.end} />}
    </>
  )
}

// Called as a plain function, not <MarkerLines />: Recharts only draws ReferenceLines
// that are direct children of the chart.
function MarkerLines({ markers }: { markers: Marker[] }) {
  // Numbered dashed lines; the numbers are explained in the list under the charts.
  return markers.map((m, i) => (
    <ReferenceLine
      key={`${m.date}-${i}`}
      x={shortDate(m.date)}
      stroke="var(--muted)"
      strokeDasharray="3 3"
      label={{ value: String(i + 1), position: 'top', fill: 'var(--muted)', fontSize: 11 }}
    />
  ))
}

function Charts({ trends, markers }: { trends: TrendsData; markers: Marker[] }) {
  const daily = trends.daily.map((d) => ({ ...d, label: shortDate(d.date) }))
  const hasSleep = trends.daily.some((d) => d.sleep_hours !== null)

  return (
    <>
      <Tiles trends={trends} />

      <div className={ui.pair}>
        <section className={ui.card}>
          <h2 className={ui.cardTitle}>
            <Icon name="pulse" /> Energy and mood
          </h2>
          <p className={styles.caption}>
            1 = lowest, 5 = highest. Gaps are days with no log.
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={daily} margin={{ top: 16, right: 8, bottom: 0, left: -24 }}>
              <CartesianGrid stroke="var(--grid)" vertical={false} />
              <XAxis dataKey="label" {...AXIS} minTickGap={24} />
              <YAxis domain={[1, 5]} ticks={[1, 2, 3, 4, 5]} {...AXIS} />
              <Tooltip {...TOOLTIP} />
              <Legend wrapperStyle={{ fontSize: 13, color: 'var(--text)' }} />
              {MarkerLines({ markers })}
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

        <section className={ui.card}>
          <h2 className={ui.cardTitle}>
            <Icon name="moon" /> Sleep
          </h2>
          <p className={styles.caption}>Hours per night</p>
          {hasSleep ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={daily} margin={{ top: 16, right: 8, bottom: 0, left: -24 }}>
                <CartesianGrid stroke="var(--grid)" vertical={false} />
                <XAxis dataKey="label" {...AXIS} minTickGap={24} />
                <YAxis domain={[0, 'dataMax + 1']} allowDecimals={false} {...AXIS} />
                <Tooltip {...TOOLTIP} formatter={(v) => [`${v} h`, 'Sleep']} />
                {MarkerLines({ markers })}
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
            <p className={ui.hint}>No sleep logged in this range.</p>
          )}
        </section>
      </div>

      <div className={ui.pair}>
        <section className={ui.card}>
          <h2 className={ui.cardTitle}>
            <Icon name="spark" /> Symptoms
          </h2>
          <p className={styles.caption}>
            Share of logged days each symptom appeared, with its average severity (1 mild – 3
            severe)
          </p>
          {trends.symptoms.length === 0 ? (
            <p className={ui.hint}>No symptoms logged in this range.</p>
          ) : (
            <SymptomBars trends={trends} />
          )}
        </section>

        {markers.length > 0 && (
          <section className={ui.card}>
            <h2 className={ui.cardTitle}>
              <Icon name="pill" /> Med &amp; supplement changes
            </h2>
            <p className={styles.caption}>The numbered dashed lines on the charts above.</p>
            <ol className={styles.markers}>
              {markers.map((m, i) => (
                <li key={`${m.date}-${i}`}>
                  <span className={styles.markerNum}>{i + 1}</span>
                  <span>{m.text}</span>
                  <span className={ui.hint}>{shortDate(m.date)}</span>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>
    </>
  )
}

type Tile = { label: string; value: string; detail: string; icon: IconName }

// The headline numbers for the range, straight from the API (already rounded there).
function Tiles({ trends }: { trends: TrendsData }) {
  const fmt = (v: number | null) => (v === null ? '–' : v.toFixed(1))
  const tiles: Tile[] = [
    {
      label: 'Days logged',
      value: `${trends.days_logged}`,
      detail: `of ${trends.days_in_range}`,
      icon: 'today',
    },
    { label: 'Avg energy', value: fmt(trends.avg_energy), detail: 'out of 5', icon: 'pulse' },
    { label: 'Avg mood', value: fmt(trends.avg_mood), detail: 'out of 5', icon: 'spark' },
    {
      label: 'Avg sleep',
      value: fmt(trends.avg_sleep_hours),
      detail: 'hours',
      icon: 'moon',
    },
  ]
  return (
    <div className={styles.tiles}>
      {tiles.map((t) => (
        <div key={t.label} className={styles.tile}>
          <span className={styles.tileLabel}>
            <Icon name={t.icon} size={15} /> {t.label}
          </span>
          <span className={styles.tileValue}>
            {t.value} <span className={styles.tileDetail}>{t.detail}</span>
          </span>
        </div>
      ))}
    </div>
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
