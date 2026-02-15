import pandas as pd
from .paths import get_paths


def load_ibge_tidy() -> pd.DataFrame:
    p = get_paths().ibge_tidy
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")
    return pd.read_parquet(p)


def load_companies_agg() -> pd.DataFrame:
    p = get_paths().companies_agg
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")
    return pd.read_parquet(p)


def load_opportunity_scores() -> pd.DataFrame:
    p = get_paths().opportunity_scores
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")
    return pd.read_parquet(p)


def save_parquet(df: pd.DataFrame, filename: str) -> None:
    p = get_paths().processed / filename
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
