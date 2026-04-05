import json
from datetime import date
from typing import Literal

import pandas as pd

from backend.banco.conexao import get_conn
from backend.backtesting.sinais import gerar_entradas, calcular_preco_entrada, extrair_contexto
from backend.backtesting.estatisticas import calcular_estatisticas
from backend.indicadores.calculos import enriquecer_dataframe
from backend.schemas.modelos import SetupParams


class ErroValidacao(Exception):
    pass


# ---------------------------------------------------------------------------
# Carregamento
# ---------------------------------------------------------------------------

def carregar_candles(ticker: str, timeframe: str, inicio: date, fim: date) -> pd.DataFrame:
    with get_conn() as conn:
        df = conn.execute("""
            SELECT datetime, open, high, low, close, volume_fin, qty
            FROM candles
            WHERE ticker = ? AND timeframe = ?
              AND datetime::DATE BETWEEN ? AND ?
            ORDER BY datetime
        """, [ticker, timeframe, inicio, fim]).df()

    if df.empty:
        raise ErroValidacao(
            f"Nenhum candle encontrado para {ticker} {timeframe} entre {inicio} e {fim}."
        )

    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


# ---------------------------------------------------------------------------
# Simulação candle a candle
# ---------------------------------------------------------------------------

def simular_trades(
    df: pd.DataFrame,
    entries: pd.Series,
    setup: SetupParams,
    cnn_modelo_id: str | None = None,
    cnn_threshold: float = 0.5,
) -> list[dict]:
    trades = []
    entradas_hoje: dict[object, int] = {}
    n = len(df)
    i = 0

    while i < n:
        sinal = int(entries.iloc[i])
        if sinal == 0:
            i += 1
            continue

        candle = df.iloc[i]
        dia = candle["datetime"].date()
        hora = candle["datetime"].time()

        # Respeitar horário (já filtrado nos sinais, mas garantir aqui)
        if hora < setup.horario_inicio or hora >= setup.horario_fim:
            i += 1
            continue

        # Limite de entradas por dia
        if entradas_hoje.get(dia, 0) >= setup.max_entradas_dia:
            i += 1
            continue

        # Filtro CNN — se ativado, pula trade sem consumir slot diário
        if cnn_modelo_id is not None:
            from backend.padroes.inferencia import prever  # import lazy (torch opcional)
            prob = prever(cnn_modelo_id, setup.ticker, setup.timeframe, candle["datetime"])
            if prob < cnn_threshold:
                i += 1
                continue

        # Direção determinada pelo sinal (+1 long, -1 short)
        long = sinal > 0

        # Preço de entrada
        entry_price = calcular_preco_entrada(candle, setup)
        entry_price += setup.slippage_pts if long else -setup.slippage_pts

        entradas_hoje[dia] = entradas_hoje.get(dia, 0) + 1

        # Níveis de stop e alvo
        if long:
            stop_price = entry_price - setup.stop_pts
        else:
            stop_price = entry_price + setup.stop_pts

        if setup.alvo_proximo_pct_dia:
            abertura_dia = float(candle.get("abertura_dia", entry_price) or entry_price)
            alvo_min = setup.alvo_minimo_pts or 600.0
            _niveis_pct = [0.005, 0.010, 0.015, 0.020, 0.025, 0.030]
            if long:
                candidatos = [
                    abertura_dia * (1 + p) for p in _niveis_pct
                    if abertura_dia * (1 + p) - entry_price >= alvo_min
                ]
                alvo_price = min(candidatos) if candidatos else entry_price + alvo_min
            else:
                candidatos = [
                    abertura_dia * (1 - p) for p in _niveis_pct
                    if entry_price - abertura_dia * (1 - p) >= alvo_min
                ]
                alvo_price = max(candidatos) if candidatos else entry_price - alvo_min
        else:
            alvo_price = entry_price + setup.alvo_pts if long else entry_price - setup.alvo_pts

        # Scan forward para encontrar saída
        saida_price = None
        saida_tipo = None
        exit_i = None

        for j in range(i + 1, n):
            prox = df.iloc[j]
            prox_dia = prox["datetime"].date()
            prox_hora = prox["datetime"].time()

            # Saída forçada: novo dia ou fechamento do pregão
            if prox_dia != dia or prox_hora >= setup.horario_fechamento:
                saida_price = df.iloc[j - 1]["close"]
                saida_tipo = "forcado"
                exit_i = j - 1
                break

            if long:
                stop_hit = prox["low"] <= stop_price
                alvo_hit = prox["high"] >= alvo_price
            else:
                stop_hit = prox["high"] >= stop_price
                alvo_hit = prox["low"] <= alvo_price

            if stop_hit and alvo_hit:
                # Conservador: stop vence
                saida_price = stop_price
                saida_tipo = "stop"
                exit_i = j
                break
            elif stop_hit:
                saida_price = stop_price
                saida_tipo = "stop"
                exit_i = j
                break
            elif alvo_hit:
                saida_price = alvo_price
                saida_tipo = "alvo"
                exit_i = j
                break

        # Fim dos dados sem saída
        if saida_price is None:
            saida_price = df.iloc[-1]["close"]
            saida_tipo = "forcado"
            exit_i = n - 1

        resultado_pts = (saida_price - entry_price) if long else (entry_price - saida_price)
        resultado_pts = round(resultado_pts, 1)

        if resultado_pts > 0:
            resultado = "gain"
        elif resultado_pts < 0:
            resultado = "loss"
        else:
            resultado = "breakeven"

        trades.append({
            "datetime": candle["datetime"],
            "direcao": "long" if long else "short",
            "preco_entrada": round(entry_price, 2),
            "preco_saida": round(saida_price, 2),
            "resultado": resultado,
            "resultado_pts": resultado_pts,
            "saida_tipo": saida_tipo,
            "contexto_json": extrair_contexto(df, i),
        })

        i = exit_i + 1

    return trades


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def persistir_run(
    setup_id: int,
    periodo_inicio: date,
    periodo_fim: date,
    sample_type: str,
    trades: list[dict],
    stats: dict,
) -> int:
    with get_conn() as conn:
        # Verificar bloqueio out-of-sample
        if sample_type == "out_of_sample":
            aprovado = conn.execute("""
                SELECT COUNT(*) FROM backtest_runs
                WHERE setup_id = ? AND sample_type = 'in_sample' AND aprovado = TRUE
            """, [setup_id]).fetchone()[0]
            if aprovado == 0:
                raise ErroValidacao(
                    "Não há nenhum run in-sample aprovado para este setup. "
                    "Aprove um run in-sample antes de testar out-of-sample."
                )

        run_id = conn.execute("""
            INSERT INTO backtest_runs (setup_id, periodo_inicio, periodo_fim, sample_type)
            VALUES (?, ?, ?, ?)
            RETURNING id
        """, [setup_id, periodo_inicio, periodo_fim, sample_type]).fetchone()[0]

        for t in trades:
            conn.execute("""
                INSERT INTO backtest_trades
                    (run_id, datetime, direcao, preco_entrada, preco_saida,
                     resultado, resultado_pts, contexto_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                run_id,
                t["datetime"],
                t["direcao"],
                t["preco_entrada"],
                t["preco_saida"],
                t["resultado"],
                t["resultado_pts"],
                json.dumps(t["contexto_json"]),
            ])

        conn.execute("""
            INSERT INTO backtest_stats (run_id, stats_json)
            VALUES (?, ?)
        """, [run_id, json.dumps(stats)])

    return run_id


# ---------------------------------------------------------------------------
# Orquestrador principal
# ---------------------------------------------------------------------------

def executar_backtest(
    setup: SetupParams,
    setup_id: int,
    periodo_inicio: date,
    periodo_fim: date,
    sample_type: Literal["in_sample", "out_of_sample"] = "in_sample",
    cnn_modelo_id: str | None = None,
    cnn_threshold: float = 0.5,
) -> dict:
    df = carregar_candles(setup.ticker, setup.timeframe, periodo_inicio, periodo_fim)
    df = enriquecer_dataframe(df)
    entries = gerar_entradas(df, setup)
    trades = simular_trades(df, entries, setup, cnn_modelo_id, cnn_threshold)
    stats = calcular_estatisticas(trades, setup.custo_por_ponto)
    run_id = persistir_run(setup_id, periodo_inicio, periodo_fim, sample_type, trades, stats)

    return {
        "run_id": run_id,
        "total_trades": len(trades),
        "stats": stats,
        "trades": [_serializar_trade(t) for t in trades],
    }


def _serializar_trade(t: dict) -> dict:
    return {
        **t,
        "datetime": str(t["datetime"]),
    }
