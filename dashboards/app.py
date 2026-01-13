import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

# ======================================================
# CONFIGURAÇÃO DA PÁGINA
# ======================================================
st.set_page_config(
    page_title="Mapeamento do Crescimento Empresarial e Oportunidades B2B no Brasil",
    page_icon="📊",
    layout="wide"
)

# ======================================================
# ESTILO GLOBAL (DARK EXECUTIVO)
# ======================================================
st.markdown("""
<style>
    body { background-color: #0E1117; color: #FAFAFA; }
    .block-container { padding-top: 2rem; }
    .kpi {
        background-color: #161B22;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        border: 1px solid #21262D;
    }
    .kpi h1 { font-size: 34px; margin-bottom: 0; }
    .kpi p { color: #8B949E; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

# ======================================================
# HELPERS
# ======================================================
def fmt_int(n: int) -> str:
    return f"{int(n):,}".replace(",", ".")

def find_project_root(start: Path) -> Path:
    start = start.resolve()
    for p in [start] + list(start.parents):
        if (p / "data" / "processed").exists():
            return p
    return start.parent

def load_parquet_safe(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_parquet(path)
    except Exception as e:
        st.warning(f"Falha lendo {path.name}: {e}")
        return None

def load_geojson_safe(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"Falha lendo {path.name}: {e}")
        return None

# ======================================================
# PATHS
# ======================================================
PROJECT_ROOT = find_project_root(Path(__file__))
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
GEO_DIR = PROJECT_ROOT / "data" / "geo"

COMPANIES_FILE = PROCESSED_DIR / "companies_agg.parquet"
OPP_SCORES_FILE = PROCESSED_DIR / "opportunity_scores.parquet"
BRAZIL_STATES_GEOJSON = GEO_DIR / "brazil_states.geojson"

# ======================================================
# DIAGNÓSTICO (AJUDA MUITO)
# ======================================================
with st.expander("✅ Diagnóstico (abra se algo não estiver mudando)", expanded=False):
    st.write("Arquivo rodando agora:", str(Path(__file__).resolve()))
    st.write("PROJECT_ROOT:", str(PROJECT_ROOT))
    st.write("COMPANIES_FILE:", str(COMPANIES_FILE), "| exists:", COMPANIES_FILE.exists())
    st.write("OPP_SCORES_FILE:", str(OPP_SCORES_FILE), "| exists:", OPP_SCORES_FILE.exists())
    st.write("GEOJSON:", str(BRAZIL_STATES_GEOJSON), "| exists:", BRAZIL_STATES_GEOJSON.exists())

# ======================================================
# LOAD DATA
# ======================================================
df_real = load_parquet_safe(COMPANIES_FILE)
df_scores = load_parquet_safe(OPP_SCORES_FILE)
geo_states = load_geojson_safe(BRAZIL_STATES_GEOJSON)

# ======================================================
# PREP EMPRESAS (CNPJ/AGG)
# ======================================================
using_mock = False

if df_real is None:
    using_mock = True
    # Mock só para não quebrar (ideal é ter dados reais multi-ano)
    df_real = pd.DataFrame({
        "year": [2019, 2020, 2021, 2022, 2023, 2024],
        "region": ["Brasil"]*6,
        "state": ["BR"]*6,
        "sector": ["Mock"]*6,
        "opened": [1200000, 1350000, 1500000, 1700000, 1900000, 2000000],
        "closed": [900000, 1000000, 1100000, 1150000, 1250000, 1300000],
        "net": [300000, 350000, 400000, 550000, 650000, 700000],
    })

df_real = df_real.copy()
df_real["year"] = pd.to_numeric(df_real["year"], errors="coerce")
df_real = df_real.dropna(subset=["year"])
df_real["year"] = df_real["year"].astype(int)

required = {"year", "state", "sector", "opened", "closed", "net"}
missing = required - set(df_real.columns)
if missing:
    st.error(f"companies_agg.parquet sem colunas: {missing}")
    st.stop()

# Série temporal
df_growth = (
    df_real.groupby("year", as_index=False)[["opened", "closed"]]
    .sum()
    .sort_values("year")
)
years_available = sorted(df_growth["year"].unique().tolist())

# ======================================================
# SIDEBAR — FILTROS
# ======================================================
st.sidebar.title("🎯 Filtros Estratégicos")

year_selected = st.sidebar.selectbox(
    "Selecione o ano",
    options=sorted(years_available, reverse=True),
    index=0,
    key="year_selected"
)
year_selected = int(year_selected)

# ======================================================
# FILTRAGEM DO ANO + LIMPEZA DE SETORES RUINS (TOTAL/T/U)
# ======================================================
df_year = df_real[df_real["year"] == year_selected].copy()

# remove Total + setores que não fazem sentido para oportunidades
if "sector" in df_year.columns:
    df_year = df_year[
        (~df_year["sector"].str.contains("Total", na=False)) &
        (~df_year["sector"].str.startswith("T ", na=False)) &
        (~df_year["sector"].str.startswith("U ", na=False))
    ]

opened = int(df_year["opened"].sum())
closed = int(df_year["closed"].sum())
balance = opened - closed

df_sector = (
    df_year.groupby("sector", as_index=False)["net"]
    .sum()
    .rename(columns={"net": "companies"})
    .sort_values("companies", ascending=False)
)

df_state = (
    df_year.groupby("state", as_index=False)["net"]
    .sum()
    .rename(columns={"net": "companies"})
    .sort_values("companies", ascending=False)
)

# ======================================================
# HEADER
# ======================================================
st.title("📊 Brazil B2B Market Intelligence")

if using_mock:
    st.info("Você está vendo dados **simulados** porque companies_agg.parquet não carregou. (No seu caso, quando ele existe, isso não aparece.)")

st.markdown(f"**Ano selecionado:** {year_selected}")
st.divider()

# ======================================================
# KPIs
# ======================================================
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="kpi">
        <h1>{fmt_int(opened)}</h1>
        <p>Empresas Abertas</p>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi">
        <h1>{fmt_int(closed)}</h1>
        <p>Empresas Encerradas</p>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi">
        <h1>{fmt_int(balance)}</h1>
        <p>Saldo Empresarial</p>
    </div>
    """, unsafe_allow_html=True)

# ======================================================
# EVOLUÇÃO TEMPORAL
# ======================================================
st.subheader("📈 Evolução do Mercado Empresarial")

fig_growth = px.line(
    df_growth,
    x="year",
    y=["opened", "closed"],
    markers=True,
    labels={"value": "Empresas", "year": "Ano", "variable": "Indicador"},
    title="Abertura vs Encerramento de Empresas"
)
fig_growth.update_layout(template="plotly_dark")
st.plotly_chart(fig_growth, use_container_width=True)

# ======================================================
# TOPS
# ======================================================
st.subheader("📊 Onde estão as oportunidades B2B?")

col_a, col_b = st.columns(2)

with col_a:
    fig_sector = px.bar(
        df_sector.head(10),
        x="sector",
        y="companies",
        text_auto=True,
        title=f"Top Setores — {year_selected}"
    )
    fig_sector.update_layout(template="plotly_dark")
    st.plotly_chart(fig_sector, use_container_width=True)

with col_b:
    fig_state = px.bar(
        df_state.head(10),
        x="state",
        y="companies",
        text_auto=True,
        title=f"Top Estados — {year_selected}"
    )
    fig_state.update_layout(template="plotly_dark")
    st.plotly_chart(fig_state, use_container_width=True)

# ======================================================
## ======================================================
# 🗺️ MAPA — Opportunity Score (IBGE 2021)
# ======================================================

st.subheader("🗺️ Mapa do Brasil — Opportunity Score (IBGE, 2021)")
st.caption("ℹ️ O Opportunity Score disponível agora é **2021** (base IBGE 2008–2021).")

if df_scores is None or geo_states is None:
    st.error("Mapa indisponível porque o app não conseguiu carregar o score IBGE (parquet) e/ou o GeoJSON.")
else:
    # --------------------------------------------------
    # Filtrar apenas IBGE 2021
    # --------------------------------------------------
    df_scores_2021 = df_scores.copy()
    if "year" in df_scores_2021.columns:
        df_scores_2021 = df_scores_2021[df_scores_2021["year"] == 2021].copy()

    # --------------------------------------------------
    # Média ponderada por 'units' (sem .apply para evitar bugs)
    # --------------------------------------------------
    df_scores_2021["_weighted"] = (
        df_scores_2021["opportunity_score"] * df_scores_2021["units"]
    )

    state_score = (
        df_scores_2021
        .groupby("state", as_index=False)
        .agg(
            weighted_score=("_weighted", "sum"),
            total_units=("units", "sum")
        )
    )

    # Evitar divisão por zero
    state_score = state_score[state_score["total_units"] > 0]

    state_score["opportunity_score"] = (
        state_score["weighted_score"] / state_score["total_units"]
    )

    state_score = state_score[["state", "opportunity_score"]]

    # --------------------------------------------------
    # Choropleth
    # --------------------------------------------------
    fig_map = px.choropleth(
        state_score,
        geojson=geo_states,
        locations="state",
        featureidkey="properties.sigla",   # seu geojson usa 'sigla'
        color="opportunity_score",
        hover_name="state",
        hover_data={"opportunity_score": ":.1f"},
        title="Opportunity Score por Estado (IBGE 2021)",
        color_continuous_scale="Turbo"
    )

    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_layout(
        template="plotly_dark",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    st.plotly_chart(fig_map, use_container_width=True)

# ======================================================
# INSIGHT FINAL
# ======================================================
st.subheader("💡 Insight Executivo")

st.markdown(f"""
> No recorte de **{year_selected}**, o saldo de **{fmt_int(balance)} empresas** ajuda a identificar  
> onde existe maior dinâmica de mercado.  
>  
> O mapa IBGE 2021 mostra o **potencial estrutural de crescimento** (oportunidade) por estado —  
> útil para decisões de **expansão, investimento e parcerias B2B**.
""")
