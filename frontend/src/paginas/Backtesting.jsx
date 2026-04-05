import { useState, useEffect } from 'react'
import api from '../api.js'
import MetricasGlobais from '../componentes/MetricasGlobais.jsx'
import EquityCurve from '../componentes/EquityCurve.jsx'
import Histograma from '../componentes/Histograma.jsx'
import TabelaOperacoes from '../componentes/TabelaOperacoes.jsx'

const TABS_SEG = ['tendencia_semanal', 'periodo_dia', 'gap_abertura_tipo', 'range_acumulado_faixa', 'variacao_dia_faixa']
const LABEL_SEG = {
  tendencia_semanal: 'Tendência Semanal',
  periodo_dia: 'Período do Dia',
  gap_abertura_tipo: 'Gap de Abertura',
  range_acumulado_faixa: 'Range Acumulado',
  variacao_dia_faixa: 'Variação do Dia',
}

export default function Backtesting() {
  const [setups, setSetups] = useState([])
  const [form, setForm] = useState({ setup_id: '', periodo_inicio: '', periodo_fim: '', sample_type: 'in_sample' })
  const [carregando, setCarregando] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState(null)
  const [tabSeg, setTabSeg] = useState('tendencia_semanal')
  const [usarCNN, setUsarCNN] = useState(false)
  const [modelosCNN, setModelosCNN] = useState([])
  const [cnnModeloId, setCnnModeloId] = useState('')
  const [cnnThreshold, setCnnThreshold] = useState(0.5)
  const [contratos, setContratos] = useState(1)

  useEffect(() => {
    api.get('/setups').then(r => setSetups(r.data)).catch(() => {})
    api.get('/cnn/modelos').then(r => setModelosCNN(r.data)).catch(() => {})
  }, [])

  function campo(key) {
    return { value: form[key], onChange: e => setForm(f => ({ ...f, [key]: e.target.value })) }
  }

  async function executar(e) {
    e.preventDefault(); setErro(null); setCarregando(true)
    try {
      const payload = {
        setup_id: Number(form.setup_id),
        periodo_inicio: form.periodo_inicio,
        periodo_fim: form.periodo_fim,
        sample_type: form.sample_type,
      }
      if (usarCNN && cnnModeloId) {
        payload.cnn_modelo_id = cnnModeloId
        payload.cnn_threshold = cnnThreshold
      }
      const r = await api.post('/backtesting/executar', payload)
      setResultado(r.data)
    } catch (err) { setErro(err.message) }
    finally { setCarregando(false) }
  }

  async function aprovar() {
    if (!resultado) return
    await api.put(`/setups/${form.setup_id}/aprovar?run_id=${resultado.run_id}`)
    alert('Run in-sample aprovado. Você pode agora testar out-of-sample.')
  }

  const VALOR_PT = { WIN: 0.20, WDO: 10.00, BITFUT: 1.00 }
  const setupSelecionado = setups.find(s => String(s.id) === String(form.setup_id))
  const valorPtBase = VALOR_PT[setupSelecionado?.ticker] ?? 0.20
  const valorPtTotal = valorPtBase * contratos

  const stats = resultado?.stats
  const seg = stats?.segmentacao?.[tabSeg]

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Backtesting</h1>

      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={executar}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: 12 }}>
            <div>
              <label>Setup</label>
              <select required {...campo('setup_id')}>
                <option value="">Selecione...</option>
                {setups.map(s => <option key={s.id} value={s.id}>{s.nome} ({s.ticker})</option>)}
              </select>
            </div>
            <div><label>Início</label><input type="date" required {...campo('periodo_inicio')} /></div>
            <div><label>Fim</label><input type="date" required {...campo('periodo_fim')} /></div>
            <div>
              <label>Amostra</label>
              <select {...campo('sample_type')}>
                <option value="in_sample">In-Sample</option>
                <option value="out_of_sample">Out-of-Sample</option>
              </select>
            </div>
          </div>
          {/* Filtro CNN */}
          <div style={{ marginTop: 16, padding: '12px 16px', background: 'var(--bg2)',
            border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13 }}>
              <input
                type="checkbox"
                checked={usarCNN}
                onChange={e => setUsarCNN(e.target.checked)}
              />
              <span style={{ fontWeight: 600 }}>Usar filtro CNN</span>
              <span style={{ color: 'var(--text2)', fontWeight: 400 }}>— só executa trades confirmados pelo modelo</span>
            </label>
            {usarCNN && (
              <div style={{ marginTop: 12, display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 12, alignItems: 'end' }}>
                <div>
                  <label style={{ fontSize: 12 }}>Modelo CNN</label>
                  <select
                    value={cnnModeloId}
                    onChange={e => setCnnModeloId(e.target.value)}
                    style={{ display: 'block', width: '100%', marginTop: 4 }}
                  >
                    <option value="">Selecione um modelo...</option>
                    {modelosCNN.map(m => (
                      <option key={m.id} value={m.id}>
                        {m.nome} — {m.ticker}/{m.timeframe} (F1 val: {m.metricas_val?.f1?.toFixed(2) ?? '?'})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: 12 }}>Threshold: <strong>{cnnThreshold.toFixed(2)}</strong></label>
                  <input
                    type="range"
                    min="0.1" max="0.9" step="0.05"
                    value={cnnThreshold}
                    onChange={e => setCnnThreshold(Number(e.target.value))}
                    style={{ display: 'block', width: '100%', marginTop: 8 }}
                  />
                </div>
                {modelosCNN.length === 0 && (
                  <p style={{ fontSize: 12, color: 'var(--text2)', gridColumn: '1 / -1', margin: 0 }}>
                    Nenhum modelo treinado. Treine um na página CNN.
                  </p>
                )}
              </div>
            )}
          </div>

          <div style={{ marginTop: 16, display: 'flex', gap: 8 }}>
            <button type="submit" disabled={carregando}>
              {carregando ? <><span className="spinner" style={{ marginRight: 8 }} />Executando...</> : 'Executar Backtest'}
            </button>
            {resultado && form.sample_type === 'in_sample' && (
              <button type="button" className="secundario" onClick={aprovar}>Aprovar Run In-Sample</button>
            )}
          </div>
        </form>
        {erro && <div className="erro-msg" style={{ marginTop: 12 }}>{erro}</div>}
      </div>

      {resultado && stats && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Simulador de contratos */}
          <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 24, padding: '14px 20px' }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)', whiteSpace: 'nowrap' }}>
              Simulação de contratos
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <button className="secundario" style={{ padding: '4px 12px', fontSize: 16, lineHeight: 1 }}
                onClick={() => setContratos(c => Math.max(1, c - 1))}>−</button>
              <input
                type="number" min="1" max="500" value={contratos}
                onChange={e => setContratos(Math.max(1, Number(e.target.value) || 1))}
                style={{ width: 64, textAlign: 'center', padding: '6px 8px', fontSize: 15, fontWeight: 700 }}
              />
              <button className="secundario" style={{ padding: '4px 12px', fontSize: 16, lineHeight: 1 }}
                onClick={() => setContratos(c => c + 1)}>+</button>
            </div>
            <div style={{ fontSize: 13, color: 'var(--text2)' }}>
              {contratos} contrato{contratos > 1 ? 's' : ''} ×{' '}
              <span style={{ color: 'var(--text)' }}>
                R$ {valorPtBase.toFixed(2).replace('.', ',')}/pt
              </span>
              {' '}={' '}
              <span style={{ color: 'var(--blue)', fontWeight: 700 }}>
                R$ {valorPtTotal.toFixed(2).replace('.', ',')}/pt
              </span>
            </div>
          </div>

          <MetricasGlobais stats={stats} contratos={contratos} valorPtBase={valorPtBase} />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div className="card"><EquityCurve equity_curve={stats.equity_curve} /></div>
            <div className="card"><Histograma histograma={stats.histograma} /></div>
          </div>

          <div className="card">
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 16 }}>Segmentação por Contexto</div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
              {TABS_SEG.map(t => (
                <button key={t} className={tabSeg === t ? '' : 'secundario'} style={{ padding: '6px 14px', fontSize: 12 }} onClick={() => setTabSeg(t)}>
                  {LABEL_SEG[t]}
                </button>
              ))}
            </div>
            {seg && Object.keys(seg).length > 0 ? (
              <table>
                <thead><tr><th>Contexto</th><th>Trades</th><th>Win Rate</th><th>Expectância</th><th>P&L Total</th></tr></thead>
                <tbody>
                  {Object.entries(seg).map(([k, v]) => (
                    <tr key={k}>
                      <td><strong>{k}</strong></td>
                      <td>{v.total_trades}</td>
                      <td style={{ color: v.win_rate >= 50 ? 'var(--green)' : 'var(--red)' }}>{v.win_rate}%</td>
                      <td style={{ color: v.expectancia_pts > 0 ? 'var(--green)' : 'var(--red)' }}>{v.expectancia_pts} pts</td>
                      <td style={{ color: v.total_pts > 0 ? 'var(--green)' : 'var(--red)' }}>{v.total_pts} pts</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p style={{ color: 'var(--text2)' }}>Sem dados para este contexto.</p>
            )}
          </div>

          <div className="card">
            <TabelaOperacoes trades={resultado.trades} />
          </div>
        </div>
      )}
    </div>
  )
}
