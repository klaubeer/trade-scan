import json
from typing import TypedDict, Optional, AsyncGenerator
from datetime import date, timedelta

from backend.agente.nos import parse_intent, formulate_setup, interpret_results, suggest_refinements
from backend.backtesting.motor import executar_backtest, ErroValidacao
from backend.banco.conexao import get_conn
from backend.schemas.modelos import SetupParams


class AgenteState(TypedDict):
    descricao: str
    setup_id: int
    setup: Optional[dict]
    run_id: Optional[int]
    stats: Optional[dict]
    interpretacao: Optional[str]
    sugestoes: list
    erro: Optional[str]


async def explorar(descricao: str, setup_id_existente: int | None = None) -> AsyncGenerator[dict, None]:
    """
    Grafo principal do agente no modo exploração.
    Retorna eventos SSE como dicionários.
    """
    yield {"no": "parse_intent", "status": "executando"}

    try:
        intencao = parse_intent(descricao)
    except Exception as e:
        yield {"no": "parse_intent", "status": "erro", "mensagem": str(e)}
        return

    yield {"no": "parse_intent", "status": "concluido", "resumo": intencao.get("resumo", "")}

    # Formular setup
    yield {"no": "formulate_setup", "status": "executando"}
    setup = formulate_setup(intencao, nome=f"IA: {descricao[:40]}")

    if setup is None:
        yield {
            "no": "pedir_esclarecimento",
            "status": "concluido",
            "resumo": "Não consegui formular um setup válido com as informações fornecidas. Poderia detalhar o timeframe, stop e alvo em pontos?",
        }
        return

    yield {"no": "formulate_setup", "status": "concluido", "setup": setup.model_dump(mode="json")}

    # Persistir setup temporário
    with get_conn() as conn:
        sid = conn.execute("""
            INSERT INTO setups (nome, ticker, params_json) VALUES (?, ?, ?) RETURNING id
        """, [setup.nome, setup.ticker, setup.model_dump_json()]).fetchone()[0]

    # Executar backtest (últimos 6 meses por padrão)
    yield {"no": "run_backtest", "status": "executando"}
    fim = date.today()
    inicio = fim - timedelta(days=180)

    try:
        resultado = executar_backtest(setup, sid, inicio, fim, "in_sample")
    except ErroValidacao as e:
        yield {"no": "run_backtest", "status": "erro", "mensagem": str(e)}
        return
    except Exception as e:
        yield {"no": "run_backtest", "status": "erro", "mensagem": f"Erro no backtest: {e}"}
        return

    yield {
        "no": "run_backtest",
        "status": "concluido",
        "run_id": resultado["run_id"],
        "total_trades": resultado["total_trades"],
    }

    if resultado["total_trades"] == 0:
        yield {"no": "interpret_results", "status": "concluido",
               "interpretacao": "Nenhuma operação foi gerada com os parâmetros fornecidos no período testado. Tente relaxar as condições de entrada ou ampliar o período."}
        return

    # Interpretar
    yield {"no": "interpret_results", "status": "executando"}
    try:
        interp = interpret_results(resultado["stats"], resultado["total_trades"])
    except Exception as e:
        interp = f"Erro na interpretação: {e}"

    yield {"no": "interpret_results", "status": "concluido", "interpretacao": interp}

    # Sugestões
    yield {"no": "suggest_refinements", "status": "executando"}
    try:
        sugestoes = suggest_refinements(resultado["stats"], setup)
    except Exception:
        sugestoes = []

    yield {"no": "suggest_refinements", "status": "concluido", "sugestoes": sugestoes}

    yield {
        "event": "result",
        "run_id": resultado["run_id"],
        "setup_id": sid,
        "interpretacao": interp,
        "sugestoes": sugestoes,
    }


def interpretar_run(run_id: int) -> dict:
    """Modo interpretação: analisa um run já existente."""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT bs.stats_json, br.setup_id
            FROM backtest_stats bs
            JOIN backtest_runs br ON br.id = bs.run_id
            WHERE bs.run_id = ?
        """, [run_id]).fetchone()

        if not row:
            raise ValueError("Run não encontrado.")

        stats = json.loads(row[0])
        setup_row = conn.execute("SELECT params_json FROM setups WHERE id = ?", [row[1]]).fetchone()
        setup = SetupParams.model_validate_json(setup_row[0])

    interp = interpret_results(stats, stats.get("total_trades", 0))
    sugestoes = suggest_refinements(stats, setup)

    return {"interpretacao": interp, "sugestoes": sugestoes}
