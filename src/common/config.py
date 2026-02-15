"""
Configuração centralizada via variáveis de ambiente
"""

import os
from typing import NamedTuple


class Config(NamedTuple):
    GCP_PROJECT: str
    BQ_DATASET_STG: str
    BQ_DATASET_GOLD: str
    BQ_DATASET_META: str
    GCS_BUCKET_RAW: str
    TIMEZONE: str


def get_config() -> Config:
    return Config(
        GCP_PROJECT=os.environ["GCP_PROJECT"],
        BQ_DATASET_STG=os.environ["BQ_DATASET_STG"],
        BQ_DATASET_GOLD=os.environ["BQ_DATASET_GOLD"],
        BQ_DATASET_META=os.environ["BQ_DATASET_META"],
        GCS_BUCKET_RAW=os.environ["GCS_BUCKET_RAW"],
        TIMEZONE=os.environ.get("TIMEZONE", "America/Fortaleza"),
    )
