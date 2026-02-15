CREATE OR REPLACE VIEW `dados-mercado-brasil.gold.gold_rais_profile_quality` AS
WITH base AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    sexo,
    grupo_idade,
    grau_instrucao,
    SUM(vinculos) AS vinculos
  FROM `dados-mercado-brasil.gold.rais_uf_ano`
  GROUP BY ano, sigla_uf, cnae_subclasse, sexo, grupo_idade, grau_instrucao
),
totais AS (
  SELECT
    ano,
    sigla_uf,
    cnae_subclasse,
    SUM(vinculos) AS vinculos_total
  FROM base
  GROUP BY ano, sigla_uf, cnae_subclasse
),
instrucao_mix AS (
  SELECT
    b.ano,
    b.sigla_uf,
    b.cnae_subclasse,
    ARRAY_AGG(
      STRUCT(
        b.grau_instrucao AS grau_instrucao,
        SAFE_DIVIDE(b.vinculos, t.vinculos_total) AS participacao
      )
      ORDER BY b.grau_instrucao
    ) AS participacao_por_grau_instrucao,
    SAFE_DIVIDE(
      SUM(
        CASE
          WHEN UPPER(b.grau_instrucao) LIKE '%SUPERIOR%'
            OR UPPER(b.grau_instrucao) LIKE '%POS%'
            OR UPPER(b.grau_instrucao) LIKE '%MESTR%'
            OR UPPER(b.grau_instrucao) LIKE '%DOUT%'
          THEN b.vinculos
          ELSE 0
        END
      ),
      t.vinculos_total
    ) AS qualidade_forca_trabalho_pct
  FROM base b
  JOIN totais t
    ON b.ano = t.ano
   AND b.sigla_uf = t.sigla_uf
   AND b.cnae_subclasse = t.cnae_subclasse
  GROUP BY b.ano, b.sigla_uf, b.cnae_subclasse, t.vinculos_total
),
idade_mix AS (
  SELECT
    b.ano,
    b.sigla_uf,
    b.cnae_subclasse,
    ARRAY_AGG(
      STRUCT(
        b.grupo_idade AS grupo_idade,
        SAFE_DIVIDE(b.vinculos, t.vinculos_total) AS participacao
      )
      ORDER BY b.grupo_idade
    ) AS participacao_por_grupo_idade
  FROM base b
  JOIN totais t
    ON b.ano = t.ano
   AND b.sigla_uf = t.sigla_uf
   AND b.cnae_subclasse = t.cnae_subclasse
  GROUP BY b.ano, b.sigla_uf, b.cnae_subclasse, t.vinculos_total
)
SELECT
  i.ano,
  i.sigla_uf,
  i.cnae_subclasse,
  i.participacao_por_grau_instrucao,
  d.participacao_por_grupo_idade,
  i.qualidade_forca_trabalho_pct
FROM instrucao_mix i
JOIN idade_mix d
  ON i.ano = d.ano
 AND i.sigla_uf = d.sigla_uf
 AND i.cnae_subclasse = d.cnae_subclasse;
