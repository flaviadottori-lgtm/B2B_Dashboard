from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

RAW_FTP_DIR = Path("data/raw/rais")  # segue seu padrão
OUT_DIR = Path("data/processed/rais/agg_parquet")


# Mapa básico de UF por código (caso a RAIS venha com código numérico)
UF_CODE_TO_SIGLA = {
    11: "RO",
    12: "AC",
    13: "AM",
    14: "RR",
    15: "PA",
    16: "AP",
    17: "TO",
    21: "MA",
    22: "PI",
    23: "CE",
    24: "RN",
    25: "PB",
    26: "PE",
    27: "AL",
    28: "SE",
    29: "BA",
    31: "MG",
    32: "ES",
    33: "RJ",
    35: "SP",
    41: "PR",
    42: "SC",
    43: "RS",
    50: "MS",
    51: "MT",
    52: "GO",
    53: "DF",
}


def idade_para_grupo(idade: pd.Series) -> pd.Series:
    # faixas simples e úteis para seu motor
    bins = [-1, 17, 24, 34, 44, 54, 64, 200]
    labels = ["14-17", "18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    return pd.cut(idade.fillna(-1).astype(int), bins=bins, labels=labels).astype("string")


def pick_first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None


def build_agg(year: int, region_tag: str, chunksize: int = 400_000) -> Path:
    """
    Lê o TXT de vínculos da RAIS (por região), agrega e salva parquet leve.
    """
    txt_path = RAW_FTP_DIR / f"ano={year}" / "ftp" / f"RAIS_VINC_PUB_{region_tag}.txt"
    if not txt_path.exists():
        raise FileNotFoundError(f"Não achei o arquivo: {txt_path}")

    # tenta detectar separador por amostra
    sample = txt_path.read_text(encoding="latin1", errors="ignore", newline="")[:5000]
    sep = ";" if ";" in sample else "|"

    print(f"📄 Lendo: {txt_path}")
    print(f"🔧 Separador detectado: {sep!r}")
    print(f"🧩 Chunksize: {chunksize}")

    agg = None

    # leitura em chunks (leve)
    start_ts = time.time()
    last_heartbeat = start_ts

    for i, chunk in enumerate(
        pd.read_csv(
            txt_path,
            sep=sep,
            encoding="latin1",
            low_memory=False,
            chunksize=chunksize,
        )
    ):
        now = time.time()
        if now - last_heartbeat >= 30:
            elapsed = int(now - start_ts)
            mm, ss = divmod(elapsed, 60)
            print(
                f"[PROGRESSO] ano={year} regiao={region_tag} chunks={i+1} elapsed={mm:02d}:{ss:02d}"
            )
            last_heartbeat = now
        if i == 0:
            print(f"✅ Colunas encontradas (amostra): {list(chunk.columns)[:20]} ...")

        # Detectar colunas explícitas para RAIS
        col_mun = pick_first_existing(chunk, ["Mun Trab", "Município"])
        col_cnae = pick_first_existing(
            chunk,
            ["CNAE 2.0 Subclasse", "CNAE 2.0 Classe"],
        )
        col_sexo = pick_first_existing(chunk, ["Sexo Trabalhador"])
        col_idade = pick_first_existing(chunk, ["Idade", "Faixa Etária"])
        col_instr = pick_first_existing(chunk, ["Escolaridade após 2005"])

        missing = [
            name
            for name, col in [
                ("MUNICIPIO", col_mun),
                ("CNAE", col_cnae),
                ("SEXO", col_sexo),
                ("IDADE/FAIXA", col_idade),
                ("INSTRUCAO", col_instr),
            ]
            if col is None
        ]
        if missing:
            raise RuntimeError(
                "Não consegui identificar colunas essenciais nesta RAIS. Faltando: "
                + ", ".join(missing)
                + ". Me mande a lista completa de colunas (print) que eu ajusto."
            )

        df = chunk[[col_mun, col_cnae, col_sexo, col_idade, col_instr]].copy()
        df.columns = ["municipio", "cnae_subclasse", "sexo", "idade_faixa", "grau_instrucao"]

        mun_num = pd.to_numeric(df["municipio"], errors="coerce")
        mun_str = mun_num.astype("Int64").astype("string").str.zfill(6)
        uf_code = pd.to_numeric(mun_str.str.slice(0, 2), errors="coerce")
        df["sigla_uf"] = uf_code.map(UF_CODE_TO_SIGLA).astype("string")

        if col_idade.lower() == "idade":
            df["grupo_idade"] = idade_para_grupo(pd.to_numeric(df["idade_faixa"], errors="coerce"))
        else:
            df["grupo_idade"] = df["idade_faixa"].astype("string").str.strip()

        df["cnae_subclasse"] = df["cnae_subclasse"].astype("string").str.strip()
        df["sexo"] = df["sexo"].astype("string").str.strip()
        df["grau_instrucao"] = df["grau_instrucao"].astype("string").str.strip()
        df["ano"] = year

        # conta vínculos (cada linha = um vínculo)
        df["vinculos"] = 1

        g = (
            df.groupby(
                ["ano", "sigla_uf", "cnae_subclasse", "sexo", "grupo_idade", "grau_instrucao"],
                dropna=False,
            )["vinculos"]
            .sum()
            .reset_index()
        )

        if agg is None:
            agg = g
        else:
            agg = pd.concat([agg, g], ignore_index=True)
            agg = (
                agg.groupby(
                    ["ano", "sigla_uf", "cnae_subclasse", "sexo", "grupo_idade", "grau_instrucao"],
                    dropna=False,
                )["vinculos"]
                .sum()
                .reset_index()
            )

        if (i + 1) % 5 == 0:
            print(f"… processados {i+1} chunks")

    if agg is None:
        raise RuntimeError(
            "Nada foi agregado. O arquivo pode estar vazio ou houve falha de leitura."
        )

    out_path = OUT_DIR / f"ano={year}" / f"rais_vinc_agg_{region_tag.lower()}_{year}.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    agg.to_parquet(out_path, index=False)
    print(f"✅ Parquet agregado salvo em: {out_path}")
    print(f"📊 Linhas agregadas: {len(agg):,}")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m src.Pipelines.rais.build_rais_agg_parquet <ANO> <TAG_REGIAO>")
        print("Ex.: python -m src.Pipelines.rais.build_rais_agg_parquet 2022 CENTRO_OESTE")
        sys.exit(1)

    year = int(sys.argv[1])
    tag = sys.argv[2]
    build_agg(year, tag)
