# src/Pipelines/build_companies_agg_from_sidra_wide.py
from __future__ import annotations

from pathlib import Path
import pandas as pd
import re

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW = PROJECT_ROOT / "data" / "raw" / "ibge" / "sidra_3274_2008_2021_raw.csv"
OUT_DIR = PROJECT_ROOT / "data" / "processed"
OUT_PARQUET = OUT_DIR / "companies_agg.parquet"

YEAR_RE = re.compile(r"^\d{4}$")


def _split(line: str) -> list[str]:
    """Split seguro por ; removendo aspas e espaços."""
    parts = [p.strip().strip('"') for p in line.strip().split(";")]
    return parts


def _is_data_row(parts: list[str]) -> bool:
    """
    Detecta uma linha de dados do SIDRA.
    No seu arquivo, começa com "BR";"1"; ... ou "GR";"1"; ...
    """
    if len(parts) < 5:
        return False
    first = parts[0]
    # geralmente BR/GR/UF etc
    return first in {"BR", "GR"} or (len(first) == 2 and first.isalpha())


def parse_sidra_wide(path: Path) -> pd.DataFrame:
    """
    Parser específico para CSV SIDRA 'achatado' em múltiplas linhas de header:
    - acha a primeira linha de dados (BR/GR/UF)
    - pega as duas linhas anteriores como headers: (anos) e (setores)
    - constrói colunas: <ano>|<setor> e devolve DataFrame wide limpo
    """
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with open(path, "r", encoding="latin1") as f:
        lines = f.readlines()

    # acha a primeira linha de dados
    data_start = None
    for i, line in enumerate(lines):
        parts = _split(line)
        if _is_data_row(parts):
            data_start = i
            break

    if data_start is None:
        raise ValueError("Não encontrei nenhuma linha de dados (ex: BR;1;...).")

    # As duas linhas antes dos dados são os headers (no layout que você mostrou)
    # - linha_years: contém ...;"2008";;;;;;"2009";...
    # - linha_sectors: contém ...;"Total";"A ...";"B ...";...
    # Às vezes pode existir uma linha extra "Nível;Cód;..." antes delas.
    # Então vamos procurar pra trás a linha com vários anos.
    header_years_idx = None
    for j in range(data_start - 1, max(-1, data_start - 10), -1):
        parts = _split(lines[j])
        # consideramos linha de anos se tiver pelo menos 5 anos distintos
        years = [p for p in parts if YEAR_RE.match(p)]
        if len(set(years)) >= 5:
            header_years_idx = j
            break

    if header_years_idx is None:
        raise ValueError("Não encontrei a linha de anos (2008..2021) antes dos dados.")

    header_sectors_idx = header_years_idx + 1
    if header_sectors_idx >= len(lines):
        raise ValueError("Linha de setores não encontrada logo após linha de anos.")

    years_line = _split(lines[header_years_idx])
    sectors_line = _split(lines[header_sectors_idx])

    # Agora lemos a parte de dados (de data_start em diante) como tabela simples
    # Usamos pandas com header=None e sep=";"
    df = pd.read_csv(
        path,
        sep=";",
        encoding="latin1",
        skiprows=data_start,
        header=None,
        engine="python",
        on_bad_lines="skip",
    )

    # Constrói nomes das colunas:
    # As primeiras 4 colunas são fixas:
    base_cols = ["level", "code", "state_raw", "event"]
    n_cols = df.shape[1]

    # Garantir que temos pelo menos 4 colunas
    if n_cols < 5:
        raise ValueError(f"Arquivo parece truncado. Colunas detectadas: {n_cols}")

    # Para as colunas 4..fim, vamos construir um vetor year_for_pos e sector_for_pos
    # Estratégia:
    # - A linha "years_line" tem anos espalhados e muitas strings vazias
    # - Preenchemos forward-fill: quando aparece um ano, ele vale até o próximo ano
    # - A linha "sectors_line" tem os nomes dos setores para cada posição
    #
    # Importante: years_line e sectors_line incluem também as colunas base no começo
    # (Nível/Cód/UF/Evento). Então alinhamos pelo índice.
    max_header_len = max(len(years_line), len(sectors_line), n_cols)
    years_line += [""] * (max_header_len - len(years_line))
    sectors_line += [""] * (max_header_len - len(sectors_line))

    # forward-fill de anos
    years_ff = []
    cur = ""
    for p in years_line:
        if YEAR_RE.match(p):
            cur = p
        years_ff.append(cur)

    # Agora monta as colunas
    cols = []
    cols.extend(base_cols)

    for idx in range(4, n_cols):
        y = years_ff[idx] if idx < len(years_ff) else ""
        s = sectors_line[idx] if idx < len(sectors_line) else f"col_{idx}"
        y = y.strip()
        s = s.strip()
        if not YEAR_RE.match(y):
            # se não achou ano, marca como unknown (vamos dropar depois)
            cols.append(f"unknown|{s or f'col_{idx}'}")
        else:
            cols.append(f"{y}|{s or 'unknown'}")

    df.columns = cols[:n_cols]

    # Limpa base
    df["year_marker"] = 1  # só pra garantir dataframe não vazio

    return df


def wide_to_long(df_wide: pd.DataFrame) -> pd.DataFrame:
    base_cols = ["level", "code", "state_raw", "event"]
    value_cols = [
        c
        for c in df_wide.columns
        if c not in base_cols and "|" in c and not c.startswith("unknown|")
    ]

    long = df_wide.melt(
        id_vars=base_cols,
        value_vars=value_cols,
        var_name="year_sector",
        value_name="value",
    )

    # split year|sector
    ys = long["year_sector"].str.split("|", n=1, expand=True)
    long["year"] = pd.to_numeric(ys[0], errors="coerce")
    long["sector"] = ys[1].astype(str)

    # value -> num
    long["value"] = (
        long["value"]
        .astype(str)
        .str.strip()
        .str.replace('"', "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    long["value"] = pd.to_numeric(long["value"], errors="coerce")

    long = long.dropna(subset=["year", "value"])
    long["year"] = long["year"].astype(int)

    # renomeia
    long = long.rename(columns={"state_raw": "state", "event": "event"})

    return long[["year", "state", "sector", "event", "value"]]


def build_companies_agg(long: pd.DataFrame) -> pd.DataFrame:
    d = long.copy()
    d["event_l"] = d["event"].astype(str).str.lower()

    d["opened"] = d["value"].where(d["event_l"].str.contains("entrada", na=False), 0)
    d["closed"] = d["value"].where(d["event_l"].str.contains("saída|saida", na=False), 0)

    out = d.groupby(["year", "state", "sector"], as_index=False)[["opened", "closed"]].sum()
    out["net"] = out["opened"] - out["closed"]
    out.insert(1, "region", "Brasil")

    # tipos
    for c in ["opened", "closed", "net"]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0).astype(int)

    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("📄 Lendo (parser SIDRA wide multiheader):", RAW)
    df_wide = parse_sidra_wide(RAW)

    print("🔁 wide -> long ...")
    long = wide_to_long(df_wide)

    print("🧮 agregando companies_agg ...")
    out = build_companies_agg(long)

    out.to_parquet(OUT_PARQUET, index=False)

    years = sorted(out["year"].unique().tolist())
    print("✅ Gerado:", OUT_PARQUET)
    print("years:", years)
    print("rows:", len(out))


if __name__ == "__main__":
    main()
