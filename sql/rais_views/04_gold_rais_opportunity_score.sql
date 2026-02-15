CREATE OR REPLACE VIEW `dados-mercado-brasil.gold.gold_rais_opportunity_score` AS
WITH sector AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    log_vinculos
  FROM `dados-mercado-brasil.gold.gold_rais_sector_structure`
),
conc AS (
  SELECT
    ano,
    sigla_uf,
    indice_diversificacao
  FROM `dados-mercado-brasil.gold.gold_rais_region_concentration`
),
qual AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    qualidade_forca_trabalho_pct
  FROM `dados-mercado-brasil.gold.gold_rais_profile_quality`
),
base AS (
  SELECT
    s.ano,
    s.sigla_uf,
    s.cnae_subclasse,
    s.log_vinculos,
    c.indice_diversificacao,
    q.qualidade_forca_trabalho_pct
  FROM sector s
  LEFT JOIN conc c
    ON s.ano = c.ano
   AND s.sigla_uf = c.sigla_uf
  LEFT JOIN qual q
    ON s.ano = q.ano
   AND s.sigla_uf = q.sigla_uf
   AND s.cnae_subclasse = q.cnae_subclasse
),
z AS (
  SELECT
    *,
    SAFE_DIVIDE(
      log_vinculos - AVG(log_vinculos) OVER (PARTITION BY ano),
      NULLIF(STDDEV_POP(log_vinculos) OVER (PARTITION BY ano), 0)
    ) AS z_log_vinculos,
    SAFE_DIVIDE(
      indice_diversificacao - AVG(indice_diversificacao) OVER (PARTITION BY ano),
      NULLIF(STDDEV_POP(indice_diversificacao) OVER (PARTITION BY ano), 0)
    ) AS z_indice_diversificacao,
    SAFE_DIVIDE(
      qualidade_forca_trabalho_pct - AVG(qualidade_forca_trabalho_pct) OVER (PARTITION BY ano),
      NULLIF(STDDEV_POP(qualidade_forca_trabalho_pct) OVER (PARTITION BY ano), 0)
    ) AS z_qualidade_forca_trabalho
  FROM base
)
SELECT
  ano,
  sigla_uf,
  cnae_subclasse,
  log_vinculos,
  indice_diversificacao,
  qualidade_forca_trabalho_pct,
  z_log_vinculos,
  z_indice_diversificacao,
  z_qualidade_forca_trabalho,
  (0.5 * z_log_vinculos) + (0.3 * z_indice_diversificacao) + (0.2 * z_qualidade_forca_trabalho) AS score_oportunidade,
  NTILE(100) OVER (PARTITION BY ano ORDER BY (0.5 * z_log_vinculos) + (0.3 * z_indice_diversificacao) + (0.2 * z_qualidade_forca_trabalho)) AS percentil_score
FROM z;
