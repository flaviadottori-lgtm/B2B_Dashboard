"""
Inicializar módulo de utilitários
"""

from .formatters import (
    fmt_int,
    fix_mojibake,
    strip_accents,
    clean_label,
    normalize_uf,
    macro_sector_from_label,
)

from .data_loading import (
    load_parquet_safe,
    load_geojson_safe,
    validate_dataframe,
)

from .logging_config import (
    setup_logging,
    get_logger,
)

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
