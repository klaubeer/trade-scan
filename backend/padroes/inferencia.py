"""
inferencia.py — Carregamento de modelos treinados e predição.

Cache simples em memória para não recarregar o modelo a cada chamada
durante o backtesting (múltiplas predições por execução).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

from backend.banco.conexao import get_conn
from backend.indicadores.calculos import enriquecer_dataframe
from backend.padroes.modelo import PatternCNN
from backend.padroes.pipeline import N_FEATURES, SEQ_LEN_PADRAO, extrair_janela

MODELS_DIR = Path("models")


@lru_cache(maxsize=8)
def _carregar_modelo(model_id: str) -> tuple[PatternCNN, dict]:
    """
    Carrega modelo e config do disco. Resultado em cache por model_id.
    Retorna (modelo, config).
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT model_path, config_json FROM ml_models WHERE id=?",
            [model_id],
        ).fetchone()

    if row is None:
        raise ValueError(f"Modelo {model_id} não encontrado no banco")

    pasta = Path(row[0])
    config = json.loads(row[1]) if isinstance(row[1], str) else row[1]

    seq_len = config.get("seq_len", SEQ_LEN_PADRAO)
    n_features = config.get("n_features", N_FEATURES)

    modelo = PatternCNN(n_features=n_features, seq_len=seq_len)
    modelo.load_state_dict(torch.load(pasta / "model.pt", map_location="cpu", weights_only=True))
    modelo.eval()

    return modelo, config


def prever(
    model_id: str,
    ticker: str,
    timeframe: str,
    datetime_fim: str | pd.Timestamp,
) -> float:
    """
    Retorna a probabilidade de entrada válida (classe 1) para a janela que
    termina em `datetime_fim`.

    Parâmetros
    ----------
    model_id     : UUID do modelo treinado
    ticker       : ex. "WIN"
    timeframe    : ex. "5min"
    datetime_fim : candle de referência (entrada sendo avaliada)

    Retorno
    -------
    float entre 0.0 e 1.0 (probabilidade softmax da classe 1)
    """
    modelo, config = _carregar_modelo(model_id)
    seq_len = config.get("seq_len", SEQ_LEN_PADRAO)

    dt_fim = pd.Timestamp(datetime_fim)

    # Carrega candles suficientes (janela + margem para indicadores)
    margem = 300  # garante mm200 calculável
    with get_conn() as conn:
        df_raw = conn.execute(
            """
            SELECT * FROM candles
            WHERE ticker=? AND timeframe=? AND datetime <= ?
            ORDER BY datetime DESC
            LIMIT ?
            """,
            [ticker, timeframe, dt_fim, seq_len + margem],
        ).fetchdf()

    if df_raw.empty or len(df_raw) < seq_len:
        return 0.0  # sem dados suficientes → não confirma

    df_raw = df_raw.sort_values("datetime").reset_index(drop=True)
    df = enriquecer_dataframe(df_raw)

    # Posição do candle de referência
    idx = df[df["datetime"] == dt_fim].index
    if len(idx) == 0:
        return 0.0

    janela = extrair_janela(df, int(idx[-1]), seq_len)
    if janela is None:
        return 0.0

    tensor = torch.tensor(janela[np.newaxis], dtype=torch.float32)  # (1, n_features, seq_len)
    with torch.no_grad():
        logits = modelo(tensor)
        prob = F.softmax(logits, dim=1)[0, 1].item()

    return float(prob)


def listar_modelos() -> list[dict]:
    """Lista todos os modelos treinados disponíveis no banco."""
    with get_conn() as conn:
        df = conn.execute(
            """
            SELECT id, nome, ticker, timeframe, n_features, seq_len,
                   train_periodo_inicio, train_periodo_fim,
                   test_periodo_inicio, test_periodo_fim,
                   metrics_json, criado_em
            FROM ml_models
            ORDER BY criado_em DESC
            """
        ).fetchdf()

    if df.empty:
        return []

    resultado = []
    for _, row in df.iterrows():
        metrics = json.loads(row["metrics_json"]) if isinstance(row["metrics_json"], str) else row["metrics_json"]
        resultado.append({
            "id": row["id"],
            "nome": row["nome"],
            "ticker": row["ticker"],
            "timeframe": row["timeframe"],
            "n_features": int(row["n_features"]),
            "seq_len": int(row["seq_len"]),
            "train_periodo_inicio": str(row["train_periodo_inicio"]) if row["train_periodo_inicio"] else None,
            "train_periodo_fim": str(row["train_periodo_fim"]) if row["train_periodo_fim"] else None,
            "criado_em": str(row["criado_em"]),
            "metricas_val": metrics.get("val") if metrics else None,
            "metricas_teste": metrics.get("teste") if metrics else None,
        })

    return resultado


def invalidar_cache(model_id: str | None = None):
    """
    Invalida o cache LRU do modelo (útil após re-treino).
    Se model_id=None, limpa todo o cache.
    """
    _carregar_modelo.cache_clear()
