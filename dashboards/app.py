"""
Painel B2B Brasil  Aplicação Streamlit Principal
Refatorado para modularidade, logging e manutenibilidade
"""

import json
import logging
import os
import sys
from pathlib import Path

# Adicionar diretório pai ao path para importações
project_root = Path(__file__).parent.parent.resolve()

# Defensive initialization for all main variables to avoid NameError
df_companies = None
df_scores = None
df_caged = None
geo_states = None
centroids = {}

print(">>> APP STARTED")
sys.path.insert(0, str(project_root))

# Opcional: manter CWD no root do projeto
os.chdir(project_root)



import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import I18N, MACRO_SECTORS, UF_ORDER, Settings
from src.core.data_processing import (
    apply_filters,
    build_gold_join,
    prep_caged,
    prep_companies,
    prep_scores,
)
from src.ui.components import apply_styles, render_kpi, render_pills
from src.ui.pnad_section import render_pnad_section
from src.utils.data_loading import (
    load_caged_state_sector_year,
    load_companies_agg,
    load_geojson_safe,
    load_opportunity_scores,
    load_pnad_metrics,
    load_rais_metrics,
)
from src.utils.duckdb_client import get_con
from src.utils.formatters import fmt_int
from src.utils.logging_config import get_logger, setup_logging


def load_geo_states():
    try:
        settings_local = Settings()
        candidates = [
            settings_local.paths.brazil_states_geojson,
            Path(__file__).resolve().parents[1] / "assets" / "geo" / "brazil_states.geojson",
            Path(__file__).resolve().parents[1] / "assets" / "geo" / "br_states.geojson",
        ]
        for geo_path in candidates:
            if geo_path and geo_path.exists():
                return load_geojson_safe(geo_path)
    except Exception:
        pass
    return None

# ======================================================
# SETUP
# ======================================================
settings = Settings()
setup_logging(log_level=settings.log_level)
logger = get_logger(__name__)

st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout=settings.layout,
)

st.title("✅ Streamlit App Loaded")
st.write("If you can see this, the app is rendering.")

apply_styles()
logger.info(f"App iniciado | Debug: {settings.debug_mode}")

# ======================================================
# SESSION STATE INITIALIZATION
# ======================================================
if "source_fallback_done" not in st.session_state:
    st.session_state.source_fallback_done = False
    st.session_state.effective_source = None

# ======================================================
# BACKEND SELECTION
# ======================================================
backend_default = settings.backend_default if settings.backend_default in ["duckdb", "bigquery"] else "duckdb"
backend_id = st.sidebar.radio(
    "Fonte de backend",
    ["duckdb", "bigquery"],
    index=0 if backend_default == "duckdb" else 1,
    format_func=lambda x: "Local (DuckDB)" if x == "duckdb" else "BigQuery",
)

# ======================================================
# LOAD DATA
# ======================================================

@st.cache_data(show_spinner=False)
def load_all_data(backend: str):
    """
    Carrega os dados principais a partir do DuckDB e o geojson.
    """
    logger.info("Carregando datasets via DuckDB...")
    try:
        df_companies = load_companies_agg(backend=backend)
    except Exception as e:
        logger.error(f"Erro ao carregar companies_agg ({backend}): {e}")
        df_companies = None
    try:
        df_scores = load_opportunity_scores(backend=backend)
    except Exception as e:
        logger.error(f"Erro ao carregar opportunity_scores ({backend}): {e}")
        df_scores = None
    try:
        df_caged = load_caged_state_sector_year(backend=backend)
    except Exception as e:
        logger.error(f"Erro ao carregar caged_state_sector_year ({backend}): {e}")
        df_caged = None
    try:
        df_pnad_metrics = load_pnad_metrics(backend=backend)
    except Exception as e:
        logger.error(f"Erro ao carregar PNAD metrics ({backend}): {e}")
        df_pnad_metrics = None
    try:
        df_rais_metrics = load_rais_metrics(backend=backend)
    except Exception as e:
        logger.error(f"Erro ao carregar RAIS metrics ({backend}): {e}")
        df_rais_metrics = None
    geo_states = load_geo_states()

    # Preparar dados - SÓ se carregou com sucesso
    if df_companies is not None and not df_companies.empty:
        try:
            df_companies = prep_companies(df_companies)
            logger.info(f"prep_companies OK: {len(df_companies)} linhas")
        except Exception as e:
            logger.error(f"Erro em prep_companies: {e}")
            df_companies = None

    if df_scores is not None and not df_scores.empty:
        try:
            df_scores = prep_scores(df_scores)
            logger.info(f"prep_scores OK: {len(df_scores)} linhas")
        except Exception as e:
            logger.error(f"Erro em prep_scores: {e}")
            df_scores = None

    if df_caged is not None and not df_caged.empty:
        try:
            df_caged = prep_caged(df_caged)
            logger.info(f"prep_caged OK: {len(df_caged)} linhas")
        except Exception as e:
            logger.error(f"Erro em prep_caged: {e}")
            df_caged = None

    logger.info("Todos os dados carregados com sucesso (DuckDB)")
    return df_companies, df_scores, df_caged, geo_states, df_pnad_metrics, df_rais_metrics



# Carregar dados principais via DuckDB

try:
    df_companies, df_scores, df_caged, geo_states, df_pnad_metrics, df_rais_metrics = load_all_data(backend=backend_id)
except Exception as e:
    st.error(f"Falha ao carregar dados: {type(e).__name__} - {e}")
    logger.error(f"Falha crítica ao carregar dados: {e}")
    df_companies = None
    df_scores = None
    df_caged = None
    geo_states = None
    df_pnad_metrics = None
    df_rais_metrics = None
    # NÃO parar - deixar app continuar renderizando

# Fallback para DuckDB se BigQuery falhar
if backend_id == "bigquery":
    if (
        (df_companies is None or df_companies.empty)
        and (df_scores is None or df_scores.empty)
        and (df_caged is None or df_caged.empty)
    ):
        st.error("Backend BigQuery indisponível. Verifique credenciais/tabelas e tente novamente. Usando DuckDB.")
        df_companies, df_scores, df_caged, geo_states, df_pnad_metrics, df_rais_metrics = load_all_data(backend="duckdb")
        backend_id = "duckdb"

# Defensive: ensure all variables are defined before use
if df_companies is None:
    df_companies = pd.DataFrame()
if df_scores is None:
    df_scores = pd.DataFrame()
if df_caged is None:
    df_caged = pd.DataFrame()
if geo_states is None:
    geo_states = None
if df_pnad_metrics is None:
    df_pnad_metrics = pd.DataFrame()
if df_rais_metrics is None:
    df_rais_metrics = pd.DataFrame()

# Visão integrada (gold)
df_gold = build_gold_join(df_companies, df_caged, df_rais_metrics, df_pnad_metrics)
if df_gold is not None and not df_gold.empty and df_scores is not None and not df_scores.empty:
    if "year" in df_scores.columns and "uf" in df_scores.columns and "opportunity_score" in df_scores.columns:
        scores_tmp = df_scores.copy()
        if "units" in scores_tmp.columns:
            scores_tmp["_w"] = scores_tmp["opportunity_score"] * scores_tmp["units"]
            scores_agg = (
                scores_tmp.groupby(["year", "uf"], as_index=False)
                .agg(weighted=("_w", "sum"), units=("units", "sum"))
            )
            scores_agg = scores_agg[scores_agg["units"] > 0].copy()
            scores_agg["opportunity_score"] = scores_agg["weighted"] / scores_agg["units"]
            scores_agg = scores_agg[["year", "uf", "opportunity_score"]]
        else:
            scores_agg = scores_tmp.groupby(["year", "uf"], as_index=False)[["opportunity_score"]].mean()
        df_gold = df_gold.merge(scores_agg, on=["year", "uf"], how="left")


# Validar dados críticos (apenas alerta; não substitui o try/except acima)
missing_files = settings.ensure_data_files_exist()
if missing_files:
    logger.warning(f"Arquivos faltando: {missing_files}")

# ======================================================
# DEBUG BLOCK - Data Loading Status
# ======================================================
if settings.debug_mode:
    st.sidebar.markdown("### 🔍 DEBUG INFO")
    debug_col1, debug_col2 = st.sidebar.columns(2)
    
    with debug_col1:
        st.write("📊 **Data Shapes:**")
        companies_shape = df_companies.shape if df_companies is not None else (0, 0)
        caged_shape = df_caged.shape if df_caged is not None else (0, 0)
        scores_shape = df_scores.shape if df_scores is not None else (0, 0)
        
        st.caption(f"Companies: {companies_shape}")
        st.caption(f"CAGED: {caged_shape}")
        st.caption(f"Scores: {scores_shape}")
    
    with debug_col2:
        st.write("📁 **Paths:**")
        st.caption(f"companies_agg.parquet")
        st.caption(f"path: {settings.paths.companies_agg}")
        st.caption(f"exists: {settings.paths.companies_agg.exists()}")


# ======================================================
# HELPERS
# ======================================================
def geojson_state_centroids(geo: dict) -> dict:
    """Calcula centróides por UF para posicionar labels no mapa."""
    centroids = {}
    if not geo or "features" not in geo:
        return centroids

    for feat in geo["features"]:
        props = feat.get("properties", {})
        uf = props.get("sigla")
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [])
        gtype = geom.get("type")

        xs, ys = [], []

        def add_points(ring):
            for pt in ring:
                if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                    xs.append(pt[0])
                    ys.append(pt[1])

        try:
            if gtype == "Polygon":
                for ring in coords:
                    add_points(ring)
            elif gtype == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        add_points(ring)
        except Exception as e:
            logger.debug(f"Erro ao extrair centróide de {uf}: {e}")

        if uf and xs and ys:
            centroids[uf] = (sum(xs) / len(xs), sum(ys) / len(ys))

    return centroids


centroids = geojson_state_centroids(geo_states) if geo_states else {}


# ======================================================
# SIDEBAR CONTROLS
# ======================================================
st.sidebar.markdown("##  CONTROLES")

# Idioma
lang = st.sidebar.selectbox(
    "Idioma",
    [I18N["pt"]["pt_opt"], I18N["en"]["en"]],
    index=0,
)
LANG = "pt" if "Portugu" in lang else "en"
T = I18N[LANG]

# Fonte de dados (IDs fixos)
source_id = st.sidebar.radio(
    T["source"],
    ["companies", "jobs"],
    index=0,
    format_func=lambda x: T["companies"] if x == "companies" else T["jobs"],
)

# Filtros
uf_selected = st.sidebar.selectbox(
    T["uf"],
    ["ALL"] + UF_ORDER,
    index=0,
    format_func=lambda x: T["macro_all"] if x == "ALL" else x,
)

st.sidebar.caption(T["note_macro"])
macro_selected = st.sidebar.selectbox(
    T["macro"],
    ["ALL"] + MACRO_SECTORS,
    index=0,
    format_func=lambda x: T["macro_all"] if x == "ALL" else x,
)

only_tech = st.sidebar.toggle(T["tech_only"], value=False)
show_raw = st.sidebar.toggle(T["debug"], value=False)

st.sidebar.divider()

# ======================================================
# DATASET AVAILABILITY CHECK - NO FATAL ERRORS
# ======================================================
# Determinar se datasets estão realmente disponíveis (baseado em dados carregados, não em filtros)
companies_available = df_companies is not None and not df_companies.empty
caged_available = df_caged is not None and not df_caged.empty
gold_available = df_gold is not None and not df_gold.empty

# Log para debug
logger.info(f"Dataset availability: companies={companies_available}, caged={caged_available}")

# ======================================================
# DETERMINE EFFECTIVE DATA SOURCE - GRACEFUL FALLBACK
# ======================================================
# Determinar qual dataset realmente usar (sem parar a aplicação)
effective_source = source_id
df_main = None
value_col = "net"
value_label = T["indicator_companies"]
source_name = "Nenhuma fonte"

# Se usuário selecionou Companies
if source_id == "companies":
    if companies_available:
        # Companies disponível - usar
        df_main = df_gold if gold_available else df_companies
        value_col = "net"
        value_label = T["indicator_companies"]
        source_name = "IBGE Empresas"
    elif caged_available:
        # Companies não disponível mas CAGED está - usar CAGED
        effective_source = "jobs"
        df_main = df_caged
        value_col = "job_balance"
        value_label = T["indicator_jobs"]
        source_name = "CAGED Empregos"
        st.warning("⚠️ Dataset de empresas não disponível. Usando Empregos (CAGED).")
        logger.warning("Companies não disponível, usando CAGED como fallback")
    else:
        # Nenhum disponível
        st.info("ℹ️ Datasets de empresas e empregos não estão disponíveis no momento.")
        logger.warning("Ambos os datasets indisponíveis - renderizando com dados vazios")

# Se usuário selecionou CAGED
elif source_id == "jobs":
    if caged_available:
        # CAGED disponível - usar
        df_main = df_gold if gold_available else df_caged
        value_col = "job_balance"
        value_label = T["indicator_jobs"]
        source_name = "CAGED Empregos"
    elif companies_available:
        # CAGED não disponível mas Companies está - usar Companies
        effective_source = "companies"
        df_main = df_companies
        value_col = "net"
        value_label = T["indicator_companies"]
        source_name = "IBGE Empresas"
        st.warning("⚠️ Dataset de empregos não disponível. Usando Empresas (IBGE).")
        logger.warning("CAGED não disponível, usando Companies como fallback")
    else:
        # Nenhum disponível
        st.info("ℹ️ Datasets de empresas e empregos não estão disponíveis no momento.")
        logger.warning("Ambos os datasets indisponíveis - renderizando com dados vazios")

# Se temos algum dataset, continuar com os filtros
if not isinstance(df_main, pd.DataFrame) or df_main.empty:
    year_selected = 2021  # valor padrão
    df_main = pd.DataFrame()
    df_view = pd.DataFrame()
    logger.warning("Nenhum dataset disponível - usando DataFrames vazios")
    st.sidebar.info("ℹ️ Nenhum dataset disponível para renderizar controles dinâmicos.")
else:
    # Ano
    years = sorted(df_main["year"].dropna().astype(int).unique().tolist())
    default_year_idx = len(years) - 1  # padrão: último ano
    if source_id == "companies" and 2021 in years:
        default_year_idx = years.index(2021)
    # Para CAGED, sempre último ano (default já é esse)
    year_selected = st.sidebar.selectbox(T["year"], years, index=default_year_idx)

    # Aplicar filtros
    df_view = apply_filters(
        df_main,
        year=int(year_selected),
        state=None if uf_selected == "ALL" else uf_selected,
        macro_sector=None if macro_selected == "ALL" else macro_selected,
        tech_only=only_tech,
    )

    # Se filtros resultaram em zero linhas, mostrar aviso mas continuar renderizando
    if df_view.empty and not df_main.empty:
        st.info(f"ℹ️ Nenhum dado disponível para os filtros selecionados. Tente ajustar os filtros.")
        logger.info(f"Filtros resultaram em dataset vazio (mas dados base existem)")

    logger.info(f"Fonte: {source_name} | Filtros: year={year_selected}, uf={uf_selected}, macro={macro_selected} | {len(df_view)} linhas")

# ======================================================
# HEADER
# ======================================================
st.markdown(f"<h1 class='title-up'> {T['title']}</h1>", unsafe_allow_html=True)
st.markdown(f"<div class='subtitle'>{T['subtitle']}</div>", unsafe_allow_html=True)
st.divider()

# ======================================================
# KPIs
# ======================================================
total_value = float(df_view[value_col].sum()) if not df_view.empty else 0.0

top_uf = ""
top_macro = ""

if not df_view.empty:
    by_uf = (
        df_view.groupby("uf", as_index=False)[value_col]
        .sum()
        .sort_values(value_col, ascending=False)
    )
    by_macro = (
        df_view.groupby("macro_sector", as_index=False)[value_col]
        .sum()
        .sort_values(value_col, ascending=False)
    )
    if len(by_uf):
        top_uf = by_uf.iloc[0]["uf"]
    if len(by_macro):
        top_macro = by_macro.iloc[0]["macro_sector"]

c1, c2, c3, c4 = st.columns(4)

with c1:
    render_kpi(
        T["kpi_source"],
        "IBGE" if source_id == "companies" else "CAGED",
        f"{T['year']}: {int(year_selected)}",
    )

with c2:
    render_kpi(
        T["kpi_indicator"],
        fmt_int(total_value),
        value_label,
    )

with c3:
    render_kpi(
        T["kpi_top_uf"],
        top_uf,
        "UF no recorte atual",
    )

with c4:
    render_kpi(
        T["kpi_top_macro"],
        top_macro,
        "Macro-setor líder",
    )

# Pills
render_pills({
    T["year"]: int(year_selected),
    T["uf"]: uf_selected,
    T["macro"]: macro_selected,
    "TECH": "SIM" if only_tech else "NÃO",
})

st.divider()

# ======================================================
# TABS
# ======================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(T["tabs"])

# -------------------------
# TAB 1  TIME SERIES
# -------------------------
with tab1:
    st.subheader(T["time_series"])

    base = apply_filters(
        df_main,
        state=None if uf_selected == "ALL" else uf_selected,
        macro_sector=None if macro_selected == "ALL" else macro_selected,
        tech_only=only_tech,
    )

    if base.empty:
        st.info(T["no_data"])
    else:
        series = (
            base.groupby("year", as_index=False)[value_col]
            .sum()
            .sort_values("year")
        )
        fig = px.line(
            series,
            x="year",
            y=value_col,
            markers=True,
            labels={"year": T["year"], value_col: value_label},
        )
        fig.update_layout(
            template="plotly_dark",
            height=360,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

# -------------------------
# TAB 2  MACRO RANKING
# -------------------------
with tab2:
    st.subheader(T["ranking_macro"])

    if df_view.empty:
        st.info(T["no_data"])
    else:
        by_macro = (
            df_view.groupby("macro_sector", as_index=False)[value_col]
            .sum()
            .sort_values(value_col, ascending=False)
        )
        fig = px.bar(
            by_macro,
            x="macro_sector",
            y=value_col,
            text_auto=True,
            labels={"macro_sector": T["macro"], value_col: value_label},
        )
        fig.update_layout(
            template="plotly_dark",
            height=420,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Tabela (ordenada)**")
        st.dataframe(by_macro, use_container_width=True, height=280)

# -------------------------
# TAB 3  INTEGRATED VIEW
# -------------------------
with tab3:
    st.subheader(" " + T["tabs"][2])

    if df_gold is None or df_gold.empty:
        st.info("Visão integrada indisponível. Verifique as bases carregadas.")
    else:
        gold_view = apply_filters(
            df_gold,
            year=int(year_selected) if "year_selected" in locals() else None,
            state=None if uf_selected == "ALL" else uf_selected,
            macro_sector=None if macro_selected == "ALL" else macro_selected,
            tech_only=only_tech,
        )

        if gold_view.empty:
            st.info(T["no_data"])
        else:
            cols = ["uf", "macro_sector"]
            metrics = []
            for c in ["opportunity_score", "net", "job_balance", "vinculos"]:
                if c in gold_view.columns:
                    metrics.append(c)
            if not metrics:
                st.info("Nenhuma métrica integrada disponível para este recorte.")
            else:
                by_uf = gold_view.groupby("uf", as_index=False)[metrics].sum(numeric_only=True)
                by_macro = gold_view.groupby("macro_sector", as_index=False)[metrics].sum(numeric_only=True)

                left, right = st.columns(2)
                with left:
                    st.markdown("**Ranking por UF (integrado)**")
                    st.dataframe(by_uf.sort_values(metrics[0], ascending=False), use_container_width=True, height=360)
                with right:
                    st.markdown("**Ranking por Macro-setor (integrado)**")
                    st.dataframe(by_macro.sort_values(metrics[0], ascending=False), use_container_width=True, height=360)

            if "vinculos" not in gold_view.columns:
                st.info("RAIS não disponível para este recorte.")
            if "taxa_informalidade" not in gold_view.columns and "taxa_desemprego" not in gold_view.columns:
                st.info("PNAD não carregada no backend selecionado.")

# -------------------------
# TAB 4  MAP & RANKINGS
# -------------------------
with tab4:
    st.subheader(" " + T["map_structural"])

    if df_scores is None or df_scores.empty or geo_states is None:
        st.warning(
            "Mapa indisponível: verifique opportunity_scores.parquet e brazil_states.geojson"
        )
    else:
        scores_2021 = df_scores.copy()
        if "year" in scores_2021.columns:
            scores_2021 = scores_2021[scores_2021["year"] == 2021].copy()

        scores_2021["_w"] = (scores_2021["opportunity_score"] * scores_2021["units"])
        state_score = (
            scores_2021.groupby("uf", as_index=False)
            .agg(weighted=("_w", "sum"), units=("units", "sum"), region=("region", "first"))
        )
        state_score = state_score[state_score["units"] > 0].copy()
        state_score["score"] = (state_score["weighted"] / state_score["units"])
        state_score = state_score[["uf", "score", "region"]].copy()
        # Normaliza UF para casar com properties.sigla do GeoJSON (ex.: SP, CE)
        if "UF_CODE_MAP" in globals() and isinstance(UF_CODE_MAP, dict):
            uf_num = pd.to_numeric(state_score["uf"], errors="coerce")
            uf_mapped = uf_num.map(lambda x: UF_CODE_MAP.get(int(x)) if pd.notna(x) else None)
            state_score["uf"] = uf_mapped.where(uf_mapped.notna(), state_score["uf"])
        state_score["uf"] = state_score["uf"].astype(str).str.strip().str.upper()

        show_rank = st.toggle(T["map_toggle_rank"], value=True)

        # Garante casamento robusto entre dados e GeoJSON (sigla ou id numérico)
        geo_props = [f.get("properties", {}) for f in geo_states.get("features", [])]
        geo_siglas = {
            str(p.get("sigla")).strip().upper()
            for p in geo_props
            if p.get("sigla") is not None
        }
        uf_to_geo_id = {
            str(p.get("sigla")).strip().upper(): p.get("id")
            for p in geo_props
            if p.get("sigla") is not None and p.get("id") is not None
        }

        match_sigla = state_score["uf"].isin(geo_siglas).sum()
        if match_sigla > 0:
            locations_col = "uf"
            feature_key = "properties.sigla"
        else:
            state_score["geo_id"] = state_score["uf"].map(uf_to_geo_id)
            state_score = state_score[state_score["geo_id"].notna()].copy()
            locations_col = "geo_id"
            feature_key = "properties.id"

        fig_map = go.Figure(
            go.Choropleth(
                geojson=geo_states,
                locations=state_score[locations_col],
                z=state_score["score"],
                featureidkey=feature_key,
                colorscale="Blues",
                colorbar=dict(
                    title=f"{T['map_col_index']}<br>",
                    thickness=12,
                    len=0.70,
                    tickformat=".1f",
                    tickfont=dict(size=10),
                ),
                marker_line_width=0.8,
                marker_line_color="rgba(255,255,255,0.75)",
                customdata=state_score[["score"]].values,
                hovertemplate=f"<b>%{{location}}</b><br>{T['map_col_index']}: %{{customdata[0]:.1f}}<extra></extra>",
            )
        )
        fig_map.update_geos(
            fitbounds="geojson",
            visible=True,
            bgcolor="rgba(255,255,255,0)",
            projection_type="mercator",
            showland=True,
            landcolor="rgba(245,247,250,1)",
            coastlinecolor="rgba(160,174,192,0.7)",
            showframe=False,
        )

        # Labels de UF
        lons, lats, texts = [], [], []
        for uf in state_score["uf"].tolist():
            if uf in centroids:
                lon, lat = centroids[uf]
                lons.append(lon)
                lats.append(lat)
                texts.append(uf)

        fig_map.add_trace(
            go.Scattergeo(
                lon=lons,
                lat=lats,
                text=texts,
                mode="text",
                textfont=dict(size=14, color="#0f172a", family="Arial Black"),
                textposition="middle center",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        fig_map.update_layout(
            template="plotly_white",
            height=680,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            font=dict(family="Arial", size=11),
            paper_bgcolor="rgba(255,255,255,1)",
            plot_bgcolor="rgba(255,255,255,1)",
        )

        rank = state_score.sort_values("score", ascending=False).reset_index(drop=True)
        rank["rank"] = rank.index + 1
        rank["score"] = rank["score"].round(2)
        rank = rank[["rank", "uf", "region", "score"]].copy()
        rank.columns = [T["map_col_rank"], T["map_col_state"], T["map_col_region"], T["map_col_index"]]

        if show_rank:
            left, right = st.columns([1.25, 0.75], gap="large")
            with left:
                st.plotly_chart(fig_map, use_container_width=True)
            with right:
                st.markdown(
                    f"**{T['map_title']}**\n\n"
                    f"<small>{T['map_description']}</small>",
                    unsafe_allow_html=True
                )
                st.divider()
                st.dataframe(
                    rank.style.format({T["map_col_index"]: "{:.2f}"}),
                    use_container_width=True,
                    height=580
                )
        else:
            st.plotly_chart(fig_map, use_container_width=True)

    st.divider()

    st.subheader(" " + T["map_story"])
    if df_view.empty:
        st.info(T["no_data"])
    else:
        top_states = (
            df_view.groupby("uf", as_index=False)[value_col]
            .sum()
            .sort_values(value_col, ascending=False)
            .head(6)
        )

        colA, colB = st.columns([1, 1], gap="large")

        with colA:
            st.markdown("**" + T["top_hiring_states"] + "**")
            fig_states = px.bar(
                top_states,
                x="uf",
                y=value_col,
                text_auto=True,
                labels={"uf": T["uf"], value_col: value_label},
            )
            fig_states.update_layout(
                template="plotly_dark",
                height=360,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig_states, use_container_width=True)

        with colB:
            st.markdown("**" + T["top_sectors_in_top_states"] + "**")
            rows = []
            for uf in top_states["uf"].tolist():
                duf = df_view[df_view["uf"] == uf].copy()
                bym = (
                    duf.groupby("macro_sector", as_index=False)[value_col]
                    .sum()
                    .sort_values(value_col, ascending=False)
                )
                if not bym.empty:
                    rows.append(
                        {
                            "uf": uf,
                            "macro_lider": bym.iloc[0]["macro_sector"],
                            "valor": float(bym.iloc[0][value_col]),
                        }
                    )
            story = pd.DataFrame(rows)
            if story.empty:
                st.write("")
            else:
                story["valor"] = story["valor"].apply(fmt_int)
                st.dataframe(story, use_container_width=True, height=360)

        top_uf_list = top_states["uf"].tolist()
        top_macro_slice = (
            df_view.groupby("macro_sector", as_index=False)[value_col]
            .sum()
            .sort_values(value_col, ascending=False)
            .head(3)
        )
        macros = top_macro_slice["macro_sector"].tolist()

        st.markdown("#### " + T["insight"])
        st.markdown(
            f"""
- **{T['year']}:** {int(year_selected)}
- **{T['uf']}:** {uf_selected}
- **{T['macro']}:** {macro_selected}
- **{value_label}:** **{fmt_int(total_value)}**
- **Top UFs:** {", ".join(top_uf_list)}
- **Top Setores:** {", ".join(macros)}
""".strip()
        )

# -------------------------
# TAB 5  PNAD
# -------------------------
with tab5:
    render_pnad_section(lang=LANG)

# -------------------------
# TAB 6  DATA & DIAGNOSTICS
# -------------------------
with tab6:
    st.subheader(" " + T["data_diag"])

    st.code(
        "\n".join(
            [
                f"PROJECT_ROOT: {settings.paths.root}",
                f"BACKEND: {backend_id}",
                f"companies_agg: {settings.paths.companies_agg} | exists={settings.paths.companies_agg.exists()}",
                f"opportunity_scores: {settings.paths.opportunity_scores} | exists={settings.paths.opportunity_scores.exists()}",
                f"caged_state_sector_year: {settings.paths.caged_state_sector_year} | exists={settings.paths.caged_state_sector_year.exists()}",
                f"brazil_states.geojson: {settings.paths.brazil_states_geojson} | exists={settings.paths.brazil_states_geojson.exists()}",
                f"Python: {sys.executable}",
                f"CWD: {os.getcwd()}",
            ]
        )
    )

    if backend_id == "bigquery":
        from src.utils.bigquery_client import check_tables
        if not settings.bq_project or not settings.bq_dataset_gold:
            st.warning("BigQuery não configurado. Defina BQ_PROJECT e BQ_DATASET_GOLD.")
        else:
            expected_tables = [
                settings.bq_table_companies,
                settings.bq_table_opportunity,
                settings.bq_table_caged,
                settings.bq_table_pnad_metrics,
                settings.bq_table_rais_metrics,
            ]
            status = check_tables(
                project=settings.bq_project,
                dataset=settings.bq_dataset_gold,
                table_names=expected_tables,
                location=settings.bq_location,
            )
            st.markdown("**BigQuery status**")
            st.json(status)

    cA, cB, cC = st.columns(3)


    with cA:
        if df_companies is not None and not df_companies.empty:
            st.write("IBGE companies:", df_companies.shape)
            if "year" in df_companies.columns:
                st.write("years:", sorted(df_companies["year"].dropna().astype(int).unique().tolist())[:25])
            else:
                st.write("years:", "N/A")
            if "uf" in df_companies.columns:
                st.write("ufs:", df_companies["uf"].nunique())
            else:
                st.write("ufs:", "N/A")
        else:
            st.write("IBGE companies:", "(Não disponível)")


    with cB:
        if df_caged is not None and not df_caged.empty:
            st.write("CAGED:", df_caged.shape)
            if "year" in df_caged.columns:
                st.write("years:", sorted(df_caged["year"].dropna().astype(int).unique().tolist()))
            else:
                st.write("years:", "N/A")
            if "uf" in df_caged.columns:
                st.write("ufs:", df_caged["uf"].nunique())
            else:
                st.write("ufs:", "N/A")
        else:
            st.write("CAGED:", "(Não disponível)")


    with cC:
        if df_scores is not None and not df_scores.empty:
            st.write("Índice estrutural:", df_scores.shape)
            if "year" in df_scores.columns:
                st.write("years:", sorted(df_scores["year"].dropna().astype(int).unique().tolist())[:25])
            else:
                st.write("years:", "N/A")
            if "uf" in df_scores.columns:
                st.write("ufs:", df_scores["uf"].nunique())
            else:
                st.write("ufs:", "N/A")
        else:
            st.write("Índice estrutural:", "(Não disponível)")

    st.divider()

    if show_raw:
        st.markdown("**Tabela do recorte atual**")
        st.dataframe(df_view, use_container_width=True, height=520)


logger.info("App renderizado com sucesso")
