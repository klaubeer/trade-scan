# SPECS — TradeScan
**Versão:** 0.1
**Data:** Abril 2026

---

## Ordem de Implementação

```
Fase 0 — Estrutura base
    ↓
Fase 1 — Ingestão de dados
    ↓
Fase 2 — Indicadores
    ↓
Fase 3 — Motor de backtesting
    ↓
Fase 4 — API FastAPI
    ↓
Fase 5 — Frontend React
    ↓
Fase 6 — Camada de IA (LangGraph)
    ↓
Fase 7 — Walk-Forward Analysis     ← depende de F3, F4, F5
Fase 8 — Monte Carlo Simulation    ← depende de F3, F4, F5
```

F7 e F8 são independentes entre si — podem ser implementadas em paralelo após F5.

---

## Fase 0 — Estrutura Base

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F0-001 | Criar estrutura de pastas conforme SDD | — | Pastas existem, `__init__.py` em cada módulo Python |
| F0-002 | `requirements.txt` com versões fixadas | — | `pip install -r requirements.txt` roda sem erro |
| F0-003 | `.env.example` com `ANTHROPIC_API_KEY` e `DB_PATH` | — | Arquivo existe, `.env` no `.gitignore` |
| F0-004 | `config.py` carregando variáveis de ambiente | F0-003 | `config.DB_PATH` e `config.ANTHROPIC_API_KEY` acessíveis |
| F0-005 | `banco/schema.py` — criação das 5 tabelas DuckDB | F0-004 | Executar `python -m backend.banco.schema` cria o `.db` com as tabelas corretas (verificar via DuckDB CLI) |
| F0-006 | `banco/conexao.py` — context manager para conexão DuckDB | F0-005 | `with get_conn() as conn:` funciona sem leak de conexão |

---

## Fase 1 — Ingestão de Dados

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F1-001 | `ingestao/parser_csv.py` — ler CSV do Profit em memória | F0-006 | Dado um CSV válido, retorna DataFrame com colunas normalizadas (`ticker, timeframe, datetime, open, high, low, close, volume_fin, qty`) |
| F1-002 | Detecção automática de ticker e timeframe | F1-001 | Dado CSV do WIN 5min, `detectar_ticker_timeframe(df)` retorna `('WIN', '5min')` sem input do usuário |
| F1-003 | Validação de formato do CSV | F1-001 | CSVs com colunas faltando ou tipos errados levantam `ErroIngestao` com mensagem clara |
| F1-004 | `ingestao/deduplicacao.py` — upsert por `(ticker, timeframe, datetime)` | F1-001 | Reimportar o mesmo CSV não duplica registros; retorna contagem de inseridos vs duplicados |
| F1-005 | `ingestao/agregacao.py` — agregação OHLCV para timeframes derivados | F1-004 | Dado base 1min, gera corretamente 5min, 15min, 60min, D, W. Verificar com 3 candles conhecidos manualmente |
| F1-006 | Rota `POST /api/ingestao/upload` | F1-004, F1-005 | Aceita multipart CSV, persiste dados, retorna `{ ticker, timeframe, candles_inseridos, candles_duplicados, periodo }` |

### Regras de agregação OHLCV

```
open  = primeiro open do período
high  = max(high) do período
low   = min(low) do período
close = último close do período
volume_fin = sum(volume_fin) do período
qty   = sum(qty) do período
```

Agrupamento semanal: semana começa na segunda-feira.
Agrupamento diário: session = pregão B3 (09:00 às 17:30, sem overnight).

---

## Fase 2 — Indicadores

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F2-001 | `indicadores/calculos.py` — MM200 (SMA 200) | F1-004 | `calcular_mm200(df)` retorna série com NaN nos primeiros 199 candles |
| F2-002 | MME9 (EMA 9) | F1-004 | `calcular_mme9(df)` retorna série correta (verificar contra cálculo manual ou TradingView) |
| F2-003 | IFR(2) — RSI 2 períodos | F1-004 | `calcular_ifr2(df)` retorna valores entre 0-100; verificar valor conhecido contra TradingView |
| F2-004 | Gap de abertura (pontos) | F1-005 | `calcular_gap(df)` retorna diferença entre `open` do primeiro candle do dia e `close` do último candle do dia anterior |
| F2-005 | Range acumulado do dia (%) | F1-004 | `calcular_range_acumulado(df)` = `(max_high_desde_abertura - min_low_desde_abertura) / abertura_dia * 100` |
| F2-006 | Direção do primeiro candle | F1-005 | `calcular_primeiro_candle(df, timeframe='15min')` retorna `'alta'` ou `'baixa'` por pregão |
| F2-007 | Tendência semanal | F1-005 | `calcular_tendencia_semanal(df)` retorna `'alta'`, `'baixa'` ou `'lateral'` por semana. Lateral = variação < 0.5% |
| F2-008 | Função `enriquecer_dataframe(df)` | F2-001..F2-007 | Recebe DataFrame de candles, retorna com todas as colunas de indicadores adicionadas |

---

## Fase 3 — Motor de Backtesting

Feature spec completo: `docs/features/backtesting/SPEC.md`

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F3-001 | `schemas/modelos.py` — `SetupParams` Pydantic completo | F0-001 | Serialização/deserialização JSON sem perda; validação de campos obrigatórios |
| F3-002 | `backtesting/sinais.py` — geração de array de entradas | F2-008, F3-001 | Dado um `SetupParams` e um DataFrame enriquecido, retorna array booleano de sinais de entrada correto para cada condição isoladamente (testes unitários por condição) |
| F3-003 | Filtro de horário e limite diário de entradas | F3-002 | Sinais fora do horário = False; após `max_entradas_dia` no mesmo pregão = False |
| F3-004 | Geração de sinal de saída forçada (fim do pregão) | F3-002 | Array de saída = True no último candle antes do `horario_fim` para posições abertas |
| F3-005 | `backtesting/motor.py` — execução via vectorbt | F3-002..F3-004 | `executar_backtest(setup, periodo_inicio, periodo_fim)` retorna objeto com trades e stats; reproduzível (mesmo input → mesmo output) |
| F3-006 | Conversão pontos → fração para sl_stop/tp_stop | F3-005 | `stop_pts=25` com `entry_price=125000` → `sl_stop=25/125000=0.0002`; verificar com 2 trades conhecidos |
| F3-007 | `backtesting/estatisticas.py` — métricas adicionais | F3-005 | Calcular: sequências de gains/losses, segmentação por contexto (tendência semanal, período do dia, gap, range acumulado) |
| F3-008 | Persistência de run + trades + stats no DuckDB | F3-005, F3-007 | Após execução, registros existem nas 3 tabelas; re-execução cria novo run (não sobrescreve) |
| F3-009 | Bloqueio out-of-sample sem in-sample aprovado | F3-008 | `executar_backtest` com `sample_type='out_of_sample'` sem run in-sample aprovado levanta `ErroValidacao` |
| F3-010 | Validação dos 3 setups de referência | F3-005 | Setup 9.1, ABC e IFR2 configurados no período Jan-Mar 2024 (com dados reais) geram resultados plausíveis e reproduzíveis |

---

## Fase 4 — API FastAPI

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F4-001 | `main.py` — app FastAPI com CORS para localhost | F0-004 | `uvicorn backend.main:app` sobe sem erro; `/docs` acessível |
| F4-002 | Rotas de setups (GET, POST, DELETE) | F3-001 | CRUD completo testado via `/docs` |
| F4-003 | Rota `POST /api/backtesting/executar` | F3-008 | Recebe `BacktestRequest`, executa, retorna resultado completo com trades e stats |
| F4-004 | Rota `GET /api/backtesting/runs/{run_id}` | F3-008 | Retorna run existente do DuckDB |
| F4-005 | Rota `GET /api/backtesting/comparativo` | F3-008 | Dado lista de `setup_ids` e período, retorna métricas principais de cada setup lado a lado |
| F4-006 | Rota `POST /api/ingestao/upload` | F1-006 | Integrada ao app principal |
| F4-007 | Tratamento de erros padronizado | F4-001 | Todos os erros retornam `{ erro: string, detalhe: string }` com status HTTP adequado |

---

## Fase 5 — Frontend React

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F5-001 | Scaffold Vite + React, todas as deps locais | F0-001 | `npm run dev` sobe; `npm run build` gera bundle sem CDN externo |
| F5-002 | Cliente HTTP configurado (baseURL = localhost) | F5-001 | Requisições chegam ao backend; erros exibidos na UI |
| F5-003 | Página Ingestão — upload de CSV com feedback | F1-006, F5-002 | Upload mostra spinner, depois exibe `{ candles_inseridos, candles_duplicados, periodo }` |
| F5-004 | Página Setups — formulário de criação | F4-002, F5-002 | Todos os campos do `SetupParams` editáveis; submit cria setup no backend |
| F5-005 | Página Backtesting — seleção de setup/período e execução | F4-003, F5-002 | Selecionar setup + período + sample_type → botão executar → exibe métricas globais |
| F5-006 | Componente MetricasGlobais | F5-005 | Exibe: total ops, win rate, payoff, expectância, P&L, fator de lucro, drawdown máx, maior sequência |
| F5-007 | Componente EquityCurve (Recharts) | F5-005 | Linha de equity por data, eixo X = datas, eixo Y = P&L acumulado em pts |
| F5-008 | Componente Histograma (Recharts) | F5-005 | Distribuição de resultados por operação em pts |
| F5-009 | Componente TabelaOperacoes | F5-005 | Tabela paginada com todos os campos do trade; botão exportar CSV |
| F5-010 | Segmentação por contexto (tabs ou accordion) | F5-005 | Métricas por: tendência semanal / período do dia / gap / range acumulado |
| F5-011 | Página Comparativo | F4-005, F5-002 | Selecionar N setups + período → tabela comparativa com highlight do melhor por métrica |

---

## Fase 6 — Camada de IA

Feature spec completo: `docs/features/agente-ia/SPEC.md`

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F6-001 | `agente/grafo.py` — estrutura do grafo LangGraph | F4-003 | Grafo compilado sem erro; nós definidos: `parse_intent`, `formulate_setup`, `run_backtest`, `interpret_results`, `suggest_refinements` |
| F6-002 | Nó `parse_intent` — extrair intenção do texto livre | F6-001 | Dado "quero testar compra no rompimento quando o candle tem mais de 50 pontos", extrai intenção estruturada |
| F6-003 | Nó `formulate_setup` — montar `SetupParams` via LLM | F6-002 | Output validado contra `SetupParams` Pydantic antes de prosseguir; inválido = pede esclarecimento |
| F6-004 | Nó `run_backtest` — tool call para o motor | F6-003, F3-005 | Chama `executar_backtest` e passa resultado adiante no estado do grafo |
| F6-005 | Nó `interpret_results` — interpretação com guardrails | F6-004 | Output nunca contém afirmação de que "vai funcionar"; sempre menciona limitações estatísticas; validado por checklist no código |
| F6-006 | Nó `suggest_refinements` — sugestões de variação | F6-005 | Retorna lista de até 3 variações de parâmetros como `SetupParams` completos |
| F6-007 | Rota `POST /api/agente/explorar` (SSE streaming) | F6-001..F6-006 | Frontend recebe steps do agente em tempo real via Server-Sent Events |
| F6-008 | Rota `POST /api/agente/interpretar` | F6-005 | Dado `run_id` existente, retorna interpretação + sugestões |
| F6-009 | Frontend — chat simples para modo exploração | F6-007, F5-002 | Campo de texto + botão → exibe steps do agente conforme chegam via SSE |

---

---

## Fase 7 — Walk-Forward Analysis

Feature spec completo: `docs/features/walk-forward/SPEC.md`

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F7-001 | `backtesting/walk_forward.py` — gerar janelas dado período e tamanhos | F3-005 | Dado período 2023-01 a 2024-12, janela_otim=6m, janela_valid=1m, step=1m → gera 18 janelas corretamente (verificar datas) |
| F7-002 | Executar backtest em cada janela (otimização + validação) | F7-001 | Cada janela tem 2 runs no DuckDB: um in_sample e um out_of_sample |
| F7-003 | Calcular eficiência e consistência | F7-002 | `eficiência = média(expectância_out) / média(expectância_in)` ; `consistência = % janelas out com expectância > 0` |
| F7-004 | Equity curve out-of-sample composta | F7-002 | Concatenar apenas os trades dos períodos de validação de cada janela em ordem cronológica |
| F7-005 | Persistência em `walk_forward_runs` e `walk_forward_janelas` | F7-003, F7-004 | Tabelas populadas corretamente com FKs válidas para backtest_runs |
| F7-006 | Rota `POST /api/walk-forward/executar` | F7-005 | Execução completa via API; resposta inclui janelas + métricas consolidadas |
| F7-007 | Rota `GET /api/walk-forward/{wf_run_id}` | F7-005 | Retorna run com janelas detalhadas |
| F7-008 | Componente `WalkForwardChart` (frontend) | F7-006, F5-001 | Gráfico de barras: expectância in vs out por janela + linha de eficiência |
| F7-009 | Página Walk-Forward integrada ao frontend | F7-008 | Usuário seleciona setup + parâmetros → executa → vê resultados |

---

## Fase 8 — Monte Carlo Simulation

Feature spec completo: `docs/features/monte-carlo/SPEC.md`

| ID | Descrição | Deps | DoD |
|----|-----------|------|-----|
| F8-001 | `backtesting/monte_carlo.py` — embaralhar trades e recalcular equity/drawdown | F3-005 | Dado lista de N trades, `simular(trades, n=1000)` retorna arrays de `max_drawdown` e `pnl_final` com len=1000 |
| F8-002 | Cálculo de percentis (P10, P25, P50, P75, P90, P95, P99) | F8-001 | Valores corretos verificados com numpy percentile em dados sintéticos |
| F8-003 | Banda de confiança para equity curve | F8-001 | Para cada posição i na sequência, calcular P10 e P90 do equity acumulado across simulações |
| F8-004 | Probabilidade de ruin configurável | F8-002 | `P(drawdown > threshold)` = contagem correta de simulações acima do threshold / n_simulacoes |
| F8-005 | Persistência em `monte_carlo_runs` | F8-002, F8-003 | `resultado_json` contém: percentis_drawdown, percentis_pnl, banda_equity (lista de {i, p10, p50, p90}) |
| F8-006 | Rota `POST /api/monte-carlo/executar` | F8-005 | Aceita `{ run_id, n_simulacoes }`, retorna resultado completo |
| F8-007 | Rota `GET /api/monte-carlo/{mc_run_id}` | F8-005 | Retorna simulação salva |
| F8-008 | Componente `MonteCarloChart` (frontend) | F8-006, F5-001 | Dois gráficos: (1) banda P10-P90 da equity curve + mediana; (2) histograma de drawdown máximo com linhas de percentil |
| F8-009 | Exibir probabilidade de ruin na UI | F8-008 | Input de threshold → atualiza P(drawdown > X%) em tempo real (cálculo local, sem nova requisição) |

---

## Resumo de Dependências Críticas

```
F0 → F1 → F2 → F3 → F4 → F5
                              ↓         ↓
                             F7        F8
                 F3 ←→ F6
```

O backtesting (F3) precisa estar completo e testado antes do frontend (F5) e da IA (F6).
F7 e F8 dependem de F3 (motor) + F4 (API) + F5 (frontend base) e são independentes entre si.

---

## Definition of Done Global

Nenhuma fase é considerada concluída até:
- [ ] Código no repositório (sem arquivos temporários)
- [ ] Sem erros de lint (`ruff check backend/`)
- [ ] Funções críticas com pelo menos 1 teste unitário (`pytest`)
- [ ] `CONTEXT.md` atualizado com status da fase

---

## Estimativa de Complexidade

| Fase | Complexidade | Motivo |
|---|---|---|
| F0 | Baixa | Scaffold padrão |
| F1 | Média | Parsing de CSV com detecção automática + agregação correta de OHLCV |
| F2 | Baixa-Média | Cálculos conhecidos; atenção à lógica de sessão diária/semanal |
| F3 | **Alta** | Núcleo do produto; conversão pontos→fração, lógica de sinais composta, saída forçada |
| F4 | Baixa | Wrappers de API sobre lógica já pronta |
| F5 | Média | Charts + tabelas; sem lógica de negócio |
| F6 | **Alta** | Fluxo multi-nó, guardrails, streaming SSE |
| F7 | Média | Orquestração de múltiplos runs; cuidado com datas de janelas |
| F8 | Média | Numpy puro; complexidade está na visualização da banda de confiança |
