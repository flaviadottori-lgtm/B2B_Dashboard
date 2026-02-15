import duckdb
import pandas as pd
from pathlib import Path
import sys

from src.utils.paths import DUCKDB_PATH

def read_df_with_fallback(name, candidates):
    for file, ftype in candidates:
        path = PROCESSED / file
        if not path.exists():
            print(f"[{name}] {path} - arquivo não encontrado.")
            continue
        if ftype == 'parquet':
            # Tenta pyarrow
            try:
                df = pd.read_parquet(path, engine='pyarrow')
                print(f"[{name}] {path} - parquet(pyarrow) - OK")
                return df
            except Exception as e:
                print(f"[{name}] {path} - parquet(pyarrow) - ERRO: {e}")
            # Tenta fastparquet se instalado
            try:
                import fastparquet
                df = pd.read_parquet(path, engine='fastparquet')
                print(f"[{name}] {path} - parquet(fastparquet) - OK")
                return df
            except ImportError:
                print(f"[{name}] {path} - fastparquet não instalado.")
            except Exception as e:
                print(f"[{name}] {path} - parquet(fastparquet) - ERRO: {e}")
        elif ftype == 'csv':
            try:
                df = pd.read_csv(path)
                print(f"[{name}] {path} - csv - OK")
                return df
            except Exception as e:
                print(f"[{name}] {path} - csv - ERRO: {e}")
    print(f"[{name}] Nenhum arquivo válido encontrado ou todos corrompidos.")
    return None


## Função build_dim_uf removida: dim_uf será sempre criada por ensure_dim_uf com schema correto

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
    # Cria view pnad_enriched se pnad existir
    tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
    if "pnad" in tables:
        con.execute("""
            CREATE OR REPLACE VIEW pnad_enriched AS
            SELECT
              p.*,
              u.sigla_uf,
              u.nome_uf,
              u.regiao
            FROM pnad p
            LEFT JOIN dim_uf u
              ON TRY_CAST(p.uf_code AS INTEGER) = u.cod_uf;
        """)
        # Sanity check
        res = con.execute("""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN sigla_uf IS NULL THEN 1 ELSE 0 END) AS sem_match
            FROM pnad_enriched;
        """).fetchone()
        total, sem_match = res
        if sem_match > 0:
            import logging
            logging.warning(f"PNAD: {sem_match} registros sem correspondência de UF (de {total}) na view pnad_enriched.")

def main():
    con = duckdb.connect(str(DB_PATH))
    ensure_dim_uf(con)
    tables = {
        "companies_agg": [
            ("companies_agg.parquet", "parquet"),
            ("companies_agg.parquet.bak", "parquet"),
            ("companies_agg.csv", "csv"),
        ],
        "opportunity_scores": [
            ("opportunity_scores.parquet", "parquet"),
            ("opportunity_scores_v3.parquet", "parquet"),
            ("opportunity_scores.parquet.bak", "parquet"),
        ],
        "caged_state_sector_year": [
            ("caged_state_sector_year.parquet", "parquet"),
            ("caged_state_sector_year.parquet.bak", "parquet"),
        ],
        "pnad_uf_quarter_gender_age": [
            ("pnad_uf_quarter_gender_age.parquet", "parquet"),
            ("pnad_uf_quarter_gender_age.csv", "csv"),
        ],
    }
    created = []
    for name, candidates in tables.items():
        df = read_df_with_fallback(name, candidates)
        if df is not None:
            con.register(f"df_{name}", df)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df_{name}")
            print(f"Tabela {name} criada no DuckDB ({len(df)} linhas)")
            created.append(name)
        else:
            print(f"Tabela {name} NÃO criada.")
    print("\nTabelas criadas:")
    print(con.execute("SHOW TABLES").df())
    for name in created:
        count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"{name}: {count} linhas")
    con.close()
    print("Mart DuckDB atualizado!")

if __name__ == "__main__":
    main()
