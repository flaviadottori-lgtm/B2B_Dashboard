CREATE OR REPLACE VIEW `dados-mercado-brasil.gold.gold_rais_region_concentration` AS
WITH sector_shares AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    vinculos,
    share_setor_na_uf
  FROM `dados-mercado-brasil.gold.gold_rais_sector_structure`
)
SELECT
  ano,
  sigla_uf,
  SUM(vinculos) AS vinculos_total_uf,
  SUM(POW(share_setor_na_uf, 2)) AS hhi_concentracao_setorial,
  SAFE_DIVIDE(1, SUM(POW(share_setor_na_uf, 2))) AS indice_diversificacao
FROM sector_shares
GROUP BY ano, sigla_uf;
