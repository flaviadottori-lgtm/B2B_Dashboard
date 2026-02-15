# Data Dictionary (Phase 1)

This document lists the **minimum required columns** for Phase 1.
Datasets may contain additional fields.

## companies_agg (IBGE)

- `year` (int): reference year
- `uf` (string): state abbreviation (UF)
- `sector` or `macro_sector` (string): sector label
- `opened` (int): new companies
- `closed` (int): closed companies
- `net` (int): opened - closed

## caged_state_sector_year (CAGED)

- `year` (int)
- `uf` (string)
- `sector` or `macro_sector` (string)
- `job_balance` (int): admissions - dismissals

## opportunity_scores (IBGE)

- `year` (int)
- `uf` (string)
- `region` (string)
- `opportunity_score` (float)
- `units` (float or int): weight for score aggregation

## PNAD metrics (optional)

- `ano` (int)
- `trimestre` (int)
- `uf_code` (int)
- `uf` (string, derived from `uf_code`)
- `sexo` (string)
- `grupo_idade` (string)
- `populacao` (int)
- `forca_trabalho` (int)
- `ocupados` (int)
- `desocupados` (int)
- `ocupados_informais` (int)
- `taxa_informalidade` (float 0..1)
- `taxa_desemprego` (float 0..1)
- `renda_media_trabalho` (float)

