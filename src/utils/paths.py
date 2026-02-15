from pathlib import Path
DUCKDB_PATH = Path(__file__).resolve().parents[2] / 'data' / 'marts' / 'b2b.duckdb'
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data: Path
    processed: Path
    raw: Path
    geo: Path

    ibge_tidy: Path
    companies_agg: Path
    opportunity_scores: Path

def get_paths() -> ProjectPaths:
    root = Path(__file__).resolve().parents[2]  # .../B2B_Dashboard
    data = root / "data"
    processed = data / "processed"
    raw = data / "raw"
    geo = data / "geo"

    return ProjectPaths(
        root=root,
        data=data,
        processed=processed,
        raw=raw,
        geo=geo,
        ibge_tidy=processed / "ibge_3274_3275_tidy.parquet",
        companies_agg=processed / "companies_agg.parquet",
        opportunity_scores=processed / "opportunity_scores.parquet",
    )
