"""
Configurações centralizadas do projeto.
Suporta variáveis de ambiente via .env
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


def get_project_root() -> Path:
    """Encontra a raiz do projeto."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PathConfig:
    """Configuração de caminhos do projeto."""

    root: Path
    data: Path
    raw: Path
    processed: Path
    geo: Path

    @property
    def ibge_tidy(self) -> Path:
        return self.processed / "ibge_3274_3275_tidy.parquet"

    @property
    def companies_agg(self) -> Path:
        return self.processed / "companies_agg.parquet"

    @property
    def companies_agg_csv(self) -> Path:
        return self.processed / "companies_agg.csv"

    @property
    def opportunity_scores(self) -> Path:
        return self.processed / "opportunity_scores.parquet"

    @property
    def opportunity_scores_v3(self) -> Path:
        return self.processed / "opportunity_scores_v3.parquet"

    @property
    def caged_state_sector_year(self) -> Path:
        return self.processed / "caged_state_sector_year.parquet"

    @property
    def caged_state_sector_month(self) -> Path:
        return self.processed / "caged_state_sector_month.parquet"

    @property
    def brazil_states_geojson(self) -> Path:
        return self.geo / "brazil_states.geojson"

    @property
    def ibge_raw_3274(self) -> Path:
        return self.raw / "ibge" / "sidra_3274_2008_2021_raw.csv"

    @property
    def ibge_raw_3275(self) -> Path:
        return self.raw / "ibge" / "sidra_3275_2008_2021_raw.csv"

    @property
    def caged_xlsx_dir(self) -> Path:
        return self.raw / "caged" / "caged_xlsx"


class Settings:
    """Configurações globais da aplicação."""

    def __init__(self):
        self.root = get_project_root()
        self.paths = PathConfig(
            root=self.root,
            data=self.root / "data",
            raw=self.root / "data" / "raw",
            processed=self.root / "data" / "processed",
            geo=self.root / "data" / "geo",
        )

        # App settings
        self.app_title = os.getenv("APP_TITLE", "Painel B2B Brasil — Inteligência de Mercado")
        self.app_icon = os.getenv("APP_ICON", "chart")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Data settings
        self.default_year: Optional[int] = None
        self.cache_ttl_seconds = int(os.getenv("CACHE_TTL", "3600"))

        # Backend settings
        self.backend_default = os.getenv("B2B_BACKEND", "duckdb").lower()

        # BigQuery settings
        self.bq_project = os.getenv("BQ_PROJECT")
        self.bq_dataset_raw = os.getenv("BQ_DATASET_RAW")
        self.bq_dataset_gold = os.getenv("BQ_DATASET_GOLD", os.getenv("BQ_DATASET"))
        self.bq_location = os.getenv("BQ_LOCATION")

        # BigQuery table names (defaults)
        self.bq_table_companies = os.getenv("BQ_TABLE_COMPANIES", "companies_agg")
        self.bq_table_opportunity = os.getenv("BQ_TABLE_OPPORTUNITY", "opportunity_scores")
        self.bq_table_caged = os.getenv("BQ_TABLE_CAGED", "caged_state_sector_year")
        self.bq_table_pnad_metrics = os.getenv(
            "BQ_TABLE_PNAD_METRICS",
            "pnad_uf_trimestre_sexo_idade_metrics",
        )
        self.bq_table_rais_metrics = os.getenv("BQ_TABLE_RAIS_METRICS", "rais_uf_ano")

        # UI settings
        self.streamlit_theme = os.getenv("STREAMLIT_THEME", "dark")
        self.layout = os.getenv("LAYOUT", "wide")

    def ensure_data_files_exist(self) -> list[str]:
        """
        Verifica se arquivos de dados críticos existem.
        Retorna lista de arquivos faltantes.
        """
        critical_files = [
            self.paths.companies_agg,
            self.paths.opportunity_scores,
            self.paths.brazil_states_geojson,
        ]

        missing = []
        for file_path in critical_files:
            if not file_path.exists():
                missing.append(str(file_path))

        return missing


# Instance global
settings = Settings()
