#!/usr/bin/env python
"""Regenerar parquets corruptos"""

import pandas as pd
from pathlib import Path

print("\n=== Regenerando parquets corruptos ===\n")

# Path
data_dir = Path("data/processed")

# Test 1: companies_agg.csv -> parquet
print("[1] Carregando companies_agg.csv...")
try:
    df = pd.read_csv(data_dir / "companies_agg.csv")
    print(f"    Loaded: {len(df)} rows")

    # Save as parquet
    parquet_path = data_dir / "companies_agg.parquet"
    df.to_parquet(parquet_path, engine="pyarrow", compression="snappy")
    print(f"    ✓ Saved: {parquet_path}")
except Exception as e:
    print(f"    ✗ Error: {e}")

print("\n[2] Verificando outros parquets...")
parquets = ["opportunity_scores.parquet", "caged_state_sector_year.parquet"]

for parquet in parquets:
    try:
        path = data_dir / parquet
        df = pd.read_parquet(path)
        print(f"    ✓ {parquet}: OK ({len(df)} rows)")
    except Exception as e:
        print(f"    ✗ {parquet}: {type(e).__name__}")

print("\n✅ Regeneracao concluida")
