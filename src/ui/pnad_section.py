"""
Componentes e renderização para seção PNAD no Streamlit app
Suporta múltiplas métricas: população, informalidade, renda, desemprego
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from typing import Optional

from src.utils.data_loading import load_pnad_metrics_data
from src.config.constants import I18N


def render_pnad_section(lang: str = "pt"):
    """
    Renderiza seção completa do PNAD no Streamlit com suporte a múltiplas métricas

    Args:
        lang: Idioma ('pt' ou 'en')
    """
    T = I18N[lang]

    # Carregar dados PNAD (métricas v2.0)
    pnad_df = st.cache_data(load_pnad_metrics_data)()
    show_diag = st.checkbox("Mostrar diagnóstico PNAD", value=False)
    if pnad_df is None or pnad_df.empty:
        st.warning("PNAD ainda não carregada. Rode python run_pnad_pipeline.py e depois o build.")
        if show_diag:
            from src.utils.duckdb_client import get_con

            con = get_con()
            st.code(str(con.execute("SHOW TABLES").fetchdf()))
            for t in ["pnad", "pnad_enriched"]:
                if t in [r[0] for r in con.execute("SHOW TABLES").fetchall()]:
                    st.write(f"COUNT {t}:", con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0])
            if "pnad_enriched" in [r[0] for r in con.execute("SHOW TABLES").fetchall()]:
                st.write(
                    "sem_match:",
                    con.execute(
                        "SELECT SUM(CASE WHEN sigla_uf IS NULL THEN 1 ELSE 0 END) FROM pnad_enriched"
                    ).fetchone()[0],
                )
        return

    # Título e descrição
    st.subheader(T["pnad_title"])
    st.caption(T["pnad_desc"])

    # Seletor de métrica
    st.markdown(f"### {T.get('pnad_metric_selector', 'Métrica')}")

    metric_options = {
        "populacao": T.get("pnad_population", "População"),
        "informalidade": T.get("pnad_informality", "Taxa de Informalidade"),
        "renda": T.get("pnad_income", "Renda Média do Trabalho"),
        "desemprego": T.get("pnad_unemployment", "Taxa de Desemprego"),
    }

    selected_metric = st.selectbox(
        T.get("pnad_select_metric", "Escolha a métrica"),
        options=list(metric_options.keys()),
        format_func=lambda x: metric_options[x],
        index=0,
    )

    # Renderizar seção baseada na métrica selecionada
    if selected_metric == "populacao":
        _render_population_section(pnad_df, T, lang)
    elif selected_metric == "informalidade":
        _render_informality_section(T, lang)
    elif selected_metric == "renda":
        _render_income_section(T, lang)
    elif selected_metric == "desemprego":
        _render_unemployment_section(T, lang)


def _render_population_section(pnad_df: pd.DataFrame, T: dict, lang: str):
    """Renderiza seção de população (compatível com parquet atual)"""

    st.markdown(f"### {T['pnad_filters']}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        years = sorted(pnad_df["ano"].unique())
        selected_year = st.selectbox(T["pnad_year"], years, index=len(years) - 1, key="pop_year")

    with col2:
        # Usar coluna 'uf' (string) e ordenar conforme UF_ORDER se disponível
        from src.config import UF_ORDER

        ufs = sorted(pnad_df["uf"].dropna().unique().tolist())
        # Ordenar por UF_ORDER se todos presentes, senão ordem alfabética
        if set(UF_ORDER).issubset(set(ufs)):
            ufs = [uf for uf in UF_ORDER if uf in ufs]
        else:
            ufs = sorted(ufs)
        selected_uf = st.selectbox(T["pnad_state"], ["(All)"] + ufs, key="pop_uf")

    with col3:
        genders = sorted(pnad_df["sexo"].unique())
        selected_gender = st.selectbox(T["pnad_gender"], ["(All)"] + genders, key="pop_gender")

    with col4:
        age_groups = sorted(pnad_df["grupo_idade"].unique())
        selected_age = st.selectbox(T["pnad_age_group"], ["(All)"] + age_groups, key="pop_age")

    # Aplicar filtros
    filtered_df = pnad_df.copy()

    if selected_year:
        filtered_df = filtered_df[filtered_df["ano"] == selected_year]

    if selected_uf != "(All)":
        filtered_df = filtered_df[filtered_df["uf"] == selected_uf]

    if selected_gender != "(All)":
        filtered_df = filtered_df[filtered_df["sexo"] == selected_gender]

    if selected_age != "(All)":
        filtered_df = filtered_df[filtered_df["grupo_idade"] == selected_age]

    if filtered_df.empty:
        st.info(T["no_data"])
        return

    # KPIs
    st.markdown(f"### {T.get('pnad_kpis', 'KPIs')}")

    col1, col2, col3 = st.columns(3)

    total_population = filtered_df["populacao"].sum()
    num_regions = filtered_df["uf"].nunique() if "uf" in filtered_df.columns else 1
    num_groups = filtered_df["grupo_idade"].nunique() if "grupo_idade" in filtered_df.columns else 1

    with col1:
        st.metric(T["pnad_population"], f"{total_population:,.0f}")

    with col2:
        st.metric("Regiões", num_regions)

    with col3:
        st.metric(T["pnad_age_group"], num_groups)

    # Gráfico: Série temporal
    years_in_data = filtered_df["ano"].nunique()

    if years_in_data > 1:
        st.markdown(f"### {T['pnad_time_series']}")

        ts_data = filtered_df.groupby("ano")["populacao"].sum().reset_index()

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ts_data["ano"],
                y=ts_data["populacao"],
                mode="lines+markers",
                name=T["pnad_population"],
                line=dict(color="#0B1F33", width=3),
                marker=dict(size=8),
            )
        )

        fig.update_layout(
            title=T["pnad_time_series"],
            xaxis_title=T["pnad_year"],
            yaxis_title=T["pnad_population"],
            hovermode="x unified",
            template="plotly_white",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    # Gráfico: Comparação por UF
    if selected_uf == "(All)" and filtered_df["uf_code"].nunique() > 1:
        st.markdown(f"### {T['pnad_comparison']}")

        uf_data = filtered_df.groupby("uf_code")["populacao"].sum().reset_index()
        uf_data = uf_data.sort_values("populacao", ascending=True)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=uf_data["uf_code"],
                x=uf_data["populacao"],
                orientation="h",
                marker=dict(color="#0B1F33"),
                text=uf_data["populacao"].apply(lambda x: f"{x:,.0f}"),
                textposition="auto",
            )
        )

        fig.update_layout(
            title=T["pnad_comparison"],
            xaxis_title=T["pnad_population"],
            yaxis_title=T["pnad_state"],
            height=400,
            template="plotly_white",
        )

        st.plotly_chart(fig, use_container_width=True)

    # Tabela de dados
    st.markdown(f"### {T['pnad_data']}")

    display_cols = ["ano", "uf_code", "sexo", "grupo_idade", "populacao"]
    display_df = filtered_df[display_cols].copy()

    # Renomear colunas com tradução
    col_names = {
        "ano": T["pnad_year"],
        "uf_code": T["pnad_state"],
        "sexo": T["pnad_gender"],
        "grupo_idade": T["pnad_age_group"],
        "populacao": T["pnad_population"],
    }

    display_df.columns = [col_names.get(c, c) for c in display_df.columns]

    st.dataframe(
        display_df.sort_values(T["pnad_population"], ascending=False),
        use_container_width=True,
        height=300,
    )


def _render_informality_section(T: dict, lang: str):
    """Renderiza seção de informalidade (requer novo parquet com métricas)"""

    # Para agora, mostrar mensagem de que está em desenvolvimento
    st.info("📊 Métrica de informalidade requer execução do pipeline com métricas avançadas.")
    st.code("python run_pnad_metrics_pipeline.py")


def _render_income_section(T: dict, lang: str):
    """Renderiza seção de renda (requer novo parquet com métricas)"""

    st.info("📊 Métrica de renda requer execução do pipeline com métricas avançadas.")
    st.code("python run_pnad_metrics_pipeline.py")


def _render_unemployment_section(T: dict, lang: str):
    """Renderiza seção de desemprego (requer novo parquet com métricas)"""

    st.info("📊 Métrica de desemprego requer execução do pipeline com métricas avançadas.")
    st.code("python run_pnad_metrics_pipeline.py")
