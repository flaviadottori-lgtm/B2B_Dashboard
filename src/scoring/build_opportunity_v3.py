from pathlib import Path
import pandas as pd
import numpy as np

DATA_DIR = Path("data/processed")


# -----------------------------
# Utils
# -----------------------------
def pct_rank(s: pd.Series) -> pd.Series:
    return s.rank(pct=True, method="average")


def _clean_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def _ensure_column(df: pd.DataFrame, target: str, candidates: list[str]) -> pd.DataFrame:
    """
    Garante que exista a coluna `target`. Se não existir, tenta renomear a partir de candidatos.
    """
    df = _clean_cols(df)
    if target in df.columns:
        return df

    found = next((c for c in candidates if c in df.columns), None)
    if found is None:
        raise KeyError(
            f"Coluna '{target}' não encontrada. "
            f"Procurei candidatos={candidates}. Colunas disponíveis: {list(df.columns)}"
        )
    return df.rename(columns={found: target})


# -----------------------------
# Momentum (CAGED)
# -----------------------------
def build_momentum_features(caged_m: pd.DataFrame) -> pd.DataFrame:
    """
    Espera colunas (case-insensitive):
      - year
      - month (ou mes)
      - state (ou uf)
      - sector (ou secao / cnae_secao / setor)
      - net_jobs (ou saldo / job_balance / etc)
    """
    c = _clean_cols(caged_m)

    # normaliza nomes comuns
    c = _ensure_column(c, "month", ["mes", "mês"])
    c = _ensure_column(c, "state", ["uf", "estado"])
    c = _ensure_column(c, "sector", ["setor", "secao", "seção", "cnae_secao", "cnae_seção"])

    # net_jobs (redundante: main garante, mas deixa robusto)
    c = _ensure_column(
        c,
        "net_jobs",
        [
            "job_balance",
            "saldo",
            "net",
            "net_job",
            "netjobs",
            "saldo_mov",
            "saldo_vagas",
            "saldo_emprego",
        ],
    )

    c["year"] = pd.to_numeric(c["year"], errors="coerce").astype("Int64")
    c["month"] = pd.to_numeric(c["month"], errors="coerce").astype("Int64")
    c = c.dropna(subset=["year", "month", "state", "sector"]).copy()

    c["year"] = c["year"].astype(int)
    c["month"] = c["month"].astype(int)
    c["net_jobs"] = pd.to_numeric(c["net_jobs"], errors="coerce").fillna(0)

    feats = []
    for (y, st, sec), g in c.groupby(["year", "state", "sector"], sort=False):
        g = g.sort_values("month")

        last6 = g.tail(6)
        last3 = g.tail(3)
        prev3 = g.tail(6).head(3)  # 3 antes dos últimos 3

        net_jobs_ytd = float(g["net_jobs"].sum())
        net_jobs_6m = float(last6["net_jobs"].sum())
        share_pos = float((g["net_jobs"] > 0).mean()) if len(g) else 0.0

        if len(last6) >= 6:
            acc = float(last3["net_jobs"].sum() - prev3["net_jobs"].sum())
        else:
            acc = float(last3["net_jobs"].sum())

        vol = float(g["net_jobs"].std(ddof=0)) if len(g) >= 2 else 0.0

        feats.append(
            {
                "year": y,
                "state": st,
                "sector": sec,
                "net_jobs_ytd": net_jobs_ytd,
                "net_jobs_6m": net_jobs_6m,
                "share_positive_months": share_pos,
                "acceleration": acc,
                "volatility_jobs": vol,
                "months_observed": int(len(g)),
            }
        )

    return pd.DataFrame(feats)


# -----------------------------
# Main
# -----------------------------
def main():
    # 1) BASE ESTRUTURAL (v2) — 2021
    v2_path = DATA_DIR / "opportunity_scores.parquet"
    df_v2 = pd.read_parquet(v2_path)
    df_v2 = _clean_cols(df_v2)

    df_v2 = _ensure_column(df_v2, "year", ["ano"])
    df_v2 = _ensure_column(df_v2, "state", ["uf", "estado"])
    df_v2 = _ensure_column(df_v2, "region", ["regiao", "região"])
    df_v2 = _ensure_column(df_v2, "sector", ["setor", "secao", "seção", "cnae_secao", "cnae_seção"])
    df_v2 = _ensure_column(df_v2, "opportunity_score", ["score", "opportunity", "op_score"])

    base = df_v2[df_v2["year"] == 2021].copy()
    if base.empty:
        raise ValueError("Não encontrei registros de 2021 em opportunity_scores.parquet (v2).")

    base = base.rename(columns={"opportunity_score": "opportunity_score_v2_2021"})

    optional_struct_cols = [
        "units",
        "employment",
        "avg_wage",
        "opened",
        "closed",
        "net",
        "hg_density",
        "cagr_2008_2021",
        "volatility_units",
    ]
    existing_struct_cols = [c for c in optional_struct_cols if c in base.columns]

    base = base[
        ["state", "region", "sector", "opportunity_score_v2_2021"] + existing_struct_cols
    ].copy()

    # 2) CAGED mensal
    caged_path = DATA_DIR / "caged_state_sector_month.parquet"
    caged = pd.read_parquet(caged_path)
    caged = _clean_cols(caged)

    # garante net_jobs (no seu caso: job_balance)
    caged = _ensure_column(
        caged,
        "net_jobs",
        [
            "job_balance",
            "saldo",
            "net",
            "net_job",
            "netjobs",
            "saldo_mov",
            "saldo_vagas",
            "saldo_emprego",
        ],
    )

    # 3) Momentum features
    mom = build_momentum_features(caged)
    if mom.empty:
        raise ValueError(
            "Momentum features vazio. Verifique se o parquet do CAGED tem dados/colunas corretas."
        )

    # 4) Join com baseline estrutural
    df = mom.merge(base, on=["state", "sector"], how="left")

    # 5) Scores
    df["structural_score"] = df.groupby("year")["opportunity_score_v2_2021"].transform(
        lambda s: 100 * pct_rank(s.fillna(s.median()))
    )

    df["m1"] = df.groupby("year")["net_jobs_ytd"].transform(pct_rank)
    df["m2"] = df.groupby("year")["net_jobs_6m"].transform(pct_rank)
    df["m3"] = df["share_positive_months"].clip(0, 1)
    df["m4"] = df.groupby("year")["acceleration"].transform(pct_rank)

    df["momentum_score"] = 100 * (
        0.40 * df["m1"] + 0.30 * df["m2"] + 0.20 * df["m3"] + 0.10 * df["m4"]
    )

    df["opportunity_score_v3"] = 0.65 * df["structural_score"] + 0.35 * df["momentum_score"]

    # 6) saída
    keep = [
        "year",
        "state",
        "region",
        "sector",
        "opportunity_score_v2_2021",
        "structural_score",
        "net_jobs_ytd",
        "net_jobs_6m",
        "share_positive_months",
        "acceleration",
        "volatility_jobs",
        "months_observed",
        "momentum_score",
        "opportunity_score_v3",
    ] + existing_struct_cols

    df = df[keep].sort_values(["year", "opportunity_score_v3"], ascending=[True, False])

    out = DATA_DIR / "opportunity_scores_v3.parquet"
    df.to_parquet(out, index=False)

    print(f"✅ Opportunity Engine v3 generated: {out}")
    print("Years:", sorted(df["year"].unique()))
    print("Rows:", f"{len(df):,}")


if __name__ == "__main__":
    main()
