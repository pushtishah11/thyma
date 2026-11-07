import { lazy, Suspense } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router'

import styles from './App.module.css'
import Icon, { type IconName } from './components/Icon'
import Settings from './pages/Settings'
import Today from './pages/Today'

// Trends pulls in Recharts (large), so it's loaded only when you open it.
const Trends = lazy(() => import('./pages/Trends'))
const Cycles = lazy(() => import('./pages/Cycles'))

const TABS: { to: string; label: string; icon: IconName }[] = [
  { to: '/today', label: 'Today', icon: 'today' },
  { to: '/trends', label: 'Trends', icon: 'trends' },
  { to: '/cycles', label: 'Cycles', icon: 'drop' },
  { to: '/settings', label: 'Settings', icon: 'settings' },
]

const tabClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.tab} ${styles.active}` : styles.tab

function App() {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <NavLink to="/today" className={styles.brand}>
          <span className={styles.logo}>
            <Icon name="logo" size={20} />
          </span>
          Thyma
        </NavLink>
        {/* On a phone this same nav becomes a tab bar fixed to the bottom of the screen. */}
        <nav className={styles.nav} aria-label="Main">
          {TABS.map((t) => (
            <NavLink key={t.to} to={t.to} className={tabClass}>
              <Icon name={t.icon} size={20} />
              <span>{t.label}</span>
            </NavLink>
          ))}
        </nav>
      </header>

      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<Navigate to="/today" replace />} />
          <Route path="/today" element={<Today />} />
          <Route
            path="/trends"
            element={
              <Suspense fallback={<p className={styles.loading}>Loading…</p>}>
                <Trends />
              </Suspense>
            }
          />
          <Route
            path="/cycles"
            element={
              <Suspense fallback={<p className={styles.loading}>Loading…</p>}>
                <Cycles />
              </Suspense>
            }
          />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<p>That page doesn't exist.</p>} />
        </Routes>
      </main>
    </div>
  )
}

export default App
