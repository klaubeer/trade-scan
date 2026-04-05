from contextlib import contextmanager
import duckdb
from backend.config import DB_PATH


@contextmanager
def get_conn():
    conn = duckdb.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass  # DuckDB pode não ter transação ativa após DDL (CREATE TEMP TABLE etc.)
        raise
    finally:
        conn.close()
