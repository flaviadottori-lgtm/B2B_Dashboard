from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = BASE_DIR / "data" / "raw" / "sidra_empresas.csv"
OUT_DIR = BASE_DIR / "data" / "processed"

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

# (fallback) nome do estado -> sigla, caso o arquivo traga "São Paulo" em vez de "SP"
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


def _read_rows_semicolon(path: Path) -> list[list[str]]:
    """
    Lê o CSV do SIDRA com separador ';' usando csv.reader (robusto contra linhas 'quebradas').
    Também remove BOM se existir.
    """
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    rows: list[list[str]] = []
    with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        for r in reader:
            # remove espaços
            r = [c.strip() for c in r]
            # ignora linhas vazias
            if not any(r):
                continue
            rows.append(r)

    if not rows:
        raise ValueError("Arquivo está vazio ou não foi possível ler.")
    return rows


def _pad_rows(rows: list[list[str]]) -> list[list[str]]:
    max_len = max(len(r) for r in rows)
    return [r + [""] * (max_len - len(r)) for r in rows]


def _find_year_and_header(rows: list[list[str]]) -> tuple[int, int, int]:
    """
    Encontra:
    - idx_year: linha que contém um ano (ex.: 2019)
    - idx_sector: linha logo abaixo, com nomes dos setores (A..., B..., etc.)
    - idx_data_start: primeira linha de dados (começa com BR/GR/UF)
    """
    year_re = re.compile(r"^(19|20)\d{2}$")

    idx_year = -1
    year_val = None
    for i, r in enumerate(rows[:200]):  # não precisa varrer tudo
        for cell in r:
            if year_re.match(cell):
                idx_year = i
                year_val = cell
                break
        if idx_year != -1:
            break

    if idx_year == -1:
        raise ValueError("Não encontrei uma linha com o ano (ex.: 2019) no CSV.")

    idx_sector = idx_year + 1  # no seu print, a linha seguinte tem os setores
    if idx_sector >= len(rows):
        raise ValueError("Não encontrei a linha de setores após a linha do ano.")

    # dados normalmente começam algumas linhas depois; achamos a primeira que tenha nível BR/GR/UF
    idx_data_start = -1
    for i in range(idx_sector + 1, min(idx_sector + 50, len(rows))):
        first = (rows[i][0] or "").upper()
        if first in {"BR", "GR", "UF"}:
            idx_data_start = i
            break

    if idx_data_start == -1:
        # fallback: varre mais um pouco
        for i in range(idx_sector + 1, min(idx_sector + 200, len(rows))):
            first = (rows[i][0] or "").upper()
            if first in {"BR", "GR", "UF"}:
                idx_data_start = i
                break

    if idx_data_start == -1:
        raise ValueError("Não encontrei o início das linhas de dados (BR/GR/UF).")

    return idx_year, idx_sector, idx_data_start


def _extract_state(name_or_sigla: str) -> str | None:
    """
    Tenta extrair sigla de UF de strings como:
    - "SP"
    - "SP - São Paulo"
    - "São Paulo"
    """
    s = (name_or_sigla or "").strip()
    if not s:
        return None

    # "SP - São Paulo"
    if "-" in s:
        left = s.split("-", 1)[0].strip().upper()
        if len(left) == 2 and left in UF_TO_REGION:
            return left

    # "SP"
    if len(s) == 2 and s.upper() in UF_TO_REGION:
        return s.upper()

    # "São Paulo"
    key = s.lower()
    return STATE_NAME_TO_UF.get(key)


def main():
    print(f"✅ Lendo arquivo: {RAW_PATH}")
    rows = _read_rows_semicolon(RAW_PATH)
    rows = _pad_rows(rows)

    idx_year, idx_sector, idx_data_start = _find_year_and_header(rows)

    # Descobre o ano (primeiro ano encontrado na linha do ano)
    year_re = re.compile(r"^(19|20)\d{2}$")
    year_val = None
    for cell in rows[idx_year]:
        if year_re.match(cell):
            year_val = int(cell)
            break
    if year_val is None:
        raise ValueError("Não consegui extrair o ano da linha detectada.")

    # A linha de setores (no seu print) tem nomes dos setores; cada setor ocupa 2 colunas:
    # [valor, unidade]. Vamos pegar só as colunas de valor.
    sector_row = rows[idx_sector]

    # Achar onde começa a parte dos setores: normalmente a primeira célula "Total"
    # (ou algo não vazio depois das colunas de identificação)
    first_sector_col = None
    for j, cell in enumerate(sector_row):
        if cell.strip().lower() in {"total", "total ", "total\t"}:
            first_sector_col = j
            break
    if first_sector_col is None:
        # fallback: pega a primeira coluna não vazia depois das 4 primeiras (Nível, Cód, Nome, Evento)
        for j in range(4, len(sector_row)):
            if sector_row[j].strip():
                first_sector_col = j
                break
    if first_sector_col is None:
        raise ValueError("Não consegui localizar onde começam as colunas de setores na tabela.")

    # Lista de (sector_name, col_index_value)
    sector_map: list[tuple[str, int]] = []
    j = first_sector_col
    while j < len(sector_row):
        sec = sector_row[j].strip()
        if not sec:
            j += 1
            continue
        # remove duplicatas do tipo "Unidades" se por acaso aparecer
        if sec.lower() == "unidades":
            j += 1
            continue
        sector_map.append((sec, j))
        j += 2  # pula a coluna "Unidades" logo depois

    if len(sector_map) < 2:
        raise ValueError(
            "Detectei poucos setores. Parece que a linha de setores não foi lida corretamente."
        )

    # Agora percorremos as linhas de dados e coletamos somente UF + Entrada/Saída
    records = []
    for r in rows[idx_data_start:]:
        level = (r[0] or "").upper()
        if level != "UF":
            continue

        # Colunas iniciais, pelo seu print:
        # 0: Nível (UF)
        # 1: Cód.
        # 2: Nome do território (pode ser "SP - São Paulo" ou "São Paulo")
        # 3: Tipo de evento (Entrada, Saída..., etc.)
        territory_name = r[2]
        event = (r[3] or "").strip().lower()

        # Filtra só o que interessa agora
        if "entrada" not in event and ("saída" not in event and "saida" not in event):
            continue

        uf = _extract_state(territory_name)
        if not uf or uf not in UF_TO_REGION:
            # se não conseguiu identificar a UF, pula
            continue

        for sector, col_idx in sector_map:
            raw_val = (r[col_idx] or "").strip()
            if not raw_val:
                val = 0
            else:
                # valor pode vir com '.' como milhar e ',' como decimal; aqui queremos inteiro
                raw_val2 = raw_val.replace(".", "").replace(",", ".")
                try:
                    val = int(float(raw_val2))
                except Exception:
                    val = 0

            records.append(
                {
                    "year": year_val,
                    "region": UF_TO_REGION[uf],
                    "state": uf,
                    "sector": sector,
                    "event": event,
                    "value": val,
                }
            )

    if not records:
        raise ValueError(
            "Não consegui extrair registros de UF para Entrada/Saída. "
            "Confirme se existem linhas UF no arquivo e se os eventos estão como Entrada/Saída."
        )

    df_long = pd.DataFrame(records)

    # opened/closed
    df_long["opened"] = df_long["value"].where(df_long["event"].str.contains("entrada"), 0)
    df_long["closed"] = df_long["value"].where(df_long["event"].str.contains("saída|saida"), 0)

    out = df_long.groupby(["year", "region", "state", "sector"], as_index=False)[
        ["opened", "closed"]
    ].sum()
    out["net"] = out["opened"] - out["closed"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_parquet = OUT_DIR / "companies_agg.parquet"
    out_csv = OUT_DIR / "companies_agg.csv"

    out.to_parquet(out_parquet, index=False)
    out.to_csv(out_csv, index=False, encoding="utf-8")

    print("✅ Arquivos gerados com sucesso:")
    print(f" - {out_parquet}")
    print(f" - {out_csv}")
    print("\n🔎 Amostra (10 linhas):")
    print(out.head(10))


if __name__ == "__main__":
    main()
