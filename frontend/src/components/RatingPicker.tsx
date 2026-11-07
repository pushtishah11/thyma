import styles from './RatingPicker.module.css'

type Props = {
  label: string
  // One word per value, 1 to 5, describing how *you* rated it (not a judgment).
  words: [string, string, string, string, string]
  value: number | null
  onChange: (value: number | null) => void
}

// A 1-5 segmented control. Tapping the selected value again clears it,
// so "I didn't rate this" is always one tap away.
export default function RatingPicker({ label, words, value, onChange }: Props) {
  return (
    <fieldset className={styles.picker}>
      <div className={styles.head}>
        <legend className={styles.label}>{label}</legend>
        <span className={styles.word} aria-live="polite">
          {value ? words[value - 1] : 'Not rated'}
        </span>
      </div>
      <div className={styles.segments}>
        {words.map((word, i) => {
          const n = i + 1
          return (
            <button
              key={n}
              type="button"
              className={styles.segment}
              aria-pressed={value === n}
              aria-label={`${label} ${n} of 5, ${word}`}
              title={word}
              onClick={() => onChange(value === n ? null : n)}
            >
              {n}
            </button>
          )
        })}
      </div>
      <div className={styles.ends} aria-hidden="true">
        <span>{words[0]}</span>
        <span>{words[4]}</span>
      </div>
    </fieldset>
  )
}
