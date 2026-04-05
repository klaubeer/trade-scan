import { useState } from 'react'

export default function TabelaOperacoes({ trades }) {
  const [pagina, setPagina] = useState(0)
  const POR_PAG = 20

  if (!trades || trades.length === 0) return null

  const total = trades.length
  const inicio = pagina * POR_PAG
  const pagina_trades = trades.slice(inicio, inicio + POR_PAG)

  function exportar() {
    const header = ['Data','Hora','Direção','Entrada','Saída','Resultado','Pts','Tendência Semanal','Range Acum %','Gap Abertura']
    const rows = trades.map(t => {
      const dt = t.datetime || ''
      const ctx = t.contexto || {}
      return [
        dt.slice(0,10), dt.slice(11,16),
        t.direcao, t.preco_entrada, t.preco_saida,
        t.resultado, t.resultado_pts,
        ctx.tendencia_semanal || '', ctx.range_acumulado_pct || '', ctx.gap_abertura_pts || ''
      ].join(';')
    })
    const csv = [header.join(';'), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'operacoes.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 600 }}>Operações ({total})</div>
        <button className="secundario" style={{ padding: '6px 12px', fontSize: 12 }} onClick={exportar}>
          Exportar CSV
        </button>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Data</th><th>Hora</th><th>Dir.</th>
              <th>Entrada</th><th>Saída</th><th>Resultado</th><th>Pts</th>
              <th>Tend. Semanal</th><th>Range %</th><th>Gap (pts)</th>
            </tr>
          </thead>
          <tbody>
            {pagina_trades.map((t, i) => {
              const ctx = t.contexto || {}
              const dt = t.datetime || ''
              return (
                <tr key={i}>
                  <td>{dt.slice(0,10)}</td>
                  <td>{dt.slice(11,16)}</td>
                  <td>{t.direcao}</td>
                  <td>{t.preco_entrada}</td>
                  <td>{t.preco_saida}</td>
                  <td><span className={`badge ${t.resultado}`}>{t.resultado}</span></td>
                  <td style={{ color: t.resultado_pts > 0 ? 'var(--green)' : t.resultado_pts < 0 ? 'var(--red)' : 'var(--text)' }}>
                    {t.resultado_pts > 0 ? '+' : ''}{t.resultado_pts}
                  </td>
                  <td style={{ color: 'var(--text2)', fontSize: 12 }}>{ctx.tendencia_semanal || '—'}</td>
                  <td style={{ color: 'var(--text2)', fontSize: 12 }}>{ctx.range_acumulado_pct ?? '—'}</td>
                  <td style={{ color: 'var(--text2)', fontSize: 12 }}>{ctx.gap_abertura_pts ?? '—'}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
      {total > POR_PAG && (
        <div style={{ display: 'flex', gap: 8, marginTop: 12, justifyContent: 'center' }}>
          <button className="secundario" disabled={pagina === 0} onClick={() => setPagina(p => p - 1)}>← Anterior</button>
          <span style={{ color: 'var(--text2)', lineHeight: '34px', fontSize: 13 }}>
            {pagina + 1} / {Math.ceil(total / POR_PAG)}
          </span>
          <button className="secundario" disabled={(pagina + 1) * POR_PAG >= total} onClick={() => setPagina(p => p + 1)}>Próximo →</button>
        </div>
      )}
    </div>
  )
}
