import pandas as pd

path = "data/processed/opportunity_scores.parquet"
df = pd.read_parquet(path)

print("Colunas:", df.columns.tolist())
print("Shape:", df.shape)

if "year" in df.columns:
    print("✅ Tem year. Anos:", sorted(df["year"].dropna().unique())[:10], "...",
          sorted(df["year"].dropna().unique())[-10:])
else:
    print("❌ NÃO tem year.")
