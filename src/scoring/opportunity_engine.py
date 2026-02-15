import numpy as np
import pandas as pd

from src.utils.io import load_companies_agg, load_ibge_tidy, save_parquet
from src.utils.schema import COMPANIES_AGG_COLS, IBGE_TIDY_COLS, require_columns

# =====================================================
# Load
# =====================================================
ibge = load_ibge_tidy()
require_columns(ibge, IBGE_TIDY_COLS, "ibge_3274_3275_tidy")

companies = load_companies_agg()
require_columns(companies, COMPANIES_AGG_COLS, "companies_agg")

# =====================================================
# Merge IBGE + Business Demography
# =====================================================
df = ibge.merge(companies, on=["year", "state", "region", "sector"], how="left")

for c in ["opened", "closed", "net"]:
    df[c] = df[c].fillna(0)

# =====================================================
# Feature Engineering
# =====================================================

# Scale
df["log_units"] = np.log1p(df["units"])

# High-growth density
df["hg_density"] = df["high_growth_units"] / df["units"]
df["hg_density"] = df["hg_density"].replace([np.inf, -np.inf], 0).fillna(0)

# Business demography
df["net_rate"] = df["net"] / df["units"]
df["net_rate"] = df["net_rate"].replace([np.inf, -np.inf], 0).fillna(0)

# Stability
df["stability"] = 1 / (1 + df["volatility_units"])

# =====================================================
# Normalize by percentile rank (per year)
# =====================================================
features = ["log_units", "cagr_2008_2021", "hg_density", "net_rate", "stability"]

for f in features:
    df[f + "_n"] = df.groupby("year")[f].rank(pct=True)

# =====================================================
# Opportunity Score (0–100)
# =====================================================
df["opportunity_score"] = 100 * (
    0.25 * df["log_units_n"]
    + 0.25 * df["cagr_2008_2021_n"]
    + 0.20 * df["hg_density_n"]
    + 0.20 * df["net_rate_n"]
    + 0.10 * df["stability_n"]
)

# =====================================================
# Output
# =====================================================
out = df[
    [
        "year",
        "state",
        "region",
        "sector",
        "units",
        "high_growth_units",
        "employment",
        "avg_wage",
        "opened",
        "closed",
        "net",
        "hg_density",
        "cagr_2008_2021",
        "volatility_units",
        "opportunity_score",
    ]
].sort_values(["year", "opportunity_score"], ascending=[True, False])

save_parquet(out, "opportunity_scores.parquet")

print("✅ Opportunity Score v2 gerado (IBGE + Business Demography)")
