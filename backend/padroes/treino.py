"""
treino.py — Loop de treino da PatternCNN.

Funcionalidades:
- Split temporal 70/15/15 (sem shuffle)
- Weighted CrossEntropyLoss para classes desbalanceadas
- Early stopping por val_loss
- Métricas: precision, recall, F1 (via scikit-learn)
- Persistência: model.pt + config.json + metrics.json + metadata.json
- Registro na tabela ml_models do DuckDB
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
from torch.utils.data import DataLoader, TensorDataset

from backend.banco.conexao import get_conn
from backend.indicadores.calculos import enriquecer_dataframe
from backend.padroes.modelo import criar_modelo
from backend.padroes.pipeline import N_FEATURES, SEQ_LEN_PADRAO, construir_dataset, split_temporal
from backend.padroes.rotulos import buscar_rotulos

MODELS_DIR = Path("models")


def _pesos_classes(y: np.ndarray) -> torch.Tensor:
    """Calcula pesos inversamente proporcionais à frequência de cada classe."""
    contagens = np.bincount(y, minlength=2).astype(float)
    contagens[contagens == 0] = 1.0  # evita divisão por zero
    pesos = 1.0 / contagens
    pesos = pesos / pesos.sum()  # normaliza para soma = 1
    return torch.tensor(pesos, dtype=torch.float32)


def _avaliar(modelo: nn.Module, loader: DataLoader, criterio: nn.Module) -> tuple[float, dict]:
    """Roda o modelo em modo eval e retorna loss + métricas."""
    modelo.eval()
    total_loss = 0.0
    todos_preds = []
    todos_labels = []

    with torch.no_grad():
        for X_batch, y_batch in loader:
            logits = modelo(X_batch)
            loss = criterio(logits, y_batch)
            total_loss += loss.item() * len(y_batch)
            preds = logits.argmax(dim=1).cpu().numpy()
            todos_preds.extend(preds)
            todos_labels.extend(y_batch.cpu().numpy())

    media_loss = total_loss / len(loader.dataset)
    todos_preds = np.array(todos_preds)
    todos_labels = np.array(todos_labels)

    metricas = {
        "precision": float(precision_score(todos_labels, todos_preds, zero_division=0)),
        "recall": float(recall_score(todos_labels, todos_preds, zero_division=0)),
        "f1": float(f1_score(todos_labels, todos_preds, zero_division=0)),
        "loss": float(media_loss),
    }
    return media_loss, metricas


def treinar(
    ticker: str,
    timeframe: str,
    nome: str,
    periodo_inicio: str | None = None,
    periodo_fim: str | None = None,
    seq_len: int = SEQ_LEN_PADRAO,
    learning_rate: float = 1e-3,
    batch_size: int = 32,
    epochs: int = 50,
    patience: int = 10,
    weight_decay: float = 1e-4,
) -> dict:
    """
    Executa o pipeline completo de treino e retorna resultados + model_id.

    Parâmetros
    ----------
    ticker, timeframe : identificam o ativo e resolução
    nome              : nome legível para o modelo
    periodo_inicio/fim: filtro de período nos rótulos (opcional)
    seq_len           : tamanho da janela temporal
    learning_rate, batch_size, epochs, patience, weight_decay : hiperparâmetros

    Retorno
    -------
    dict com model_id, métricas de treino/val/teste, avisos de qualidade
    """
    # --- 1. Carregar rótulos ---
    rotulos = buscar_rotulos(ticker, timeframe, periodo_inicio, periodo_fim)
    if not rotulos:
        raise ValueError(f"Nenhum rótulo encontrado para {ticker}/{timeframe}")

    n_positivos = sum(v for v in rotulos.values())
    n_negativos = len(rotulos) - n_positivos
    avisos = []
    if n_positivos < 200:
        avisos.append(
            f"Dataset pequeno: apenas {n_positivos} exemplos positivos (recomendado ≥ 200). "
            "O modelo pode não generalizar bem."
        )

    # --- 2. Carregar candles e enriquecer ---
    with get_conn() as conn:
        datas_cond = ""
        params: list = [ticker, timeframe]
        if periodo_inicio:
            datas_cond += " AND datetime >= ?"
            params.append(pd.Timestamp(periodo_inicio))
        if periodo_fim:
            datas_cond += " AND datetime <= ?"
            params.append(pd.Timestamp(periodo_fim))
        df_raw = conn.execute(
            f"SELECT * FROM candles WHERE ticker=? AND timeframe=? {datas_cond} ORDER BY datetime",
            params,
        ).fetchdf()

    if df_raw.empty:
        raise ValueError(f"Sem candles para {ticker}/{timeframe} no período informado")

    df = enriquecer_dataframe(df_raw)

    # --- 3. Construir dataset ---
    X, y = construir_dataset(df, rotulos, seq_len)

    # --- 4. Split temporal ---
    X_tr, y_tr, X_val, y_val, X_te, y_te = split_temporal(X, y)

    if len(X_val) == 0 or len(X_te) == 0:
        raise ValueError("Dataset pequeno demais para split 70/15/15. Adicione mais rótulos.")

    # --- 5. Datasets e DataLoaders ---
    def para_tensor(X_arr, y_arr):
        return TensorDataset(
            torch.tensor(X_arr, dtype=torch.float32),
            torch.tensor(y_arr, dtype=torch.long),
        )

    loader_tr  = DataLoader(para_tensor(X_tr, y_tr),   batch_size=batch_size, shuffle=False)
    loader_val = DataLoader(para_tensor(X_val, y_val), batch_size=batch_size, shuffle=False)
    loader_te  = DataLoader(para_tensor(X_te, y_te),   batch_size=batch_size, shuffle=False)

    # --- 6. Modelo + otimizador + loss ---
    modelo = criar_modelo(n_features=N_FEATURES, seq_len=seq_len)
    otimizador = torch.optim.Adam(modelo.parameters(), lr=learning_rate, weight_decay=weight_decay)
    pesos = _pesos_classes(y_tr)
    criterio = nn.CrossEntropyLoss(weight=pesos)

    # --- 7. Loop de treino com early stopping ---
    melhor_val_loss = float("inf")
    epocas_sem_melhora = 0
    melhor_estado = None
    historico_loss: list[dict] = []

    for epoca in range(1, epochs + 1):
        modelo.train()
        loss_treino_total = 0.0

        for X_batch, y_batch in loader_tr:
            otimizador.zero_grad()
            logits = modelo(X_batch)
            loss = criterio(logits, y_batch)
            loss.backward()
            otimizador.step()
            loss_treino_total += loss.item() * len(y_batch)

        loss_treino = loss_treino_total / len(loader_tr.dataset)
        val_loss, _ = _avaliar(modelo, loader_val, criterio)

        historico_loss.append({"epoca": epoca, "treino": round(loss_treino, 6), "val": round(val_loss, 6)})

        if val_loss < melhor_val_loss:
            melhor_val_loss = val_loss
            epocas_sem_melhora = 0
            melhor_estado = {k: v.clone() for k, v in modelo.state_dict().items()}
        else:
            epocas_sem_melhora += 1
            if epocas_sem_melhora >= patience:
                break

    # Restaura melhor modelo
    if melhor_estado:
        modelo.load_state_dict(melhor_estado)

    # --- 8. Métricas finais ---
    _, metricas_tr  = _avaliar(modelo, loader_tr,  criterio)
    _, metricas_val = _avaliar(modelo, loader_val, criterio)
    _, metricas_te  = _avaliar(modelo, loader_te,  criterio)

    # Alerta de overfitting
    if (metricas_tr["f1"] - metricas_val["f1"]) > 0.10:
        avisos.append(
            f"Possível overfitting: F1_treino={metricas_tr['f1']:.2f} vs F1_val={metricas_val['f1']:.2f}. "
            "Reduza epochs ou aumente o dataset."
        )

    # --- 9. Persistir artefatos ---
    model_id = str(uuid.uuid4())
    pasta = MODELS_DIR / model_id
    pasta.mkdir(parents=True, exist_ok=True)

    torch.save(modelo.state_dict(), pasta / "model.pt")

    config = {
        "seq_len": seq_len,
        "n_features": N_FEATURES,
        "learning_rate": learning_rate,
        "batch_size": batch_size,
        "epochs_executadas": len(historico_loss),
        "patience": patience,
        "weight_decay": weight_decay,
    }
    (pasta / "config.json").write_text(json.dumps(config, indent=2))

    metrics = {
        "treino": metricas_tr,
        "val": metricas_val,
        "teste": metricas_te,
        "historico_loss": historico_loss,
        "n_positivos": n_positivos,
        "n_negativos": n_negativos,
    }
    (pasta / "metrics.json").write_text(json.dumps(metrics, indent=2))

    # Datas do dataset: usamos rótulos disponíveis
    dts_rotulos = sorted(rotulos.keys())
    n_total = len(dts_rotulos)
    fim_treino_idx  = int(n_total * 0.70)
    fim_val_idx     = int(n_total * 0.85)

    metadata = {
        "model_id": model_id,
        "nome": nome,
        "ticker": ticker,
        "timeframe": timeframe,
        "features": list(config.keys()),
    }
    (pasta / "metadata.json").write_text(json.dumps(metadata, indent=2))

    # --- 10. Registro no DuckDB ---
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO ml_models
                (id, nome, ticker, timeframe, n_features, seq_len,
                 train_periodo_inicio, train_periodo_fim,
                 test_periodo_inicio, test_periodo_fim,
                 metrics_json, config_json, model_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                model_id, nome, ticker, timeframe, N_FEATURES, seq_len,
                dts_rotulos[0] if dts_rotulos else None,
                dts_rotulos[fim_treino_idx - 1] if fim_treino_idx > 0 else None,
                dts_rotulos[fim_val_idx] if fim_val_idx < n_total else None,
                dts_rotulos[-1] if dts_rotulos else None,
                json.dumps(metrics),
                json.dumps(config),
                str(pasta),
            ],
        )
        conn.commit()

    return {
        "model_id": model_id,
        "nome": nome,
        "ticker": ticker,
        "timeframe": timeframe,
        "n_amostras": len(X),
        "n_positivos": n_positivos,
        "n_negativos": n_negativos,
        "epochs_executadas": len(historico_loss),
        "metricas_treino": metricas_tr,
        "metricas_val": metricas_val,
        "metricas_teste": metricas_te,
        "historico_loss": historico_loss,
        "avisos": avisos,
    }
