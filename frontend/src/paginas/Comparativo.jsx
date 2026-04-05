import { useState, useEffect } from 'react'
import api from '../api.js'

const METRICAS = ['win_rate','expectancia_pts','total_pts','fator_lucro','max_drawdown_pts']
const LABEL = { win_rate: 'Win Rate (%)', expectancia_pts: 'Expectância (pts)', total_pts: 'P&L Total (pts)', fator_lucro: 'Fator de Lucro', max_drawdown_pts: 'Drawdown Máx (pts)' }

function melhorIdx(dados, metrica) {
  if (dados.length === 0) return -1
  const vals = dados.map(d => d[metrica] ?? -Infinity)
  const f = metrica === 'max_drawdown_pts' ? Math.min : Math.max
  const best = f(...vals)
  return vals.indexOf(best)
}

export default function Comparativo() {
  const [setups, setSetups] = useState([])
  const [selecionados, setSelecionados] = useState([])
  const [form, setForm] = useState({ periodo_inicio: '', periodo_fim: '', sample_type: 'in_sample' })
  const [dados, setDados] = useState([])
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)

  useEffect(() => { api.get('/setups').then(r => setSetups(r.data)).catch(() => {}) }, [])

  function toggleSetup(id) {
    setSelecionados(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  }

  async function comparar(e) {
    e.preventDefault(); setErro(null); setCarregando(true)
    try {
      const r = await api.get('/backtesting/comparativo', {
        params: { setup_ids: selecionados.join(','), periodo_inicio: form.periodo_inicio, periodo_fim: form.periodo_fim, sample_type: form.sample_type }
      })
      setDados(r.data)
    } catch (err) { setErro(err.message) }
    finally { setCarregando(false) }
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Comparativo de Setups</h1>

      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={comparar}>
          <div style={{ marginBottom: 12, fontSize: 13, fontWeight: 600 }}>Selecionar Setups</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
            {setups.map(s => (
              <button key={s.id} type="button"
                className={selecionados.includes(s.id) ? '' : 'secundario'}
                style={{ padding: '6px 14px', fontSize: 13 }}
                onClick={() => toggleSetup(s.id)}>
                {s.nome}
              </button>
            ))}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
            <div><label>Início</label><input type="date" required value={form.periodo_inicio} onChange={e => setForm(f => ({ ...f, periodo_inicio: e.target.value }))} /></div>
            <div><label>Fim</label><input type="date" required value={form.periodo_fim} onChange={e => setForm(f => ({ ...f, periodo_fim: e.target.value }))} /></div>
            <div><label>Amostra</label>
              <select value={form.sample_type} onChange={e => setForm(f => ({ ...f, sample_type: e.target.value }))}>
                <option value="in_sample">In-Sample</option>
                <option value="out_of_sample">Out-of-Sample</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop: 16 }}>
            <button type="submit" disabled={selecionados.length < 2 || carregando}>Comparar</button>
          </div>
        </form>
        {selecionados.length < 2 && <p style={{ color: 'var(--text2)', marginTop: 8, fontSize: 12 }}>Selecione ao menos 2 setups.</p>}
        {erro && <div className="erro-msg" style={{ marginTop: 12 }}>{erro}</div>}
      </div>

      {dados.length > 0 && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Setup</th>
                <th>Trades</th>
                {METRICAS.map(m => <th key={m}>{LABEL[m]}</th>)}
              </tr>
            </thead>
            <tbody>
              {dados.map((d, i) => (
                <tr key={i}>
                  <td><strong>{d.nome}</strong></td>
                  <td>{d.total_trades}</td>
                  {METRICAS.map(m => {
                    const isBest = melhorIdx(dados, m) === i
                    const val = d[m]
                    const negativo = m === 'max_drawdown_pts'
                    return (
                      <td key={m} style={{
                        fontWeight: isBest ? 700 : 400,
                        color: isBest ? (negativo ? 'var(--red)' : 'var(--green)') : 'var(--text)',
                        background: isBest ? (negativo ? 'rgba(231,76,94,0.08)' : 'rgba(38,194,129,0.08)') : 'transparent',
                      }}>
                        {val != null ? (m === 'win_rate' ? `${val}%` : val) : '—'}
                        {isBest && ' ★'}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
