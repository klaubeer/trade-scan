import { BrowserRouter, Routes, Route, NavLink, Link } from 'react-router-dom'
import Home from './paginas/Home.jsx'
import Ingestao from './paginas/Ingestao.jsx'
import Setups from './paginas/Setups.jsx'
import Backtesting from './paginas/Backtesting.jsx'
import Comparativo from './paginas/Comparativo.jsx'
import WalkForward from './paginas/WalkForward.jsx'
import MonteCarlo from './paginas/MonteCarlo.jsx'
import CNNPadroes from './paginas/CNNPadroes.jsx'
import Historico from './paginas/Historico.jsx'

const nav = [
  { to: '/dados',        label: 'Dados' },
  { to: '/setups',       label: 'Setups' },
  { to: '/backtest',     label: 'Backtesting' },
  { to: '/historico',    label: 'Histórico' },
  { to: '/comparativo',  label: 'Comparativo' },
  { to: '/walk-forward', label: 'Walk-Forward' },
  { to: '/monte-carlo',  label: 'Monte Carlo' },
  { to: '/cnn-padroes',  label: 'CNN' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh' }}>
        <nav style={{
          width: 180, flexShrink: 0,
          background: 'var(--bg2)', borderRight: '1px solid var(--border)',
          padding: '24px 0',
        }}>
          <Link to="/" style={{ display: 'block', padding: '0 20px 24px', fontWeight: 700, fontSize: 18, color: 'var(--blue)', textDecoration: 'none' }}>
            TradeScan
          </Link>
          {nav.map(n => (
            <NavLink
              key={n.to} to={n.to} end={n.to === '/'}
              style={({ isActive }) => ({
                display: 'block', padding: '10px 20px',
                color: isActive ? 'var(--blue)' : 'var(--text2)',
                background: isActive ? 'rgba(74,158,255,0.08)' : 'transparent',
                borderLeft: isActive ? '3px solid var(--blue)' : '3px solid transparent',
                fontSize: 14,
              })}
            >
              {n.label}
            </NavLink>
          ))}
        </nav>

        <main style={{ flex: 1, padding: '32px', overflowY: 'auto', maxWidth: 1200 }}>
          <Routes>
            <Route path="/"             element={<Home />} />
            <Route path="/dados"        element={<Ingestao />} />
            <Route path="/setups"       element={<Setups />} />
            <Route path="/backtest"     element={<Backtesting />} />
            <Route path="/comparativo"  element={<Comparativo />} />
            <Route path="/walk-forward" element={<WalkForward />} />
            <Route path="/monte-carlo"  element={<MonteCarlo />} />
            <Route path="/historico"    element={<Historico />} />
            <Route path="/cnn-padroes"  element={<CNNPadroes />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
