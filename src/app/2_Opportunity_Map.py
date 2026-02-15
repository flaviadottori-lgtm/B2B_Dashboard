from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import streamlit as st
from sklearn.preprocessing import StandardScaler

# -----------------------------
# Paths (ajuste se necessário)
# -----------------------------
TIDY_PATH = Path("data/processed/ibge_3274_3275_tidy.parquet")
SCORES_SNAPSHOT_PATH = Path("data/processed/opportunity_scores.parquet")  # seu atual (2021)
SCORES_BY_YEAR_DIR = Path("data/processed/opportunity_scores_by_year")  # novo dataset particionado


# -----------------------------
# Build scores by year (auto)
# -----------------------------
def rolling_cagr(s: pd.Series) -> float:
    s = s.dropna()
    if len(s) < 2:
        return np.nan
    if s.iloc[0] <= 0 or s.iloc[-1] <= 0:
        return np.nan
    return float((s.iloc[-1] / s.iloc[0]) ** (1 / (len(s) - 1)) - 1)


def rolling_volatility(s: pd.Series) -> float:
    s = s.dropna()
    if len(s) < 3:
        return np.nan
    return float(s.pct_change().std())


@st.cache_data(show_spinner=True)
def build_opportunity_scores_by_year(
    tidy_path: str | Path,
    out_dir: str | Path,
    window_years: int = 5,
    min_year: int | None = None,
    max_year: int | None = None,
) -> pd.DataFrame:
    """
    Gera opportunity_score por ano (janelas móveis) a partir do tidy.
    Também salva como dataset particionado por year em out_dir.
    Retorna o dataframe completo gerado.
    """
    tidy_path = Path(tidy_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(tidy_path)
    # Esperado no tidy: year, state, sector, units, high_growth_units (e opcional emprego/salário)
    required = {"year", "state", "sector", "units"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Tidy não tem colunas obrigatórias: {missing}. Colunas: {list(df.columns)}"
        )

    if "high_growth_units" not in df.columns:
        # se não existir, cria como 0
        df["high_growth_units"] = 0

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["state"] = df["state"].astype(str).str.upper().str.strip()
    df["sector"] = df["sector"].astype(str).str.strip()
    df["units"] = pd.to_numeric(df["units"], errors="coerce")
    df["high_growth_units"] = pd.to_numeric(df["high_growth_units"], errors="coerce").fillna(0)

    df = df.dropna(subset=["year", "state", "sector", "units"])
    df = df.sort_values(["state", "sector", "year"])

    if min_year is not None:
        df = df[df["year"] >= min_year]
    if max_year is not None:
        df = df[df["year"] <= max_year]

    records = []
    for (state, sector), g in df.groupby(["state", "sector"]):
        g = g.sort_values("year")
        years = g["year"].astype(int).to_numpy()

        # garante sequência suficiente
        if len(g) < window_years:
            continue

        for i in range(window_years - 1, len(g)):
            window = g.iloc[i - window_years + 1 : i + 1]
            Y = int(window["year"].iloc[-1])

            units = float(window["units"].iloc[-1])
            hgu = float(window["high_growth_units"].iloc[-1])
            hgr = (hgu / units) if units > 0 else 0.0

            cagr = rolling_cagr(window["units"])
            vol = rolling_volatility(window["units"])

            rec = {
                "year": Y,
                "state": state,
                "sector": sector,
                "units": units,
                "high_growth_units": hgu,
                "high_growth_ratio": hgr,
                "cagr_window": cagr,
                "volatility_window": vol,
            }

            # opcionais se existirem no tidy
            if "employment" in window.columns:
                rec["employment"] = float(window["employment"].iloc[-1])
            if "avg_wage" in window.columns:
                rec["avg_wage"] = float(window["avg_wage"].iloc[-1])

            records.append(rec)

    out = pd.DataFrame(records)
    if out.empty:
        raise ValueError(
            "Não consegui gerar scores por ano (dataset vazio). Verifique o tidy e a janela."
        )

    # score: padroniza features por ano (evita comparar 2010 com 2021 de forma enviesada)
    # você pode mudar pesos depois — aqui é um default robusto.
    def score_per_year(grp: pd.DataFrame) -> pd.DataFrame:
        grp = grp.copy()
        feats = [
            "units",
            "high_growth_units",
            "high_growth_ratio",
            "cagr_window",
            "volatility_window",
        ]

        X = grp[feats].copy()
        # estabilidade: menor vol é melhor
        X["volatility_window"] = -pd.to_numeric(X["volatility_window"], errors="coerce")

        # preenche NaN com median do ano (pra não quebrar scaler)
        for c in X.columns:
            med = X[c].median()
            X[c] = X[c].fillna(med)

        Z = StandardScaler().fit_transform(X)

        # pesos default (ajuste se quiser)
        grp["opportunity_score"] = (
            0.35 * Z[:, 0]  # size
            + 0.20 * Z[:, 1]  # high growth units
            + 0.15 * Z[:, 2]  # ratio
            + 0.20 * Z[:, 3]  # growth
            + 0.10 * Z[:, 4]  # stability (inverted vol)
        )

        return grp

    out = out.groupby("year", group_keys=False).apply(score_per_year)

    # salva particionado (rápido pra carregar por ano)
    table = pa.Table.from_pandas(out, preserve_index=False)
    pq.write_to_dataset(
        table,
        root_path=str(out_dir),
        partition_cols=["year"],
        existing_data_behavior="overwrite_or_ignore",
    )

    return out


@st.cache_data(show_spinner=False)
def load_scores(
    dataset_dir: str | Path, year: int | None = None, year_range: tuple[int, int] | None = None
) -> pd.DataFrame:
    filters = None
    if year is not None:
        filters = [("year", "==", int(year))]
    elif year_range is not None:
        y0, y1 = year_range
        filters = [("year", ">=", int(y0)), ("year", "<=", int(y1))]

    return pd.read_parquet(str(dataset_dir), engine="pyarrow", filters=filters)


def ensure_scores_dataset(window_years: int = 5):
    """
    Garante que existe o dataset particionado. Se não existir, cria.
    """
    if SCORES_BY_YEAR_DIR.exists() and any(SCORES_BY_YEAR_DIR.glob("year=*/")):
        return

    if not TIDY_PATH.exists():
        raise FileNotFoundError(f"Não encontrei o tidy: {TIDY_PATH.resolve()}")

    build_opportunity_scores_by_year(
        tidy_path=TIDY_PATH,
        out_dir=SCORES_BY_YEAR_DIR,
        window_years=window_years,
    )


# -----------------------------
# UI
# -----------------------------
st.title("🧭 Opportunity Map")
st.caption("Ano específico ou Momentum (últimos N anos). Leve: carrega só o recorte.")

with st.sidebar:
    st.subheader("⚙️ Config")
    window_years = st.slider("Janela para crescimento (anos)", 3, 8, 5)
    mode = st.radio("Modo", ["Ano específico", "Momentum (últimos N anos)"], horizontal=False)

    # botão opcional (rebuild)
    if st.button("Regerar dataset por ano (se necessário)"):
        # limpa cache e força rebuild
        st.cache_data.clear()
        if SCORES_BY_YEAR_DIR.exists():
            # não apaga automaticamente por segurança
            st.warning(
                "Cache limpo. Se quiser rebuild total, apague a pasta opportunity_scores_by_year e rode de novo."
            )
        st.rerun()

# garante dataset
try:
    ensure_scores_dataset(window_years=window_years)
except Exception as e:
    st.error(f"Falha ao preparar dataset por ano: {e}")
    st.stop()

# lista anos disponíveis
all_years = sorted([int(p.name.split("=")[1]) for p in SCORES_BY_YEAR_DIR.glob("year=*")])

if mode == "Ano específico":
    year_sel = st.selectbox("Ano", all_years, index=len(all_years) - 1)
    df = load_scores(SCORES_BY_YEAR_DIR, year=year_sel)

else:
    n_years = st.slider("Últimos N anos", 3, min(10, len(all_years)), min(5, len(all_years)))
    y1 = max(all_years)
    y0 = y1 - (n_years - 1)
    df = load_scores(SCORES_BY_YEAR_DIR, year_range=(y0, y1))

st.success(f"Dados carregados: {df.shape[0]} linhas • anos: {sorted(df['year'].unique())[:3]} ...")

st.dataframe(df.head(50), use_container_width=True)
