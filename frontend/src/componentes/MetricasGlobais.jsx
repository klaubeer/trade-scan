export default function MetricasGlobais({ stats, contratos = 1, valorPtBase = 0.20 }) {
  if (!stats) return null
  const pos = v => v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text)'

  const brl = pts => (pts * valorPtBase * contratos).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

  const items = [
    { label: 'Total Operações', value: stats.total_trades },
    { label: 'Win Rate', value: `${stats.win_rate}%`, color: stats.win_rate >= 50 ? 'var(--green)' : 'var(--red)' },
    { label: 'Payoff', value: stats.payoff?.toFixed(2) },
    { label: 'Expectância', value: `${stats.expectancia_pts} pts`, color: pos(stats.expectancia_pts) },
    { label: 'P&L Total', value: `${stats.total_pts} pts`, color: pos(stats.total_pts) },
    { label: 'P&L (R$)', value: brl(stats.total_pts), color: pos(stats.total_pts) },
    { label: 'Fator de Lucro', value: stats.fator_lucro?.toFixed(2), color: stats.fator_lucro >= 1 ? 'var(--green)' : 'var(--red)' },
    { label: 'Drawdown Máx', value: `${stats.max_drawdown_pts} pts  /  ${brl(Math.abs(stats.max_drawdown_pts))}`, color: 'var(--red)' },
    { label: 'Seq. Gains', value: stats.max_wins_consecutivos, color: 'var(--green)' },
    { label: 'Seq. Losses', value: stats.max_losses_consecutivos, color: 'var(--red)' },
    { label: 'Melhor Trade', value: `+${stats.melhor_trade_pts} pts  /  ${brl(stats.melhor_trade_pts)}`, color: 'var(--green)' },
    { label: 'Pior Trade', value: `${stats.pior_trade_pts} pts  /  ${brl(stats.pior_trade_pts)}`, color: 'var(--red)' },
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
      {items.map(item => (
        <div key={item.label} className="card" style={{ padding: '14px 16px' }}>
          <div style={{ fontSize: 11, color: 'var(--text2)', marginBottom: 4 }}>{item.label}</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: item.color || 'var(--text)' }}>
            {item.value}
          </div>
        </div>
      ))}
    </div>
  )
}
