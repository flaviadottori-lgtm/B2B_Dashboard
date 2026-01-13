from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"

print("\n📁 Arquivos em data/processed:\n")

for f in PROCESSED.glob("*.parquet"):
    print(f"➡ {f.name}")

    try:
        df = pd.read_parquet(f)

        print(f"   Linhas: {len(df):,}")
        print(f"   Colunas: {len(df.columns)}")
        print(f"   Campos:")
        for c in df.columns:
            print(f"     - {c}")

        print("\n   Tipos:")
        print(df.dtypes)
        print("\n   Exemplo:")
        print(df.head(3))
        print("-" * 80)

    except Exception as e:
        print("   ❌ Erro ao abrir:", e)
