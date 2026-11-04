import styles from './RatingPicker.module.css'

type Props = {
  label: string
  low: string
  high: string
  value: number | null
  onChange: (value: number | null) => void
}

// A 1-5 row of buttons. Tapping the selected value again clears it,
// so "I didn't rate this" is always one tap away.
export default function RatingPicker({ label, low, high, value, onChange }: Props) {
  return (
    <fieldset className={styles.picker}>
      <legend className={styles.label}>{label}</legend>
      <div className={styles.buttons}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            className={styles.button}
            aria-pressed={value === n}
            aria-label={`${label} ${n} of 5`}
            onClick={() => onChange(value === n ? null : n)}
          >
            {n}
          </button>
        ))}
      </div>
      <div className={styles.ends} aria-hidden="true">
        <span>{low}</span>
        <span>{high}</span>
      </div>
    </fieldset>
  )
}
