#!/usr/bin/env python3
"""
Script para reconstruir parquets usando fastparquet (mais compatível).
"""

import pandas as pd
from pathlib import Path
import sys

print("=" * 70)
print("RECONSTRUINDO PARQUETS COM FASTPARQUET")
print("=" * 70)

# 1. Reconstruir companies_agg.parquet
print("\n[1] Reconstruindo companies_agg.parquet...")
try:
    csv_path = Path("data/processed/companies_agg.csv")
    parquet_path = Path("data/processed/companies_agg.parquet")

    df = pd.read_csv(csv_path)
    print(f"    ✓ CSV carregado: {len(df)} linhas")

    df.to_parquet(parquet_path, engine="fastparquet", compression="snappy")
    print(f"    ✓ Parquet salvo com fastparquet")

    df_test = pd.read_parquet(parquet_path, engine="fastparquet")
    print(f"    ✓ Verificação: {len(df_test)} linhas")
except Exception as e:
    print(f"    ✗ Erro: {e}")

# 2. Reconstruir opportunity_scores
print("\n[2] Reconstruindo opportunity_scores.parquet...")
try:
    backup_path = Path("data/processed/opportunity_scores.parquet.bak")
    parquet_path = Path("data/processed/opportunity_scores.parquet")

    df = pd.read_parquet(backup_path, engine="fastparquet")
    print(f"    ✓ Backup carregado: {len(df)} linhas")

    df.to_parquet(parquet_path, engine="fastparquet", compression="snappy")
    print(f"    ✓ Parquet salvo com fastparquet")

    df_test = pd.read_parquet(parquet_path, engine="fastparquet")
    print(f"    ✓ Verificação: {len(df_test)} linhas")
except Exception as e:
    print(f"    ✗ Erro: {e}")

# 3. Reconstruir caged
print("\n[3] Reconstruindo caged_state_sector_year.parquet...")
try:
    backup_path = Path("data/processed/caged_state_sector_year.parquet.bak")
    parquet_path = Path("data/processed/caged_state_sector_year.parquet")

    df = pd.read_parquet(backup_path, engine="fastparquet")
    print(f"    ✓ Backup carregado: {len(df)} linhas")

    df.to_parquet(parquet_path, engine="fastparquet", compression="snappy")
    print(f"    ✓ Parquet salvo com fastparquet")

    df_test = pd.read_parquet(parquet_path, engine="fastparquet")
    print(f"    ✓ Verificação: {len(df_test)} linhas")
except Exception as e:
    print(f"    ✗ Erro: {e}")

print("\n" + "=" * 70)
print("✅ Reconstrução concluída!")
print("=" * 70)
