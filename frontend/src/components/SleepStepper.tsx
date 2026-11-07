import Icon from './Icon'
import styles from './SleepStepper.module.css'

type Props = {
  value: number | null
  onChange: (value: number | null) => void
}

const STEP = 0.5
const START = 7 // first tap on an empty value starts here, so you nudge rather than count up from 0

// Hours of sleep with - / + buttons in half-hour steps, instead of typing a number.
export default function SleepStepper({ value, onChange }: Props) {
  const nudge = (delta: number) => {
    if (value === null) return onChange(START)
    onChange(Math.min(24, Math.max(0, value + delta)))
  }

  return (
    <div className={styles.row}>
      <button
        type="button"
        className={styles.step}
        onClick={() => nudge(-STEP)}
        disabled={value === 0}
        aria-label="Half an hour less sleep"
      >
        <Icon name="minus" />
      </button>
      <div className={styles.value} aria-live="polite">
        {value === null ? (
          <span className={styles.empty}>Not logged</span>
        ) : (
          <>
            <span className={styles.number}>{value}</span>
            <span className={styles.unit}>hours</span>
          </>
        )}
      </div>
      <button
        type="button"
        className={styles.step}
        onClick={() => nudge(STEP)}
        disabled={value === 24}
        aria-label="Half an hour more sleep"
      >
        <Icon name="plus" />
      </button>
      {value !== null && (
        <button type="button" className={styles.clear} onClick={() => onChange(null)}>
          Clear
        </button>
      )}
    </div>
  )
}
