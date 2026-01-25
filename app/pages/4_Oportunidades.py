import streamlit as st

from lib import bq, queries, sector
from lib.i18n import APP_NAME, language_selector, t

st.set_page_config(page_title=f"{APP_NAME} - {t('page_opportunities')}", layout="wide")
language_selector()

filters = bq.render_filters_rais()
params = bq.build_params(filters)

score_df = bq.run_query_checked(
    queries.opportunity_sql(),
    params=params,
    required_columns_by_view={
        queries.VIEW_OPPORTUNITY: [
            "ano",
            "sigla_uf",
            "cnae_subclasse",
            "vinculos",
            "crescimento_vinculos_yoy",
            "volatilidade_vinculos_5a",
            "opportunity_score",
            "score_percentil_ano",
        ]
    },
)

st.title(t("opportunities_title"))
st.caption(t("opportunities_subtitle"))

if score_df.empty:
    st.info(t("no_data_filters"))
    st.stop()

score_df = sector.add_macro_columns(score_df, t)
if filters.get("macro_keys"):
    score_df = score_df[score_df["macro_key"].isin(filters["macro_keys"])]

score_df["subclasse_label"] = score_df["cnae_subclasse"].apply(sector.format_cnae_subclasse)
top_n = st.slider(t("top_n"), min_value=5, max_value=50, value=20)
cols = [
    "sigla_uf",
    "macro_label",
    "subclasse_label",
    "opportunity_score",
    "score_percentil_ano",
    "vinculos",
    "crescimento_vinculos_yoy",
    "volatilidade_vinculos_5a",
]
table = score_df.sort_values("opportunity_score", ascending=False)[cols].head(top_n)
table_display = table.rename(
    columns={
        "sigla_uf": t("col_state"),
        "macro_label": t("col_setor"),
        "subclasse_label": t("col_cnae_subclasse"),
        "opportunity_score": t("col_score"),
        "score_percentil_ano": t("col_percentil"),
        "vinculos": t("col_vinculos"),
        "crescimento_vinculos_yoy": t("col_crescimento"),
        "volatilidade_vinculos_5a": t("col_volatilidade"),
    }
)
st.dataframe(table_display, use_container_width=True)
