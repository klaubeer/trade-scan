import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

export default function EquityCurve({ equity_curve }) {
  if (!equity_curve || equity_curve.length === 0) return null

  const data = equity_curve.map((v, i) => ({ trade: i + 1, pts: v }))

  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Equity Curve</div>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="trade" tick={{ fontSize: 11, fill: 'var(--text2)' }} label={{ value: 'Trade #', position: 'insideBottom', offset: -2, fill: 'var(--text2)', fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--text2)' }} />
          <Tooltip
            contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6 }}
            labelStyle={{ color: 'var(--text2)', fontSize: 11 }}
            formatter={v => [`${v} pts`, 'P&L']}
          />
          <ReferenceLine y={0} stroke="var(--border)" />
          <Line type="monotone" dataKey="pts" stroke="var(--blue)" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
