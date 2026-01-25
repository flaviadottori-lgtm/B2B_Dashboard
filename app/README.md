# Market Opportunity Dashboard (BigQuery)

## Overview
Streamlit app that reads directly from BigQuery tables and views (CAGED, RAIS, PNAD).
Language support: Portuguese and English via sidebar selector.

## Data Sources (BigQuery)
- Base tables:
  - `dados-mercado-brasil.gold.caged_uf_mes`
  - `dados-mercado-brasil.gold.rais_uf_ano`
  - `dados-mercado-brasil.gold.pnad_uf_trimestre`
- Views:
  - `gold_rais_sector_year_metrics`
  - `gold_rais_region_risk`
  - `gold_rais_profile_mix`
  - `gold_rais_opportunity_score`

## How to run
1) Set credentials:
```
set GOOGLE_APPLICATION_CREDENTIALS=C:\\path\\to\\service-account.json
```
2) (Optional) set project/dataset overrides using Streamlit secrets or env vars:
```
set BQ_PROJECT_ID=dados-mercado-brasil
set BQ_DATASET_GOLD=gold
```
3) Install requirements and run:
```
pip install -r app/requirements.txt
streamlit run app/main.py
```

## Notes
- No CNAE description table is available in this repo. Subclasse labels show codes only.
- Add a `dim_cnae` later for friendly sector descriptions.
