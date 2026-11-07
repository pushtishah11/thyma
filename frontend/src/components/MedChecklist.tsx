import { useEffect, useState } from 'react'
import { Link } from 'react-router'

import { getDoses, putDose } from '../api'
import { nowTime, todayIso } from '../dates'
import { doseLabel } from '../format'
import ui from '../styles/ui.module.css'
import type { DayDose } from '../types'
import Icon from './Icon'
import styles from './MedChecklist.module.css'

// "Taken today" for every med and supplement active on `date`.
// Each tap saves straight away (it's separate from the day's Save button),
// so ticking a pill off never depends on remembering to save the rest.
export default function MedChecklist({ date }: { date: string }) {
  const [rows, setRows] = useState<{ date: string; doses: DayDose[] } | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    getDoses(date)
      .then((doses) => active && setRows({ date, doses }))
      .catch((e: Error) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [date])

  async function save(dose: DayDose, taken: boolean, time: string | null) {
    if (!rows) return
    const before = rows
    const id = dose.medication.id
    // Show the change right away; put it back if the save fails.
    setRows({
      ...rows,
      doses: rows.doses.map((d) =>
        d.medication.id === id ? { ...d, taken, time_taken: time } : d,
      ),
    })
    setError(null)
    try {
      await putDose(id, date, taken, time)
    } catch (e) {
      setRows(before)
      setError((e as Error).message)
    }
  }

  function tap(dose: DayDose) {
    // Not marked -> taken -> skipped -> taken ...
    if (dose.taken === true) return save(dose, false, null)
    const time = date === todayIso() ? nowTime() : null
    return save(dose, true, time)
  }

  if (!rows || rows.date !== date) {
    return <p className={ui.hint}>{error ?? 'Loading…'}</p>
  }

  if (rows.doses.length === 0) {
    return (
      <p className={ui.hint}>
        Nothing active on this day. <Link to="/meds">Add meds or supplements</Link> to tick them off
        here.
      </p>
    )
  }

  return (
    <>
      <ul className={styles.list}>
        {rows.doses.map((d) => {
          const state = d.taken === true ? 'taken' : d.taken === false ? 'skipped' : 'open'
          const label = [d.medication.name, doseLabel(d.medication)].filter(Boolean).join(' ')
          return (
            <li key={d.medication.id} className={styles.row} data-state={state}>
              <button
                type="button"
                className={styles.toggle}
                onClick={() => tap(d)}
                aria-label={`${label}: ${state === 'open' ? 'not marked' : state}. Tap to change.`}
              >
                <span className={styles.check} aria-hidden="true">
                  {state === 'taken' && <Icon name="check" size={16} />}
                  {state === 'skipped' && <Icon name="skip" size={14} />}
                </span>
                <span className={styles.text}>
                  <span className={styles.name}>{d.medication.name}</span>
                  <span className={styles.meta}>
                    {[doseLabel(d.medication), d.medication.kind].filter(Boolean).join(' · ')}
                  </span>
                </span>
                <span className={styles.status}>
                  {state === 'open' && 'Tap when taken'}
                  {state === 'taken' && 'Taken'}
                  {state === 'skipped' && 'Skipped'}
                </span>
              </button>
              {state === 'taken' && (
                <input
                  type="time"
                  className={styles.time}
                  aria-label={`Time ${d.medication.name} was taken`}
                  value={d.time_taken?.slice(0, 5) ?? ''}
                  onChange={(e) => save(d, true, e.target.value || null)}
                />
              )}
            </li>
          )
        })}
      </ul>
      {error && <p className={ui.error}>{error}</p>}
    </>
  )
}
