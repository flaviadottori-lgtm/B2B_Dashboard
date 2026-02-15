from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
XLSX = ROOT / "data" / "raw" / "caged" / "caged_xlsx" / "novo_caged_2025_01.xlsx"

print("📄", XLSX)
print("Existe?", XLSX.exists())
if not XLSX.exists():
    raise FileNotFoundError(XLSX)

xls = pd.ExcelFile(XLSX, engine="openpyxl")

print("\n📑 Abas:")
for s in xls.sheet_names:
    print(" -", s)


def first_data_row(df0: pd.DataFrame) -> int | None:
    # df0 é lido com header=None
    # acha a primeira linha que tem pelo menos 3 células preenchidas
    filled = df0.notna().sum(axis=1).to_numpy()
    idx = np.where(filled >= 3)[0]
    return int(idx[0]) if len(idx) else None


print("\n🔎 Varredura das abas (procurando dados reais):")
candidates = []
for s in xls.sheet_names:
    try:
        # lê um pedaço grande SEM header
        df0 = pd.read_excel(XLSX, sheet_name=s, header=None, nrows=120, engine="openpyxl")
        r0 = first_data_row(df0)
        if r0 is None:
            print(f" - {s}: vazio/sem dados detectáveis")
            continue

        # pega umas linhas ao redor para inspecionar
        sample = df0.iloc[max(0, r0 - 2) : r0 + 6, :15]
        non_empty_cols = sample.notna().sum().sum()

        print(f" - {s}: primeira linha com dados ~ linha {r0} (amostra abaixo)")
        print(sample)
        print("-" * 80)

        candidates.append((s, r0, non_empty_cols))
    except Exception as e:
        print(f" - {s}: erro ao ler ({e})")

# resumo do melhor candidato
if not candidates:
    print(
        "\n❌ Nenhuma aba com dados detectáveis. Talvez o arquivo seja protegido ou o conteúdo esteja em imagens."
    )
else:
    candidates.sort(key=lambda x: (x[2], -x[1]), reverse=True)
    best = candidates[0]
    print(f"\n✅ Melhor candidata: {best[0]} (primeira linha dados ~ {best[1]})")
