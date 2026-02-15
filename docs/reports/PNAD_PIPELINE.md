# Pipeline PNAD Contínua via BigQuery

## Visão Geral

Pipeline para extrair dados da **PNAD Contínua** (Pesquisa Nacional por Amostra de Domicílios Contínua) diretamente do BigQuery através do projeto público **Base dos Dados**.

- **Fonte**: `basedosdados.br_ibge_pnadc.ano_uf_grupo_idade`
- **Cobertura**: 2012-2019 (dados agregados por UF, ano, sexo, grupo etário)
- **Saída**: Parquet otimizado em `data/marts/pnad/pnad_uf_quarter_gender_age.parquet`
- **Custo**: ~50MB por query (query cache reutilizável)

## Arquitetura

```
src/Pipelines/pnad/
├── __init__.py                      # Exports públicos
└── extract_pnad_bigquery.py         # PNADCExtractor + convenience functions

run_pnad_pipeline.py                 # CLI para executar o pipeline
test_pnad_pipeline.py                # Smoke tests
```

## Uso

### 1. Rodar o pipeline com defaults (2017-2019)

```bash
python run_pnad_pipeline.py
```

Saída:
```
======================================================================
PNAD CONTÍNUA EXTRACTION PIPELINE
======================================================================

✓ BigQuery client initialized
✓ Query executed: 4,131 rows
✓ File size: 0.02 MB

======================================================================
PIPELINE COMPLETED SUCCESSFULLY
======================================================================
Records extracted: 4,131
Output: data/marts/pnad/pnad_uf_quarter_gender_age.parquet
```

### 2. Rodar com ano mínimo customizado

```bash
python run_pnad_pipeline.py --min-year 2012
```

### 3. Usar como módulo Python

```python
from src.Pipelines.pnad import extract_pnad
from pathlib import Path

# Extrair e salvar
df = extract_pnad(
    min_year=2017,
    output_path=Path('data/pnad.parquet')
)

# Ou só extrair em memória
df = extract_pnad(min_year=2017, output_path=None)
```

### 4. Rodar smoke tests

```bash
python test_pnad_pipeline.py
```

## Autenticação

O pipeline usa **Application Default Credentials (ADC)** da Google Cloud:

```bash
gcloud auth application-default login
```

Certificado armazenado em:
```
C:\Users\{user}\AppData\Roaming\gcloud\application_default_credentials.json
```

## Schema dos Dados

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `ano` | int64 | Ano (2012-2019) |
| `uf_code` | string | ID UF (IBGE) |
| `sexo` | string | "Masculino" ou "Feminino" |
| `grupo_idade` | string | Ex: "0 a 4 anos", "5 a 9 anos", etc |
| `populacao` | int64 | População total |
| `extracao_data` | timestamp | Timestamp de extração |

## Dados Disponíveis

```
Years:    [2017, 2018, 2019]
UFs:      27
Rows:     4,131
Columns:  6
Memory:   0.76 MB
```

## Próximos Passos

Para enriquecer o dataset:

1. **Dados de rendimento/informalidade**: 
   - Usar tabela `br_ibge_pnadc.rendimentos_outras_fontes` ou `microdados`
   - Requer query mais complexa (custo maior)

2. **Integração com Postgres**:
   - Criar tabela `public.pnad_uf_year_gender_age`
   - Sincronizar via trigger diário

3. **Agregações adicionais**:
   - Por região geográfica
   - Por setor econômico (se dados disponíveis)
   - Por educação

## Troubleshooting

### "Module not found: db-dtypes"

```bash
python -m pip install db-dtypes --force-reinstall
```

### "Access Denied: User does not have permission"

Verificar que ADC está configurada:
```bash
gcloud auth application-default print-access-token
```

### Query retorna 0 linhas

A tabela `ano_uf_grupo_idade` só tem dados 2012-2019. 
Use `--min-year` com valor nesse range.

## Referências

- [Base dos Dados PNAD](https://basedosdados.org/dataset/br-ibge-pnadc)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
