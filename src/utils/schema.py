from typing import Iterable

import pandas as pd


def require_columns(df: pd.DataFrame, cols: Iterable[str], name: str) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{name}] Colunas faltando: {missing}\n" f"Colunas existentes: {list(df.columns)}"
        )


IBGE_TIDY_COLS = [
    "year",
    "state",
    "region",
    "sector",
    "units",
    "high_growth_units",
    "employment",
    "avg_wage",
    "high_growth_ratio",
    "cagr_2008_2021",
    "volatility_units",
]

COMPANIES_AGG_COLS = ["year", "region", "state", "sector", "opened", "closed", "net"]
