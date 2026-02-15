import plotly.express as px
import streamlit as st

from lib import bq, geo, queries, sector
from lib.i18n import APP_NAME, language_selector, t

st.set_page_config(page_title=APP_NAME, layout="wide")
language_selector()

st.markdown(f"# {t('app_name')}")
st.caption(t("app_subtitle"))

filters = bq.render_filters_home()
params = bq.build_params(filters)

caged_df = bq.run_query_checked(
    queries.caged_filtered_sql(),
    params=params,
    required_columns_by_view={
        queries.TABLE_CAGED: [
            "ano",
            "mes",
            "sigla_uf",
            "cnae_secao",
            "cnae_subclasse",
            "admissoes",
            "desligamentos",
            "saldo",
        ]
    },
)
rais_df = bq.run_query_checked(
    queries.rais_filtered_sql(),
    params=params,
    required_columns_by_view={
        queries.TABLE_RAIS: [
            "ano",
            "sigla_uf",
            "cnae_subclasse",
            "vinculos",
        ]
    },
)

st.markdown(t("home_intro"))
st.caption(t("home_hint"))

ufs = filters.get("ufs") or []
macros = filters.get("caged_secoes") or []
macro_label = (
    t("filters_summary_all")
    if not macros
    else ", ".join(sector.secao_display_label(value, t) for value in macros)
)
subclasses = filters.get("caged_subclasses") or []
subclass_label = (
    t("filters_summary_all")
    if not subclasses
    else ", ".join(sector.format_cnae_subclasse(value) for value in subclasses)
)
summary = (
    f"{t('filters_summary_year')}: {filters['ano']} · "
    f"{t('filters_summary_state')}: {t('filters_summary_brazil') if not ufs else ', '.join(ufs)} · "
    f"{t('filters_summary_macro')}: {macro_label} · "
    f"{t('filters_summary_subclass')}: {subclass_label}"
)
st.markdown(summary)

st.divider()

saldo_total = int(caged_df["saldo"].sum()) if not caged_df.empty else 0
adm_total = int(caged_df["admissoes"].sum()) if not caged_df.empty else 0
des_total = int(caged_df["desligamentos"].sum()) if not caged_df.empty else 0
vinculos_total = int(rais_df["vinculos"].sum()) if not rais_df.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("kpi_caged_balance"), f"{saldo_total:,}")
col2.metric(t("kpi_caged_adm"), f"{adm_total:,}")
col3.metric(t("kpi_caged_des"), f"{des_total:,}")
col4.metric(t("kpi_rais_vinculos"), f"{vinculos_total:,}")

metric_options = {
    t("map_metric_saldo"): ("caged", "saldo", t("col_saldo")),
    t("map_metric_adm"): ("caged", "admissoes", t("col_admissoes")),
    t("map_metric_des"): ("caged", "desligamentos", t("col_desligamentos")),
    t("map_metric_vinculos"): ("rais", "vinculos", t("col_vinculos")),
}
metric_choice = st.selectbox(t("map_metric_label"), list(metric_options.keys()), index=0)
metric_source, metric_col, metric_label = metric_options[metric_choice]

if metric_source == "caged" and not caged_df.empty:
    map_df = caged_df.groupby("sigla_uf", as_index=False)[metric_col].sum()
    macro_df = sector.add_macro_columns(caged_df.copy(), t, cnae_secao_col="cnae_secao")
    top_macro = (
        macro_df.groupby("macro_label", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
    )
elif metric_source == "rais" and not rais_df.empty:
    map_df = rais_df.groupby("sigla_uf", as_index=False)[metric_col].sum()
    macro_df = sector.add_macro_columns(rais_df.copy(), t)
    top_macro = (
        macro_df.groupby("macro_label", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
    )
else:
    map_df = None
    top_macro = None

st.subheader(t("map_title"))
if map_df is None or map_df.empty:
    st.info(t("no_data_filters"))
else:
    try:
        geojson = geo.load_geojson()
        feature_key, _ = geo.resolve_geo_feature_key(geojson)
        if not feature_key:
            st.info(t("geojson_missing"))
        else:
            fig = px.choropleth(
                map_df,
                geojson=geojson,
                locations="sigla_uf",
                featureidkey=feature_key,
                color=metric_col,
                color_continuous_scale="YlOrBr",
                hover_data={"sigla_uf": True, metric_col: True},
            )
            fig.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info(t("geojson_missing"))

st.subheader(t("ranking_title"))
left, right = st.columns(2)
with left:
    st.markdown(f"**{t('ranking_ufs')}**")
    if map_df is None or map_df.empty:
        st.info(t("no_data_filters"))
    else:
        ranking_ufs = map_df.sort_values(metric_col, ascending=False).head(10)
        ranking_ufs = ranking_ufs.rename(
            columns={"sigla_uf": t("col_state"), metric_col: metric_label}
        )
        st.dataframe(ranking_ufs, use_container_width=True)
with right:
    st.markdown(f"**{t('ranking_macro')}**")
    if top_macro is None or top_macro.empty:
        st.info(t("no_data_filters"))
    else:
        ranking_macro = top_macro.head(10).rename(
            columns={"macro_label": t("col_setor"), metric_col: metric_label}
        )
        st.dataframe(ranking_macro, use_container_width=True)
