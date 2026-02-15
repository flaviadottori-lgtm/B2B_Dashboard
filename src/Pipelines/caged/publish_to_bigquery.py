from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from google.cloud import bigquery

LOGGER = logging.getLogger("caged.publish")


DEFAULT_PROJECT = os.getenv("GCP_PROJECT", "dados-mercado-brasil")
DEFAULT_DATASET_RAW = os.getenv("BQ_DATASET_RAW", "raw")
DEFAULT_DATASET_GOLD = os.getenv("BQ_DATASET_GOLD", "gold")
DEFAULT_LOCATION = "southamerica-east1"


def _find_parquet(processed_dir: Path) -> Path:
    preferred = processed_dir / "caged_state_sector_month.parquet"
    if preferred.exists():
        return preferred
    candidates = sorted(processed_dir.glob("caged*.parquet"))
    if not candidates:
        raise FileNotFoundError(f"No CAGED parquet found in {processed_dir}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _pick_column(schema: list[bigquery.SchemaField], names: list[str]) -> Optional[str]:
    lower_map = {field.name.lower(): field.name for field in schema}
    for name in names:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None


def _cast_expr(column: str, as_type: str) -> str:
    return f"SAFE_CAST(`{column}` AS {as_type})"


def load_raw_table(
    client: bigquery.Client,
    parquet_path: Path,
    project_id: str,
    dataset_raw: str,
    table_raw: str = "caged_movimentacao",
    write_disposition: str = "WRITE_TRUNCATE",
    location: str = DEFAULT_LOCATION,
) -> str:
    table_id = f"{project_id}.{dataset_raw}.{table_raw}"
    LOGGER.info("Loading raw table: %s", table_id)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=write_disposition,
        autodetect=True,
    )
    with open(parquet_path, "rb") as handle:
        load_job = client.load_table_from_file(
            handle,
            table_id,
            job_config=job_config,
            location=location,
        )
    load_job.result()
    LOGGER.info("Raw load completed: %s rows", client.get_table(table_id).num_rows)
    return table_id


def build_gold_table(
    client: bigquery.Client,
    project_id: str,
    dataset_raw: str,
    dataset_gold: str,
    raw_table: str = "caged_movimentacao",
    gold_table: str = "caged_uf_mes",
    location: str = DEFAULT_LOCATION,
) -> None:
    raw_table_id = f"{project_id}.{dataset_raw}.{raw_table}"
    gold_table_id = f"{project_id}.{dataset_gold}.{gold_table}"

    schema = client.get_table(raw_table_id).schema
    year_col = _pick_column(schema, ["ano", "year"])
    month_col = _pick_column(schema, ["mes", "month"])
    uf_col = _pick_column(schema, ["sigla_uf", "uf", "state"])
    sector_col = _pick_column(schema, ["cnae_2_secao", "sector"])
    subclasse_col = _pick_column(schema, ["cnae_2_subclasse", "subclasse"])
    saldo_col = _pick_column(schema, ["saldo_movimentacao", "job_balance", "saldo"])
    adm_col = _pick_column(schema, ["admissoes", "admissao"])
    des_col = _pick_column(schema, ["desligamentos", "desligamento"])

    missing = [
        name
        for name, col in {
            "ano/year": year_col,
            "mes/month": month_col,
            "sigla_uf/uf/state": uf_col,
            "cnae_2_secao/sector": sector_col,
            "saldo_movimentacao/job_balance": saldo_col,
        }.items()
        if col is None
    ]
    if missing:
        raise ValueError(f"Missing required columns in raw table: {', '.join(missing)}")

    if sector_col != "cnae_2_secao":
        LOGGER.warning("Using raw column '%s' as cnae_2_secao", sector_col)
    if subclasse_col is None:
        LOGGER.warning("cnae_2_subclasse missing in raw table; writing NULLs")
    if adm_col is None or des_col is None:
        LOGGER.warning("admissoes/desligamentos missing in raw table; writing NULLs")

    ano_expr = _cast_expr(year_col, "INT64")
    mes_expr = _cast_expr(month_col, "INT64")
    uf_expr = f"`{uf_col}`"
    secao_expr = f"`{sector_col}`"
    subclasse_expr = f"`{subclasse_col}`" if subclasse_col else "CAST(NULL AS STRING)"
    saldo_mov_expr = _cast_expr(saldo_col, "FLOAT64")
    adm_expr = _cast_expr(adm_col, "FLOAT64") if adm_col else "CAST(NULL AS FLOAT64)"
    des_expr = _cast_expr(des_col, "FLOAT64") if des_col else "CAST(NULL AS FLOAT64)"

    truncate_sql = f"TRUNCATE TABLE `{gold_table_id}`"
    insert_sql = f"""
    INSERT INTO `{gold_table_id}` (
        ano,
        mes,
        sigla_uf,
        cnae_2_secao,
        cnae_2_subclasse,
        saldo_movimentacao,
        admissoes,
        desligamentos,
        saldo,
        indice_volatilidade,
        extracao_data
    )
    SELECT
        {ano_expr} AS ano,
        {mes_expr} AS mes,
        {uf_expr} AS sigla_uf,
        {secao_expr} AS cnae_2_secao,
        {subclasse_expr} AS cnae_2_subclasse,
        {saldo_mov_expr} AS saldo_movimentacao,
        {adm_expr} AS admissoes,
        {des_expr} AS desligamentos,
        {saldo_mov_expr} AS saldo,
        STDDEV_POP({saldo_mov_expr}) OVER (
            PARTITION BY {uf_expr}, {secao_expr}, {subclasse_expr}
        ) AS indice_volatilidade,
        CURRENT_TIMESTAMP() AS extracao_data
    FROM `{raw_table_id}`
    """

    LOGGER.info("Refreshing gold table: %s", gold_table_id)
    client.query(truncate_sql, location=location).result()
    client.query(insert_sql, location=location).result()
    LOGGER.info("Gold table refresh completed")


def publish_caged_to_bigquery(
    processed_dir: Path,
    project_id: str = DEFAULT_PROJECT,
    dataset_raw: str = DEFAULT_DATASET_RAW,
    dataset_gold: str = DEFAULT_DATASET_GOLD,
    location: str = DEFAULT_LOCATION,
    write_disposition: str = "WRITE_TRUNCATE",
) -> None:
    client = bigquery.Client(project=project_id)
    parquet_path = _find_parquet(processed_dir)
    LOGGER.info("Using parquet: %s", parquet_path)
    load_raw_table(
        client,
        parquet_path,
        project_id=project_id,
        dataset_raw=dataset_raw,
        write_disposition=write_disposition,
        location=location,
    )
    build_gold_table(
        client,
        project_id=project_id,
        dataset_raw=dataset_raw,
        dataset_gold=dataset_gold,
        location=location,
    )
