"""
Testes para módulo de carregamento de dados (src/utils/data_loading.py)
"""

import pytest
import pandas as pd
from pathlib import Path
from src.utils.data_loading import (
    validate_dataframe,
)


class TestValidateDataframe:
    """Testes para validação de DataFrame"""

    def test_validate_dataframe_valid(self):
        """Valida DataFrame com colunas obrigatórias"""
        df = pd.DataFrame(
            {
                "year": [2024, 2025],
                "state": ["SP", "RJ"],
                "value": [100, 200],
            }
        )
        assert validate_dataframe(df, ["year", "state", "value"]) is True

    def test_validate_dataframe_empty(self):
        """Rejeita DataFrame vazio"""
        df = pd.DataFrame()
        assert validate_dataframe(df, ["year"]) is False

    def test_validate_dataframe_none(self):
        """Rejeita None"""
        assert validate_dataframe(None, ["year"]) is False

    def test_validate_dataframe_missing_columns(self):
        """Rejeita quando faltam colunas"""
        df = pd.DataFrame({"year": [2024]})
        assert validate_dataframe(df, ["year", "state"]) is False

    def test_validate_dataframe_subset_of_columns(self):
        """Valida quando DataFrame tem colunas extras"""
        df = pd.DataFrame(
            {
                "year": [2024],
                "state": ["SP"],
                "value": [100],
                "extra": [999],
            }
        )
        assert validate_dataframe(df, ["year", "state"]) is True
