import type { Severity } from '../types'
import styles from './SymptomChip.module.css'

const SEVERITY_WORD: Record<Severity, string> = { 1: 'mild', 2: 'moderate', 3: 'severe' }

type Props = {
  name: string
  severity: Severity | null
  onTap: () => void
}

export default function SymptomChip({ name, severity, onTap }: Props) {
  const word = severity ? SEVERITY_WORD[severity] : null
  return (
    <button
      type="button"
      className={styles.chip}
      data-severity={severity ?? 0}
      aria-label={word ? `${name}, ${word}` : `${name}, not logged`}
      onClick={onTap}
    >
      <span>{name}</span>
      {severity && (
        <span className={styles.dots} aria-hidden="true">
          {'●'.repeat(severity)}
          <span className={styles.empty}>{'●'.repeat(3 - severity)}</span>
        </span>
      )}
    </button>
  )
}
