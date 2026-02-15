# Architecture (Phase 1)

This project delivers a **territorial + sectoral opportunity engine** for Brazil using
local DuckDB as the default runtime and an optional BigQuery mode.

## Data Layers

- **Raw**: source extracts (IBGE, CAGED, PNAD, RAIS) in `data/raw/`.
- **Processed**: cleaned/standardized parquet tables in `data/processed/`.
- **Gold (Marts)**: analytical aggregates and curated views in `data/marts/` (DuckDB).

## Default Runtime (Local)

- **DuckDB**: `data/marts/b2b.duckdb`
- **Streamlit app**: `streamlit run app.py` (imports `dashboards/app.py`)

The dashboard reads aggregated tables from DuckDB:

- `companies_agg`
- `caged_state_sector_year`
- `opportunity_scores`
- `pnad` / `pnad_enriched` (when built)

## Optional Runtime (BigQuery)

The BigQuery Streamlit app lives in `app/main.py` and connects to:

- `dados-mercado-brasil.gold.caged_uf_mes`
- `dados-mercado-brasil.gold.rais_uf_ano`
- `dados-mercado-brasil.gold.pnad_uf_trimestre`

This mode is optional and documented in the README.

## Opportunity Score (Phase 1)

The Opportunity Score is a **structural index** built from IBGE-based aggregates.
It is designed to be **comparable across states** and **explainable** (no black box).
See README for a high-level explanation.

