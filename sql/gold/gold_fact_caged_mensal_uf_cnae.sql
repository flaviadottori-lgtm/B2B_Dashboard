-- Tabela gold: agregação mensal CAGED por UF e CNAE
CREATE OR REPLACE TABLE `${BQ_DATASET_GOLD}.fact_caged_mensal_uf_cnae`
PARTITION BY competencia
CLUSTER BY uf, cnae
AS
SELECT
  competencia,
  uf,
  cnae,
  SUM(admissoes) AS admissoes,
  SUM(desligamentos) AS desligamentos,
  SUM(saldo) AS saldo,
  SAFE_DIVIDE(SUM(saldo), NULLIF(SUM(admissoes),0)) AS saldo_pct,
  AVG(saldo) OVER (PARTITION BY uf, cnae ORDER BY competencia ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS media_movel_3m,
  AVG(saldo) OVER (PARTITION BY uf, cnae ORDER BY competencia ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS media_movel_12m,
  STDDEV(saldo) OVER (PARTITION BY uf, cnae ORDER BY competencia ROWS BETWEEN 11 PRECEDING AND CURRENT ROW) AS volatilidade_12m
FROM `${BQ_DATASET_STG}.stg_caged_movimentacoes`
WHERE competencia = @competencia
GROUP BY competencia, uf, cnae
