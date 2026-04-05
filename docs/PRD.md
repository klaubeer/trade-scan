# PRD — TradeScan
**Versão:** 0.1
**Status:** Draft
**Autor:** Klauber Fischer
**Data:** Abril 2026

---

## 1. Visão Geral

TradeScan é um backtester inteligente para day traders pessoa física, focado em mini-índice (WIN), mini-dólar (WDO) e BITFUT da B3. O sistema permite carregar dados históricos de candles, definir setups operacionais, executar simulações de backtesting e obter estatísticas detalhadas — eliminando o viés emocional e o processo manual de validação em planilhas.

A camada de IA auxilia na formulação e refinamento de hipóteses de setup, interpretando resultados estatísticos e sugerindo variações para teste.

**Objetivo central:** responder com dados reais se um setup específico tem edge estatístico positivo — e em quais condições de mercado ele performa melhor ou pior.

---

## 2. Problema

Day traders pessoa física operam frequentemente baseados em intuição, padrões visuais e setups não validados estatisticamente. O processo de validação manual (planilhas, anotações) é lento, propenso a viés de confirmação e não escala para testar múltiplas variações de parâmetros.

O resultado: o trader não sabe com precisão se seu setup tem edge real ou se os ganhos/perdas foram ruído estatístico.

---

## 3. Usuário

Trader pessoa física com experiência em análise gráfica, operando ativos da B3 (WIN, WDO, BITFUT). Tem conhecimento técnico suficiente para descrever seus setups e interpretar estatísticas. Usa Profit (Nelogica) como plataforma principal de trading.

---

## 4. Fora do Escopo

- Execução automática de ordens (não é um bot de trading)
- Dados em tempo real ou integração com corretoras
- Múltiplos usuários / autenticação
- Gráfico de candles interativo (usuário usa o Profit para isso)
- Otimização automática de parâmetros sem validação out-of-sample

---

## 5. Funcionalidades

### 5.1 Ingestão e Armazenamento de Dados

**Input:** CSV exportado pelo Profit (Nelogica)
**Formato:** `Ticker;Data;Hora;Abertura;Máxima;Mínima;Fechamento;VolumeFinanceiro;QtdContratos`
**Ativos suportados:** WIN, WDO, BITFUT
**Timeframe base:** qualquer (1min, 5min, 15min — conforme exportado)

**Comportamento:**
- Upload de CSV via interface
- Sistema valida formato e detecta o ativo/timeframe automaticamente
- Deduplicação por chave `(ticker, data, hora)` — reimport não duplica dados
- Append incremental — usuário carrega apenas os novos dias
- Dados armazenados em DuckDB local

**Timeframes derivados:** gerados por agregação a partir dos dados base
- Se base = 1min → agrega para 5min, 15min, 60min, diário, semanal
- Se base = 5min → agrega para 15min, 60min, diário, semanal
- Se base = 15min → agrega para 60min, diário, semanal

---

### 5.2 Indicadores Calculados

Calculados automaticamente sobre os dados armazenados:

| Indicador | Descrição |
|---|---|
| MM200 | Média móvel simples dos últimos 200 candles (no timeframe selecionado) |
| MME9 | Média móvel exponencial de 9 períodos (para Setup 9.1) |
| IFR(2) | RSI de 2 períodos (para Setup IFR2) |
| % do dia | Variação percentual em relação à abertura do pregão (0.5%, 1%, 1.5%, etc.) |
| Gap de abertura | Diferença entre abertura do dia e fechamento do dia anterior |
| Range acumulado | Total de pontos percorridos desde a abertura até o candle atual |
| Direção do primeiro candle | Alta ou baixa no primeiro candle do pregão (configurável: 15min ou 60min) |
| Tendência semanal | Direção da semana corrente (alta / baixa / lateral) com base no OHLC semanal agregado |

---

### 5.3 Definição de Setups

O usuário define um setup via interface. Um setup é composto por:

**Parâmetros obrigatórios:**
- Nome do setup
- Ativo (WIN / WDO / BITFUT)
- Timeframe de execução (1min / 5min / 15min)
- Direção permitida (long / short / ambos)
- Condição de entrada (ver abaixo)
- Stop em pontos (fixo)
- Alvo em pontos (fixo) — pode ser múltiplo (ex: 100pts ou 150pts)
- Horário permitido (ex: 09:00 às 12:00)
- Máximo de entradas por dia

**Condições de entrada (configuráveis via interface):**
- Range do candle > X pontos
- Pavio total (sup + inf) < Y pontos
- Pavio individual (superior ou inferior) < Y pontos
- Fechamento acima/abaixo da MM200
- Fechamento acima/abaixo da MME9
- IFR(2) < X (sobrevendido) ou IFR(2) > X (sobrecomprado)
- Range acumulado do dia < X% (filtro de range esgotado)
- Gap de abertura > X pontos
- Direção do primeiro candle = alta/baixa
- Tendência semanal = alta/baixa/qualquer

**Condição de rompimento:**
- Entrada no rompimento do fechamento do candle gatilho
- Entrada no fechamento do candle gatilho
- Entrada no rompimento da máxima/mínima do candle gatilho

**Modo IA (opcional):**
O usuário descreve uma ideia em linguagem natural. O agente LangGraph formula as condições em parâmetros estruturados, submete ao motor de backtesting e retorna os resultados com interpretação.

---

### 5.4 Motor de Backtesting

**Funcionamento:**
- Percorre candle a candle no período selecionado
- Aplica as condições de entrada conforme o setup
- Simula entrada, stop e alvo com base nos candles seguintes
- Registra cada operação com todos os metadados de contexto

**Regras de simulação:**
- Uma operação aberta por vez (sem múltiplas posições simultâneas)
- Stop e alvo verificados barra a barra (high/low do candle)
- Se stop e alvo são atingidos no mesmo candle → computa o stop (conservador)
- Encerramento forçado no horário limite do dia (sem carregar posição overnight)
- Slippage configurável (padrão: 0 pontos)
- Custo operacional configurável (padrão: 0 — usuário ajusta conforme corretora)

**Separação in-sample / out-of-sample:**
- Usuário define período de exploração (in-sample) e período de validação (out-of-sample)
- Sistema alerta se setup for testado no período out-of-sample antes de definir os parâmetros no in-sample

---

### 5.5 Estatísticas e Resultados

**Métricas globais:**
- Total de operações
- Win rate (%)
- Payoff médio (gain médio / loss médio)
- Expectância por operação (pts e R$)
- P&L total (pts e R$, configurável por valor do ponto)
- Fator de lucro (gross profit / gross loss)

**Métricas de risco:**
- Drawdown máximo (pts e %)
- Maior sequência de losses consecutivos
- Maior sequência de gains consecutivos
- Maior loss individual
- Maior gain individual

**Evolução temporal:**
- P&L por dia
- P&L por mês
- Equity curve (linha de evolução do saldo)

**Segmentação por contexto:**
- Tendência semanal: alta / baixa / lateral
- Período do dia: manhã (09h-12h) / tarde (12h-17h)
- Gap de abertura: positivo / negativo / sem gap
- Range acumulado até a entrada: < 0.5% / 0.5-1% / > 1%

**Histograma:**
- Distribuição de resultados individuais (pts por operação)

---

### 5.6 Lista de Operações

Exportável e filtrável. Cada linha contém:

| Campo | Descrição |
|---|---|
| Data | Data do pregão |
| Hora entrada | Horário da entrada |
| Direção | Long / Short |
| Preço entrada | Nível de entrada |
| Preço saída | Stop ou alvo atingido |
| Resultado | Gain / Loss / Breakeven |
| Pontos | Resultado em pontos |
| R$ | Resultado em reais |
| Tendência semanal | Alta / Baixa / Lateral |
| Range acumulado | % do dia até a entrada |
| Gap abertura | Pontos |

Objetivo: permitir que o usuário confira operação por operação no Profit para validação visual.

---

### 5.7 Comparativo de Setups

- Testar múltiplos setups no mesmo período
- Tabela comparativa de métricas principais
- Identificação visual do setup com melhor expectância

---

### 5.9 Walk-Forward Analysis

Ao invés de um corte fixo in-sample/out-of-sample, executa janelas rolantes que simulam o processo real de um trader que re-otimiza periodicamente.

**Funcionamento:**
- Usuário define: período total, tamanho da janela de otimização (ex: 6 meses), tamanho da janela de validação (ex: 1 mês), step entre janelas (ex: 1 mês)
- Sistema cria automaticamente as janelas: otimiza em [Jan-Jun], valida em [Jul]; depois otimiza em [Fev-Jul], valida em [Ago]; e assim por diante
- Em cada janela de otimização, o setup é testado como está (sem auto-otimização de parâmetros — isso é configurado pelo usuário)
- Os resultados das janelas de validação são concatenados para formar a curva out-of-sample real

**Resultados por janela:**
- Métricas de cada janela de otimização (in-sample)
- Métricas de cada janela de validação (out-of-sample)
- Degradação: diferença de win rate e expectância entre in-sample e out-of-sample por janela

**Resultado consolidado:**
- Equity curve composta apenas pelos períodos out-of-sample
- Eficiência do walk-forward: `expectância_out / expectância_in` (< 0.5 = sinal de overfitting)
- Consistência: % de janelas out-of-sample com expectância positiva

**Interpretação:**
- Setup com eficiência > 0.6 e consistência > 60% das janelas = robusto
- Setup que só performa em certas janelas = dependente de regime de mercado (identificar qual regime)

---

### 5.10 Monte Carlo sobre Trades

Dado o conjunto de trades de um backtest já executado, embaralha a sequência aleatoriamente N vezes e calcula a distribuição de drawdowns e equity curves possíveis.

**Funcionamento:**
- Input: lista de trades de um `backtest_run` existente
- N simulações (padrão: 1.000 — configurável até 10.000)
- Cada simulação: embaralhar a ordem dos trades, recalcular equity curve e drawdown máximo

**Resultados:**
- Distribuição de drawdown máximo (histograma): P10, P25, P50, P75, P90, P95, P99
- Distribuição de P&L final: mesmo percentis
- Probabilidade de ruin configurável (ex: P(drawdown > 30%) = X%)
- Equity curve: banda de confiança (P10-P90) + mediana

**Uso prático:**
- O drawdown histórico observado é otimista (você teve sorte na sequência)
- O P95 do Monte Carlo é o drawdown que você deve esperar suportar psicologicamente
- Se P95 de drawdown for insuportável → setup não é operável, mesmo com expectância positiva

---

### 5.8 Camada de IA

**Modo exploração:**
1. Usuário descreve ideia em linguagem natural
2. Agente (LangGraph) formula hipóteses de setup em parâmetros estruturados
3. Motor de backtesting executa
4. LLM interpreta resultados e sugere refinamentos ("e se o stop fosse 150 ao invés de 200?")
5. Usuário decide se quer testar a variação

**Modo interpretação:**
- Após qualquer backtesting, usuário pode pedir interpretação dos resultados
- LLM identifica padrões (ex: "o setup performa bem em tendência de alta mas perde no lateral")
- Sugere filtros adicionais baseados nos dados de segmentação

**Guardrails:**
- LLM nunca afirma que um setup "vai funcionar" — apenas descreve o que os dados mostram
- Sempre alerta sobre risco de overfitting quando múltiplas variações são testadas no mesmo período

---

## 6. Arquitetura Técnica

```
Frontend (React)
    ↓ HTTP
Backend (FastAPI / Python)
    ├── Pipeline de ingestão (pandas → DuckDB)
    ├── Motor de indicadores (pandas / numpy)
    ├── Motor de backtesting (vectorbt)
    ├── Agente LLM (LangGraph + Claude API)
    └── DuckDB (banco local)
```

**Stack:**
- **Backend:** Python 3.12 + FastAPI
- **Banco:** DuckDB (embedded, arquivo local)
- **Backtesting:** vectorbt
- **Agente:** LangGraph + Claude API (claude-sonnet-4-6)
- **Frontend:** React + Recharts (equity curve, histograma)
- **Deploy:** Local

---

## 7. Dados e Persistência

**Tabelas DuckDB:**

```sql
candles (ticker, timeframe, datetime, open, high, low, close, volume_fin, qty)
setups (id, name, ticker, params_json, created_at)
backtest_runs (id, setup_id, period_start, period_end, sample_type, created_at)
backtest_trades (id, run_id, datetime, direction, entry, exit, result_pts, context_json)
backtest_stats (id, run_id, stats_json)
```

---

## 8. Fluxo Principal do Usuário

```
1. Upload CSV do Profit
   → Sistema ingere, deduplica, armazena

2. Define período in-sample e out-of-sample

3. Cria um setup
   → Manual (interface) ou IA (linguagem natural)

4. Executa backtesting no in-sample

5. Analisa estatísticas e lista de operações
   → Confere operações no Profit se necessário
   → Pede interpretação da IA se quiser

6. Refina o setup (ajusta parâmetros)
   → Repete passos 4-5

7. Quando satisfeito → valida no out-of-sample
   → Se performa bem nos dois períodos: setup tem potencial
   → Se só performa no in-sample: overfitting, descarta

8. Salva setup validado para referência futura
```

---

## 9. Métricas de Sucesso do Produto

- Usuário consegue testar um setup completo em menos de 5 minutos
- Sistema detecta corretamente os sinais dos setups de referência (9.1, ABC, IFR2)
- Resultados reproduzíveis: mesmo setup, mesmo período → mesmos números sempre
- Lista de operações suficientemente detalhada para conferência no Profit

---

## 10. Próximos Passos

1. ~~**SDD**~~ ✅ — `docs/SDD.md`
2. ~~**Setups de referência**~~ ✅ — `docs/setups-referencia/`
3. **Specs** — Especificação detalhada com breakdown de tarefas e ordem de implementação
4. **Implementação** — Pipeline de ingestão → Motor de backtesting → API → Frontend

---

*Documento vivo — atualizar conforme decisões de design forem tomadas.*
