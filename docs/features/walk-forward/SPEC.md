# SPEC — Walk-Forward Analysis

## O que faz
Executa um setup em janelas rolantes de otimização + validação, simulando o processo real de um trader que re-avalia periodicamente. Produz uma equity curve composta apenas pelos períodos out-of-sample e métricas de robustez.

## Status atual
📋 PLANNED

## Subtarefas

| ID | Descrição | Status | DoD |
|----|-----------|--------|-----|
| F7-001 | Geração de janelas | 📋 PLANNED | Datas corretas verificadas |
| F7-002 | Execução de backtests por janela | 📋 PLANNED | 2 runs por janela no DuckDB |
| F7-003 | Eficiência e consistência | 📋 PLANNED | Fórmulas verificadas manualmente |
| F7-004 | Equity curve out-of-sample composta | 📋 PLANNED | Trades em ordem cronológica |
| F7-005 | Persistência | 📋 PLANNED | FKs válidas |
| F7-006 | Rota POST executar | 📋 PLANNED | Resposta completa |
| F7-007 | Rota GET resultado | 📋 PLANNED | Janelas detalhadas |
| F7-008 | WalkForwardChart | 📋 PLANNED | Barras in vs out + linha eficiência |
| F7-009 | Página frontend integrada | 📋 PLANNED | End-to-end funcionando |

## Decisões específicas desta feature

- **Sem auto-otimização de parâmetros** — o sistema não varia os parâmetros do setup em cada janela de otimização. O usuário define os parâmetros manualmente. O walk-forward aqui é puramente de validação temporal: "esse setup, com esses parâmetros fixos, performa consistentemente ao longo do tempo?" Isso é diferente do walk-forward de otimização automática (que seria overfitting em outro nível).

- **Janelas com overlap permitido** — com step < janela_otim, as janelas de otimização se sobrepõem. Isso é padrão e esperado; os períodos de validação nunca se sobrepõem.

- **Execução sequencial das janelas** — não paralelizar para evitar contenção no DuckDB (single-writer). Cada janela executa e persiste antes da próxima começar.

## Algoritmo de geração de janelas

```python
def gerar_janelas(periodo_inicio, periodo_fim,
                  janela_otim_meses, janela_valid_meses, step_meses):
    janelas = []
    cursor = periodo_inicio
    janela_num = 1

    while True:
        otim_inicio = cursor
        otim_fim    = cursor + relativedelta(months=janela_otim_meses) - timedelta(days=1)
        valid_inicio = otim_fim + timedelta(days=1)
        valid_fim   = valid_inicio + relativedelta(months=janela_valid_meses) - timedelta(days=1)

        if valid_fim > periodo_fim:
            break

        janelas.append({
            "num": janela_num,
            "otim_inicio": otim_inicio,
            "otim_fim": otim_fim,
            "valid_inicio": valid_inicio,
            "valid_fim": valid_fim,
        })

        cursor += relativedelta(months=step_meses)
        janela_num += 1

    return janelas
```

**Exemplo:** período 2023-01-01 a 2024-12-31, otim=6m, valid=1m, step=1m
- Janela 1: otim [Jan-Jun/23] | valid [Jul/23]
- Janela 2: otim [Fev-Jul/23] | valid [Ago/23]
- ...
- Janela 18: otim [Jul-Dez/24] | valid não cabe → para

## Métricas consolidadas

```python
# Eficiência: quão próximo o out-of-sample chega do in-sample
eficiencia = mean([j.expectância_out for j in janelas]) / mean([j.expectância_in for j in janelas])

# Consistência: % de janelas com resultado positivo no out-of-sample
consistencia = len([j for j in janelas if j.expectância_out > 0]) / len(janelas)
```

**Interpretação sugerida (exibir na UI):**

| Eficiência | Consistência | Diagnóstico |
|---|---|---|
| > 0.6 | > 60% | Setup robusto |
| 0.3–0.6 | > 50% | Setup funcional, monitorar |
| < 0.3 | qualquer | Sinal de overfitting |
| qualquer | < 40% | Dependência de regime — investigar quais janelas falharam |

## Equity curve out-of-sample composta

Concatenar os trades dos períodos de **validação** de cada janela, em ordem cronológica.
Calcular equity curve e drawdown sobre essa sequência — esse é o resultado "real" do setup.

## Resposta da API

```json
{
  "wf_run_id": 1,
  "setup_id": 3,
  "eficiencia": 0.72,
  "consistencia": 0.78,
  "total_janelas": 18,
  "janelas_positivas": 14,
  "equity_out_composta": [0, 50, 120, 80, 200, ...],
  "janelas": [
    {
      "num": 1,
      "otim_inicio": "2023-01-01",
      "otim_fim": "2023-06-30",
      "valid_inicio": "2023-07-01",
      "valid_fim": "2023-07-31",
      "run_id_otim": 10,
      "run_id_valid": 11,
      "expectancia_in": 42.5,
      "expectancia_out": 31.2,
      "win_rate_in": 0.62,
      "win_rate_out": 0.58,
      "total_trades_in": 34,
      "total_trades_out": 6
    }
  ]
}
```

## Aviso de janelas com poucos trades

Se uma janela de validação tiver menos de 10 trades, exibir aviso na UI:
"Janela X tem apenas N trades no out-of-sample — resultado estatisticamente pouco significativo."

## Dependências externas
- dateutil.relativedelta (para manipulação de meses)
- Motor de backtesting (F3)
- DuckDB (tabelas walk_forward_runs, walk_forward_janelas)
