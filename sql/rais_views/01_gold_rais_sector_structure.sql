CREATE OR REPLACE VIEW `dados-mercado-brasil.gold.gold_rais_sector_structure` AS
WITH base AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    SUM(vinculos) AS vinculos
  FROM `dados-mercado-brasil.gold.rais_uf_ano`
  GROUP BY ano, sigla_uf, cnae_subclasse
),
uf_total AS (
  SELECT
    ano,
    sigla_uf,
    SUM(vinculos) AS vinculos_total_uf
  FROM base
  GROUP BY ano, sigla_uf
)
SELECT
  b.ano,
  b.sigla_uf,
  b.cnae_subclasse,
  b.vinculos,
  SAFE_DIVIDE(b.vinculos, u.vinculos_total_uf) AS share_setor_na_uf,
  LOG(1 + b.vinculos) AS log_vinculos
FROM base b
JOIN uf_total u
  ON b.ano = u.ano
 AND b.sigla_uf = u.sigla_uf;
