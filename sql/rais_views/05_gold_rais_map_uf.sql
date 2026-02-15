CREATE OR REPLACE VIEW `dados-mercado-brasil.gold.gold_rais_map_uf` AS
WITH sector_base AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    SUM(vinculos) AS total_vinculos
  FROM `dados-mercado-brasil.gold.gold_rais_sector_year_metrics`
  GROUP BY ano, sigla_uf, cnae_subclasse
),
sector_labeled AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    total_vinculos,
    CASE
      WHEN cnae2 BETWEEN 1 AND 3 THEN 'Agro'
      WHEN cnae2 BETWEEN 10 AND 33 THEN 'Industria'
      WHEN cnae2 BETWEEN 41 AND 43 THEN 'Construcao'
      WHEN cnae2 BETWEEN 45 AND 47 THEN 'Comercio'
      WHEN cnae2 BETWEEN 49 AND 53 THEN 'Transporte e Logistica'
      WHEN cnae2 = 84 THEN 'Administracao Publica'
      WHEN cnae2 BETWEEN 55 AND 96 THEN 'Servicos'
      ELSE 'Outros'
    END AS setor_label
  FROM (
    SELECT
      ano,
      sigla_uf,
      cnae_subclasse,
      total_vinculos,
      SAFE_CAST(SUBSTR(REGEXP_REPLACE(cnae_subclasse, r'\D', ''), 1, 2) AS INT64) AS cnae2
    FROM sector_base
  )
),
opportunity AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    score_oportunidade AS opportunity_score
  FROM `dados-mercado-brasil.gold.gold_rais_opportunity_score`
),
risk AS (
  SELECT
    ano,
    sigla_uf,
    risco_score,
    indice_diversificacao
  FROM `dados-mercado-brasil.gold.gold_rais_region_risk`
)
SELECT
  s.ano,
  s.sigla_uf,
  s.setor_label,
  SUM(s.total_vinculos) AS total_vinculos,
  AVG(o.opportunity_score) AS opportunity_score,
  AVG(r.indice_diversificacao) AS indice_diversificacao,
  AVG(r.risco_score) AS risco_score
FROM sector_labeled s
LEFT JOIN opportunity o
  ON s.ano = o.ano
 AND s.sigla_uf = o.sigla_uf
 AND s.cnae_subclasse = o.cnae_subclasse
LEFT JOIN risk r
  ON s.ano = r.ano
 AND s.sigla_uf = r.sigla_uf
GROUP BY s.ano, s.sigla_uf, s.setor_label;
