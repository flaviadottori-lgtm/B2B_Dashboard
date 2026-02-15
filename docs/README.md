# B2B Opportunity Engine - Cloud-Native Pipeline

## Como executar o pipeline CAGED

### Local
1. Configure as variáveis de ambiente:
   - GCP_PROJECT, BQ_DATASET_STG, BQ_DATASET_GOLD, BQ_DATASET_META, GCS_BUCKET_RAW, TIMEZONE
2. Instale dependências: `pip install -r requirements.txt`
3. Execute: `python -m src.pipelines.caged.run --competencia YYYY-MM`

### Cloud Run
- Siga os comandos em `/infra/gcp/gcloud_commands.md` para build, deploy e agendamento.
- O job será executado mensalmente via Cloud Scheduler.

## Observabilidade
- Logs estruturados (JSON) no stdout
- run_id único por execução
- Métricas: tempo de download, tempo de load, linhas carregadas

## PNAD/PNADc
- Scaffold pronto em `src/pipelines/pnad/` aguardando microdados
