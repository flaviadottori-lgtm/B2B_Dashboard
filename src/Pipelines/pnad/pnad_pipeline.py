from __future__ import annotations

import argparse
import logging
import os
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import duckdb
import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)


UF_CODE_MAP = {
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


def _strip_accents(value: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", value) if not unicodedata.combining(ch)
    )


def _norm_text(value: str) -> str:
    text = _strip_accents(str(value)).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _resolve_column(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    col_map = {_norm_text(c): c for c in columns}
    for cand in candidates:
        key = _norm_text(cand)
        if key in col_map:
            return col_map[key]
    return None


def _parse_quarter(value: object) -> Optional[int]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        if int(value) in {1, 2, 3, 4}:
            return int(value)
    text = _norm_text(str(value))
    match = re.search(r"(?:t|tri|trimestre)?_?([1-4])", text)
    if match:
        return int(match.group(1))
    return None


def _normalize_uf(value: object) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return UF_CODE_MAP.get(int(value))
    text = str(value).strip().upper()
    if len(text) == 2:
        return text
    if text.isdigit():
        return UF_CODE_MAP.get(int(text))
    return None


def _normalize_sex(value: object) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = _norm_text(str(value))
    if text in {"m", "masculino", "homem", "male"}:
        return "Masculino"
    if text in {"f", "feminino", "mulher", "female"}:
        return "Feminino"
    if text in {"1", "2"}:
        return "Masculino" if text == "1" else "Feminino"
    return str(value).strip()


def _age_group_from_age(age: object) -> Optional[str]:
    if age is None or (isinstance(age, float) and pd.isna(age)):
        return None
    try:
        age_int = int(float(age))
    except Exception:
        return None
    bins = [
        (0, 9, "00-09"),
        (10, 14, "10-14"),
        (15, 17, "15-17"),
        (18, 19, "18-19"),
        (20, 24, "20-24"),
        (25, 29, "25-29"),
        (30, 34, "30-34"),
        (35, 39, "35-39"),
        (40, 44, "40-44"),
        (45, 49, "45-49"),
        (50, 54, "50-54"),
        (55, 59, "55-59"),
        (60, 64, "60-64"),
    ]
    for low, high, label in bins:
        if low <= age_int <= high:
            return label
    return "65+"


def _normalize_formality(value: object) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = _norm_text(str(value))
    formal_keys = {
        "formal",
        "com_carteira",
        "empregado_com_carteira",
        "militar",
        "funcionario_publico",
        "servidor_publico",
        "celetista",
    }
    informal_keys = {
        "informal",
        "sem_carteira",
        "conta_propria",
        "autonomo",
        "empregador_sem_cnpj",
        "trabalhador_familiar_auxiliar",
        "ajudante_familiar",
    }
    if text in formal_keys:
        return "formal"
    if text in informal_keys:
        return "informal"
    return str(value).strip()


@dataclass
class PNADPipelineConfig:
    base_dir: Path
    min_year: int = 2017
    source_url: Optional[str] = None
    raw_dir: Optional[Path] = None
    processed_dir: Optional[Path] = None
    gold_dir: Optional[Path] = None

    def __post_init__(self) -> None:
        if self.raw_dir is None:
            self.raw_dir = self.base_dir / "data" / "raw" / "pnad"
        if self.processed_dir is None:
            self.processed_dir = self.base_dir / "data" / "processed" / "pnad"
        if self.gold_dir is None:
            self.gold_dir = self.base_dir / "data" / "gold" / "pnad"


class PNADPipeline:
    def __init__(self, config: PNADPipelineConfig) -> None:
        self.config = config

    def run(self) -> pd.DataFrame:
        self._ensure_dirs()
        raw_path = self._ensure_raw_data()
        df_raw = self._load_raw(raw_path)
        df_clean = self._standardize(df_raw)
        df_agg = self._aggregate(df_clean)
        self._save_outputs(df_clean, df_agg)
        return df_agg

    def _ensure_dirs(self) -> None:
        self.config.raw_dir.mkdir(parents=True, exist_ok=True)
        self.config.processed_dir.mkdir(parents=True, exist_ok=True)
        self.config.gold_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_raw_data(self) -> Path:
        candidates = sorted(self.config.raw_dir.glob("pnad*.parquet"))
        candidates += sorted(self.config.raw_dir.glob("pnad*.csv"))
        if candidates:
            latest = max(candidates, key=lambda p: p.stat().st_mtime)
            LOGGER.info("Using local raw file: %s", latest)
            return latest

        if not self.config.source_url:
            raise FileNotFoundError(
                "No local PNAD raw file found. Set PNAD_SOURCE_URL to download from Base dos Dados."
            )

        filename = Path(self.config.source_url).name or "pnad_raw.parquet"
        target = self.config.raw_dir / filename
        LOGGER.info("Downloading PNAD data from %s", self.config.source_url)
        self._download(self.config.source_url, target)
        return target

    def _download(self, url: str, target: Path) -> None:
        with requests.get(url, stream=True, timeout=300) as response:
            response.raise_for_status()
            with open(target, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        LOGGER.info("Saved raw file: %s (%.2f MB)", target, target.stat().st_size / (1024**2))

    def _load_raw(self, path: Path) -> pd.DataFrame:
        LOGGER.info("Loading raw data: %s", path)
        if path.suffix.lower() == ".parquet":
            query = f"SELECT * FROM read_parquet('{path.as_posix()}')"
            return duckdb.query(query).df()
        if path.suffix.lower() == ".csv":
            query = f"SELECT * FROM read_csv_auto('{path.as_posix()}')"
            return duckdb.query(query).df()
        raise ValueError(f"Unsupported raw format: {path.suffix}")

    def _standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        LOGGER.info("Standardizing columns and values")
        columns = list(df.columns)

        col_year = _resolve_column(columns, ["ano", "year"])
        col_quarter = _resolve_column(columns, ["trimestre", "quarter", "tri"])
        col_uf = _resolve_column(columns, ["uf", "uf_code", "id_uf", "sigla_uf", "cod_uf"])
        col_sex = _resolve_column(columns, ["sexo", "gender", "sex"])
        col_age_group = _resolve_column(columns, ["grupo_idade", "faixa_etaria", "age_group"])
        col_age = _resolve_column(columns, ["idade", "age"])
        col_formality = _resolve_column(columns, ["formalidade", "posicao_ocupacao", "vinculo"])
        col_sector = _resolve_column(columns, ["setor", "atividade", "cnae", "setor_ocupacao"])
        col_occupation = _resolve_column(columns, ["ocupacao", "ocupacao_principal", "cbo"])
        col_weight = _resolve_column(columns, ["peso", "peso_amostral", "peso_pessoa"])
        col_population = _resolve_column(columns, ["populacao", "valor", "value"])

        if not col_year or not col_uf or not col_sex:
            raise ValueError(
                "Missing required columns (ano/uf/sexo). Check the raw PNAD file schema."
            )

        df = df.copy()
        df["ano"] = pd.to_numeric(df[col_year], errors="coerce").astype("Int64")
        df["trimestre"] = df[col_quarter].apply(_parse_quarter) if col_quarter else None
        df["uf_code"] = df[col_uf].apply(_normalize_uf)
        df["sexo"] = df[col_sex].apply(_normalize_sex)

        if col_age_group:
            df["grupo_idade"] = df[col_age_group].astype(str).str.strip()
        elif col_age:
            df["grupo_idade"] = df[col_age].apply(_age_group_from_age)
        else:
            df["grupo_idade"] = None

        if col_formality:
            df["formalidade"] = df[col_formality].apply(_normalize_formality)

        if col_sector:
            df["setor"] = df[col_sector].astype(str).str.strip()

        if col_occupation:
            df["ocupacao"] = df[col_occupation].astype(str).str.strip()

        if col_population:
            df["populacao"] = pd.to_numeric(df[col_population], errors="coerce")
        elif col_weight:
            df["populacao"] = pd.to_numeric(df[col_weight], errors="coerce")

        df = df[df["ano"].notna() & df["uf_code"].notna() & df["sexo"].notna()]
        df["ano"] = df["ano"].astype(int)
        if col_quarter:
            df = df[df["trimestre"].notna()]
            df["trimestre"] = df["trimestre"].astype(int)
        else:
            df["trimestre"] = 0

        df = df[df["ano"] >= self.config.min_year]
        LOGGER.info("Standardized rows: %s", len(df))
        return df

    def _aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        LOGGER.info("Aggregating PNAD data")
        group_cols = ["ano", "trimestre", "uf_code", "sexo", "grupo_idade"]
        for optional_col in ["formalidade", "ocupacao", "setor"]:
            if optional_col in df.columns and df[optional_col].notna().any():
                group_cols.append(optional_col)

        if "populacao" in df.columns:
            agg = df.groupby(group_cols, dropna=False)["populacao"].sum().reset_index()
        else:
            agg = df.groupby(group_cols, dropna=False).size().reset_index(name="populacao")

        agg["extracao_data"] = datetime.utcnow()
        LOGGER.info("Aggregated rows: %s", len(agg))
        return agg

    def _save_outputs(self, df_clean: pd.DataFrame, df_agg: pd.DataFrame) -> None:
        processed_path = self.config.processed_dir / "pnad_clean.parquet"
        gold_path = self.config.gold_dir / "pnad_uf_trimestre_sexo_idade.parquet"

        df_clean.to_parquet(processed_path, index=False, compression="snappy")
        df_agg.to_parquet(gold_path, index=False, compression="snappy")

        LOGGER.info("Saved processed: %s", processed_path)
        LOGGER.info("Saved gold: %s", gold_path)


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="PNAD pipeline (Base dos Dados, no BigQuery)")
    parser.add_argument("--min-year", type=int, default=2017, help="Minimum year to keep")
    parser.add_argument(
        "--source-url",
        type=str,
        default=os.getenv("PNAD_SOURCE_URL"),
        help="Direct URL to a PNAD file from Base dos Dados (parquet or csv)",
    )
    args = parser.parse_args()

    _setup_logging()

    base_dir = Path(__file__).resolve().parents[3]
    config = PNADPipelineConfig(
        base_dir=base_dir,
        min_year=args.min_year,
        source_url=args.source_url,
    )

    pipeline = PNADPipeline(config)
    pipeline.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
