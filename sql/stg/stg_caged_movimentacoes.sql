-- Criação da tabela staging para CAGED
CREATE OR REPLACE TABLE `${BQ_DATASET_STG}.stg_caged_movimentacoes`
PARTITION BY DATE(competencia)
CLUSTER BY uf, cnae
AS
SELECT
  PARSE_DATE('%Y-%m', competencia) AS competencia,
  SAFE_CAST(uf AS STRING) AS uf,
  SAFE_CAST(cnae AS STRING) AS cnae,
  SAFE_CAST(municipio AS STRING) AS municipio,
  SAFE_CAST(admissoes AS INT64) AS admissoes,
  SAFE_CAST(desligamentos AS INT64) AS desligamentos,
  SAFE_CAST(saldo AS INT64) AS saldo
FROM
  EXTERNAL_QUERY(
    'connection_id',
    '''SELECT * FROM ...''' -- Substituir pelo caminho Parquet/CSV no GCS
  );
