import pandas as pd
import numpy as np
from backend.schemas.modelos import SetupParams


def _mask_seq(df: pd.DataFrame, N: int, long: bool, wick_max_pct: float | None) -> pd.Series:
    """
    Máscara vetorizada de sequência direcional de N candles.
    long=True: candles de alta quebrando máximas consecutivas.
    long=False: candles de baixa quebrando mínimas consecutivas.
    """
    if long:
        eh_direcional = df["close"] > df["open"]
        rompe_anterior = df["high"] > df["high"].shift(1)
    else:
        eh_direcional = df["close"] < df["open"]
        rompe_anterior = df["low"] < df["low"].shift(1)

    seq = pd.Series(True, index=df.index)
    for k in range(N):
        seq &= eh_direcional.shift(k).fillna(False)
    for k in range(N - 1):
        seq &= rompe_anterior.shift(k).fillna(False)

    if wick_max_pct is not None:
        limite = wick_max_pct / 100.0
        wick_ok = (df["pavio_total"] / df["range_candle"].replace(0, np.nan)) <= limite
        for k in range(N):
            seq &= wick_ok.shift(k).fillna(False)

    return seq


def gerar_entradas(df: pd.DataFrame, setup: SetupParams) -> pd.Series:
    """
    Retorna série sinalizada:
      +1 = entrada long
      -1 = entrada short
       0 = sem entrada
    """
    mask = pd.Series(True, index=df.index)

    if setup.range_candle_min is not None:
        mask &= df["range_candle"] >= setup.range_candle_min

    if setup.pavio_total_max is not None:
        mask &= df["pavio_total"] <= setup.pavio_total_max

    if setup.pavio_superior_max is not None:
        mask &= df["pavio_superior"] <= setup.pavio_superior_max

    if setup.pavio_inferior_max is not None:
        mask &= df["pavio_inferior"] <= setup.pavio_inferior_max

    if setup.mm200_posicao == "acima":
        mask &= df["close"] > df["mm200"]
    elif setup.mm200_posicao == "abaixo":
        mask &= df["close"] < df["mm200"]

    if setup.mme9_posicao == "acima":
        mask &= df["close"] > df["mme9"]
    elif setup.mme9_posicao == "abaixo":
        mask &= df["close"] < df["mme9"]

    if setup.ifr2_max is not None:
        mask &= df["ifr2"] < setup.ifr2_max

    if setup.ifr2_min is not None:
        mask &= df["ifr2"] > setup.ifr2_min

    if setup.range_acumulado_max_pct is not None:
        mask &= df["range_acumulado_pct"] <= setup.range_acumulado_max_pct

    if setup.gap_abertura_min is not None:
        mask &= df["gap_abertura"].abs() >= setup.gap_abertura_min

    if setup.primeiro_candle_direcao is not None:
        mask &= df["primeiro_candle_dir"] == setup.primeiro_candle_direcao

    if setup.tendencia_semanal and setup.tendencia_semanal != "qualquer":
        mask &= df["tendencia_semanal"] == setup.tendencia_semanal

    # ADX: força de tendência mínima
    if setup.adx_min is not None:
        mask &= df["adx"].fillna(0) >= setup.adx_min

    # ATR diário: range do dia deve ser >= fator × ATR(14) diário
    if setup.atr_fator_range is not None:
        atr_ok = df["atr_diario"].notna() & (
            df["range_dia_pts"] >= setup.atr_fator_range * df["atr_diario"]
        )
        mask &= atr_ok.fillna(False)

    # Filtro de horário
    hora = df["datetime"].dt.time
    mask &= hora >= setup.horario_inicio
    mask &= hora < setup.horario_fim

    # Sem NaN nas colunas críticas
    mask &= df["mm200"].notna() | (setup.mm200_posicao is None)
    mask &= df["mme9"].notna() | (setup.mme9_posicao is None)
    mask &= df["ifr2"].notna() | (setup.ifr2_max is None and setup.ifr2_min is None)

    mask = mask.fillna(False)

    # --- Montagem da série sinalizada ---
    if setup.sequencia_candles is not None:
        N = setup.sequencia_candles
        wick = setup.sequencia_wick_max_pct

        if setup.direcao == "long":
            seq_long = _mask_seq(df, N, long=True, wick_max_pct=wick)
            entries = (mask & seq_long).astype(int)

        elif setup.direcao == "short":
            seq_short = _mask_seq(df, N, long=False, wick_max_pct=wick)
            entries = -(mask & seq_short).astype(int)

        else:  # ambos — detecta as duas direções independentemente
            seq_long  = _mask_seq(df, N, long=True,  wick_max_pct=wick)
            seq_short = _mask_seq(df, N, long=False, wick_max_pct=wick)
            entries = pd.Series(0, index=df.index, dtype=int)
            entries[mask & seq_long]  =  1
            entries[mask & seq_short] = -1  # short sobrescreve se ambos (raro)

    else:
        # Sem sequência: direção fixa
        if setup.direcao == "long":
            entries = mask.astype(int)
        elif setup.direcao == "short":
            entries = -mask.astype(int)
        else:  # ambos sem sequência → long por padrão (comportamento anterior)
            entries = mask.astype(int)

    # Filtro de zonas de S/R: candle gatilho não pode tocar nenhum nível de % do dia
    if setup.sequencia_filtrar_zonas and setup.sequencia_candles is not None:
        _NIVEIS_PCT = [0.000, 0.005, 0.010, 0.015, 0.020, 0.025, 0.030]
        zona_hit = pd.Series(False, index=df.index)
        for pct in _NIVEIS_PCT:
            nivel_pos = df["abertura_dia"] * (1 + pct)
            zona_hit |= (df["low"] <= nivel_pos) & (df["high"] >= nivel_pos)
            if pct > 0:
                nivel_neg = df["abertura_dia"] * (1 - pct)
                zona_hit |= (df["low"] <= nivel_neg) & (df["high"] >= nivel_neg)
        entries[zona_hit] = 0

    return entries


def calcular_preco_entrada(candle: pd.Series, setup: SetupParams) -> float:
    """
    Calcula o preço de entrada com base no tipo de entrada e direção.
    """
    if setup.tipo_entrada in ("fechamento_gatilho", "rompimento_fechamento"):
        return candle["close"]
    elif setup.tipo_entrada == "rompimento_maxima":
        return candle["high"] + 1
    elif setup.tipo_entrada == "rompimento_minima":
        return candle["low"] - 1
    return candle["close"]


def extrair_contexto(df: pd.DataFrame, idx: int) -> dict:
    candle = df.iloc[idx]
    range_pct = candle.get("range_acumulado_pct", float("nan"))

    if pd.isna(range_pct):
        faixa_range = "desconhecido"
    elif range_pct < 0.5:
        faixa_range = "<0.5%"
    elif range_pct < 1.0:
        faixa_range = "0.5-1%"
    elif range_pct < 1.5:
        faixa_range = "1-1.5%"
    elif range_pct < 2.0:
        faixa_range = "1.5-2%"
    elif range_pct < 2.5:
        faixa_range = "2-2.5%"
    elif range_pct < 3.0:
        faixa_range = "2.5-3%"
    else:
        faixa_range = ">3%"

    hora = candle["datetime"].time()
    from datetime import time as t
    periodo_dia = "manha" if hora < t(12, 0) else "tarde"

    gap = candle.get("gap_abertura", float("nan"))
    if pd.isna(gap):
        gap_tipo = "desconhecido"
    elif gap > 0:
        gap_tipo = "positivo"
    elif gap < 0:
        gap_tipo = "negativo"
    else:
        gap_tipo = "sem_gap"

    var_dia = candle.get("variacao_dia_pct", float("nan"))
    LIMIARES = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    ROTULOS  = ["<-3%", "-3 a -2.5%", "-2.5 a -2%", "-2 a -1.5%", "-1.5 a -1%",
                "-1 a -0.5%", "-0.5 a 0%", "0 a 0.5%", "0.5 a 1%",
                "1 a 1.5%", "1.5 a 2%", "2 a 2.5%", "2.5 a 3%", ">3%"]
    if pd.isna(var_dia):
        faixa_var = "desconhecido"
    else:
        faixa_var = ROTULOS[-1]
        for i, lim in enumerate(LIMIARES):
            if var_dia < lim:
                faixa_var = ROTULOS[i]
                break

    return {
        "tendencia_semanal": candle.get("tendencia_semanal", None),
        "periodo_dia": periodo_dia,
        "gap_abertura_pts": round(float(gap), 1) if not pd.isna(gap) else None,
        "gap_abertura_tipo": gap_tipo,
        "range_acumulado_pct": round(float(range_pct), 2) if not pd.isna(range_pct) else None,
        "range_acumulado_faixa": faixa_range,
        "variacao_dia_pct": round(float(var_dia), 2) if not pd.isna(var_dia) else None,
        "variacao_dia_faixa": faixa_var,
        "mm200_posicao": "acima" if candle["close"] > candle.get("mm200", float("nan")) else "abaixo",
        "mme9_posicao": "acima" if candle["close"] > candle.get("mme9", float("nan")) else "abaixo",
        "ifr2_valor": round(float(candle.get("ifr2", float("nan"))), 1)
            if not pd.isna(candle.get("ifr2", float("nan"))) else None,
    }
