import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import api from '../api.js'

export default function MonteCarlo() {
  const [searchParams] = useSearchParams()
  const [runs, setRuns] = useState([])
  const [form, setForm] = useState({ run_id: searchParams.get('run_id') || '', n_simulacoes: 1000 })
  const [carregando, setCarregando] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState(null)
  const [thresholdRuin, setThresholdRuin] = useState(300)

  useEffect(() => {
    api.get('/setups').then(async r => {
      const allRuns = []
      for (const s of r.data) {
        // buscar runs recentes por setup seria melhor, mas simplificamos aqui
      }
      setRuns(allRuns)
    }).catch(() => {})
  }, [])

  async function executar(e) {
    e.preventDefault(); setErro(null); setCarregando(true)
    try {
      const r = await api.post('/monte-carlo/executar', {
        run_id: Number(form.run_id),
        n_simulacoes: Number(form.n_simulacoes),
      })
      setResultado(r.data)
    } catch (err) { setErro(err.message) }
    finally { setCarregando(false) }
  }

  const pRuin = resultado?.max_drawdowns
    ? (resultado.max_drawdowns.filter(d => d > thresholdRuin).length / resultado.max_drawdowns.length * 100).toFixed(1)
    : null

  const bandaData = resultado?.banda_equity?.map(b => ({
    trade: b.posicao + 1, p10: b.p10, p50: b.p50, p90: b.p90,
  })) || []

  const histDDData = () => {
    if (!resultado?.max_drawdowns) return []
    const vals = resultado.max_drawdowns
    const min = Math.floor(Math.min(...vals) / 50) * 50
    const max = Math.ceil(Math.max(...vals) / 50) * 50
    const bins = []
    for (let b = min; b < max; b += 50) {
      bins.push({ bin: b, contagem: vals.filter(v => v >= b && v < b + 50).length })
    }
    return bins
  }

  const pct = resultado?.percentis_drawdown

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Monte Carlo Simulation</h1>

      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={executar}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div>
              <label>Run ID (de um backtest executado)</label>
              <input type="number" required min="1"
                value={form.run_id}
                onChange={e => setForm(f => ({ ...f, run_id: e.target.value }))}
                placeholder="Ex: 1"
              />
            </div>
            <div>
              <label>Número de Simulações</label>
              <input type="number" min="100" max="10000"
                value={form.n_simulacoes}
                onChange={e => setForm(f => ({ ...f, n_simulacoes: e.target.value }))}
              />
            </div>
          </div>
          <div style={{ marginTop: 16 }}>
            <button type="submit" disabled={carregando}>
              {carregando ? <><span className="spinner" style={{ marginRight: 8 }} />Simulando...</> : 'Executar Monte Carlo'}
            </button>
          </div>
        </form>
        {erro && <div className="erro-msg" style={{ marginTop: 12 }}>{erro}</div>}
      </div>

      {resultado && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {resultado.n_trades < 30 && (
            <div className="aviso">⚠ Apenas {resultado.n_trades} trades — percentis podem não ser representativos.</div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {pct && [
              { label: 'Drawdown P50', value: `${pct.p50?.toFixed(0)} pts` },
              { label: 'Drawdown P90', value: `${pct.p90?.toFixed(0)} pts`, color: 'var(--yellow)' },
              { label: 'Drawdown P95', value: `${pct.p95?.toFixed(0)} pts`, color: 'var(--red)' },
              { label: 'Drawdown Histórico', value: `${resultado.drawdown_historico_pts?.toFixed(0)} pts` },
            ].map(item => (
              <div key={item.label} className="card" style={{ padding: '14px 16px' }}>
                <div style={{ fontSize: 11, color: 'var(--text2)', marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: item.color || 'var(--text)' }}>{item.value}</div>
              </div>
            ))}
          </div>

          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600 }}>Probabilidade de Ruin</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--text2)' }}>P(drawdown &gt;</span>
                <input type="number" value={thresholdRuin} onChange={e => setThresholdRuin(Number(e.target.value))}
                  style={{ width: 80 }} />
                <span style={{ fontSize: 12, color: 'var(--text2)' }}>pts) =</span>
                <strong style={{ color: Number(pRuin) > 20 ? 'var(--red)' : 'var(--green)', fontSize: 18 }}>{pRuin}%</strong>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Banda de Confiança — Equity Curve</div>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={bandaData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="trade" tick={{ fontSize: 10, fill: 'var(--text2)' }} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--text2)' }} />
                  <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6 }} />
                  <ReferenceLine y={0} stroke="var(--border)" />
                  <Area type="monotone" dataKey="p90" stroke="none" fill="var(--blue)" fillOpacity={0.15} />
                  <Area type="monotone" dataKey="p10" stroke="none" fill="var(--bg)" fillOpacity={1} />
                  <Area type="monotone" dataKey="p50" stroke="var(--blue)" strokeWidth={2} fill="none" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
              <div style={{ fontSize: 11, color: 'var(--text2)', marginTop: 8, textAlign: 'center' }}>
                Área = P10–P90 | Linha = Mediana (P50)
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Distribuição de Drawdown Máximo</div>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={histDDData()} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="bin" tick={{ fontSize: 10, fill: 'var(--text2)' }} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--text2)' }} />
                  <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6 }} />
                  {pct && [
                    { val: pct.p50, color: 'var(--blue)', label: 'P50' },
                    { val: pct.p90, color: 'var(--yellow)', label: 'P90' },
                    { val: pct.p95, color: 'var(--red)', label: 'P95' },
                  ].map(l => <ReferenceLine key={l.label} x={Math.round(l.val / 50) * 50} stroke={l.color} strokeDasharray="4 2" label={{ value: l.label, fill: l.color, fontSize: 10 }} />)}
                  <Bar dataKey="contagem" fill="var(--blue)" fillOpacity={0.6} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
