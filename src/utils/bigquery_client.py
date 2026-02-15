"""
Cliente BigQuery com tratamento de erros e retorno em DataFrame.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import pandas as pd

try:
    from google.cloud import bigquery
except Exception:  # pragma: no cover
    bigquery = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def get_bq_client(project: Optional[str] = None) -> Optional["bigquery.Client"]:
    """
    Retorna cliente BigQuery usando ADC ou GOOGLE_APPLICATION_CREDENTIALS.
    """
    if bigquery is None:
        logger.error("google-cloud-bigquery não está instalado.")
        return None

    project_id = project or os.getenv("BQ_PROJECT")
    try:
        return bigquery.Client(project=project_id)
    except Exception as exc:
        logger.error(f"Erro ao criar cliente BigQuery: {exc}")
        return None


def query_df(
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    project: Optional[str] = None,
    location: Optional[str] = None,
) -> pd.DataFrame:
    """
    Executa SQL no BigQuery e retorna DataFrame.
    """
    client = get_bq_client(project=project)
    if client is None:
        return pd.DataFrame()

    job_config = None
    if params:
        try:
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(k, "STRING" if isinstance(v, str) else "INT64", v)
                    for k, v in params.items()
                ]
            )
        except Exception as exc:
            logger.error(f"Erro ao montar parâmetros BigQuery: {exc}")
            job_config = None

    try:
        query_job = client.query(sql, job_config=job_config, location=location)
        return query_job.result().to_dataframe()
    except Exception as exc:
        logger.error(f"Erro ao executar query BigQuery: {exc}")
        return pd.DataFrame()


def check_tables(
    project: str,
    dataset: str,
    table_names: list[str],
    location: Optional[str] = None,
) -> Dict[str, bool]:
    """
    Verifica existência de tabelas no dataset.
    """
    if bigquery is None:
        return {name: False for name in table_names}

    sql = f"""
    SELECT table_name
    FROM `{project}.{dataset}.INFORMATION_SCHEMA.TABLES`
    """
    df = query_df(sql, project=project, location=location)
    if df.empty or "table_name" not in df.columns:
        return {name: False for name in table_names}
    available = {str(t).lower() for t in df["table_name"].tolist()}
    return {name: (name.lower() in available) for name in table_names}

