from src.utils.paths import DUCKDB_PATH
import duckdb


def test_duckdb_path_consistency():
    # O bootstrap e o app devem usar exatamente este caminho
    db_path = str(DUCKDB_PATH)
    con = duckdb.connect(db_path)
    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    # O banco deve ter as views/tabelas padrão criadas pelo bootstrap
    assert "pnad" in tables
    assert "pnad_enriched" in tables
    assert "dim_uf" in tables
    con.close()
