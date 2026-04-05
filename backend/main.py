import json
import os
from datetime import date
from typing import AsyncGenerator

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.banco.schema import inicializar_banco
from backend.banco.conexao import get_conn
from backend.ingestao.parser_csv import parse_csv, ErroIngestao
from backend.ingestao.deduplicacao import upsert_candles, periodo_disponivel
from backend.ingestao.agregacao import agregar_timeframes
from backend.backtesting.motor import executar_backtest, ErroValidacao
from backend.schemas.modelos import SetupParams, BacktestRequest, WalkForwardRequest, MonteCarloRequest

app = FastAPI(title="TradeScan API", version="0.1.0")

_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    inicializar_banco()


# ---------------------------------------------------------------------------
# Utilitário de erro
# ---------------------------------------------------------------------------

def erro(mensagem: str, status: int = 400):
    raise HTTPException(status_code=status, detail={"erro": mensagem})


# ---------------------------------------------------------------------------
# Ingestão
# ---------------------------------------------------------------------------

@app.post("/api/ingestao/upload")
async def upload_csv(arquivo: UploadFile = File(...)):
    if not arquivo.filename.endswith(".csv"):
        erro("Arquivo deve ser um CSV.")
    conteudo = await arquivo.read()
    try:
        df = parse_csv(conteudo)
    except ErroIngestao as e:
        erro(str(e))

    ticker = df["ticker"].iloc[0]
    timeframe = df["timeframe"].iloc[0]

    info = upsert_candles(df)
    agregar_timeframes(ticker, timeframe)
    periodo = periodo_disponivel(ticker, timeframe)

    return {
        "ticker": ticker,
        "timeframe": timeframe,
        "candles_no_arquivo": len(df),
        "candles_inseridos": info["inseridos"],
        "candles_duplicados": info["duplicados"],
        "periodo": periodo,
    }


@app.get("/api/ingestao/disponivel")
def dados_disponiveis():
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT ticker, timeframe, MIN(datetime::DATE) as inicio, MAX(datetime::DATE) as fim, COUNT(*) as total
            FROM candles
            GROUP BY ticker, timeframe
            ORDER BY ticker, timeframe
        """).fetchall()
    return [
        {"ticker": r[0], "timeframe": r[1], "inicio": str(r[2]), "fim": str(r[3]), "total_candles": r[4]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Setups
# ---------------------------------------------------------------------------

@app.get("/api/setups")
def listar_setups():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, nome, ticker, params_json, criado_em FROM setups ORDER BY criado_em DESC"
        ).fetchall()
    return [
        {"id": r[0], "nome": r[1], "ticker": r[2], "params": json.loads(r[3]), "criado_em": str(r[4])}
        for r in rows
    ]


@app.post("/api/setups", status_code=201)
def criar_setup(params: SetupParams):
    with get_conn() as conn:
        setup_id = conn.execute("""
            INSERT INTO setups (nome, ticker, params_json)
            VALUES (?, ?, ?)
            RETURNING id
        """, [params.nome, params.ticker, params.model_dump_json()]).fetchone()[0]
    return {"id": setup_id, "nome": params.nome}


@app.get("/api/setups/{setup_id}")
def detalhe_setup(setup_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, nome, ticker, params_json, criado_em FROM setups WHERE id = ?",
            [setup_id]
        ).fetchone()
    if not row:
        erro("Setup não encontrado.", 404)
    return {"id": row[0], "nome": row[1], "ticker": row[2], "params": json.loads(row[3]), "criado_em": str(row[4])}


@app.put("/api/setups/{setup_id}")
def atualizar_setup(setup_id: int, params: SetupParams):
    with get_conn() as conn:
        affected = conn.execute(
            "UPDATE setups SET nome=?, ticker=?, params_json=? WHERE id=?",
            [params.nome, params.ticker, params.model_dump_json(), setup_id]
        ).rowcount
    if affected == 0:
        erro("Setup não encontrado.", 404)
    return {"id": setup_id, "nome": params.nome}


@app.delete("/api/setups/{setup_id}", status_code=204)
def deletar_setup(setup_id: int):
    with get_conn() as conn:
        conn.execute("DELETE FROM setups WHERE id = ?", [setup_id])


@app.put("/api/setups/{setup_id}/aprovar")
def aprovar_run_insample(setup_id: int, run_id: int):
    with get_conn() as conn:
        conn.execute("""
            UPDATE backtest_runs SET aprovado = TRUE
            WHERE id = ? AND setup_id = ? AND sample_type = 'in_sample'
        """, [run_id, setup_id])
    return {"aprovado": True}


# ---------------------------------------------------------------------------
# Backtesting
# ---------------------------------------------------------------------------

@app.post("/api/backtesting/executar")
def executar(req: BacktestRequest):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT params_json FROM setups WHERE id = ?", [req.setup_id]
        ).fetchone()
    if not row:
        erro("Setup não encontrado.", 404)

    params = SetupParams.model_validate_json(row[0])
    params.slippage_pts = req.slippage_pts
    params.custo_por_ponto = req.custo_por_ponto

    try:
        resultado = executar_backtest(
            setup=params,
            setup_id=req.setup_id,
            periodo_inicio=req.periodo_inicio,
            periodo_fim=req.periodo_fim,
            sample_type=req.sample_type,
            cnn_modelo_id=req.cnn_modelo_id,
            cnn_threshold=req.cnn_threshold,
        )
    except ErroValidacao as e:
        erro(str(e), 422)

    return resultado


@app.get("/api/backtesting/runs")
def listar_runs(setup_id: int | None = None, sample_type: str | None = None):
    with get_conn() as conn:
        where = "WHERE 1=1"
        params = []
        if setup_id is not None:
            where += " AND br.setup_id = ?"
            params.append(setup_id)
        if sample_type is not None:
            where += " AND br.sample_type = ?"
            params.append(sample_type)

        rows = conn.execute(f"""
            SELECT br.id, br.setup_id, s.nome, br.periodo_inicio, br.periodo_fim,
                   br.sample_type, br.aprovado, br.criado_em, bs.stats_json
            FROM backtest_runs br
            JOIN setups s ON s.id = br.setup_id
            LEFT JOIN backtest_stats bs ON bs.run_id = br.id
            {where}
            ORDER BY br.criado_em DESC
        """, params).fetchall()

    resultado = []
    for r in rows:
        stats = json.loads(r[8]) if r[8] else {}
        resultado.append({
            "run_id": r[0],
            "setup_id": r[1],
            "setup_nome": r[2],
            "periodo_inicio": str(r[3]),
            "periodo_fim": str(r[4]),
            "sample_type": r[5],
            "aprovado": r[6],
            "criado_em": str(r[7]),
            "total_trades": stats.get("total_trades"),
            "win_rate": stats.get("win_rate"),
            "expectancia_pts": stats.get("expectancia_pts"),
            "total_pts": stats.get("total_pts"),
            "fator_lucro": stats.get("fator_lucro"),
            "max_drawdown_pts": stats.get("max_drawdown_pts"),
        })
    return resultado


@app.delete("/api/backtesting/runs/{run_id}")
def deletar_run(run_id: int):
    with get_conn() as conn:
        run = conn.execute(
            "SELECT aprovado FROM backtest_runs WHERE id = ?", [run_id]
        ).fetchone()
        if not run:
            erro("Run não encontrado.", 404)
        if run[0]:
            erro("Não é possível apagar um run aprovado.", 400)
        conn.execute("DELETE FROM backtest_trades WHERE run_id = ?", [run_id])
        conn.execute("DELETE FROM backtest_stats WHERE run_id = ?", [run_id])
        conn.execute("DELETE FROM backtest_runs WHERE id = ?", [run_id])
    return {"ok": True}


@app.get("/api/backtesting/runs/{run_id}")
def obter_run(run_id: int):
    with get_conn() as conn:
        run = conn.execute(
            "SELECT id, setup_id, periodo_inicio, periodo_fim, sample_type, aprovado FROM backtest_runs WHERE id = ?",
            [run_id]
        ).fetchone()
        if not run:
            erro("Run não encontrado.", 404)

        stats_row = conn.execute(
            "SELECT stats_json FROM backtest_stats WHERE run_id = ?", [run_id]
        ).fetchone()

        trades = conn.execute("""
            SELECT datetime, direcao, preco_entrada, preco_saida, resultado, resultado_pts, contexto_json
            FROM backtest_trades WHERE run_id = ? ORDER BY datetime
        """, [run_id]).fetchall()

    return {
        "run": {
            "id": run[0], "setup_id": run[1],
            "periodo_inicio": str(run[2]), "periodo_fim": str(run[3]),
            "sample_type": run[4], "aprovado": run[5],
        },
        "stats": json.loads(stats_row[0]) if stats_row else None,
        "trades": [
            {
                "datetime": str(t[0]), "direcao": t[1],
                "preco_entrada": t[2], "preco_saida": t[3],
                "resultado": t[4], "resultado_pts": t[5],
                "contexto": json.loads(t[6]) if t[6] else {},
            }
            for t in trades
        ],
    }


@app.get("/api/backtesting/comparativo")
def comparativo(setup_ids: str, periodo_inicio: date, periodo_fim: date, sample_type: str = "in_sample"):
    ids = [int(x) for x in setup_ids.split(",")]
    resultado = []

    with get_conn() as conn:
        for sid in ids:
            run = conn.execute("""
                SELECT br.id, s.nome, bs.stats_json
                FROM backtest_runs br
                JOIN setups s ON s.id = br.setup_id
                JOIN backtest_stats bs ON bs.run_id = br.id
                WHERE br.setup_id = ?
                  AND br.periodo_inicio = ?
                  AND br.periodo_fim = ?
                  AND br.sample_type = ?
                ORDER BY br.criado_em DESC
                LIMIT 1
            """, [sid, periodo_inicio, periodo_fim, sample_type]).fetchone()

            if run:
                stats = json.loads(run[2])
                resultado.append({
                    "setup_id": sid,
                    "nome": run[1],
                    "run_id": run[0],
                    "total_trades": stats.get("total_trades"),
                    "win_rate": stats.get("win_rate"),
                    "expectancia_pts": stats.get("expectancia_pts"),
                    "total_pts": stats.get("total_pts"),
                    "fator_lucro": stats.get("fator_lucro"),
                    "max_drawdown_pts": stats.get("max_drawdown_pts"),
                })

    return resultado


# ---------------------------------------------------------------------------
# Walk-Forward
# ---------------------------------------------------------------------------

@app.post("/api/walk-forward/executar")
def executar_walk_forward(req: WalkForwardRequest):
    from backend.backtesting.walk_forward import executar_walk_forward as _wf
    with get_conn() as conn:
        row = conn.execute("SELECT params_json FROM setups WHERE id = ?", [req.setup_id]).fetchone()
    if not row:
        erro("Setup não encontrado.", 404)

    params = SetupParams.model_validate_json(row[0])
    params.slippage_pts = req.slippage_pts
    params.custo_por_ponto = req.custo_por_ponto

    try:
        resultado = _wf(params, req.setup_id, req.periodo_inicio, req.periodo_fim,
                        req.janela_otim_meses, req.janela_valid_meses, req.step_meses)
    except ErroValidacao as e:
        erro(str(e), 422)
    return resultado


@app.get("/api/walk-forward/{wf_run_id}")
def obter_walk_forward(wf_run_id: int):
    with get_conn() as conn:
        wf = conn.execute(
            "SELECT * FROM walk_forward_runs WHERE id = ?", [wf_run_id]
        ).fetchone()
        if not wf:
            erro("Walk-forward run não encontrado.", 404)
        janelas = conn.execute(
            "SELECT * FROM walk_forward_janelas WHERE wf_run_id = ? ORDER BY janela_num",
            [wf_run_id]
        ).fetchall()
    return {"wf_run": wf, "janelas": janelas}


# ---------------------------------------------------------------------------
# Monte Carlo
# ---------------------------------------------------------------------------

@app.post("/api/monte-carlo/executar")
def executar_monte_carlo(req: MonteCarloRequest):
    from backend.backtesting.monte_carlo import simular_monte_carlo, persistir_monte_carlo

    with get_conn() as conn:
        trades = conn.execute(
            "SELECT resultado_pts FROM backtest_trades WHERE run_id = ? ORDER BY datetime",
            [req.run_id]
        ).fetchall()

    if not trades:
        erro("Run não encontrado ou sem trades.", 404)

    resultado_pts = [t[0] for t in trades]
    resultado = simular_monte_carlo(resultado_pts, req.n_simulacoes)
    mc_run_id = persistir_monte_carlo(req.run_id, req.n_simulacoes, resultado)

    return {"mc_run_id": mc_run_id, **resultado}


@app.get("/api/monte-carlo/{mc_run_id}")
def obter_monte_carlo(mc_run_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT run_id, n_simulacoes, resultado_json FROM monte_carlo_runs WHERE id = ?",
            [mc_run_id]
        ).fetchone()
    if not row:
        erro("Monte Carlo run não encontrado.", 404)
    return {"mc_run_id": mc_run_id, "run_id": row[0], "n_simulacoes": row[1], **json.loads(row[2])}


# ---------------------------------------------------------------------------
# Agente IA
# ---------------------------------------------------------------------------

class ExplorarRequest(BaseModel):
    descricao_natural: str

class InterpretarRequest(BaseModel):
    run_id: int


@app.post("/api/agente/explorar")
async def agente_explorar(req: ExplorarRequest):
    from backend.agente.grafo import explorar

    async def gerar():
        async for evento in explorar(req.descricao_natural):
            yield f"data: {json.dumps(evento, ensure_ascii=False)}\n\n"

    return StreamingResponse(gerar(), media_type="text/event-stream")


@app.post("/api/agente/interpretar")
def agente_interpretar(req: InterpretarRequest):
    from backend.agente.grafo import interpretar_run
    try:
        return interpretar_run(req.run_id)
    except ValueError as e:
        erro(str(e), 404)


# ---------------------------------------------------------------------------
# CNN — Reconhecimento de Padrões
# ---------------------------------------------------------------------------

class RotularRequest(BaseModel):
    ticker: str
    timeframe: str
    datetime: str
    label: int  # 0 ou 1


class TreinarCNNRequest(BaseModel):
    ticker: str
    timeframe: str
    nome: str
    run_id: int | None = None
    periodo_inicio: str | None = None
    periodo_fim: str | None = None
    seq_len: int = 50
    learning_rate: float = 1e-3
    batch_size: int = 32
    epochs: int = 50
    patience: int = 10


class PreverRequest(BaseModel):
    model_id: str
    ticker: str
    timeframe: str
    datetime_fim: str


@app.post("/api/cnn/rotular/run/{run_id}")
def rotular_por_backtest(run_id: int):
    """Gera rótulos automáticos a partir dos trades de um backtest_run."""
    from backend.padroes.rotulos import rotular_por_run
    try:
        return rotular_por_run(run_id)
    except ValueError as e:
        erro(str(e), 404)


@app.post("/api/cnn/rotular")
def rotular_manual(req: RotularRequest):
    """Insere ou atualiza um rótulo manual para um candle específico."""
    from backend.padroes.rotulos import rotular_manual as _rotular
    if req.label not in (0, 1):
        erro("label deve ser 0 ou 1")
    return _rotular(req.ticker, req.timeframe, req.datetime, req.label)


@app.get("/api/cnn/rotulos/resumo")
def resumo_rotulos(ticker: str, timeframe: str):
    """Retorna contagem de rótulos positivos/negativos disponíveis para treino."""
    from backend.padroes.rotulos import resumo_rotulos as _resumo
    return _resumo(ticker, timeframe)


@app.post("/api/cnn/treinar")
def treinar_cnn(req: TreinarCNNRequest):
    """
    Executa o pipeline completo de treino.
    Se run_id informado, gera rótulos automáticos antes de treinar.
    """
    from backend.padroes.rotulos import rotular_por_run
    from backend.padroes.treino import treinar

    if req.run_id is not None:
        try:
            rotular_por_run(req.run_id)
        except ValueError as e:
            erro(str(e), 404)

    try:
        resultado = treinar(
            ticker=req.ticker,
            timeframe=req.timeframe,
            nome=req.nome,
            periodo_inicio=req.periodo_inicio,
            periodo_fim=req.periodo_fim,
            seq_len=req.seq_len,
            learning_rate=req.learning_rate,
            batch_size=req.batch_size,
            epochs=req.epochs,
            patience=req.patience,
        )
    except ValueError as e:
        erro(str(e), 422)

    return resultado


@app.get("/api/cnn/modelos")
def listar_modelos_cnn():
    """Lista todos os modelos CNN treinados."""
    from backend.padroes.inferencia import listar_modelos
    return listar_modelos()


@app.post("/api/cnn/prever")
def prever_cnn(req: PreverRequest):
    """Retorna probabilidade de entrada válida (0–1) para uma janela de candles."""
    from backend.padroes.inferencia import prever
    try:
        prob = prever(req.model_id, req.ticker, req.timeframe, req.datetime_fim)
    except ValueError as e:
        erro(str(e), 404)
    return {"model_id": req.model_id, "probabilidade": prob, "predicao": int(prob >= 0.5)}
