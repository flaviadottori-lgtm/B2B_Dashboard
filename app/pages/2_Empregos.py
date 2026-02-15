import plotly.express as px
import streamlit as st

from lib import bq, queries, sector
from lib.i18n import APP_NAME, language_selector, t

st.set_page_config(page_title=f"{APP_NAME} - {t('page_employment')}", layout="wide")
language_selector()

filters = bq.render_filters_caged()
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

series_filters = dict(filters)
series_filters["mes"] = 0
series_params = bq.build_params(series_filters)
series_raw = bq.run_query_checked(
    queries.caged_filtered_sql(),
    params=series_params,
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

st.title(t("employment_title"))
st.caption(t("employment_subtitle"))

if caged_df.empty:
    st.info(t("no_data_filters"))
    st.stop()

st.subheader(t("employment_series"))
series_df = series_raw.groupby("mes", as_index=False)["saldo"].sum().sort_values("mes")
fig = px.line(
    series_df,
    x="mes",
    y="saldo",
    markers=True,
    labels={"mes": t("col_mes"), "saldo": t("col_saldo")},
)
fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

st.subheader(t("employment_growth"))
if "cnae_secao" not in caged_df.columns:
    st.info(t("employment_no_sector"))
else:
    sector_df = series_raw.copy()
    sector_df = sector.add_macro_columns(sector_df, t, cnae_secao_col="cnae_secao")
    latest_month = int(sector_df["mes"].max())
    prev_month = latest_month - 1
    latest = sector_df[sector_df["mes"] == latest_month]
    prev = sector_df[sector_df["mes"] == prev_month]

    growth = (
        latest.groupby("macro_label", as_index=False)["saldo"]
        .sum()
        .rename(columns={"saldo": "saldo_atual"})
    )
    if not prev.empty:
        prev_sum = (
            prev.groupby("macro_label", as_index=False)["saldo"]
            .sum()
            .rename(columns={"saldo": "saldo_prev"})
        )
        growth = growth.merge(prev_sum, on="macro_label", how="left")
        growth["saldo_prev"] = growth["saldo_prev"].fillna(0)
        growth["delta"] = growth["saldo_atual"] - growth["saldo_prev"]
    else:
        growth["delta"] = growth["saldo_atual"]

    growth = growth.sort_values("delta", ascending=False).head(10)
    growth_display = growth.rename(columns={"macro_label": t("col_setor"), "delta": t("col_saldo")})
    st.dataframe(growth_display, use_container_width=True)
