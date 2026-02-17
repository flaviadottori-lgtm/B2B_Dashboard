import duckdb
import sys
from src.utils.paths import DUCKDB_PATH


def print_db_info():
    db_path = DUCKDB_PATH.resolve()
    print(f"[BOOTSTRAP] DuckDB path: {db_path}")
    if db_path.exists():
        print(f"[BOOTSTRAP] DB exists: True | Size: {db_path.stat().st_size} bytes")
    else:
        print(f"[BOOTSTRAP] DB exists: False")


def get_con():
    DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(DUCKDB_PATH))


def ensure_dim_uf(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS dim_uf (
          cod_uf INTEGER PRIMARY KEY,
          sigla_uf VARCHAR NOT NULL,
          nome_uf  VARCHAR NOT NULL,
          regiao   VARCHAR NOT NULL
        );
    """)
    con.execute("DELETE FROM dim_uf;")
    con.execute("""
        INSERT INTO dim_uf VALUES
        (11,'RO','Rondônia','Norte'),
        (12,'AC','Acre','Norte'),
        (13,'AM','Amazonas','Norte'),
        (14,'RR','Roraima','Norte'),
        (15,'PA','Pará','Norte'),
        (16,'AP','Amapá','Norte'),
        (17,'TO','Tocantins','Norte'),
        (21,'MA','Maranhão','Nordeste'),
        (22,'PI','Piauí','Nordeste'),
        (23,'CE','Ceará','Nordeste'),
        (24,'RN','Rio Grande do Norte','Nordeste'),
        (25,'PB','Paraíba','Nordeste'),
        (26,'PE','Pernambuco','Nordeste'),
        (27,'AL','Alagoas','Nordeste'),
        (28,'SE','Sergipe','Nordeste'),
        (29,'BA','Bahia','Nordeste'),
        (31,'MG','Minas Gerais','Sudeste'),
        (32,'ES','Espírito Santo','Sudeste'),
        (33,'RJ','Rio de Janeiro','Sudeste'),
        (35,'SP','São Paulo','Sudeste'),
        (41,'PR','Paraná','Sul'),
        (42,'SC','Santa Catarina','Sul'),
        (43,'RS','Rio Grande do Sul','Sul'),
        (50,'MS','Mato Grosso do Sul','Centro-Oeste'),
        (51,'MT','Mato Grosso','Centro-Oeste'),
        (52,'GO','Goiás','Centro-Oeste'),
        (53,'DF','Distrito Federal','Centro-Oeste');
    """)


def ensure_views(con):
    def is_table(name):
        q = """
        SELECT table_type FROM information_schema.tables WHERE table_name = ?
        """
        res = con.execute(q, [name]).fetchone()
        return res and res[0] == "BASE TABLE"

    def is_view(name):
        q = """
        SELECT table_type FROM information_schema.tables WHERE table_name = ?
        """
        res = con.execute(q, [name]).fetchone()
        return res and res[0] == "VIEW"

    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]

    # PNAD: priorizar tabela física
    pnad_base = None
    if "pnad_uf_quarter_gender_age" in tables and is_table("pnad_uf_quarter_gender_age"):
        pnad_base = "pnad_uf_quarter_gender_age"
    elif "pnad" in tables and is_table("pnad"):
        pnad_base = "pnad"

    if pnad_base:
        con.execute(f"CREATE OR REPLACE VIEW pnad AS SELECT * FROM {pnad_base};")
        info = con.execute(f"PRAGMA table_info('{pnad_base}')").fetchdf()
        uf_col = None
        for col in ["uf_code", "cod_uf", "uf", "state"]:
            if col in info["name"].values:
                uf_col = col
                break
        if uf_col:
            join_expr = f"TRY_CAST(p.{uf_col} AS INTEGER) = u.cod_uf"
            con.execute(f"""
                CREATE OR REPLACE VIEW pnad_enriched AS
                SELECT p.*, u.sigla_uf, u.nome_uf, u.regiao
                FROM {pnad_base} p
                LEFT JOIN dim_uf u
                  ON {join_expr};
            """)
        else:
            con.execute("""
                CREATE OR REPLACE VIEW pnad_enriched AS
                SELECT p.*, CAST(NULL AS VARCHAR) AS sigla_uf, CAST(NULL AS VARCHAR) AS nome_uf, CAST(NULL AS VARCHAR) AS regiao
                FROM {pnad_base} p WHERE FALSE;
            """)
    else:
        con.execute("""
            CREATE OR REPLACE VIEW pnad AS
            SELECT
              CAST(NULL AS INTEGER) AS ano,
              CAST(NULL AS VARCHAR) AS quarter,
              CAST(NULL AS INTEGER) AS cod_uf,
              CAST(NULL AS VARCHAR) AS gender,
              CAST(NULL AS VARCHAR) AS age_group,
              CAST(NULL AS DOUBLE) AS value
            WHERE FALSE;
        """)
        con.execute("""
            CREATE OR REPLACE VIEW pnad_enriched AS
            SELECT CAST(NULL AS INTEGER) AS ano, CAST(NULL AS VARCHAR) AS quarter, CAST(NULL AS INTEGER) AS cod_uf, CAST(NULL AS VARCHAR) AS gender, CAST(NULL AS VARCHAR) AS age_group, CAST(NULL AS DOUBLE) AS value, CAST(NULL AS VARCHAR) AS sigla_uf, CAST(NULL AS VARCHAR) AS nome_uf, CAST(NULL AS VARCHAR) AS regiao
            WHERE FALSE;
        """)

    # CAGED: priorizar tabela física
    caged_base = None
    if "caged_state_sector_year" in tables and is_table("caged_state_sector_year"):
        caged_base = "caged_state_sector_year"
    elif "caged" in tables and is_table("caged"):
        caged_base = "caged"

    if caged_base:
        con.execute(f"CREATE OR REPLACE VIEW caged AS SELECT * FROM {caged_base};")
        info = con.execute(f"PRAGMA table_info('{caged_base}')").fetchdf()
        uf_col = None
        for col in ["cod_uf", "uf_code", "uf", "state"]:
            if col in info["name"].values:
                uf_col = col
                break
        if uf_col:
            join_expr = f"TRY_CAST(c.{uf_col} AS INTEGER) = u.cod_uf"
            con.execute(f"""
                CREATE OR REPLACE VIEW caged_enriched AS
                SELECT c.*, u.sigla_uf, u.nome_uf, u.regiao
                FROM {caged_base} c
                LEFT JOIN dim_uf u
                  ON {join_expr};
            """)
        else:
            con.execute(f"""
                CREATE OR REPLACE VIEW caged_enriched AS
                SELECT c.*, CAST(NULL AS VARCHAR) AS sigla_uf, CAST(NULL AS VARCHAR) AS nome_uf, CAST(NULL AS VARCHAR) AS regiao
                FROM {caged_base} c WHERE FALSE;
            """)
    else:
        con.execute("""
            CREATE OR REPLACE VIEW caged AS
            SELECT
              CAST(NULL AS INTEGER) AS year,
              CAST(NULL AS INTEGER) AS cod_uf,
              CAST(NULL AS VARCHAR) AS sector,
              CAST(NULL AS DOUBLE) AS value
            WHERE FALSE;
        """)
        con.execute("""
            CREATE OR REPLACE VIEW caged_enriched AS
            SELECT CAST(NULL AS INTEGER) AS year, CAST(NULL AS INTEGER) AS cod_uf, CAST(NULL AS VARCHAR) AS sector, CAST(NULL AS DOUBLE) AS value, CAST(NULL AS VARCHAR) AS sigla_uf, CAST(NULL AS VARCHAR) AS nome_uf, CAST(NULL AS VARCHAR) AS regiao
            WHERE FALSE;
        """)


def main():
    con = get_con()

    # Ingestão PNAD opcional
    import os
    from pathlib import Path

    candidates = [
        Path("data/processed/pnad_uf_quarter_gender_age.parquet"),
        Path("data/marts/pnad/pnad_uf_quarter_gender_age.parquet"),
        Path("data/processed/pnad_uf_quarter_gender_age.csv"),
    ]
    pnad_loaded = False
    for file in candidates:
        if file.exists():
            if file.suffix == ".parquet":
                con.execute(
                    f"CREATE OR REPLACE TABLE pnad_uf_quarter_gender_age AS SELECT * FROM read_parquet('{str(file)}')"
                )
                print(f"PNAD carregado de {file}")
                pnad_loaded = True
                break
            elif file.suffix == ".csv":
                con.execute(
                    f"CREATE OR REPLACE TABLE pnad_uf_quarter_gender_age AS SELECT * FROM read_csv_auto('{str(file)}')"
                )
                print(f"PNAD carregado de {file}")
                pnad_loaded = True
                break
    ensure_dim_uf(con)
    ensure_views(con)
    con.close()
    print("Bootstrap DuckDB concluído com sucesso.")


if __name__ == "__main__":
    main()
