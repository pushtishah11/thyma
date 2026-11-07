import { useEffect, useState } from 'react'

import { addFoodTag, addMeal, deleteMeal, getFoodTags, getMealsForDay, suggestTags } from '../api'
import { nowTime, todayIso } from '../dates'
import ui from '../styles/ui.module.css'
import type { FoodTag, Meal, MealType } from '../types'
import Icon from './Icon'
import styles from './MealLogger.module.css'

const MEAL_TYPES: { key: MealType; label: string }[] = [
  { key: 'breakfast', label: 'Breakfast' },
  { key: 'lunch', label: 'Lunch' },
  { key: 'dinner', label: 'Dinner' },
  { key: 'snack', label: 'Snack' },
  { key: 'drink', label: 'Drink' },
]

// Set from the time by the server; never offered as a choice.
const LATE_NIGHT = 'late_night'

function guessMealType(): MealType {
  const hour = new Date().getHours()
  if (hour < 11) return 'breakfast'
  if (hour < 16) return 'lunch'
  if (hour < 21) return 'dinner'
  return 'snack'
}

// Meals for one day, plus a quick "add meal" row. Like the med checklist, meals save
// straight away and don't wait for the day's Save button.
export default function MealLogger({ date }: { date: string }) {
  const [meals, setMeals] = useState<{ date: string; list: Meal[] } | null>(null)
  const [tags, setTags] = useState<FoodTag[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    getFoodTags()
      .then((t) => active && setTags(t))
      .catch(() => {})
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    getMealsForDay(date)
      .then((list) => active && setMeals({ date, list }))
      .catch((e: Error) => active && setError(e.message))
    return () => {
      active = false
    }
  }, [date])

  const names = new Map(tags.map((t) => [t.key, t.display_name]))

  async function remove(meal: Meal) {
    if (!meals) return
    try {
      await deleteMeal(meal.id)
      setMeals({ ...meals, list: meals.list.filter((m) => m.id !== meal.id) })
    } catch (e) {
      setError((e as Error).message)
    }
  }

  if (!meals || meals.date !== date) return <p className={ui.hint}>{error ?? 'Loading…'}</p>

  return (
    <div className={styles.wrap}>
      {meals.list.length > 0 && (
        <ul className={styles.meals}>
          {meals.list.map((m) => (
            <li key={m.id} className={styles.meal}>
              <div className={styles.mealMain}>
                <span className={styles.mealHead}>
                  <span className={styles.mealType}>{m.meal_type}</span>
                  {m.time && <span className={ui.hint}>{m.time.slice(0, 5)}</span>}
                </span>
                <span className={styles.mealText}>{m.description}</span>
                {m.tags.length > 0 && (
                  <span className={styles.mealTags}>
                    {m.tags.map((t) => (
                      <span key={t} className={styles.pill}>
                        {names.get(t) ?? t}
                      </span>
                    ))}
                  </span>
                )}
              </div>
              <button
                type="button"
                className={styles.iconButton}
                onClick={() => remove(m)}
                aria-label={`Delete ${m.meal_type}: ${m.description}`}
              >
                <Icon name="close" size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
      <AddMeal
        key={date} // a fresh form (and default time) for each day
        date={date}
        tags={tags}
        onTagAdded={(tag) => setTags((t) => [...t, tag])}
        onAdded={(meal) =>
          setMeals((current) =>
            current && current.date === meal.date
              ? { ...current, list: [...current.list, meal] }
              : current,
          )
        }
      />
      {error && <p className={ui.error}>{error}</p>}
    </div>
  )
}

function AddMeal({
  date,
  tags,
  onAdded,
  onTagAdded,
}: {
  date: string
  tags: FoodTag[]
  onAdded: (meal: Meal) => void
  onTagAdded: (tag: FoodTag) => void
}) {
  const [mealType, setMealType] = useState<MealType>(guessMealType)
  const [description, setDescription] = useState('')
  const [time, setTime] = useState(() => (date === todayIso() ? nowTime() : ''))
  const [suggested, setSuggested] = useState<string[]>([])
  // What you tapped yourself always wins over a suggestion.
  const [manual, setManual] = useState<Record<string, boolean>>({})
  const [newTag, setNewTag] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Ask for suggestions a moment after you stop typing, not on every key.
  useEffect(() => {
    const text = description.trim()
    if (!text) return
    let active = true
    const timer = setTimeout(() => {
      suggestTags(text)
        .then((r) => active && setSuggested(r.tags))
        .catch(() => {})
    }, 350)
    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [description])

  const visibleSuggested = description.trim() ? suggested : []
  const isOn = (key: string) => manual[key] ?? visibleSuggested.includes(key)
  const selected = tags.filter((t) => t.key !== LATE_NIGHT && isOn(t.key)).map((t) => t.key)

  function toggle(key: string) {
    setManual((m) => ({ ...m, [key]: !isOn(key) }))
  }

  async function createTag() {
    const name = newTag?.trim()
    if (!name) return setNewTag(null)
    try {
      const tag = await addFoodTag(name)
      onTagAdded(tag)
      setManual((m) => ({ ...m, [tag.key]: true }))
      setNewTag(null)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!description.trim()) return
    setBusy(true)
    setError(null)
    try {
      const meal = await addMeal({
        date,
        time: time || null,
        meal_type: mealType,
        description: description.trim(),
        tags: selected,
      })
      onAdded(meal)
      setDescription('')
      setSuggested([])
      setManual({})
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    // A <div>, not a <form>: this sits inside the Today page's own form.
    <div className={styles.add}>
      <div className={styles.types} role="radiogroup" aria-label="Meal type">
        {MEAL_TYPES.map((t) => (
          <button
            key={t.key}
            type="button"
            role="radio"
            aria-checked={mealType === t.key}
            className={styles.type}
            onClick={() => setMealType(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className={styles.inputRow}>
        <input
          className={styles.description}
          maxLength={300}
          placeholder="What did you have? e.g. paneer wrap and chai"
          aria-label="What you ate or drank"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit(e)
          }}
        />
        <input
          type="time"
          className={styles.time}
          aria-label="Time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
        />
      </div>
      {description.trim() && (
        <>
          <p className={ui.hint}>
            {visibleSuggested.length > 0
              ? 'Tags suggested from what you typed. Tap to change.'
              : 'Tap any tags that fit.'}
          </p>
          <div className={styles.tagList}>
            {tags
              .filter((t) => t.key !== LATE_NIGHT)
              .map((t) => (
                <button
                  key={t.key}
                  type="button"
                  className={styles.tag}
                  aria-pressed={isOn(t.key)}
                  onClick={() => toggle(t.key)}
                >
                  {isOn(t.key) && <Icon name="check" size={13} />}
                  {t.display_name}
                </button>
              ))}
            {newTag === null ? (
              <button type="button" className={styles.newTag} onClick={() => setNewTag('')}>
                <Icon name="plus" size={13} /> Own tag
              </button>
            ) : (
              <input
                className={styles.newTagInput}
                autoFocus
                maxLength={40}
                placeholder="e.g. matcha"
                aria-label="New tag"
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onBlur={createTag}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    createTag()
                  }
                  if (e.key === 'Escape') setNewTag(null)
                }}
              />
            )}
          </div>
          <div className={styles.addActions}>
            <button
              type="button"
              className={ui.primary}
              disabled={busy}
              onClick={(e) => submit(e)}
            >
              Add {mealType}
            </button>
          </div>
        </>
      )}
      {error && <p className={ui.error}>{error}</p>}
    </div>
  )
}
