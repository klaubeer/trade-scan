import { useState } from 'react'
import api from '../api.js'

export default function Agente() {
  const [descricao, setDescricao] = useState('')
  const [steps, setSteps] = useState([])
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState(null)
  const [runId, setRunId] = useState('')
  const [interpretacao, setInterpretacao] = useState(null)
  const [carregandoInterp, setCarregandoInterp] = useState(false)
  const [resultadoFinal, setResultadoFinal] = useState(null)   // { setup_id, run_id, setup }
  const [novoNome, setNovoNome] = useState('')
  const [nomeAtualizado, setNomeAtualizado] = useState(false)

  async function explorar(e) {
    e.preventDefault()
    setErro(null); setSteps([]); setCarregando(true)
    setResultadoFinal(null); setNovoNome(''); setNomeAtualizado(false)

    try {
      const response = await fetch('/api/agente/explorar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ descricao_natural: descricao }),
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.event === 'result') {
                setResultadoFinal(data)
              } else {
                setSteps(s => [...s, data])
                // captura setup do step formulate_setup para usar no rename
                if (data.no === 'formulate_setup' && data.setup) {
                  setResultadoFinal(prev => ({ ...prev, setup: data.setup }))
                }
              }
            } catch {}
          }
        }
      }
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  async function renomearSetup() {
    if (!resultadoFinal?.setup_id || !novoNome.trim()) return
    const params = { ...resultadoFinal.setup, nome: novoNome.trim() }
    try {
      await api.put(`/setups/${resultadoFinal.setup_id}`, params)
      setNomeAtualizado(true)
    } catch (err) {
      setErro(err.message)
    }
  }

  async function interpretar(e) {
    e.preventDefault()
    setCarregandoInterp(true); setInterpretacao(null)
    try {
      const r = await api.post('/agente/interpretar', { run_id: Number(runId) })
      setInterpretacao(r.data)
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregandoInterp(false)
    }
  }

  const NO_LABELS = {
    parse_intent: '🔍 Interpretando intenção',
    formulate_setup: '⚙️ Formulando setup',
    run_backtest: '📊 Executando backtest',
    interpret_results: '🧠 Analisando resultados',
    suggest_refinements: '💡 Sugerindo refinamentos',
    pedir_esclarecimento: '❓ Pedindo esclarecimento',
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>Agente IA</h1>
      <p style={{ color: 'var(--text2)', marginBottom: 24, fontSize: 13 }}>
        Descreva um setup em linguagem natural e o agente formulará os parâmetros, executará o backtest e interpretará os resultados.
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div className="card">
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Modo Exploração</div>
          <form onSubmit={explorar}>
            <label>Descreva seu setup</label>
            <textarea
              rows={4}
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              placeholder="Ex: quero testar compra quando o candle de 5min tem range acima de 40 pontos, preço acima da MM200, em tendência semanal de alta, stop de 30 pontos e alvo de 60 pontos"
              style={{ width: '100%', background: 'var(--bg3)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', color: 'var(--text)', padding: '10px 12px', fontFamily: 'var(--font)', fontSize: 14, resize: 'vertical', marginTop: 4 }}
            />
            <div style={{ marginTop: 12 }}>
              <button type="submit" disabled={!descricao.trim() || carregando}>
                {carregando ? <><span className="spinner" style={{ marginRight: 8 }} />Processando...</> : 'Explorar com IA'}
              </button>
            </div>
          </form>

          {steps.length > 0 && (
            <div style={{ marginTop: 20 }}>
              {steps.map((step, i) => (
                <div key={i} style={{ padding: '10px 14px', marginBottom: 8, background: 'var(--bg3)', borderRadius: 'var(--radius)', borderLeft: '3px solid var(--blue)' }}>
                  <div style={{ fontSize: 12, color: 'var(--blue)', fontWeight: 600, marginBottom: 4 }}>
                    {NO_LABELS[step.no] || step.no}
                    {step.status === 'concluido' && <span style={{ color: 'var(--green)', marginLeft: 8 }}>✓</span>}
                    {step.status === 'executando' && <span className="spinner" style={{ marginLeft: 8, width: 12, height: 12 }} />}
                  </div>
                  {step.resumo && <div style={{ fontSize: 13, color: 'var(--text)' }}>{step.resumo}</div>}
                  {step.interpretacao && (
                    <div style={{ fontSize: 13, color: 'var(--text)', lineHeight: 1.6, marginTop: 4 }}>{step.interpretacao}</div>
                  )}
                  {step.sugestoes && step.sugestoes.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <div style={{ fontSize: 11, color: 'var(--text2)', marginBottom: 4 }}>Sugestões de refinamento:</div>
                      {step.sugestoes.map((s, j) => (
                        <div key={j} style={{ fontSize: 12, color: 'var(--text2)', padding: '4px 8px', background: 'var(--bg2)', borderRadius: 4, marginBottom: 4 }}>
                          Stop: {s.stop_pts}pts | Alvo: {s.alvo_pts}pts
                          {s.mm200_posicao && ` | MM200: ${s.mm200_posicao}`}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          {resultadoFinal?.setup_id && (
            <div style={{ marginTop: 16, padding: '14px 16px', background: 'var(--bg3)',
              border: '1px solid var(--green)', borderRadius: 'var(--radius)' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--green)', marginBottom: 10 }}>
                ✓ Setup salvo — ID #{resultadoFinal.setup_id}
              </div>
              {nomeAtualizado ? (
                <div style={{ fontSize: 13, color: 'var(--text2)' }}>Nome atualizado para: <strong>{novoNome}</strong></div>
              ) : (
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <input
                    type="text"
                    value={novoNome}
                    onChange={e => setNovoNome(e.target.value)}
                    placeholder={`IA: ${descricao.slice(0, 35)}…`}
                    style={{ flex: 1, padding: '6px 10px', background: 'var(--bg)',
                      border: '1px solid var(--border)', borderRadius: 4,
                      color: 'var(--text)', fontSize: 13 }}
                  />
                  <button
                    className="secundario"
                    style={{ padding: '6px 14px', fontSize: 13, whiteSpace: 'nowrap' }}
                    onClick={renomearSetup}
                    disabled={!novoNome.trim()}
                  >
                    Renomear
                  </button>
                </div>
              )}
            </div>
          )}
          {erro && <div className="erro-msg" style={{ marginTop: 12 }}>{erro}</div>}
        </div>

        <div className="card">
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>Modo Interpretação</div>
          <p style={{ color: 'var(--text2)', fontSize: 13, marginBottom: 16 }}>
            Informe o ID de um backtest já executado para receber interpretação dos resultados e sugestões de melhoria.
          </p>
          <form onSubmit={interpretar}>
            <label>Run ID</label>
            <input type="number" min="1" value={runId} onChange={e => setRunId(e.target.value)} placeholder="Ex: 1" />
            <div style={{ marginTop: 12 }}>
              <button type="submit" disabled={!runId || carregandoInterp}>
                {carregandoInterp ? <><span className="spinner" style={{ marginRight: 8 }} />Analisando...</> : 'Interpretar Resultados'}
              </button>
            </div>
          </form>

          {interpretacao && (
            <div style={{ marginTop: 20 }}>
              <div style={{ fontSize: 13, lineHeight: 1.7, color: 'var(--text)', padding: '14px', background: 'var(--bg3)', borderRadius: 'var(--radius)', borderLeft: '3px solid var(--green)' }}>
                {interpretacao.interpretacao}
              </div>
              {interpretacao.sugestoes?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 8 }}>Variações sugeridas para testar:</div>
                  {interpretacao.sugestoes.map((s, i) => (
                    <div key={i} style={{ padding: '10px 14px', background: 'var(--bg3)', borderRadius: 'var(--radius)', marginBottom: 8, fontSize: 13 }}>
                      <strong>Variação {i + 1}:</strong> Stop {s.stop_pts}pts, Alvo {s.alvo_pts}pts
                      {s.mm200_posicao && `, MM200 ${s.mm200_posicao}`}
                      {s.tendencia_semanal && `, Tendência ${s.tendencia_semanal}`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
