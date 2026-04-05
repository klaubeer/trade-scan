import json
from datetime import date
from dateutil.relativedelta import relativedelta

from backend.backtesting.motor import executar_backtest, ErroValidacao
from backend.backtesting.estatisticas import calcular_estatisticas
from backend.banco.conexao import get_conn
from backend.schemas.modelos import SetupParams


def gerar_janelas(
    periodo_inicio: date,
    periodo_fim: date,
    janela_otim_meses: int,
    janela_valid_meses: int,
    step_meses: int,
) -> list[dict]:
    janelas = []
    cursor = periodo_inicio
    num = 1

    while True:
        otim_inicio = cursor
        otim_fim = cursor + relativedelta(months=janela_otim_meses) - relativedelta(days=1)
        valid_inicio = otim_fim + relativedelta(days=1)
        valid_fim = valid_inicio + relativedelta(months=janela_valid_meses) - relativedelta(days=1)

        if valid_fim > periodo_fim:
            break

        janelas.append({
            "janela_num": num,
            "otim_inicio": otim_inicio,
            "otim_fim": otim_fim,
            "valid_inicio": valid_inicio,
            "valid_fim": valid_fim,
        })

        cursor += relativedelta(months=step_meses)
        num += 1

    return janelas


def executar_walk_forward(
    setup: SetupParams,
    setup_id: int,
    periodo_inicio: date,
    periodo_fim: date,
    janela_otim_meses: int = 6,
    janela_valid_meses: int = 1,
    step_meses: int = 1,
) -> dict:
    janelas_config = gerar_janelas(
        periodo_inicio, periodo_fim,
        janela_otim_meses, janela_valid_meses, step_meses,
    )

    if not janelas_config:
        raise ErroValidacao(
            "Período insuficiente para gerar janelas com os parâmetros fornecidos."
        )

    # Criar registro do walk-forward run
    with get_conn() as conn:
        wf_run_id = conn.execute("""
            INSERT INTO walk_forward_runs
                (setup_id, periodo_inicio, periodo_fim, janela_otim_meses, janela_valid_meses, step_meses)
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING id
        """, [setup_id, periodo_inicio, periodo_fim, janela_otim_meses, janela_valid_meses, step_meses]).fetchone()[0]

    janelas_resultado = []
    expectancias_in = []
    expectancias_out = []

    for jc in janelas_config:
        # Executar in-sample
        try:
            res_otim = executar_backtest(setup, setup_id, jc["otim_inicio"], jc["otim_fim"], "in_sample")
            run_id_otim = res_otim["run_id"]
            exp_in = res_otim["stats"].get("expectancia_pts", 0)
            trades_in = res_otim["total_trades"]
        except Exception:
            run_id_otim = None
            exp_in = 0
            trades_in = 0

        # Aprovar automaticamente o in-sample para permitir o out-of-sample
        if run_id_otim:
            with get_conn() as conn:
                conn.execute(
                    "UPDATE backtest_runs SET aprovado = TRUE WHERE id = ?", [run_id_otim]
                )

        # Executar out-of-sample
        try:
            res_valid = executar_backtest(setup, setup_id, jc["valid_inicio"], jc["valid_fim"], "out_of_sample")
            run_id_valid = res_valid["run_id"]
            exp_out = res_valid["stats"].get("expectancia_pts", 0)
            trades_out = res_valid["total_trades"]
        except Exception:
            run_id_valid = None
            exp_out = 0
            trades_out = 0

        # Persistir janela
        with get_conn() as conn:
            conn.execute("""
                INSERT INTO walk_forward_janelas
                    (wf_run_id, janela_num, otim_inicio, otim_fim, valid_inicio, valid_fim, run_id_otim, run_id_valid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                wf_run_id, jc["janela_num"],
                jc["otim_inicio"], jc["otim_fim"],
                jc["valid_inicio"], jc["valid_fim"],
                run_id_otim, run_id_valid,
            ])

        expectancias_in.append(exp_in)
        expectancias_out.append(exp_out)

        janelas_resultado.append({
            "janela_num": jc["janela_num"],
            "otim_inicio": str(jc["otim_inicio"]),
            "otim_fim": str(jc["otim_fim"]),
            "valid_inicio": str(jc["valid_inicio"]),
            "valid_fim": str(jc["valid_fim"]),
            "run_id_otim": run_id_otim,
            "run_id_valid": run_id_valid,
            "expectancia_in": round(exp_in, 1),
            "expectancia_out": round(exp_out, 1),
            "total_trades_in": trades_in,
            "total_trades_out": trades_out,
        })

    # Métricas consolidadas
    media_in = sum(expectancias_in) / len(expectancias_in) if expectancias_in else 0
    media_out = sum(expectancias_out) / len(expectancias_out) if expectancias_out else 0
    eficiencia = round(media_out / media_in, 3) if media_in != 0 else None
    janelas_positivas = sum(1 for e in expectancias_out if e > 0)
    consistencia = round(janelas_positivas / len(expectancias_out), 3) if expectancias_out else 0

    # Atualizar registro com métricas
    with get_conn() as conn:
        conn.execute("""
            UPDATE walk_forward_runs SET eficiencia = ?, consistencia = ? WHERE id = ?
        """, [eficiencia, consistencia, wf_run_id])

    return {
        "wf_run_id": wf_run_id,
        "total_janelas": len(janelas_resultado),
        "janelas_positivas": janelas_positivas,
        "eficiencia": eficiencia,
        "consistencia": consistencia,
        "janelas": janelas_resultado,
    }
