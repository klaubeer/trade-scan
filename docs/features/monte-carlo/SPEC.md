# SPEC — Monte Carlo Simulation

## O que faz
Dado o conjunto de trades de um backtest já executado, embaralha a sequência aleatoriamente N vezes para produzir a distribuição real de drawdowns e equity curves possíveis. Responde a pergunta: "qual drawdown eu devo esperar suportar, não apenas qual aconteceu historicamente?"

## Status atual
📋 PLANNED

## Subtarefas

| ID | Descrição | Status | DoD |
|----|-----------|--------|-----|
| F8-001 | Simulação core — embaralhar e recalcular | 📋 PLANNED | 1.000 simulações em < 2s para 200 trades |
| F8-002 | Percentis de drawdown e P&L | 📋 PLANNED | Verificados com numpy em dados sintéticos |
| F8-003 | Banda de confiança da equity curve | 📋 PLANNED | Arrays P10, P50, P90 por posição |
| F8-004 | Probabilidade de ruin | 📋 PLANNED | P(drawdown > X%) correto |
| F8-005 | Persistência | 📋 PLANNED | resultado_json no DuckDB |
| F8-006 | Rota POST executar | 📋 PLANNED | Resposta completa em < 5s |
| F8-007 | Rota GET resultado | 📋 PLANNED | Retorna simulação salva |
| F8-008 | MonteCarloChart (frontend) | 📋 PLANNED | 2 gráficos: banda equity + histograma drawdown |
| F8-009 | Probabilidade de ruin interativa | 📋 PLANNED | Input threshold → P(ruin) atualiza sem nova req. |

## Decisões específicas desta feature

- **Embaralhamento da sequência, não reamostragem com reposição** — usar `numpy.random.shuffle` (sem reposição) em vez de bootstrap. Motivo: queremos explorar a ordem dos mesmos trades reais, não gerar trades sintéticos. Reposição poderia criar sequências com o mesmo trade repetido muitas vezes, distorcendo o resultado.

- **n_simulacoes padrão = 1.000** — suficiente para percentis estáveis. 10.000 é o máximo permitido; acima disso o tempo de resposta fica impraticável para o frontend.

- **Computação em numpy puro** — sem pandas no loop interno. Equity curve e drawdown calculados como operações vetorizadas em arrays numpy. Meta: 1.000 simulações de 200 trades em < 1s.

- **Banda de confiança armazenada como lista de objetos** — armazenar no `resultado_json` apenas P10, P50 e P90 por posição (não todas as 1.000 curvas). Isso mantém o JSON em tamanho razoável (~3 arrays de comprimento N).

- **Probabilidade de ruin calculada no frontend** — dado que o frontend já tem o array de `max_drawdowns` das N simulações, calcular `P(drawdown > threshold)` é uma filtragem local. Evita requisição extra ao backend.

## Algoritmo core

```python
import numpy as np

def simular_monte_carlo(resultado_pts: list[float], n_simulacoes: int = 1000) -> dict:
    trades = np.array(resultado_pts)
    n = len(trades)

    max_drawdowns = np.empty(n_simulacoes)
    pnl_finais    = np.empty(n_simulacoes)
    # banda: shape (n_simulacoes, n) — equity acumulada por posição
    equities      = np.empty((n_simulacoes, n))

    for i in range(n_simulacoes):
        shuffled = trades.copy()
        np.random.shuffle(shuffled)
        equity = np.cumsum(shuffled)
        equities[i] = equity
        pnl_finais[i] = equity[-1]

        # drawdown máximo: max(pico - vale) em pontos
        pico = np.maximum.accumulate(equity)
        drawdowns = pico - equity
        max_drawdowns[i] = drawdowns.max()

    percentis = [10, 25, 50, 75, 90, 95, 99]

    return {
        "percentis_drawdown": {
            f"p{p}": float(np.percentile(max_drawdowns, p)) for p in percentis
        },
        "percentis_pnl": {
            f"p{p}": float(np.percentile(pnl_finais, p)) for p in percentis
        },
        "banda_equity": [
            {
                "posicao": j,
                "p10": float(np.percentile(equities[:, j], 10)),
                "p50": float(np.percentile(equities[:, j], 50)),
                "p90": float(np.percentile(equities[:, j], 90)),
            }
            for j in range(n)
        ],
        "max_drawdowns": max_drawdowns.tolist(),  # array completo para cálculo de ruin no frontend
    }
```

> **Otimização se necessário:** usar `np.apply_along_axis` ou vetorizar completamente com broadcasting. Para 1.000 × 200 = 200.000 operações, o loop Python é aceitável. Para 10.000 simulações, avaliar vetorização.

## Resposta da API

```json
{
  "mc_run_id": 5,
  "run_id": 42,
  "n_simulacoes": 1000,
  "n_trades": 87,
  "drawdown_historico_pts": 320,
  "percentis_drawdown": {
    "p10": 180, "p25": 240, "p50": 310,
    "p75": 390, "p90": 470, "p95": 520, "p99": 640
  },
  "percentis_pnl": {
    "p10": 800, "p25": 1200, "p50": 1800,
    "p75": 2400, "p90": 3100, "p95": 3500, "p99": 4200
  },
  "banda_equity": [
    { "posicao": 0, "p10": -20, "p50": 10, "p90": 45 },
    { "posicao": 1, "p10": -15, "p50": 25, "p90": 80 },
    ...
  ],
  "max_drawdowns": [280, 310, 250, ...]
}
```

## Visualização — dois gráficos

### Gráfico 1: Banda de Confiança da Equity Curve
- Eixo X: número do trade (1 a N)
- Eixo Y: P&L acumulado em pontos
- Área sombreada: P10–P90
- Linha central: P50 (mediana)
- Linha tracejada: equity curve histórica real (para comparação)

### Gráfico 2: Histograma de Drawdown Máximo
- Eixo X: drawdown em pontos (bins de 50pts)
- Eixo Y: frequência (% das simulações)
- Linhas verticais: P50, P90, P95
- Linha vermelha: drawdown histórico observado (para mostrar onde cai na distribuição)

## Mensagem interpretativa (exibir abaixo dos gráficos)

```
"Em {n_simulacoes} simulações com os mesmos {n_trades} trades embaralhados:
- 50% das sequências tiveram drawdown máximo de até {p50} pts
- Em 90% dos casos, o drawdown não passou de {p90} pts
- Existe {p_ruin}% de chance de drawdown acima de {threshold} pts

O drawdown histórico observado ({drawdown_historico} pts) está no percentil {pct_historico}
da distribuição simulada — {'você teve sorte na sequência' if pct_historico < 40 else 'resultado esperado'}."
```

## Aviso de poucos trades

Se `n_trades < 30`: exibir aviso amarelo — "Simulação com poucos trades. Os percentis podem não ser representativos."

## Dependências externas
- numpy (operações vetorizadas)
- Nenhuma lib adicional necessária
