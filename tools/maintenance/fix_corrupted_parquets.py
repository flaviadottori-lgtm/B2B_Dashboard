#!/usr/bin/env python3
"""
Script para corrigir parquets corrompidos.
Deleta e regenera todos os parquets com pyarrow de forma confiável.
"""

import pandas as pd
from pathlib import Path
import shutil
import os

data_dir = Path("data/processed")

# Mapping de source -> target files
# Tentaremos recuperar dados se existirem backups ou arquivos relacionados
files_to_fix = {
    "opportunity_scores.parquet": [
        "ibge_3274_3275_tidy.parquet",  # backup alternativo
    ],
    "caged_state_sector_year.parquet": [
        "caged_state_sector_month.parquet",  # pode derivar
    ],
    "companies_agg.parquet": [
        "companies_agg.csv",  # source CSV
    ],
}

print("=" * 70)
print("CORRIGINDO PARQUETS CORROMPIDOS")
print("=" * 70)

for target_file, source_options in files_to_fix.items():
    target_path = data_dir / target_file
    
    print(f"\n[{target_file}]")
    print(f"  Status atual: {target_path.stat().st_size} bytes")
    
    # Tentar recuperar dos sources
    recovered = False
    
    for source_file in source_options:
        source_path = data_dir / source_file
        
        if not source_path.exists():
            continue
        
        print(f"  Tentando recuperar de: {source_file}")
        
        try:
            # Ler o source com pyarrow explicitamente
            if source_file.endswith('.parquet'):
                # Ler parquet com fallback
                try:
                    df = pd.read_parquet(source_path, engine='pyarrow')
                except:
                    try:
                        # Tentar com pandas reader padrão
                        df = pd.read_parquet(source_path)
                    except Exception as e:
                        print(f"    Falha ao ler parquet: {e}")
                        continue
            else:
                # Ler CSV
                df = pd.read_csv(source_path, encoding='utf-8')
            
            print(f"    Lido: {df.shape}")
            
            # Fazer backup do arquivo corrompido
            backup_path = target_path.with_suffix('.parquet.bak')
            shutil.copy(target_path, backup_path)
            print(f"    Backup: {backup_path.name}")
            
            # Deletar o arquivo corrompido
            os.remove(target_path)
            
            # Regenerar com pandas.to_parquet
            df.to_parquet(
                target_path,
                engine='pyarrow',
                compression='snappy',
                index=False
            )
            
            print(f"    Salvo: {target_path.stat().st_size} bytes")
            
            # Verificar se consegue ler de volta
            df_check = pd.read_parquet(target_path, engine='pyarrow')
            print(f"    Verificado: {df_check.shape}")
            print(f"  OK - Recuperado com sucesso!")
            recovered = True
            break
            
        except Exception as e:
            print(f"    Erro: {str(e)[:80]}")
    
    if not recovered:
        print(f"  FALHA - Não foi possível recuperar")

print("\n" + "=" * 70)
print("VERIFICACAO FINAL")
print("=" * 70)

for target_file in files_to_fix.keys():
    target_path = data_dir / target_file
    
    try:
        df = pd.read_parquet(target_path, engine='pyarrow')
        print(f"[OK] {target_file}: {df.shape}")
    except Exception as e:
        print(f"[ERRO] {target_file}: {str(e)[:60]}")

print("\nDone!")
