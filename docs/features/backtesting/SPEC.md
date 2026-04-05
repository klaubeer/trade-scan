# SPEC — Motor de Backtesting

## O que faz
Recebe um `SetupParams` e um período, percorre os candles, gera sinais de entrada/saída, executa a simulação via vectorbt e retorna trades individuais + estatísticas agregadas.

## Status atual
📋 PLANNED

## Subtarefas

| ID | Descrição | Status | DoD |
|----|-----------|--------|-----|
| F3-001 | `SetupParams` Pydantic | 📋 PLANNED | Serialização round-trip sem perda |
| F3-002 | Geração de sinais de entrada | 📋 PLANNED | Testes unitários por condição |
| F3-003 | Filtro de horário e limite diário | 📋 PLANNED | Zero sinais fora do horário |
| F3-004 | Sinal de saída forçada | 📋 PLANNED | Posição sempre fechada no `horario_fim` |
| F3-005 | Execução vectorbt | 📋 PLANNED | Reproduzível |
| F3-006 | Conversão pontos→fração | 📋 PLANNED | Verificado com 2 trades manuais |
| F3-007 | Estatísticas adicionais | 📋 PLANNED | Segmentação por contexto calculada |
| F3-008 | Persistência DuckDB | 📋 PLANNED | 3 tabelas populadas após execução |
| F3-009 | Bloqueio out-of-sample | 📋 PLANNED | Erro levantado corretamente |
| F3-010 | Validação setups referência | 📋 PLANNED | 3 setups testados com dados reais |

## Decisões específicas desta feature

- **vectorbt `from_signals`** — usado no modo signal-based. Arrays de entrada (`entries`) e saída (`exits`) pré-computados em pandas antes de passar ao vectorbt. Mais controlável que o modo event-driven.
- **Stop/alvo no mesmo candle → stop** — comportamento padrão do vectorbt quando `sl_stop` e `tp_stop` conflitam no mesmo candle: stop prevalece. Isso é conservador e correto para backtesting.
- **Conversão pontos → fração** — vectorbt espera `sl_stop` como fração do preço de entrada (ex: 0.002). Converter `stop_pts / entry_price` dinamicamente por trade, não um valor fixo global.
- **Saída forçada** — implementada como array `exits` = True no candle imediatamente anterior ao `horario_fim`, para qualquer candle onde há posição aberta.
- **Uma posição por vez** — `vectorbt` com `accumulate=False` (padrão). Novo sinal de entrada enquanto há posição aberta é ignorado.

## Fluxo detalhado de geração de sinais

```python
# 1. Carregar candles do DuckDB → df (já enriquecido com indicadores)
# 2. Para cada condição do setup → coluna booleana no df
# 3. entries = AND de todas as condições ativas
# 4. Aplicar filtro de horário: entries &= (df.time >= horario_inicio) & (df.time < horario_fim)
# 5. Aplicar limite diário:
#    - Para cada dia, zerar entries após a N-ésima ocorrência (N = max_entradas_dia)
# 6. exits_forcados = posição aberta no candle anterior ao horario_fim de cada pregão
# 7. Executar vectorbt
```

## Mapeamento condições → colunas

| Condição no SetupParams | Cálculo no DataFrame |
|---|---|
| `range_candle_min` | `(df.high - df.low) >= range_candle_min` |
| `pavio_total_max` | `(df.high - df.close).abs() + (df.close - df.low).abs() <= pavio_total_max` (simplificado) |
| `mm200_posicao = 'acima'` | `df.close > df.mm200` |
| `mm200_posicao = 'abaixo'` | `df.close < df.mm200` |
| `mme9_posicao = 'acima'` | `df.close > df.mme9` |
| `mme9_posicao = 'abaixo'` | `df.close < df.mme9` |
| `ifr2_max` | `df.ifr2 < ifr2_max` (compra sobrevendido) |
| `ifr2_min` | `df.ifr2 > ifr2_min` (venda sobrecomprado) |
| `range_acumulado_max_pct` | `df.range_acumulado_pct < range_acumulado_max_pct` |
| `gap_abertura_min` | `df.gap_abertura.abs() > gap_abertura_min` |
| `primeiro_candle_direcao` | `df.primeiro_candle_dir == direcao` |
| `tendencia_semanal` | `df.tendencia_semanal == tendencia` (ou qualquer) |

## Cálculo de pavios (definição correta)

```
corpo = abs(close - open)
pavio_superior = high - max(open, close)
pavio_inferior = min(open, close) - low
pavio_total = pavio_superior + pavio_inferior
```

## Estrutura do contexto_json por trade

```json
{
  "tendencia_semanal": "alta",
  "periodo_dia": "manha",
  "gap_abertura_pts": 150,
  "gap_abertura_tipo": "positivo",
  "range_acumulado_pct": 0.42,
  "range_acumulado_faixa": "<0.5%",
  "mm200_posicao": "acima",
  "mme9_posicao": "abaixo",
  "ifr2_valor": 3.2
}
```

## Estatísticas a calcular

### Globais (via vectorbt)
- total_trades, win_rate, avg_win, avg_loss, payoff, expectancy
- total_pnl_pts, total_pnl_brl, profit_factor
- max_drawdown_pts, max_drawdown_pct

### Adicionais (calcular manualmente pós-vectorbt)
- max_consec_wins, max_consec_losses
- best_trade_pts, worst_trade_pts
- pnl_por_dia (dict date → pts)
- pnl_por_mes (dict YYYY-MM → pts)
- equity_curve (lista de pts acumulados por trade)
- histograma (bins de 10 pts, -200 a +200)

### Segmentação por contexto
Para cada dimensão, calcular: total_trades, win_rate, expectancy, total_pnl_pts

```
por_tendencia_semanal: { alta: {...}, baixa: {...}, lateral: {...} }
por_periodo_dia:        { manha: {...}, tarde: {...} }
por_gap:                { positivo: {...}, negativo: {...}, sem_gap: {...} }
por_range_acumulado:    { '<0.5%': {...}, '0.5-1%': {...}, '>1%': {...} }
```

## Dependências externas
- vectorbt 0.26.x
- DuckDB 1.2.x
- pandas, numpy
