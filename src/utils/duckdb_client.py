# Corrige NameError para duckdb
import duckdb


def get_con():
    """
    Retorna uma conexão DuckDB para o arquivo b2b.duckdb.
    """
    from src.utils.paths import DUCKDB_PATH

    return duckdb.connect(str(DUCKDB_PATH))
