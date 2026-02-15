from __future__ import annotations

import re
import unicodedata
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

print("RUNNING FILE:", __file__)
print("CWD:", Path().resolve())

RAW_DIR = Path("data/raw/caged/caged_xlsx").resolve()
OUT_MONTH = Path("data/processed/caged_state_sector_month.parquet").resolve()
OUT_YEAR = Path("data/processed/caged_state_sector_year.parquet").resolve()

FNAME_RE = re.compile(r"novo_caged_(\d{4})_(\d{2})\.xlsx$", re.IGNORECASE)

UF_SET = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}
UF_TOKEN_RE = re.compile(r"\b(" + "|".join(sorted(UF_SET)) + r")\b", re.IGNORECASE)

STATE_NAME_TO_UF = {
    "acre": "AC",
    "alagoas": "AL",
    "amapa": "AP",
    "amazonas": "AM",
    "bahia": "BA",
    "ceara": "CE",
    "distrito federal": "DF",
    "espirito santo": "ES",
    "goias": "GO",
    "maranhao": "MA",
    "mato grosso": "MT",
    "mato grosso do sul": "MS",
    "minas gerais": "MG",
    "para": "PA",
    "paraiba": "PB",
    "parana": "PR",
    "pernambuco": "PE",
    "piaui": "PI",
    "rio de janeiro": "RJ",
    "rio grande do norte": "RN",
    "rio grande do sul": "RS",
    "rondonia": "RO",
    "roraima": "RR",
    "santa catarina": "SC",
    "sao paulo": "SP",
    "sergipe": "SE",
    "tocantins": "TO",
}

MAX_USECOLS = 500
MAX_NROWS = 520

COL_SCAN_ROWS = 260
GLOBAL_SCAN_ROWS = 360


def _strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


def _norm_str(x) -> str:
    if pd.isna(x):
        return ""
    s = str(x).replace("\n", " ").strip()
    return re.sub(r"\s+", " ", s)


def _norm_key(x) -> str:
    return _strip_accents(_norm_str(x).lower())


def parse_year_month_from_filename(path: Path) -> tuple[int, int]:
    m = FNAME_RE.search(path.name)
    if not m:
        raise ValueError(f"Nome inesperado: {path.name} (esperado: novo_caged_YYYY_MM.xlsx)")
    return int(m.group(1)), int(m.group(2))


def _extract_uf_or_state_name(x) -> str | None:
    """
    Extrai UF a partir de:
      1) tokens UF (AC, SP etc) quando existirem
      2) nomes de estados (ex: 'Mato Grosso do Sul', 'Paraíba', etc)

    ✅ Correção crítica: sempre testar nomes LONGOS antes de curtos
    para evitar colisões:
      - 'mato grosso' vs 'mato grosso do sul'
      - 'para' vs 'paraiba'
    """
    s = _norm_str(x)
    if not s:
        return None

    # 1) tenta UF explícito
    m = UF_TOKEN_RE.search(s.upper())
    if m:
        uf = m.group(1).upper()
        if uf in UF_SET:
            return uf

    # 2) tenta nome do estado (ordenado por comprimento desc)
    key = _norm_key(s)
    for name, uf in sorted(STATE_NAME_TO_UF.items(), key=lambda kv: -len(kv[0])):
        if name in key:
            return uf

    return None


def _to_number_series(s: pd.Series) -> pd.Series:
    s = s.astype(str).str.strip()
    s = s.str.replace("\u00a0", "", regex=False)
    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _find_tabela4_sheet(xls: pd.ExcelFile) -> str:
    for sh in xls.sheet_names:
        shn = sh.strip().lower()
        if shn == "tabela 4" or shn == "tabela4" or "tabela 4" in shn:
            return sh
    raise KeyError("Não encontrei a aba da Tabela 4.")


def _read_excel_safe(xls: pd.ExcelFile, sheet: str, nrows: int, max_cols: int) -> pd.DataFrame:
    prev = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=120)
    ncols = prev.shape[1] if prev is not None else 0
    if ncols <= 0:
        return pd.read_excel(xls, sheet_name=sheet, header=None, nrows=nrows)

    use_n = min(ncols, max_cols)
    return pd.read_excel(
        xls,
        sheet_name=sheet,
        header=None,
        nrows=nrows,
        usecols=list(range(0, use_n)),
    )


def _ffill_vertical_only(df: pd.DataFrame) -> pd.DataFrame:
    # NÃO preencher horizontalmente — quebra header de estados
    return df.ffill(axis=0)


def _detect_header_row_and_sector_col(df: pd.DataFrame) -> tuple[int, int]:
    best = None  # (score, row, sector_col)

    scan_rows = min(240, len(df))
    scan_cols = df.shape[1]

    for r in range(scan_rows):
        row = df.iloc[r, :scan_cols].tolist()

        ufs = []
        for v in row:
            uf = _extract_uf_or_state_name(v)
            if uf:
                ufs.append(uf)
        score = len(set(ufs))

        sector_col = None
        for c, v in enumerate(row):
            if "grupamento de atividades" in _norm_key(v):
                sector_col = c
                break
        if sector_col is None:
            sector_col = 1

        if best is None or score > best[0]:
            best = (score, r, sector_col)

    if best is None or best[0] < 6:
        raise KeyError("Não consegui detectar header_row na Tabela 4.")

    return best[1], best[2]


def _detect_states_by_column_heavy(df: pd.DataFrame) -> list[tuple[int, str]]:
    """
    Detecta estados por COLUNA, varrendo até COL_SCAN_ROWS linhas.
    """
    max_r = min(COL_SCAN_ROWS, len(df))
    pairs = []

    for c in range(df.shape[1]):
        col_vals = df.iloc[:max_r, c]
        found = None
        for v in col_vals:
            uf = _extract_uf_or_state_name(v)
            if uf:
                found = uf
                break
        if found:
            pairs.append((c, found))

    # remove duplicatas por UF mantendo a primeira coluna
    out = []
    seen = set()
    for c, uf in sorted(pairs, key=lambda t: t[0]):
        if uf in seen:
            continue
        seen.add(uf)
        out.append((c, uf))

    return out


def _clean_sector(x) -> str | None:
    t = _norm_str(x)
    if not t:
        return None
    low = t.lower()
    if "grupamento" in low or low == "total" or "tabela" in low:
        return None
    return t


def read_caged_tabela4(path: Path, debug: bool = False) -> pd.DataFrame:
    xls = pd.ExcelFile(path, engine="openpyxl")
    sh = _find_tabela4_sheet(xls)

    raw = _read_excel_safe(xls, sheet=sh, nrows=MAX_NROWS, max_cols=MAX_USECOLS)
    raw = raw.dropna(how="all").reset_index(drop=True)
    filled = _ffill_vertical_only(raw)

    header_row, sector_col = _detect_header_row_and_sector_col(filled)
    state_pairs = _detect_states_by_column_heavy(filled)

    # valida
    ufs_found = sorted({uf for _, uf in state_pairs})
    missing = sorted(list(UF_SET - set(ufs_found)))

    if debug:
        print(f"   🔎 DEBUG sheet: {sh}")
        print(
            f"   🔎 DEBUG header_row: {header_row} | sector_col: {sector_col} | state_cols: {len(state_pairs)}"
        )
        print(f"   🔎 DEBUG UFs found ({len(ufs_found)}): {ufs_found}")
        print(f"   🔎 DEBUG Missing UFs ({len(missing)}): {missing}")

    data = filled.iloc[header_row + 1 :, :].copy()

    records = []
    for _, row in data.iterrows():
        sector = _clean_sector(row.iloc[sector_col] if sector_col < len(row) else None)
        if not sector:
            continue

        for col_idx, uf in state_pairs:
            if col_idx >= len(row):
                continue
            records.append((uf, sector, row.iloc[col_idx]))

    if not records:
        raise KeyError("Tabela 4 encontrada, mas records vazio na extração.")

    df = pd.DataFrame(records, columns=["state", "sector", "job_balance_raw"])
    df["job_balance"] = _to_number_series(df["job_balance_raw"]).fillna(0)

    out = df.groupby(["state", "sector"], as_index=False)["job_balance"].sum()
    return out


def main():
    print("📁 RAW_DIR:", RAW_DIR)
    files = sorted(RAW_DIR.glob("novo_caged_*.xlsx"))

    print(f"📦 XLSX encontrados: {len(files)}")
    print("🗓️ 2024:", len(list(RAW_DIR.glob("novo_caged_2024_*.xlsx"))))
    print("🗓️ 2025:", len(list(RAW_DIR.glob("novo_caged_2025_*.xlsx"))))
    print("📄 Primeiros arquivos:", [f.name for f in files[:5]])

    if not files:
        raise FileNotFoundError(f"Nenhum XLSX em {RAW_DIR}")

    all_rows = []
    ok = 0
    fail = 0

    for idx, fp in enumerate(files):
        year, month = parse_year_month_from_filename(fp)
        print("➡️ Processando:", fp.name)
        try:
            df = read_caged_tabela4(fp, debug=(idx == 0))
            df["year"] = year
            df["month"] = month
            df = df[["year", "month", "state", "sector", "job_balance"]].copy()
            all_rows.append(df)
            ok += 1
        except Exception as e:
            fail += 1
            print(f"⚠️ Falhou em {fp.name}: {e}")

    if not all_rows:
        raise RuntimeError("Nenhum arquivo CAGED foi processado com sucesso. Veja logs acima.")

    month_df = pd.concat(all_rows, ignore_index=True)

    OUT_MONTH.parent.mkdir(parents=True, exist_ok=True)
    month_df.to_parquet(OUT_MONTH, index=False)

    year_df = month_df.groupby(["year", "state", "sector"], as_index=False)["job_balance"].sum()
    year_df.to_parquet(OUT_YEAR, index=False)

    print(
        f"✅ Saved monthly: {OUT_MONTH} | files_ok={ok} files_fail={fail} | "
        f"years={sorted(month_df.year.unique())} | rows={len(month_df):,} | UFs={month_df['state'].nunique()}"
    )
    print(
        f"✅ Saved yearly : {OUT_YEAR} | years={sorted(year_df.year.unique())} | rows={len(year_df):,}"
    )


if __name__ == "__main__":
    main()
