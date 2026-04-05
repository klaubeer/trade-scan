"""
seed.py — Popula os setups de referência no banco TradeScan.

Uso:
    python -m backend.banco.seed
"""

import json
from backend.banco.conexao import get_conn

SETUPS = [
    # ------------------------------------------------------------------ #
    #  SETUPS DE SCALPING — WIN                                           #
    #  Volatilidade alta: stops mínimos 100-120 pts, alvos 150-200 pts   #
    # ------------------------------------------------------------------ #
    {
        "nome": "EMA Crossover Scalp - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "EMA Crossover Scalp - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "ambos",
            # 2 candles consecutivos na mesma direção = proxy de EMA9 cruzando EMA21
            "sequencia_candles": 2,
            "sequencia_wick_max_pct": 40.0,
            "adx_min": 15.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 100,
            "alvo_pts": 150,
            "horario_inicio": "09:00:00",
            "horario_fim": "11:00:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "MACD Momentum Scalp - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "MACD Momentum Scalp - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "ambos",
            # Sequência de 2 candles limpos = proxy de histograma MACD acelerando
            "sequencia_candles": 2,
            "sequencia_wick_max_pct": 35.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 100,
            "alvo_pts": 200,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:00:00",
            "max_entradas_dia": 4,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Liquidity Sweep Reclaim - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "Liquidity Sweep Reclaim - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "ambos",
            # Sweep de stops + reclaim: 2 candles (varre extremo, fecha de volta)
            "sequencia_candles": 2,
            "sequencia_filtrar_zonas": True,
            "range_candle_min": 30.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 100,
            "alvo_pts": 150,
            "horario_inicio": "09:00:00",
            "horario_fim": "12:00:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        # Mean Reversion fica SEPARADO por long/short — condições são opostas:
        # Long: IFR2 < 10 (oversold) | Short: IFR2 > 90 (overbought)
        "nome": "Mean Reversion IFR2 Long - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "Mean Reversion IFR2 Long - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "long",
            "ifr2_max": 10.0,
            "range_acumulado_max_pct": 1.2,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 120,
            "alvo_pts": 200,
            "horario_inicio": "10:00:00",
            "horario_fim": "15:00:00",
            "max_entradas_dia": 2,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Mean Reversion IFR2 Short - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "Mean Reversion IFR2 Short - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "short",
            "ifr2_min": 90.0,
            "range_acumulado_max_pct": 1.2,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 120,
            "alvo_pts": 200,
            "horario_inicio": "10:00:00",
            "horario_fim": "15:00:00",
            "max_entradas_dia": 2,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    # ------------------------------------------------------------------ #
    #  SETUPS DE TENDÊNCIA — WIN                                          #
    #  Range maior: stops 200-400 pts, alvos 400-700 pts                 #
    # ------------------------------------------------------------------ #
    {
        "nome": "Pullback EMA20 + ADX - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "Pullback EMA20 + ADX - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "ambos",
            # ADX > 25 confirma tendência; 2 candles de retomada após pull-back
            "sequencia_candles": 2,
            "adx_min": 25.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 250,
            "alvo_pts": 500,
            "horario_inicio": "09:15:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 3.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Break of Structure - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "Break of Structure - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "ambos",
            # 3 candles quebrando HH (long) ou LL (short) = BoS confirmado
            "sequencia_candles": 3,
            "sequencia_wick_max_pct": 35.0,
            "adx_min": 20.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 300,
            "alvo_pts": 600,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 3.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Dual EMA Pullback - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "Dual EMA Pullback - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "ambos",
            # EMA9 > EMA30 com retomada: 2 candles após pullback
            "sequencia_candles": 2,
            "sequencia_wick_max_pct": 45.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 200,
            "alvo_pts": 400,
            "horario_inicio": "09:15:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Donchian Breakout - WIN 60min",
        "ticker": "WIN",
        "params": {
            "nome": "Donchian Breakout - WIN 60min",
            "ticker": "WIN",
            "timeframe": "60min",
            "direcao": "ambos",
            # 3 candles = novo high/low de 20 períodos sustentado (canal Donchian)
            "sequencia_candles": 3,
            "atr_fator_range": 0.8,
            "adx_min": 20.0,
            "tipo_entrada": "fechamento_gatilho",
            # Stop = 2×ATR 60min ≈ 400 pts
            "stop_pts": 400,
            "alvo_pts": 700,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:00:00",
            "max_entradas_dia": 1,
            "slippage_pts": 5.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "ABCD Pattern Tendência - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "ABCD Pattern Tendência - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "ambos",
            # 3 candles = leg AB formado + pullback BC + início do CD (retomada)
            "sequencia_candles": 3,
            "sequencia_wick_max_pct": 40.0,
            "tipo_entrada": "fechamento_gatilho",
            # Stop abaixo do ponto C; alvo = projeção CD = AB
            "stop_pts": 350,
            "alvo_pts": 700,
            "alvo2_pts": 1000,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    # ------------------------------------------------------------------ #
    #  SETUPS CLÁSSICOS DE REFERÊNCIA                                     #
    # ------------------------------------------------------------------ #
    {
        "nome": "9.1 Larry Williams Long - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "9.1 Larry Williams Long - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "long",
            "tipo_entrada": "rompimento_maxima",
            "mme9_posicao": "abaixo",
            "stop_pts": 25,
            "alvo_pts": 50,
            "horario_inicio": "09:00:00",
            "horario_fim": "17:00:00",
            "max_entradas_dia": 2,
            "slippage_pts": 0.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "ABC Long - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "ABC Long - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "long",
            "tipo_entrada": "rompimento_maxima",
            "mm200_posicao": "acima",
            "stop_pts": 30,
            "alvo_pts": 60,
            "horario_inicio": "09:00:00",
            "horario_fim": "17:00:00",
            "max_entradas_dia": 2,
            "slippage_pts": 0.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "IFR2 Long - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "IFR2 Long - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "long",
            "tipo_entrada": "fechamento_gatilho",
            "ifr2_max": 5,
            "stop_pts": 30,
            "alvo_pts": 50,
            "horario_inicio": "09:00:00",
            "horario_fim": "17:00:00",
            "max_entradas_dia": 1,
            "slippage_pts": 0.0,
            "custo_por_ponto": 0.20,
        },
    },
]


def seed():
    with get_conn() as conn:
        inseridos = 0
        ignorados = 0
        for s in SETUPS:
            existente = conn.execute(
                "SELECT id FROM setups WHERE nome = ?", [s["nome"]]
            ).fetchone()
            if existente:
                ignorados += 1
                continue
            conn.execute(
                "INSERT INTO setups (nome, ticker, params_json) VALUES (?, ?, ?)",
                [s["nome"], s["ticker"], json.dumps(s["params"])],
            )
            inseridos += 1
        conn.commit()

    print(f"Setups inseridos: {inseridos} | já existiam: {ignorados}")


if __name__ == "__main__":
    seed()
