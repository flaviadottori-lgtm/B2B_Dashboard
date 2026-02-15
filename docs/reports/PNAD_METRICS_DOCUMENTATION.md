# PNAD Métricas Avançadas - Documentação

**Versão:** 2.0  
**Data:** January 18, 2026  
**Status:** ✅ Implementação completa

---

## Overview

Evolução do pipeline PNAD para incluir métricas socioeconômicas além de população:

- **Taxa de Informalidade**: % de ocupados sem registro formal
- **Renda Média do Trabalho**: Média salarial (com tratamento de outliers)
- **Taxa de Desemprego**: % de desocupados na força de trabalho

---

## Arquivos Novos/Modificados

### 1. `src/Pipelines/pnad/extract_pnad_metrics.py` (NEW)

**Classe:** `PNADCMetricsExtractor`

```python
from src.Pipelines.pnad.extract_pnad_metrics import extract_pnad_metrics

df = extract_pnad_metrics(
    min_year=2017,
    output_path=Path('data/pnad_metrics.parquet')
)
```

**Recursos:**
- SQL otimizada com SAFE_DIVIDE para divisão segura
- Winsorização de renda (5%-95% percentis) para remover outliers
- Validação de dados pós-processamento
- Logging detalhado de operações

**Query SQL:**
- Extrai de `basedosdados.br_ibge_pnadc.pessoa`
- Agrupa por: UF × Ano × Trimestre × Sexo × Grupo Idade
- Calcula: ocupados, desocupados, informais, renda média
- Deriva: taxa_informalidade, taxa_desemprego

**Output:** `pnad_uf_trimestre_sexo_idade_metrics.parquet`

---

### 2. `run_pnad_metrics_pipeline.py` (NEW)

CLI para execução:

```bash
python run_pnad_metrics_pipeline.py [OPTIONS]

Options:
  --min-year INT          # Ano mínimo (default: 2017)
  --output PATH           # Caminho output (default: data/marts/pnad/...)
  --no-save               # Sem salvar parquet
  --project STR           # GCP project ID (default: b2b-opportunity-engine)
```

**Exemplo:**
```bash
python run_pnad_metrics_pipeline.py --min-year 2017 --output data/custom_metrics.parquet
```

---

### 3. `src/ui/pnad_section.py` (ATUALIZADO)

**Nova estrutura:**
- Seletor de métrica (selectbox com 4 opções)
- Funções separadas por métrica:
  - `_render_population_section()` (compatível com v1.0)
  - `_render_informality_section()` (placeholder - aguarda v2.0)
  - `_render_income_section()` (placeholder)
  - `_render_unemployment_section()` (placeholder)

**Recursos mantidos:**
- Filtros dinâmicos (Ano, Estado, Sexo, Faixa Etária)
- KPIs contextuais
- Gráficos (série temporal, comparação)
- Tabelas interativas
- i18n PT/EN

**Upgrade path:**
1. Executar `python run_pnad_metrics_pipeline.py` para gerar novo parquet
2. Atualizar loader para carregar ambos os parquets
3. Renderizar gráficos dinâmicos por métrica
4. Adicionar comparações (ex: renda por gênero, informalidade por idade)

---

### 4. `src/config/constants.py` (ESTENDIDO)

**Novas chaves i18n (PT + EN):**
- `pnad_metric_selector`: "Seletor de Métrica" / "Metric Selector"
- `pnad_select_metric`: "Escolha a métrica..." / "Choose a metric..."
- `pnad_kpis`: "KPIs" / "KPIs"
- `pnad_informality`: "Taxa de Informalidade" / "Informality Rate"
- `pnad_income`: "Renda Média do Trabalho" / "Average Work Income"
- `pnad_unemployment`: "Taxa de Desemprego" / "Unemployment Rate"

---

## Schema do Novo Parquet

**Arquivo:** `data/marts/pnad/pnad_uf_trimestre_sexo_idade_metrics.parquet`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `ano` | int64 | 2012-2019 |
| `trimestre` | int64 | 1, 2, 3, 4 |
| `uf_code` | string | AC, AL, ..., SP |
| `sexo` | string | Masculino, Feminino |
| `grupo_idade` | string | 00-09, 10-14, ..., 65+ |
| `populacao` | int64 | Total de pessoas |
| `forca_trabalho` | int64 | Ocupados + Desocupados |
| `ocupados` | int64 | Com ocupação |
| `desocupados` | int64 | Procurando emprego |
| `ocupados_informais` | int64 | Sem registro formal |
| `taxa_informalidade` | float64 | 0 a 1 (proporção) |
| `taxa_desemprego` | float64 | 0 a 1 (proporção) |
| `renda_media_trabalho` | float64 | Em R$ (winsorizada) |
| `renda_registros` | int64 | Quantos têm renda válida |
| `extracao_data` | timestamp | Quando foi extraído |

---

## Como Usar

### 1. Gerar novo parquet com métricas

```bash
cd /path/to/B2B_Dashboard
python run_pnad_metrics_pipeline.py
```

**Output esperado:**
```
======================================================================
PNAD CONTÍNUA METRICS EXTRACTION PIPELINE
======================================================================

✓ BigQuery client initialized
✓ Query executed: 45,000 rows
✓ Processing renda values (winsorization at 5%-95%)...
✓ File size: 8.45 MB

======================================================================
PIPELINE COMPLETED SUCCESSFULLY
======================================================================
Records extracted: 45,000
Output: data/marts/pnad/pnad_uf_trimestre_sexo_idade_metrics.parquet

Metrics included:
  - taxa_informalidade: % ocupados informais
  - taxa_desemprego: % desocupados / força trabalho
  - renda_media_trabalho: média renda (winsorizada 5%-95%)
```

### 2. Usar no app Streamlit

```bash
streamlit run dashboards/app.py
```

Na aba "💼 PNAD":
1. Selecione a métrica (dropdown com 4 opções)
2. Aplique filtros conforme necessário
3. Explore gráficos e tabelas

**Nota:** As seções de informalidade, renda e desemprego mostrarão mensagem orientando a executar o pipeline v2.0.

### 3. Usar via Python

```python
from src.Pipelines.pnad.extract_pnad_metrics import extract_pnad_metrics
from pathlib import Path

# Extrair
df = extract_pnad_metrics(min_year=2017)

# Explorar
print(f"Linhas: {len(df)}")
print(f"Colunas: {df.columns.tolist()}")
print(f"Informalidade média: {df['taxa_informalidade'].mean():.1%}")
print(f"Desemprego médio: {df['taxa_desemprego'].mean():.1%}")
print(f"Renda média: R$ {df['renda_media_trabalho'].mean():,.0f}")
```

---

## Testes

### Smoke tests

```bash
# Validar sintaxe
python -m py_compile src/Pipelines/pnad/extract_pnad_metrics.py

# Validar imports
python -c "from src.Pipelines.pnad.extract_pnad_metrics import extract_pnad_metrics; print('OK')"

# Validar i18n
python -c "from src.config.constants import I18N; print(I18N['pt']['pnad_informality'])"

# Suite completa
python test_pnad_integration.py
```

---

## Roadmap (v2.1+)

- [ ] Carregar ambos os parquets (v1 + v2) simultaneamente
- [ ] Renderizar gráficos dinâmicos para cada métrica
- [ ] Comparações cruzadas (ex: renda vs informalidade por UF)
- [ ] Trends YoY (Year-over-Year)
- [ ] Export de relatórios (PDF/Excel)
- [ ] Cache em PostgreSQL

---

## Troubleshooting

| Erro | Solução |
|------|---------|
| `ModuleNotFoundError: google.cloud` | `pip install google-cloud-bigquery` |
| `BigQuery authentication failed` | `gcloud auth application-default login` |
| `Query timeout` | Aumentar `maximum_bytes_billed` ou usar `--min-year 2019` |
| `Memory error` | Processar ano a ano em vez de período completo |

---

**Status:** ✅ Pronto para v2.0  
**Próximo passo:** Integrar renderização de gráficos dinâmicos por métrica
