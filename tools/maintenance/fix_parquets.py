"""Regenerate parquet files from CSV sources - UTF-8 safe"""

import os
from pathlib import Path
import pandas as pd

# Setup paths
project_root = Path(__file__).parent
data_dir = project_root / "data" / "processed"
data_dir.mkdir(parents=True, exist_ok=True)

# CSV source file
csv_path = data_dir / "companies_agg.csv"
parquet_path = data_dir / "companies_agg.parquet"

print("Regenerating parquet files...")
print("-" * 60)

try:
    print(f"[1] Loading {csv_path.name}...")
    df = pd.read_csv(csv_path, encoding="utf-8")
    print(f"    Loaded: {len(df)} rows, {len(df.columns)} columns")

    # Save as parquet
    df.to_parquet(parquet_path, index=False, compression="snappy", engine="pyarrow")

    file_size = parquet_path.stat().st_size / 1024
    print(f"    Saved: {parquet_path} ({file_size:.1f} KB)")

except Exception as e:
    print(f"    Error: {e}")
    import traceback

    traceback.print_exc()

print("-" * 60)
print("Done!")
