"""
seed.py — Popula os 3 setups de referência no banco TradeScan.

Uso:
    python -m backend.banco.seed
"""

import json
from backend.banco.conexao import get_conn

SETUPS = [
    # ------------------------------------------------------------------ #
    #  SETUPS DE SCALPING — WIN                                           #
    #  Calibração: amplitude média 3.485 pts, alvo scalping base 174 pts #
    # ------------------------------------------------------------------ #
    {
        "nome": "EMA Crossover + Filtro Tendência Scalp Long - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "EMA Crossover + Filtro Tendência Scalp Long - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "long",
            # Preço acima da MME9 (EMA9 > EMA21 approximation) + MM200 como filtro direcional
            "mme9_posicao": "acima",
            "mm200_posicao": "acima",
            # IFR(2) > 50 como proxy de momentum acima do neutro (RSI 14 > 50)
            "ifr2_min": 50.0,
            "tipo_entrada": "fechamento_gatilho",
            # Alvo base scalping WIN = 174 pts; stop ~50% do alvo (R:R 1:2)
            "stop_pts": 80,
            "alvo_pts": 160,
            # Primeira hora: máxima liquidez e momentum
            "horario_inicio": "09:00:00",
            "horario_fim": "11:00:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "EMA Crossover + Filtro Tendência Scalp Short - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "EMA Crossover + Filtro Tendência Scalp Short - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "short",
            "mme9_posicao": "abaixo",
            "mm200_posicao": "abaixo",
            # IFR(2) < 50 = momentum vendedor
            "ifr2_max": 50.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 80,
            "alvo_pts": 160,
            "horario_inicio": "09:00:00",
            "horario_fim": "11:00:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "MACD Momentum Scalp Long - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "MACD Momentum Scalp Long - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            # Sequência de 2 candles de alta quebrando máximas = proxy de histograma MACD positivo
            "direcao": "long",
            "sequencia_candles": 2,
            "sequencia_wick_max_pct": 40.0,  # pavios pequenos = candles limpos
            "mme9_posicao": "acima",
            "tipo_entrada": "rompimento_maxima",
            "stop_pts": 80,
            "alvo_pts": 160,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:00:00",
            "max_entradas_dia": 4,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "MACD Momentum Scalp Short - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "MACD Momentum Scalp Short - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "short",
            "sequencia_candles": 2,
            "sequencia_wick_max_pct": 40.0,
            "mme9_posicao": "abaixo",
            "tipo_entrada": "rompimento_minima",
            "stop_pts": 80,
            "alvo_pts": 160,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:00:00",
            "max_entradas_dia": 4,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Liquidity Sweep Reclaim Long - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "Liquidity Sweep Reclaim Long - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "long",
            # Sequência: 1º candle varre mínima (stop hunt), 2º fecha acima = reclaim
            "sequencia_candles": 2,
            "sequencia_filtrar_zonas": True,   # sweep não pode estar em zona % do dia
            "range_candle_min": 30.0,          # candle de sweep tem corpo relevante
            "tipo_entrada": "fechamento_gatilho",
            # Stop apertado: invalidação é nova mínima além do sweep
            "stop_pts": 60,
            "alvo_pts": 120,
            "horario_inicio": "09:00:00",
            "horario_fim": "12:00:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Liquidity Sweep Reclaim Short - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "Liquidity Sweep Reclaim Short - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "short",
            "sequencia_candles": 2,
            "sequencia_filtrar_zonas": True,
            "range_candle_min": 30.0,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 60,
            "alvo_pts": 120,
            "horario_inicio": "09:00:00",
            "horario_fim": "12:00:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Mean Reversion IFR2 Long - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "Mean Reversion IFR2 Long - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "long",
            # IFR(2) < 10 = oversold extremo (proxy Bollinger Bands toque na banda inferior)
            "ifr2_max": 10.0,
            # Mercado em range: range acumulado baixo = Bollinger Bands flat
            "range_acumulado_max_pct": 1.2,
            "tipo_entrada": "fechamento_gatilho",
            # Alvo: retorno à MME9 (proxy VWAP/banda superior); maior R:R por ser mean reversion
            "stop_pts": 100,
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
            # IFR(2) > 90 = overbought extremo
            "ifr2_min": 90.0,
            "range_acumulado_max_pct": 1.2,
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 100,
            "alvo_pts": 200,
            "horario_inicio": "10:00:00",
            "horario_fim": "15:00:00",
            "max_entradas_dia": 2,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Price Action Volume Scalp Long - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "Price Action Volume Scalp Long - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "long",
            # Candle com corpo limpo e pavio mínimo = absorção de oferta (proxy tape reading)
            "range_candle_min": 25.0,
            "pavio_total_max": 15.0,    # pavio total pequeno = determinação direcional
            "sequencia_candles": 2,
            "mme9_posicao": "acima",
            "tipo_entrada": "fechamento_gatilho",
            # Ultra-tight: stop próximo ao nível de absorção (1-2 ticks no DOM)
            "stop_pts": 25,
            "alvo_pts": 75,
            "horario_inicio": "09:00:00",
            "horario_fim": "10:30:00",
            "max_entradas_dia": 5,
            "slippage_pts": 1.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Price Action Volume Scalp Short - WIN 1min",
        "ticker": "WIN",
        "params": {
            "nome": "Price Action Volume Scalp Short - WIN 1min",
            "ticker": "WIN",
            "timeframe": "1min",
            "direcao": "short",
            "range_candle_min": 25.0,
            "pavio_total_max": 15.0,
            "sequencia_candles": 2,
            "mme9_posicao": "abaixo",
            "tipo_entrada": "fechamento_gatilho",
            "stop_pts": 25,
            "alvo_pts": 75,
            "horario_inicio": "09:00:00",
            "horario_fim": "10:30:00",
            "max_entradas_dia": 5,
            "slippage_pts": 1.0,
            "custo_por_ponto": 0.20,
        },
    },
    # ------------------------------------------------------------------ #
    #  SETUPS DE TENDÊNCIA — WIN                                          #
    #  ATR 15min ≈ 150-200 pts; ATR 60min ≈ 300-400 pts                  #
    #  Stop e alvo calibrados em múltiplos de ATR                        #
    # ------------------------------------------------------------------ #
    {
        "nome": "Pullback EMA20 + ADX Long - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "Pullback EMA20 + ADX Long - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "long",
            # ADX > 25 confirma tendência forte antes de entrar no pullback
            "adx_min": 25.0,
            # Preço acima da MME9 = retornou à média após pullback
            "mme9_posicao": "acima",
            "mm200_posicao": "acima",
            "sequencia_candles": 2,   # 2 candles de retomada alta após pull-back
            "tipo_entrada": "rompimento_maxima",
            # Stop ~1.3×ATR15min; alvo ~2.6×ATR15min (R:R 1:2)
            "stop_pts": 200,
            "alvo_pts": 400,
            "horario_inicio": "09:15:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 3.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Pullback EMA20 + ADX Short - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "Pullback EMA20 + ADX Short - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "short",
            "adx_min": 25.0,
            "mme9_posicao": "abaixo",
            "mm200_posicao": "abaixo",
            "sequencia_candles": 2,
            "tipo_entrada": "rompimento_minima",
            "stop_pts": 200,
            "alvo_pts": 400,
            "horario_inicio": "09:15:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 3.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Break of Structure Long - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "Break of Structure Long - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "long",
            # 3 candles quebrando máximas = Higher High confirmado com momentum
            "sequencia_candles": 3,
            "sequencia_wick_max_pct": 35.0,
            "mm200_posicao": "acima",
            "adx_min": 20.0,
            "tipo_entrada": "rompimento_maxima",
            # Stop abaixo do último Higher Low; alvo = projeção do leg anterior
            "stop_pts": 250,
            "alvo_pts": 500,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 3.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Break of Structure Short - WIN 15min",
        "ticker": "WIN",
        "params": {
            "nome": "Break of Structure Short - WIN 15min",
            "ticker": "WIN",
            "timeframe": "15min",
            "direcao": "short",
            "sequencia_candles": 3,
            "sequencia_wick_max_pct": 35.0,
            "mm200_posicao": "abaixo",
            "adx_min": 20.0,
            "tipo_entrada": "rompimento_minima",
            "stop_pts": 250,
            "alvo_pts": 500,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 3.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Dual EMA Pullback Long - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "Dual EMA Pullback Long - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "long",
            # EMA 9 > EMA 30 = golden cross; sequência 2 candles = confirmação retomada
            "sequencia_candles": 2,
            "sequencia_wick_max_pct": 45.0,
            "mme9_posicao": "acima",
            "tipo_entrada": "rompimento_maxima",
            # Stop abaixo da EMA 30 (suporte dinâmico lento); alvo R:R 2:1
            "stop_pts": 150,
            "alvo_pts": 300,
            "horario_inicio": "09:15:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Dual EMA Pullback Short - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "Dual EMA Pullback Short - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "short",
            "sequencia_candles": 2,
            "sequencia_wick_max_pct": 45.0,
            "mme9_posicao": "abaixo",
            "tipo_entrada": "rompimento_minima",
            "stop_pts": 150,
            "alvo_pts": 300,
            "horario_inicio": "09:15:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 3,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Donchian Breakout Long - WIN 60min",
        "ticker": "WIN",
        "params": {
            "nome": "Donchian Breakout Long - WIN 60min",
            "ticker": "WIN",
            "timeframe": "60min",
            "direcao": "long",
            # Sequência 3 candles = novo high de 20 períodos sustentado (canal Donchian)
            "sequencia_candles": 3,
            # Range do dia >= 0.8× ATR diário confirma volatilidade pré-breakout
            "atr_fator_range": 0.8,
            "adx_min": 20.0,
            "tipo_entrada": "rompimento_maxima",
            # Stop = 2×ATR 60min ≈ 400 pts; alvo = 2× stop (trailing implícito)
            "stop_pts": 400,
            "alvo_pts": 800,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:00:00",
            "max_entradas_dia": 1,
            "slippage_pts": 5.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "Donchian Breakout Short - WIN 60min",
        "ticker": "WIN",
        "params": {
            "nome": "Donchian Breakout Short - WIN 60min",
            "ticker": "WIN",
            "timeframe": "60min",
            "direcao": "short",
            "sequencia_candles": 3,
            "atr_fator_range": 0.8,
            "adx_min": 20.0,
            "tipo_entrada": "rompimento_minima",
            "stop_pts": 400,
            "alvo_pts": 800,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:00:00",
            "max_entradas_dia": 1,
            "slippage_pts": 5.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "ABCD Pattern Tendência Long - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "ABCD Pattern Tendência Long - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "long",
            # 3 candles = leg AB formado + pullback BC + início CD (retomada)
            "sequencia_candles": 3,
            "sequencia_wick_max_pct": 40.0,
            # Preço acima da MME9 = VWAP confirmando viés comprador
            "mme9_posicao": "acima",
            "mm200_posicao": "acima",
            "tipo_entrada": "rompimento_maxima",
            # Stop abaixo do ponto C; alvo = CD = AB em distância (R:R 1:2)
            "stop_pts": 180,
            "alvo_pts": 360,
            # Segundo alvo: extensão 1.618 do leg AB
            "alvo2_pts": 500,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    {
        "nome": "ABCD Pattern Tendência Short - WIN 5min",
        "ticker": "WIN",
        "params": {
            "nome": "ABCD Pattern Tendência Short - WIN 5min",
            "ticker": "WIN",
            "timeframe": "5min",
            "direcao": "short",
            "sequencia_candles": 3,
            "sequencia_wick_max_pct": 40.0,
            "mme9_posicao": "abaixo",
            "mm200_posicao": "abaixo",
            "tipo_entrada": "rompimento_minima",
            "stop_pts": 180,
            "alvo_pts": 360,
            "alvo2_pts": 500,
            "horario_inicio": "09:00:00",
            "horario_fim": "16:30:00",
            "max_entradas_dia": 2,
            "slippage_pts": 2.0,
            "custo_por_ponto": 0.20,
        },
    },
    # ------------------------------------------------------------------ #
    #  SETUPS ORIGINAIS                                                   #
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
            "mme9_posicao": "abaixo",   # candle fechou abaixo da MME9 (pull-back)
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
            "mm200_posicao": "acima",   # preço acima da MM200 (tendência de alta)
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
            "ifr2_max": 5,              # IFR(2) abaixo de 5 = sobrevendido extremo
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
