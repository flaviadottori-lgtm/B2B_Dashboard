import pandas as pd
import plotly.express as px
import streamlit as st

from lib import bq, queries, sector
from lib.i18n import APP_NAME, language_selector, t

st.set_page_config(page_title=f"{APP_NAME} - {t('page_profile')}", layout="wide")
language_selector()

filters = bq.render_filters_rais()
params = bq.build_params(filters)

profile_df = bq.run_query_checked(
    queries.profile_mix_sql(),
    params=params,
    required_columns_by_view={
        queries.VIEW_PROFILE: [
            "ano",
            "sigla_uf",
            "cnae_subclasse",
            "sexo",
            "grupo_idade",
            "grau_instrucao",
            "participacao",
            "vinculos_total",
        ]
    },
)

st.title(t("profile_title"))

if profile_df.empty:
    st.info(t("no_data_filters"))
    st.stop()

profile_df = sector.add_macro_columns(profile_df, t)
if filters.get("macro_keys"):
    profile_df = profile_df[profile_df["macro_key"].isin(filters["macro_keys"])]


def weighted_share(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_col, "share"])
    df = df.copy()
    df["peso"] = df["vinculos_total"].fillna(0)
    if (df["peso"] > 0).any():
        grouped = df.groupby(group_col).apply(
            lambda g: (g["participacao"] * g["peso"]).sum() / g["peso"].sum()
        )
        return grouped.reset_index().rename(columns={0: "share"})
    return df.groupby(group_col)["participacao"].mean().reset_index().rename(columns={"participacao": "share"})


col1, col2 = st.columns(2)

with col1:
    st.subheader(t("profile_education"))
    edu = weighted_share(profile_df, "grau_instrucao")
    fig = px.bar(
        edu,
        x="grau_instrucao",
        y="share",
        labels={"grau_instrucao": t("col_grau_instrucao"), "share": t("col_participacao")},
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader(t("profile_gender"))
    sex = weighted_share(profile_df, "sexo")
    fig = px.pie(
        sex,
        names="sexo",
        values="share",
    )
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.subheader(t("profile_age"))
age = weighted_share(profile_df, "grupo_idade")
fig = px.bar(
    age,
    x="grupo_idade",
    y="share",
    labels={"grupo_idade": t("col_grupo_idade"), "share": t("col_participacao")},
)
fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)
