"""
Extract PNAD Contínua data from BigQuery (Base dos Dados)

Módulo para extrair dados da PNAD Contínua agregados por:
- UF (Unidade da Federação)
- Ano
- Sexo
- Grupo de idade

Source: basedosdados.br_ibge_pnadc (table: ano_uf_grupo_idade)
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

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] | %(levelname)-8s | %(message)s', '%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class PNADCExtractor:
    """
    Extrai dados PNAD Contínua do BigQuery (Base dos Dados)
    
    Usa tabela agregada 'ano_uf_grupo_idade' para otimizar custos:
    - Dados já agregados por UF, ano, sexo, grupo de idade
    - ~2000 linhas (27 UFs × 3 anos × 2 sexos × ~15 grupos)
    - Baixo custo de query (~50MB processado)
    """
    
    def __init__(self, project_id: str = 'b2b-opportunity-engine'):
        """
        Initialize BigQuery client with ADC (Application Default Credentials)
        
        Args:
            project_id: GCP project for billing
        """
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        logger.info(f"✓ BigQuery client initialized (project: {project_id})")
    
    def extract_pnad_data(
        self, 
        min_year: int = 2017,
        output_path: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Extrai dados PNAD Contínua
        
        NOTA: Dados disponíveis em basedosdados.br_ibge_pnadc.ano_uf_grupo_idade
        cobrem período 2012-2019 (table agregada pelo IBGE)
        
        Args:
            min_year: Ano mínimo para filtro (default 2017 = últimos 3 anos disponíveis)
            output_path: Path para salvar parquet. Se None, retorna só DataFrame
            
        Returns:
            DataFrame com dados PNAD agregados
        """
        
        logger.info(f"Extracting PNAD data (min_year={min_year})...")
        
        # SQL otimizada - usa tabela agregada para baixo custo
        query = f"""
        SELECT
            ano,
            id_uf as uf_code,
            sexo,
            grupo_idade,
            populacao,
            CURRENT_TIMESTAMP() as extracao_data
        FROM `basedosdados.br_ibge_pnadc.ano_uf_grupo_idade`
        WHERE ano >= {min_year}
        ORDER BY ano DESC, id_uf, sexo, grupo_idade
        """
        
        logger.info("Executing BigQuery...")
        
        job_config = bigquery.QueryJobConfig(
            use_query_cache=True,
            priority=bigquery.QueryPriority.INTERACTIVE,
            maximum_bytes_billed=int(1e8),  # Max 100MB
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
            
            # Validations
            self._validate_data(df)
            
            # Save if path provided
            if output_path:
                self._save_parquet(df, output_path)
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            raise
    
    def _validate_data(self, df: pd.DataFrame):
        """Validate extracted data"""
        logger.info("\nValidating data...")
        
        # Expected columns
        expected_cols = {
            'ano': 'int64',
            'uf_code': 'object',
            'sexo': 'object',
            'grupo_idade': 'object',
            'populacao': 'int64',
        }
        
        for col, dtype in expected_cols.items():
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")
            logger.info(f"  ✓ {col:20} {str(df[col].dtype):15}")
        
        # Check for nulls in key columns
        key_cols = ['ano', 'uf_code', 'sexo', 'grupo_idade']
        has_nulls = False
        for col in key_cols:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.warning(f"  ⚠ {col}: {null_count} nulls")
                has_nulls = True
            else:
                logger.info(f"  ✓ {col:20} No nulls")
        
        if has_nulls:
            raise ValueError("Key columns contain nulls - data integrity issue")
        
        # Show summary
        logger.info(f"\n  Dataset summary:")
        logger.info(f"    Rows:     {len(df):,}")
        logger.info(f"    Columns:  {len(df.columns)}")
        logger.info(f"    Years:    {sorted(df['ano'].unique())}")
        logger.info(f"    UFs:      {df['uf_code'].nunique()}")
        logger.info(f"    Memory:   {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
    
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


def extract_pnad(
    min_year: int = 2022,
    output_path: Optional[Path] = None,
    project_id: str = 'b2b-opportunity-engine'
) -> pd.DataFrame:
    """
    Convenience function to extract PNAD data
    
    Usage:
        df = extract_pnad(min_year=2022, output_path=Path('data/pnad.parquet'))
    """
    extractor = PNADCExtractor(project_id=project_id)
    return extractor.extract_pnad_data(min_year=min_year, output_path=output_path)


if __name__ == '__main__':
    # Simple test
    try:
        extractor = PNADCExtractor()
        df = extractor.extract_pnad_data(min_year=2022)
        logger.info(f"\n✓ Success: {len(df):,} rows extracted")
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        sys.exit(1)
