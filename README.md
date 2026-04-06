[English version here](README-EN.md)

<div align="center">

# TradeScan

**Backtester inteligente para day traders da B3**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.2-FFC832?style=flat-square&logo=duckdb&logoColor=black)](https://duckdb.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org)
[![Status](https://img.shields.io/badge/status-produção-22c55e?style=flat-square)]()

**[tradescan.klauberfischer.online](https://tradescan.klauberfischer.online)**

</div>

---

A maioria dos traders define setups sem nunca validá-los com dados históricos. O TradeScan resolve isso: importa dados do Profit (Nelogica), executa backtests com regras objetivas e entrega métricas completas — win rate, fator de lucro, drawdown, segmentação por horário e contexto de mercado.

Validação robusta via Walk-Forward e Monte Carlo incluídos. CNN 1D treinada sobre os candles históricos filtra entradas de baixa qualidade. Sem dependências de cloud, sem custo por uso.

---

## Telas

![Home](docs/screenshots/home.png)
*Landing com todos os módulos e navegação rápida.*

![Setups](docs/screenshots/setups.png)
*Biblioteca de setups com mais de 13 configurações pré-calibradas para WIN.*

![Histórico](docs/screenshots/historico.png)
*Histórico completo de runs com métricas inline, aprovação IS→OOS e acesso direto ao Monte Carlo.*

![Monte Carlo](docs/screenshots/monte-carlo-resultado.png)
*Simulação Monte Carlo: distribuição de drawdown máximo, banda de confiança da equity curve e análise automática em linguagem natural.*

---

## Funcionalidades

| Módulo | O que faz |
|---|---|
| **Dados** | Parse de CSVs do Profit com detecção automática de ticker/timeframe. Deduplicação por chave composta. Agregação multi-timeframe a partir dos dados base (1min → 5min, 15min, 60min, D, W). |
| **Setups** | Mais de 30 condições configuráveis: EMAs, IFR(2), ADX, ATR, sequência de candles, gap de abertura, horário, filtro de zonas S/R. 13 setups pré-calibrados para WIN. |
| **Backtesting** | Motor candle-a-candle com suporte a long, short e ambos. Stop/alvo em pontos, slippage, custo por contrato, múltiplas entradas por dia, filtro CNN opcional. |
| **Walk-Forward** | Janelas deslizantes de otimização + validação. Detecta overfitting antes de operar ao medir eficiência e consistência out-of-sample. |
| **Monte Carlo** | Permutação aleatória da sequência de trades em 1.000+ simulações. Retorna distribuição de drawdown máximo (P10–P99), banda de confiança da equity e probabilidade de ruin configurável. |
| **CNN — Padrões** | Rede 1D Convolucional treinada sobre os 50 candles anteriores a cada entrada. Usada como filtro no backtest: só executa se a probabilidade de ganho superar o threshold definido. |
| **Comparativo** | Compara múltiplos setups lado a lado no mesmo período histórico. |
| **Histórico** | Registro completo com aprovação de runs in-sample para liberar out-of-sample. |

---

## Como funciona — implementação técnica

### 1. Pipeline de ingestão

O parser (`backend/ingestao/parser_csv.py`) lê CSVs do Profit com suporte a múltiplos encodings (UTF-8, latin-1, cp1252) e dois formatos de exportação (com e sem cabeçalho). O timeframe é detectado automaticamente calculando a mediana dos deltas entre candles consecutivos e mapeando para os timeframes conhecidos com tolerância de ±50%.

```python
# Detecção automática de timeframe
mediana_delta = timestamps.diff().median().total_seconds()
# 60s → 1min | 300s → 5min | 900s → 15min | 3600s → 60min
```

Após ingestão, dados base são agregados para timeframes derivados via `pandas.resample()`, garantindo OHLCV correto (open=first, high=max, low=min, close=last, volume=sum).

---

### 2. Motor de indicadores

O módulo `backend/indicadores/calculos.py` enriquece cada DataFrame com 15 colunas calculadas de forma totalmente vetorizada:

| Indicador | Implementação | Detalhe |
|---|---|---|
| MM200 | SMA(200) | `min_periods=200` — retorna NaN até acumular histórico suficiente |
| MME9 | EMA(9) | `adjust=False` (fórmula recursiva, não ponderada por janela) |
| IFR(2) | RSI Wilder(2) | Suavização α=1/2 em ganhos/perdas; range 0–100 |
| ADX(14) | Wilder DM | True Range + DM+ / DM− com α=1/14; mede força da tendência |
| ATR diário | ATR(14) deslocado -1 | **Shift de 1 barra** para evitar lookahead bias no backtest |
| Gap de abertura | `open_dia − close_anterior` | Calculado no primeiro candle do pregão |
| Range acumulado % | `(max_high − min_low) / open_dia` | Expansão intradiária — detecta range esgotado |
| Tendência semanal | Resample semanal | `>+0.5%` = alta, `<−0.5%` = baixa, else lateral |
| Pavio sup/inf | `high − max(open,close)` | Métricas de qualidade do candle |

---

### 3. Detecção de sinais de entrada

`backend/backtesting/sinais.py` — função `gerar_entradas(df, setup)` — aplica as condições do setup como **máscaras booleanas vetorizadas** sobre o DataFrame inteiro:

```python
mask = pd.Series(True, index=df.index)

# Filtros de candle
if setup.range_candle_min:
    mask &= df["range_candle"] >= setup.range_candle_min

# Posição relativa a MAs
if setup.mm200_posicao == "acima":
    mask &= df["close"] > df["mm200"]

# Momentum
if setup.ifr2_max:
    mask &= df["ifr2"] <= setup.ifr2_max  # sobrevendido → long

# Janela de horário
mask &= (df.index.time >= horario_inicio) & (df.index.time <= horario_fim)

# Força de tendência
if setup.adx_min:
    mask &= df["adx"] >= setup.adx_min
```

**Detecção de sequência de candles** (`_mask_seq`): identifica N candles consecutivos com alta (close > open, high > max_high_anterior) ou baixa (close < open, low < min_low_anterior) para setups de momentum/trend-following. Inclui filtro opcional de pavio máximo como % do range do candle.

**Filtro de zonas S/R**: quando ativado, bloqueia entradas em candles que toquem os níveis percentuais do dia (±0.5%, ±1.0%, ..., ±3.0% em relação à abertura), evitando entrar em zonas de resistência/suporte.

**Preço de entrada**: calculado conforme `tipo_entrada` do setup — fechamento do candle gatilho, rompimento da máxima/mínima ou fechamento com slippage.

---

### 4. Motor de backtesting

`backend/backtesting/motor.py` executa candle-a-candle (não vetorizado — necessário para simular stop/alvo corretamente):

```
Para cada candle com sinal de entrada:
  1. Verificar limite diário de entradas
  2. Aplicar filtro CNN (opcional) → pular se prob < threshold
  3. Abrir posição: entry_price ± slippage
  4. Varrer candles seguintes:
     - (long)  low  ≤ stop_price  → stop
     - (long)  high ≥ alvo_price  → alvo
     - Mesmo candle: stop e alvo atingidos → computa stop (conservador)
  5. EOD forçado: fecha posição sem carregar overnight
```

**Alvo dinâmico**: quando `alvo_proximo_pct_dia` está ativo, o alvo é o nível percentual mais próximo (0.5%, 1.0%, ..., 3.0%) com distância mínima configurável, tornando o alvo adaptativo à volatilidade do dia.

**Contexto de cada trade**: cada operação armazena um `context_json` com tendência semanal, período do dia, tipo de gap, faixa de range acumulado, posição relativa a MM200/MME9 e valor do IFR(2) no momento da entrada — base para a segmentação dos resultados.

---

### 5. Walk-Forward Analysis

`backend/backtesting/walk_forward.py` — valida se um setup tem **robustez fora da janela de otimização**:

```
Janela 1:  IN  [Jan–Jun 2024]  OUT  [Jul 2024]
Janela 2:  IN  [Fev–Jul 2024]  OUT  [Ago 2024]
...
```

Métricas consolidadas:
- **Eficiência** = `expectância_out / expectância_in` — valores < 0.3 indicam overfitting severo
- **Consistência** = % de janelas out-of-sample com expectância positiva

Um setup com eficiência ≥ 0.6 e consistência ≥ 60% é considerado robusto para operação.

---

### 6. Monte Carlo

`backend/backtesting/monte_carlo.py` — responde a pergunta: *"se os trades tivessem chegado em outra ordem, qual seria o pior cenário?"*

```python
for _ in range(n_simulacoes):
    shuffled = np.random.permutation(resultado_pts)
    equity = np.cumsum(shuffled)
    drawdown = np.maximum.accumulate(equity) - equity
    max_drawdowns.append(drawdown.max())
```

Retorna percentis P10/P25/P50/P75/P90/P95/P99 do drawdown máximo e da equity final, além de banda de confiança (P10–P90) ao longo da sequência de trades. O P95 é o drawdown que o trader deve ser capaz de suportar psicologicamente para operar o setup.

---

### 7. CNN de Padrões (1D Convolucional)

`backend/padroes/modelo.py` — rede treinada sobre os 50 candles anteriores a cada entrada histórica para classificar se aquele padrão tem probabilidade alta de ganho.

**Arquitetura `PatternCNN`:**

```
Input: (batch, 10 features, 50 candles)
  │
  ├─ Conv1d(10→32, kernel=3) + BatchNorm + ReLU
  ├─ Conv1d(32→64, kernel=3) + BatchNorm + ReLU
  ├─ Conv1d(64→128, kernel=3) + BatchNorm + ReLU
  │
  ├─ AdaptiveAvgPool1d(1)  →  (batch, 128)
  │
  ├─ Dropout(0.3) → Linear(128→64) → ReLU
  └─ Dropout(0.2) → Linear(64→2)

Output: softmax → P(ganho)
```

**10 features por candle:** `open, high, low, close, volume_fin, mm200, mme9, ifr2, range_acumulado_pct, range_candle`

**Normalização por janela (z-score):** cada janela de 50 candles é normalizada independentemente para evitar lookahead bias — o modelo nunca vê estatísticas globais calculadas com dados futuros.

**Treinamento:**
- Labels geradas automaticamente a partir de backtests: trade com ganho → 1, perda/breakeven → 0
- Split temporal 70/15/15 (treino/validação/teste) — sem shuffle para preservar ordem cronológica
- `CrossEntropyLoss` com class weights inversamente proporcionais à frequência (compensa desbalanceamento)
- Early stopping com patience=10 épocas, monitorando F1 de validação
- Alerta automático de overfitting se `F1_treino − F1_val > 0.10`

Após treinado, o modelo fica disponível como filtro opcional no backtest: entradas com `P(ganho) < threshold` são ignoradas.

---

## Stack

```
Backend    Python 3.12 · FastAPI · DuckDB · PyTorch (CPU)
Frontend   React 18 · Vite · Recharts
Deploy     Docker · Nginx · Traefik · VPS
```

DuckDB embarcado no processo — sem container de banco, sem overhead de rede. Queries analíticas sobre séries temporais densas em milissegundos. Dados persistidos em volume Docker (`tradescan-dados`), modelos em volume separado (`tradescan-models`).

---

## Uso

```bash
# Backend
pip install -r requirements.txt
python -m backend.banco.seed
uvicorn backend.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

Acesse `http://localhost:5173`. Exporte candles do Profit em CSV, importe na tela de Dados e rode o primeiro backtest.

---

## Deploy

```bash
cp .env.prod.example .env.prod  # preencher ANTHROPIC_API_KEY
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Guia completo: [`docs/deploy-vps.md`](docs/deploy-vps.md)

---

<div align="center">

**[tradescan.klauberfischer.online](https://tradescan.klauberfischer.online)**

</div>
