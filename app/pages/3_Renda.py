import plotly.express as px
import streamlit as st
from google.cloud import bigquery

from lib import bq, queries
from lib.i18n import APP_NAME, language_selector, t

st.set_page_config(page_title=f"{APP_NAME} - {t('page_income')}", layout="wide")
language_selector()

filters = bq.render_filters_pnad()
params = (
    bigquery.ScalarQueryParameter("ano", "INT64", filters.get("ano", 0)),
    bigquery.ArrayQueryParameter("ufs", "STRING", filters.get("ufs", [])),
)

pnad_df = bq.run_query_checked(
    queries.pnad_sql(),
    params=params,
    required_columns_by_view={
        queries.TABLE_PNAD: [
            "ano",
            "trimestre",
            "sigla_uf",
            "formalidade",
            "pessoas ",
        ]
    },
)

st.title(t("income_title"))
st.caption(t("income_subtitle"))

if pnad_df.empty:
    st.info(t("no_data_filters"))
    st.stop()

if filters.get("trimestre"):
    pnad_df = pnad_df[pnad_df["trimestre"] == filters["trimestre"]]

if "pessoas" not in pnad_df.columns:
    st.info(t("income_unavailable"))
    st.stop()

series = (
    pnad_df.groupby("trimestre", as_index=False)["pessoas"].sum().sort_values("trimestre")
)
fig = px.bar(
    series,
    x="trimestre",
    y="pessoas",
    labels={"trimestre": t("col_trimestre"), "pessoas": t("col_vinculos")},
)
fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
