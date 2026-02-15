"""
Inicializar módulo de utilitários
"""

from .data_loading import load_geojson_safe, load_parquet_safe, validate_dataframe
from .formatters import (
    clean_label,
    fix_mojibake,
    fmt_int,
    macro_sector_from_label,
    normalize_uf,
    strip_accents,
)
from .logging_config import get_logger, setup_logging

__all__ = [
    "fmt_int",
    "fix_mojibake",
    "strip_accents",
    "clean_label",
    "normalize_uf",
    "macro_sector_from_label",
    "load_parquet_safe",
    "load_geojson_safe",
    "validate_dataframe",
    "setup_logging",
    "get_logger",
]
