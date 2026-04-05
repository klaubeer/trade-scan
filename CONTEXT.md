# CONTEXT.md

## STATUS GERAL DO PROJETO

- **Fase atual:** PRODUÇÃO
- **Milestone atual:** App deployado em https://tradescan.klauberfischer.online — pronto para uso com dados reais
- **Última decisão relevante:** Deploy via Docker + Traefik na VPS klauberfischer.online; nginx com `client_max_body_size 50M` para uploads de CSV; 23 setups de referência seedados (5 scalping × long/short + 5 tendência × long/short + 3 clássicos)
- **Próximo passo:** Importar CSV do WIN e rodar primeiros backtests com os setups de referência

---

## FEATURES

| Status | Feature | Observações |
|--------|---------|-------------|
| ✅ DONE | Ingestão de CSV (Profit) | `backend/ingestao/` — parser, deduplicação, agregação |
| ✅ DONE | Indicadores calculados | `backend/indicadores/calculos.py` — MM200, MME9, IFR2, gap, range, tendência |
| ✅ DONE | Definição de Setups | `backend/schemas/modelos.py` + API CRUD |
| ✅ DONE | Motor de Backtesting | `backend/backtesting/motor.py` — pandas/numpy puro |
| ✅ DONE | Estatísticas e Resultados | `backend/backtesting/estatisticas.py` — métricas + segmentação |
| ✅ DONE | Lista de Operações | Frontend `TabelaOperacoes.jsx` — paginada, exportável |
| ✅ DONE | Comparativo de Setups | `frontend/src/paginas/Comparativo.jsx` |
| ✅ DONE | Camada de IA | `backend/agente/` — LangGraph, guardrails, SSE streaming |
| ✅ DONE | Frontend React | Vite + React, 7 páginas, Recharts, offline |
| ✅ DONE | Walk-Forward Analysis | `backend/backtesting/walk_forward.py` + página frontend |
| ✅ DONE | Monte Carlo Simulation | `backend/backtesting/monte_carlo.py` + página frontend |
| ✅ DONE | CNN 1D — Reconhecimento de Padrões | `backend/padroes/` — pipeline, modelo, treino, inferência + frontend `/cnn-padroes` |
| ✅ DONE | Edição de Setups | `PUT /api/setups/{id}` + botão ✎ na tabela de setups |
| ✅ DONE | Seed de Setups de Referência | `backend/banco/seed.py` — 9.1 Larry Williams, ABC, IFR2 |
| ✅ DONE | Segmentação Variação do Dia | 14 faixas direcionais (−3% a +3%) em `sinais.py` + `estatisticas.py` |
| ✅ DONE | Parser CSV sem cabeçalho | `ingestao/parser_csv.py` detecta formato Profit automático |
| ✅ DONE | Setup Sequência de Candles | `sequencia_candles`, `sequencia_wick_max_pct`, `alvo_proximo_pct_dia`, `alvo_minimo_pts` — detecção vetorizada em `sinais.py`, alvo dinâmico em `motor.py` |
| ✅ DONE | Filtros ADX / ATR | `adx_min` (ADX ≥ X) e `atr_fator_range` (range_dia ≥ fator×ATR_diário) em `SetupParams`; `calcular_adx`, `calcular_atr_diario`, `calcular_range_dia_pts` em `calculos.py` |
| ✅ DONE | Detecção bilateral de sequências | `gerar_entradas` retorna série assinada (+1/-1/0); SHORT detectado independentemente de LONG no modo `direcao="ambos"` |
| ✅ DONE | Separação horário entrada / fechamento | `horario_fim` = última entrada; `horario_fechamento` = fecha posições abertas (padrão 18h) |
| ✅ DONE | Filtrar zonas S/R | `sequencia_filtrar_zonas` — rejeita entrada se candle gatilho cruza nível percentual do dia (0%, ±0.5%, ±1% … ±3%) |
| ✅ DONE | Histórico de Backtests | Página `/historico` — lista todos os runs, aprovação tardia de IS, exclusão de runs não aprovados |
| ✅ DONE | Simulador de contratos | Backtesting.jsx — slider de contratos com P&L em R$ para WIN/WDO/BITFUT |

---

## DECISÕES ATIVAS — NÃO ALTERAR SEM DISCUSSÃO

- **Banco:** DuckDB embarcado, arquivo `dados/tradescan.db` — decidido Abril 2026 (ADR-001)
- **Backtesting:** vectorbt `from_signals` com sl_stop/tp_stop fracionais — decidido Abril 2026 (ADR-002)
- **IA:** LangGraph + claude-sonnet-4-6 — decidido Abril 2026 (ADR-003)
- **Frontend:** Vite + React, todas as deps bundleadas localmente (sem CDN) — decidido Abril 2026 (ADR-004)
- **in-sample/out-of-sample:** bloqueio via campo `aprovado` na tabela `backtest_runs` — decidido Abril 2026 (ADR-005)
- **Indicadores adicionais:** MME9 e IFR(2) adicionados ao escopo (além dos listados no PRD) para suportar setups de referência 9.1 e IFR2

---

## SETUPS DE REFERÊNCIA (para validação do motor)

| Setup | Arquivo | Indicadores necessários |
|---|---|---|
| 9.1 Larry Williams | docs/setups-referencia/setup-9.1-larry-williams.md | MME9 |
| ABC Price Action | docs/setups-referencia/setup-abc.md | MM200 (já no PRD) |
| IFR2 (Stormer) | docs/setups-referencia/setup-ifr2.md | IFR(2) |

---

## ARQUIVOS DO PROJETO

| Arquivo | Descrição |
|---|---|
| docs/PRD.md | Requisitos do produto |
| docs/SDD.md | Design de software (ADRs, schema, API, estrutura de pastas) |
| docs/SPECS.md | Breakdown de tarefas com IDs, deps e DoD |
| docs/features/backtesting/SPEC.md | Spec detalhado do motor de backtesting |
| docs/features/agente-ia/SPEC.md | Spec detalhado do agente LangGraph |
| docs/features/walk-forward/SPEC.md | Spec detalhado do walk-forward analysis |
| docs/features/monte-carlo/SPEC.md | Spec detalhado da simulação Monte Carlo |
| docs/features/cnn-padroes/SPEC.md | Spec detalhado do módulo CNN 1D |
| CONTEXT.md | Este arquivo — lido no início de cada sessão |
