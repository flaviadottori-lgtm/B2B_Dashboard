"""
Módulo de configuração centralizado do B2B Dashboard.
"""

from .settings import Settings, get_project_root
from .constants import (
    UF_ORDER,
    STATE_TO_UF,
    UF_TO_REGION,
    I18N,
    MACRO_SECTORS,
)

__all__ = [
    "Settings",
    "get_project_root",
    "UF_ORDER",
    "STATE_TO_UF",
    "UF_TO_REGION",
    "I18N",
    "MACRO_SECTORS",
]
