# SDD — TradeScan
**Versão:** 0.1
**Status:** Draft
**Data:** Abril 2026

---

## 1. Decisões Arquiteturais (ADRs)

### ADR-001 — DuckDB como banco de dados principal

**Contexto:** Aplicação single-user, local/VPS, com foco em consultas analíticas sobre séries temporais de candles.

**Decisão:** DuckDB embarcado (arquivo `.db` local).

**Alternativas descartadas:**
- SQLite: sem suporte nativo a operações analíticas vetorizadas; mais lento para agregações de candles
- PostgreSQL: overhead operacional desnecessário para single-user; requer servidor separado

**Consequências:**
- Sem concorrência multi-processo (OK para single-user)
- Queries analíticas (GROUP BY, window functions) muito mais rápidas que SQLite
- Arquivo único = backup simples (copiar o `.db`)

---

### ADR-002 — vectorbt para motor de backtesting

**Contexto:** Backtesting candle a candle com regras condicionais compostas.

**Decisão:** vectorbt com modo signal-based. As condições de entrada são computadas como arrays booleanos (pandas/numpy) e passadas ao vectorbt via `from_signals`.

**Alternativas descartadas:**
- Backtrader: event-driven puro, mais lento, API verbose
- Implementação própria: retrabalho para métricas já prontas (drawdown, sharpe, etc.)
- zipline: descontinuado, focado em ações US

**Limitação conhecida:** vectorbt assume que stop/target são verificados no fechamento da barra, a menos que se use `SL_stop` e `TP_stop` com `open_trade_info`. Usaremos `Portfolio.from_signals` com `sl_stop` e `tp_stop` em fração do preço de entrada, convertendo pontos para fração on-the-fly.

**Consequências:**
- Lógica de "se stop e alvo atingidos no mesmo candle → computa stop" é o comportamento padrão do vectorbt (conservador) ✓
- Encerramento forçado no horário limite: implementado como sinal de saída explícito no array de sinais

---

### ADR-003 — LangGraph + Claude API para camada de IA

**Contexto:** Agente que interpreta linguagem natural, formula parâmetros de setup e interpreta resultados.

**Decisão:** LangGraph com nós: `parse_intent` → `formulate_setup` → `run_backtest` (tool call) → `interpret_results` → `suggest_refinements`.

**Alternativas descartadas:**
- Agente simples (prompt único): sem controle de fluxo multi-passo, difícil de testar
- LlamaIndex: menos flexível para fluxos customizados

**Modelo:** `claude-sonnet-4-6` (custo/performance balanceados para o caso de uso)

**Consequências:**
- Guardrails implementados como system prompt + validação de output no nó `interpret_results`
- LLM nunca retorna recomendação de operação em tempo real — apenas análise histórica

---

### ADR-004 — React (sem Next.js) + bundler local

**Contexto:** Frontend offline, sem dependência de CDN.

**Decisão:** Vite + React. Todas as dependências bundleadas localmente.

**Alternativas descartadas:**
- Next.js: overhead de SSR desnecessário para SPA local
- Vue/Svelte: ecossistema de charts menos maduro para o caso de uso

**Libs de visualização:** Recharts (bundleada localmente via npm).

---

### ADR-005 — Separação in-sample / out-of-sample no nível de dado

**Contexto:** Prevenir que o usuário teste acidentalmente o out-of-sample antes de finalizar o setup.

**Decisão:** `backtest_runs` registra `sample_type` ('in_sample' | 'out_of_sample'). A API bloqueia execução out-of-sample se não houver ao menos um run in-sample aprovado pelo usuário para o mesmo setup.

---

## 2. Estrutura de Pastas

```
trade-scan/
├── docs/
│   ├── PRD.md
│   ├── SDD.md
│   └── setups-referencia/
│       ├── setup-9.1-larry-williams.md
│       ├── setup-abc.md
│       └── setup-ifr2.md
├── backend/
│   ├── main.py                  # FastAPI app, rotas
│   ├── config.py                # Configurações (path do DB, etc.)
│   ├── banco/
│   │   ├── schema.py            # Criação das tabelas DuckDB
│   │   ├── conexao.py           # Gerenciamento de conexão
│   │   └── seed.py              # Popula 3 setups de referência (9.1, ABC, IFR2)
│   ├── ingestao/
│   │   ├── parser_csv.py        # Leitura e validação do CSV do Profit (c/ e s/ cabeçalho)
│   │   ├── deduplicacao.py      # Lógica de upsert por (ticker, timeframe, datetime)
│   │   └── agregacao.py         # Geração de timeframes derivados
│   ├── indicadores/
│   │   └── calculos.py          # MM200, MME9, IFR2, gap, range acumulado, variação dia, etc.
│   ├── backtesting/
│   │   ├── motor.py             # Orquestrador: recebe setup, retorna trades + stats
│   │   ├── sinais.py            # Geração de sinais + contexto (faixas de variação do dia)
│   │   ├── estatisticas.py      # Métricas + segmentação (7 faixas de range, 14 de variação)
│   │   ├── walk_forward.py      # Janelas rolantes in/out-of-sample
│   │   └── monte_carlo.py       # Simulação Monte Carlo sobre trades
│   ├── agente/
│   │   ├── grafo.py             # Definição do grafo LangGraph
│   │   ├── nos.py               # Implementação de cada nó do grafo
│   │   └── guardrails.py        # Validação de outputs do LLM
│   ├── padroes/
│   │   ├── pipeline.py          # Janelas deslizantes + normalização z-score por janela
│   │   ├── rotulos.py           # Labeling automático (backtest_trades) e manual
│   │   ├── modelo.py            # PatternCNN (3x Conv1D + AdaptiveAvgPool + MLP)
│   │   ├── treino.py            # Loop de treino, early stopping, persistência
│   │   └── inferencia.py        # Carregamento de modelo com cache LRU, predict_proba
│   └── schemas/
│       └── modelos.py           # Pydantic models (SetupParams, BacktestRequest, etc.)
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── paginas/
│       │   ├── Ingestao.jsx     # Upload de CSV
│       │   ├── Setups.jsx       # CRUD de setups
│       │   ├── Backtesting.jsx  # Execução e resultados
│       │   └── Comparativo.jsx  # Comparativo de setups
│       └── componentes/
│           ├── EquityCurve.jsx
│           ├── Histograma.jsx
│           ├── TabelaOperacoes.jsx
│           ├── MetricasGlobais.jsx
│           ├── WalkForwardChart.jsx  # Barras in/out por janela + eficiência
│           └── MonteCarloChart.jsx   # Banda P10-P90 + histograma de drawdown
├── dados/
│   └── tradescan.db             # DuckDB (gerado automaticamente)
├── .env.example
├── requirements.txt
└── CONTEXT.md
```

---

## 3. Schema DuckDB

```sql
-- Candles base e derivados
CREATE TABLE candles (
    ticker      VARCHAR NOT NULL,        -- 'WIN', 'WDO', 'BITFUT'
    timeframe   VARCHAR NOT NULL,        -- '1min', '5min', '15min', '60min', 'D', 'W'
    datetime    TIMESTAMP NOT NULL,
    open        DOUBLE NOT NULL,
    high        DOUBLE NOT NULL,
    low         DOUBLE NOT NULL,
    close       DOUBLE NOT NULL,
    volume_fin  DOUBLE,
    qty         INTEGER,
    PRIMARY KEY (ticker, timeframe, datetime)
);

-- Setups definidos pelo usuário
CREATE TABLE setups (
    id          INTEGER PRIMARY KEY,
    nome        VARCHAR NOT NULL,
    ticker      VARCHAR NOT NULL,
    params_json JSON NOT NULL,           -- SetupParams serializado
    criado_em   TIMESTAMP DEFAULT NOW()
);

-- Execuções de backtesting
CREATE TABLE backtest_runs (
    id              INTEGER PRIMARY KEY,
    setup_id        INTEGER REFERENCES setups(id),
    periodo_inicio  DATE NOT NULL,
    periodo_fim     DATE NOT NULL,
    sample_type     VARCHAR NOT NULL,    -- 'in_sample' | 'out_of_sample'
    aprovado        BOOLEAN DEFAULT FALSE,
    criado_em       TIMESTAMP DEFAULT NOW()
);

-- Operações individuais de cada run
CREATE TABLE backtest_trades (
    id              INTEGER PRIMARY KEY,
    run_id          INTEGER REFERENCES backtest_runs(id),
    datetime        TIMESTAMP NOT NULL,
    direcao         VARCHAR NOT NULL,    -- 'long' | 'short'
    preco_entrada   DOUBLE NOT NULL,
    preco_saida     DOUBLE NOT NULL,
    resultado       VARCHAR NOT NULL,    -- 'gain' | 'loss' | 'breakeven'
    resultado_pts   DOUBLE NOT NULL,
    contexto_json   JSON                 -- tendência semanal, gap, range acumulado, etc.
);

-- Estatísticas consolidadas por run
CREATE TABLE backtest_stats (
    id          INTEGER PRIMARY KEY,
    run_id      INTEGER REFERENCES backtest_runs(id),
    stats_json  JSON NOT NULL
);

-- Walk-forward: configuração de uma análise completa
CREATE TABLE walk_forward_runs (
    id                  INTEGER PRIMARY KEY,
    setup_id            INTEGER REFERENCES setups(id),
    periodo_inicio      DATE NOT NULL,
    periodo_fim         DATE NOT NULL,
    janela_otim_meses   INTEGER NOT NULL,   -- ex: 6
    janela_valid_meses  INTEGER NOT NULL,   -- ex: 1
    step_meses          INTEGER NOT NULL,   -- ex: 1
    eficiencia          DOUBLE,             -- expectância_out / expectância_in
    consistencia        DOUBLE,             -- % janelas out-of-sample positivas
    criado_em           TIMESTAMP DEFAULT NOW()
);

-- Walk-forward: resultado de cada janela individual
CREATE TABLE walk_forward_janelas (
    id              INTEGER PRIMARY KEY,
    wf_run_id       INTEGER REFERENCES walk_forward_runs(id),
    janela_num      INTEGER NOT NULL,
    otim_inicio     DATE NOT NULL,
    otim_fim        DATE NOT NULL,
    valid_inicio    DATE NOT NULL,
    valid_fim       DATE NOT NULL,
    run_id_otim     INTEGER REFERENCES backtest_runs(id),
    run_id_valid    INTEGER REFERENCES backtest_runs(id)
);

-- Monte Carlo: resultado de uma simulação sobre um backtest_run
CREATE TABLE monte_carlo_runs (
    id              INTEGER PRIMARY KEY,
    run_id          INTEGER REFERENCES backtest_runs(id),
    n_simulacoes    INTEGER NOT NULL,
    resultado_json  JSON NOT NULL,   -- percentis de drawdown e P&L, banda de confiança
    criado_em       TIMESTAMP DEFAULT NOW()
);

-- CNN: rótulos de treino (gain=1 / loss=0)
CREATE TABLE rotulos (
    id          INTEGER PRIMARY KEY,
    ticker      VARCHAR NOT NULL,
    timeframe   VARCHAR NOT NULL,
    datetime    TIMESTAMP NOT NULL,
    label       INTEGER NOT NULL,          -- 0 ou 1
    fonte       VARCHAR DEFAULT 'backtest', -- 'backtest' | 'manual'
    run_id      INTEGER REFERENCES backtest_runs(id),
    criado_em   TIMESTAMP DEFAULT NOW(),
    UNIQUE (ticker, timeframe, datetime, run_id)
);

-- CNN: modelos treinados e seus metadados
CREATE TABLE ml_models (
    id                   VARCHAR PRIMARY KEY,  -- UUID
    nome                 VARCHAR NOT NULL,
    ticker               VARCHAR NOT NULL,
    timeframe            VARCHAR NOT NULL,
    n_features           INTEGER NOT NULL,
    seq_len              INTEGER NOT NULL,
    train_periodo_inicio TIMESTAMP,
    train_periodo_fim    TIMESTAMP,
    test_periodo_inicio  TIMESTAMP,
    test_periodo_fim     TIMESTAMP,
    metrics_json         JSON,
    config_json          JSON,
    model_path           VARCHAR NOT NULL,
    criado_em            TIMESTAMP DEFAULT NOW()
);
```

---

## 4. Contratos de API (FastAPI)

### Ingestão
```
POST /api/ingestao/upload
  Body: multipart/form-data { arquivo: CSV }
  Response: { ticker, timeframe, candles_inseridos, candles_duplicados, periodo }
```

### Setups
```
GET    /api/setups               → lista todos os setups
POST   /api/setups               → cria novo setup (body: SetupParams)
GET    /api/setups/{id}          → detalhe
PUT    /api/setups/{id}          → atualiza setup (body: SetupParams)
DELETE /api/setups/{id}          → remove
PUT    /api/setups/{id}/aprovar  → aprova run in-sample
```

### Backtesting
```
POST /api/backtesting/executar
  Body: { setup_id, periodo_inicio, periodo_fim, sample_type, slippage, custo_pt }
  Response: { run_id, stats, trades[] }

GET /api/backtesting/runs/{run_id}   → resultado de um run
GET /api/backtesting/comparativo     → query: setup_ids[], periodo_inicio, periodo_fim
```

### Walk-Forward
```
POST /api/walk-forward/executar
  Body: { setup_id, periodo_inicio, periodo_fim,
          janela_otim_meses, janela_valid_meses, step_meses }
  Response: { wf_run_id, janelas[], eficiencia, consistencia }

GET /api/walk-forward/{wf_run_id}    → resultado completo com janelas
```

### Monte Carlo
```
POST /api/monte-carlo/executar
  Body: { run_id, n_simulacoes }     -- run_id de um backtest_run existente
  Response: { mc_run_id, percentis_drawdown, percentis_pnl, banda_equity }

GET /api/monte-carlo/{mc_run_id}     → resultado de uma simulação salva
```

### Agente IA
```
POST /api/agente/explorar
  Body: { descricao_natural: string }
  Response: stream (SSE) com steps do agente + resultado final

POST /api/agente/interpretar
  Body: { run_id: int }
  Response: { interpretacao: string, sugestoes: SetupParams[] }
```

### CNN — Reconhecimento de Padrões
```
POST /api/cnn/rotular/run/{run_id}   → gera rótulos automáticos de um backtest_run
POST /api/cnn/rotular                → insere rótulo manual { ticker, timeframe, datetime, label }
GET  /api/cnn/rotulos/resumo         → contagem de rótulos disponíveis (ticker, timeframe)
POST /api/cnn/treinar                → treina PatternCNN { ticker, timeframe, nome, run_id?, config? }
GET  /api/cnn/modelos                → lista modelos treinados
POST /api/cnn/prever                 → predict_proba { model_id, ticker, timeframe, datetime_fim }
```

---

## 5. SetupParams — Modelo Pydantic

```python
class SetupParams(BaseModel):
    nome: str
    ticker: Literal["WIN", "WDO", "BITFUT"]
    timeframe: Literal["1min", "5min", "15min"]
    direcao: Literal["long", "short", "ambos"]

    # Condições de entrada (todas opcionais — None = não aplicar filtro)
    range_candle_min: Optional[float] = None        # pontos
    pavio_total_max: Optional[float] = None          # pontos
    pavio_superior_max: Optional[float] = None       # pontos
    pavio_inferior_max: Optional[float] = None       # pontos
    mm200_posicao: Optional[Literal["acima", "abaixo"]] = None
    range_acumulado_max_pct: Optional[float] = None  # % do dia
    gap_abertura_min: Optional[float] = None         # pontos
    primeiro_candle_direcao: Optional[Literal["alta", "baixa"]] = None
    tendencia_semanal: Optional[Literal["alta", "baixa", "qualquer"]] = None

    # Execução
    tipo_entrada: Literal["fechamento_gatilho", "rompimento_fechamento",
                           "rompimento_maxima", "rompimento_minima"]
    stop_pts: float
    alvo_pts: float                   # alvo primário
    alvo2_pts: Optional[float] = None # alvo secundário opcional

    # Filtros de horário
    horario_inicio: time = time(9, 0)
    horario_fim: time = time(17, 30)
    max_entradas_dia: int = 1

    # Custos
    slippage_pts: float = 0.0
    custo_por_ponto: float = 0.20     # WIN padrão
```

---

## 6. Fluxo de Backtesting (Motor)

```
1. Carregar candles do DuckDB para o período → DataFrame pandas
2. Calcular indicadores (MM200, gap, range acum., tendência semanal) → colunas adicionais
3. Gerar array de sinais de entrada:
   - Para cada candle: avaliar todas as condições do setup → bool
   - Aplicar filtro de horário
   - Aplicar limite de entradas por dia
4. Gerar array de sinais de saída forçada (horário limite)
5. Converter stop/alvo de pontos para fração do preço de entrada
6. Executar vectorbt Portfolio.from_signals(...)
7. Extrair trades do portfolio → enriquecer com contexto_json
8. Calcular métricas adicionais (sequências, segmentação por contexto)
9. Persistir run + trades + stats no DuckDB
10. Retornar resultado
```

---

## 7. Considerações de Segurança

| Superfície | Risco | Mitigação |
|---|---|---|
| Upload CSV | Path traversal, arquivo malicioso | Validar extensão + estrutura do CSV antes de processar; não salvar arquivo no disco (processar em memória) |
| API local | SSRF, acesso não autorizado | Bind apenas em `127.0.0.1` por padrão; sem autenticação (single-user local) |
| Claude API key | Exposição de credencial | Carregada via `.env`, nunca commitada; `.env` no `.gitignore` |
| Queries DuckDB | SQL injection | Usar parâmetros posicionais do DuckDB, nunca f-string em queries |
| LLM output | Prompt injection via dados do usuário | Sanitizar nomes de setups/descrições antes de passar ao LLM; outputs do LLM validados contra schema Pydantic antes de execução |

---

## 8. Versões Fixadas (principais)

| Lib | Versão |
|---|---|
| Python | 3.12 |
| FastAPI | 0.115.x |
| DuckDB | 1.2.x |
| vectorbt | 0.26.x |
| LangGraph | 0.3.x |
| anthropic (SDK) | 0.40.x |
| React | 18.x |
| Recharts | 2.x |
| Vite | 5.x |

---

*Documento vivo — atualizar conforme implementação avança.*
