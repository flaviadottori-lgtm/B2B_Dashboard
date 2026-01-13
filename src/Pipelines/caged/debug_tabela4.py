import pandas as pd
import re

UF = {
    "AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG",
    "PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"
}
pat = re.compile(r"\b([A-Z]{2})\b")

fp = "data/raw/caged/caged_xlsx/novo_caged_2025_09.xlsx"

x = pd.ExcelFile(fp, engine="openpyxl")
print("SHEETS:", x.sheet_names)

# 1) descobre quantas colunas existem de verdade na Tabela 4
preview = pd.read_excel(x, sheet_name="Tabela 4", header=None, nrows=5)
ncols = preview.shape[1]
print("Tabela 4 ncols:", ncols)

# 2) lê só as colunas existentes
df = pd.read_excel(x, sheet_name="Tabela 4", header=None, nrows=200)
df = df.ffill(axis=0).ffill(axis=1)

print("Shape lido:", df.shape)

# 3) encontra linhas com UFs (se existirem)
best = []
for r in range(min(120, len(df))):
    row = df.iloc[r, :].tolist()
    ufs = set()
    for v in row:
        if v is None:
            continue
        m = pat.search(str(v).upper())
        if m and m.group(1) in UF:
            ufs.add(m.group(1))
    if len(ufs) >= 2:
        best.append((r, len(ufs), sorted(ufs)[:15]))

best = sorted(best, key=lambda t: t[1], reverse=True)[:15]
print("TOP ROWS WITH UFs (row, uf_count, sample_ufs):")
print("\n".join([str(b) for b in best]) if best else "NONE")

# 4) mostra as 15 primeiras linhas e 12 primeiras colunas (pra enxergar o layout)
print("\n--- HEAD (first 15 rows, first 12 cols) ---")
print(df.iloc[:15, :min(12, df.shape[1])].to_string(index=True, header=False))

out = "preview_tabela4_2025_09.csv"
df.to_csv(out, index=False, header=False, encoding="utf-8-sig")
print("\nSaved preview CSV:", out)
