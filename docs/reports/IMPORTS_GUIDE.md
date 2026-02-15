"""
Guia de Imports - B2B Dashboard v2.0

Exemplos corretos de como importar de cada módulo centralizado.
"""

# ======================================================
# IMPORTAR CONFIGURAÇÕES
# ======================================================

# ✅ Recomendado
from src.config import settings, I18N, UF_ORDER, MACRO_SECTORS

# Acessar paths
company_file = settings.paths.companies_agg
config_root = settings.paths.root

# Acessar constantes
macro_sectors = MACRO_SECTORS  # ["Agronegócio", "Indústria", ...]
lang_pt = I18N["pt"]
ufs = UF_ORDER  # ["AC", "AL", ...]

# Validar dados críticos
missing = settings.ensure_data_files_exist()


# ======================================================
# IMPORTAR UTILITÁRIOS
# ======================================================

# ✅ Para formatação e normalização
from src.utils import (
    fmt_int,
    normalize_uf,
    clean_label,
    macro_sector_from_label,
)

# Exemplo
valor_formatado = fmt_int(1234567)  # "1.234.567"
uf_normalizado = normalize_uf("são paulo")  # "SP"

# ✅ Para carregamento de dados
from src.utils import (
    load_parquet_safe,
    load_geojson_safe,
    validate_dataframe,
)

# Exemplo
df = load_parquet_safe(settings.paths.companies_agg)
geo = load_geojson_safe(settings.paths.brazil_states_geojson)

# ✅ Para logging
from src.utils import setup_logging, get_logger

setup_logging(log_level="INFO")
logger = get_logger(__name__)
logger.info("Iniciando carregamento...")


# ======================================================
# IMPORTAR PROCESSAMENTO DE DADOS
# ======================================================

# ✅ Para preparar dados
from src.core import (
    prep_companies,
    prep_scores,
    prep_caged,
    apply_filters,
)

# Exemplo
df_raw = load_parquet_safe(settings.paths.companies_agg)
df_clean = prep_companies(df_raw)
df_filtered = apply_filters(
    df_clean,
    year=2024,
    state="SP",
    macro_sector="Tecnologia",
    tech_only=False,
)


# ======================================================
# IMPORTAR COMPONENTES UI
# ======================================================

# ✅ Para renderização e estilos
from src.ui import (
    apply_styles,
    render_kpi,
    render_pills,
    render_diagnostic_info,
)

import streamlit as st

# Aplicar estilos (UMA VEZ no início)
apply_styles()

# Renderizar KPI
render_kpi(
    label="Total Empresas",
    value="1.234.567",
    hint="Saldo 2024"
)

# Renderizar pills
render_pills({
    "Ano": 2024,
    "Estado": "SP",
    "Setor": "Tecnologia"
})


# ======================================================
# EXEMPLO COMPLETO: NOVO SCRIPT/MÓDULO
# ======================================================

import logging
import pandas as pd
import streamlit as st

# Imports centralizados
from src.config import settings, MACRO_SECTORS
from src.utils import setup_logging, get_logger, load_parquet_safe, fmt_int
from src.core import prep_companies, apply_filters
from src.ui import apply_styles, render_kpi

# ======================================================
# SETUP
# ======================================================
setup_logging(log_level=settings.log_level)
logger = get_logger(__name__)

st.set_page_config(
    page_title="Meu Módulo",
    layout=settings.layout,
)
apply_styles()

# ======================================================
# LÓGICA
# ======================================================

logger.info("Iniciando módulo...")

# Carregar dados
df = load_parquet_safe(settings.paths.companies_agg)
if df is None:
    st.error("❌ Dados não encontrados")
    st.stop()

# Preparar
df = prep_companies(df)

# Filtrar
state = st.sidebar.selectbox("Estado", MACRO_SECTORS)
df_view = apply_filters(df, state=state)

# Mostrar
render_kpi("Total", fmt_int(df_view["value"].sum()), "Saldo")

logger.info("✅ Módulo renderizado")


# ======================================================
# ❌ NÃO FAZER ISTO
# ======================================================

# ❌ Hardcoding de caminhos
df = pd.read_parquet("data/processed/companies_agg.parquet")

# ❌ Imports desorganizados
from src.config.settings import *
from src.utils.formatters import *

# ❌ Print para debug (usar logger)
print("Debug info")
print(df.shape)

# ❌ Magic numbers
threshold = 0.8  # Usar constantes em src/config/constants.py

# ❌ Lógica duplicada
val = f"{int(x):,}".replace(",", ".")  # Usar fmt_int()

# ❌ Sem type hints
def process_data(df):
    return df


# ======================================================
# ✅ PADRÃO RECOMENDADO PARA NOVO ARQUIVO
# ======================================================

"""
novo_modulo.py - Descrição do que faz

Responsabilidades:
- Fazer X
- Fazer Y
- Fazer Z

Exemplo:
    >>> from novo_modulo import funcao
    >>> resultado = funcao(param)
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from src.config import settings
from src.utils import get_logger

logger = get_logger(__name__)


def minha_funcao(
    df: pd.DataFrame,
    state: Optional[str] = None,
) -> pd.DataFrame:
    """
    Descrição breve.

    Args:
        df: DataFrame de entrada
        state: Estado para filtrar (opcional)

    Returns:
        DataFrame processado

    Raises:
        ValueError: Se DataFrame vazio

    Example:
        >>> df = load_parquet_safe(settings.paths.companies_agg)
        >>> resultado = minha_funcao(df, state="SP")
    """
    if df.empty:
        logger.warning("DataFrame vazio recebido")
        raise ValueError("DataFrame não pode estar vazio")

    logger.info(f"Processando {len(df)} linhas...")

    if state:
        df = df[df["uf"] == state].copy()
        logger.debug(f"Filtrado para {len(df)} linhas (state={state})")

    logger.info("✅ Processamento concluído")
    return df
