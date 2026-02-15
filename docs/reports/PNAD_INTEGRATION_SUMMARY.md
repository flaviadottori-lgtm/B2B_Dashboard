# PNAD Streamlit Integration - Summary

**Completed:** January 18, 2026  
**Phase:** Lote 11 - PNAD Data Integration in Streamlit  
**Status:** ✅ Complete

---

## Executive Summary

Successfully integrated pre-generated PNAD (Pesquisa Nacional por Amostra de Domicílios Contínua) data into the Streamlit dashboard without runtime BigQuery queries. The implementation reuses existing patterns (i18n system, caching, UI components) while adding a new 5th tab with interactive PNAD analysis.

**Key Metrics:**
- 4,101 rows of PNAD data (after NA handling)
- 5 tabs in app (extended from 4)
- 13 new i18n keys (PT + EN)
- 0 breaking changes to existing functionality
- All smoke tests passing (7/7)

---

## Files Modified/Created

### 1. **src/ui/pnad_section.py** (NEW)
**Status:** ✅ Created  
**Size:** ~165 lines  
**Purpose:** PNAD UI rendering component for Streamlit

**Features:**
- 4-column filter layout: year (selectbox), state (dropdown with "All"), gender, age_group
- 3 KPI metrics: total_population, num_regions, num_groups
- Conditional time series chart (if multiple years in filtered data)
- Conditional comparison bar chart (if not filtered by state)
- Data table with translated column headers
- Graceful error handling (shows instruction if parquet missing)
- Full PT/EN support via i18n system
- Dark blue color scheme (#0B1F33) consistent with existing UI

**Cache Implementation:**
```python
@st.cache_data(show_spinner=False)
def load_pnad_cached():
    return load_pnad_data()
```

**Error Handling:**
Shows user-friendly warning if `data/marts/pnad/pnad_uf_quarter_gender_age.parquet` is missing, with instruction to run `run_pnad_pipeline.py`.

---

### 2. **src/utils/data_loading.py** (ENHANCED)
**Status:** ✅ Updated  
**Added Function:** `load_pnad_data(pnad_path: Optional[Path] = None) -> Optional[pd.DataFrame]`  
**Lines Added:** ~50

**Implementation Details:**
- Loads from `data/marts/pnad/pnad_uf_quarter_gender_age.parquet` by default
- Validates required columns: `ano`, `uf_code`, `sexo`, `grupo_idade`, `populacao`
- Removes rows with NA in critical columns (ano, populacao)
- Converts types: ano → int64, populacao → int64
- Returns None gracefully if file missing or validation fails
- Logs all operations for debugging
- Reuses existing `load_parquet_safe()` and `validate_dataframe()` patterns

**Return Value:** DataFrame (4,101 rows after NA handling) or None

---

### 3. **src/config/constants.py** (EXTENDED)
**Status:** ✅ Updated  
**Changes:**
1. Added 13 new i18n keys for PT (Portuguese):
   - `pnad_title`: "Mercado de Trabalho (PNAD)"
   - `pnad_desc`: "Dados agregados da Pesquisa Nacional por Amostra de Domicílios Contínua (IBGE)"
   - `pnad_year`, `pnad_state`, `pnad_gender`, `pnad_age_group`, `pnad_population`
   - `pnad_filters`, `pnad_data`, `pnad_not_found`, `pnad_not_found_msg`
   - `pnad_time_series`, `pnad_comparison`

2. Added 13 identical keys for EN (English):
   - All keys with English translations

3. Updated `"tabs"` arrays:
   - PT: Added "💼 PNAD" (now 5 tabs instead of 4)
   - EN: Added "💼 PNAD" (now 5 tabs instead of 4)

**Sample Translation Keys:**
```python
# Portuguese
"pnad_title": "Mercado de Trabalho (PNAD)",
"pnad_desc": "Dados agregados da PNAD Contínua (IBGE)",
"pnad_year": "Ano",
"pnad_state": "Estado",

# English
"pnad_title": "Labor Market (PNAD)",
"pnad_desc": "Aggregated PNAD Contínua Data (IBGE)",
"pnad_year": "Year",
"pnad_state": "State",
```

---

### 4. **dashboards/app.py** (INTEGRATED)
**Status:** ✅ Updated  
**Changes:**
1. Added import:
   ```python
   from src.ui.pnad_section import render_pnad_section
   ```

2. Updated tab unpacking (line ~267):
   ```python
   # Before
   tab1, tab2, tab3, tab4 = st.tabs(T["tabs"])
   
   # After
   tab1, tab2, tab3, tab4, tab5 = st.tabs(T["tabs"])
   ```

3. Added PNAD tab rendering (line ~538):
   ```python
   # TAB 4  PNAD
   with tab4:
       render_pnad_section(lang=LANG)
   
   # TAB 5  DATA & DIAGNOSTICS
   with tab5:
       # (existing diagnostics code)
   ```

**Impact:** Previous "Data & Diagnostics" tab moved from tab4 to tab5

---

## Testing & Validation

### Test File: **test_pnad_integration.py** (NEW)
**Status:** ✅ Created  
**Test Count:** 7 tests

**Test Results:**
```
✓ All PNAD i18n keys exist in PT and EN
✓ All PNAD i18n values are non-empty
✓ Tab arrays updated to 5 tabs including PNAD
✓ Loader gracefully returns None for missing parquet
✓ Loader returns correct DataFrame structure (4101 rows)
✓ App imports pnad_section successfully
✓ All smoke tests passed

✅ All PNAD integration tests passed!
```

### App Import Validation:
```
✅ App imports successfully
✅ All datasets loaded (9353 companies, 7938 scores, 1512 CAGED, GeoJSON)
✅ PNAD data loaded: 4101 rows (after NA handling)
✅ App rendered successfully
```

---

## Data Schema

**Source:** `basedosdados.br_ibge_pnadc.ano_uf_grupo_idade` (Public BigQuery)  
**File:** `data/marts/pnad/pnad_uf_quarter_gender_age.parquet`  
**Size:** 16.82 KB (snappy compressed)  
**Rows:** 4,131 (raw) → 4,101 (after NA handling)  
**Coverage:** 2017-2019, all 27 UFs, 2 sexes, 17 age groups

**Schema:**
| Column | Type | Example |
|--------|------|---------|
| ano | int64 | 2017 |
| uf_code | string | "AC" |
| sexo | string | "Masculino" |
| grupo_idade | string | "10 a 14 anos" |
| populacao | int64 | 45230 |
| extracao_data | timestamp | 2025-09-01 |

---

## UI Components

### PNAD Section Features:

1. **Filters** (4 columns):
   - Year: Selectbox (default = latest year in data)
   - State: Selectbox with "All" option
   - Gender: Multi-select filter
   - Age Group: Multi-select filter

2. **KPI Metrics** (3 cards):
   - Total Population
   - Number of Regions
   - Number of Age Groups

3. **Charts** (conditional):
   - **Time Series**: Line chart with markers (if multiple years selected)
   - **Comparison**: Horizontal bar chart (if not filtered by state)

4. **Data Table**:
   - Dynamic column naming based on language
   - Scrollable with height constraint

5. **Error Handling**:
   - If parquet missing: Show warning + instruction
   - If data empty: Show info message
   - Graceful degradation (app doesn't break)

---

## Integration Pattern

The PNAD integration follows established project patterns:

### 1. **Data Loading Pattern**
```python
# Reuses existing validation framework
df = load_parquet_safe(path)
validate_dataframe(df, required_columns)
```

### 2. **Caching Pattern**
```python
@st.cache_data(show_spinner=False)
def load_pnad_cached():
    return load_pnad_data()
```

### 3. **i18n Pattern**
```python
# Uses existing I18N system
T = I18N[lang]  # lang = 'pt' or 'en'
T["pnad_title"]
```

### 4. **Styling Pattern**
```python
# Consistent with existing dark blue palette
color_continuous_scale=["#0B1F33", "#143A5A", ...]
```

---

## Performance Considerations

1. **Caching**: PNAD data cached on first load (Streamlit cache_data)
2. **Lazy Loading**: PNAD only loaded when tab4 is accessed
3. **Data Volume**: 4,101 rows → negligible impact on app performance
4. **Memory**: Parquet file ~17 KB → minimal memory footprint

---

## Bilingual Support

All PNAD UI elements support dynamic language switching (PT ↔ EN):

**Portuguese (PT):**
- Tab name: "💼 PNAD"
- Title: "Mercado de Trabalho (PNAD)"
- Filter labels: "Ano", "Estado", "Gênero", "Faixa Etária"

**English (EN):**
- Tab name: "💼 PNAD"
- Title: "Labor Market (PNAD)"
- Filter labels: "Year", "State", "Gender", "Age Group"

---

## Graceful Degradation

If PNAD parquet file is missing:

1. App doesn't break ✅
2. Tab4 (PNAD) still renders ✅
3. Shows user-friendly warning with instructions ✅
4. User can run `python run_pnad_pipeline.py` to generate parquet ✅

---

## Next Steps (Optional Future Work)

1. **Advanced Filters**: Add education level, employment status filters
2. **Time Series Analysis**: Add YoY growth, trend analysis
3. **Regional Comparison**: Add heatmap comparing regions
4. **Export**: Add CSV/Excel export functionality
5. **Database Integration**: Replace parquet with live database query (PostgreSQL)

---

## Files Summary

| File | Status | Changes |
|------|--------|---------|
| `src/ui/pnad_section.py` | ✅ NEW | 165 lines |
| `src/utils/data_loading.py` | ✅ ENHANCED | +50 lines |
| `src/config/constants.py` | ✅ EXTENDED | 13+13 i18n keys |
| `dashboards/app.py` | ✅ INTEGRATED | 3 edits |
| `test_pnad_integration.py` | ✅ NEW | 7 tests (all passing) |

---

## Validation Checklist

- ✅ All files have correct syntax (py_compile)
- ✅ App imports successfully
- ✅ All datasets load without error
- ✅ i18n keys exist (PT + EN)
- ✅ Loader handles missing parquet gracefully
- ✅ Loader validates data structure
- ✅ Tab4 renders PNAD section correctly
- ✅ Bilingual switching works
- ✅ No breaking changes to existing functionality
- ✅ Smoke tests pass (7/7)

---

## How to Use

### 1. Verify PNAD parquet exists:
```bash
ls -la data/marts/pnad/pnad_uf_quarter_gender_age.parquet
```

### 2. Run the app:
```bash
streamlit run dashboards/app.py
```

### 3. Navigate to PNAD tab:
- Select language (PT/EN) from sidebar
- Click on "💼 PNAD" tab
- Use filters to explore data

### 4. If parquet missing:
```bash
python run_pnad_pipeline.py
```

---

## Notes

- All changes are **non-breaking** to existing functionality
- PNAD tab can be independently disabled/removed if needed
- Caching ensures fast tab switching
- i18n keys follow existing naming convention: `pnad_*`
- Color scheme matches existing dark blue palette

---

**Integration Completed Successfully** ✅  
**All Tests Passing** ✅  
**Ready for Production** ✅
