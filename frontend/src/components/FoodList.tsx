import { useEffect, useState } from 'react'

import { getFoodTags, getMealsInRange } from '../api'
import { formatLong } from '../dates'
import ui from '../styles/ui.module.css'
import type { Meal } from '../types'
import styles from './FoodList.module.css'
import Icon from './Icon'

const DAYS_SHOWN = 7

// What you ate in the range, newest day first, with how often each tag came up.
// Counts only: no totals, scores or "good/bad" anywhere.
export default function FoodList({ start, end }: { start: string; end: string }) {
  const [meals, setMeals] = useState<{ key: string; list: Meal[] } | null>(null)
  const [names, setNames] = useState<Map<string, string>>(new Map())
  const [error, setError] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)
  const key = `${start}/${end}`

  useEffect(() => {
    let active = true
    Promise.all([getMealsInRange(start, end), getFoodTags()])
      .then(([list, tags]) => {
        if (!active) return
        setMeals({ key: `${start}/${end}`, list })
        setNames(new Map(tags.map((t) => [t.key, t.display_name])))
      })
      .catch((e: Error) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [start, end])

  const list = meals?.key === key ? meals.list : null

  const byDay = new Map<string, Meal[]>()
  for (const m of list ?? []) byDay.set(m.date, [...(byDay.get(m.date) ?? []), m])
  const days = [...byDay.keys()].sort().reverse()
  const shownDays = showAll ? days : days.slice(0, DAYS_SHOWN)

  const tagCounts = new Map<string, number>()
  for (const m of list ?? []) for (const t of m.tags) tagCounts.set(t, (tagCounts.get(t) ?? 0) + 1)
  const topTags = [...tagCounts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))

  return (
    <section className={ui.card}>
      <div className={ui.cardHead}>
        <h2 className={ui.cardTitle}>
          <Icon name="bowl" /> Food &amp; drinks
        </h2>
        {list && list.length > 0 && <span className={ui.hint}>{list.length} logged</span>}
      </div>

      {error && <p className={ui.error}>{error}</p>}
      {!list && !error && <p className={ui.hint}>Loading…</p>}
      {list && list.length === 0 && (
        <p className={ui.hint}>No meals logged in this range. Add them from the Today page.</p>
      )}

      {topTags.length > 0 && (
        <div className={styles.tags}>
          <span className={ui.hint}>Tags in this range:</span>
          {topTags.map(([t, n]) => (
            <span key={t} className={styles.tagCount}>
              {names.get(t) ?? t} <strong>{n}</strong>
            </span>
          ))}
        </div>
      )}

      {shownDays.map((day) => (
        <div key={day} className={styles.day}>
          <h3 className={styles.dayTitle}>{formatLong(day)}</h3>
          <ul className={styles.meals}>
            {byDay.get(day)!.map((m) => (
              <li key={m.id} className={styles.meal}>
                <span className={styles.type}>{m.meal_type}</span>
                <span className={styles.text}>
                  {m.description}
                  {m.tags.length > 0 && (
                    <span className={styles.mealTags}>
                      {' · '}
                      {m.tags.map((t) => names.get(t) ?? t).join(', ')}
                    </span>
                  )}
                </span>
                {m.time && <span className={ui.hint}>{m.time.slice(0, 5)}</span>}
              </li>
            ))}
          </ul>
        </div>
      ))}

      {days.length > DAYS_SHOWN && (
        <button type="button" className={ui.linkButton} onClick={() => setShowAll((s) => !s)}>
          {showAll ? 'Show fewer days' : `Show all ${days.length} days`}
        </button>
      )}
    </section>
  )
}
