# Arquivo: src/pipelines/caged/run.py
"""
Pipeline CAGED - download -> parquet -> publish BigQuery.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path

from src.pipelines.caged.download_caged_xlsx import download_competencia
from src.pipelines.caged.build_caged_parquet import main as build_caged_parquet
from src.pipelines.caged.publish_to_bigquery import publish_caged_to_bigquery
from src.pipelines.caged.watermark import WatermarkController
from src.common.config import get_config
from src.common.logging_utils import setup_logging, get_run_id


def parse_args():
    parser = argparse.ArgumentParser(description="CAGED Cloud Pipeline Runner")
    parser.add_argument(
        "--competencia", type=str, help="Competência YYYY-MM a processar (default: mês anterior)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Forçar reprocessamento mesmo se já processado com sucesso",
    )
    return parser.parse_args()


def get_default_competencia(tz: str) -> str:
    now = datetime.now(timezone.utc).astimezone()
    if tz:
        try:
            import pytz

            now = now.astimezone(pytz.timezone(tz))
        except Exception:
            pass
    first_day = now.replace(day=1)
    prev_month = first_day - timedelta(days=1)
    return prev_month.strftime("%Y-%m")


def main():
    args = parse_args()
    config = get_config()
    setup_logging()
    run_id = get_run_id()
    competencia = args.competencia or get_default_competencia(config.TIMEZONE)
    logger = logging.getLogger("caged.pipeline")
    logger.info({"event": "pipeline_start", "run_id": run_id, "competencia": competencia})

    watermark = WatermarkController(config)
    if watermark.is_processed(competencia) and not args.force:
        logger.info({"event": "already_processed", "competencia": competencia})
        print(f"Competência {competencia} já processada com sucesso. Use --force para reprocessar.")
        sys.exit(0)

    try:
        year, month = competencia.split("-")
        download_competencia(int(year), int(month))
        build_caged_parquet()

        processed_dir = Path(__file__).resolve().parents[3] / "data" / "processed"
        dataset_raw = os.getenv("BQ_DATASET_RAW", "raw")
        publish_caged_to_bigquery(
            processed_dir=processed_dir,
            project_id=config.GCP_PROJECT,
            dataset_raw=dataset_raw,
            dataset_gold=config.BQ_DATASET_GOLD,
        )
        watermark.mark_success(competencia, run_id)
        logger.info({"event": "pipeline_success", "run_id": run_id, "competencia": competencia})
    except Exception as e:
        watermark.mark_failed(competencia, run_id, str(e))
        logger.error(
            {
                "event": "pipeline_failed",
                "run_id": run_id,
                "competencia": competencia,
                "error": str(e),
            }
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
