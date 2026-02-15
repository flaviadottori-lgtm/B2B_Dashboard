from pathlib import Path

import duckdb
import pytest

from scripts.bootstrap_duckdb import ensure_dim_uf, ensure_views


def test_bootstrap_duckdb_contract():
    con = duckdb.connect(":memory:")
    # Cria fake PNAD e CAGED
    import tempfile

    import pandas as pd

    # Caso 1: ingestão parquet sintético
    with tempfile.TemporaryDirectory() as tmpdir:
        parquet_path = Path(tmpdir) / "pnad_uf_quarter_gender_age.parquet"
        df = pd.DataFrame(
            {
                "ano": [2022],
                "quarter": ["Q1"],
                "gender": ["M"],
                "age_group": ["25-29"],
                "value": [1000.0],
                "uf_code": ["11"],
            }
        )
        df.to_parquet(parquet_path)
        con.execute(
            f"CREATE OR REPLACE TABLE caged_state_sector_year (year INTEGER, cod_uf INTEGER, sector VARCHAR, value DOUBLE, uf_code VARCHAR);"
        )
        con.execute(f"INSERT INTO caged_state_sector_year VALUES (2022, 11, 'Agro', 500.0, '11');")
        # Simula ingestão
        con.execute(
            f"CREATE OR REPLACE TABLE pnad_uf_quarter_gender_age AS SELECT * FROM read_parquet('{str(parquet_path)}')"
        )
        ensure_dim_uf(con)
        ensure_views(con)
        ensure_dim_uf(con)
        ensure_views(con)
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        for t in ["dim_uf", "pnad", "pnad_enriched", "caged", "caged_enriched"]:
            assert t in tables
        assert con.execute("SELECT COUNT(*) FROM dim_uf").fetchone()[0] == 27
        df_out = con.execute("SELECT sigla_uf FROM pnad_enriched").fetchdf()
        assert df_out["sigla_uf"].iloc[0] == "RO"
        df2 = con.execute("SELECT sigla_uf FROM caged_enriched").fetchdf()
        assert df2["sigla_uf"].iloc[0] == "RO"
        # pnad_enriched tem > 0
        assert con.execute("SELECT COUNT(*) FROM pnad_enriched").fetchone()[0] > 0
        # Caso 2: PNAD só com cod_uf
        con.execute("DROP TABLE pnad_uf_quarter_gender_age")
        con.execute("""
            CREATE TABLE pnad_uf_quarter_gender_age (
                ano INTEGER, quarter VARCHAR, gender VARCHAR, age_group VARCHAR, value DOUBLE, cod_uf INTEGER
            );
            INSERT INTO pnad_uf_quarter_gender_age VALUES (2022, 'Q1', 'M', '25-29', 1000.0, 11);
        """)
        ensure_views(con)
        ensure_views(con)
        df_out2 = con.execute("SELECT sigla_uf FROM pnad_enriched").fetchdf()
        assert df_out2["sigla_uf"].iloc[0] == "RO"
        con.close()
