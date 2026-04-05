import pandas as pd
from backend.banco.conexao import get_conn


def upsert_candles(df: pd.DataFrame) -> dict:
    """
    Insere candles no DuckDB ignorando duplicatas por (ticker, timeframe, datetime).
    Retorna contagem de inseridos e duplicados.
    """
    if df.empty:
        return {"inseridos": 0, "duplicados": 0}

    ticker = df["ticker"].iloc[0]
    timeframe = df["timeframe"].iloc[0]

    with get_conn() as conn:
        # Criar tabela temporária com os novos dados
        conn.execute("CREATE TEMP TABLE IF NOT EXISTS _tmp_candles AS SELECT * FROM candles WHERE 1=0")
        conn.execute("DELETE FROM _tmp_candles")
        conn.register("_df_candles", df)
        conn.execute("INSERT INTO _tmp_candles SELECT * FROM _df_candles")

        # Contar quantos já existem
        duplicados = conn.execute("""
            SELECT COUNT(*) FROM _tmp_candles t
            WHERE EXISTS (
                SELECT 1 FROM candles c
                WHERE c.ticker = t.ticker
                  AND c.timeframe = t.timeframe
                  AND c.datetime = t.datetime
            )
        """).fetchone()[0]

        # Inserir apenas os que não existem
        conn.execute("""
            INSERT INTO candles
            SELECT t.* FROM _tmp_candles t
            WHERE NOT EXISTS (
                SELECT 1 FROM candles c
                WHERE c.ticker = t.ticker
                  AND c.timeframe = t.timeframe
                  AND c.datetime = t.datetime
            )
        """)

        inseridos = len(df) - duplicados

    return {"inseridos": inseridos, "duplicados": duplicados}


def periodo_disponivel(ticker: str, timeframe: str) -> dict | None:
    """Retorna o período de dados disponíveis para um ativo/timeframe."""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT MIN(datetime), MAX(datetime)
            FROM candles
            WHERE ticker = ? AND timeframe = ?
        """, [ticker, timeframe]).fetchone()

    if row and row[0]:
        return {"inicio": str(row[0].date()), "fim": str(row[1].date())}
    return None
