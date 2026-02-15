# Corrige NameError para duckdb
# Corrige NameError para Path
from pathlib import Path

import duckdb

"""
Utilitários para carregamento e validação de dados.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Union

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def load_parquet_safe(path: Union[str, Path]) -> Optional[pd.DataFrame]:
    """
    Carrega arquivo Parquet de forma segura com tratamento de erro detalhado.

    Args:
        path: Caminho do arquivo parquet (str ou Path)

    Returns:
        DataFrame ou None se arquivo não existir ou houver exceção
    """
    # Converter para Path se necessário
    if not isinstance(path, Path):
        path = Path(path)

    # Resolver caminho absoluto para mensagens
    abs_path = path.resolve()

    # Verificar se arquivo existe
    if not path.exists():
        msg = f"❌ Arquivo parquet não encontrado: {abs_path}"
        logger.warning(msg)
        st.error(msg)
        return None

    # Tentar carregar
    try:
        df = pd.read_parquet(path, engine="pyarrow")
        success_msg = f"✅ Parquet carregado: {abs_path} ({len(df)} linhas)"
        logger.info(success_msg)
        return df
    except Exception as e:
        error_msg = f"❌ Erro ao carregar parquet\n**Caminho:** {abs_path}\n**Tipo:** {type(e).__name__}\n**Mensagem:** {str(e)}"
        logger.error(f"[ERRO] {error_msg}")
        st.error(error_msg)
        return None


def load_geojson_safe(path: Union[str, Path]) -> Optional[dict]:
    """
    Carrega arquivo GeoJSON de forma segura com tratamento de erro detalhado.

    Args:
        path: Caminho do arquivo geojson (str ou Path)

    Returns:
        Dict com GeoJSON ou None se arquivo não existir ou houver exceção
    """
    # Converter para Path se necessário
    if not isinstance(path, Path):
        path = Path(path)

    # Resolver caminho absoluto para mensagens
    abs_path = path.resolve()

    # Verificar se arquivo existe
    if not path.exists():
        msg = f"❌ Arquivo GeoJSON não encontrado: {abs_path}"
        logger.warning(msg)
        st.error(msg)
        return None

    # Tentar carregar
    try:
        with open(path, "r", encoding="utf-8") as f:
            geo = json.load(f)
        success_msg = f"✅ GeoJSON carregado: {abs_path}"
        logger.info(success_msg)
        return geo
    except Exception as e:
        error_msg = f"❌ Erro ao carregar GeoJSON\n**Caminho:** {abs_path}\n**Tipo:** {type(e).__name__}\n**Mensagem:** {str(e)}"
        logger.error(f"[ERRO] {error_msg}")
        st.error(error_msg)
        return None


def validate_dataframe(
    df: pd.DataFrame, required_columns: list[str], name: str = "DataFrame"
) -> bool:
    """
    Valida se DataFrame possui colunas obrigatórias.

    Args:
        df: DataFrame a validar
        required_columns: Lista de colunas obrigatórias
        name: Nome do dataset para mensagens

    Returns:
        True se válido, False caso contrário
    """
    if df is None or df.empty:
        logger.warning(f"{name} está vazio ou None")
        return False

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        logger.error(
            f"{name} - Colunas faltando: {missing}\n" f"Colunas disponíveis: {list(df.columns)}"
        )
        return False

    logger.info(f"[OK] {name} validado com sucesso ({len(df)} linhas)")
    return True


def load_pnad_data(pnad_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """
    Carrega dados PNAD Contínua via DuckDB, faz join com dim_uf e retorna uf (string).
    """
    try:
        from src.utils.duckdb_client import get_con

        con = get_con()
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        if "pnad_enriched" in tables:
            df = con.execute("SELECT * FROM pnad_enriched").df()
            source = "pnad_enriched"
        elif "pnad" in tables:
            df = con.execute("SELECT * FROM pnad").df()
            source = "pnad"
        else:
            logger.warning("PNAD não encontrada no DuckDB!")
            return None
        if df.empty:
            logger.warning(f"PNAD ({source}) via DuckDB retornou vazio!")
            return None
        # Validar colunas obrigatórias
        required_cols = ["ano", "cod_uf", "gender", "age_group", "value"]
        if not validate_dataframe(df, required_cols, name=f"PNAD ({source})"):
            return None
        # Conversão de tipos
        df = df.dropna(subset=["ano", "value"])
        df["ano"] = df["ano"].astype("int64")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        logger.info(f"[OK] PNAD ({source}) via DuckDB carregado: {len(df)} linhas")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar PNAD via DuckDB: {e}")
        return None


def load_pnad_metrics_data(metrics_path: Optional[Path] = None) -> Optional[pd.DataFrame]:
    """
    Carrega dados PNAD Contínua v2.0 com métricas avançadas (informalidade, renda, desemprego).

    Args:
        metrics_path: Caminho do arquivo parquet com métricas.
                     Se None, usa default: data/marts/pnad/pnad_uf_trimestre_sexo_idade_metrics.parquet

    Returns:
        DataFrame com dados PNAD + métricas ou None se arquivo não existir/inválido

    Raises:
        FileNotFoundError: Se arquivo não existir (log informativo)
    """
    if metrics_path is None:
        metrics_path = (
            Path(__file__).parent.parent.parent
            / "data"
            / "marts"
            / "pnad"
            / "pnad_uf_trimestre_sexo_idade_metrics.parquet"
        )

    if not isinstance(metrics_path, Path):
        metrics_path = Path(metrics_path)

    # Carregar arquivo
    df = load_parquet_safe(metrics_path)
    if df is None:
        logger.warning(
            f"Arquivo com métricas PNAD v2.0 não encontrado: {metrics_path}\n"
            "Execute: python run_pnad_metrics_pipeline.py"
        )
        return None

    # Validar colunas obrigatórias para v2.0
    required_cols = [
        "ano",
        "trimestre",
        "uf_code",
        "sexo",
        "grupo_idade",
        "populacao",
        "forca_trabalho",
        "ocupados",
        "desocupados",
        "ocupados_informais",
        "taxa_informalidade",
        "taxa_desemprego",
        "renda_media_trabalho",
    ]
    if not validate_dataframe(df, required_cols, name="PNAD Metrics"):
        return None

    # Garantir tipos corretos
    try:
        df = df.dropna(subset=["ano", "trimestre", "populacao"])

        if df.empty:
            logger.warning("PNAD Metrics vazio após remover NAs")
            return df

        # Conversão de tipos
        df["ano"] = df["ano"].astype("int64")
        df["trimestre"] = df["trimestre"].astype("int64")
        df["populacao"] = df["populacao"].astype("int64")
        df["forca_trabalho"] = df["forca_trabalho"].astype("int64")
        df["ocupados"] = df["ocupados"].astype("int64")
        df["desocupados"] = df["desocupados"].astype("int64")
        df["ocupados_informais"] = df["ocupados_informais"].astype("int64")
        df["taxa_informalidade"] = pd.to_numeric(df["taxa_informalidade"], errors="coerce")
        df["taxa_desemprego"] = pd.to_numeric(df["taxa_desemprego"], errors="coerce")
        df["renda_media_trabalho"] = pd.to_numeric(df["renda_media_trabalho"], errors="coerce")

        # Garantir coluna UF para a UI (derivada de uf_code)
        if "uf" not in df.columns and "uf_code" in df.columns:
            ibge_uf_map = {
                11: "RO",
                12: "AC",
                13: "AM",
                14: "RR",
                15: "PA",
                16: "AP",
                17: "TO",
                21: "MA",
                22: "PI",
                23: "CE",
                24: "RN",
                25: "PB",
                26: "PE",
                27: "AL",
                28: "SE",
                29: "BA",
                31: "MG",
                32: "ES",
                33: "RJ",
                35: "SP",
                41: "PR",
                42: "SC",
                43: "RS",
                50: "MS",
                51: "MT",
                52: "GO",
                53: "DF",
            }
            df["uf"] = df["uf_code"].map(ibge_uf_map)

        # Validar ranges de taxas
        invalid_rates = ((df["taxa_informalidade"] < 0) | (df["taxa_informalidade"] > 1)) | (
            (df["taxa_desemprego"] < 0) | (df["taxa_desemprego"] > 1)
        )

        if invalid_rates.any():
            logger.warning(f"{invalid_rates.sum()} linhas com taxas fora do intervalo [0, 1]")
            df = df[~invalid_rates]

        logger.info(f"[OK] PNAD Metrics carregado com sucesso: {len(df)} linhas após tratamento")
    except Exception as e:
        logger.error(f"Erro ao converter tipos PNAD Metrics: {e}")
        return None

    return df


def load_pnad(con):
    """
    Carrega dados PNAD Contínua a partir de arquivos Parquet ou CSV na pasta de dados processados.

    Tenta detectar e carregar a tabela PNAD a partir de arquivos na pasta `data/processed`.
    Se múltiplos arquivos forem encontrados, o carregamento será feito a partir do primeiro arquivo válido.

    Args:
        con: Conexão DuckDB ativa

    Returns:
        None

    Raises:
        Exception: Se houver erro genérico durante o carregamento
    """
    ROOT = Path(__file__).resolve().parents[2]
    DATA_PROCESSED = ROOT / "data" / "processed"
    candidates = [
        DATA_PROCESSED / "pnad_uf_quarter_gender_age.parquet",
        DATA_PROCESSED / "pnad_uf_quarter_gender_age.csv",
    ]
    if not any(f.exists() for f in candidates):
        candidates += sorted(DATA_PROCESSED.glob("pnad*.parquet"))
        candidates += sorted(DATA_PROCESSED.glob("pnad*.csv"))
    schema = {
        "ano": "Int64",
        "quarter": "string",
        "cod_uf": "Int64",
        "gender": "string",
        "age_group": "string",
        "value": "float64",
    }
    for file in candidates:
        if file.exists():
            try:
                if file.suffix == ".parquet":
                    df = pd.read_parquet(file)
                elif file.suffix == ".csv":
                    df = pd.read_csv(file)
                else:
                    continue
                col_map = {
                    "uf_code": "cod_uf",
                    "grupo_idade": "age_group",
                    "sexo": "gender",
                    "trimestre": "quarter",
                }
                df = df.rename(columns=col_map)
                for col, dtype in schema.items():
                    if col not in df.columns:
                        df[col] = pd.NA
                    df[col] = df[col].astype(dtype)
                df = df[list(schema.keys())]
                con.register("df_pnad", df)
                con.execute("CREATE OR REPLACE TABLE pnad AS SELECT * FROM df_pnad")
                return
            except Exception:
                continue
    col_defs = ",\n    ".join(
        [
            "ano INTEGER",
            "quarter VARCHAR",
            "cod_uf INTEGER",
            "gender VARCHAR",
            "age_group VARCHAR",
            "value DOUBLE",
        ]
    )
    con.execute(f"""
        CREATE OR REPLACE TABLE pnad (
            {col_defs}
        )
    """)


# ======================================================
# BACKEND-AWARE LOADERS (DuckDB / BigQuery)
# ======================================================
def _bq_table_fqn(project: str, dataset: str, table: str) -> str:
    return f"`{project}.{dataset}.{table}`"


def load_companies_agg(backend: str = "duckdb") -> pd.DataFrame:
    try:
        if backend == "bigquery":
            from src.config import Settings
            from src.utils.bigquery_client import query_df

            settings = Settings()
            if not settings.bq_project or not settings.bq_dataset_gold:
                logger.error("BQ_PROJECT ou BQ_DATASET_GOLD não configurados.")
                return pd.DataFrame()
            sql = f"SELECT * FROM {_bq_table_fqn(settings.bq_project, settings.bq_dataset_gold, settings.bq_table_companies)}"
            return query_df(sql, project=settings.bq_project, location=settings.bq_location)
        # DuckDB
        from src.utils.duckdb_client import get_con

        con = get_con()
        return con.execute("SELECT * FROM companies_agg").df()
    except Exception as exc:
        logger.error(f"Erro em load_companies_agg ({backend}): {exc}")
        return pd.DataFrame()


def load_opportunity_scores(backend: str = "duckdb") -> pd.DataFrame:
    try:
        if backend == "bigquery":
            from src.config import Settings
            from src.utils.bigquery_client import query_df

            settings = Settings()
            if not settings.bq_project or not settings.bq_dataset_gold:
                logger.error("BQ_PROJECT ou BQ_DATASET_GOLD não configurados.")
                return pd.DataFrame()
            sql = f"SELECT * FROM {_bq_table_fqn(settings.bq_project, settings.bq_dataset_gold, settings.bq_table_opportunity)}"
            return query_df(sql, project=settings.bq_project, location=settings.bq_location)
        from src.utils.duckdb_client import get_con

        con = get_con()
        return con.execute("SELECT * FROM opportunity_scores").df()
    except Exception as exc:
        logger.error(f"Erro em load_opportunity_scores ({backend}): {exc}")
        return pd.DataFrame()


def load_caged_state_sector_year(backend: str = "duckdb") -> pd.DataFrame:
    try:
        if backend == "bigquery":
            from src.config import Settings
            from src.utils.bigquery_client import query_df

            settings = Settings()
            if not settings.bq_project or not settings.bq_dataset_gold:
                logger.error("BQ_PROJECT ou BQ_DATASET_GOLD não configurados.")
                return pd.DataFrame()
            sql = f"SELECT * FROM {_bq_table_fqn(settings.bq_project, settings.bq_dataset_gold, settings.bq_table_caged)}"
            return query_df(sql, project=settings.bq_project, location=settings.bq_location)
        from src.utils.duckdb_client import get_con

        con = get_con()
        return con.execute("SELECT * FROM caged_state_sector_year").df()
    except Exception as exc:
        logger.error(f"Erro em load_caged_state_sector_year ({backend}): {exc}")
        return pd.DataFrame()


def load_pnad_metrics(backend: str = "duckdb") -> pd.DataFrame:
    try:
        if backend == "bigquery":
            from src.config import Settings
            from src.utils.bigquery_client import query_df

            settings = Settings()
            if not settings.bq_project or not settings.bq_dataset_gold:
                logger.error("BQ_PROJECT ou BQ_DATASET_GOLD não configurados.")
                return pd.DataFrame()
            sql = f"SELECT * FROM {_bq_table_fqn(settings.bq_project, settings.bq_dataset_gold, settings.bq_table_pnad_metrics)}"
            return query_df(sql, project=settings.bq_project, location=settings.bq_location)
        # DuckDB -> parquet metrics
        df = load_pnad_metrics_data()
        return df if df is not None else pd.DataFrame()
    except Exception as exc:
        logger.error(f"Erro em load_pnad_metrics ({backend}): {exc}")
        return pd.DataFrame()


def load_rais_metrics(backend: str = "duckdb") -> pd.DataFrame:
    try:
        if backend == "bigquery":
            from src.config import Settings
            from src.utils.bigquery_client import query_df

            settings = Settings()
            if not settings.bq_project or not settings.bq_dataset_gold:
                logger.error("BQ_PROJECT ou BQ_DATASET_GOLD não configurados.")
                return pd.DataFrame()
            sql = f"SELECT * FROM {_bq_table_fqn(settings.bq_project, settings.bq_dataset_gold, settings.bq_table_rais_metrics)}"
            return query_df(sql, project=settings.bq_project, location=settings.bq_location)
        return pd.DataFrame()
    except Exception as exc:
        logger.error(f"Erro em load_rais_metrics ({backend}): {exc}")
        return pd.DataFrame()
