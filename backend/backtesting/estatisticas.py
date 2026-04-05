import numpy as np
from itertools import groupby


def calcular_estatisticas(trades: list[dict], custo_por_ponto: float = 0.20) -> dict:
    if not trades:
        return _stats_vazio()

    pts = [t["resultado_pts"] for t in trades]
    ganhos = [p for p in pts if p > 0]
    perdas = [p for p in pts if p < 0]

    total = len(pts)
    wins = len(ganhos)
    losses = len(perdas)
    win_rate = wins / total if total > 0 else 0

    avg_ganho = np.mean(ganhos) if ganhos else 0
    avg_perda = abs(np.mean(perdas)) if perdas else 0
    payoff = avg_ganho / avg_perda if avg_perda > 0 else float("inf")

    expectancia_pts = np.mean(pts)
    total_pts = sum(pts)
    total_brl = total_pts * custo_por_ponto

    gross_profit = sum(ganhos) if ganhos else 0
    gross_loss = abs(sum(perdas)) if perdas else 0
    fator_lucro = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Equity curve e drawdown
    equity = np.cumsum(pts)
    pico = np.maximum.accumulate(equity)
    drawdown_serie = pico - equity
    max_drawdown_pts = float(drawdown_serie.max()) if len(drawdown_serie) > 0 else 0

    # % do drawdown máximo em relação ao pico
    pico_no_max_dd = pico[np.argmax(drawdown_serie)] if len(pico) > 0 else 0
    max_drawdown_pct = (max_drawdown_pts / abs(pico_no_max_dd) * 100) if pico_no_max_dd != 0 else 0

    # Sequências consecutivas
    max_wins_consec = _max_consecutivos(pts, lambda x: x > 0)
    max_losses_consec = _max_consecutivos(pts, lambda x: x < 0)

    # Extremos
    melhor_trade = max(pts) if pts else 0
    pior_trade = min(pts) if pts else 0

    # P&L por dia
    pnl_por_dia = {}
    for t in trades:
        dia = str(t["datetime"].date()) if hasattr(t["datetime"], "date") else str(t["datetime"])[:10]
        pnl_por_dia[dia] = round(pnl_por_dia.get(dia, 0) + t["resultado_pts"], 1)

    # P&L por mês
    pnl_por_mes = {}
    for t in trades:
        dt = t["datetime"]
        mes = str(dt)[:7] if isinstance(dt, str) else f"{dt.year:04d}-{dt.month:02d}"
        pnl_por_mes[mes] = round(pnl_por_mes.get(mes, 0) + t["resultado_pts"], 1)

    # Equity curve como lista
    equity_curve = [round(float(v), 1) for v in equity]

    # Histograma (bins de 10 pts de -300 a +300)
    hist_counts, hist_bins = np.histogram(pts, bins=range(-300, 310, 10))
    histograma = [
        {"bin": int(hist_bins[i]), "contagem": int(hist_counts[i])}
        for i in range(len(hist_counts))
    ]

    # Segmentação por contexto
    segmentacao = _segmentar(trades)

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "breakevens": total - wins - losses,
        "win_rate": round(win_rate * 100, 1),
        "avg_ganho_pts": round(avg_ganho, 1),
        "avg_perda_pts": round(avg_perda, 1),
        "payoff": round(payoff, 2),
        "expectancia_pts": round(float(expectancia_pts), 1),
        "expectancia_brl": round(float(expectancia_pts) * custo_por_ponto, 2),
        "total_pts": round(total_pts, 1),
        "total_brl": round(total_brl, 2),
        "gross_profit": round(gross_profit, 1),
        "gross_loss": round(gross_loss, 1),
        "fator_lucro": round(fator_lucro, 2),
        "max_drawdown_pts": round(max_drawdown_pts, 1),
        "max_drawdown_pct": round(max_drawdown_pct, 1),
        "max_wins_consecutivos": max_wins_consec,
        "max_losses_consecutivos": max_losses_consec,
        "melhor_trade_pts": round(melhor_trade, 1),
        "pior_trade_pts": round(pior_trade, 1),
        "pnl_por_dia": pnl_por_dia,
        "pnl_por_mes": pnl_por_mes,
        "equity_curve": equity_curve,
        "histograma": histograma,
        "segmentacao": segmentacao,
    }


def _max_consecutivos(pts: list, condicao) -> int:
    max_seq = 0
    seq_atual = 0
    for p in pts:
        if condicao(p):
            seq_atual += 1
            max_seq = max(max_seq, seq_atual)
        else:
            seq_atual = 0
    return max_seq


def _segmentar(trades: list[dict]) -> dict:
    dims = {
        "tendencia_semanal": ["alta", "baixa", "lateral"],
        "periodo_dia": ["manha", "tarde"],
        "gap_abertura_tipo": ["positivo", "negativo", "sem_gap"],
        "range_acumulado_faixa": ["<0.5%", "0.5-1%", "1-1.5%", "1.5-2%", "2-2.5%", "2.5-3%", ">3%"],
        "variacao_dia_faixa": ["<-3%", "-3 a -2.5%", "-2.5 a -2%", "-2 a -1.5%", "-1.5 a -1%",
                               "-1 a -0.5%", "-0.5 a 0%", "0 a 0.5%", "0.5 a 1%",
                               "1 a 1.5%", "1.5 a 2%", "2 a 2.5%", "2.5 a 3%", ">3%"],
    }
    resultado = {}
    for dim, valores in dims.items():
        resultado[dim] = {}
        for val in valores:
            subset = [
                t for t in trades
                if t.get("contexto_json", {}).get(dim) == val
            ]
            if not subset:
                continue
            pts_sub = [t["resultado_pts"] for t in subset]
            wins_sub = sum(1 for p in pts_sub if p > 0)
            resultado[dim][val] = {
                "total_trades": len(subset),
                "win_rate": round(wins_sub / len(subset) * 100, 1),
                "expectancia_pts": round(float(np.mean(pts_sub)), 1),
                "total_pts": round(sum(pts_sub), 1),
            }
    return resultado


def _stats_vazio() -> dict:
    return {
        "total_trades": 0,
        "wins": 0, "losses": 0, "breakevens": 0,
        "win_rate": 0, "avg_ganho_pts": 0, "avg_perda_pts": 0,
        "payoff": 0, "expectancia_pts": 0, "expectancia_brl": 0,
        "total_pts": 0, "total_brl": 0,
        "gross_profit": 0, "gross_loss": 0, "fator_lucro": 0,
        "max_drawdown_pts": 0, "max_drawdown_pct": 0,
        "max_wins_consecutivos": 0, "max_losses_consecutivos": 0,
        "melhor_trade_pts": 0, "pior_trade_pts": 0,
        "pnl_por_dia": {}, "pnl_por_mes": {},
        "equity_curve": [], "histograma": [], "segmentacao": {},
    }
