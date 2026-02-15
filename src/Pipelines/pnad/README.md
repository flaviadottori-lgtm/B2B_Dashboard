# Pipeline PNAD/PNADc (scaffold)

Este diretório contém o scaffold para futura ingestão cloud-native dos microdados PNAD/PNADc.

- CLI: `python -m src.pipelines.pnad.run --competencia YYYY-MM`
- Ainda não há ingestão real: aguardando disponibilização dos microdados.
- O padrão será GCS (raw) -> BigQuery (stg/gold), idêntico ao pipeline CAGED.
- Placeholders para:
  - Download de fonte oficial
  - Schema mapping
  - Tabelas gold previstas: taxa_ocupacao_uf, renda_media_uf, informalidade_uf
- Tudo desabilitado por padrão para não quebrar o build.
