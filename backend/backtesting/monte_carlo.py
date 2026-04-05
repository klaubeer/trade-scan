import json
import numpy as np
from backend.banco.conexao import get_conn


def simular_monte_carlo(resultado_pts: list[float], n_simulacoes: int = 1000) -> dict:
    trades = np.array(resultado_pts, dtype=float)
    n = len(trades)

    max_drawdowns = np.empty(n_simulacoes)
    pnl_finais = np.empty(n_simulacoes)
    equities = np.empty((n_simulacoes, n))

    rng = np.random.default_rng()

    for i in range(n_simulacoes):
        shuffled = trades.copy()
        rng.shuffle(shuffled)
        equity = np.cumsum(shuffled)
        equities[i] = equity
        pnl_finais[i] = equity[-1]

        pico = np.maximum.accumulate(equity)
        drawdowns = pico - equity
        max_drawdowns[i] = drawdowns.max()

    percentis = [10, 25, 50, 75, 90, 95, 99]

    # Equity histórica para comparação
    equity_hist = np.cumsum(trades)
    pico_hist = np.maximum.accumulate(equity_hist)
    dd_hist = pico_hist - equity_hist
    max_dd_historico = float(dd_hist.max())

    # Percentil do drawdown histórico na distribuição simulada
    pct_historico = float(np.mean(max_drawdowns <= max_dd_historico) * 100)

    # Banda de confiança — amostra a cada N candles para manter JSON compacto
    passo = max(1, n // 100)  # máx 100 pontos na curva
    indices = list(range(0, n, passo))
    if indices[-1] != n - 1:
        indices.append(n - 1)

    banda_equity = [
        {
            "posicao": int(j),
            "p10": round(float(np.percentile(equities[:, j], 10)), 1),
            "p50": round(float(np.percentile(equities[:, j], 50)), 1),
            "p90": round(float(np.percentile(equities[:, j], 90)), 1),
        }
        for j in indices
    ]

    return {
        "n_trades": n,
        "n_simulacoes": n_simulacoes,
        "drawdown_historico_pts": round(max_dd_historico, 1),
        "pct_historico_na_distribuicao": round(pct_historico, 1),
        "percentis_drawdown": {
            f"p{p}": round(float(np.percentile(max_drawdowns, p)), 1)
            for p in percentis
        },
        "percentis_pnl": {
            f"p{p}": round(float(np.percentile(pnl_finais, p)), 1)
            for p in percentis
        },
        "banda_equity": banda_equity,
        "max_drawdowns": [round(float(v), 1) for v in max_drawdowns],
    }


def persistir_monte_carlo(run_id: int, n_simulacoes: int, resultado: dict) -> int:
    # Salvar sem o array completo de max_drawdowns (muito grande) — guardar apenas os percentis
    resultado_compacto = {k: v for k, v in resultado.items() if k != "max_drawdowns"}

    with get_conn() as conn:
        mc_id = conn.execute("""
            INSERT INTO monte_carlo_runs (run_id, n_simulacoes, resultado_json)
            VALUES (?, ?, ?)
            RETURNING id
        """, [run_id, n_simulacoes, json.dumps(resultado_compacto)]).fetchone()[0]

    return mc_id
