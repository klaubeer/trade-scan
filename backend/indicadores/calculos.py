import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Médias móveis
# ---------------------------------------------------------------------------

def calcular_mm200(df: pd.DataFrame) -> pd.Series:
    """Média móvel simples de 200 períodos."""
    return df["close"].rolling(window=200, min_periods=200).mean()


def calcular_mme9(df: pd.DataFrame) -> pd.Series:
    """Média móvel exponencial de 9 períodos."""
    return df["close"].ewm(span=9, adjust=False, min_periods=9).mean()


# ---------------------------------------------------------------------------
# IFR2 — RSI de 2 períodos (Wilder)
# ---------------------------------------------------------------------------

def calcular_ifr2(df: pd.DataFrame) -> pd.Series:
    periodo = 2
    delta = df["close"].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    # Smoothing de Wilder = EMA com alpha = 1/periodo
    media_ganho = ganho.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()
    media_perda = perda.ewm(alpha=1 / periodo, adjust=False, min_periods=periodo).mean()

    rs = media_ganho / media_perda.replace(0, np.nan)
    ifr2 = 100 - (100 / (1 + rs))
    return ifr2


# ---------------------------------------------------------------------------
# Contexto diário
# ---------------------------------------------------------------------------

def calcular_gap_abertura(df: pd.DataFrame) -> pd.Series:
    """
    Gap de abertura em pontos: open do 1º candle do dia − close do último candle do dia anterior.
    Retorna série alinhada com o DataFrame original (NaN em candles que não são o 1º do dia).
    """
    df = df.copy()
    df["_data"] = df["datetime"].dt.date

    # Close do último candle de cada dia
    close_dia = (
        df.groupby("_data")["close"]
        .last()
        .reset_index()
        .rename(columns={"_data": "_data", "close": "_close_anterior"})
    )
    close_dia["_data_prox"] = close_dia["_data"].shift(-1)
    close_map = close_dia.set_index("_data_prox")["_close_anterior"].to_dict()

    # Open do 1º candle de cada dia
    idx_primeiro = df.groupby("_data")["datetime"].idxmin()
    gap = pd.Series(np.nan, index=df.index)
    for idx in idx_primeiro:
        data = df.loc[idx, "_data"]
        close_ant = close_map.get(data, np.nan)
        gap.loc[idx] = df.loc[idx, "open"] - close_ant

    return gap


def calcular_range_acumulado(df: pd.DataFrame) -> pd.Series:
    """
    Range acumulado do dia em % = (max_high - min_low desde abertura) / open_dia * 100.
    Calculado candle a candle, acumulando dentro do pregão.
    """
    df = df.copy()
    df["_data"] = df["datetime"].dt.date

    range_pct = pd.Series(np.nan, index=df.index)

    for data, grupo in df.groupby("_data"):
        open_dia = grupo["open"].iloc[0]
        if open_dia == 0:
            continue
        high_acum = grupo["high"].expanding().max()
        low_acum = grupo["low"].expanding().min()
        range_pct.loc[grupo.index] = (high_acum - low_acum) / open_dia * 100

    return range_pct


def calcular_abertura_dia(df: pd.DataFrame) -> pd.Series:
    """
    Retorna o preço de abertura do primeiro candle de cada dia,
    propagado para todos os candles do mesmo pregão.
    Necessário para calcular alvos dinâmicos baseados em % do dia.
    """
    df = df.copy()
    df["_data"] = df["datetime"].dt.date
    abertura_map = df.groupby("_data")["open"].first().to_dict()
    return df["_data"].map(abertura_map)


def calcular_variacao_dia(df: pd.DataFrame) -> pd.Series:
    """
    Variação % direcional do dia: (close_atual - open_dia) / open_dia * 100.
    Positivo = dia subindo, negativo = dia caindo.
    Calculado candle a candle dentro do pregão.
    """
    df = df.copy()
    df["_data"] = df["datetime"].dt.date

    var_pct = pd.Series(np.nan, index=df.index)

    for data, grupo in df.groupby("_data"):
        open_dia = grupo["open"].iloc[0]
        if open_dia == 0:
            continue
        var_pct.loc[grupo.index] = (grupo["close"] - open_dia) / open_dia * 100

    return var_pct


def calcular_primeiro_candle(df: pd.DataFrame, timeframe_ref: str = "15min") -> pd.Series:
    """
    Direção do primeiro candle do pregão: 'alta' se close > open, 'baixa' caso contrário.
    Retorna série com valor preenchido para todos os candles do mesmo pregão.
    """
    df = df.copy()
    df["_data"] = df["datetime"].dt.date

    direcao_por_dia: dict = {}
    for data, grupo in df.groupby("_data"):
        primeiro = grupo.iloc[0]
        direcao_por_dia[data] = "alta" if primeiro["close"] >= primeiro["open"] else "baixa"

    return df["_data"].map(direcao_por_dia)


def calcular_tendencia_semanal(df: pd.DataFrame) -> pd.Series:
    """
    Tendência da semana corrente baseada no OHLC semanal agregado.
    'alta' se close_semana > open_semana + 0.5%
    'baixa' se close_semana < open_semana - 0.5%
    'lateral' caso contrário.
    Retorna série com valor preenchido para todos os candles da mesma semana.
    """
    df = df.copy()
    df["_semana"] = df["datetime"].dt.to_period("W")

    tendencia_por_semana: dict = {}
    for semana, grupo in df.groupby("_semana"):
        open_s = grupo["open"].iloc[0]
        close_s = grupo["close"].iloc[-1]
        if open_s == 0:
            tendencia_por_semana[semana] = "lateral"
            continue
        var_pct = (close_s - open_s) / open_s * 100
        if var_pct > 0.5:
            tendencia_por_semana[semana] = "alta"
        elif var_pct < -0.5:
            tendencia_por_semana[semana] = "baixa"
        else:
            tendencia_por_semana[semana] = "lateral"

    return df["_semana"].map(tendencia_por_semana)


# ---------------------------------------------------------------------------
# ADX — Average Directional Index (Wilder, período padrão 14)
# ---------------------------------------------------------------------------

def calcular_adx(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    """
    ADX(14) no timeframe operacional.
    Mede a força da tendência (0-100), independente da direção.
    >25 = tendência, <20 = lateral.
    """
    high = df["high"]
    low  = df["low"]
    prev_close = df["close"].shift(1)
    prev_high  = high.shift(1)
    prev_low   = low.shift(1)

    # True Range
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)

    # Directional Movement (+DM e -DM)
    dm_pos = (high - prev_high).clip(lower=0)
    dm_neg = (prev_low - low).clip(lower=0)
    # Quando ambos positivos, manter apenas o maior
    ambos = (dm_pos > 0) & (dm_neg > 0)
    dm_pos = dm_pos.where(~ambos | (dm_pos >= dm_neg), 0.0)
    dm_neg = dm_neg.where(~ambos | (dm_neg >  dm_pos), 0.0)

    # Wilder smoothing: alpha = 1/periodo
    alpha = 1.0 / periodo
    kw = dict(alpha=alpha, adjust=False, min_periods=periodo)

    tr_s      = tr.ewm(**kw).mean()
    dm_pos_s  = dm_pos.ewm(**kw).mean()
    dm_neg_s  = dm_neg.ewm(**kw).mean()

    di_pos = 100 * dm_pos_s / tr_s.replace(0, np.nan)
    di_neg = 100 * dm_neg_s / tr_s.replace(0, np.nan)
    dx     = 100 * (di_pos - di_neg).abs() / (di_pos + di_neg).replace(0, np.nan)
    adx    = dx.ewm(**kw).mean()

    return adx.round(2)


# ---------------------------------------------------------------------------
# ATR Diário — calculado nas barras D1 e propagado para o intraday
# ---------------------------------------------------------------------------

def calcular_atr_diario(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    """
    ATR(14) diário (série D1), mapeado para cada candle intraday.
    Usa o ATR do dia ANTERIOR para evitar lookahead bias.
    """
    df = df.copy()
    df["_data"] = df["datetime"].dt.date

    daily = (
        df.groupby("_data")
        .agg(high=("high", "max"), low=("low", "min"), close=("close", "last"))
        .reset_index()
    )

    prev_close = daily["close"].shift(1)
    tr_d = pd.concat([
        daily["high"] - daily["low"],
        (daily["high"] - prev_close).abs(),
        (daily["low"]  - prev_close).abs(),
    ], axis=1).max(axis=1)

    alpha = 1.0 / periodo
    daily["atr_diario"] = tr_d.ewm(alpha=alpha, adjust=False, min_periods=periodo).mean()
    # Shift: o ATR de hoje usa dados até ontem (sem lookahead)
    daily["atr_diario"] = daily["atr_diario"].shift(1)

    atr_map = daily.set_index("_data")["atr_diario"].to_dict()
    return df["_data"].map(atr_map)


# ---------------------------------------------------------------------------
# Range do dia em pontos (expansão da máxima − mínima até o candle atual)
# ---------------------------------------------------------------------------

def calcular_range_dia_pts(df: pd.DataFrame) -> pd.Series:
    """Range acumulado do dia em pontos (high_max - low_min até o candle atual)."""
    df = df.copy()
    df["_data"] = df["datetime"].dt.date
    range_pts = pd.Series(np.nan, index=df.index)
    for data, grupo in df.groupby("_data"):
        high_acum = grupo["high"].expanding().max()
        low_acum  = grupo["low"].expanding().min()
        range_pts.loc[grupo.index] = high_acum - low_acum
    return range_pts


# ---------------------------------------------------------------------------
# Enriquecimento completo
# ---------------------------------------------------------------------------

def enriquecer_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe DataFrame de candles e adiciona todas as colunas de indicadores.
    Mantém os dados originais intactos.
    """
    df = df.copy().sort_values("datetime").reset_index(drop=True)

    df["mm200"] = calcular_mm200(df)
    df["mme9"] = calcular_mme9(df)
    df["ifr2"] = calcular_ifr2(df)
    df["gap_abertura"] = calcular_gap_abertura(df)
    df["range_acumulado_pct"] = calcular_range_acumulado(df)
    df["abertura_dia"] = calcular_abertura_dia(df)
    df["variacao_dia_pct"] = calcular_variacao_dia(df)
    df["primeiro_candle_dir"] = calcular_primeiro_candle(df)
    df["tendencia_semanal"] = calcular_tendencia_semanal(df)
    df["adx"] = calcular_adx(df)
    df["atr_diario"] = calcular_atr_diario(df)
    df["range_dia_pts"] = calcular_range_dia_pts(df)

    # Pavio
    df["corpo"] = (df["close"] - df["open"]).abs()
    df["pavio_superior"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["pavio_inferior"] = df[["open", "close"]].min(axis=1) - df["low"]
    df["pavio_total"] = df["pavio_superior"] + df["pavio_inferior"]
    df["range_candle"] = df["high"] - df["low"]

    return df
