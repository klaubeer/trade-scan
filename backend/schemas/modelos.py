from datetime import time, date
from typing import Literal, Optional
from pydantic import BaseModel, Field


class SetupParams(BaseModel):
    nome: str
    ticker: Literal["WIN", "WDO", "BITFUT"]
    timeframe: Literal["1min", "5min", "15min", "60min"]
    direcao: Literal["long", "short", "ambos"]

    # --- Condições de entrada (None = não aplicar) ---
    range_candle_min: Optional[float] = None
    pavio_total_max: Optional[float] = None
    pavio_superior_max: Optional[float] = None
    pavio_inferior_max: Optional[float] = None
    mm200_posicao: Optional[Literal["acima", "abaixo"]] = None
    mme9_posicao: Optional[Literal["acima", "abaixo"]] = None
    ifr2_max: Optional[float] = None   # IFR2 < X (sobrevendido → compra)
    ifr2_min: Optional[float] = None   # IFR2 > X (sobrecomprado → venda)
    range_acumulado_max_pct: Optional[float] = None
    gap_abertura_min: Optional[float] = None
    primeiro_candle_direcao: Optional[Literal["alta", "baixa"]] = None
    tendencia_semanal: Optional[Literal["alta", "baixa", "qualquer"]] = None

    # --- Filtros ADX / ATR ---
    adx_min: Optional[float] = Field(default=None, ge=0, le=100)   # ADX >= X para entrar (ex: 25)
    atr_fator_range: Optional[float] = Field(default=None, ge=0)   # range_dia >= fator × ATR_diário (ex: 1.0)

    # --- Sequência de candles ---
    sequencia_candles: Optional[int] = Field(default=None, ge=2, le=10)
    sequencia_wick_max_pct: Optional[float] = Field(default=None, ge=0, le=100)
    sequencia_filtrar_zonas: bool = False

    # --- Execução ---
    tipo_entrada: Literal[
        "fechamento_gatilho",
        "rompimento_fechamento",
        "rompimento_maxima",
        "rompimento_minima",
    ] = "fechamento_gatilho"

    stop_pts: float = Field(gt=0)
    alvo_pts: float = Field(gt=0)
    alvo2_pts: Optional[float] = None

    # --- Alvo dinâmico ---
    alvo_proximo_pct_dia: bool = False
    alvo_minimo_pts: Optional[float] = Field(default=None, gt=0)

    horario_inicio: time = time(9, 0)
    horario_fim: time = time(17, 30)        # último horário para ABRIR nova entrada
    horario_fechamento: time = time(18, 0)  # fecha posições abertas (fim do pregão)
    max_entradas_dia: int = Field(default=1, ge=1, le=10)

    slippage_pts: float = 0.0
    custo_por_ponto: float = Field(default=0.20, ge=0)


class BacktestRequest(BaseModel):
    setup_id: int
    periodo_inicio: date
    periodo_fim: date
    sample_type: Literal["in_sample", "out_of_sample"] = "in_sample"
    slippage_pts: float = 0.0
    custo_por_ponto: float = 0.20
    cnn_modelo_id: Optional[str] = None
    cnn_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class WalkForwardRequest(BaseModel):
    setup_id: int
    periodo_inicio: date
    periodo_fim: date
    janela_otim_meses: int = Field(default=6, ge=1)
    janela_valid_meses: int = Field(default=1, ge=1)
    step_meses: int = Field(default=1, ge=1)
    slippage_pts: float = 0.0
    custo_por_ponto: float = 0.20


class MonteCarloRequest(BaseModel):
    run_id: int
    n_simulacoes: int = Field(default=1000, ge=100, le=10000)
