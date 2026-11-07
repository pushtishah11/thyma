// Shared chart styling for Recharts: recessive grid and axes, text in text colors.

export const AXIS = { stroke: 'var(--border)', tick: { fill: 'var(--muted)', fontSize: 12 } }

export const TOOLTIP = {
  contentStyle: {
    background: 'var(--surface)',
    border: '1px solid var(--border)',
    borderRadius: 8,
    color: 'var(--text)',
  },
  labelStyle: { color: 'var(--text-strong)', fontWeight: 600 },
}
