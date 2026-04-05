import { useState, useEffect } from 'react'
import {
  LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine,
} from 'recharts'
import api from '../api.js'

const DISCLAIMER =
  'Este modelo é um filtro estatístico baseado em padrões históricos. ' +
  'Desempenho passado não garante resultados futuros.'

const card = {
  background: 'var(--bg2)',
  border: '1px solid var(--border)',
  borderRadius: 'var(--radius)',
  padding: '16px 20px',
}

const metricaItem = (label, valor, cor) => (
  <div key={label} style={{ ...card, textAlign: 'center' }}>
    <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 22, fontWeight: 700, color: cor || 'var(--text)' }}>
      {valor ?? '—'}
    </div>
  </div>
)

export default function CNNPadroes() {
  const [runs, setRuns] = useState([])
  const [modelos, setModelos] = useState([])
  const [form, setForm] = useState({
    ticker: 'WIN',
    timeframe: '5min',
    nome: '',
    run_id: '',
    periodo_inicio: '',
    periodo_fim: '',
    seq_len: 50,
    epochs: 50,
    patience: 10,
  })
  const [resumo, setResumo] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)
  const [abaAtiva, setAbaAtiva] = useState('treinar')

  useEffect(() => {
    carregarDados()
  }, [])

  async function carregarDados() {
    try {
      const [runsRes, modelosRes] = await Promise.all([
        api.get('/backtesting/runs/list').catch(() => ({ data: [] })),
        api.get('/cnn/modelos'),
      ])
      setModelos(modelosRes.data)
    } catch (_) {}

    // Carrega runs disponíveis para labeling
    try {
      const r = await api.get('/backtesting/comparativo', {
        params: { setup_ids: '0', periodo_inicio: '2020-01-01', periodo_fim: '2099-01-01' },
      }).catch(() => ({ data: [] }))
    } catch (_) {}

    // Lista runs pelo banco
    try {
      const conn = await api.get('/ingestao/disponivel')
    } catch (_) {}
  }

  async function carregarResumo() {
    if (!form.ticker || !form.timeframe) return
    try {
      const r = await api.get('/cnn/rotulos/resumo', {
        params: { ticker: form.ticker, timeframe: form.timeframe },
      })
      setResumo(r.data)
    } catch (_) {
      setResumo(null)
    }
  }

  async function rotularRun(e) {
    e.preventDefault()
    if (!form.run_id) return setErro('Informe um run_id para rotular.')
    setErro(null)
    setCarregando(true)
    try {
      const r = await api.post(`/cnn/rotular/run/${form.run_id}`)
      setResumo({
        ticker: r.data.ticker,
        timeframe: r.data.timeframe,
        total: r.data.total_trades,
        positivos: r.data.positivos,
        negativos: r.data.negativos,
      })
      await carregarResumo()
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  async function treinar(e) {
    e.preventDefault()
    setErro(null)
    setResultado(null)
    setCarregando(true)
    try {
      const payload = {
        ticker: form.ticker,
        timeframe: form.timeframe,
        nome: form.nome || `${form.ticker}/${form.timeframe} — ${new Date().toLocaleDateString('pt-BR')}`,
        seq_len: Number(form.seq_len),
        epochs: Number(form.epochs),
        patience: Number(form.patience),
      }
      if (form.run_id) payload.run_id = Number(form.run_id)
      if (form.periodo_inicio) payload.periodo_inicio = form.periodo_inicio
      if (form.periodo_fim) payload.periodo_fim = form.periodo_fim

      const r = await api.post('/cnn/treinar', payload)
      setResultado(r.data)
      // Atualiza lista de modelos
      const m = await api.get('/cnn/modelos')
      setModelos(m.data)
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  const f = (v) => typeof v === 'number' ? v.toFixed(3) : v

  const historicoParaGrafico = resultado?.historico_loss?.map(h => ({
    epoca: h.epoca,
    Treino: h.treino,
    Val: h.val,
  })) ?? []

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>CNN — Reconhecimento de Padrões</h1>
      <p style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 24 }}>{DISCLAIMER}</p>

      {/* Abas */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24 }}>
        {[['treinar', 'Treinar Modelo'], ['modelos', 'Modelos Treinados']].map(([id, label]) => (
          <button
            key={id}
            onClick={() => setAbaAtiva(id)}
            style={{
              padding: '6px 16px',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--border)',
              background: abaAtiva === id ? 'var(--blue)' : 'var(--bg2)',
              color: abaAtiva === id ? '#fff' : 'var(--text)',
              cursor: 'pointer',
              fontSize: 14,
              fontWeight: abaAtiva === id ? 600 : 400,
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* === ABA: Treinar === */}
      {abaAtiva === 'treinar' && (
        <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 24, alignItems: 'start' }}>
          {/* Formulário */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Rotulagem automática */}
            <div style={card}>
              <div style={{ fontWeight: 600, marginBottom: 12 }}>1. Gerar Rótulos do Backtest</div>
              <form onSubmit={rotularRun} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <label style={{ fontSize: 13 }}>
                  Run ID do Backtest
                  <input
                    type="number"
                    value={form.run_id}
                    onChange={e => setForm(f => ({ ...f, run_id: e.target.value }))}
                    placeholder="ex: 12"
                    style={{ display: 'block', width: '100%', marginTop: 4, padding: '6px 8px',
                      background: 'var(--bg)', border: '1px solid var(--border)',
                      borderRadius: 4, color: 'var(--text)', fontSize: 13 }}
                  />
                </label>
                <button
                  type="submit"
                  disabled={carregando || !form.run_id}
                  style={{ padding: '7px 0', background: 'var(--blue)', color: '#fff',
                    border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 13 }}
                >
                  Importar Trades como Rótulos
                </button>
              </form>
            </div>

            {/* Resumo de rótulos */}
            {resumo && (
              <div style={{ ...card, borderColor: resumo.positivos < 200 ? 'var(--yellow)' : 'var(--border)' }}>
                <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 13 }}>Rótulos disponíveis</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  {metricaItem('Total', resumo.total)}
                  {metricaItem('Positivos (1)', resumo.positivos, 'var(--green)')}
                  {metricaItem('Negativos (0)', resumo.negativos, 'var(--red)')}
                </div>
                {resumo.positivos < 200 && (
                  <div style={{ marginTop: 10, fontSize: 12, color: 'var(--yellow)' }}>
                    ⚠ Menos de 200 positivos. O modelo pode não generalizar.
                  </div>
                )}
              </div>
            )}

            {/* Configuração de treino */}
            <div style={card}>
              <div style={{ fontWeight: 600, marginBottom: 12 }}>2. Configurar Treino</div>
              <form onSubmit={treinar} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  ['Ticker', 'ticker', 'text', 'WIN'],
                  ['Timeframe', 'timeframe', 'text', '5min'],
                  ['Nome do Modelo', 'nome', 'text', 'WIN 5min — Setup X'],
                  ['Período Início (opcional)', 'periodo_inicio', 'date', ''],
                  ['Período Fim (opcional)', 'periodo_fim', 'date', ''],
                  ['Janela (seq_len)', 'seq_len', 'number', '50'],
                  ['Épocas máx.', 'epochs', 'number', '50'],
                  ['Early Stop (patience)', 'patience', 'number', '10'],
                ].map(([label, key, type, ph]) => (
                  <label key={key} style={{ fontSize: 13 }}>
                    {label}
                    <input
                      type={type}
                      value={form[key]}
                      onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                      placeholder={ph}
                      style={{ display: 'block', width: '100%', marginTop: 4, padding: '6px 8px',
                        background: 'var(--bg)', border: '1px solid var(--border)',
                        borderRadius: 4, color: 'var(--text)', fontSize: 13 }}
                    />
                  </label>
                ))}

                <button
                  type="submit"
                  disabled={carregando}
                  style={{ marginTop: 4, padding: '8px 0', background: 'var(--blue)', color: '#fff',
                    border: 'none', borderRadius: 4, cursor: 'pointer', fontWeight: 600 }}
                >
                  {carregando ? 'Treinando…' : 'Treinar Modelo'}
                </button>
              </form>
            </div>
          </div>

          {/* Resultados */}
          <div>
            {erro && (
              <div style={{ ...card, borderColor: 'var(--red)', color: 'var(--red)', marginBottom: 16 }}>
                {erro}
              </div>
            )}

            {resultado && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {resultado.avisos?.length > 0 && (
                  <div style={{ ...card, borderColor: 'var(--yellow)' }}>
                    <div style={{ fontWeight: 600, color: 'var(--yellow)', marginBottom: 8 }}>⚠ Avisos</div>
                    {resultado.avisos.map((a, i) => (
                      <p key={i} style={{ fontSize: 13, color: 'var(--text2)', margin: '4px 0' }}>{a}</p>
                    ))}
                  </div>
                )}

                {/* Métricas */}
                {['treino', 'val', 'teste'].map(conjunto => (
                  <div key={conjunto}>
                    <div style={{ fontWeight: 600, marginBottom: 10, textTransform: 'capitalize' }}>
                      {conjunto === 'val' ? 'Validação' : conjunto === 'teste' ? 'Teste (out-of-sample)' : 'Treino'}
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                      {metricaItem('Precision', f(resultado[`metricas_${conjunto}`]?.precision))}
                      {metricaItem('Recall', f(resultado[`metricas_${conjunto}`]?.recall))}
                      {metricaItem('F1', f(resultado[`metricas_${conjunto}`]?.f1), 'var(--blue)')}
                      {metricaItem('Loss', f(resultado[`metricas_${conjunto}`]?.loss))}
                    </div>
                  </div>
                ))}

                {/* Loss curve */}
                {historicoParaGrafico.length > 0 && (
                  <div style={card}>
                    <div style={{ fontWeight: 600, marginBottom: 16 }}>Curva de Loss por Época</div>
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={historicoParaGrafico}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                        <XAxis dataKey="epoca" tick={{ fontSize: 11 }} label={{ value: 'Época', position: 'insideBottom', offset: -2 }} />
                        <YAxis tick={{ fontSize: 11 }} width={55} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="Treino" stroke="var(--blue)" dot={false} strokeWidth={2} />
                        <Line type="monotone" dataKey="Val" stroke="var(--yellow)" dot={false} strokeWidth={2} strokeDasharray="5 5" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Model ID */}
                <div style={{ ...card, fontSize: 12, color: 'var(--text2)' }}>
                  <span style={{ fontWeight: 600 }}>Model ID: </span>{resultado.model_id}
                  <br />
                  <span style={{ fontWeight: 600 }}>Épocas executadas: </span>{resultado.epochs_executadas}
                  {' · '}
                  <span style={{ fontWeight: 600 }}>Amostras: </span>{resultado.n_amostras}
                  {' ('}+{resultado.n_positivos} / -{resultado.n_negativos}{')'}
                </div>
              </div>
            )}

            {!resultado && !erro && (
              <div style={{ ...card, color: 'var(--text2)', fontSize: 13, textAlign: 'center', padding: 40 }}>
                Configure e execute o treino para ver os resultados aqui.
              </div>
            )}
          </div>
        </div>
      )}

      {/* === ABA: Modelos Treinados === */}
      {abaAtiva === 'modelos' && (
        <div>
          {modelos.length === 0 ? (
            <div style={{ ...card, color: 'var(--text2)', fontSize: 13, textAlign: 'center', padding: 40 }}>
              Nenhum modelo treinado ainda.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {modelos.map(m => (
                <div key={m.id} style={{ ...card, display: 'grid', gridTemplateColumns: '1fr auto', alignItems: 'center', gap: 16 }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{m.nome}</div>
                    <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 2 }}>
                      {m.ticker} · {m.timeframe} · seq_len={m.seq_len} · criado {new Date(m.criado_em).toLocaleDateString('pt-BR')}
                    </div>
                    {m.metricas_val && (
                      <div style={{ fontSize: 12, marginTop: 6, display: 'flex', gap: 16 }}>
                        <span>Val F1: <strong>{f(m.metricas_val.f1)}</strong></span>
                        <span>Precision: <strong>{f(m.metricas_val.precision)}</strong></span>
                        <span>Recall: <strong>{f(m.metricas_val.recall)}</strong></span>
                      </div>
                    )}
                    {m.metricas_teste && (
                      <div style={{ fontSize: 12, marginTop: 4, display: 'flex', gap: 16, color: 'var(--text2)' }}>
                        <span>Teste F1: <strong style={{ color: 'var(--text)' }}>{f(m.metricas_teste.f1)}</strong></span>
                        <span>Precision: <strong style={{ color: 'var(--text)' }}>{f(m.metricas_teste.precision)}</strong></span>
                      </div>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text2)', fontFamily: 'monospace', maxWidth: 260, wordBreak: 'break-all' }}>
                    {m.id}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
