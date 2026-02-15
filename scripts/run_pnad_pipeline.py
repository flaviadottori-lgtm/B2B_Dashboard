#!/usr/bin/env python
"""
CLI para rodar o pipeline PNAD Contínua

Uso:
    python run_pnad_pipeline.py                  # Extrai últimos 3 anos
    python run_pnad_pipeline.py --min-year 2021 # Extrai a partir de 2021
"""

import sys
from pathlib import Path
import argparse
import logging

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.Pipelines.pnad import extract_pnad


def setup_logging(level=logging.INFO):
    """Configure logging for CLI"""
    logging.basicConfig(
        level=level, format="[%(asctime)s] %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"
    )


def main():
    parser = argparse.ArgumentParser(description="Extract PNAD Contínua data from BigQuery")
    parser.add_argument(
        "--min-year",
        type=int,
        default=2017,
        help="Minimum year to extract (default: 2017 = available data from 2012-2019)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output parquet file path (default: data/marts/pnad/pnad_uf_quarter_gender_age.parquet)",
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Only extract to DataFrame, do not save parquet"
    )
    parser.add_argument(
        "--project", type=str, default="b2b-opportunity-engine", help="GCP project ID for billing"
    )

    args = parser.parse_args()
    setup_logging()

    # Default output path
    if args.output is None and not args.no_save:
        args.output = (
            project_root / "data" / "marts" / "pnad" / "pnad_uf_quarter_gender_age.parquet"
        )

    try:
        print()
        print("=" * 70)
        print("PNAD CONTÍNUA EXTRACTION PIPELINE")
        print("=" * 70)
        print()

        # Extract data
        df = extract_pnad(
            min_year=args.min_year,
            output_path=args.output if not args.no_save else None,
            project_id=args.project,
        )

        print()
        print("=" * 70)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Records extracted: {len(df):,}")
        if args.output:
            print(f"Output: {args.output}")
        print()

        return 0

    except Exception as e:
        logging.error(f"\n❌ Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
