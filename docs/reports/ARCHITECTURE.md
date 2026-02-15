# Architecture Overview

## 📐 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    B2B Dashboard v2.0                       │
│                   Production Ready Stack                    │
└─────────────────────────────────────────────────────────────┘

                      ┌──────────────┐
                      │  Streamlit   │
                      │  Dashboard   │
                      │  (app.py)    │
                      └──────┬───────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
      ┌───▼──┐          ┌───▼──┐          ┌───▼──┐
      │ UI   │          │ Core │          │Utils │
      │Module│          │Module│          │Module│
      └─┬────┘          └─┬────┘          └─┬────┘
        │                 │                  │
        │            ┌────▼────┐            │
        │            │ Business │           │
        │            │  Logic   │           │
        │            └────┬─────┘           │
        │                 │                 │
      ┌─▼─────────────────▼─────────────────▼─┐
      │           src/ (Modular Code)         │
      │  ┌────────┬──────────┬────────────┐   │
      │  │config/ │  data/   │ processing │   │
      │  └────────┴──────────┴────────────┘   │
      └────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    ┌───▼───┐    ┌───▼───┐    ┌───▼──┐
    │ IBGE  │    │ CAGED │    │Data  │
    │ Data  │    │ Data  │    │Files │
    └───┬───┘    └───┬───┘    └───┬──┘
        │            │            │
        └────────────┼────────────┘
                     │
             ┌───────▼────────┐
             │  Data Lake     │
             │  (Parquet)     │
             └────────────────┘


```

## 🗂️ Module Structure

```
┌─────────────────────────────────────────┐
│          src/config/                    │
│  ┌────────────────────────────────────┐ │
│  │ settings.py                        │ │
│  │ - PathConfig (paths)               │ │
│  │ - Settings (env config)            │ │
│  │ - Project root detection           │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ constants.py                       │ │
│  │ - UF_ORDER                         │ │
│  │ - MACRO_SECTORS                    │ │
│  │ - I18N translations                │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          src/utils/                     │
│  ┌────────────────────────────────────┐ │
│  │ formatters.py                      │ │
│  │ - fmt_int()                        │ │
│  │ - normalize_uf()                   │ │
│  │ - clean_label()                    │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ data_loading.py                    │ │
│  │ - load_parquet_safe()              │ │
│  │ - validate_dataframe()             │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ logging_config.py                  │ │
│  │ - setup_logging()                  │ │
│  │ - get_logger()                     │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          src/core/                      │
│  ┌────────────────────────────────────┐ │
│  │ data_processing.py                 │ │
│  │ - prep_companies()                 │ │
│  │ - prep_scores()                    │ │
│  │ - prep_caged()                     │ │
│  │ - apply_filters()                  │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│          src/ui/                        │
│  ┌────────────────────────────────────┐ │
│  │ components.py                      │ │
│  │ - apply_styles()                   │ │
│  │ - render_kpi()                     │ │
│  │ - render_pills()                   │ │
│  │ - render_diagnostic_info()         │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘

```

## 🔄 Data Flow

```
┌──────────────────────────────────────────────────────────┐
│                   Data Flow Pipeline                     │
└──────────────────────────────────────────────────────────┘

Raw Data Sources
    │
    ├─► IBGE API
    ├─► CAGED Files
    ├─► Receita CNPJ
    └─► External CSVs
         │
         ▼
    ┌─────────────┐
    │  ETL        │  (Pipelines/)
    │  Processes  │
    └──────┬──────┘
           │
           ▼
    ┌──────────────────────┐
    │  Data Lake (Raw)     │
    │  - CSV Files         │
    │  - Parquet Format    │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │  Data Processing     │  (core/data_processing.py)
    │  - Validation        │
    │  - Cleaning          │
    │  - Enrichment        │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │  Processed Data      │
    │  - Cleaned CSVs      │
    │  - Aggregated Data   │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │  Streamlit App       │  (dashboards/app.py)
    │  - Load Cached Data  │
    │  - Apply Filters     │
    │  - Render Viz        │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │  User Dashboard      │
    │  - Maps              │
    │  - Charts            │
    │  - KPIs              │
    └──────────────────────┘

```

## 🧪 Testing Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Test Pyramid (55+ tests)                   │
│                                                          │
│                    Integration Tests                     │
│                   (Pipeline E2E)                         │
│                  test_core.py (18 tests)                │
│                 ▲                                        │
│                ╱ ╲                                       │
│               ╱   ╲                                      │
│              ╱ Unit ╲                                    │
│             ╱ Tests ╲                                    │
│            ╱ (37     ╲                                   │
│           ╱  tests)   ╲                                  │
│          ╱              ╲                                │
│         ╱ ━━━━━━━━━━━━━━ ╲                              │
│        ├─ test_formatters  ├ (20 tests)                │
│        ├─ test_data_load   ├ (5 tests)                 │
│        ├─ test_config      ├ (6 tests)                 │
│        ├─ test_ui          ├ (13 tests)                │
│        └─ test_core        └ (18 tests)                │
│                                                          │
└─────────────────────────────────────────────────────────┘

Each test layer:
- Unit: Fast, isolated, single component
- Integration: Moderate speed, multiple components
- E2E: Full pipeline, real data (in staging)
```

## 🚀 Deployment Options

```
                  ┌──────────────────┐
                  │   Git Repository │
                  │   (source code)  │
                  └────────┬─────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼──┐      ┌─────▼──┐      ┌─────▼──┐
    │ Heroku │      │   AWS   │      │ Docker │
    │ (Dev)  │      │ (Scale) │      │ (Any)  │
    └────┬───┘      └────┬────┘      └────┬───┘
         │               │                │
    ┌────▼────────────────▼────────────────▼─────┐
    │         Environment Detection              │
    │     (dotenv, environment vars)             │
    └──────────┬──────────────────────────────────┘
               │
    ┌──────────▼──────────────┐
    │  Streamlit Application  │
    │  - Cached Resources     │
    │  - Data Processing      │
    │  - User Interface       │
    └────────────────────────┘
```

## 📊 CI/CD Pipeline

```
Git Push
  │
  └─► GitHub Actions
      │
      ├─► ci.yml
      │   ├─ Run Tests (Python 3.9-3.12)
      │   ├─ Generate Coverage
      │   └─ Upload to codecov
      │
      └─► quality.yml
          ├─ Black (format)
          ├─ isort (imports)
          ├─ pylint (lint)
          ├─ mypy (types)
          └─ bandit (security)
          
All Checks Pass
  │
  └─► Merge Allowed
      │
      └─► Deploy (optional)
          ├─ Heroku: git push heroku main
          ├─ AWS: docker push / deployment
          └─ Docker: docker run latest
```

## 🔐 Security Layers

```
┌────────────────────────────────────────┐
│     Security & Quality Automation      │
├────────────────────────────────────────┤
│ 1. Pre-commit Hooks (Local)            │
│    ├─ No hardcoded secrets             │
│    ├─ No large files                   │
│    └─ Format validation                │
├────────────────────────────────────────┤
│ 2. GitHub Actions CI (Remote)          │
│    ├─ Security scan (bandit)           │
│    ├─ Dependency audit                 │
│    └─ Type safety check                │
├────────────────────────────────────────┤
│ 3. Environment Isolation               │
│    ├─ .env for secrets                 │
│    ├─ No .env in repo                  │
│    └─ Per-environment config           │
├────────────────────────────────────────┤
│ 4. Code Review                         │
│    ├─ PR required before merge         │
│    ├─ All checks must pass             │
│    └─ Approval needed                  │
└────────────────────────────────────────┘
```

## 📈 Performance Optimization

```
┌──────────────────────────────────┐
│  Performance Optimization Stack  │
├──────────────────────────────────┤
│ 1. Caching Layer                 │
│    @st.cache_resource            │
│    - Data loaded once            │
│    - Shared across sessions      │
├──────────────────────────────────┤
│ 2. Lazy Loading                  │
│    - Load on demand              │
│    - Filter before process       │
├──────────────────────────────────┤
│ 3. Data Format                   │
│    - Parquet (efficient)         │
│    - Compressed                  │
├──────────────────────────────────┤
│ 4. Filtering Early               │
│    - Apply filters at source     │
│    - Reduce computation          │
└──────────────────────────────────┘
```

---

**Architecture Version:** 2.0 (Phase 2 Complete)  
**Last Updated:** Janeiro 2024  
**Status:** Production Ready ✅
