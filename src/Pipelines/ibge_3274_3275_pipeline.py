from __future__ import annotations

import csv
import re
from pathlib import Path

import numpy as np
import pandas as pd

# ================= PATHS =================
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_3274 = BASE_DIR / "data" / "raw" / "ibge" / "sidra_3274_2008_2021_raw.csv"
RAW_3275 = BASE_DIR / "data" / "raw" / "ibge" / "sidra_3275_2008_2021_raw.csv"
OUT_DIR = BASE_DIR / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

UF_TO_REGION = {
    "AC": "Norte",
    "AL": "Nordeste",
    "AM": "Norte",
    "AP": "Norte",
    "BA": "Nordeste",
    "CE": "Nordeste",
    "DF": "Centro-Oeste",
    "ES": "Sudeste",
    "GO": "Centro-Oeste",
    "MA": "Nordeste",
    "MG": "Sudeste",
    "MS": "Centro-Oeste",
    "MT": "Centro-Oeste",
    "PA": "Norte",
    "PB": "Nordeste",
    "PE": "Nordeste",
    "PI": "Nordeste",
    "PR": "Sul",
    "RJ": "Sudeste",
    "RN": "Nordeste",
    "RO": "Norte",
    "RR": "Norte",
    "RS": "Sul",
    "SC": "Sul",
    "SE": "Nordeste",
    "SP": "Sudeste",
    "TO": "Norte",
}

STATE_NAME_TO_UF = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amapá": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "ceará": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "espírito santo": "ES",
    "goias": "GO",
    "goiás": "GO",
    "maranhao": "MA",
    "maranhão": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "para": "PA",
    "pará": "PA",
    "paraiba": "PB",
    "paraíba": "PB",
    "parana": "PR",
    "paraná": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "piauí": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "rondônia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "são paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}

YEAR_RE = re.compile(r"^(19|20)\d{2}$")


# ================= IO =================
def _read_rows_semicolon(path: Path) -> list[list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")
    rows: list[list[str]] = []
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for r in reader:
            r = [c.strip() for c in r]
            if not any(r):
                continue
            rows.append(r)
    if not rows:
        raise ValueError(f"Arquivo vazio ou ilegível: {path}")
    return rows


def _pad_rows(rows: list[list[str]]) -> list[list[str]]:
    max_len = max(len(r) for r in rows)
    return [r + [""] * (max_len - len(r)) for r in rows]


# ================= HELPERS =================
def _extract_state(cell: str) -> str | None:
    s = (cell or "").strip()
    if not s:
        return None

    if "-" in s:
        left = s.split("-", 1)[0].strip().upper()
        if len(left) == 2 and left in UF_TO_REGION:
            return left

    if len(s) == 2 and s.upper() in UF_TO_REGION:
        return s.upper()

    return STATE_NAME_TO_UF.get(s.lower())


def _find_header(rows: list[list[str]]) -> tuple[int, int, int]:
    """
    - idx_year: linha que contém vários anos
    - idx_sector: linha abaixo com setores
    - idx_data_start: início das linhas de dados
    """
    idx_year = -1
    for i, r in enumerate(rows[:600]):
        if sum(1 for c in r if YEAR_RE.match(c)) >= 3:
            idx_year = i
            break

    if idx_year == -1:
        for i, r in enumerate(rows[:600]):
            if any(YEAR_RE.match(c) for c in r):
                idx_year = i
                break

    if idx_year == -1:
        raise ValueError("Não encontrei a linha com anos no cabeçalho.")

    idx_sector = idx_year + 1
    if idx_sector >= len(rows):
        raise ValueError("Não encontrei a linha de setores após a linha dos anos.")

    idx_data_start = -1
    for i in range(idx_sector + 1, min(idx_sector + 800, len(rows))):
        first = (rows[i][0] or "").strip().upper()
        if first in {"UF", "GR", "BR"}:
            idx_data_start = i
            break

    if idx_data_start == -1:
        for i in range(idx_sector + 1, min(idx_sector + 1200, len(rows))):
            if any(_extract_state(c) for c in rows[i][:12]):
                idx_data_start = i
                break

    if idx_data_start == -1:
        raise ValueError("Não encontrei o início das linhas de dados.")

    return idx_year, idx_sector, idx_data_start


def _infer_variable(rows: list[list[str]]) -> str:
    for r in rows[:120]:
        line = " ".join([c for c in r if c]).strip()
        if not line:
            continue
        if line.lower().startswith("variável"):
            return line.split("-", 1)[1].strip() if "-" in line else line
    return "Valor"


def _detect_stride(sector_row: list[str], start_col: int, end_col: int) -> int:
    """
    - 3274: valor+unidade (stride 2) -> presença de "Unidades"
    - 3275: só valor (stride 1)
    """
    window = [c.strip().lower() for c in sector_row[start_col:end_col] if c.strip()]
    if not window:
        return 1

    units_hits = sum(1 for c in window if c == "unidades" or "unidade" in c)
    if units_hits >= 3:
        return 2

    pairs = 0
    i = start_col
    while i + 1 < end_col:
        a = (sector_row[i] or "").strip()
        b = (sector_row[i + 1] or "").strip().lower()
        if a and (b == "unidades" or "unidade" in b):
            pairs += 1
        i += 2
    if pairs >= 3:
        return 2

    return 1


def _build_year_sector_map(
    year_row: list[str], sector_row: list[str]
) -> list[tuple[int, str, int]]:
    year_starts: list[tuple[int, int]] = [
        (j, int(c)) for j, c in enumerate(year_row) if YEAR_RE.match(c)
    ]
    if not year_starts:
        raise ValueError("Não encontrei blocos de anos no cabeçalho.")

    ranges: list[tuple[int, int, int]] = []
    for i, (start, y) in enumerate(year_starts):
        end = year_starts[i + 1][0] if i + 1 < len(year_starts) else len(year_row)
        ranges.append((y, start, end))

    mapping: list[tuple[int, str, int]] = []
    for y, start, end in ranges:
        stride = _detect_stride(sector_row, start, end)

        j = start
        while j < end:
            sec = (sector_row[j] or "").strip()
            if not sec:
                j += 1
                continue
            if sec.lower() == "unidades":
                j += 1
                continue

            mapping.append((y, sec, j))
            j += stride

    if len(mapping) < 20:
        raise ValueError(
            "Mapeamento de (ano, setor) pequeno demais. Layout do cabeçalho pode ser diferente."
        )
    return mapping


def _row_has_any_keywords(row: list[str], keywords: list[str], max_cols: int = 18) -> bool:
    keys = [k.lower() for k in keywords]
    for cell in row[:max_cols]:
        c = (cell or "").strip().lower()
        if any(k in c for k in keys):
            return True
    return False


# ================= CORE PARSER =================
def parse_sidra_multi_year(path: Path, require_total: bool) -> pd.DataFrame:
    """
    DF LONG:
    year, state, region, sector, variable, value

    require_total=True  -> 3274 (filtra 'total' nas primeiras colunas)
    require_total=False -> 3275 (não filtra por 'total'; evita apenas palavras de evento se existirem)
    """
    rows = _pad_rows(_read_rows_semicolon(path))
    idx_year, idx_sector, idx_data_start = _find_header(rows)

    var_name = _infer_variable(rows)
    mapping = _build_year_sector_map(rows[idx_year], rows[idx_sector])

    records: list[dict] = []

    for r in rows[idx_data_start:]:
        first = (r[0] or "").strip().upper()
        likely_row = first in {"UF", "GR", "BR"} or any(_extract_state(c) for c in r[:12])
        if not likely_row:
            continue

        uf = None
        for cell in r[:12]:
            ufx = _extract_state(cell)
            if ufx:
                uf = ufx
                break
        if not uf or uf not in UF_TO_REGION:
            continue

        if require_total:
            if not _row_has_any_keywords(r, ["total"], max_cols=22):
                continue
        else:
            # 3275 normalmente não tem eventos, mas se tiver, evita os que não são "estoque"
            if _row_has_any_keywords(
                r, ["entrada", "saída", "saida", "nascimento", "reentrada", "sobreviv"], max_cols=24
            ):
                continue

        for y, sec, col in mapping:
            raw = (r[col] or "").strip()
            if not raw:
                val = 0.0
            else:
                raw2 = raw.replace(".", "").replace(",", ".")
                try:
                    val = float(raw2)
                except Exception:
                    val = 0.0

            records.append(
                {
                    "year": y,
                    "state": uf,
                    "region": UF_TO_REGION[uf],
                    "sector": sec,
                    "variable": var_name,
                    "value": val,
                }
            )

    return pd.DataFrame(records, columns=["year", "state", "region", "sector", "variable", "value"])


def _norm(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    if len(s) == 0 or s.max() == s.min():
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.min()) / (s.max() - s.min())


# ================= MAIN =================
def main():
    print(f"✅ Lendo 3274: {RAW_3274}")
    df3274 = parse_sidra_multi_year(RAW_3274, require_total=True)

    print(f"✅ Lendo 3275: {RAW_3275}")
    df3275 = parse_sidra_multi_year(RAW_3275, require_total=False)

    if df3274.empty:
        raise ValueError("3274 veio vazio. O parser não encontrou UF + 'total' no arquivo.")
    if df3275.empty:
        raise ValueError("3275 veio vazio. Provável layout diferente no cabeçalho (anos/setores).")

    # 3274 normalmente é 1 variável por export (no seu caso: unidades locais)
    v3274 = df3274["variable"].iloc[0].lower()

    if ("pessoal ocupado" in v3274) or ("pessoal" in v3274):
        df3274 = df3274.rename(columns={"value": "employment"})
        keep_cols_3274 = ["year", "state", "region", "sector", "employment"]
    elif ("salário" in v3274) or ("salario" in v3274):
        df3274 = df3274.rename(columns={"value": "avg_wage"})
        keep_cols_3274 = ["year", "state", "region", "sector", "avg_wage"]
    else:
        df3274 = df3274.rename(columns={"value": "units"})
        keep_cols_3274 = ["year", "state", "region", "sector", "units"]

    df3274 = (
        df3274[keep_cols_3274]
        .groupby(["year", "state", "region", "sector"], as_index=False)
        .sum(numeric_only=True)
    )

    # 3275 = alto crescimento
    df3275 = df3275.rename(columns={"value": "high_growth_units"})
    df3275 = (
        df3275[["year", "state", "sector", "high_growth_units"]]
        .groupby(["year", "state", "sector"], as_index=False)
        .sum()
    )

    # merge
    df = df3274.merge(df3275, on=["year", "state", "sector"], how="left")
    df["high_growth_units"] = df["high_growth_units"].fillna(0)

    # --------- CORREÇÕES IMPORTANTES ----------
    # Remove agregação "Total" e qualquer "setor" que não seja CNAE real
    df["sector_clean"] = df["sector"].astype(str).str.strip()
    df = df[df["sector_clean"].str.lower() != "total"].copy()
    df = df[~df["sector_clean"].str.lower().str.contains("unidade", na=False)].copy()
    df = df.drop(columns=["sector_clean"])
    # -----------------------------------------

    # garantir colunas
    if "units" not in df.columns:
        df["units"] = np.nan
    if "employment" not in df.columns:
        df["employment"] = np.nan
    if "avg_wage" not in df.columns:
        df["avg_wage"] = np.nan

    df["units"] = df["units"].fillna(0)
    df["high_growth_ratio"] = np.where(df["units"] > 0, df["high_growth_units"] / df["units"], 0.0)

    # CAGR 2008–2021 (units)
    def calc_cagr(g: pd.DataFrame) -> float:
        try:
            start = g.loc[g["year"] == 2008, "units"].values[0]
            end = g.loc[g["year"] == 2021, "units"].values[0]
            return (end / start) ** (1 / 13) - 1 if start > 0 else np.nan
        except Exception:
            return np.nan

    cagr_df = df.groupby(["state", "sector"]).apply(calc_cagr).reset_index(name="cagr_2008_2021")
    df = df.merge(cagr_df, on=["state", "sector"], how="left")

    vol_df = df.groupby(["state", "sector"])["units"].std().reset_index(name="volatility_units")
    df = df.merge(vol_df, on=["state", "sector"], how="left")

    # Base 2021 para ranking (já sem Total)
    base = df[df["year"] == 2021].copy()

    base["size_n"] = _norm(np.log1p(base["units"]))
    base["hg_n"] = _norm(base["high_growth_units"])
    base["hgr_n"] = _norm(base["high_growth_ratio"])
    base["cagr_n"] = _norm(base["cagr_2008_2021"].fillna(0))
    base["stab_n"] = 1 - _norm(base["volatility_units"].fillna(0))

    base["structural_index"] = 0.45 * base["size_n"] + 0.35 * base["cagr_n"] + 0.20 * base["stab_n"]
    base["growth_index"] = 0.60 * base["hg_n"] + 0.40 * base["hgr_n"]
    base["opportunity_score"] = 100 * (
        0.60 * base["structural_index"] + 0.40 * base["growth_index"]
    )

    # Salvar
    df.to_parquet(OUT_DIR / "ibge_3274_3275_tidy.parquet", index=False)
    base.to_parquet(OUT_DIR / "opportunity_scores.parquet", index=False)

    print("✅ Arquivos gerados:")
    print(f" - {OUT_DIR / 'ibge_3274_3275_tidy.parquet'}")
    print(f" - {OUT_DIR / 'opportunity_scores.parquet'}")
    print("\n🔎 Top 10 opportunities (2021) — sem 'Total':")
    show_cols = [
        "state",
        "region",
        "sector",
        "units",
        "high_growth_units",
        "high_growth_ratio",
        "cagr_2008_2021",
        "opportunity_score",
    ]
    print(base[show_cols].sort_values("opportunity_score", ascending=False).head(10))


if __name__ == "__main__":
    main()
