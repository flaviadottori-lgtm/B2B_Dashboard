import plotly.express as px
import streamlit as st

from lib import bq, geo, queries, sector
from lib.i18n import APP_NAME, language_selector, t

st.set_page_config(page_title=f"{APP_NAME} - {t('page_overview')}", layout="wide")
language_selector()

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

st.title(t("overview_title"))
st.caption(t("overview_subtitle"))

saldo_total = int(caged_df["saldo"].sum()) if not caged_df.empty else 0
top_uf = ""
top_macro = ""
if not caged_df.empty:
    by_uf = (
        caged_df.groupby("sigla_uf", as_index=False)["saldo"]
        .sum()
        .sort_values("saldo", ascending=False)
    )
    if not by_uf.empty:
        top_uf = by_uf.iloc[0]["sigla_uf"]
    macro_df = sector.add_macro_columns(caged_df.copy(), t, cnae_secao_col="cnae_secao")
    by_macro = (
        macro_df.groupby("macro_label", as_index=False)["saldo"]
        .sum()
        .sort_values("saldo", ascending=False)
    )
    if not by_macro.empty:
        top_macro = by_macro.iloc[0]["macro_label"]

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("kpi_caged_balance"), f"{saldo_total:,}")
col2.metric(t("kpi_top_uf"), top_uf or "-")
col3.metric(t("kpi_top_macro"), top_macro or "-")
col4.metric(t("kpi_source_period"), f"CAGED {filters['ano']}/{filters['mes']}")

st.subheader(t("map_title"))
if caged_df.empty:
    st.info(t("no_data_filters"))
else:
    map_df = caged_df.groupby("sigla_uf", as_index=False)["saldo"].sum()
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
                color="saldo",
                color_continuous_scale="YlOrBr",
                hover_data={"sigla_uf": True, "saldo": True},
            )
            fig.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info(t("geojson_missing"))

st.subheader(t("ranking_title"))
left, right = st.columns(2)
with left:
    st.markdown(f"**{t('ranking_ufs')}**")
    if caged_df.empty:
        st.info(t("no_data_filters"))
    else:
        ranking_ufs = (
            caged_df.groupby("sigla_uf", as_index=False)["saldo"]
            .sum()
            .sort_values("saldo", ascending=False)
            .head(10)
        )
        ranking_ufs = ranking_ufs.rename(
            columns={"sigla_uf": t("col_state"), "saldo": t("col_saldo")}
        )
        st.dataframe(ranking_ufs, use_container_width=True)

with right:
    st.markdown(f"**{t('ranking_macro')}**")
    if caged_df.empty:
        st.info(t("no_data_filters"))
    else:
        macro_df = sector.add_macro_columns(caged_df.copy(), t, cnae_secao_col="cnae_secao")
        ranking_macro = (
            macro_df.groupby("macro_label", as_index=False)["saldo"]
            .sum()
            .sort_values("saldo", ascending=False)
            .head(10)
        )
        ranking_macro = ranking_macro.rename(
            columns={"macro_label": t("col_setor"), "saldo": t("col_saldo")}
        )
        st.dataframe(ranking_macro, use_container_width=True)

st.divider()
if rais_df.empty:
    st.info(t("no_data_filters"))
else:
    rais_summary = (
        rais_df.groupby("sigla_uf", as_index=False)["vinculos"]
        .sum()
        .sort_values("vinculos", ascending=False)
    )
    st.markdown(f"**{t('kpi_rais_vinculos')}**")
    st.dataframe(
        rais_summary.head(10).rename(
            columns={"sigla_uf": t("col_state"), "vinculos": t("col_vinculos")}
        ),
        use_container_width=True,
    )
