import duckdb
from backend.config import DB_PATH


DDL = """
CREATE SEQUENCE IF NOT EXISTS seq_setups_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_backtest_runs_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_backtest_trades_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_backtest_stats_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_wf_runs_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_wf_janelas_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_mc_runs_id START 1;
CREATE SEQUENCE IF NOT EXISTS seq_rotulos_id START 1;

CREATE TABLE IF NOT EXISTS candles (
    ticker      VARCHAR NOT NULL,
    timeframe   VARCHAR NOT NULL,
    datetime    TIMESTAMP NOT NULL,
    open        DOUBLE NOT NULL,
    high        DOUBLE NOT NULL,
    low         DOUBLE NOT NULL,
    close       DOUBLE NOT NULL,
    volume_fin  DOUBLE,
    qty         BIGINT,
    PRIMARY KEY (ticker, timeframe, datetime)
);

CREATE TABLE IF NOT EXISTS setups (
    id          INTEGER DEFAULT nextval('seq_setups_id') PRIMARY KEY,
    nome        VARCHAR NOT NULL,
    ticker      VARCHAR NOT NULL,
    params_json JSON NOT NULL,
    criado_em   TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS backtest_runs (
    id              INTEGER DEFAULT nextval('seq_backtest_runs_id') PRIMARY KEY,
    setup_id        INTEGER REFERENCES setups(id),
    periodo_inicio  DATE NOT NULL,
    periodo_fim     DATE NOT NULL,
    sample_type     VARCHAR NOT NULL,
    aprovado        BOOLEAN DEFAULT FALSE,
    criado_em       TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id              INTEGER DEFAULT nextval('seq_backtest_trades_id') PRIMARY KEY,
    run_id          INTEGER REFERENCES backtest_runs(id),
    datetime        TIMESTAMP NOT NULL,
    direcao         VARCHAR NOT NULL,
    preco_entrada   DOUBLE NOT NULL,
    preco_saida     DOUBLE NOT NULL,
    resultado       VARCHAR NOT NULL,
    resultado_pts   DOUBLE NOT NULL,
    contexto_json   JSON
);

CREATE TABLE IF NOT EXISTS backtest_stats (
    id      INTEGER DEFAULT nextval('seq_backtest_stats_id') PRIMARY KEY,
    run_id  INTEGER REFERENCES backtest_runs(id),
    stats_json JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS walk_forward_runs (
    id                  INTEGER DEFAULT nextval('seq_wf_runs_id') PRIMARY KEY,
    setup_id            INTEGER REFERENCES setups(id),
    periodo_inicio      DATE NOT NULL,
    periodo_fim         DATE NOT NULL,
    janela_otim_meses   INTEGER NOT NULL,
    janela_valid_meses  INTEGER NOT NULL,
    step_meses          INTEGER NOT NULL,
    eficiencia          DOUBLE,
    consistencia        DOUBLE,
    criado_em           TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS walk_forward_janelas (
    id              INTEGER DEFAULT nextval('seq_wf_janelas_id') PRIMARY KEY,
    wf_run_id       INTEGER REFERENCES walk_forward_runs(id),
    janela_num      INTEGER NOT NULL,
    otim_inicio     DATE NOT NULL,
    otim_fim        DATE NOT NULL,
    valid_inicio    DATE NOT NULL,
    valid_fim       DATE NOT NULL,
    run_id_otim     INTEGER REFERENCES backtest_runs(id),
    run_id_valid    INTEGER REFERENCES backtest_runs(id)
);

CREATE TABLE IF NOT EXISTS monte_carlo_runs (
    id              INTEGER DEFAULT nextval('seq_mc_runs_id') PRIMARY KEY,
    run_id          INTEGER REFERENCES backtest_runs(id),
    n_simulacoes    INTEGER NOT NULL,
    resultado_json  JSON NOT NULL,
    criado_em       TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rotulos (
    id          INTEGER DEFAULT nextval('seq_rotulos_id') PRIMARY KEY,
    ticker      VARCHAR NOT NULL,
    timeframe   VARCHAR NOT NULL,
    datetime    TIMESTAMP NOT NULL,
    label       INTEGER NOT NULL,
    fonte       VARCHAR DEFAULT 'backtest',
    run_id      INTEGER REFERENCES backtest_runs(id),
    criado_em   TIMESTAMP DEFAULT now(),
    UNIQUE (ticker, timeframe, datetime, run_id)
);

CREATE TABLE IF NOT EXISTS ml_models (
    id                   VARCHAR PRIMARY KEY,
    nome                 VARCHAR NOT NULL,
    ticker               VARCHAR NOT NULL,
    timeframe            VARCHAR NOT NULL,
    n_features           INTEGER NOT NULL,
    seq_len              INTEGER NOT NULL,
    train_periodo_inicio TIMESTAMP,
    train_periodo_fim    TIMESTAMP,
    test_periodo_inicio  TIMESTAMP,
    test_periodo_fim     TIMESTAMP,
    metrics_json         JSON,
    config_json          JSON,
    model_path           VARCHAR NOT NULL,
    criado_em            TIMESTAMP DEFAULT now()
);
"""


def inicializar_banco():
    conn = duckdb.connect(DB_PATH)
    try:
        for stmt in DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(stmt)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    inicializar_banco()
    print(f"Banco inicializado em: {DB_PATH}")
