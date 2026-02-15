import os
import sys
from pathlib import Path

import duckdb

# ===== DuckDB path (single source of truth) =====
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # raiz do repo (B2B_Dashboard)
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "marts" / "b2b.duckdb"
DB_PATH = Path(os.getenv("B2B_DUCKDB_PATH", str(DEFAULT_DB_PATH))).resolve()

if not DB_PATH.exists():
    print(f"ERRO: DuckDB não encontrado em: {DB_PATH}")
    print("Dica: defina a env var B2B_DUCKDB_PATH ou gere o banco em data/marts/b2b.duckdb")
    sys.exit(1)

print(f"✅ Usando DuckDB: {DB_PATH}")

con = duckdb.connect(str(DB_PATH), read_only=True)


def exists(table_name: str) -> bool:
    return table_name in [r[0] for r in con.execute("SHOW TABLES").fetchall()]


print("\nSHOW TABLES:")
print(con.execute("SHOW TABLES").fetchdf())

if not exists("dim_uf"):
    print("\nERRO: dim_uf não existe!")
    sys.exit(1)

print("\nCOUNT dim_uf:")
print(con.execute("SELECT COUNT(*) AS n FROM dim_uf").fetchdf())

for t in ["pnad", "pnad_enriched"]:
    if exists(t):
        print(f"\nCOUNT {t}:")
        print(con.execute(f"SELECT COUNT(*) AS n FROM {t}").fetchdf())
    else:
        print(f"\nINFO: tabela '{t}' não existe (ok, depende do pipeline).")

if exists("pnad_enriched"):
    print("\nDiagnóstico pnad_enriched (sem_match):")
    print(con.execute("""
            SELECT
              SUM(CASE WHEN sigla_uf IS NULL THEN 1 ELSE 0 END) AS sem_match
            FROM pnad_enriched
            """).fetchdf())

con.close()
