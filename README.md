<div align="center">

# TradeScan

**Backtester para day traders da B3**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.2-FFC832?style=flat-square&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Status](https://img.shields.io/badge/status-produção-22c55e?style=flat-square)]()

**[tradescan.klauberfischer.online](https://tradescan.klauberfischer.online)**

</div>

---

A maioria dos traders define setups sem nunca validá-los com dados históricos. O TradeScan resolve isso: importa dados do Profit (Nelogica), executa backtests com regras objetivas e entrega métricas completas — win rate, fator de lucro, drawdown, segmentação por horário e variação do dia.

Validação robusta via Walk-Forward e Monte Carlo incluídos. Sem dependências de cloud, sem custo por uso.

---

## Funcionalidades

| | Módulo | |
|---|---|---|
| **Backtesting** | Motor vetorizado com suporte a long, short e ambos. Stop/alvo em pontos, slippage, custo por contrato, múltiplas entradas por dia. | |
| **Setups** | Mais de 30 condições configuráveis: EMAs, IFR(2), ADX, ATR, sequência de candles, gap de abertura, horário, filtro de zonas S/R. Vem com 13 setups calibrados para o WIN. | |
| **Walk-Forward** | Divide o histórico em janelas deslizantes e valida o setup fora da janela de otimização. Detecta overfitting antes de operar. | |
| **Monte Carlo** | Simula 1.000+ sequências alternativas dos trades para estimar drawdown máximo e risco de ruína com distribuição de probabilidade. | |
| **CNN — Padrões** | Treina um modelo 1D sobre os candles anteriores às entradas históricas. Pode ser usado como filtro adicional no backtest. | |
| **Comparativo** | Compara múltiplos setups lado a lado no mesmo período. | |
| **Histórico** | Registro completo de todos os backtests com aprovação de runs in-sample para liberar out-of-sample. | |

---

## Stack

```
Backend    Python 3.12 · FastAPI · DuckDB · PyTorch (CPU)
Frontend   React 18 · Vite · Recharts
Deploy     Docker · Traefik · VPS
```

DuckDB embarcado no processo — sem container de banco, sem overhead de rede. Queries analíticas sobre séries temporais densas em milissegundos.

---

## Uso

```bash
# 1. Backend
pip install -r requirements.txt
python -m backend.banco.seed
uvicorn backend.main:app --reload

# 2. Frontend
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
