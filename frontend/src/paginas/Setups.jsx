import { useState, useEffect } from 'react'
import api from '../api.js'

const DEFAULTS = {
  nome: '', ticker: 'WIN', timeframe: '5min', direcao: 'long',
  tipo_entrada: 'fechamento_gatilho', stop_pts: 30, alvo_pts: 60,
  horario_inicio: '09:00', horario_fim: '17:30', horario_fechamento: '18:00', max_entradas_dia: 1,
  slippage_pts: 0, custo_por_ponto: 0.20,
  range_candle_min: '', pavio_total_max: '', pavio_superior_max: '', pavio_inferior_max: '',
  mm200_posicao: '', mme9_posicao: '', ifr2_max: '', ifr2_min: '',
  range_acumulado_max_pct: '', gap_abertura_min: '', primeiro_candle_direcao: '', tendencia_semanal: '',
  adx_min: '', atr_fator_range: '',
  sequencia_candles: '', sequencia_wick_max_pct: '',
  sequencia_filtrar_zonas: false,
  alvo_proximo_pct_dia: false, alvo_minimo_pts: '',
}

export default function Setups() {
  const [setups, setSetups] = useState([])
  const [form, setForm] = useState(DEFAULTS)
  const [mostarForm, setMostrarForm] = useState(false)
  const [editandoId, setEditandoId] = useState(null)
  const [erro, setErro] = useState(null)
  const [sucesso, setSucesso] = useState(null)

  useEffect(() => { carregar() }, [])

  async function carregar() {
    try { const r = await api.get('/setups'); setSetups(r.data) } catch {}
  }

  function campo(key) {
    return {
      value: form[key],
      onChange: e => setForm(f => ({ ...f, [key]: e.target.value }))
    }
  }

  function numericoCampo(key) {
    return {
      value: form[key],
      onChange: e => setForm(f => ({ ...f, [key]: e.target.value === '' ? '' : Number(e.target.value) }))
    }
  }

  function editar(setup) {
    const p = setup.params
    setForm({
      nome: setup.nome,
      ticker: setup.ticker,
      timeframe: p.timeframe ?? '5min',
      direcao: p.direcao ?? 'long',
      tipo_entrada: p.tipo_entrada ?? 'fechamento_gatilho',
      stop_pts: p.stop_pts ?? 30,
      alvo_pts: p.alvo_pts ?? 60,
      horario_inicio: p.horario_inicio ?? '09:00',
      horario_fim: p.horario_fim ?? '17:30',
      horario_fechamento: p.horario_fechamento ?? '18:00',
      max_entradas_dia: p.max_entradas_dia ?? 1,
      slippage_pts: p.slippage_pts ?? 0,
      custo_por_ponto: p.custo_por_ponto ?? 0.20,
      range_candle_min: p.range_candle_min ?? '',
      pavio_total_max: p.pavio_total_max ?? '',
      pavio_superior_max: p.pavio_superior_max ?? '',
      pavio_inferior_max: p.pavio_inferior_max ?? '',
      mm200_posicao: p.mm200_posicao ?? '',
      mme9_posicao: p.mme9_posicao ?? '',
      ifr2_max: p.ifr2_max ?? '',
      ifr2_min: p.ifr2_min ?? '',
      range_acumulado_max_pct: p.range_acumulado_max_pct ?? '',
      gap_abertura_min: p.gap_abertura_min ?? '',
      primeiro_candle_direcao: p.primeiro_candle_direcao ?? '',
      tendencia_semanal: p.tendencia_semanal ?? '',
      adx_min: p.adx_min ?? '',
      atr_fator_range: p.atr_fator_range ?? '',
      sequencia_candles: p.sequencia_candles ?? '',
      sequencia_wick_max_pct: p.sequencia_wick_max_pct ?? '',
      sequencia_filtrar_zonas: p.sequencia_filtrar_zonas ?? false,
      alvo_proximo_pct_dia: p.alvo_proximo_pct_dia ?? false,
      alvo_minimo_pts: p.alvo_minimo_pts ?? '',
    })
    setEditandoId(setup.id)
    setMostrarForm(true)
    window.scrollTo(0, 0)
  }

  async function salvar(e) {
    e.preventDefault(); setErro(null); setSucesso(null)
    const payload = { ...form }
    const opcionais = ['range_candle_min','pavio_total_max','pavio_superior_max','pavio_inferior_max',
      'mm200_posicao','mme9_posicao','ifr2_max','ifr2_min','range_acumulado_max_pct',
      'gap_abertura_min','primeiro_candle_direcao','tendencia_semanal',
      'adx_min','atr_fator_range',
      'sequencia_candles','sequencia_wick_max_pct','alvo_minimo_pts']
    opcionais.forEach(k => { if (payload[k] === '' || payload[k] === null) delete payload[k] })
    try {
      if (editandoId) {
        await api.put(`/setups/${editandoId}`, payload)
        setSucesso('Setup atualizado com sucesso.')
      } else {
        await api.post('/setups', payload)
        setSucesso('Setup criado com sucesso.')
      }
      setForm(DEFAULTS); setMostrarForm(false); setEditandoId(null)
      carregar()
    } catch (err) { setErro(err.message) }
  }

  async function deletar(id) {
    if (!confirm('Deletar setup?')) return
    await api.delete(`/setups/${id}`); carregar()
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Setups</h1>
        <button onClick={() => { setMostrarForm(v => !v); setEditandoId(null); setForm(DEFAULTS) }}>
          {mostarForm ? 'Cancelar' : '+ Novo Setup'}
        </button>
      </div>

      {sucesso && <div className="sucesso-msg" style={{ marginBottom: 16 }}>{sucesso}</div>}
      {erro && <div className="erro-msg" style={{ marginBottom: 16 }}>{erro}</div>}

      {mostarForm && (
        <div className="card" style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 16 }}>{editandoId ? 'Editar Setup' : 'Novo Setup'}</h2>
          <form onSubmit={salvar}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
              <div><label>Nome</label><input required {...campo('nome')} /></div>
              <div><label>Ativo</label>
                <select {...campo('ticker')}>
                  {['WIN','WDO','BITFUT'].map(v => <option key={v}>{v}</option>)}
                </select>
              </div>
              <div><label>Timeframe</label>
                <select {...campo('timeframe')}>
                  {['1min','5min','15min','60min'].map(v => <option key={v}>{v}</option>)}
                </select>
              </div>
              <div><label>Direção</label>
                <select {...campo('direcao')}>
                  {['long','short','ambos'].map(v => <option key={v}>{v}</option>)}
                </select>
              </div>
              <div><label>Tipo de Entrada</label>
                <select {...campo('tipo_entrada')}>
                  {['fechamento_gatilho','rompimento_fechamento','rompimento_maxima','rompimento_minima'].map(v => <option key={v}>{v}</option>)}
                </select>
              </div>
              <div><label>Stop (pts)</label><input type="number" step="0.1" required {...numericoCampo('stop_pts')} /></div>
              <div><label>Alvo (pts)</label><input type="number" step="0.1" required {...numericoCampo('alvo_pts')} /></div>
              <div><label>Abertura (início entradas)</label><input type="time" {...campo('horario_inicio')} /></div>
              <div><label>Corte (última entrada)</label><input type="time" {...campo('horario_fim')} /></div>
              <div><label>Fechamento (fim pregão)</label><input type="time" {...campo('horario_fechamento')} /></div>
              <div><label>Máx. Entradas/Dia</label><input type="number" min="1" max="10" {...numericoCampo('max_entradas_dia')} /></div>
              <div><label>Slippage (pts)</label><input type="number" step="0.1" {...numericoCampo('slippage_pts')} /></div>
              <div><label>Custo por Ponto (R$)</label><input type="number" step="0.01" {...numericoCampo('custo_por_ponto')} /></div>
            </div>

            <div style={{ margin: '20px 0 8px', fontSize: 12, color: 'var(--text2)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Filtros de Entrada (opcionais)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
              <div><label>Range candle mín (pts)</label><input type="number" placeholder="—" {...numericoCampo('range_candle_min')} /></div>
              <div><label>Pavio total máx (pts)</label><input type="number" placeholder="—" {...numericoCampo('pavio_total_max')} /></div>
              <div><label>MM200 posição</label>
                <select {...campo('mm200_posicao')}><option value="">—</option><option value="acima">Acima</option><option value="abaixo">Abaixo</option></select>
              </div>
              <div><label>MME9 posição</label>
                <select {...campo('mme9_posicao')}><option value="">—</option><option value="acima">Acima</option><option value="abaixo">Abaixo</option></select>
              </div>
              <div><label>IFR2 {'<'} (sobrevendido)</label><input type="number" placeholder="ex: 5" {...numericoCampo('ifr2_max')} /></div>
              <div><label>IFR2 {'>'} (sobrecomprado)</label><input type="number" placeholder="ex: 95" {...numericoCampo('ifr2_min')} /></div>
              <div><label>Range acum. máx (%)</label><input type="number" step="0.1" placeholder="—" {...numericoCampo('range_acumulado_max_pct')} /></div>
              <div><label>Gap abertura mín (pts)</label><input type="number" placeholder="—" {...numericoCampo('gap_abertura_min')} /></div>
              <div><label>1º Candle direção</label>
                <select {...campo('primeiro_candle_direcao')}><option value="">—</option><option value="alta">Alta</option><option value="baixa">Baixa</option></select>
              </div>
              <div><label>Tendência semanal</label>
                <select {...campo('tendencia_semanal')}><option value="">—</option><option value="alta">Alta</option><option value="baixa">Baixa</option><option value="lateral">Lateral</option><option value="qualquer">Qualquer</option></select>
              </div>
            </div>

            <div style={{ margin: '20px 0 8px', fontSize: 12, color: 'var(--text2)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Filtros ADX / ATR (opcional)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12 }}>
              <div>
                <label>ADX mínimo</label>
                <input type="number" min="0" max="100" step="1" placeholder="ex: 25" {...numericoCampo('adx_min')} />
                <div style={{ fontSize: 11, color: 'var(--text2)', marginTop: 3 }}>ADX(14) ≥ X para entrar</div>
              </div>
              <div>
                <label>Fator ATR do dia</label>
                <input type="number" min="0" step="0.1" placeholder="ex: 1.0" {...numericoCampo('atr_fator_range')} />
                <div style={{ fontSize: 11, color: 'var(--text2)', marginTop: 3 }}>Range dia ≥ X × ATR(14) diário</div>
              </div>
            </div>

            <div style={{ margin: '20px 0 8px', fontSize: 12, color: 'var(--text2)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Sequência de Candles (opcional)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 12, alignItems: 'end' }}>
              <div>
                <label>Nº candles consecutivos</label>
                <input type="number" min="2" max="10" placeholder="ex: 3" {...numericoCampo('sequencia_candles')} />
              </div>
              <div>
                <label>Pavio máx (% do range)</label>
                <input type="number" min="0" max="100" step="1" placeholder="ex: 50" {...numericoCampo('sequencia_wick_max_pct')} />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginBottom: 0 }}>
                  <input
                    type="checkbox"
                    checked={form.sequencia_filtrar_zonas}
                    onChange={e => setForm(f => ({ ...f, sequencia_filtrar_zonas: e.target.checked }))}
                  />
                  Filtrar zonas S/R
                </label>
                <div style={{ fontSize: 11, color: 'var(--text2)', marginTop: 4 }}>
                  Ignora entrada se candle toca abertura ou % do dia
                </div>
              </div>
            </div>

            <div style={{ margin: '20px 0 8px', fontSize: 12, color: 'var(--text2)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Alvo Dinâmico (opcional)
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
              <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', marginBottom: 0 }}>
                  <input
                    type="checkbox"
                    checked={form.alvo_proximo_pct_dia}
                    onChange={e => setForm(f => ({ ...f, alvo_proximo_pct_dia: e.target.checked }))}
                  />
                  Alvo no próximo % do dia
                </label>
                <div style={{ fontSize: 11, color: 'var(--text2)', marginTop: 4 }}>
                  0,5% / 1% / 1,5% / 2% / 2,5% / 3% da abertura
                </div>
              </div>
              <div>
                <label>Distância mínima do alvo (pts)</label>
                <input type="number" step="10" placeholder={form.alvo_proximo_pct_dia ? 'ex: 600' : '—'} disabled={!form.alvo_proximo_pct_dia} {...numericoCampo('alvo_minimo_pts')} />
              </div>
            </div>

            <div style={{ marginTop: 20 }}>
              <button type="submit">{editandoId ? 'Atualizar Setup' : 'Salvar Setup'}</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {setups.length === 0 ? (
          <p style={{ color: 'var(--text2)' }}>Nenhum setup criado ainda.</p>
        ) : (
          <table>
            <thead><tr><th>Nome</th><th>Ativo</th><th>TF</th><th>Direção</th><th>Stop</th><th>Alvo</th><th>Entrada</th><th></th></tr></thead>
            <tbody>
              {setups.map(s => (
                <tr key={s.id}>
                  <td><strong>{s.nome}</strong></td>
                  <td>{s.ticker}</td>
                  <td><span className="tag">{s.params.timeframe}</span></td>
                  <td>{s.params.direcao}</td>
                  <td style={{ color: 'var(--red)' }}>{s.params.stop_pts} pts</td>
                  <td style={{ color: 'var(--green)' }}>{s.params.alvo_pts} pts</td>
                  <td style={{ fontSize: 12, color: 'var(--text2)' }}>{s.params.tipo_entrada}</td>
                  <td style={{ display: 'flex', gap: 6 }}>
                    <button className="secundario" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => editar(s)}>✎</button>
                    <button className="perigo" style={{ padding: '4px 10px', fontSize: 12 }} onClick={() => deletar(s.id)}>×</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
