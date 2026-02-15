from __future__ import annotations

import os

BASE_PROJECT = os.getenv("BQ_PROJECT_ID", "dados-mercado-brasil")
BASE_DATASET = os.getenv("BQ_DATASET_GOLD", "gold")

TABLE_CAGED = f"`{BASE_PROJECT}.{BASE_DATASET}.caged_uf_mes`"
TABLE_PNAD = f"`{BASE_PROJECT}.{BASE_DATASET}.pnad_uf_trimestre`"
TABLE_RAIS = f"`{BASE_PROJECT}.{BASE_DATASET}.rais_uf_ano`"

VIEW_OPPORTUNITY = f"`{BASE_PROJECT}.{BASE_DATASET}.gold_rais_opportunity_score`"
VIEW_PROFILE = f"`{BASE_PROJECT}.{BASE_DATASET}.gold_rais_profile_mix`"
VIEW_REGION_RISK = f"`{BASE_PROJECT}.{BASE_DATASET}.gold_rais_region_risk`"
VIEW_SECTOR_YEAR = f"`{BASE_PROJECT}.{BASE_DATASET}.gold_rais_sector_year_metrics`"


def caged_filtered_sql() -> str:
    return f"""
    SELECT
      ano,
      mes,
      sigla_uf,
      cnae_secao,
      cnae_subclasse,
      admissoes,
      desligamentos,
      saldo,
      indice_volatilidade
    FROM {TABLE_CAGED}
    WHERE ano = @ano
      AND (@mes = 0 OR mes = @mes)
      AND (ARRAY_LENGTH(@ufs) = 0 OR sigla_uf IN UNNEST(@ufs))
      AND (ARRAY_LENGTH(@caged_secoes) = 0 OR cnae_secao IN UNNEST(@caged_secoes))
      AND (ARRAY_LENGTH(@caged_subclasses) = 0 OR cnae_subclasse IN UNNEST(@caged_subclasses))
    """


def rais_filtered_sql() -> str:
    return f"""
    WITH base AS (
      SELECT
        ano,
        sigla_uf,
        cnae_subclasse,
        vinculos,
        SUBSTR(REGEXP_REPLACE(cnae_subclasse, r'\\D', ''), 1, 2) AS cnae2
      FROM {TABLE_RAIS}
    ),
    filtered AS (
      SELECT *
      FROM base
      WHERE ano = @ano
        AND (ARRAY_LENGTH(@ufs) = 0 OR sigla_uf IN UNNEST(@ufs))
        AND (ARRAY_LENGTH(@rais_subclasses) = 0 OR cnae_subclasse IN UNNEST(@rais_subclasses))
    )
    SELECT * FROM filtered
    """


def opportunity_sql() -> str:
    return f"""
    WITH base AS (
      SELECT
        ano,
        sigla_uf,
        cnae_subclasse,
        vinculos,
        crescimento_vinculos_yoy,
        volatilidade_vinculos_5a,
        z_crescimento,
        z_tamanho,
        z_volatilidade,
        opportunity_score,
        score_percentil_ano,
        SUBSTR(REGEXP_REPLACE(cnae_subclasse, r'\\D', ''), 1, 2) AS cnae2
      FROM {VIEW_OPPORTUNITY}
    ),
    filtered AS (
      SELECT *
      FROM base
      WHERE ano = @ano
        AND (ARRAY_LENGTH(@ufs) = 0 OR sigla_uf IN UNNEST(@ufs))
        AND (ARRAY_LENGTH(@rais_subclasses) = 0 OR cnae_subclasse IN UNNEST(@rais_subclasses))
    )
    SELECT * FROM filtered
    """


def sector_year_sql() -> str:
    return f"""
    WITH base AS (
      SELECT
        ano,
        sigla_uf,
        cnae_subclasse,
        vinculos,
        crescimento_vinculos_yoy,
        volatilidade_vinculos_5a,
        SUBSTR(REGEXP_REPLACE(cnae_subclasse, r'\\D', ''), 1, 2) AS cnae2
      FROM {VIEW_SECTOR_YEAR}
    )
    SELECT *
    FROM base
    WHERE ano = @ano
      AND (ARRAY_LENGTH(@ufs) = 0 OR sigla_uf IN UNNEST(@ufs))
      AND (ARRAY_LENGTH(@rais_subclasses) = 0 OR cnae_subclasse IN UNNEST(@rais_subclasses))
    """


def region_risk_sql() -> str:
    return f"""
    SELECT
      ano,
      sigla_uf,
      vinculos_uf,
      crescimento_vinculos_uf_yoy,
      volatilidade_uf_5a,
      hhi_concentracao_setorial,
      top3_setores
    FROM {VIEW_REGION_RISK}
    WHERE ano = @ano
      AND (ARRAY_LENGTH(@ufs) = 0 OR sigla_uf IN UNNEST(@ufs))
    """


def profile_mix_sql() -> str:
    return f"""
    SELECT
      ano,
      sigla_uf,
      cnae_subclasse,
      sexo,
      grupo_idade,
      grau_instrucao,
      vinculos,
      vinculos_total,
      participacao,
      SUBSTR(REGEXP_REPLACE(cnae_subclasse, r'\\D', ''), 1, 2) AS cnae2
    FROM {VIEW_PROFILE}
    WHERE ano = @ano
      AND (ARRAY_LENGTH(@ufs) = 0 OR sigla_uf IN UNNEST(@ufs))
      AND (ARRAY_LENGTH(@rais_subclasses) = 0 OR cnae_subclasse IN UNNEST(@rais_subclasses))
    """


def pnad_sql() -> str:
    return f"""
    SELECT
      ano,
      trimestre,
      sigla_uf,
      sexo,
      grupo_idade,
      formalidade,
      `pessoas ` AS pessoas
    FROM {TABLE_PNAD}
    WHERE ano = @ano
      AND (ARRAY_LENGTH(@ufs) = 0 OR sigla_uf IN UNNEST(@ufs))
    """
