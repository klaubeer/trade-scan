<div align="center">

# TradeScan

**Backtester inteligente para day traders da B3**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.2-FFC832?style=flat-square&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Claude](https://img.shields.io/badge/Claude-Sonnet_4.6-D97757?style=flat-square&logo=anthropic&logoColor=white)](https://anthropic.com)
[![Status](https://img.shields.io/badge/status-produção-22c55e?style=flat-square)]()

**[tradescan.klauberfischer.online](https://tradescan.klauberfischer.online)**

</div>

---

## O problema

Day traders brasileiros definem setups de entrada e saída no mercado, mas raramente conseguem validá-los com dados históricos de forma objetiva. As ferramentas disponíveis são caras, genéricas, e não falam a linguagem do trader da B3 — WIN, WDO, BITFUT, candles em pontos, custo por contrato, lógica de IFR(2) e MME9.

O resultado: setups são operados na fé, sem saber se têm edge real.

## A solução

O TradeScan transforma qualquer setup descrito em regras objetivas (IF-THEN) em um backtest completo contra dados históricos reais exportados do Profit (Nelogica). Em segundos você obtém win rate, fator de lucro, drawdown máximo, segmentação por horário e variação do dia — e uma análise do agente de IA explicando o que os números significam.

---

## Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| **Ingestão de dados** | Upload direto de CSVs exportados do Profit. Deduplicação automática, agregação multi-timeframe. |
| **Motor de backtesting** | Execução vetorizada com pandas/numpy. Suporte a long/short/ambos, múltiplas entradas por dia, stop e alvo em pontos, slippage, custo por contrato. |
| **Setups parametrizados** | Mais de 30 condições de entrada configuráveis: EMAs, IFR(2), ADX, ATR, sequência de candles, pavios, gap de abertura, horário, tendência semanal, filtro de zonas S/R. |
| **Walk-Forward Analysis** | Validação temporal com janelas deslizantes para detectar overfitting. Compara in-sample vs out-of-sample automaticamente. |
| **Monte Carlo** | Simulação de 1.000+ cenários sobre os trades reais para estimar risco de ruína e drawdown máximo com distribuição de probabilidade. |
| **CNN 1D — Padrão de Candles** | Treina um modelo de deep learning sobre os padrões visuais dos candles antes de entradas históricas. O modelo filtra os próximos sinais em tempo real. |
| **Agente de IA** | Análise em linguagem natural dos resultados via Claude Sonnet 4.6 + LangGraph. Identifica edge, pontos fracos e sugere otimizações. |
| **Comparativo de setups** | Tabela lado a lado de múltiplos setups no mesmo período para comparação objetiva de métricas. |
| **Simulador de contratos** | Slider de contratos com P&L projetado em R$ para WIN, WDO e BITFUT. |

---

## Setups incluídos

O TradeScan já vem com 23 setups prontos para uso imediato:

**Scalping (WIN 1min / 5min)**
- EMA Crossover + Filtro de Tendência
- MACD Momentum Scalp
- Liquidity Sweep Reclaim
- Mean Reversion IFR(2)
- Price Action + Volume (proxy tape reading)

**Tendência (WIN 5min / 15min / 60min)**
- Pullback EMA20 + ADX (Holy Grail)
- Break of Structure (BoS)
- Dual EMA Crossover + Pullback
- Donchian Channel Breakout (Turtle System adaptado)
- ABCD Pattern + VWAP

**Referência clássica (WIN 15min)**
- 9.1 Larry Williams
- ABC Price Action
- IFR2 Stormer

> Todos calibrados para o WIN com amplitude média de 3.485 pontos/dia. Cada estratégia tem versão long e short independente.

---

## Stack

```
Backend    Python 3.12 + FastAPI + DuckDB + LangGraph + Claude API + PyTorch (CPU)
Frontend   Vite + React 18 + Recharts — 100% offline, sem CDN
Deploy     Docker + Traefik + VPS própria
```

---

## Rodando localmente

**Pré-requisitos:** Python 3.12+, Node 20+

```bash
# Backend
pip install -r requirements.txt
python -m backend.banco.seed          # popula os setups de referência
uvicorn backend.main:app --reload

# Frontend (outro terminal)
cd frontend
npm install
npm run dev
```

Acesse: `http://localhost:5173`

---

## Deploy em produção

Ver [`docs/deploy-vps.md`](docs/deploy-vps.md) para o guia completo com Docker + Traefik.

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

---

## Como usar

1. **Importe seus dados** — exporte candles do Profit em CSV e faça upload na tela de Ingestão
2. **Escolha ou crie um setup** — configure timeframe, indicadores, stop e alvo em pontos
3. **Rode o backtest** — selecione o período in-sample e execute
4. **Analise com IA** — peça ao agente para interpretar os resultados em linguagem natural
5. **Valide com Walk-Forward** — confirme que o edge se mantém fora da janela de otimização
6. **Simule o risco** — rode Monte Carlo para ver a distribuição de drawdown e risco de ruína
7. **Treine o padrão visual** — use CNN para filtrar entradas com base nos padrões de candles

---

<div align="center">

Feito para traders que operam com método, não com achismo.

**[tradescan.klauberfischer.online](https://tradescan.klauberfischer.online)**

</div>
