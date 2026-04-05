import { useState, useEffect } from 'react'
import api from '../api.js'
import MetricasGlobais from '../componentes/MetricasGlobais.jsx'
import EquityCurve from '../componentes/EquityCurve.jsx'
import TabelaOperacoes from '../componentes/TabelaOperacoes.jsx'

export default function Historico() {
  const [setups, setSetups] = useState([])
  const [runs, setRuns] = useState([])
  const [filtroSetup, setFiltroSetup] = useState('')
  const [filtroTipo, setFiltroTipo] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [detalhe, setDetalhe] = useState(null)      // run_id expandido
  const [detalheData, setDetalheData] = useState(null)
  const [carregandoDetalhe, setCarregandoDetalhe] = useState(false)
  const [aprovandoId, setAprovandoId] = useState(null)
  const [apagandoId, setApagandoId] = useState(null)
  const [erro, setErro] = useState(null)

  useEffect(() => {
    api.get('/setups').then(r => setSetups(r.data)).catch(() => {})
    carregar()
  }, [])

  async function carregar() {
    setCarregando(true)
    try {
      const params = new URLSearchParams()
      if (filtroSetup) params.set('setup_id', filtroSetup)
      if (filtroTipo) params.set('sample_type', filtroTipo)
      const r = await api.get(`/backtesting/runs?${params}`)
      setRuns(r.data)
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  async function toggleDetalhe(run) {
    if (detalhe === run.run_id) {
      setDetalhe(null); setDetalheData(null)
      return
    }
    setDetalhe(run.run_id); setDetalheData(null); setCarregandoDetalhe(true)
    try {
      const r = await api.get(`/backtesting/runs/${run.run_id}`)
      setDetalheData(r.data)
    } catch {}
    finally { setCarregandoDetalhe(false) }
  }

  async function apagar(run) {
    if (!window.confirm(`Apagar run #${run.run_id} (${run.setup_nome})? Esta ação não pode ser desfeita.`)) return
    setApagandoId(run.run_id)
    try {
      await api.delete(`/backtesting/runs/${run.run_id}`)
      if (detalhe === run.run_id) { setDetalhe(null); setDetalheData(null) }
      await carregar()
    } catch (err) {
      setErro(err.response?.data?.detail || err.message)
    } finally {
      setApagandoId(null)
    }
  }

  async function aprovar(run) {
    setAprovandoId(run.run_id)
    try {
      await api.put(`/setups/${run.setup_id}/aprovar?run_id=${run.run_id}`)
      await carregar()
      // atualiza detalhe se estiver aberto
      if (detalhe === run.run_id && detalheData) {
        setDetalheData(d => ({ ...d, run: { ...d.run, aprovado: true } }))
      }
    } catch (err) {
      setErro(err.message)
    } finally {
      setAprovandoId(null)
    }
  }

  const pos = v => v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text)'

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Histórico de Backtests</h1>
      <p style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 24 }}>
        Todos os backtests executados. Clique numa linha para ver detalhes e aprovar runs IS.
      </p>

      {/* Filtros */}
      <div className="card" style={{ marginBottom: 20, display: 'flex', gap: 16, alignItems: 'flex-end', flexWrap: 'wrap' }}>
        <div>
          <label>Setup</label>
          <select value={filtroSetup} onChange={e => setFiltroSetup(e.target.value)} style={{ minWidth: 200 }}>
            <option value="">Todos</option>
            {setups.map(s => <option key={s.id} value={s.id}>{s.nome}</option>)}
          </select>
        </div>
        <div>
          <label>Tipo de Amostra</label>
          <select value={filtroTipo} onChange={e => setFiltroTipo(e.target.value)}>
            <option value="">Todos</option>
            <option value="in_sample">In-Sample</option>
            <option value="out_of_sample">Out-of-Sample</option>
          </select>
        </div>
        <button onClick={carregar} disabled={carregando}>
          {carregando ? <><span className="spinner" style={{ marginRight: 6 }} />Carregando...</> : 'Filtrar'}
        </button>
      </div>

      {erro && <div className="erro-msg" style={{ marginBottom: 16 }}>{erro}</div>}

      <div className="card" style={{ padding: 0 }}>
        {runs.length === 0 && !carregando ? (
          <p style={{ color: 'var(--text2)', padding: 24 }}>Nenhum backtest encontrado.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Setup</th>
                <th>Período</th>
                <th>Tipo</th>
                <th>Trades</th>
                <th>Win Rate</th>
                <th>Expectância</th>
                <th>Total pts</th>
                <th>Drawdown</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map(run => [
                <tr
                  key={run.run_id}
                  style={{ cursor: 'pointer', background: detalhe === run.run_id ? 'rgba(74,158,255,0.06)' : undefined }}
                  onClick={() => toggleDetalhe(run)}
                >
                  <td style={{ color: 'var(--text2)', fontSize: 12 }}>#{run.run_id}</td>
                  <td><strong>{run.setup_nome}</strong></td>
                  <td style={{ fontSize: 12, color: 'var(--text2)' }}>
                    {run.periodo_inicio} → {run.periodo_fim}
                  </td>
                  <td>
                    <span className="tag" style={{ background: run.sample_type === 'out_of_sample' ? 'rgba(255,170,0,0.15)' : undefined, color: run.sample_type === 'out_of_sample' ? 'var(--yellow, #ffaa00)' : undefined }}>
                      {run.sample_type === 'in_sample' ? 'IS' : 'OOS'}
                    </span>
                  </td>
                  <td>{run.total_trades ?? '—'}</td>
                  <td style={{ color: run.win_rate >= 50 ? 'var(--green)' : 'var(--red)' }}>
                    {run.win_rate != null ? `${run.win_rate}%` : '—'}
                  </td>
                  <td style={{ color: run.expectancia_pts != null ? pos(run.expectancia_pts) : undefined }}>
                    {run.expectancia_pts != null ? `${run.expectancia_pts} pts` : '—'}
                  </td>
                  <td style={{ color: run.total_pts != null ? pos(run.total_pts) : undefined }}>
                    {run.total_pts != null ? `${run.total_pts} pts` : '—'}
                  </td>
                  <td style={{ color: 'var(--red)' }}>
                    {run.max_drawdown_pts != null ? `${run.max_drawdown_pts} pts` : '—'}
                  </td>
                  <td>
                    {run.aprovado
                      ? <span style={{ color: 'var(--green)', fontSize: 12 }}>✓ Aprovado</span>
                      : run.sample_type === 'in_sample'
                        ? <span style={{ color: 'var(--text2)', fontSize: 12 }}>Pendente</span>
                        : <span style={{ color: 'var(--text2)', fontSize: 12 }}>—</span>
                    }
                  </td>
                  <td onClick={e => e.stopPropagation()} style={{ whiteSpace: 'nowrap', display: 'flex', gap: 6, alignItems: 'center' }}>
                    {run.sample_type === 'in_sample' && !run.aprovado && (
                      <button
                        className="secundario"
                        style={{ padding: '4px 10px', fontSize: 12 }}
                        disabled={aprovandoId === run.run_id}
                        onClick={() => aprovar(run)}
                      >
                        {aprovandoId === run.run_id ? '...' : 'Aprovar'}
                      </button>
                    )}
                    {!run.aprovado && (
                      <button
                        className="secundario"
                        style={{ padding: '4px 8px', fontSize: 13, color: 'var(--red)', borderColor: 'var(--red)' }}
                        disabled={apagandoId === run.run_id}
                        onClick={() => apagar(run)}
                        title="Apagar run"
                      >
                        {apagandoId === run.run_id ? '...' : '🗑'}
                      </button>
                    )}
                  </td>
                </tr>,

                detalhe === run.run_id && (
                  <tr key={`d-${run.run_id}`}>
                    <td colSpan={11} style={{ padding: '20px 24px', background: 'var(--bg3)', borderTop: '1px solid var(--border)' }}>
                      {carregandoDetalhe ? (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text2)' }}>
                          <span className="spinner" />Carregando detalhes...
                        </div>
                      ) : detalheData ? (
                        <DetalheRun data={detalheData} />
                      ) : null}
                    </td>
                  </tr>
                )
              ])}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}


function DetalheRun({ data }) {
  const { stats, trades } = data
  const [tabSeg, setTabSeg] = useState('tendencia_semanal')

  const TABS_SEG = ['tendencia_semanal', 'periodo_dia', 'gap_abertura_tipo', 'range_acumulado_faixa', 'variacao_dia_faixa']
  const LABEL_SEG = {
    tendencia_semanal: 'Tendência Semanal',
    periodo_dia: 'Período do Dia',
    gap_abertura_tipo: 'Gap de Abertura',
    range_acumulado_faixa: 'Range Acumulado',
    variacao_dia_faixa: 'Variação do Dia',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <MetricasGlobais stats={stats} />

      {trades.length > 0 && (
        <EquityCurve trades={trades} custo_por_ponto={0.20} />
      )}

      {stats?.segmentacao && (
        <div>
          <div style={{ display: 'flex', gap: 4, marginBottom: 12, flexWrap: 'wrap' }}>
            {TABS_SEG.map(t => (
              <button
                key={t}
                className={tabSeg === t ? '' : 'secundario'}
                style={{ padding: '5px 12px', fontSize: 12 }}
                onClick={() => setTabSeg(t)}
              >
                {LABEL_SEG[t]}
              </button>
            ))}
          </div>
          <SegmentacaoTabela dados={stats.segmentacao[tabSeg]} />
        </div>
      )}

      {trades.length > 0 && (
        <TabelaOperacoes trades={trades} />
      )}
    </div>
  )
}


function SegmentacaoTabela({ dados }) {
  if (!dados || Object.keys(dados).length === 0) {
    return <p style={{ color: 'var(--text2)', fontSize: 13 }}>Sem dados de segmentação.</p>
  }
  const pos = v => v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text)'
  return (
    <table>
      <thead>
        <tr>
          <th>Segmento</th>
          <th>Trades</th>
          <th>Win Rate</th>
          <th>Expectância</th>
          <th>Total pts</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(dados).map(([seg, m]) => (
          <tr key={seg}>
            <td>{seg}</td>
            <td>{m.total_trades}</td>
            <td style={{ color: m.win_rate >= 50 ? 'var(--green)' : 'var(--red)' }}>{m.win_rate}%</td>
            <td style={{ color: pos(m.expectancia_pts) }}>{m.expectancia_pts} pts</td>
            <td style={{ color: pos(m.total_pts) }}>{m.total_pts} pts</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
