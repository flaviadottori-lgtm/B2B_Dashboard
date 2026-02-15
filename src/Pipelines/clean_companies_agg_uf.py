from __future__ import annotations
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INP = PROJECT_ROOT / "data" / "processed" / "companies_agg.parquet"
OUT = PROJECT_ROOT / "data" / "processed" / "companies_agg_uf.parquet"

REGIONS_AND_TOTALS = {
    "Brasil",
    "Norte", "Nordeste", "Sul", "Sudeste", "Centro-Oeste",
    "Brasil, Grande Região e Unidade da Federação",
}

UF_NAME_TO_SIGLA = {
    "Acre": "AC",
    "Alagoas": "AL",
    "Amapá": "AP",
    "Amazonas": "AM",
    "Bahia": "BA",
    "Ceará": "CE",
    "Distrito Federal": "DF",
    "Espírito Santo": "ES",
    "Goiás": "GO",
    "Maranhão": "MA",
    "Mato Grosso": "MT",
    "Mato Grosso do Sul": "MS",
    "Minas Gerais": "MG",
    "Pará": "PA",
    "Paraíba": "PB",
    "Paraná": "PR",
    "Pernambuco": "PE",
    "Piauí": "PI",
    "Rio de Janeiro": "RJ",
    "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS",
    "Rondônia": "RO",
    "Roraima": "RR",
    "Santa Catarina": "SC",
    "São Paulo": "SP",
    "Sergipe": "SE",
    "Tocantins": "TO",
}

def fix_mojibake(s: str) -> str:
    """
    Corrige casos tipo 'AmapÃ¡' -> 'Amapá' tentando latin1->utf8.
    Se não der, retorna original.
    """
    if not isinstance(s, str):
        return str(s)
    s = s.strip().strip('"')
    try:
        # comum quando o texto foi salvo em UTF-8 e lido como latin1
        return s.encode("latin1", errors="ignore").decode("utf-8", errors="ignore").strip()
    except Exception:
        return s

def normalize_state(s: str) -> str:
    s2 = fix_mojibake(s)
    s2 = s2.replace("  ", " ").strip()
    return s2

def main():
    if not INP.exists():
        raise FileNotFoundError(f"Não achei {INP}")

    df = pd.read_parquet(INP).copy()

    if "state" not in df.columns:
        raise ValueError("companies_agg.parquet não tem coluna 'state'.")

    # 1) normaliza encoding / espaços
    df["state"] = df["state"].astype(str).map(normalize_state)

    # 2) remove linhas agregadas (Brasil/regiões/header lixo)
    df = df[~df["state"].isin(REGIONS_AND_TOTALS)].copy()
    df = df[~df["state"].str.contains("Grande Região", na=False)].copy()

    # 3) mapeia UF por extenso -> sigla
    df["state_sigla"] = df["state"].map(UF_NAME_TO_SIGLA)

    # mantém apenas as 27 UFs
    df = df[df["state_sigla"].notna()].copy()

    # substitui state por sigla (pra casar com GeoJSON e mapas)
    df["state"] = df["state_sigla"]
    df = df.drop(columns=["state_sigla"])

    # sanity check
    ufs = sorted(df["state"].unique().tolist())
    print("UFs detectadas:", ufs)
    print("n_ufs:", len(ufs))
    print("years:", sorted(df["year"].unique().tolist()))
    print("rows:", len(df))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print("✅ Salvo:", OUT)

if __name__ == "__main__":
    main()
