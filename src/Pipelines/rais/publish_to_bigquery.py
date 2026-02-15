from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List

from google.cloud import bigquery

LOGGER = logging.getLogger("rais.publish")

DEFAULT_PROJECT = os.getenv("GCP_PROJECT", "dados-mercado-brasil")
DEFAULT_DATASET_RAW = os.getenv("BQ_DATASET_RAW", "raw")
DEFAULT_DATASET_GOLD = os.getenv("BQ_DATASET_GOLD", "gold")
DEFAULT_LOCATION = "southamerica-east1"


def _find_parquets(base_dir: Path) -> List[Path]:
    return sorted(base_dir.rglob("*.parquet"))


def _build_gold_insert_sql(
    project_id: str,
    dataset_gold: str,
    dataset_raw: str,
    raw_table: str,
    gold_table: str,
    gold_schema: List[bigquery.SchemaField],
) -> str:
    return f"""
    CREATE OR REPLACE TABLE `{project_id}.{dataset_gold}.{gold_table}` AS
    SELECT
      ano,
      sigla_uf,
      cnae_subclasse,
      sexo,
      grupo_idade,
      grau_instrucao,
      SUM(vinculos) AS vinculos,
      CURRENT_TIMESTAMP() AS extracao_data
    FROM `{project_id}.{dataset_raw}.{raw_table}`
    GROUP BY
      ano, sigla_uf, cnae_subclasse, sexo, grupo_idade, grau_instrucao;
    """


def publish_rais_to_bigquery(
    base_dir: Path,
    project_id: str = DEFAULT_PROJECT,
    dataset_raw: str = DEFAULT_DATASET_RAW,
    dataset_gold: str = DEFAULT_DATASET_GOLD,
    raw_table: str = "rais_vinc_uf_ano",
    gold_table: str = "rais_uf_ano",
    location: str = DEFAULT_LOCATION,
) -> None:
    client = bigquery.Client(project=project_id)

    parquet_files = _find_parquets(base_dir)
    LOGGER.info("Parquets encontrados: %d", len(parquet_files))
    if not parquet_files:
        raise FileNotFoundError(f"Nenhum parquet encontrado em {base_dir}")

    raw_table_id = f"{project_id}.{dataset_raw}.{raw_table}"
    LOGGER.info("Iniciando upload RAW para %s", raw_table_id)

    for idx, parquet_path in enumerate(parquet_files):
        write_disp = (
            bigquery.WriteDisposition.WRITE_TRUNCATE
            if idx == 0
            else bigquery.WriteDisposition.WRITE_APPEND
        )
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition=write_disp,
            autodetect=True,
        )
        with open(parquet_path, "rb") as handle:
            job = client.load_table_from_file(
                handle,
                raw_table_id,
                job_config=job_config,
                location=location,
            )
        job.result()
        LOGGER.info("Upload concluido: %s", parquet_path.name)

    LOGGER.info("Upload RAW finalizado")

    gold_table_id = f"{project_id}.{dataset_gold}.{gold_table}"
    gold_schema = client.get_table(gold_table_id).schema
    sql = _build_gold_insert_sql(
        project_id=project_id,
        dataset_gold=dataset_gold,
        dataset_raw=dataset_raw,
        raw_table=raw_table,
        gold_table=gold_table,
        gold_schema=gold_schema,
    )

    LOGGER.info("Atualizando GOLD: %s", gold_table_id)
    client.query(sql, location=location).result()
    LOGGER.info("Atualizacao GOLD concluida")

    raw_count_sql = f"SELECT COUNT(*) AS raw_rows FROM `{project_id}.{dataset_raw}.{raw_table}`"
    gold_count_sql = f"SELECT COUNT(*) AS gold_rows FROM `{project_id}.{dataset_gold}.{gold_table}`"
    coverage_sql = f"""
    SELECT
      COUNT(DISTINCT sigla_uf) AS ufs,
      COUNT(DISTINCT ano) AS anos
    FROM `{project_id}.{dataset_gold}.{gold_table}`
    """
    extracao_null_sql = f"""
    SELECT COUNTIF(extracao_data IS NULL) AS nulos
    FROM `{project_id}.{dataset_gold}.{gold_table}`
    """
    max_ano_sql = f"SELECT MAX(ano) AS max_ano FROM `{project_id}.{dataset_gold}.{gold_table}`"
    top_ufs_sql = f"""
    SELECT sigla_uf, SUM(vinculos) AS vinculos
    FROM `{project_id}.{dataset_gold}.{gold_table}`
    WHERE ano = @ano
    GROUP BY sigla_uf
    ORDER BY vinculos DESC
    LIMIT 10
    """

    raw_rows = next(iter(client.query(raw_count_sql, location=location).result()))["raw_rows"]
    gold_rows = next(iter(client.query(gold_count_sql, location=location).result()))["gold_rows"]
    LOGGER.info("VALIDACAO | RAW rows=%s, GOLD rows=%s", raw_rows, gold_rows)

    coverage_row = next(iter(client.query(coverage_sql, location=location).result()))
    LOGGER.info(
        "VALIDACAO | GOLD cobertura: ufs=%s, anos=%s",
        coverage_row["ufs"],
        coverage_row["anos"],
    )

    extracao_row = next(iter(client.query(extracao_null_sql, location=location).result()))
    LOGGER.info("VALIDACAO | extracao_data nulos=%s", extracao_row["nulos"])

    max_ano_row = next(iter(client.query(max_ano_sql, location=location).result()))
    max_ano = max_ano_row["max_ano"]

    if max_ano is not None:
        ufs_sql = f"""
        SELECT DISTINCT sigla_uf
        FROM `{project_id}.{dataset_gold}.{gold_table}`
        WHERE ano = @ano
        ORDER BY sigla_uf
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("ano", "INT64", max_ano)]
        )
        ufs_rows = list(client.query(ufs_sql, location=location, job_config=job_config).result())
        ufs_list = ",".join(row["sigla_uf"] for row in ufs_rows)
        LOGGER.info("VALIDACAO | UFs no ano=%s: %s", max_ano, ufs_list)

        LOGGER.info("VALIDACAO | Top 10 UFs (ano=%s):", max_ano)
        rows = list(client.query(top_ufs_sql, location=location, job_config=job_config).result())
        if not rows:
            LOGGER.info("VALIDACAO | Top 10 vazio (sem dados).")
        for row in rows:
            LOGGER.info("VALIDACAO | UF=%s vinculos=%s", row["sigla_uf"], row["vinculos"])
    else:
        LOGGER.info("VALIDACAO | Top 10 UFs: sem ano disponivel")

    if gold_rows == 0:
        LOGGER.error("VALIDACAO | GOLD rows=0")
        raise RuntimeError("GOLD rows=0")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    base_dir = Path("data/processed/rais/agg_parquet")
    publish_rais_to_bigquery(base_dir=base_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
