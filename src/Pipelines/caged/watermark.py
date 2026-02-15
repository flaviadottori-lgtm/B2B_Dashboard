"""
Controle de watermark/idempotência para pipeline CAGED
"""

import logging
from datetime import datetime
from typing import Optional

from google.cloud import bigquery


class WatermarkController:
    def __init__(self, config):
        self.config = config
        self.client = bigquery.Client(project=config.GCP_PROJECT)
        self.table = f"{config.GCP_PROJECT}.{config.BQ_DATASET_META}.pipeline_watermark"

    def is_processed(self, competencia: str) -> bool:
        query = f"""
        SELECT status FROM `{self.table}`
        WHERE pipeline_name = 'caged' AND last_success_competencia = @competencia AND status = 'SUCCESS'
        LIMIT 1
        """
        job = self.client.query(
            query,
            job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("competencia", "STRING", competencia)
                ]
            ),
        )
        rows = list(job)
        return bool(rows)

    def mark_success(self, competencia: str, run_id: str):
        self._insert_status(competencia, run_id, "SUCCESS", "")

    def mark_failed(self, competencia: str, run_id: str, details: str):
        self._insert_status(competencia, run_id, "FAILED", details)

    def _insert_status(self, competencia: str, run_id: str, status: str, details: str):
        row = {
            "pipeline_name": "caged",
            "last_success_competencia": competencia,
            "last_run_ts": datetime.utcnow().isoformat(),
            "status": status,
            "details": details,
            "run_id": run_id,
        }
        errors = self.client.insert_rows_json(self.table, [row])
        if errors:
            logging.error(f"Erro ao inserir watermark: {errors}")
