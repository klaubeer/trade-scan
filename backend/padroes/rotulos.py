"""
rotulos.py — Geração e persistência de rótulos para o dataset de treino da CNN.

Forma 1 (automática): importa trades de um backtest_run existente.
  - gain  → label 1
  - loss / breakeven → label 0

Forma 2 (manual): insere um rótulo pontual via API.
"""

from __future__ import annotations

import pandas as pd

from backend.banco.conexao import get_conn


def rotular_por_run(run_id: int) -> dict:
    """
    Gera rótulos a partir dos trades de um backtest_run existente e persiste
    na tabela `rotulos`.

    Retorna contagem de rótulos inseridos e ignorados (duplicatas).
    """
    with get_conn() as conn:
        # Buscar trades do run
        trades = conn.execute(
            """
            SELECT bt.datetime, bt.resultado,
                   br.setup_id,
                   s.ticker,
                   (s.params_json->>'timeframe') AS timeframe
            FROM backtest_trades bt
            JOIN backtest_runs br ON bt.run_id = br.id
            JOIN setups s ON br.setup_id = s.id
            WHERE bt.run_id = ?
            """,
            [run_id],
        ).fetchdf()

    if trades.empty:
        raise ValueError(f"Nenhum trade encontrado para run_id={run_id}")

    ticker = trades["ticker"].iloc[0]
    timeframe = trades["timeframe"].iloc[0]

    inseridos = 0
    ignorados = 0

    with get_conn() as conn:
        for _, row in trades.iterrows():
            label = 1 if row["resultado"] == "gain" else 0
            try:
                conn.execute(
                    """
                    INSERT INTO rotulos (ticker, timeframe, datetime, label, fonte, run_id)
                    VALUES (?, ?, ?, ?, 'backtest', ?)
                    ON CONFLICT (ticker, timeframe, datetime, run_id) DO NOTHING
                    """,
                    [ticker, timeframe, row["datetime"], label, run_id],
                )
                # DuckDB não retorna rowcount para ON CONFLICT; checamos separado
                inseridos += 1
            except Exception:
                ignorados += 1

        conn.commit()

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "run_id": run_id,
        "total_trades": len(trades),
        "inseridos": inseridos,
        "ignorados": ignorados,
        "positivos": int((trades["resultado"] == "gain").sum()),
        "negativos": int((trades["resultado"] != "gain").sum()),
    }


def rotular_manual(
    ticker: str,
    timeframe: str,
    datetime_entrada: str | pd.Timestamp,
    label: int,
) -> dict:
    """
    Insere um rótulo manual (sem run_id).

    label: 0 ou 1
    """
    if label not in (0, 1):
        raise ValueError("label deve ser 0 ou 1")

    dt = pd.Timestamp(datetime_entrada)

    with get_conn() as conn:
        # run_id = NULL para rótulos manuais; usa UNIQUE (ticker, timeframe, datetime, run_id)
        # DuckDB trata NULL como distinto em constraints UNIQUE, então permite múltiplos manuais
        # para o mesmo datetime se necessário. Para evitar duplicata manual exata, checamos antes.
        existente = conn.execute(
            """
            SELECT id FROM rotulos
            WHERE ticker=? AND timeframe=? AND datetime=? AND fonte='manual'
            """,
            [ticker, timeframe, dt],
        ).fetchone()

        if existente:
            # Atualiza o label existente
            conn.execute(
                "UPDATE rotulos SET label=? WHERE id=?",
                [label, existente[0]],
            )
            conn.commit()
            return {"status": "atualizado", "ticker": ticker, "timeframe": timeframe, "datetime": str(dt), "label": label}

        conn.execute(
            """
            INSERT INTO rotulos (ticker, timeframe, datetime, label, fonte)
            VALUES (?, ?, ?, ?, 'manual')
            """,
            [ticker, timeframe, dt, label],
        )
        conn.commit()

    return {"status": "inserido", "ticker": ticker, "timeframe": timeframe, "datetime": str(dt), "label": label}


def buscar_rotulos(
    ticker: str,
    timeframe: str,
    periodo_inicio: str | None = None,
    periodo_fim: str | None = None,
) -> dict[pd.Timestamp, int]:
    """
    Retorna dicionário { datetime → label } para o ticker/timeframe, com
    filtro opcional de período.
    """
    query = "SELECT datetime, label FROM rotulos WHERE ticker=? AND timeframe=?"
    params: list = [ticker, timeframe]

    if periodo_inicio:
        query += " AND datetime >= ?"
        params.append(pd.Timestamp(periodo_inicio))
    if periodo_fim:
        query += " AND datetime <= ?"
        params.append(pd.Timestamp(periodo_fim))

    with get_conn() as conn:
        df = conn.execute(query, params).fetchdf()

    if df.empty:
        return {}

    return {pd.Timestamp(row["datetime"]): int(row["label"]) for _, row in df.iterrows()}


def resumo_rotulos(ticker: str, timeframe: str) -> dict:
    """Retorna contagens de positivos/negativos disponíveis para treino."""
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN label=1 THEN 1 ELSE 0 END) AS positivos,
                SUM(CASE WHEN label=0 THEN 1 ELSE 0 END) AS negativos,
                MIN(datetime) AS periodo_inicio,
                MAX(datetime) AS periodo_fim
            FROM rotulos
            WHERE ticker=? AND timeframe=?
            """,
            [ticker, timeframe],
        ).fetchone()

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "total": int(row[0] or 0),
        "positivos": int(row[1] or 0),
        "negativos": int(row[2] or 0),
        "periodo_inicio": str(row[3]) if row[3] else None,
        "periodo_fim": str(row[4]) if row[4] else None,
    }
