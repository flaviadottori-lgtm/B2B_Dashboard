"""
Guia de Desenvolvimento - B2B Dashboard
Boas práticas, padrões e conventions do projeto
"""

# ======================================================
# ESTRUTURA DE MÓDULOS
# ======================================================

# ✅ BOM: Imports organizados e limpos
from pathlib import Path
import logging

from src.config import settings
from src.utils import fmt_int, load_parquet_safe
from src.core import prep_companies

logger = logging.getLogger(__name__)

# ❌ RUIM: Imports desorganizados
# from src.config import *
# from src import *
# import pandas as pd, numpy as np, plotly.express as px


# ======================================================
# TYPE HINTS E DOCSTRINGS
# ======================================================

# ✅ BOM: Type hints + docstring Google
def calculate_net_jobs(admissions: int, separations: int) -> int:
    """
    Calcula o saldo líquido de empregos.

    Args:
        admissions: Número de admissões no período
        separations: Número de desligamentos no período

    Returns:
        Saldo líquido (admissões - desligamentos)

    Example:
        >>> calculate_net_jobs(1000, 200)
        800
    """
    return admissions - separations


# ❌ RUIM: Sem type hints e sem docstring
def calculate_net_jobs(admissions, separations):
    return admissions - separations


# ======================================================
# LOGGING
# ======================================================

# ✅ BOM: Usar logger centralizado
logger = logging.getLogger(__name__)

def load_data():
    logger.info("Iniciando carregamento...")
    try:
        df = load_parquet_safe(settings.paths.companies_agg)
        logger.info(f"✅ Dados carregados: {len(df)} linhas")
        return df
    except Exception as e:
        logger.error(f"❌ Falha ao carregar: {e}")
        return None


# ❌ RUIM: Usar print() para debug
def load_data():
    print("Loading data...")
    df = load_parquet_safe(settings.paths.companies_agg)
    print(f"Loaded: {len(df)} rows")


# ======================================================
# CONFIGURAÇÕES
# ======================================================

# ✅ BOM: Usar settings centralizados
def get_processed_files():
    files = [
        settings.paths.companies_agg,
        settings.paths.opportunity_scores,
        settings.paths.brazil_states_geojson,
    ]
    return files


# ❌ RUIM: Hardcoding de caminhos
def get_processed_files():
    files = [
        Path("data/processed/companies_agg.parquet"),
        Path("data/processed/opportunity_scores.parquet"),
        Path("data/geo/brazil_states.geojson"),
    ]
    return files


# ======================================================
# VALIDAÇÃO DE DADOS
# ======================================================

# ✅ BOM: Validar inputs
import pandas as pd

def prep_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepara dataset com validação."""
    if df is None or df.empty:
        logger.warning("DataFrame vazio")
        return pd.DataFrame()

    required_cols = ["year", "state", "value"]
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Colunas faltando: {required_cols}")
        raise ValueError("Colunas obrigatórias faltam")

    logger.info(f"Dataset válido: {len(df)} linhas")
    return df


# ❌ RUIM: Sem validação
def prep_data(df):
    return df[["year", "state", "value"]]  # Pode quebrar se coluna não existir


# ======================================================
# CONSTANTES E MÁGICOS
# ======================================================

# ✅ BOM: Constantes em src/config/constants.py
from src.config import MACRO_SECTORS, UF_ORDER

macro = MACRO_SECTORS[0]  # "Agronegócio"
uf = UF_ORDER[0]  # "AC"


# ❌ RUIM: Magic numbers e strings
def filter_states(df):
    ufs = ["SP", "RJ", "MG", "BA", "SC"]  # Magic list
    return df[df["uf"].isin(ufs)]


# ======================================================
# COMPONENTES STREAMLIT
# ======================================================

# ✅ BOM: Usar componentes reutilizáveis
import streamlit as st
from src.ui import render_kpi, apply_styles

apply_styles()
render_kpi("Total", "1.234.567", "Saldo de empresas")


# ❌ RUIM: CSS inline repetido
st.markdown("""
<div class="kpi">
  <div class="label">Total</div>
  <div class="value">1.234.567</div>
</div>
""", unsafe_allow_html=True)


# ======================================================
# NOMEAÇÃO DE VARIÁVEIS
# ======================================================

# ✅ BOM: Nomes descritivos
total_companies_by_state = df.groupby("uf")["value"].sum()
top_hiring_states = total_companies_by_state.nlargest(5)


# ❌ RUIM: Nomes genéricos
t = df.groupby("uf")["value"].sum()
x = t.nlargest(5)


# ======================================================
# ERROR HANDLING
# ======================================================

# ✅ BOM: Tratamento específico
def safe_divide(numerator: float, denominator: float) -> float:
    """Divide com tratamento de divisão por zero."""
    try:
        return numerator / denominator
    except ZeroDivisionError:
        logger.warning("Divisão por zero evitada")
        return 0.0


# ❌ RUIM: Catch genérico
def safe_divide(numerator, denominator):
    try:
        return numerator / denominator
    except:
        return 0


# ======================================================
# TESTING
# ======================================================

# ✅ BOM: Escrever testes (em tests/test_formatters.py)
import pytest

def test_fmt_int():
    from src.utils import fmt_int
    assert fmt_int(1234567) == "1.234.567"
    assert fmt_int(0) == "0"
    assert fmt_int("invalid") == "invalid"


# ======================================================
# DOCUMENTAÇÃO
# ======================================================

# ✅ BOM: Adicionar docstrings em todos os módulos
"""
src/core/data_processing.py - Processamento e transformação de dados

Este módulo contém funções para:
- Preparar datasets IBGE, CAGED e scores
- Aplicar filtros
- Validar estrutura de dados

Exemplo:
    >>> df = load_parquet_safe(settings.paths.companies_agg)
    >>> df = prep_companies(df)
    >>> df_filtered = apply_filters(df, state="SP", year=2024)
"""


# ======================================================
# CHECKLIST ANTES DE COMMIT
# ======================================================
"""
☐ Type hints em 100% do código novo
☐ Docstrings em módulos, funções complexas
☐ Logging em pontos críticos (início, fim, erros)
☐ Sem hardcoding de caminhos (usar settings)
☐ Sem magic numbers (usar constantes)
☐ Tratamento de erro específico (não catch genérico)
☐ Teste a função antes de commit
☐ Code style (black, isort)
☐ Sem print() - usar logger
☐ Sem import * - imports explícitos
"""
