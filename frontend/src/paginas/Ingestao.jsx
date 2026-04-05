import { useState, useEffect } from 'react'
import api from '../api.js'

export default function Ingestao() {
  const [arquivo, setArquivo] = useState(null)
  const [carregando, setCarregando] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState(null)
  const [disponiveis, setDisponiveis] = useState([])

  useEffect(() => { carregarDisponiveis() }, [])

  async function carregarDisponiveis() {
    try {
      const r = await api.get('/ingestao/disponivel')
      setDisponiveis(r.data)
    } catch {}
  }

  async function enviar(e) {
    e.preventDefault()
    if (!arquivo) return
    setCarregando(true); setErro(null); setResultado(null)
    const form = new FormData()
    form.append('arquivo', arquivo)
    try {
      const r = await api.post('/ingestao/upload', form)
      setResultado(r.data)
      carregarDisponiveis()
    } catch (err) {
      setErro(err.message)
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 24 }}>Dados Históricos</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div className="card">
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>Upload CSV do Profit</h2>
          <form onSubmit={enviar}>
            <label>Arquivo CSV</label>
            <input
              type="file" accept=".csv"
              onChange={e => setArquivo(e.target.files[0])}
              style={{ padding: '6px 0', border: 'none', background: 'transparent' }}
            />
            <div style={{ marginTop: 16 }}>
              <button type="submit" disabled={!arquivo || carregando}>
                {carregando ? <span className="spinner" /> : 'Importar'}
              </button>
            </div>
          </form>

          {erro && <div className="erro-msg" style={{ marginTop: 16 }}>{erro}</div>}

          {resultado && (
            <div className="sucesso-msg" style={{ marginTop: 16 }}>
              <strong>{resultado.ticker} {resultado.timeframe}</strong> importado com sucesso
              <div style={{ marginTop: 8, fontSize: 13, lineHeight: 1.8 }}>
                <div>Inseridos: <strong>{resultado.candles_inseridos}</strong></div>
                <div>Duplicados ignorados: <strong>{resultado.candles_duplicados}</strong></div>
                {resultado.periodo && (
                  <div>Período: <strong>{resultado.periodo.inicio} → {resultado.periodo.fim}</strong></div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>Dados Disponíveis</h2>
          {disponiveis.length > 0 && (
            <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 16 }}>
              Profit · já importado até{' '}
              <span style={{ color: 'var(--green)', fontWeight: 600 }}>
                {disponiveis.reduce((max, d) => d.fim > max ? d.fim : max, '')}
              </span>
            </div>
          )}
          {disponiveis.length === 0 ? (
            <p style={{ color: 'var(--text2)' }}>Nenhum dado importado ainda.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Ativo</th>
                  <th>Timeframe</th>
                  <th>Início</th>
                  <th>Fim</th>
                  <th>Candles</th>
                </tr>
              </thead>
              <tbody>
                {disponiveis.map((d, i) => (
                  <tr key={i}>
                    <td><strong>{d.ticker}</strong></td>
                    <td><span className="tag">{d.timeframe}</span></td>
                    <td style={{ color: 'var(--text2)' }}>{d.inicio}</td>
                    <td style={{ color: 'var(--text2)' }}>{d.fim}</td>
                    <td>{d.total_candles.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
