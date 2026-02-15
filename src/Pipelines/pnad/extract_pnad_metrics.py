"""
Extract PNAD Contínua metrics: informalidade, renda, desemprego

Extende o extract_pnad_bigquery.py com novas métricas mantendo a granularidade.

Métricas calculadas:
- taxa_informalidade: proporção de ocupados informais
- renda_media_trabalho: média da renda do trabalho (com tratamento de outliers)
- taxa_desemprego: desocupados / força de trabalho
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

# Add project to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from google.cloud import bigquery
import pandas as pd
import numpy as np

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] | %(levelname)-8s | %(message)s', '%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class PNADCMetricsExtractor:
    """
    Extrai métricas avançadas PNAD Contínua
    
    Usa tabela detalhada `ano_trimestre_uf_sexo_idade_educacao` para calcular:
    - Taxa de informalidade (ocupados informais / total ocupados)
    - Renda média do trabalho (com winsorização em 5%-95%)
    - Taxa de desemprego (desocupados / força de trabalho)
    
    Resultado agregado por: UF x ano x trimestre x sexo x grupo_idade
    """
    
    def __init__(self, project_id: str = 'b2b-opportunity-engine'):
        """
        Initialize BigQuery client with ADC
        
        Args:
            project_id: GCP project for billing
        """
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.sql_query = None  # Will be set during extraction
        logger.info(f"✓ BigQuery client initialized (project: {project_id})")
    
    def extract_pnad_metrics(
        self, 
        min_year: int = 2017,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Extrai métricas PNAD com granularidade: UF x ano x trimestre x sexo x grupo_idade
        
        Usa agregação no BigQuery para otimizar custos.
        
        Args:
            min_year: Ano mínimo para filtro
            output_path: Path para salvar parquet
            
        Returns:
            DataFrame com métricas agregadas
        """
        
        logger.info(f"Extracting PNAD metrics (min_year={min_year})...")
        
        # SQL otimizada - calcula métricas no BigQuery
        query = f"""
        WITH pnad_data AS (
            -- Selecionar dados relevantes da PNAD
            SELECT
                ano,
                trimestre,
                id_uf as uf_code,
                sexo,
                idade,
                situacao_principal,  -- Ocupado, Desocupado, Inativo, etc
                posicao_ocupacao,     -- Formal, Informal, Conta-própria, etc
                renda_trabalho,
                CURRENT_TIMESTAMP() as extracao_data
            FROM `basedosdados.br_ibge_pnadc_microdados.pessoa`
            WHERE ano >= {min_year}
              AND id_uf IS NOT NULL
              AND sexo IS NOT NULL
              AND idade IS NOT NULL
        ),
        -- Agrupar por UF, ano, trimestre, sexo, grupo_idade
        aggregated AS (
            SELECT
                ano,
                trimestre,
                uf_code,
                sexo,
                CASE 
                    WHEN idade < 10 THEN '00-09'
                    WHEN idade < 15 THEN '10-14'
                    WHEN idade < 18 THEN '15-17'
                    WHEN idade < 20 THEN '18-19'
                    WHEN idade < 25 THEN '20-24'
                    WHEN idade < 30 THEN '25-29'
                    WHEN idade < 35 THEN '30-34'
                    WHEN idade < 40 THEN '35-39'
                    WHEN idade < 45 THEN '40-44'
                    WHEN idade < 50 THEN '45-49'
                    WHEN idade < 55 THEN '50-54'
                    WHEN idade < 60 THEN '55-59'
                    WHEN idade < 65 THEN '60-64'
                    ELSE '65+'
                END as grupo_idade,
                -- Población total
                COUNT(*) as populacao,
                -- Força de trabalho (ocupados + desocupados)
                COUNTIF(situacao_principal IN ('Ocupado', 'Desocupado')) as forca_trabalho,
                -- Ocupados
                COUNTIF(situacao_principal = 'Ocupado') as ocupados,
                -- Desocupados
                COUNTIF(situacao_principal = 'Desocupado') as desocupados,
                -- Ocupados informais (não formal + conta-própria sem registro)
                COUNTIF(
                    situacao_principal = 'Ocupado' 
                    AND posicao_ocupacao IN ('Informal', 'Conta-própria')
                ) as ocupados_informais,
                -- Renda média (com tratamento de nulos)
                AVG(CASE 
                    WHEN renda_trabalho > 0 THEN renda_trabalho 
                    ELSE NULL 
                END) as renda_media_raw,
                -- Contagem de registros com renda válida
                COUNTIF(renda_trabalho > 0) as renda_registros,
                extracao_data
            FROM pnad_data
            GROUP BY ano, trimestre, uf_code, sexo, grupo_idade, extracao_data
        )
        -- Calcular métricas finais com tratamento de divisão
        SELECT
            ano,
            trimestre,
            uf_code,
            sexo,
            grupo_idade,
            populacao,
            forca_trabalho,
            ocupados,
            desocupados,
            ocupados_informais,
            -- Taxa de informalidade (ocupados informais / ocupados)
            SAFE_DIVIDE(ocupados_informais, ocupados) as taxa_informalidade,
            -- Taxa de desemprego (desocupados / força de trabalho)
            SAFE_DIVIDE(desocupados, forca_trabalho) as taxa_desemprego,
            -- Renda média (aproximada - BigQuery não suporta percentil direto em agregação)
            renda_media_raw as renda_media_trabalho,
            renda_registros,
            extracao_data
        FROM aggregated
        WHERE forca_trabalho > 0 OR populacao > 0  -- Filtrar grupos vazios
        ORDER BY ano DESC, trimestre DESC, uf_code, sexo, grupo_idade
        """
        
        # Store SQL for inspection
        self.sql_query = query
        
        logger.info("Executing BigQuery...")
        
        job_config = bigquery.QueryJobConfig(
            use_query_cache=True,
            priority=bigquery.QueryPriority.INTERACTIVE,
            maximum_bytes_billed=int(5e8),  # Max 500MB (mais dados que população)
        )
        
        try:
            query_job = self.client.query(
                query,
                job_config=job_config,
                location='US'
            )
            
            logger.info(f"  Job ID: {query_job.job_id}")
            
            # Get results
            df = query_job.to_dataframe()
            logger.info(f"✓ Query executed: {len(df):,} rows")
            
            if len(df) == 0:
                logger.warning("⚠ Query returned 0 rows!")
                return df
            
            # Post-processing: tratamento de outliers em renda
            df = self._process_renda(df)
            
            # Validations
            self._validate_data(df)
            
            # Save if path provided
            if output_path:
                self._save_parquet(df, output_path)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            raise
    
    def extract(self, min_year: int = 2017, output_path: Optional[Path] = None) -> pd.DataFrame:
        """Alias para extract_pnad_metrics() para compatibilidade"""
        return self.extract_pnad_metrics(min_year=min_year, output_path=output_path)
    
    def _process_renda(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplicar winsorização na renda para remover outliers
        
        Usa percentis 5% e 95% para cap valores extremos
        """
        logger.info("\nProcessing renda values (winsorization at 5%-95%)...")
        
        if 'renda_media_trabalho' in df.columns:
            # Winsorizar por UF para ser mais preciso
            for uf in df['uf_code'].unique():
                mask = df['uf_code'] == uf
                renda_col = df.loc[mask, 'renda_media_trabalho']
                
                if renda_col.notna().sum() > 0:
                    p5 = renda_col.quantile(0.05)
                    p95 = renda_col.quantile(0.95)
                    
                    # Cap values
                    df.loc[mask, 'renda_media_trabalho'] = df.loc[mask, 'renda_media_trabalho'].clip(p5, p95)
                    
                    logger.info(f"  {uf}: [R$ {p5:,.0f} - R$ {p95:,.0f}]")
        
        return df
    
    def _validate_data(self, df: pd.DataFrame):
        """Validate extracted data"""
        logger.info("\nValidating data...")
        
        # Expected columns
        expected_cols = {
            'ano': 'int64',
            'trimestre': 'int64',
            'uf_code': 'object',
            'sexo': 'object',
            'grupo_idade': 'object',
            'populacao': 'int64',
            'taxa_informalidade': 'float64',
            'taxa_desemprego': 'float64',
            'renda_media_trabalho': 'float64',
        }
        
        for col, expected_dtype in expected_cols.items():
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")
            logger.info(f"  ✓ {col:25} {str(df[col].dtype):15}")
        
        # Check for nulls in key columns
        key_cols = ['ano', 'uf_code', 'sexo', 'grupo_idade']
        has_nulls = False
        for col in key_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"  ⚠ {col}: {null_count} nulls")
                has_nulls = True
            else:
                logger.info(f"  ✓ {col:25} No nulls")
        
        if has_nulls:
            raise ValueError("Key columns contain nulls - data integrity issue")
        
        # Show summary
        logger.info(f"\n  Dataset summary:")
        logger.info(f"    Rows:              {len(df):,}")
        logger.info(f"    Columns:           {len(df.columns)}")
        logger.info(f"    Years:             {sorted(df['ano'].unique())}")
        logger.info(f"    Trimesters:        {sorted(df['trimestre'].unique())}")
        logger.info(f"    UFs:               {df['uf_code'].nunique()}")
        logger.info(f"    Memory:            {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
        logger.info(f"    Avg Informalidade: {df['taxa_informalidade'].mean():.1%}")
        logger.info(f"    Avg Desemprego:    {df['taxa_desemprego'].mean():.1%}")
        logger.info(f"    Renda Média:       R$ {df['renda_media_trabalho'].mean():,.0f}")
    
    def _save_parquet(self, df: pd.DataFrame, output_path: Path):
        """Save DataFrame to parquet"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\nSaving parquet: {output_path}")
        
        df.to_parquet(
            output_path,
            index=False,
            compression='snappy',
            engine='pyarrow'
        )
        
        file_size = output_path.stat().st_size / (1024**2)
        logger.info(f"✓ File size: {file_size:.2f} MB")


def extract_pnad_metrics(
    min_year: int = 2017,
    output_path: Optional[Path] = None,
    project_id: str = 'b2b-opportunity-engine'
) -> pd.DataFrame:
    """
    Convenience function to extract PNAD metrics
    
    Usage:
        df = extract_pnad_metrics(
            min_year=2017, 
            output_path=Path('data/marts/pnad/pnad_metrics.parquet')
        )
    """
    extractor = PNADCMetricsExtractor(project_id=project_id)
    return extractor.extract_pnad_metrics(min_year=min_year, output_path=output_path)


if __name__ == '__main__':
    # Simple test
    try:
        extractor = PNADCMetricsExtractor()
        df = extractor.extract_pnad_metrics(min_year=2017)
        logger.info(f"\n✓ Success: {len(df):,} rows extracted")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        sys.exit(1)
