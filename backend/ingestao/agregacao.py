import pandas as pd
from backend.banco.conexao import get_conn
from backend.ingestao.deduplicacao import upsert_candles


# Mapeamento: timeframe base → timeframes derivados possíveis
DERIVADOS = {
    "1min":  ["5min", "15min", "60min", "D", "W"],
    "5min":  ["15min", "60min", "D", "W"],
    "15min": ["60min", "D", "W"],
    "60min": ["D", "W"],
}

RESAMPLE_RULES = {
    "5min":  "5min",
    "15min": "15min",
    "60min": "60h",
    "D":     "B",     # dias úteis — ajustado abaixo
    "W":     "W-MON", # semana começa segunda
}


def agregar_timeframes(ticker: str, timeframe_base: str) -> dict:
    """
    Gera timeframes derivados a partir do timeframe base já armazenado no DuckDB.
    Retorna contagem de candles inseridos por timeframe derivado.
    """
    derivados = DERIVADOS.get(timeframe_base, [])
    if not derivados:
        return {}

    with get_conn() as conn:
        df_base = conn.execute("""
            SELECT datetime, open, high, low, close, volume_fin, qty
            FROM candles
            WHERE ticker = ? AND timeframe = ?
            ORDER BY datetime
        """, [ticker, timeframe_base]).df()

    if df_base.empty:
        return {}

    df_base["datetime"] = pd.to_datetime(df_base["datetime"])
    df_base = df_base.set_index("datetime")

    resultados = {}
    for tf in derivados:
        df_agg = _agregar(df_base, tf)
        if df_agg.empty:
            continue

        df_agg["ticker"] = ticker
        df_agg["timeframe"] = tf
        df_agg = df_agg.reset_index().rename(columns={"index": "datetime"})
        df_agg = df_agg[["ticker", "timeframe", "datetime", "open", "high", "low", "close", "volume_fin", "qty"]]

        info = upsert_candles(df_agg)
        resultados[tf] = info

    return resultados


def _agregar(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    rule = _rule(timeframe)

    agg = df.resample(rule, label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume_fin=("volume_fin", "sum"),
        qty=("qty", "sum"),
    ).dropna(subset=["open"])

    return agg


def _rule(timeframe: str) -> str:
    mapa = {
        "5min":  "5min",
        "15min": "15min",
        "60min": "60min",
        "D":     "D",
        "W":     "W-FRI",  # semana encerra na sexta
    }
    return mapa[timeframe]
