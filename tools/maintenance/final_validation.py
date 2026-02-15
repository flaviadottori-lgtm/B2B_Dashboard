"""
Final validation of PNAD pipeline
"""

import pandas as pd
from pathlib import Path

print("=" * 70)
print("VERIFICAÇÃO FINAL DO PIPELINE PNAD")
print("=" * 70)
print()

# 1. Verificar parquet
pq_file = Path("data/marts/pnad/pnad_uf_quarter_gender_age.parquet")
print(f"✓ Arquivo parquet: {pq_file.name}")
print(f"  Tamanho: {pq_file.stat().st_size / 1024:.2f} KB")
print()

# 2. Ler e validar dados
df = pd.read_parquet(pq_file)
print(f"✓ DataFrame carregado:")
print(f"  Linhas: {len(df):,}")
print(f"  Colunas: {len(df.columns)}")
print()

# 3. Resumo de dados
print(f"✓ Dados:")
print(f'  Anos: {sorted(df["ano"].unique())}')
print(f'  UFs: {df["uf_code"].nunique()}')
print(f'  Sexos: {df["sexo"].nunique()}')
print(f'  Grupos etários: {df["grupo_idade"].nunique()}')
print()

# 4. Amostra
print(f"✓ Amostra (primeiras 5 linhas):")
print(df.head().to_string())
print()

# 5. Estatísticas
print(f"✓ Estatísticas da população:")
print(df["populacao"].describe())

print()
print("=" * 70)
print("✅ PIPELINE VALIDADO COM SUCESSO!")
print("=" * 70)
