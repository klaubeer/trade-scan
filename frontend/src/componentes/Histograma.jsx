import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ReferenceLine, ResponsiveContainer } from 'recharts'

export default function Histograma({ histograma }) {
  if (!histograma || histograma.length === 0) return null
  const data = histograma.filter(h => h.contagem > 0)

  return (
    <div>
      <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 12 }}>Distribuição de Resultados</div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="bin" tick={{ fontSize: 10, fill: 'var(--text2)' }} />
          <YAxis tick={{ fontSize: 11, fill: 'var(--text2)' }} />
          <Tooltip
            contentStyle={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6 }}
            formatter={(v, _, p) => [v, `${p.payload.bin} pts`]}
          />
          <ReferenceLine x={0} stroke="var(--border)" />
          <Bar dataKey="contagem">
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.bin >= 0 ? 'var(--green)' : 'var(--red)'} fillOpacity={0.7} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
