import io
import re
import pandas as pd
from datetime import timedelta


COLUNAS_ESPERADAS = [
    "Ticker", "Data", "Hora",
    "Abertura", "Máxima", "Mínima", "Fechamento",
    "VolumeFinanceiro", "QtdContratos",
]

TICKER_MAP = {
    r"^WIN": "WIN",
    r"^WDO": "WDO",
    r"^BIT": "BITFUT",
}

TIMEFRAME_MAP = [
    (60,   "1min"),
    (300,  "5min"),
    (900,  "15min"),
    (3600, "60min"),
]


class ErroIngestao(Exception):
    pass


def parse_csv(conteudo: bytes) -> pd.DataFrame:
    """Lê CSV do Profit e retorna DataFrame normalizado.

    Suporta dois formatos:
    - Com cabeçalho: primeira linha contém os nomes das colunas
    - Sem cabeçalho: arquivo do Profit exportado diretamente (formato mais comum)
    """
    df = None
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            # Tentativa 1: com cabeçalho
            candidato = pd.read_csv(
                io.BytesIO(conteudo),
                sep=";",
                encoding=encoding,
                decimal=",",
                thousands=".",
            )
            candidato.columns = [c.strip() for c in candidato.columns]

            if all(c in candidato.columns for c in COLUNAS_ESPERADAS):
                df = candidato
                break

            # Tentativa 2: sem cabeçalho (Profit padrão — dados na primeira linha)
            candidato_sem_header = pd.read_csv(
                io.BytesIO(conteudo),
                sep=";",
                encoding=encoding,
                decimal=",",
                thousands=".",
                header=None,
                names=COLUNAS_ESPERADAS,
            )
            df = candidato_sem_header
            break

        except UnicodeDecodeError:
            continue

    if df is None:
        raise ErroIngestao("Não foi possível decodificar o arquivo CSV.")

    faltando = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
    if faltando:
        raise ErroIngestao(f"Colunas faltando no CSV: {faltando}")

    if df.empty:
        raise ErroIngestao("CSV está vazio.")

    # Combinar Data + Hora em datetime
    try:
        df["datetime"] = pd.to_datetime(
            df["Data"].astype(str) + " " + df["Hora"].astype(str),
            dayfirst=True,
        )
    except Exception as e:
        raise ErroIngestao(f"Erro ao parsear datas: {e}")

    ticker_raw = str(df["Ticker"].iloc[0]).strip().upper()
    ticker = _normalizar_ticker(ticker_raw)
    timeframe = _detectar_timeframe(df["datetime"])

    df = df.rename(columns={
        "Abertura": "open",
        "Máxima": "high",
        "Mínima": "low",
        "Fechamento": "close",
        "VolumeFinanceiro": "volume_fin",
        "QtdContratos": "qty",
    })

    df["ticker"] = ticker
    df["timeframe"] = timeframe

    for col in ("open", "high", "low", "close", "volume_fin"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["qty"] = pd.to_numeric(df["qty"], errors="coerce").astype("Int64")

    df = df.dropna(subset=["datetime", "open", "high", "low", "close"])
    df = df.sort_values("datetime").reset_index(drop=True)

    return df[["ticker", "timeframe", "datetime", "open", "high", "low", "close", "volume_fin", "qty"]]


def _normalizar_ticker(ticker_raw: str) -> str:
    for pattern, nome in TICKER_MAP.items():
        if re.match(pattern, ticker_raw):
            return nome
    raise ErroIngestao(
        f"Ticker '{ticker_raw}' não reconhecido. Suportados: WIN, WDO, BITFUT."
    )


def _detectar_timeframe(serie_dt: pd.Series) -> str:
    if len(serie_dt) < 2:
        raise ErroIngestao("CSV com menos de 2 candles — impossível detectar timeframe.")

    deltas = serie_dt.sort_values().diff().dropna()
    # Filtrar apenas deltas positivos (ignorar mudanças de sessão overnight)
    deltas_segundos = deltas[deltas > timedelta(0)].dt.total_seconds()
    if deltas_segundos.empty:
        raise ErroIngestao("Não foi possível detectar o timeframe.")

    mediana = deltas_segundos.median()

    for segundos, nome in TIMEFRAME_MAP:
        if abs(mediana - segundos) / segundos < 0.5:
            return nome

    # Diário
    if mediana > 3600 * 4:
        return "D"

    raise ErroIngestao(f"Timeframe não reconhecido (delta mediano: {mediana:.0f}s).")
