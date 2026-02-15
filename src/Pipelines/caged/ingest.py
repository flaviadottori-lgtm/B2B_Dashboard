"""
Ingestão CAGED: download, upload GCS, validação, manifest
"""

import logging
import os
import tempfile
from typing import Dict
from datetime import datetime
from src.common.gcs_utils import upload_to_gcs, file_exists_gcs
from src.common.govbr_caged import fetch_caged_links, download_caged_file
from src.common.manifest import write_manifest


def ingest_caged(competencia: str, config, run_id: str):
    logger = logging.getLogger("caged.ingest")
    year, month = competencia.split("-")
    links = fetch_caged_links(year, month)
    if not links:
        raise RuntimeError(f"Nenhum link encontrado para competência {competencia}")
    for link in links:
        fname = os.path.basename(link)
        gcs_path = f"caged/raw/ano={year}/mes={month}/{fname}"
        if file_exists_gcs(config.GCS_BUCKET_RAW, gcs_path):
            logger.info({"event": "file_exists_gcs", "gcs_path": gcs_path})
            continue
        with tempfile.TemporaryDirectory() as tmpdir:
            local_path = os.path.join(tmpdir, fname)
            download_caged_file(link, local_path)
            if os.path.getsize(local_path) == 0:
                raise RuntimeError(f"Arquivo baixado está vazio: {link}")
            upload_to_gcs(config.GCS_BUCKET_RAW, gcs_path, local_path)
            logger.info(
                {"event": "uploaded_gcs", "gcs_path": gcs_path, "size": os.path.getsize(local_path)}
            )
            manifest = {
                "competencia": competencia,
                "url": link,
                "filename": fname,
                "gcs_path": gcs_path,
                "run_id": run_id,
                "timestamp": datetime.utcnow().isoformat(),
                "size": os.path.getsize(local_path),
            }
            write_manifest(config.GCS_BUCKET_RAW, gcs_path + ".manifest.json", manifest)
            logger.info({"event": "manifest_written", "manifest": manifest})
