import { useNavigate } from 'react-router-dom'

const FEATURES = [
  {
    icon: '📂',
    nome: 'Dados',
    descricao: 'Importe CSVs exportados do Profit. Deduplicação automática e agregação multi-timeframe.',
    rota: '/dados',
    cor: 'var(--blue)',
  },
  {
    icon: '⚙️',
    nome: 'Setups',
    descricao: 'Defina regras objetivas de entrada e saída com mais de 30 parâmetros configuráveis.',
    rota: '/setups',
    cor: 'var(--yellow)',
  },
  {
    icon: '▶️',
    nome: 'Backtesting',
    descricao: 'Execute o setup contra dados históricos reais e veja win rate, fator de lucro, drawdown e muito mais.',
    rota: '/backtest',
    cor: 'var(--green)',
  },
  {
    icon: '📋',
    nome: 'Histórico',
    descricao: 'Revise todos os backtests executados, compare períodos e aprove runs para out-of-sample.',
    rota: '/historico',
    cor: 'var(--blue)',
  },
  {
    icon: '⚖️',
    nome: 'Comparativo',
    descricao: 'Compare múltiplos setups lado a lado no mesmo período para identificar o de maior edge.',
    rota: '/comparativo',
    cor: 'var(--yellow)',
  },
  {
    icon: '🔄',
    nome: 'Walk-Forward',
    descricao: 'Valide o setup com janelas deslizantes para detectar overfitting antes de operar.',
    rota: '/walk-forward',
    cor: 'var(--green)',
  },
  {
    icon: '🎲',
    nome: 'Monte Carlo',
    descricao: 'Simule 1.000+ cenários sobre os trades reais para estimar risco de ruína e drawdown máximo.',
    rota: '/monte-carlo',
    cor: 'var(--red)',
  },
  {
    icon: '🧠',
    nome: 'CNN — Padrões',
    descricao: 'Treina um modelo de deep learning sobre os candles antes de entradas históricas para filtrar sinais futuros.',
    rota: '/cnn-padroes',
    cor: 'var(--yellow)',
  },
]

const PASSOS = [
  { num: '01', titulo: 'Importe seus dados', desc: 'Exporte candles do Profit em CSV e faça upload na tela de Dados.' },
  { num: '02', titulo: 'Crie um setup', desc: 'Configure timeframe, indicadores, stop e alvo em pontos para o WIN, WDO ou BITFUT.' },
  { num: '03', titulo: 'Rode o backtest', desc: 'Selecione o período in-sample, execute e analise as métricas.' },
  { num: '04', titulo: 'Valide o edge', desc: 'Use Walk-Forward e Monte Carlo para confirmar que o setup sobrevive fora da janela de otimização.' },
]

export default function Home() {
  const navigate = useNavigate()

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>

      {/* Hero */}
      <div style={{ textAlign: 'center', padding: '48px 0 56px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 12,
          background: 'rgba(74,158,255,0.08)', border: '1px solid rgba(74,158,255,0.2)',
          borderRadius: 999, padding: '6px 18px', marginBottom: 28,
          fontSize: 13, color: 'var(--blue)',
        }}>
          <span style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
          em produção · tradescan.klauberfischer.online
        </div>

        <h1 style={{ fontSize: 48, fontWeight: 800, color: 'var(--text)', margin: '0 0 16px', lineHeight: 1.15 }}>
          Backtester inteligente<br />
          <span style={{ color: 'var(--blue)' }}>para day traders da B3</span>
        </h1>

        <p style={{ fontSize: 18, color: 'var(--text2)', maxWidth: 600, margin: '0 auto 36px', lineHeight: 1.6 }}>
          Valide seus setups de day trade com dados históricos reais do Profit.
          Win rate, fator de lucro, drawdown e análise de IA — tudo em segundos.
        </p>

        <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
          <button className="btn" onClick={() => navigate('/backtest')}
            style={{ padding: '12px 28px', fontSize: 15 }}>
            Rodar backtest
          </button>
          <button className="btn btn-secondary" onClick={() => navigate('/dados')}
            style={{ padding: '12px 28px', fontSize: 15 }}>
            Importar dados
          </button>
        </div>
      </div>

      {/* Features */}
      <div style={{ marginBottom: 64 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', marginBottom: 24 }}>
          Módulos
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {FEATURES.map(f => (
            <div
              key={f.rota}
              onClick={() => navigate(f.rota)}
              className="card"
              style={{ cursor: 'pointer', transition: 'border-color .15s', borderColor: 'var(--border)' }}
              onMouseEnter={e => e.currentTarget.style.borderColor = f.cor}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{ fontSize: 28, marginBottom: 10 }}>{f.icon}</div>
              <div style={{ fontWeight: 700, color: f.cor, marginBottom: 6, fontSize: 15 }}>{f.nome}</div>
              <div style={{ color: 'var(--text2)', fontSize: 13, lineHeight: 1.6 }}>{f.descricao}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Como usar */}
      <div style={{ marginBottom: 64 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', marginBottom: 24 }}>
          Como usar
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16 }}>
          {PASSOS.map(p => (
            <div key={p.num} className="card">
              <div style={{ fontSize: 28, fontWeight: 800, color: 'rgba(74,158,255,0.25)', marginBottom: 12, fontVariantNumeric: 'tabular-nums' }}>
                {p.num}
              </div>
              <div style={{ fontWeight: 600, color: 'var(--text)', marginBottom: 6, fontSize: 14 }}>{p.titulo}</div>
              <div style={{ color: 'var(--text2)', fontSize: 13, lineHeight: 1.6 }}>{p.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Ativos suportados */}
      <div style={{
        background: 'var(--bg2)', border: '1px solid var(--border)',
        borderRadius: 12, padding: '24px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 48,
      }}>
        <div>
          <div style={{ fontWeight: 700, color: 'var(--text)', marginBottom: 4 }}>Ativos suportados</div>
          <div style={{ color: 'var(--text2)', fontSize: 13 }}>Mini-índice, mini-dólar e Bitcoin Futuro da B3</div>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          {['WIN', 'WDO', 'BITFUT'].map(a => (
            <span key={a} style={{
              background: 'rgba(74,158,255,0.1)', color: 'var(--blue)',
              border: '1px solid rgba(74,158,255,0.2)',
              borderRadius: 8, padding: '6px 16px', fontWeight: 700, fontSize: 14,
            }}>{a}</span>
          ))}
        </div>
      </div>

    </div>
  )
}
