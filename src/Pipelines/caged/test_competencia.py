import pytest
from src.pipelines.caged.run import get_default_competencia

def test_get_default_competencia():
    # Simula mês anterior
    competencia = get_default_competencia("America/Fortaleza")
    assert len(competencia) == 7 and competencia[4] == '-'
