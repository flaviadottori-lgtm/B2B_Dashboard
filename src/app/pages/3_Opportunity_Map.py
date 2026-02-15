import streamlit as st
import pandas as pd


@st.cache_data
def load_companies_agg():
    return pd.read_parquet("data/processed/companies_agg.parquet")


df_comp = load_companies_agg()
years = sorted(df_comp["year"].dropna().unique().tolist())

# guarda em session_state com uma key fixa, pra outras páginas usarem
st.sidebar.selectbox("Selecione o ano", years, index=years.index(max(years)), key="selected_year")
