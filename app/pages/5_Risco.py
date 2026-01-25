import streamlit as st

from lib import bq, queries
from lib.i18n import APP_NAME, language_selector, t

st.set_page_config(page_title=f"{APP_NAME} - {t('page_risk')}", layout="wide")
language_selector()

filters = bq.render_filters_rais()
params = bq.build_params(filters)

region_df = bq.run_query_checked(
    queries.region_risk_sql(),
    params=params,
    required_columns_by_view={
        queries.VIEW_REGION_RISK: [
            "ano",
            "sigla_uf",
            "vinculos_uf",
            "crescimento_vinculos_uf_yoy",
            "volatilidade_uf_5a",
            "hhi_concentracao_setorial",
            "top3_setores",
        ]
    },
)

st.title(t("risk_title"))

if region_df.empty:
    st.info(t("no_data_filters"))
    st.stop()

region_df["top3_setores"] = region_df["top3_setores"].apply(lambda v: ", ".join(v) if isinstance(v, list) else str(v))

region_display = region_df.rename(
    columns={
        "sigla_uf": t("col_state"),
        "vinculos_uf": t("col_vinculos"),
        "crescimento_vinculos_uf_yoy": t("col_crescimento"),
        "volatilidade_uf_5a": t("col_volatilidade"),
        "hhi_concentracao_setorial": t("col_hhi"),
        "top3_setores": t("col_setor"),
    }
)
st.dataframe(region_display, use_container_width=True)
