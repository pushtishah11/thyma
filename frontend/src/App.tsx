import { lazy, Suspense } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router'

import styles from './App.module.css'
import Settings from './pages/Settings'
import Today from './pages/Today'

// Trends pulls in Recharts (large), so it's loaded only when you open it.
const Trends = lazy(() => import('./pages/Trends'))

const navClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.navLink} ${styles.active}` : styles.navLink

function App() {
  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <span className={styles.brand}>Thyma</span>
        <nav className={styles.nav}>
          <NavLink to="/today" className={navClass}>
            Today
          </NavLink>
          <NavLink to="/trends" className={navClass}>
            Trends
          </NavLink>
          <NavLink to="/settings" className={navClass}>
            Settings
          </NavLink>
        </nav>
      </header>

      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<Navigate to="/today" replace />} />
          <Route path="/today" element={<Today />} />
          <Route
            path="/trends"
            element={
              <Suspense fallback={<p>Loading…</p>}>
                <Trends />
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
