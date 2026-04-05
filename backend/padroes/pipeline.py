"""
pipeline.py — Criação de janelas deslizantes e normalização por janela.

Princípios críticos:
- Normalização por janela (z-score), nunca global — evita lookahead bias.
- Janela usa apenas candles ANTERIORES ao ponto de entrada (inclusive).
- NaN em indicadores (ex: mm200 nos primeiros 200 candles) são preenchidos com 0
  após normalização — o modelo aprende a ignorar pela ausência de variância.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FEATURES = [
    "open",
    "high",
    "low",
    "close",
    "volume_fin",
    "mm200",
    "mme9",
    "ifr2",
    "range_acumulado_pct",
    "range_candle",
]

N_FEATURES = len(FEATURES)  # 10
SEQ_LEN_PADRAO = 50


def normalizar_janela(janela: np.ndarray) -> np.ndarray:
    """
    Normaliza cada feature dentro da janela individualmente (z-score).

    janela shape: (n_features, seq_len)
    Retorna array do mesmo shape normalizado.
    """
    media = janela.mean(axis=1, keepdims=True)
    desvio = janela.std(axis=1, keepdims=True)
    desvio[desvio == 0] = 1.0  # evita divisão por zero para features constantes
    normalizado = (janela - media) / desvio
    # NaN residuais (feature toda NaN, ex: mm200 no início da série)
    normalizado = np.nan_to_num(normalizado, nan=0.0)
    return normalizado


def extrair_janela(
    df: pd.DataFrame,
    indice_fim: int,
    seq_len: int = SEQ_LEN_PADRAO,
) -> np.ndarray | None:
    """
    Extrai e normaliza uma janela de `seq_len` candles terminando em `indice_fim`.

    Parâmetros
    ----------
    df : DataFrame enriquecido (saída de `enriquecer_dataframe`)
    indice_fim : posição inteira no DataFrame (inclusive)
    seq_len : tamanho da janela (padrão 50)

    Retorno
    -------
    np.ndarray shape (n_features, seq_len) normalizado, ou None se não há
    candles suficientes antes do ponto de entrada.
    """
    indice_inicio = indice_fim - seq_len + 1
    if indice_inicio < 0:
        return None

    fatia = df.iloc[indice_inicio : indice_fim + 1]

    # Verificar se todas as features estão presentes
    faltando = [f for f in FEATURES if f not in fatia.columns]
    if faltando:
        raise ValueError(f"Colunas ausentes no DataFrame: {faltando}")

    janela = fatia[FEATURES].values.T.astype(np.float32)  # (n_features, seq_len)
    return normalizar_janela(janela)


def construir_dataset(
    df: pd.DataFrame,
    rotulos: dict[pd.Timestamp, int],
    seq_len: int = SEQ_LEN_PADRAO,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Constrói o dataset completo de janelas + labels para treino.

    Parâmetros
    ----------
    df : DataFrame enriquecido com índice datetime resetado (coluna 'datetime')
    rotulos : { datetime → 0 ou 1 }
    seq_len : tamanho da janela

    Retorno
    -------
    X : np.ndarray shape (n_amostras, n_features, seq_len)
    y : np.ndarray shape (n_amostras,) com valores 0 ou 1
    """
    df_reset = df.reset_index(drop=True)

    # Mapeia datetime → índice posicional
    if "datetime" not in df_reset.columns:
        raise ValueError("DataFrame deve ter coluna 'datetime'")

    dt_para_idx = {pd.Timestamp(dt): i for i, dt in enumerate(df_reset["datetime"])}

    X_lista = []
    y_lista = []

    for dt, label in rotulos.items():
        ts = pd.Timestamp(dt)
        if ts not in dt_para_idx:
            continue
        idx = dt_para_idx[ts]
        janela = extrair_janela(df_reset, idx, seq_len)
        if janela is None:
            continue
        X_lista.append(janela)
        y_lista.append(label)

    if not X_lista:
        raise ValueError("Nenhuma janela válida construída. Verifique os rótulos e o período.")

    return np.stack(X_lista), np.array(y_lista, dtype=np.int64)


def split_temporal(
    X: np.ndarray,
    y: np.ndarray,
    proporcao_treino: float = 0.70,
    proporcao_val: float = 0.15,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Divide X e y em treino/val/teste mantendo a ordem cronológica.
    NÃO faz shuffle — séries temporais não podem ser embaralhadas.

    Retorno: X_treino, y_treino, X_val, y_val, X_teste, y_teste
    """
    n = len(X)
    fim_treino = int(n * proporcao_treino)
    fim_val = int(n * (proporcao_treino + proporcao_val))

    return (
        X[:fim_treino], y[:fim_treino],
        X[fim_treino:fim_val], y[fim_treino:fim_val],
        X[fim_val:], y[fim_val:],
    )
