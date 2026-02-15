# Comandos GCP para automação cloud-native CAGED

## 1. Criar bucket raw
```
gsutil mb -l southamerica-east1 gs://<BUCKET_RAW>
```

## 2. Criar service account
```
gcloud iam service-accounts create caged-pipeline-sa --display-name "CAGED Pipeline Service Account"
```

## 3. Conceder permissões mínimas
```
gcloud projects add-iam-policy-binding <GCP_PROJECT> \
  --member="serviceAccount:caged-pipeline-sa@<GCP_PROJECT>.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
gcloud projects add-iam-policy-binding <GCP_PROJECT> \
  --member="serviceAccount:caged-pipeline-sa@<GCP_PROJECT>.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
gcloud projects add-iam-policy-binding <GCP_PROJECT> \
  --member="serviceAccount:caged-pipeline-sa@<GCP_PROJECT>.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

## 4. Build e deploy do Cloud Run Job
```
gcloud builds submit --tag gcr.io/<GCP_PROJECT>/caged-pipeline

gcloud run jobs create caged-pipeline-job \
  --image gcr.io/<GCP_PROJECT>/caged-pipeline \
  --region southamerica-east1 \
  --service-account caged-pipeline-sa@<GCP_PROJECT>.iam.gserviceaccount.com \
  --set-env-vars GCP_PROJECT=<GCP_PROJECT>,BQ_DATASET_STG=<BQ_DATASET_STG>,BQ_DATASET_GOLD=<BQ_DATASET_GOLD>,BQ_DATASET_META=<BQ_DATASET_META>,GCS_BUCKET_RAW=<BUCKET_RAW>,TIMEZONE=America/Fortaleza
```

## 5. Criar Cloud Scheduler para rodar mensalmente
```
gcloud scheduler jobs create http caged-pipeline-sched \
  --schedule="0 6 3 * *" \
  --uri="https://REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/<GCP_PROJECT>/jobs/caged-pipeline-job:run" \
  --http-method=POST \
  --oauth-service-account-email=caged-pipeline-sa@<GCP_PROJECT>.iam.gserviceaccount.com \
  --time-zone="America/Fortaleza"
```
