"""
Painel B2B Brasil  Aplicação Streamlit Principal
Refatorado para modularidade, logging e manutenibilidade
"""

import logging
import sys
import os
from pathlib import Path

# Adicionar diretório pai ao path para importações
project_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(project_root))

# Opcional: manter CWD no root do projeto
os.chdir(project_root)

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Imports dos módulos centralizados
from src.config import Settings, I18N, UF_ORDER, MACRO_SECTORS
from src.utils.formatters import fmt_int
from src.utils.data_loading import load_parquet_safe, load_geojson_safe
from src.utils.logging_config import setup_logging, get_logger
from src.core.data_processing import prep_companies, prep_scores, prep_caged, apply_filters
from src.ui.components import apply_styles, render_kpi, render_pills
from src.ui.pnad_section import render_pnad_section

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

apply_styles()
logger.info(f"App iniciado | Debug: {settings.debug_mode}")

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(show_spinner=False)
def load_all_data(
    companies_path: str,
    scores_path: str,
    caged_path: str,
    geo_path: str,
):
    """Carrega datasets críticos (cacheado como dado)."""
    logger.info("Carregando datasets...")

    df_companies = load_parquet_safe(Path(companies_path))
    df_scores = load_parquet_safe(Path(scores_path))
    df_caged = load_parquet_safe(Path(caged_path))
    geo_states = load_geojson_safe(Path(geo_path))

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

    logger.info("Todos os dados carregados com sucesso")
    return df_companies, df_scores, df_caged, geo_states


# Carregar dados com tratamento de erro REAL (sem mascarar como "não encontrado")
try:
    df_companies, df_scores, df_caged, geo_states = load_all_data(
        str(settings.paths.companies_agg),
        str(settings.paths.opportunity_scores),
        str(settings.paths.caged_state_sector_year),
        str(settings.paths.brazil_states_geojson),
    )
except Exception as e:
    st.error(f"Falha ao carregar dados: {type(e).__name__} - {e}")
    st.stop()


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

# Fonte de dados
source = st.sidebar.radio(
    T["source"],
    [T["companies"], T["jobs"]],
    index=0,
)

# Filtros
uf_selected = st.sidebar.selectbox(
    T["uf"],
    [T["macro_all"]] + UF_ORDER,
    index=0,
)

st.sidebar.caption(T["note_macro"])
macro_selected = st.sidebar.selectbox(
    T["macro"],
    [T["macro_all"]] + MACRO_SECTORS,
    index=0,
)

only_tech = st.sidebar.toggle(T["tech_only"], value=False)
show_raw = st.sidebar.toggle(T["debug"], value=False)

st.sidebar.divider()

# ======================================================
# SELECIONAR DATASET - COM FALLBACK AUTOMÁTICO
# ======================================================
# Determinar se datasets estão disponíveis
companies_available = df_companies is not None and not df_companies.empty
caged_available = df_caged is not None and not df_caged.empty

# Se usuário selecionou Companies mas não está disponível, mudar para CAGED
if source == T["companies"] and not companies_available:
    st.warning("⚠️ Dataset de empresas não disponível. Alternando para Empregos (CAGED)...")
    source = T["jobs"]
    logger.warning("Companies não disponível, fallback para CAGED")

# Se usuário selecionou CAGED mas não está disponível, mudar para Companies
if source == T["jobs"] and not caged_available:
    st.warning("⚠️ Dataset de empregos não disponível. Alternando para Empresas (IBGE)...")
    source = T["companies"]
    logger.warning("CAGED não disponível, fallback para Companies")

# Se nenhum dataset está disponível, parar
if not companies_available and not caged_available:
    st.error("❌ NENHUM DATASET DISPONÍVEL. Verifique os arquivos parquet.")
    st.stop()

# Selecionar dataset baseado na fonte
if source == T["companies"]:
    df_main = df_companies
    value_col = "net"
    value_label = T["indicator_companies"]
else:
    df_main = df_caged
    value_col = "job_balance"
    value_label = T["indicator_jobs"]

# Ano
years = sorted(df_main["year"].dropna().astype(int).unique().tolist())
year_selected = st.sidebar.selectbox(T["year"], years, index=len(years) - 1)

# Aplicar filtros
df_view = apply_filters(
    df_main,
    year=int(year_selected),
    state=None if uf_selected == T["macro_all"] else uf_selected,
    macro_sector=None if macro_selected == T["macro_all"] else macro_selected,
    tech_only=only_tech,
)

logger.info(f"Filtros: year={year_selected}, uf={uf_selected}, macro={macro_selected} | {len(df_view)} linhas")

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
        "IBGE" if source == T["companies"] else "CAGED",
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
tab1, tab2, tab3, tab4, tab5 = st.tabs(T["tabs"])

# -------------------------
# TAB 1  TIME SERIES
# -------------------------
with tab1:
    st.subheader(T["time_series"])

    base = apply_filters(
        df_main,
        state=None if uf_selected == T["macro_all"] else uf_selected,
        macro_sector=None if macro_selected == T["macro_all"] else macro_selected,
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
# TAB 3  MAP & RANKINGS
# -------------------------
with tab3:
    st.subheader(" " + T["map_structural"])

    if df_scores.empty or geo_states is None:
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

        show_rank = st.toggle(T["map_toggle_rank"], value=True)

        fig_map = px.choropleth(
            state_score,
            geojson=geo_states,
            locations="uf",
            featureidkey="properties.sigla",
            color="score",
            hover_name="uf",
            hover_data={"uf": False, "score": ":.1f"},
            labels={"score": T["map_col_index"]},
        )
        fig_map.update_traces(
            hovertemplate=f"<b>%{{hovertext}}</b><br>{T['map_col_index']}: %{{customdata[0]:.1f}}<extra></extra>",
            customdata=state_score[["score"]].values,
        )
        fig_map.update_geos(
            fitbounds="geojson",
            visible=False,
            projection_type="mercator",
            showland=True,
            landcolor="rgba(20,20,20,1)",
            coastlinecolor="rgba(30,30,30,0.5)",
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
                textfont=dict(size=14, color="white", family="Arial Black"),
                textposition="middle center",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        fig_map.update_layout(
            template="plotly_dark",
            height=680,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            coloraxis_colorbar=dict(
                title=f"{T['map_col_index']}<br>",
                thickness=12,
                len=0.70,
                tickformat=".1f",
                tickfont=dict(size=10),
            ),
            font=dict(family="Arial", size=11),
            paper_bgcolor="rgba(17,17,17,1)",
            plot_bgcolor="rgba(17,17,17,1)",
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
# TAB 4  PNAD
# -------------------------
with tab4:
    render_pnad_section(lang=LANG)

# -------------------------
# TAB 5  DATA & DIAGNOSTICS
# -------------------------
with tab5:
    st.subheader(" " + T["data_diag"])

    st.code(
        "\n".join(
            [
                f"PROJECT_ROOT: {settings.paths.root}",
                f"companies_agg: {settings.paths.companies_agg} | exists={settings.paths.companies_agg.exists()}",
                f"opportunity_scores: {settings.paths.opportunity_scores} | exists={settings.paths.opportunity_scores.exists()}",
                f"caged_state_sector_year: {settings.paths.caged_state_sector_year} | exists={settings.paths.caged_state_sector_year.exists()}",
                f"brazil_states.geojson: {settings.paths.brazil_states_geojson} | exists={settings.paths.brazil_states_geojson.exists()}",
                f"Python: {sys.executable}",
                f"CWD: {os.getcwd()}",
            ]
        )
    )

    cA, cB, cC = st.columns(3)

    with cA:
        st.write("IBGE companies:", df_companies.shape)
        st.write("years:", sorted(df_companies["year"].dropna().astype(int).unique().tolist())[:25])
        st.write("ufs:", df_companies["uf"].nunique())

    with cB:
        st.write("CAGED:", df_caged.shape)
        st.write("years:", sorted(df_caged["year"].dropna().astype(int).unique().tolist()))
        st.write("ufs:", df_caged["uf"].nunique())

    with cC:
        st.write("Índice estrutural:", df_scores.shape)
        st.write("years:", sorted(df_scores["year"].dropna().astype(int).unique().tolist())[:25])
        st.write("ufs:", df_scores["uf"].nunique())

    st.divider()

    if show_raw:
        st.markdown("**Tabela do recorte atual**")
        st.dataframe(df_view, use_container_width=True, height=520)


logger.info("App renderizado com sucesso")
