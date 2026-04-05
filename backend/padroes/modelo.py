"""
modelo.py — Arquitetura PatternCNN.

CNN 1D para classificação binária de padrões em price action.
Input:  (batch, n_features, seq_len)
Output: logits (batch, 2)  →  classe 0 = não operar, classe 1 = operar
"""

from __future__ import annotations

import torch
import torch.nn as nn

from backend.padroes.pipeline import N_FEATURES, SEQ_LEN_PADRAO


class PatternCNN(nn.Module):
    """
    CNN 1D com 3 blocos convolucionais + pooling adaptativo + classificador MLP.

    Parâmetros
    ----------
    n_features : número de features por candle (padrão 10)
    seq_len    : tamanho da janela temporal (padrão 50) — usado apenas para
                 validação de shape; o AdaptiveAvgPool1d torna o modelo agnóstico
                 ao seq_len em tempo de inferência.
    n_classes  : 2 (classificação binária via CrossEntropyLoss)
    """

    def __init__(
        self,
        n_features: int = N_FEATURES,
        seq_len: int = SEQ_LEN_PADRAO,
        n_classes: int = 2,
    ):
        super().__init__()
        self.n_features = n_features
        self.seq_len = seq_len
        self.n_classes = n_classes

        self.features = nn.Sequential(
            nn.Conv1d(n_features, 32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
        )
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, n_features, seq_len)
        x = self.features(x)           # (batch, 128, seq_len)
        x = self.pool(x).squeeze(-1)   # (batch, 128)
        return self.classifier(x)      # (batch, n_classes)


def criar_modelo(n_features: int = N_FEATURES, seq_len: int = SEQ_LEN_PADRAO) -> PatternCNN:
    """Fábrica — retorna modelo numa CPU (device padrão do TradeScan)."""
    return PatternCNN(n_features=n_features, seq_len=seq_len)
