from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
import os

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError

from lib import sector
from lib.i18n import t

DEFAULT_PROJECT = 'dados-mercado-brasil'
DEFAULT_DATASET_GOLD = 'gold'


def get_config(key: str, default: Any | None = None) -> Any | None:
    value = os.getenv(key)
    if value:
        return value
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


@st.cache_resource
def get_client() -> bigquery.Client | None:
    project_id = get_config('BQ_PROJECT_ID', DEFAULT_PROJECT)
    credentials_path = get_config('GOOGLE_APPLICATION_CREDENTIALS')
    try:
        if credentials_path:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            return bigquery.Client(project=project_id, credentials=credentials)
        return bigquery.Client(project=project_id)
    except DefaultCredentialsError:
        st.error(f"{t('bq_auth_error_title')}: {t('bq_auth_error_body')}")
        return None


@st.cache_data(show_spinner=False)
def run_query(
    sql: str,
    params: Tuple[bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter, ...],
) -> pd.DataFrame:
    try:
        client = get_client()
        if client is None:
            return pd.DataFrame()
        job_config = bigquery.QueryJobConfig(query_parameters=list(params))
        return client.query(sql, job_config=job_config).result().to_dataframe()
    except DefaultCredentialsError:
        return pd.DataFrame()
    except Exception as exc:
        st.error(str(exc))
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_caged_options() -> Dict[str, List[Any]]:
    try:
        client = get_client()
        if client is None:
            return {
                'anos': [],
                'ufs': [],
                'secoes': [],
                'subclasses': [],
            }
    except DefaultCredentialsError:
        return {
            'anos': [],
            'ufs': [],
            'secoes': [],
            'subclasses': [],
        }
    project_id = get_config('BQ_PROJECT_ID', DEFAULT_PROJECT)
    dataset = get_config('BQ_DATASET_GOLD', DEFAULT_DATASET_GOLD)
    table = f"`{project_id}.{dataset}.caged_uf_mes`"
    cols = get_view_columns(table)
    has_secao = "cnae_secao" in cols

    secao_select = "cnae_secao," if has_secao else ""
    secao_agg = (
        "ARRAY_AGG(DISTINCT cnae_secao ORDER BY cnae_secao IGNORE NULLS) AS secoes,"
        if has_secao
        else "[] AS secoes,"
    )

    sql = f"""
    WITH base AS (
      SELECT
        ano,
        mes,
        sigla_uf,
        {secao_select}
        cnae_subclasse
      FROM {table}
      WHERE cnae_subclasse IS NOT NULL
        AND sigla_uf IS NOT NULL
        AND sigla_uf != ''
        AND ano IS NOT NULL
    )
    SELECT
      ARRAY_AGG(DISTINCT ano ORDER BY ano IGNORE NULLS) AS anos,
      ARRAY_AGG(DISTINCT sigla_uf ORDER BY sigla_uf IGNORE NULLS) AS ufs,
      {secao_agg}
      ARRAY_AGG(DISTINCT cnae_subclasse ORDER BY cnae_subclasse IGNORE NULLS) AS subclasses
    FROM base
    """
    try:
        df = client.query(sql).result().to_dataframe()
    except Exception as exc:
        st.error(str(exc))
        return {
            'anos': [],
            'ufs': [],
            'secoes': [],
            'subclasses': [],
        }
    if df.empty:
        return {
            'anos': [],
            'ufs': [],
            'secoes': [],
            'subclasses': [],
        }
    row = df.iloc[0]
    anos = row['anos']
    ufs = row['ufs']
    secoes = row['secoes']
    subclasses = row['subclasses']
    return {
        'anos': anos if anos is not None and len(anos) > 0 else [],
        'ufs': ufs if ufs is not None and len(ufs) > 0 else [],
        'secoes': [s for s in (secoes if secoes is not None else []) if s],
        'subclasses': [c for c in (subclasses if subclasses is not None else []) if c],
    }


@st.cache_data(show_spinner=False)
def load_rais_options() -> Dict[str, List[Any]]:
    try:
        client = get_client()
        if client is None:
            return {
                'anos': [],
                'ufs': [],
                'subclasses': [],
                'cnae2_list': [],
            }
    except DefaultCredentialsError:
        return {
            'anos': [],
            'ufs': [],
            'subclasses': [],
            'cnae2_list': [],
        }
    project_id = get_config('BQ_PROJECT_ID', DEFAULT_PROJECT)
    dataset = get_config('BQ_DATASET_GOLD', DEFAULT_DATASET_GOLD)
    table = f"`{project_id}.{dataset}.rais_uf_ano`"

    sql = f"""
    WITH base AS (
      SELECT
        ano,
        sigla_uf,
        cnae_subclasse,
        SUBSTR(REGEXP_REPLACE(cnae_subclasse, r'\\D', ''), 1, 2) AS cnae2
      FROM {table}
      WHERE cnae_subclasse IS NOT NULL
        AND sigla_uf IS NOT NULL
        AND sigla_uf != ''
        AND ano IS NOT NULL
    )
    SELECT
      ARRAY_AGG(DISTINCT ano ORDER BY ano IGNORE NULLS) AS anos,
      ARRAY_AGG(DISTINCT sigla_uf ORDER BY sigla_uf IGNORE NULLS) AS ufs,
      ARRAY_AGG(DISTINCT cnae_subclasse ORDER BY cnae_subclasse IGNORE NULLS) AS subclasses,
      ARRAY_AGG(DISTINCT cnae2 ORDER BY cnae2 IGNORE NULLS) AS cnae2_list
    FROM base
    WHERE cnae2 IS NOT NULL AND cnae2 != ''
    """
    try:
        df = client.query(sql).result().to_dataframe()
    except Exception as exc:
        st.error(str(exc))
        return {
            'anos': [],
            'ufs': [],
            'subclasses': [],
            'cnae2_list': [],
        }
    if df.empty:
        return {
            'anos': [],
            'ufs': [],
            'subclasses': [],
            'cnae2_list': [],
        }
    row = df.iloc[0]
    anos = row['anos']
    ufs = row['ufs']
    subclasses = row['subclasses']
    cnae2_list = row['cnae2_list']
    return {
        'anos': anos if anos is not None and len(anos) > 0 else [],
        'ufs': ufs if ufs is not None and len(ufs) > 0 else [],
        'subclasses': [c for c in (subclasses if subclasses is not None else []) if c],
        'cnae2_list': [c for c in (cnae2_list if cnae2_list is not None else []) if c],
    }


@st.cache_data(show_spinner=False)
def load_caged_months(ano: int) -> List[int]:
    client = get_client()
    if client is None:
        return []
    project_id = get_config('BQ_PROJECT_ID', DEFAULT_PROJECT)
    dataset = get_config('BQ_DATASET_GOLD', DEFAULT_DATASET_GOLD)
    table = f"`{project_id}.{dataset}.caged_uf_mes`"
    sql = f"""
    SELECT ARRAY_AGG(DISTINCT mes ORDER BY mes IGNORE NULLS) AS meses
    FROM {table}
    WHERE ano = @ano AND mes IS NOT NULL
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("ano", "INT64", ano)]
    )
    try:
        df = client.query(sql, job_config=job_config).result().to_dataframe()
    except Exception:
        return []
    if df.empty:
        return []
    meses = df.iloc[0]["meses"]
    return [int(m) for m in (meses if meses is not None else []) if m]


@st.cache_data(show_spinner=False)
def load_pnad_options() -> Dict[str, List[Any]]:
    client = get_client()
    if client is None:
        return {
            "anos": [],
            "ufs": [],
            "trimestres": [],
        }
    project_id = get_config("BQ_PROJECT_ID", DEFAULT_PROJECT)
    dataset = get_config("BQ_DATASET_GOLD", DEFAULT_DATASET_GOLD)
    table = f"`{project_id}.{dataset}.pnad_uf_trimestre`"
    sql = f"""
    SELECT
      ARRAY_AGG(DISTINCT ano ORDER BY ano IGNORE NULLS) AS anos,
      ARRAY_AGG(DISTINCT sigla_uf ORDER BY sigla_uf IGNORE NULLS) AS ufs,
      ARRAY_AGG(DISTINCT trimestre ORDER BY trimestre IGNORE NULLS) AS trimestres
    FROM {table}
    WHERE ano IS NOT NULL AND sigla_uf IS NOT NULL AND sigla_uf != ''
    """
    try:
        df = client.query(sql).result().to_dataframe()
    except Exception:
        return {
            "anos": [],
            "ufs": [],
            "trimestres": [],
        }
    if df.empty:
        return {
            "anos": [],
            "ufs": [],
            "trimestres": [],
        }
    row = df.iloc[0]
    return {
        "anos": [int(v) for v in (row["anos"] if row["anos"] is not None else [])],
        "ufs": [v for v in (row["ufs"] if row["ufs"] is not None else []) if v],
        "trimestres": [int(v) for v in (row["trimestres"] if row["trimestres"] is not None else [])],
    }


def render_filters_pnad() -> Dict[str, Any]:
    opts = load_pnad_options()
    anos = opts.get("anos", [])
    ufs = opts.get("ufs", [])
    trimestres = opts.get("trimestres", [])
    default_ano = anos[-1] if anos else 2022

    if not anos and not ufs:
        st.sidebar.info(t("filters_empty"))

    st.sidebar.header(t("filters_title"))
    ano = st.sidebar.selectbox(t("filter_year"), anos or [default_ano], index=(len(anos) - 1 if anos else 0))
    trimestre = st.sidebar.selectbox(t("col_trimestre"), trimestres or [0], index=(len(trimestres) - 1 if trimestres else 0))
    ufs_selected = st.sidebar.multiselect(t("filter_state"), ufs, default=[])

    return {
        "ano": int(ano),
        "trimestre": int(trimestre) if trimestre else 0,
        "ufs": ufs_selected,
    }


def render_filters_home() -> Dict[str, Any]:
    caged_opts = load_caged_options()
    rais_opts = load_rais_options()
    caged_years = caged_opts.get("anos", [])
    rais_years = rais_opts.get("anos", [])
    years = sorted({*caged_years, *rais_years})
    default_year = (max(years) if years else 2022)

    if not years:
        st.sidebar.info(t("filters_empty"))

    st.sidebar.header(t("filters_title"))
    ano = st.sidebar.selectbox(t("filter_year"), years or [default_year], index=(len(years) - 1 if years else 0))

    meses = load_caged_months(int(ano)) if caged_years else []
    mes = st.sidebar.selectbox(t("filter_month"), meses or [0], index=(len(meses) - 1 if meses else 0))

    ufs = sorted({*(caged_opts.get("ufs", []) or []), *(rais_opts.get("ufs", []) or [])})
    ufs_selected = st.sidebar.multiselect(t("filter_state"), ufs, default=[])

    secoes = sorted({s for s in (caged_opts.get("secoes", []) or []) if s})
    if not secoes:
        st.sidebar.info(t("caged_section_disabled"))
    secao_labels = [sector.secao_display_label(secao, t) for secao in secoes]
    secao_map = dict(zip(secao_labels, secoes))
    secao_selected_labels = st.sidebar.multiselect(t("filter_macro"), secao_labels, default=[])
    secao_selected = [secao_map[label] for label in secao_selected_labels]

    subclasses = sorted({*(caged_opts.get("subclasses", []) or []), *(rais_opts.get("subclasses", []) or [])})
    advanced = st.sidebar.expander(t("filter_advanced"), expanded=False)
    subclass_labels = [sector.format_cnae_subclasse(value) for value in subclasses]
    subclass_map = dict(zip(subclass_labels, subclasses))
    subclass_selected_labels = advanced.multiselect(t("filter_subclass"), subclass_labels, default=[])
    subclass_selected = [subclass_map[label] for label in subclass_selected_labels]

    return {
        "ano": int(ano),
        "mes": int(mes) if mes else 0,
        "ufs": ufs_selected,
        "caged_secoes": secao_selected,
        "caged_subclasses": subclass_selected,
        "rais_subclasses": subclass_selected,
    }


def render_filters_caged() -> Dict[str, Any]:
    opts = load_caged_options()
    anos = opts.get("anos", [])
    ufs = opts.get("ufs", [])
    secoes = opts.get("secoes", [])
    subclasses = opts.get("subclasses", [])
    default_ano = anos[-1] if anos else 2022

    if not anos and not ufs:
        st.sidebar.info(t("filters_empty"))

    st.sidebar.header(t("filters_title"))
    ano = st.sidebar.selectbox(t("filter_year"), anos or [default_ano], index=(len(anos) - 1 if anos else 0))
    meses = load_caged_months(int(ano)) if anos else []
    mes = st.sidebar.selectbox(t("filter_month"), meses or [0], index=(len(meses) - 1 if meses else 0))
    ufs_selected = st.sidebar.multiselect(t("filter_state"), ufs, default=[])

    if not secoes:
        st.sidebar.info(t("caged_section_disabled"))
    secao_labels = [sector.secao_display_label(secao, t) for secao in secoes]
    secao_map = dict(zip(secao_labels, secoes))
    secao_selected_labels = st.sidebar.multiselect(t("filter_macro"), secao_labels, default=[])
    secao_selected = [secao_map[label] for label in secao_selected_labels]

    advanced = st.sidebar.expander(t("filter_advanced"), expanded=False)
    subclass_labels = [sector.format_cnae_subclasse(value) for value in subclasses]
    subclass_map = dict(zip(subclass_labels, subclasses))
    subclass_selected_labels = advanced.multiselect(t("filter_subclass"), subclass_labels, default=[])
    subclass_selected = [subclass_map[label] for label in subclass_selected_labels]

    return {
        "ano": int(ano),
        "mes": int(mes) if mes else 0,
        "ufs": ufs_selected,
        "caged_secoes": secao_selected,
        "caged_subclasses": subclass_selected,
        "rais_subclasses": [],
    }


def render_filters_rais() -> Dict[str, Any]:
    opts = load_rais_options()
    anos = opts.get("anos", [])
    ufs = opts.get("ufs", [])
    subclasses = opts.get("subclasses", [])
    cnae2_list = opts.get("cnae2_list", [])
    default_ano = anos[-1] if anos else 2022

    if not anos and not ufs:
        st.sidebar.info(t("filters_empty"))

    st.sidebar.header(t("filters_title"))
    ano = st.sidebar.selectbox(t("filter_year"), anos or [default_ano], index=(len(anos) - 1 if anos else 0))
    ufs_selected = st.sidebar.multiselect(t("filter_state"), ufs, default=[])

    macro_keys = sector.available_macro_keys_from_cnae2_list(cnae2_list)
    macro_labels = [sector.macro_label_with_range(key, t) for key in macro_keys]
    macro_map = dict(zip(macro_labels, macro_keys))
    macro_selected_labels = st.sidebar.multiselect(t("filter_macro"), macro_labels, default=[])
    macro_selected = [macro_map[label] for label in macro_selected_labels]

    advanced = st.sidebar.expander(t("filter_advanced"), expanded=False)
    subclass_labels = [sector.format_cnae_subclasse(value) for value in subclasses]
    subclass_map = dict(zip(subclass_labels, subclasses))
    subclass_selected_labels = advanced.multiselect(t("filter_subclass"), subclass_labels, default=[])
    subclass_selected = [subclass_map[label] for label in subclass_selected_labels]

    return {
        "ano": int(ano),
        "mes": 0,
        "ufs": ufs_selected,
        "macro_keys": macro_selected,
        "caged_secoes": [],
        "caged_subclasses": [],
        "rais_subclasses": subclass_selected,
    }

    def is_empty(value: Any) -> bool:
        return value is None or len(value) == 0

    if is_empty(ufs) and is_empty(cnae2_list):
        st.sidebar.info(t('filters_empty'))

    st.sidebar.header(t('filters_title'))
    ano = st.sidebar.selectbox(t('filter_year'), anos or [default_ano], index=(len(anos) - 1 if anos else 0))
    ufs = st.sidebar.multiselect(t('filter_state'), ufs, default=[])

    available_groups = sector.available_groups(cnae2_list)
    all_label = t('option_all')
    sector_labels = [sector.sector_label(group, t) for group in available_groups]
    sector_options = [all_label] + sector_labels
    sector_choice = st.sidebar.selectbox(t('filter_sector'), sector_options, index=0)

    if sector_choice == all_label:
        subsetor_groups = available_groups
    else:
        subsetor_groups = [
            group for group in available_groups if sector.sector_label(group, t) == sector_choice
        ]
    subsetor_labels = [sector.subsetor_label(group, t) for group in subsetor_groups]
    subsetor_options = [all_label] + subsetor_labels
    subsetor_choice = st.sidebar.selectbox(t('filter_subsector'), subsetor_options, index=0)

    cnae_filters: List[str] = []
    selected_sector_label: Optional[str] = None
    selected_subsetor_label: Optional[str] = None
    if subsetor_choice != all_label:
        for group in subsetor_groups:
            if sector.subsetor_label(group, t) == subsetor_choice:
                cnae_filters = sector.codes_for_group(cnae2_list, group['key'])
                selected_sector_label = sector.sector_label(group, t)
                selected_subsetor_label = sector.subsetor_label(group, t)
                break
    elif sector_choice != all_label:
        for group in available_groups:
            if sector.sector_label(group, t) == sector_choice:
                cnae_filters = sector.codes_for_group(cnae2_list, group['key'])
                selected_sector_label = sector_choice
                break

    return {
        'ano': int(ano),
        'ufs': ufs,
        'cnae_level': 'CNAE2',
        'cnaes': cnae_filters,
        'setor_label': selected_sector_label,
        'subsetor_label': selected_subsetor_label,
    }


def build_params(
    filters: Dict[str, Any]
) -> Tuple[bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter, ...]:
    params: List[bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter] = [
        bigquery.ScalarQueryParameter("ano", "INT64", filters.get("ano", 0)),
        bigquery.ScalarQueryParameter("mes", "INT64", filters.get("mes", 0)),
        bigquery.ArrayQueryParameter("ufs", "STRING", filters.get("ufs", [])),
        bigquery.ArrayQueryParameter("caged_secoes", "STRING", filters.get("caged_secoes", [])),
        bigquery.ArrayQueryParameter("caged_subclasses", "STRING", filters.get("caged_subclasses", [])),
        bigquery.ArrayQueryParameter("rais_subclasses", "STRING", filters.get("rais_subclasses", [])),
    ]
    return tuple(params)


@st.cache_data(show_spinner=False)
def get_view_columns(view_fqn: str) -> Set[str]:
    view_name = view_fqn.replace("`", "")
    parts = view_name.split(".")
    if len(parts) != 3:
        return set()
    project_id, dataset, table = parts
    sql = f"""
    SELECT column_name
    FROM `{project_id}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = '{table}'
    """
    client = get_client()
    if client is None:
        return set()
    try:
        df = client.query(sql).result().to_dataframe()
    except Exception:
        return set()
    if df.empty:
        return set()
    return {str(name).lower() for name in df["column_name"].tolist() if name}


def run_query_checked(
    sql: str,
    params: Tuple[bigquery.ScalarQueryParameter | bigquery.ArrayQueryParameter, ...],
    required_columns_by_view: Dict[str, Iterable[str]],
) -> pd.DataFrame:
    for view_fqn, required_cols in required_columns_by_view.items():
        cols = get_view_columns(view_fqn)
        if not cols:
            st.warning(
                f"{t('view_missing_title')}: {view_fqn}. {t('view_missing_body')}"
            )
            return pd.DataFrame()
        missing = [col for col in required_cols if col.lower() not in cols]
        if missing:
            st.warning(
                f"{t('columns_missing_title')}: {view_fqn}. "
                f"{t('columns_missing_body')} {', '.join(missing)}"
            )
            return pd.DataFrame()
    return run_query(sql, params=params)


def diagnose_schema(
    dataset: str = DEFAULT_DATASET_GOLD,
    table_names: Optional[Iterable[str]] = None,
) -> Dict[str, List[str]]:
    names = list(table_names) if table_names is not None else []
    if not names:
        names = [
            "caged_uf_mes",
            "pnad_uf_trimestre",
            "rais_uf_ano",
            "gold_rais_opportunity_score",
            "gold_rais_profile_mix",
            "gold_rais_region_risk",
            "gold_rais_sector_year_metrics",
        ]
    project_id = get_config('BQ_PROJECT_ID', DEFAULT_PROJECT)
    client = get_client()
    if client is None:
        return {}
    sql = f"""
    SELECT
      table_name,
      column_name
    FROM `{project_id}.{dataset}.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name IN UNNEST(@tables)
    ORDER BY table_name, ordinal_position
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ArrayQueryParameter("tables", "STRING", names)]
    )
    try:
        df = client.query(sql, job_config=job_config).result().to_dataframe()
    except Exception:
        return {}
    schema: Dict[str, List[str]] = {}
    for _, row in df.iterrows():
        table = row.get("table_name")
        column = row.get("column_name")
        if table and column:
            schema.setdefault(str(table), []).append(str(column))
    return schema
