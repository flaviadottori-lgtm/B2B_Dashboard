# Market Opportunity Dashboard

Economic intelligence platform that integrates **IBGE** and **CAGED** data to map  
**business growth, B2B opportunities, and sectoral dynamics in Brazil**.

Plataforma de inteligência econômica que integra dados do **IBGE** e **CAGED** para mapear  
**crescimento empresarial, oportunidades B2B e dinâmica setorial no Brasil**.

---

## 🖥️ Project Overview

### Data Pipeline & Opportunity Engine
![Pipeline](assets/opportunityv3.jpg)

### Interactive Dashboard (Streamlit)
![Dashboard](assets/Postlinkedin1.jpg)

---

## ✅ Default Runtime (Fase 1)

O modo recomendado é **Local (DuckDB)**, com o app principal em `app.py`:

```bash
streamlit run app.py
```

O modo **BigQuery** é opcional e está em `app/main.py` (veja a seção "BigQuery").

Também é possível selecionar o backend diretamente no app (DuckDB ou BigQuery) via sidebar.

---

## 📈 Opportunity Score (explicável)

O **Opportunity Score** é um índice estrutural baseado em dados IBGE agregados,
comparável entre estados e explicável. Ele combina:

- intensidade de atividade econômica por UF
- distribuição setorial (macro-setores executivos)
- volume de unidades (peso para comparação)

O objetivo é **rankear oportunidades** de forma transparente, sem caixa-preta.

---

## 🇧🇷 Sobre o Projeto | 🇺🇸 About the Project

This project analyzes the **Brazilian business landscape** using public economic and labor
market data to identify **growth signals, emerging regions, and high-potential B2B sectors**.

The objective is to transform raw public data into **market and economic intelligence**,
supporting:

- strategic decision-making  
- B2B market analysis  
- regional and sectoral opportunity mapping  
- identification of emerging business hubs  

The dashboard is designed with a **business-oriented and executive-friendly approach**,
prioritizing clarity, interpretability, and decision support.

---


## 🚦 Rotina Padrão de Inicialização

1. Rode os pipelines de dados (PNAD/CAGED/RAIS quando aplicável)

2. Execute o bootstrap do DuckDB para garantir as views e dimensões padrão no banco oficial:

```bash
python scripts/bootstrap_duckdb.py
# O banco oficial é data/marts/b2b.duckdb
```

3. Rode o Streamlit:

```bash
streamlit run app/main.py
```

Assim, o app nunca ficará sem dados por nomes inconsistentes e todas as views padrão estarão disponíveis no banco data/marts/b2b.duckdb.

---

## 🧠 Analytical Approach

## 🧠 Analytical Approach

- Exploratory Data Analysis (EDA)  
- Aggregations by region, state, and economic sector  
- Opportunity scoring and comparative analysis  
- Executive-oriented data visualization and storytelling  

---

## 📊 Key Analyses

- Evolution of business openings over time  
- Regional comparisons across Brazil  
- Identification of emerging states and clusters  
- Sectoral distribution with a B2B market focus  

---

## 🛠️ Technologies & Stack

- **Python 3.9+** (Pandas, NumPy)  
- **Parquet** (analytical data lake)  
- **Automated ETL pipelines**  
- **Statistical models** (regression-based analysis)  
- **Streamlit** (executive dashboards)  
- **Plotly & GeoJSON** (spatial and regional analysis)  

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11 ou 3.12 (recomendado)
- pip ou conda
- Git

### Execucao rapida (DuckDB - recomendado)
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### Execucao rapida (BigQuery - opcional)
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r app/requirements.txt
set GOOGLE_APPLICATION_CREDENTIALS=C:\\path\\to\\service-account.json
set BQ_PROJECT_ID=dados-mercado-brasil
set BQ_DATASET_GOLD=gold
streamlit run app/main.py
```

### Usar BigQuery no app principal (sidebar)
Configure variáveis no `.env`:
```
B2B_BACKEND=bigquery
BQ_PROJECT=seu-projeto
BQ_DATASET_GOLD=seu_dataset
BQ_LOCATION=us
GOOGLE_APPLICATION_CREDENTIALS=C:\\path\\to\\service-account.json
```
Depois rode:
```bash
streamlit run app.py
```

### Installation

1. **Clone o repositório:**
```bash
git clone https://github.com/seu-usuario/b2b-dashboard.git
cd B2B_Dashboard
```

2. **Crie um ambiente virtual:**
```bash
# Com venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
```
```powershell
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```
```bat
# Windows (CMD)
.venv\Scripts\activate.bat
```

# Com conda
conda create -n b2b-dashboard python=3.12
conda activate b2b-dashboard
```

3. **Instale as dependencias:**
```bash
pip install -r requirements.txt
```

Nota: `types-openpyxl` e outros stubs de tipos sao opcionais (dev-only) e nao sao necessarios para rodar o app.

4. **Configure variáveis de ambiente:**
```bash
# Copie o template
cp .env.example .env

# Edite conforme necessário (opcional para desenvolvimento)
```

5. **Execute o dashboard:**
```bash
streamlit run app.py
```

O app estará disponível em `http://localhost:8501`

---

## Streamlit Dashboard

- App name: Market Opportunity Dashboard
- Language support: Portuguese and English via sidebar selector
- Credentials: set `GOOGLE_APPLICATION_CREDENTIALS` to your service account JSON path
- BigQuery overrides: `BQ_PROJECT_ID` and `BQ_DATASET_GOLD`
- RAIS data is available only for 2022 (no temporal metrics)

### Atualizacao do ambiente (Windows)
```bash
pip install -U pip setuptools wheel
pip install -r requirements.txt
streamlit run app/main.py
```

---

## Criar views no BigQuery

Crie (ou atualize) as views abaixo no dataset configurado (`BQ_DATASET_GOLD`):

- `gold_rais_sector_year_metrics`
- `gold_rais_region_risk`
- `gold_rais_profile_mix`
- `gold_rais_opportunity_score`

Os SQLs estao em `sql/rais_views/`.

Nota: nao existe dimensao de descricao CNAE neste projeto. Os seletores exibem CNAE por codigo. Uma futura melhoria e integrar uma `dim_cnae`.

---

## 📸 Screenshots (placeholders)

Coloque imagens em `assets/` e atualize os links acima:

- `assets/opportunityv3.jpg`
- `assets/Postlinkedin1.jpg`

---

## ⚠️ Limitações

- O índice é comparativo e depende da qualidade das bases públicas.
- Não prevê o futuro; indica sinais estruturais e tendências recentes.
- PNAD e CAGED são complementares ao índice estrutural, não protagonistas.

---

## 🧭 Roadmap

**Fase 2**
- Consolidar Opportunity Score v3 (IBGE + CNPJ + CAGED)
- Melhorar narrativas executivas e explainability

**Fase 3**
- Módulos de previsão (tendências 2026+)
- Integração de RAG/LLM para relatórios

---

## 🏗️ Architecture & Project Structure

### Nova Estrutura Modularizada (v2.0+)

```text
B2B_Dashboard/
│
├── src/                          # Código principal
│   ├── config/                   # ⭐ Configuração centralizada
│   │   ├── __init__.py
│   │   ├── settings.py           # Paths, variáveis de ambiente
│   │   └── constants.py          # UF_ORDER, I18N, MACRO_SECTORS
│   │
│   ├── core/                     # ⭐ Lógica de negócio
│   │   ├── __init__.py
│   │   └── data_processing.py    # Prep, filtering, transformações
│   │
│   ├── ui/                       # ⭐ Componentes UI reutilizáveis
│   │   ├── __init__.py
│   │   └── components.py         # Styles, KPIs, Pills
│   │
│   ├── utils/                    # Utilitários gerais
│   │   ├── __init__.py
│   │   ├── formatters.py         # fmt_int, normalize_uf, etc
│   │   ├── data_loading.py       # load_parquet_safe, validate
│   │   └── logging_config.py     # Setup logging estruturado
│   │
│   ├── Pipelines/                # Scripts ETL/Transform
│   │   ├── caged/
│   │   └── ibge_3274_3275_pipeline.py
│   │
│   └── scoring/
│       └── opportunity_engine.py
│
├── dashboards/
│   └── app.py                    # ⭐ Refatorado (140 linhas!)
│
├── tests/                        # Testes unitários
│   ├── __init__.py
│   ├── test_formatters.py
│   └── test_data_processing.py
│
├── data/
│   ├── geo/
│   ├── processed/
│   └── raw/
│
├── .env.example                  # Template de variáveis
├── pyproject.toml                # Gerenciamento moderno
├── .streamlit/config.toml
└── README.md
```

### Mudanças Principais (v2.0)

✅ **Configuração centralizada** → `src/config/settings.py` e `constants.py`  
✅ **Modularização** → Helpers em `src/utils/`, componentes em `src/ui/`, lógica em `src/core/`  
✅ **Logging estruturado** → `src/utils/logging_config.py`  
✅ **Type hints & docstrings** → 100% do código  
✅ **app.py simplificado** → De 832 para ~140 linhas  
✅ **pyproject.toml moderno** → Substituindo requirements.txt  
✅ **Suporte a .env** → Variáveis de ambiente centralizadas  

---

## 📁 Project Structure (Legacy)

```text
B2B_Dashboard/
│
├── dashboards/
│   └── app.py                  # Streamlit application
│
├── data/
│   ├── geo/
│   │   └── brazil_states.geojson
│   │
│   ├── processed/
│   │   ├── companies_agg.parquet
│   │   ├── ibge_3274_3275_tidy.parquet
│   │   ├── opportunity_scores.parquet
│   │   ├── opportunity_scores_v3.parquet
│   │   ├── caged_state_sector_month.parquet
│   │   └── caged_state_sector_year.parquet
│   │
│   └── raw/
│       └── caged/
│           └── caged_xlsx/
│               ├── novo_caged_2024_01.xlsx
│               ├── novo_caged_2024_02.xlsx
│               └── ...
│
└── src/
    ├── Pipelines/
    │   ├── caged/
    │   │   ├── download_caged_xlsx.py
    │   │   └── build_caged_parquet.py
    │   └── ibge_3274_3275_pipeline.py
│
    └── scoring/
        ├── opportunity_engine.py
        └── build_opportunity_v3.py
🚧 Project Status
Under active development.

Current focus areas include:

Deepening regional and sectoral analysis

Improving data quality and consistency

Expanding strategic and comparative insights

🗺️ Next Steps
Consolidate Opportunity Score v3 (IBGE + CNPJ + CAGED)

Add Market Momentum and Hiring Heatmap modules

Develop predictive trend analysis for 2026

Integrate LLM + RAG for executive narratives
(where to invest, why, and when)

📌 Final Notes
This project is part of a Data Analytics and Business Intelligence portfolio, focused on
transforming public economic data into actionable market insights, particularly for
B2B strategy and decision-making.

👤 Author
Flávia Dottori
Data Analytics & Market Intelligence

🔗 LinkedIn: https://www.linkedin.com/in/fmdottori

markdown
Copiar código
