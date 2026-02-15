# B2B Opportunity Engine  
## Data Systems & Economic Intelligence Platform

Data engineering project focused on transforming Brazilian public economic and labor datasets into structured analytical data marts and explainable opportunity scoring models.

---

## Overview

This repository emphasizes:

- End-to-end data pipelines  
- Modular ETL architecture  
- Analytical modeling  
- Data quality validation  
- Parquet-based data lake  
- Local (DuckDB) and cloud (BigQuery) query layers  

---

## 1. Architectural Overview

The platform is structured in analytical layers:

Raw Public Data
↓
Ingestion & Cleaning Pipelines
↓
Normalization & Aggregation
↓
Feature Engineering
↓
Opportunity Scoring Model
↓
Analytical Data Marts (Parquet / DuckDB / BigQuery)
↓
Visualization Layer (Streamlit – optional)


**Core objective:**  
Convert heterogeneous public datasets into consistent, comparable, and explainable economic intelligence assets.

---

## 2. Data Sources

The engine integrates structured Brazilian public datasets:

- **IBGE** (economic structure tables 3274 / 3275)  
- **CAGED** (employment flows)  
- **RAIS** (formal employment snapshot)  
- **CNPJ** (business registry structure)  
- **PNAD** (household labor data, optional modules)  

These datasets differ in:

- Frequency  
- Schema design  
- Aggregation level  
- Update cycle  

The engine standardizes them into analytical-ready tables.

---

## 3. Core Components

### 3.1 ETL Pipelines

Located in `src/pipelines/`

**Responsibilities:**

- Automated ingestion  
- Schema validation  
- Data cleaning and normalization  
- UF standardization  
- Sector harmonization  
- Year and period consistency checks  
- Parquet export  

**Key design principles:**

- Deterministic transformations  
- Idempotent runs  
- Explicit logging  
- Separation of raw vs processed data  

---

### 3.2 Analytical Data Lake

**Format:** Parquet  
**Storage:** `data/processed/`

**Why Parquet:**

- Columnar storage  
- Efficient aggregations  
- Lightweight local analytics  
- Compatibility with DuckDB and BigQuery  

**Generated analytical datasets include:**

- `ibge_3274_3275_tidy.parquet`  
- `caged_state_sector_year.parquet`  
- `caged_state_sector_month.parquet`  
- `companies_agg.parquet`  
- `opportunity_scores.parquet`  
- `opportunity_scores_v3.parquet`  

---

### 3.3 Opportunity Scoring Engine

Located in `src/scoring/`

The Opportunity Score is a structural composite index based on:

- Economic intensity  
- Sectoral distribution  
- Business density  
- Relative comparability across states  

**Design characteristics:**

- Explainable components  
- No black-box ML dependency  
- Transparent weighting  
- Comparable across UFs  
- Reproducible logic  

The model is structural, not predictive.

---

### 3.4 Query Layer

Two query backends supported:

#### DuckDB (Default)

Local analytical engine.

**Advantages:**

- Zero infrastructure  
- Fast aggregation  
- Ideal for prototyping  

#### BigQuery (Optional)

Cloud execution layer.

**Used for:**

- Scalable aggregation  
- View materialization  
- Cloud-ready deployment  

SQL definitions are stored in:

sql/


---

## 4. Repository Structure

B2B_Dashboard/
│
├── src/
│ ├── config/
│ ├── core/
│ ├── scoring/
│ ├── utils/
│ └── pipelines/
│
├── dashboards/ # Visualization layer (optional)
│
├── data/
│ ├── geo/
│ ├── processed/ # Analytical marts (Parquet)
│ └── raw/ # Source data (not versioned in production)
│
├── sql/
├── tests/
├── docs/
├── infra/
│
├── requirements.txt
├── pyproject.toml
└── README.md


---

## 5. Data Engineering Practices Applied

- Modular pipeline design  
- Separation of ingestion and transformation layers  
- Parquet-based data lake  
- Environment variable configuration (`.env`)  
- Type hints and structured logging  
- Reproducible builds  
- Unit tests for transformation logic  
- Backend abstraction (DuckDB / BigQuery)  

---

## 6. Execution

### Local Setup

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate    # Linux/Mac
pip install -r requirements.txt
Run Pipelines
python run_pnad_pipeline.py
python run_pnad_metrics_pipeline.py
Launch Dashboard (Optional Layer)
streamlit run app.py
7. Data Flow Governance
Raw data is never overwritten.
Processed data is stored in versionable Parquet outputs.

Recommended:

Ignore data/raw/ in version control

Version only transformation logic

Maintain reproducibility via pipeline execution

8. Limitations
Dependent on public dataset update frequency

Structural index (not forward-looking prediction)

Some datasets limited historically

Data harmonization depends on official classification consistency

9. Roadmap
Consolidate Opportunity Score v3 (IBGE + CNPJ + CAGED)

Improve feature engineering depth

Introduce momentum indicators

Add predictive modeling layer

Implement cloud-native deployment architecture

Structured reporting module (LLM-assisted summaries)

10. Strategic Positioning
This project demonstrates:

Data systems architecture

Public data integration

Analytical modeling

Explainable scoring systems

Hybrid query layers (local + cloud)

Production-ready modular design

It is part of a broader portfolio focused on data infrastructure and market intelligence systems.

Author
Flávia Dottori
Data Systems & Economic Intelligence

LinkedIn: https://www.linkedin.com/in/fmdottori


---
