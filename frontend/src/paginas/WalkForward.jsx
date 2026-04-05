import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts'
import api from '../api.js'

export default function WalkForward() {
  const [setups, setSetups] = useState([])
  const [form, setForm] = useState({ setup_id: '', periodo_inicio: '', periodo_fim: '', janela_otim_meses: 6, janela_valid_meses: 1, step_meses: 1 })
  const [carregando, setCarregando] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState(null)

  useEffect(() => { api.get('/setups').then(r => setSetups(r.data)).catch(() => {}) }, [])

  function campo(key) {
    return { value: form[key], onChange: e => setForm(f => ({ ...f, [key]: e.target.value })) }
  }

  async function executar(e) {
    e.preventDefault(); setErro(null); setCarregando(true)
    try {
      const r = await api.post('/walk-forward/executar', {
        setup_id: Number(form.setup_id),
        periodo_inicio: form.periodo_inicio,
        periodo_fim: form.periodo_fim,
        janela_otim_meses: Number(form.janela_otim_meses),
        janela_valid_meses: Number(form.janela_valid_meses),
        step_meses: Number(form.step_meses),
      })
      setResultado(r.data)
    } catch (err) { setErro(err.message) }
    finally { setCarregando(false) }
  }

  const chartData = resultado?.janelas?.map(j => ({
    label: `J${j.janela_num}`,
    'In-Sample': j.expectancia_in,
    'Out-of-Sample': j.expectancia_out,
  })) || []

  const ef = resultado?.eficiencia
  const cons = resultado?.consistencia

  const diagnostico = () => {
    if (!ef && !cons) return null
    if (ef >= 0.6 && cons >= 0.6) return { msg: 'Setup robusto', cor: 'var(--green)' }
    if (ef >= 0.3 && cons >= 0.5) return { msg: 'Funcional — monitorar', cor: 'var(--yellow)' }
    if (ef < 0.3) return { msg: 'Sinal de overfitting', cor: 'var(--red)' }
    return { msg: 'Dependente de regime', cor: 'var(--yellow)' }
  }
  const diag = diagnostico()

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Walk-Forward Analysis</h1>

      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={executar}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            <div>
              <label>Setup</label>
              <select required {...campo('setup_id')}>
                <option value="">Selecione...</option>
                {setups.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
              </select>
            </div>
            <div><label>Início</label><input type="date" required {...campo('periodo_inicio')} /></div>
            <div><label>Fim</label><input type="date" required {...campo('periodo_fim')} /></div>
            <div><label>Janela Otimização (meses)</label><input type="number" min="1" {...campo('janela_otim_meses')} /></div>
            <div><label>Janela Validação (meses)</label><input type="number" min="1" {...campo('janela_valid_meses')} /></div>
            <div><label>Step (meses)</label><input type="number" min="1" {...campo('step_meses')} /></div>
          </div>
          <div style={{ marginTop: 16 }}>
            <button type="submit" disabled={carregando}>
              {carregando ? <><span className="spinner" style={{ marginRight: 8 }} />Executando...</> : 'Executar Walk-Forward'}
            </button>
          </div>
        </form>
        {erro && <div className="erro-msg" style={{ marginTop: 12 }}>{erro}</div>}
      </div>

      {resultado && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
            {[
              { label: 'Total Janelas', value: resultado.total_janelas },
              { label: 'Janelas Positivas', value: resultado.janelas_positivas, color: 'var(--green)' },
              { label: 'Eficiência', value: ef != null ? ef.toFixed(2) : '—', color: ef >= 0.6 ? 'var(--green)' : ef >= 0.3 ? 'var(--yellow)' : 'var(--red)' },
              { label: 'Consistência', value: cons != null ? `${(cons * 100).toFixed(0)}%` : '—', color: cons >= 0.6 ? 'var(--green)' : cons >= 0.5 ? 'var(--yellow)' : 'var(--red)' },
            ].map(item => (
              <div key={item.label} className="card" style={{ padding: '14px 16px' }}>
                <div style={{ fontSize: 11, color: 'var(--text2)', marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 22, fontWeight: 700, color: item.color || 'var(--text)' }}>{item.value}</div>
              </div>
            ))}
          </div>

          {diag && (
            <div style={{ padding: '12px 16px', borderRadius: 'var(--radius)', border: `1px solid ${diag.cor}`, background: `${diag.cor}15`, color: diag.cor, fontWeight: 600 }}>
              Diagnóstico: {diag.msg}
            </div>
          )}

          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Expectância por Janela — In-Sample vs Out-of-Sample</div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="label" tick={{ fontSize: 11, fill: 'var(--text2)' }} />
                <YAxis tick={{ fontSize: 11, fill: 'var(--text2)' }} />
                <Tooltip contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <ReferenceLine y={0} stroke="var(--border)" />
                <Bar dataKey="In-Sample" fill="var(--blue)" fillOpacity={0.6} />
                <Bar dataKey="Out-of-Sample" fill="var(--green)" fillOpacity={0.8} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Detalhe por Janela</div>
            <table>
              <thead>
                <tr><th>#</th><th>Otim</th><th>Valid</th><th>Trades In</th><th>Exp. In</th><th>Trades Out</th><th>Exp. Out</th><th>Degradação</th></tr>
              </thead>
              <tbody>
                {resultado.janelas?.map(j => {
                  const deg = j.expectancia_in > 0 ? ((j.expectancia_out / j.expectancia_in) * 100).toFixed(0) : '—'
                  return (
                    <tr key={j.janela_num}>
                      <td>{j.janela_num}</td>
                      <td style={{ fontSize: 12, color: 'var(--text2)' }}>{j.otim_inicio} → {j.otim_fim}</td>
                      <td style={{ fontSize: 12, color: 'var(--text2)' }}>{j.valid_inicio} → {j.valid_fim}</td>
                      <td>{j.total_trades_in}</td>
                      <td style={{ color: j.expectancia_in > 0 ? 'var(--green)' : 'var(--red)' }}>{j.expectancia_in?.toFixed(1)}</td>
                      <td>{j.total_trades_out}
                        {j.total_trades_out < 10 && <span title="Poucos trades" style={{ color: 'var(--yellow)', marginLeft: 4 }}>⚠</span>}
                      </td>
                      <td style={{ color: j.expectancia_out > 0 ? 'var(--green)' : 'var(--red)' }}>{j.expectancia_out?.toFixed(1)}</td>
                      <td style={{ color: 'var(--text2)', fontSize: 12 }}>{deg !== '—' ? `${deg}%` : '—'}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
