"""
Funções de preparação e processamento de dados para a UI.
"""

import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def prep_companies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara dataset de empresas para visualização.

    Objetivos:
    - Nunca retornar None.
    - Nunca "matar" o app com raise por motivo comum (df vazio / colunas faltando).
    - Garantir colunas mínimas: year, uf, macro_sector, net/opened/closed.
    - Log detalhado (step-by-step) para depurar onde está o problema.

    Observação:
    - Se o parquet não estiver sendo lido (por engine/erro), df pode chegar vazio.
      Nesse caso, esta função apenas retorna vazio e loga.
    """
    from ..utils.formatters import clean_label, normalize_uf, macro_sector_from_label

    if df is None:
        logger.error("[prep_companies] df=None (entrada inválida). Retornando DF vazio.")
        return pd.DataFrame()

    if df.empty:
        logger.warning("[prep_companies] df vazio na entrada. Retornando DF vazio.")
        return df.copy()

    d = df.copy()
    initial_rows = len(d)
    logger.info(f"[prep_companies][STEP 0] Input: rows={initial_rows}, cols={len(d.columns)}")

    # Normalizar nomes de colunas
    d.columns = [str(c).strip() for c in d.columns]
    logger.info(f"[prep_companies][STEP 1] Colunas (amostra): {d.columns.tolist()[:25]}")

    # -----------------------------
    # YEAR (robusto)
    # -----------------------------
    if "year" in d.columns:
        d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    elif "ano" in d.columns:
        d["year"] = pd.to_numeric(d["ano"], errors="coerce").astype("Int64")
    else:
        d["year"] = pd.Series([pd.NA] * len(d), dtype="Int64")
        logger.warning("[prep_companies] Coluna 'year' não encontrada (nem 'ano'). Criada como NA.")

    logger.info(
        f"[prep_companies][STEP 2] year: non_null={int(d['year'].notna().sum())}/{len(d)} | "
        f"min={d['year'].min()} max={d['year'].max()}"
    )

    # -----------------------------
    # UF (robusto)
    # -----------------------------
    if "state" in d.columns:
        d["state"] = d["state"].astype(str).apply(clean_label)
        d["uf"] = d["state"].apply(normalize_uf)
    elif "uf" in d.columns:
        d["uf"] = d["uf"].astype(str).apply(clean_label).apply(normalize_uf)
    else:
        d["uf"] = pd.Series([None] * len(d))
        logger.warning(
            "[prep_companies] Coluna 'state'/'uf' não encontrada. 'uf' criado como None."
        )

    logger.info(
        f"[prep_companies][STEP 3] uf: non_null={int(pd.Series(d['uf']).notna().sum())}/{len(d)} | "
        f"nunique={pd.Series(d['uf']).nunique(dropna=True)}"
    )

    # -----------------------------
    # Macro-setor (robusto)
    # -----------------------------
    if "sector" in d.columns:
        d["sector"] = d["sector"].astype(str).apply(clean_label)
        d["macro_sector"] = d["sector"].apply(macro_sector_from_label)
    else:
        d["macro_sector"] = None
        logger.warning("[prep_companies] Coluna 'sector' não encontrada. macro_sector=None.")

    logger.info(
        f"[prep_companies][STEP 4] macro_sector: non_null={int(pd.Series(d['macro_sector']).notna().sum())}/{len(d)}"
    )

    # -----------------------------
    # Valores numéricos (nunca quebra)
    # -----------------------------
    for col in ["net", "opened", "closed"]:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)
        else:
            d[col] = 0
            logger.warning(f"[prep_companies] Coluna '{col}' não encontrada. Criada com 0.")

    logger.info(
        f"[prep_companies][STEP 5] numeric ok | "
        f"net_sum={float(d['net'].sum())} opened_sum={float(d['opened'].sum())} closed_sum={float(d['closed'].sum())}"
    )

    logger.info(f"[prep_companies][OK] Output: rows={len(d)}, cols={len(d.columns)}")
    return d


def prep_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara dataset de oportunidades para visualização.
    """
    from ..utils.formatters import clean_label, normalize_uf

    if df is None:
        logger.error("[prep_scores] df=None. Retornando DF vazio.")
        return pd.DataFrame()
    if df.empty:
        logger.warning("[prep_scores] df vazio. Retornando DF vazio.")
        return df.copy()

    d = df.copy()
    d.columns = [str(c).strip() for c in d.columns]

    if "year" in d.columns:
        d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    else:
        d["year"] = pd.Series([pd.NA] * len(d), dtype="Int64")
        logger.warning("[prep_scores] Coluna 'year' não encontrada. Criada como NA.")

    if "opportunity_score" in d.columns:
        d["opportunity_score"] = pd.to_numeric(d["opportunity_score"], errors="coerce")
    else:
        d["opportunity_score"] = pd.NA
        logger.warning("[prep_scores] Coluna 'opportunity_score' não encontrada.")

    if "units" in d.columns:
        d["units"] = pd.to_numeric(d["units"], errors="coerce")
    else:
        d["units"] = pd.NA
        logger.warning("[prep_scores] Coluna 'units' não encontrada.")

    # UF
    if "state" in d.columns:
        d["state"] = d["state"].astype(str).apply(clean_label)
        d["uf"] = d["state"].apply(normalize_uf)
    elif "uf" in d.columns:
        d["uf"] = d["uf"].astype(str).apply(clean_label).apply(normalize_uf)
    else:
        d["uf"] = None
        logger.warning("[prep_scores] Coluna 'state'/'uf' não encontrada. uf=None.")

    logger.info(f"[prep_scores][OK] Output: rows={len(d)}, cols={len(d.columns)}")
    return d


def prep_caged(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara dataset CAGED (empregos) para visualização.
    """
    from ..utils.formatters import clean_label, normalize_uf, macro_sector_from_label

    if df is None:
        logger.error("[prep_caged] df=None. Retornando DF vazio.")
        return pd.DataFrame()
    if df.empty:
        logger.warning("[prep_caged] df vazio. Retornando DF vazio.")
        return df.copy()

    d = df.copy()
    d.columns = [str(c).strip() for c in d.columns]

    if "year" in d.columns:
        d["year"] = pd.to_numeric(d["year"], errors="coerce").astype("Int64")
    else:
        d["year"] = pd.Series([pd.NA] * len(d), dtype="Int64")
        logger.warning("[prep_caged] Coluna 'year' não encontrada. Criada como NA.")

    # UF
    if "state" in d.columns:
        d["state"] = d["state"].astype(str).apply(clean_label)
        d["uf"] = d["state"].apply(normalize_uf)
    elif "uf" in d.columns:
        d["uf"] = d["uf"].astype(str).apply(clean_label).apply(normalize_uf)
    else:
        d["uf"] = None
        logger.warning("[prep_caged] Coluna 'state'/'uf' não encontrada. uf=None.")

    # Macro-setor
    if "sector" in d.columns:
        d["sector"] = d["sector"].astype(str).apply(clean_label)
        d["macro_sector"] = d["sector"].apply(macro_sector_from_label)
    else:
        d["macro_sector"] = None
        logger.warning("[prep_caged] Coluna 'sector' não encontrada. macro_sector=None.")

    # Job balance
    if "job_balance" in d.columns:
        d["job_balance"] = pd.to_numeric(d["job_balance"], errors="coerce").fillna(0)
    else:
        d["job_balance"] = 0
        logger.warning("[prep_caged] Coluna 'job_balance' não encontrada. Criada com 0.")

    logger.info(f"[prep_caged][OK] Output: rows={len(d)}, cols={len(d.columns)}")
    return d


def apply_filters(
    df: pd.DataFrame,
    year: Optional[int] = None,
    state: Optional[str] = None,
    macro_sector: Optional[str] = None,
    tech_only: bool = False,
    uf: Optional[list[str]] = None,
    setor: Optional[list[str]] = None,
    min_revenue: Optional[float] = None,
    max_revenue: Optional[float] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Filtros tolerantes para uso na UI.
    Se a coluna não existir, o filtro é ignorado (não quebra).
    """
    if df is None:
        return pd.DataFrame()

    out = df.copy()

    # Ano (year/ano)
    if year is not None:
        if "year" in out.columns:
            out = out[out["year"] == year]
        elif "ano" in out.columns:
            out = out[out["ano"] == year]

    # UF/Estado (aceita string única ou lista)
    state_values = None
    if state is not None:
        state_values = [state]
    if uf:
        state_values = uf
    if state_values:
        col = "uf" if "uf" in out.columns else ("state" if "state" in out.columns else None)
        if col:
            out = out[out[col].isin(state_values)]

    # Macro-setor/Setor
    if macro_sector:
        col = (
            "macro_sector"
            if "macro_sector" in out.columns
            else (
                "macro"
                if "macro" in out.columns
                else (
                    "setor"
                    if "setor" in out.columns
                    else ("sector" if "sector" in out.columns else None)
                )
            )
        )
        if col:
            out = out[out[col].isin([macro_sector])]

    if setor:
        col = "setor" if "setor" in out.columns else ("sector" if "sector" in out.columns else None)
        if col:
            out = out[out[col].isin(setor)]

    # Tech only (quando houver macro_sector/sector)
    if tech_only:
        col = (
            "macro_sector"
            if "macro_sector" in out.columns
            else (
                "setor"
                if "setor" in out.columns
                else ("sector" if "sector" in out.columns else None)
            )
        )
        if col:
            out = out[out[col].astype(str).str.contains("tec", case=False, na=False)]

    # Receita
    if min_revenue is not None or max_revenue is not None:
        col = (
            "revenue"
            if "revenue" in out.columns
            else ("receita" if "receita" in out.columns else None)
        )
        if col:
            if min_revenue is not None:
                out = out[out[col] >= min_revenue]
            if max_revenue is not None:
                out = out[out[col] <= max_revenue]

    return out


def build_gold_join(
    df_companies: pd.DataFrame,
    df_caged: pd.DataFrame,
    df_rais: pd.DataFrame,
    df_pnad: pd.DataFrame,
) -> pd.DataFrame:
    """
    Cria visão integrada (gold) por year/uf/macro_sector com joins tolerantes.
    """

    def _norm(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        out = df.copy()
        out.columns = [str(c).strip() for c in out.columns]
        # aliases básicos
        if "ano" in out.columns and "year" not in out.columns:
            out["year"] = out["ano"]
        if "sigla_uf" in out.columns and "uf" not in out.columns:
            out["uf"] = out["sigla_uf"]
        if "macro" in out.columns and "macro_sector" not in out.columns:
            out["macro_sector"] = out["macro"]
        if "setor" in out.columns and "macro_sector" not in out.columns:
            out["macro_sector"] = out["setor"]
        if "sector" in out.columns and "macro_sector" not in out.columns:
            out["macro_sector"] = out["sector"]
        return out

    companies = _norm(df_companies)
    caged = _norm(df_caged)
    rais = _norm(df_rais)
    pnad = _norm(df_pnad)

    keys = ["year", "uf", "macro_sector"]

    # Reduzir cada dataset às colunas chave + métricas principais
    def _select(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        existing = [c for c in cols if c in df.columns]
        if not existing:
            return pd.DataFrame()
        return df[existing].copy()

    comp_cols = keys + [c for c in ["net", "opened", "closed"] if c in companies.columns]
    caged_cols = keys + [
        c for c in ["job_balance", "admissoes", "desligamentos"] if c in caged.columns
    ]
    rais_cols = keys + [c for c in ["vinculos", "crescimento_yoy"] if c in rais.columns]
    pnad_cols = keys + [c for c in ["taxa_informalidade", "taxa_desemprego"] if c in pnad.columns]

    comp_df = _select(companies, comp_cols)
    caged_df = _select(caged, caged_cols)
    rais_df = _select(rais, rais_cols)
    pnad_df = _select(pnad, pnad_cols)

    # Base inicial
    df_gold = pd.DataFrame()
    if not comp_df.empty:
        df_gold = comp_df
    elif not caged_df.empty:
        df_gold = caged_df
    elif not rais_df.empty:
        df_gold = rais_df
    elif not pnad_df.empty:
        df_gold = pnad_df

    if df_gold.empty:
        return df_gold

    # Joins tolerantes (outer)
    for add_df in [caged_df, rais_df, pnad_df]:
        if not add_df.empty:
            df_gold = df_gold.merge(add_df, on=keys, how="outer")

    return df_gold
