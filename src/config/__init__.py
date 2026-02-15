"""
Módulo de configuração centralizado do B2B Dashboard.
"""

from .constants import I18N, MACRO_SECTORS, STATE_TO_UF, UF_ORDER, UF_TO_REGION
from .settings import Settings, get_project_root

__all__ = [
    "Settings",
    "get_project_root",
    "UF_ORDER",
    "STATE_TO_UF",
    "UF_TO_REGION",
    "I18N",
    "MACRO_SECTORS",
]
